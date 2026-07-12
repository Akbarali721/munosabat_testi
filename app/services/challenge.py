import json
from dataclasses import dataclass
from datetime import datetime

from app.constants import SEVEN_DAY_EXERCISES, WEEKLY_REFLECTIONS
from app.models import Session


@dataclass
class ChallengeDayView:
    day: int
    title: str
    text: str
    completed: bool
    is_today: bool
    is_locked: bool


@dataclass
class ChallengeView:
    current_day: int
    days: list[ChallengeDayView]
    completed_count: int
    total_days: int
    is_complete: bool
    week_number: int
    weekly_prompt: str | None
    weekly_prompt_title: str | None


def _load_progress(session: Session) -> dict[str, bool]:
    try:
        raw = json.loads(session.challenge_progress_json or "{}")
    except json.JSONDecodeError:
        return {}
    return {str(key): bool(value) for key, value in raw.items()}


def _save_progress(session: Session, progress: dict[str, bool]) -> None:
    session.challenge_progress_json = json.dumps(progress)


def current_challenge_day(session: Session) -> int:
    if not session.challenge_started_at:
        return 1
    elapsed = (datetime.utcnow().date() - session.challenge_started_at.date()).days
    return min(max(elapsed + 1, 1), 7)


def challenge_week_number(session: Session) -> int:
    if not session.challenge_started_at:
        return 0
    elapsed_days = (datetime.utcnow().date() - session.challenge_started_at.date()).days
    if elapsed_days < 7:
        return 0
    return (elapsed_days // 7)


def start_challenge_if_needed(session: Session) -> None:
    if session.challenge_started_at:
        return
    session.challenge_started_at = datetime.utcnow()
    if not session.challenge_progress_json:
        session.challenge_progress_json = "{}"


def build_challenge_view(session: Session) -> ChallengeView:
    progress = _load_progress(session)
    current = current_challenge_day(session)
    days: list[ChallengeDayView] = []

    for index, (title, text) in enumerate(SEVEN_DAY_EXERCISES, start=1):
        completed = progress.get(str(index), False)
        days.append(
            ChallengeDayView(
                day=index,
                title=title,
                text=text,
                completed=completed,
                is_today=index == current and not completed,
                is_locked=index > current,
            )
        )

    completed_count = sum(1 for day in days if day.completed)
    week_number = challenge_week_number(session)
    weekly_prompt = None
    weekly_prompt_title = None

    if week_number > 0 and WEEKLY_REFLECTIONS:
        reflection = WEEKLY_REFLECTIONS[(week_number - 1) % len(WEEKLY_REFLECTIONS)]
        weekly_prompt_title = reflection[0]
        weekly_prompt = reflection[1]

    return ChallengeView(
        current_day=current,
        days=days,
        completed_count=completed_count,
        total_days=len(SEVEN_DAY_EXERCISES),
        is_complete=completed_count >= len(SEVEN_DAY_EXERCISES),
        week_number=week_number,
        weekly_prompt=weekly_prompt,
        weekly_prompt_title=weekly_prompt_title,
    )


def mark_day_complete(session: Session, day: int) -> bool:
    if day < 1 or day > len(SEVEN_DAY_EXERCISES):
        return False

    current = current_challenge_day(session)
    if day > current:
        return False

    progress = _load_progress(session)
    progress[str(day)] = True
    _save_progress(session, progress)
    return True
