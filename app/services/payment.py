import base64
import hashlib
import logging
from datetime import datetime
from urllib.parse import urlencode

from sqlalchemy.orm import Session as DbSession

from app.config import get_settings
from app.constants import PREMIUM_PRICE_UZS
from app.models import (
    PaymentOrder,
    PaymentProvider,
    PaymentStatus,
    PremiumPaymentStatus,
    Session,
)
from app.services.challenge import start_challenge_if_needed
from app.services.events import log_relationship_event

logger = logging.getLogger(__name__)


class PaymentError(Exception):
    pass


def premium_access_granted(session: Session) -> bool:
    """Backend gate: premium content only when unlocked AND payment approved."""
    if not bool(getattr(session, "is_premium_unlocked", False)):
        return False
    status = getattr(session, "premium_payment_status", None)
    if status is None:
        return False
    if isinstance(status, PremiumPaymentStatus):
        return status == PremiumPaymentStatus.approved
    return str(status) == PremiumPaymentStatus.approved.value


def unlock_premium_session(db: DbSession, session: Session) -> None:
    """Mark premium open. Prefer admin approve path for product flow."""
    session.is_premium_unlocked = True
    session.premium_unlocked_at = datetime.utcnow()
    session.premium_payment_status = PremiumPaymentStatus.approved
    start_challenge_if_needed(session)


def lock_premium_session(session: Session, *, status: PremiumPaymentStatus) -> None:
    session.is_premium_unlocked = False
    session.premium_unlocked_at = None
    session.premium_payment_status = status


def approve_premium(db: DbSession, session: Session, *, actor: str = "admin") -> None:
    unlock_premium_session(db, session)
    # Mark latest pending order paid if any
    pending = (
        db.query(PaymentOrder)
        .filter(
            PaymentOrder.session_id == session.id,
            PaymentOrder.status == PaymentStatus.pending,
        )
        .order_by(PaymentOrder.created_at.desc())
        .first()
    )
    if pending:
        pending.status = PaymentStatus.paid
        pending.paid_at = datetime.utcnow()
    log_relationship_event(
        db,
        session_id=session.id,
        event_type="admin_premium_approved",
        payload=actor,
    )


def reject_premium(db: DbSession, session: Session, *, actor: str = "admin") -> None:
    lock_premium_session(session, status=PremiumPaymentStatus.rejected)
    pending = (
        db.query(PaymentOrder)
        .filter(
            PaymentOrder.session_id == session.id,
            PaymentOrder.status == PaymentStatus.pending,
        )
        .order_by(PaymentOrder.created_at.desc())
        .all()
    )
    for order in pending:
        order.status = PaymentStatus.failed
    log_relationship_event(
        db,
        session_id=session.id,
        event_type="admin_premium_rejected",
        payload=actor,
    )


def reblock_premium(db: DbSession, session: Session, *, actor: str = "admin") -> None:
    lock_premium_session(session, status=PremiumPaymentStatus.pending)
    log_relationship_event(
        db,
        session_id=session.id,
        event_type="admin_premium_reblocked",
        payload=actor,
    )


def create_payment_order(db: DbSession, session: Session) -> PaymentOrder:
    settings = get_settings()
    provider = (
        PaymentProvider.payme
        if settings.payment_mode == "payme" and settings.payme_configured
        else PaymentProvider.demo
    )

    order = PaymentOrder(
        session_id=session.id,
        amount_uzs=PREMIUM_PRICE_UZS,
        status=PaymentStatus.pending,
        provider=provider,
    )
    db.add(order)
    db.flush()
    return order


def complete_payment_order(db: DbSession, order: PaymentOrder) -> Session:
    """
    Mark provider order as paid. Does NOT unlock premium —
    admin approval (or explicit unlock) is required.
    """
    session = db.get(Session, order.session_id)
    if not session:
        raise PaymentError("Sessiya topilmadi")

    if order.status != PaymentStatus.paid:
        order.status = PaymentStatus.paid
        order.paid_at = datetime.utcnow()

    if session.premium_payment_status != PremiumPaymentStatus.approved:
        session.premium_payment_status = PremiumPaymentStatus.pending

    log_relationship_event(
        db,
        session_id=session.id,
        event_type="premium_payment_received",
        payload=f"order={order.id}",
    )
    return session


def initiate_premium_payment(
    db: DbSession,
    session: Session,
    *,
    viewer_role: str = "user_a",
) -> tuple[str, PaymentOrder | None]:
    """
    Start premium purchase.
    Never auto-unlocks. Returns:
      - ("already_unlocked", None)
      - ("pending_admin", order) for demo / manual admin approval
      - (checkout_url, order) for Payme redirect
    """
    if premium_access_granted(session):
        return "already_unlocked", None

    settings = get_settings()
    role = "user_b" if viewer_role == "user_b" else "user_a"

    # Ensure session is marked as awaiting approval
    if session.premium_payment_status != PremiumPaymentStatus.approved:
        session.premium_payment_status = PremiumPaymentStatus.pending
        session.is_premium_unlocked = False

    if settings.payment_mode == "demo" or not settings.payme_configured:
        order = create_payment_order(db, session)
        log_relationship_event(
            db,
            session_id=session.id,
            event_type="premium_requested",
            payload=f"demo_order={order.id}",
        )
        return "pending_admin", order

    order = create_payment_order(db, session)
    checkout_url = build_payme_checkout_url(order, viewer_role=role)
    log_relationship_event(
        db,
        session_id=session.id,
        event_type="premium_requested",
        payload=f"payme_order={order.id}",
    )
    return checkout_url, order


def build_payme_checkout_url(order: PaymentOrder, *, viewer_role: str = "user_a") -> str:
    settings = get_settings()
    if not settings.payme_merchant_id:
        raise PaymentError("Payme sozlanmagan")

    amount_tiyin = order.amount_uzs * 100
    role = "user_b" if viewer_role == "user_b" else "user_a"
    params = {
        "m": settings.payme_merchant_id,
        "ac.order_id": order.id,
        "a": amount_tiyin,
        "c": (
            f"{settings.app_base_url}/session/{order.session_id}/payment/return"
            f"?order_id={order.id}&role={role}"
        ),
    }
    encoded = base64.b64encode(urlencode(params).encode("utf-8")).decode("utf-8")
    order.external_id = order.id
    return f"https://checkout.paycom.uz/{encoded}"


def verify_payme_callback(payload: dict) -> bool:
    settings = get_settings()
    if not settings.payme_secret_key:
        return False

    method = payload.get("method")
    if method != "PerformTransaction":
        return True

    params = payload.get("params") or {}
    order_id = params.get("account", {}).get("order_id")
    if not order_id:
        return False

    signature = payload.get("sign")
    if not signature:
        return False

    raw = f"{order_id}{params.get('amount', '')}{settings.payme_secret_key}"
    expected = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return signature == expected


def get_order_for_session(db: DbSession, session_id: str, order_id: str) -> PaymentOrder | None:
    return (
        db.query(PaymentOrder)
        .filter(PaymentOrder.id == order_id, PaymentOrder.session_id == session_id)
        .first()
    )


def payment_page_url(session_id: str, *, role: str = "user_a") -> str:
    return f"/session/{session_id}/premium/payment?role={role}"


def love_payment_page_url(session_id: str, *, role: str = "user_a") -> str:
    return f"/love/session/{session_id}/premium/payment?role={role}"
