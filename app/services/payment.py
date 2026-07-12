import base64
import hashlib
import logging
from datetime import datetime
from urllib.parse import urlencode

from sqlalchemy.orm import Session as DbSession

from app.config import get_settings
from app.constants import PREMIUM_PRICE_UZS
from app.models import PaymentOrder, PaymentProvider, PaymentStatus, Session
from app.services.challenge import start_challenge_if_needed

logger = logging.getLogger(__name__)


class PaymentError(Exception):
    pass


def unlock_premium_session(db: DbSession, session: Session) -> None:
    if session.is_premium_unlocked:
        return
    session.is_premium_unlocked = True
    session.premium_unlocked_at = datetime.utcnow()
    start_challenge_if_needed(session)


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
    if order.status == PaymentStatus.paid:
        session = db.get(Session, order.session_id)
        if not session:
            raise PaymentError("Sessiya topilmadi")
        return session

    order.status = PaymentStatus.paid
    order.paid_at = datetime.utcnow()

    session = db.get(Session, order.session_id)
    if not session:
        raise PaymentError("Sessiya topilmadi")

    unlock_premium_session(db, session)
    return session


def initiate_premium_payment(
    db: DbSession,
    session: Session,
    *,
    viewer_role: str = "user_a",
) -> tuple[str, PaymentOrder | None]:
    if session.is_premium_unlocked:
        return "already_unlocked", None

    settings = get_settings()
    role = "user_b" if viewer_role == "user_b" else "user_a"

    if settings.payment_mode == "demo" or not settings.payme_configured:
        order = create_payment_order(db, session)
        order.status = PaymentStatus.paid
        order.paid_at = datetime.utcnow()
        unlock_premium_session(db, session)
        return "demo_unlocked", order

    order = create_payment_order(db, session)
    checkout_url = build_payme_checkout_url(order, viewer_role=role)
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
