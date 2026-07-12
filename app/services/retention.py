import json
import logging
from datetime import date, datetime, time, timedelta

from sqlalchemy.orm import Session as DbSession

from app.bot.telegram_client import telegram_client
from app.config import get_settings
from app.copy.retention import (
    anniversary_reminder,
    birthday_reminder,
    challenge_completed_celebration,
    challenge_daily_nudge,
    new_year_reminder,
    weekly_reflection_prompt,
)
from app.constants import SEVEN_DAY_EXERCISES, WEEKLY_REFLECTIONS
from app.models import Reminder, ReminderKind, Session
from app.services.challenge import (
    build_challenge_view,
    challenge_week_number,
    current_challenge_day,
)

logger = logging.getLogger(__name__)


def _reminder_exists(
    db: DbSession,
    *,
    session_id: str,
    participant_id: str | None,
    kind: ReminderKind,
    scheduled_for: datetime,
) -> bool:
    query = db.query(Reminder).filter(
        Reminder.session_id == session_id,
        Reminder.kind == kind,
        Reminder.scheduled_for == scheduled_for,
    )
    if participant_id:
        query = query.filter(Reminder.participant_id == participant_id)
    else:
        query = query.filter(Reminder.participant_id.is_(None))
    return query.first() is not None


def _schedule_reminder(
    db: DbSession,
    *,
    session_id: str,
    participant_id: str | None,
    kind: ReminderKind,
    scheduled_for: datetime,
    payload: dict | None = None,
) -> None:
    if _reminder_exists(
        db,
        session_id=session_id,
        participant_id=participant_id,
        kind=kind,
        scheduled_for=scheduled_for,
    ):
        return

    db.add(
        Reminder(
            session_id=session_id,
            participant_id=participant_id,
            kind=kind,
            scheduled_for=scheduled_for,
            payload_json=json.dumps(payload or {}),
        )
    )


def _at_noon(target_date: date) -> datetime:
    return datetime.combine(target_date, time(hour=9, minute=0))


def _next_occurrence(month: int, day: int, *, after: date) -> date:
    year = after.year
    try:
        candidate = date(year, month, day)
    except ValueError:
        candidate = date(year, month, 28)
    if candidate < after:
        try:
            candidate = date(year + 1, month, day)
        except ValueError:
            candidate = date(year + 1, month, 28)
    return candidate


def schedule_session_reminders(db: DbSession, session: Session) -> None:
    if not session.reminders_enabled:
        return

    today = datetime.utcnow().date()
    participants = session.participants

    if session.anniversary_date:
        anniversary = _next_occurrence(
            session.anniversary_date.month,
            session.anniversary_date.day,
            after=today,
        )
        years = anniversary.year - session.anniversary_date.year
        _schedule_reminder(
            db,
            session_id=session.id,
            participant_id=None,
            kind=ReminderKind.anniversary,
            scheduled_for=_at_noon(anniversary),
            payload={"years": years},
        )

    for participant in participants:
        if not participant.birthday:
            continue
        birthday = _next_occurrence(
            participant.birthday.month,
            participant.birthday.day,
            after=today,
        )
        _schedule_reminder(
            db,
            session_id=session.id,
            participant_id=participant.id,
            kind=ReminderKind.birthday,
            scheduled_for=_at_noon(birthday),
            payload={"name": participant.name},
        )

    new_year = date(today.year if today.month < 12 or today.day < 25 else today.year + 1, 12, 31)
    if new_year <= today:
        new_year = date(today.year + 1, 12, 31)
    _schedule_reminder(
        db,
        session_id=session.id,
        participant_id=None,
        kind=ReminderKind.new_year,
        scheduled_for=_at_noon(new_year),
    )

    if session.challenge_started_at:
        schedule_challenge_reminders(db, session)


def schedule_challenge_reminders(db: DbSession, session: Session) -> None:
    if not session.reminders_enabled or not session.challenge_started_at:
        return

    progress_view = build_challenge_view(session)
    if progress_view.is_complete:
        return

    current_day = current_challenge_day(session)
    for day_index, (title, _) in enumerate(SEVEN_DAY_EXERCISES, start=1):
        if day_index < current_day:
            continue
        if progress_view.days[day_index - 1].completed:
            continue
        target_date = session.challenge_started_at.date() + timedelta(days=day_index - 1)
        if target_date < datetime.utcnow().date():
            target_date = datetime.utcnow().date()
        _schedule_reminder(
            db,
            session_id=session.id,
            participant_id=None,
            kind=ReminderKind.challenge_daily,
            scheduled_for=_at_noon(target_date),
            payload={"day": day_index, "title": title},
        )

    week_number = challenge_week_number(session)
    if week_number > 0:
        reflection = WEEKLY_REFLECTIONS[(week_number - 1) % len(WEEKLY_REFLECTIONS)]
        week_start = session.challenge_started_at.date() + timedelta(days=7 * week_number)
        _schedule_reminder(
            db,
            session_id=session.id,
            participant_id=None,
            kind=ReminderKind.weekly_reflection,
            scheduled_for=_at_noon(week_start),
            payload={
                "week": week_number,
                "title": reflection[0],
                "prompt": reflection[1],
            },
        )


async def process_due_reminders(db: DbSession) -> int:
    if not telegram_client.enabled:
        return 0

    now = datetime.utcnow()
    due = (
        db.query(Reminder)
        .filter(Reminder.sent_at.is_(None), Reminder.scheduled_for <= now)
        .order_by(Reminder.scheduled_for)
        .limit(50)
        .all()
    )

    settings = get_settings()
    sent_count = 0

    for reminder in due:
        session = db.get(Session, reminder.session_id)
        if not session or not session.reminders_enabled:
            reminder.sent_at = now
            continue

        recipients = _telegram_recipients(session)
        if not recipients:
            reminder.sent_at = now
            continue

        payload = json.loads(reminder.payload_json or "{}")
        challenge_url = f"{settings.app_base_url}/session/{session.id}/challenge"
        text, button = _build_reminder_message(reminder.kind, payload, session, reminder)

        delivered = False
        for chat_id in recipients:
            ok = await telegram_client.send_message(
                chat_id,
                text,
                button_text=button,
                button_url=challenge_url if button else None,
            )
            delivered = delivered or ok

        if delivered or reminder.kind == ReminderKind.new_year:
            reminder.sent_at = now
            sent_count += 1

    db.commit()
    return sent_count


def _telegram_recipients(session: Session) -> list[int]:
    chat_ids: list[int] = []
    for participant in session.participants:
        if participant.telegram_chat_id:
            chat_ids.append(participant.telegram_chat_id)
    return chat_ids


def _build_reminder_message(
    kind: ReminderKind,
    payload: dict,
    session: Session,
    reminder: Reminder,
) -> tuple[str, str | None]:
    if kind == ReminderKind.birthday:
        return birthday_reminder(payload.get("name", "juftingiz")), None

    if kind == ReminderKind.anniversary:
        years = payload.get("years")
        return anniversary_reminder(years if isinstance(years, int) else None), None

    if kind == ReminderKind.new_year:
        return new_year_reminder(), None

    if kind == ReminderKind.challenge_daily:
        day = int(payload.get("day", 1))
        title = str(payload.get("title", ""))
        if day >= 7 and build_challenge_view(session).completed_count >= 6:
            return challenge_completed_celebration(), "Challenge sahifasini ochish"
        return challenge_daily_nudge(day, title)

    if kind == ReminderKind.weekly_reflection:
        week = int(payload.get("week", 1))
        prompt = str(payload.get("prompt", ""))
        return weekly_reflection_prompt(week, prompt)

    return "💛 Qadam — munosabat uchun kichik eslatma.", None
