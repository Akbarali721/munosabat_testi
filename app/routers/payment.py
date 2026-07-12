import logging

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session as DbSession

from app.config import get_settings
from app.database import get_db
from app.models import PaymentOrder, PaymentStatus
from app.services.payment import (
    PaymentError,
    complete_payment_order,
    get_order_for_session,
    initiate_premium_payment,
    verify_payme_callback,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/session/{session_id}/premium/unlock")
def premium_unlock(
    session_id: str,
    role: str = Form("user_a"),
    db: DbSession = Depends(get_db),
):
    from app.routers.pages import _require_complete_session

    session, _, _ = _require_complete_session(db, session_id)
    viewer_role = "user_b" if role == "user_b" else "user_a"
    result_url = f"/session/{session_id}/result?role={viewer_role}&opened=1"

    if session.is_premium_unlocked:
        return RedirectResponse(url=result_url, status_code=303)

    try:
        result, order = initiate_premium_payment(db, session, viewer_role=viewer_role)
    except PaymentError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if result == "already_unlocked":
        return RedirectResponse(url=result_url, status_code=303)

    if result == "demo_unlocked":
        from app.services.retention import schedule_challenge_reminders, schedule_session_reminders

        schedule_session_reminders(db, session)
        schedule_challenge_reminders(db, session)
        db.commit()
        return RedirectResponse(url=result_url, status_code=303)

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
        from app.services.retention import schedule_challenge_reminders, schedule_session_reminders

        session = order.session
        schedule_session_reminders(db, session)
        schedule_challenge_reminders(db, session)
        db.commit()

    viewer_role = "user_b" if role == "user_b" else "user_a"
    return RedirectResponse(
        url=f"/session/{session_id}/result?role={viewer_role}&opened=1",
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
