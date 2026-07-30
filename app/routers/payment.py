import logging

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlalchemy.orm import Session as DbSession

from app.config import get_settings
from app.constants import PREMIUM_PRICE_UZS, premium_price_label
from app.database import get_db
from app.models import PaymentOrder, PaymentStatus
from app.services.payment import (
    PaymentError,
    complete_payment_order,
    get_order_for_session,
    initiate_premium_payment,
    payment_page_url,
    premium_access_granted,
    verify_payme_callback,
)
from app.ui import random_footer_quote

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))


def _render_payment_page(request: Request, session, *, role: str, order: PaymentOrder | None = None):
    settings = get_settings()
    granted = premium_access_granted(session)
    return templates.TemplateResponse(
        "premium_payment.html",
        {
            "request": request,
            "title": "Premium to‘lov",
            "session": session,
            "premium_price": PREMIUM_PRICE_UZS,
            "premium_price_label": premium_price_label(
                order.amount_uzs if order else None
            ),
            "viewer_role": role,
            "payment_demo": settings.payment_demo,
            "premium_granted": granted,
            "payment_status": getattr(session, "premium_payment_status", None),
            "latest_order": order,
            "footer_quote": random_footer_quote(),
        },
    )


@router.get("/session/{session_id}/premium/payment", response_class=HTMLResponse)
@router.get("/love/session/{session_id}/premium/payment", response_class=HTMLResponse)
def premium_payment_page(
    request: Request,
    session_id: str,
    role: str = "user_a",
    db: DbSession = Depends(get_db),
):
    from app.routers.pages import _require_complete_session

    session, _, _ = _require_complete_session(db, session_id)
    viewer_role = "user_b" if role == "user_b" else "user_a"

    if premium_access_granted(session):
        return RedirectResponse(
            url=f"/session/{session_id}/premium?role={viewer_role}",
            status_code=303,
        )

    latest = (
        db.query(PaymentOrder)
        .filter(PaymentOrder.session_id == session_id)
        .order_by(PaymentOrder.created_at.desc())
        .first()
    )
    return _render_payment_page(request, session, role=viewer_role, order=latest)


@router.post("/session/{session_id}/premium/unlock")
@router.post("/love/session/{session_id}/premium/unlock")
def premium_unlock(
    session_id: str,
    role: str = Form("user_a"),
    db: DbSession = Depends(get_db),
):
    """
    Start purchase request. Never unlocks premium by itself.
    Demo mode creates a pending order awaiting admin approval.
    """
    from app.routers.pages import _require_complete_session

    session, _, _ = _require_complete_session(db, session_id)
    viewer_role = "user_b" if role == "user_b" else "user_a"

    if premium_access_granted(session):
        return RedirectResponse(
            url=f"/session/{session_id}/premium?role={viewer_role}",
            status_code=303,
        )

    try:
        result, _order = initiate_premium_payment(db, session, viewer_role=viewer_role)
    except PaymentError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    db.commit()

    if result == "already_unlocked":
        return RedirectResponse(
            url=f"/session/{session_id}/premium?role={viewer_role}",
            status_code=303,
        )

    if result == "pending_admin":
        return RedirectResponse(
            url=payment_page_url(session_id, role=viewer_role) + "&requested=1",
            status_code=303,
        )

    # Payme checkout URL
    return RedirectResponse(url=result, status_code=303)


@router.get("/session/{session_id}/payment/return")
def payment_return(
    session_id: str,
    order_id: str,
    role: str = "user_a",
    db: DbSession = Depends(get_db),
):
    order = get_order_for_session(db, session_id, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Buyurtma topilmadi")

    if order.status != PaymentStatus.paid:
        complete_payment_order(db, order)
        db.commit()

    viewer_role = "user_b" if role == "user_b" else "user_a"
    # Still requires admin approval for premium content
    return RedirectResponse(
        url=payment_page_url(session_id, role=viewer_role) + "&paid=1",
        status_code=303,
    )


@router.post("/payment/payme/callback")
async def payme_callback(request: Request, db: DbSession = Depends(get_db)):
    payload = await request.json()
    if not verify_payme_callback(payload):
        raise HTTPException(status_code=403, detail="Noto‘g‘ri imzo")

    params = payload.get("params") or {}
    order_id = params.get("account", {}).get("order_id")
    if not order_id:
        raise HTTPException(status_code=400, detail="Buyurtma ID yo‘q")

    order = db.get(PaymentOrder, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Buyurtma topilmadi")

    complete_payment_order(db, order)
    db.commit()
    return {"result": {"state": 2}}
