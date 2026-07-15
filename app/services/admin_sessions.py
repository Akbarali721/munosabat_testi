"""Admin views over relationship sessions (list, filters, stats, problems)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session as DbSession, joinedload

from app.models import (
    Answer,
    Participant,
    ParticipantRole,
    PaymentOrder,
    PaymentStatus,
    PremiumPaymentStatus,
    RelationshipEvent,
    Session,
    SessionStatus,
)
from app.services.invite_share import build_partner_deep_link
from app.services.payment import premium_access_granted
from app.constants import PREMIUM_PRICE_UZS, STAGE_LABELS


EVENT_LABELS: dict[str, str] = {
    "session_created": "Sessiya yaratildi",
    "initiator_test_started": "User1 testni boshladi",
    "initiator_test_completed": "User1 testni tugatdi",
    "invite_token_created": "Taklif tokeni yaratildi",
    "partner_share_message_created": "Bot User1 ga yuborish tugmasini jo‘natdi",
    "share_message_sent_to_initiator": "Bot User1 ga yuborish tugmasini jo‘natdi",
    "partner_share_message_failed": "Bot notification yuborilmadi",
    "partner_share_message_skipped_no_telegram": "Bot notification o‘tkazib yuborildi (Telegram ID yo‘q)",
    "partner_deeplink_opened": "User2 deep-linkni ochdi",
    "partner_attached_to_session": "Sherik sessiyaga biriktirildi",
    "partner_attached": "Sherik sessiyaga biriktirildi",
    "partner_test_started": "User2 testni boshladi",
    "partner_test_completed": "User2 testni tugatdi",
    "relationship_result_generated": "Umumiy natija yaratildi",
    "result_generated": "Umumiy natija yaratildi",
    "initiator_result_notified": "Natija User1 ga yuborildi",
    "result_sent_to_initiator": "Natija User1 ga yuborildi",
    "admin_action": "Admin amali",
    "admin_resend_share": "Admin: share xabarini qayta yubordi",
    "admin_resend_result": "Admin: natijani qayta yubordi",
    "admin_revoke_token": "Admin: taklif tokenini bekor qildi",
    "admin_regenerate_token": "Admin: yangi token yaratdi",
    "admin_cancel_session": "Admin: sessiyani bekor qildi",
    "admin_premium_approved": "Admin: premiumni tasdiqladi",
    "admin_premium_rejected": "Admin: to‘lovni rad etdi",
    "admin_premium_reblocked": "Admin: premiumni qayta blokladi",
    "premium_requested": "Premium so‘rovi yuborildi",
    "premium_payment_received": "Premium to‘lov qabul qilindi",
}


ADMIN_STATUS_MAP = {
    SessionStatus.awaiting_user_b: "waiting_for_partner",
    SessionStatus.awaiting_user_b_answers: "partner_in_progress",
    SessionStatus.complete: "completed",
    SessionStatus.cancelled: "cancelled",
}

STATUS_LABELS = {
    "initiator_in_progress": "User1 jarayonda",
    "waiting_for_partner": "Sherik kutilyapti",
    "partner_in_progress": "User2 jarayonda",
    "completed": "Tugallangan",
    "cancelled": "Bekor qilingan",
    "expired": "Muddati o‘tgan",
}


def mask_token(token: str | None) -> str:
    if not token:
        return "—"
    if len(token) <= 10:
        return token
    return f"{token[:6]}…{token[-4:]}"


def format_username(username: str | None) -> str:
    if not username:
        return "Username mavjud emas"
    return f"@{username.lstrip('@')}"


def display_status(session: Session, user_a: Participant | None) -> str:
    if session.status == SessionStatus.cancelled:
        return "cancelled"
    if session.status == SessionStatus.complete:
        return "completed"
    if session.status == SessionStatus.awaiting_user_b_answers:
        return "partner_in_progress"
    if session.status == SessionStatus.awaiting_user_b:
        if user_a and user_a.completed_at:
            return "waiting_for_partner"
        return "initiator_in_progress"
    return session.status.value


def share_state_label(session: Session) -> str:
    if session.partner_telegram_id or session.partner_started_at:
        return "Taklif ochildi / sherik biriktirildi"
    if session.initiator_share_notified_at:
        return "Yuborishga tayyor (share xabar yuborilgan)"
    if session.invite_token and not session.invite_revoked_at:
        return "Taklif yaratildi"
    return "Token yo‘q"


def user2_state_label(session: Session, user_b: Participant | None) -> str:
    if user_b and user_b.completed_at:
        return "Tugatgan"
    if session.partner_started_at or (user_b and user_b.telegram_chat_id):
        if user_b and user_b.name and user_b.name != "__pending__":
            return "Boshlagan"
        return "Ochgan"
    return "Ochmagan"


@dataclass
class SessionProblem:
    code: str
    label: str


def detect_problems(
    session: Session,
    user_a: Participant | None,
    user_b: Participant | None,
    *,
    answer_count_a: int = 0,
    answer_count_b: int = 0,
) -> list[SessionProblem]:
    problems: list[SessionProblem] = []
    if user_a and user_a.completed_at and not session.initiator_share_notified_at:
        problems.append(
            SessionProblem("no_share_notify", "User1 tugatgan, lekin bot notification yuborilmagan")
        )
    if user_a and user_a.completed_at and not session.invite_token:
        problems.append(SessionProblem("no_token", "User1 tugatgan, ammo invite token yo‘q"))
    if session.partner_started_at and not session.partner_telegram_id:
        problems.append(
            SessionProblem("open_not_bound", "User2 linkni ochgan, lekin Telegram ID biriktirilmagan")
        )
    if user_b and user_b.completed_at and session.status != SessionStatus.complete:
        problems.append(
            SessionProblem(
                "partner_done_not_complete",
                "User2 tugatgan, lekin sessiya completed emas",
            )
        )
    if (
        user_a
        and user_b
        and user_a.completed_at
        and user_b.completed_at
        and session.status == SessionStatus.complete
        and not (user_a.result_notified_at)
    ):
        problems.append(
            SessionProblem(
                "result_not_sent",
                "Natija yaratilgan, ammo User1 ga yuborilmagan",
            )
        )
    return problems


@dataclass
class AdminSessionRow:
    session: Session
    user_a: Participant | None
    user_b: Participant | None
    admin_status: str
    status_label: str
    share_state: str
    user2_state: str
    pair_label: str
    token_masked: str
    problems: list[SessionProblem] = field(default_factory=list)
    is_problem: bool = False


def _pair_label(user_a: Participant | None, user_b: Participant | None, session: Session) -> str:
    left = (user_a.name if user_a else "User1")
    left_u = format_username(user_a.telegram_username if user_a else None)
    if left_u != "Username mavjud emas":
        left = f"{left} ({left_u})"
    if session.partner_telegram_id and user_b and user_b.name and user_b.name != "__pending__":
        right = user_b.name
        right_u = format_username(user_b.telegram_username)
        if right_u != "Username mavjud emas":
            right = f"{right} ({right_u})"
        return f"{left} → {right}"
    return f"{left} → Hali noma’lum"


def build_admin_row(session: Session) -> AdminSessionRow:
    user_a = next((p for p in session.participants if p.role == ParticipantRole.user_a), None)
    user_b = next((p for p in session.participants if p.role == ParticipantRole.user_b), None)
    admin_status = display_status(session, user_a)
    problems = detect_problems(session, user_a, user_b)
    return AdminSessionRow(
        session=session,
        user_a=user_a,
        user_b=user_b,
        admin_status=admin_status,
        status_label=STATUS_LABELS.get(admin_status, admin_status),
        share_state=share_state_label(session),
        user2_state=user2_state_label(session, user_b),
        pair_label=_pair_label(user_a, user_b, session),
        token_masked=mask_token(session.invite_token),
        problems=problems,
        is_problem=bool(problems),
    )


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def list_sessions(
    db: DbSession,
    *,
    status: str | None = None,
    quick: str | None = None,
    q: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    initiator_tg: str | None = None,
    partner_tg: str | None = None,
    only_problems: bool = False,
    limit: int = 200,
) -> list[AdminSessionRow]:
    query = (
        db.query(Session)
        .options(joinedload(Session.participants))
        .order_by(Session.created_at.desc())
    )

    df = _parse_date(date_from)
    dt = _parse_date(date_to)
    if df:
        query = query.filter(Session.created_at >= datetime.combine(df, datetime.min.time()))
    if dt:
        query = query.filter(Session.created_at <= datetime.combine(dt, datetime.max.time()))

    if quick == "today":
        today = date.today()
        query = query.filter(Session.created_at >= datetime.combine(today, datetime.min.time()))
    elif quick == "7d":
        query = query.filter(Session.created_at >= datetime.utcnow() - timedelta(days=7))
    elif quick == "waiting":
        query = query.filter(Session.status == SessionStatus.awaiting_user_b)
    elif quick == "in_progress":
        query = query.filter(Session.status == SessionStatus.awaiting_user_b_answers)
    elif quick == "completed":
        query = query.filter(Session.status == SessionStatus.complete)

    if status == "waiting_for_partner":
        query = query.filter(Session.status == SessionStatus.awaiting_user_b)
    elif status == "partner_in_progress":
        query = query.filter(Session.status == SessionStatus.awaiting_user_b_answers)
    elif status == "completed":
        query = query.filter(Session.status == SessionStatus.complete)
    elif status == "cancelled":
        query = query.filter(Session.status == SessionStatus.cancelled)
    elif status == "initiator_in_progress":
        # awaiting partner but initiator not completed — rare for create-then-answer flow
        query = query.filter(Session.status == SessionStatus.awaiting_user_b)

    if initiator_tg and initiator_tg.strip().isdigit():
        query = query.filter(Session.initiator_telegram_id == int(initiator_tg.strip()))
    if partner_tg and partner_tg.strip().isdigit():
        query = query.filter(Session.partner_telegram_id == int(partner_tg.strip()))

    if q and q.strip():
        term = f"%{q.strip().lstrip('@')}%"
        query = (
            query.join(Participant, Participant.session_id == Session.id)
            .filter(
                or_(
                    Participant.name.ilike(term),
                    Participant.telegram_username.ilike(term),
                    Session.id.ilike(term),
                    Session.invite_token.ilike(term),
                )
            )
            .distinct()
        )

    sessions = query.limit(limit).all()
    rows = [build_admin_row(s) for s in sessions]
    if only_problems or quick == "problems":
        rows = [r for r in rows if r.is_problem]
    return rows


def compute_stats(db: DbSession) -> dict[str, Any]:
    today = datetime.combine(date.today(), datetime.min.time())
    created_today = (
        db.query(func.count(Session.id)).filter(Session.created_at >= today).scalar() or 0
    )
    initiator_done = (
        db.query(func.count(Participant.id))
        .filter(
            Participant.role == ParticipantRole.user_a,
            Participant.completed_at.isnot(None),
        )
        .scalar()
        or 0
    )
    share_ready = (
        db.query(func.count(Session.id))
        .filter(Session.initiator_share_notified_at.isnot(None))
        .scalar()
        or 0
    )
    partner_opened = (
        db.query(func.count(Session.id))
        .filter(
            or_(
                Session.partner_started_at.isnot(None),
                Session.partner_telegram_id.isnot(None),
            )
        )
        .scalar()
        or 0
    )
    partner_done = (
        db.query(func.count(Participant.id))
        .filter(
            Participant.role == ParticipantRole.user_b,
            Participant.completed_at.isnot(None),
        )
        .scalar()
        or 0
    )
    completed = (
        db.query(func.count(Session.id))
        .filter(Session.status == SessionStatus.complete)
        .scalar()
        or 0
    )
    premium = (
        db.query(func.count(Session.id))
        .filter(
            Session.is_premium_unlocked.is_(True),
            Session.premium_payment_status == PremiumPaymentStatus.approved,
        )
        .scalar()
        or 0
    )

    def pct(num: int, den: int) -> float:
        if den <= 0:
            return 0.0
        return round(100.0 * num / den, 1)

    return {
        "created_today": created_today,
        "initiator_done": initiator_done,
        "share_ready": share_ready,
        "partner_opened": partner_opened,
        "partner_done": partner_done,
        "completed": completed,
        "premium": premium,
        "conv_open": pct(partner_opened, initiator_done),
        "conv_partner_complete": pct(partner_done, partner_opened),
        "conv_full": pct(completed, initiator_done),
    }


def get_session_detail(db: DbSession, session_id: str) -> dict[str, Any] | None:
    session = (
        db.query(Session)
        .options(joinedload(Session.participants), joinedload(Session.payment_orders))
        .filter(Session.id == session_id)
        .first()
    )
    if not session:
        return None

    user_a = next((p for p in session.participants if p.role == ParticipantRole.user_a), None)
    user_b = next((p for p in session.participants if p.role == ParticipantRole.user_b), None)
    row = build_admin_row(session)

    def answer_count(participant: Participant | None) -> int:
        if not participant:
            return 0
        return (
            db.query(func.count(Answer.id))
            .filter(Answer.participant_id == participant.id)
            .scalar()
            or 0
        )

    events = (
        db.query(RelationshipEvent)
        .filter(RelationshipEvent.session_id == session_id)
        .order_by(RelationshipEvent.created_at.asc())
        .all()
    )
    timeline = []
    for ev in events:
        timeline.append(
            {
                "at": ev.created_at,
                "type": ev.event_type,
                "label": EVENT_LABELS.get(ev.event_type, ev.event_type),
                "telegram_id": ev.telegram_id,
                "payload": ev.payload,
            }
        )

    # Synthesize missing early timeline points from fields
    if user_a and session.created_at:
        timeline.insert(
            0,
            {
                "at": session.created_at,
                "type": "session_created",
                "label": EVENT_LABELS["session_created"],
                "telegram_id": session.initiator_telegram_id,
                "payload": "",
            },
        )

    timeline.sort(key=lambda x: x["at"] or datetime.min)

    paid = any(o.status == PaymentStatus.paid for o in session.payment_orders)
    deep_link = (
        build_partner_deep_link(session.invite_token)
        if session.invite_token and not session.invite_revoked_at
        else None
    )

    return {
        "row": row,
        "session": session,
        "user_a": user_a,
        "user_b": user_b,
        "answers_a": answer_count(user_a),
        "answers_b": answer_count(user_b),
        "timeline": timeline,
        "deep_link": deep_link,
        "premium_unlocked": premium_access_granted(session),
        "premium_payment_status": getattr(
            session.premium_payment_status, "value", session.premium_payment_status
        ),
        "payment_paid": paid,
        "result_ready": session.status == SessionStatus.complete,
        "result_sent_user1": bool(user_a and user_a.result_notified_at),
        "result_sent_user2": bool(user_b and user_b.result_notified_at),
    }


@dataclass
class PremiumPaymentRow:
    session: Session
    user_name: str
    telegram_id: int | None
    test_type: str
    amount_uzs: int
    created_at: datetime | None
    payment_status: str
    receipt_url: str | None
    receipt_label: str
    order: PaymentOrder | None
    premium_access: bool


def _latest_order(session: Session) -> PaymentOrder | None:
    orders = list(session.payment_orders or [])
    if not orders:
        return None
    return max(orders, key=lambda o: o.created_at or datetime.min)


def _receipt_info(order: PaymentOrder | None) -> tuple[str | None, str]:
    if not order:
        return None, "Chek yo‘q"
    ext = (order.external_id or "").strip()
    if ext.startswith("http://") or ext.startswith("https://"):
        return ext, "Chekni ochish"
    if ext:
        return None, f"Tashqi ID: {ext}"
    return None, "Chek yo‘q"


def build_premium_payment_row(session: Session) -> PremiumPaymentRow:
    user_a = next(
        (p for p in session.participants if p.role == ParticipantRole.user_a),
        None,
    )
    order = _latest_order(session)
    status = getattr(session.premium_payment_status, "value", session.premium_payment_status) or "pending"
    receipt_url, receipt_label = _receipt_info(order)
    created = None
    if order and order.created_at:
        created = order.created_at
    elif session.premium_unlocked_at:
        created = session.premium_unlocked_at
    else:
        created = session.created_at
    tg_id = session.initiator_telegram_id
    if tg_id is None and user_a is not None:
        tg_id = user_a.telegram_chat_id
    return PremiumPaymentRow(
        session=session,
        user_name=(user_a.name if user_a and user_a.name else "Noma’lum"),
        telegram_id=tg_id,
        test_type=STAGE_LABELS.get(session.relationship_stage, str(session.relationship_stage)),
        amount_uzs=order.amount_uzs if order else PREMIUM_PRICE_UZS,
        created_at=created,
        payment_status=str(status),
        receipt_url=receipt_url,
        receipt_label=receipt_label,
        order=order,
        premium_access=premium_access_granted(session),
    )


def list_premium_payments(db: DbSession) -> dict[str, list[PremiumPaymentRow]]:
    """Pending first for approval queue; approved separate for history."""
    sessions = (
        db.query(Session)
        .options(joinedload(Session.participants), joinedload(Session.payment_orders))
        .filter(
            or_(
                Session.premium_payment_status == PremiumPaymentStatus.pending,
                Session.premium_payment_status == PremiumPaymentStatus.approved,
                Session.premium_payment_status == PremiumPaymentStatus.rejected,
                Session.is_premium_unlocked.is_(True),
            )
        )
        .order_by(Session.created_at.desc())
        .all()
    )

    pending: list[PremiumPaymentRow] = []
    approved: list[PremiumPaymentRow] = []
    rejected: list[PremiumPaymentRow] = []

    for session in sessions:
        # Only show rows that are relevant to premium payment workflow
        has_order = bool(session.payment_orders)
        status = session.premium_payment_status
        if status == PremiumPaymentStatus.pending and not has_order and not session.is_premium_unlocked:
            # Skip untouched complete sessions that never requested premium
            continue
        row = build_premium_payment_row(session)
        if row.premium_access or status == PremiumPaymentStatus.approved:
            approved.append(row)
        elif status == PremiumPaymentStatus.rejected:
            rejected.append(row)
        elif status == PremiumPaymentStatus.pending or has_order:
            pending.append(row)

    def sort_key(r: PremiumPaymentRow):
        return r.created_at or datetime.min

    pending.sort(key=sort_key, reverse=True)
    approved.sort(key=sort_key, reverse=True)
    rejected.sort(key=sort_key, reverse=True)
    return {"pending": pending, "approved": approved, "rejected": rejected}
