from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session as DbSession

from app.database import get_db
from app.routers.pages import _require_complete_session
from app.services.challenge import build_challenge_view, mark_day_complete, start_challenge_if_needed
from app.services.payment import payment_page_url, premium_access_granted
from app.services.retention import schedule_challenge_reminders
from app.ui import random_footer_quote

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))


def _render(request: Request, template_name: str, context: dict | None = None):
    context = dict(context) if context else {}
    context["request"] = request
    context.setdefault("footer_quote", random_footer_quote())
    return templates.TemplateResponse(template_name, context)


@router.get("/session/{session_id}/challenge", response_class=HTMLResponse)
def challenge_page(
    request: Request,
    session_id: str,
    db: DbSession = Depends(get_db),
):
    session, user_a, user_b = _require_complete_session(db, session_id)

    if not premium_access_granted(session):
        return RedirectResponse(
            url=payment_page_url(session_id),
            status_code=302,
        )

    start_challenge_if_needed(session)
    db.commit()

    challenge = build_challenge_view(session)

    return _render(
        request,
        "challenge.html",
        {
            "title": "7 kunlik Challenge",
            "session": session,
            "user_a": user_a,
            "user_b": user_b,
            "challenge": challenge,
        },
    )


@router.post("/session/{session_id}/challenge/complete")
def complete_challenge_day(
    session_id: str,
    day: int = Form(...),
    db: DbSession = Depends(get_db),
):
    session, _, _ = _require_complete_session(db, session_id)

    if not premium_access_granted(session):
        raise HTTPException(status_code=403, detail="Premium ochilmagan")

    if not mark_day_complete(session, day):
        raise HTTPException(status_code=400, detail="Bu kun hali ochilmagan")

    schedule_challenge_reminders(db, session)
    db.commit()

    return RedirectResponse(url=f"/session/{session_id}/challenge", status_code=303)
