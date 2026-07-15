"""Admin panel: relationship sessions monitoring."""

from __future__ import annotations

import hmac
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session as DbSession

from app.config import get_settings
from app.database import get_db
from app.models import Session, SessionStatus
from app.services.admin_sessions import (
    STATUS_LABELS,
    compute_stats,
    get_session_detail,
    list_premium_payments,
    list_sessions,
    mask_token,
)
from app.services.events import log_relationship_event
from app.services.invite_token import ensure_invite_token, revoke_invite_token
from app.services.notifications import (
    notify_initiator_answers_saved,
    send_result_notifications,
)
from app.services.payment import approve_premium, reject_premium, reblock_premium

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))

ADMIN_COOKIE = "qadam_admin"


def _admin_configured() -> bool:
    return bool(get_settings().admin_secret)


def _is_admin(request: Request) -> bool:
    secret = get_settings().admin_secret
    if not secret:
        return False
    cookie = request.cookies.get(ADMIN_COOKIE, "")
    return hmac.compare_digest(cookie, secret)


def _require_admin(request: Request) -> None:
    if not _admin_configured():
        raise HTTPException(
            status_code=503,
            detail="ADMIN_SECRET (yoki CRON_SECRET) sozlanmagan",
        )
    if not _is_admin(request):
        raise HTTPException(status_code=303, detail="login", headers={"Location": "/admin/login"})


def _admin_token_from_request(request: Request, form: dict | None = None) -> str:
    if form:
        for key in ("admin_token", "token"):
            val = form.get(key)
            if val:
                text = str(val).strip()
                if text:
                    return text
    return (
        request.query_params.get("admin_token")
        or request.query_params.get("token")
        or ""
    ).strip()


def _with_admin_token(url: str, token: str) -> str:
    if not token:
        return url
    from urllib.parse import quote

    qs = f"admin_token={quote(token)}"
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}{qs}"


def _preserve_admin_token(request: Request, url: str, form: dict | None = None) -> str:
    return _with_admin_token(url, _admin_token_from_request(request, form))


def _safe_admin_next(raw: str | None) -> str | None:
    if not raw:
        return None
    candidate = str(raw).strip()
    if not candidate.startswith("/admin"):
        return None
    if candidate.startswith("//"):
        return None
    return candidate


def _redirect_after_premium_action(
    request: Request,
    session_id: str,
    *,
    msg: str | None = None,
    next_url: str | None = None,
    form: dict | None = None,
):
    token = _admin_token_from_request(request, form)
    target = _safe_admin_next(next_url)
    if target:
        if msg:
            sep = "&" if "?" in target else "?"
            target = f"{target}{sep}msg={msg}"
        return RedirectResponse(_with_admin_token(target, token), status_code=303)
    return _redirect_detail(session_id, msg=msg)


def _render(request: Request, name: str, context: dict | None = None, status_code: int = 200):
    ctx = dict(context or {})
    ctx["request"] = request
    ctx["admin_ok"] = _is_admin(request)
    ctx["admin_token"] = _admin_token_from_request(request)
    return templates.TemplateResponse(name, ctx, status_code=status_code)


@router.get("/login", response_class=HTMLResponse)
def admin_login_page(request: Request):
    if _is_admin(request):
        return RedirectResponse("/admin/relationship-sessions", status_code=303)
    return _render(
        request,
        "admin/login.html",
        {"title": "Admin kirish", "error": None, "configured": _admin_configured()},
    )


@router.post("/login")
async def admin_login_submit(request: Request, password: str = Form(...)):
    secret = get_settings().admin_secret
    if not secret or not hmac.compare_digest(password.strip(), secret):
        return _render(
            request,
            "admin/login.html",
            {
                "title": "Admin kirish",
                "error": "Parol noto‘g‘ri yoki ADMIN_SECRET sozlanmagan",
                "configured": _admin_configured(),
            },
            status_code=401,
        )
    response = RedirectResponse("/admin/relationship-sessions", status_code=303)
    response.set_cookie(
        ADMIN_COOKIE,
        secret,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,
    )
    return response


@router.post("/logout")
def admin_logout():
    response = RedirectResponse("/admin/login", status_code=303)
    response.delete_cookie(ADMIN_COOKIE)
    return response


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def admin_home(request: Request):
    if not _is_admin(request):
        return RedirectResponse("/admin/login", status_code=303)
    return RedirectResponse("/admin/relationship-sessions", status_code=303)


@router.get("/premium-payments", response_class=HTMLResponse)
def premium_payments_list(
    request: Request,
    db: DbSession = Depends(get_db),
    msg: str | None = None,
):
    if not _is_admin(request):
        return RedirectResponse(
            _preserve_admin_token(request, "/admin/login"),
            status_code=303,
        )

    grouped = list_premium_payments(db)
    return _render(
        request,
        "admin/premium_payments.html",
        {
            "title": "Premium to‘lovlar",
            "pending": grouped["pending"],
            "approved": grouped["approved"],
            "rejected": grouped["rejected"],
            "flash_ok": msg,
        },
    )


@router.get("/relationship-sessions", response_class=HTMLResponse)
def relationship_sessions_list(
    request: Request,
    db: DbSession = Depends(get_db),
    status: str | None = None,
    quick: str | None = None,
    q: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    initiator_tg: str | None = None,
    partner_tg: str | None = None,
    problems: str | None = None,
):
    if not _is_admin(request):
        return RedirectResponse("/admin/login", status_code=303)

    rows = list_sessions(
        db,
        status=status,
        quick=quick,
        q=q,
        date_from=date_from,
        date_to=date_to,
        initiator_tg=initiator_tg,
        partner_tg=partner_tg,
        only_problems=problems == "1",
    )
    stats = compute_stats(db)
    return _render(
        request,
        "admin/relationship_sessions.html",
        {
            "title": "Munosabat sessiyalari",
            "rows": rows,
            "stats": stats,
            "filters": {
                "status": status or "",
                "quick": quick or "",
                "q": q or "",
                "date_from": date_from or "",
                "date_to": date_to or "",
                "initiator_tg": initiator_tg or "",
                "partner_tg": partner_tg or "",
                "problems": problems or "",
            },
            "status_labels": STATUS_LABELS,
        },
    )


@router.get("/relationship-sessions/{session_id}", response_class=HTMLResponse)
def relationship_session_detail(
    request: Request,
    session_id: str,
    db: DbSession = Depends(get_db),
    msg: str | None = None,
    err: str | None = None,
):
    if not _is_admin(request):
        return RedirectResponse("/admin/login", status_code=303)

    detail = get_session_detail(db, session_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Sessiya topilmadi")

    return _render(
        request,
        "admin/relationship_session_detail.html",
        {
            "title": f"Sessiya {session_id[:8]}…",
            "detail": detail,
            "mask_token": mask_token,
            "flash_ok": msg,
            "flash_err": err,
        },
    )


def _redirect_detail(session_id: str, *, msg: str | None = None, err: str | None = None):
    qs = []
    if msg:
        qs.append(f"msg={msg}")
    if err:
        qs.append(f"err={err}")
    suffix = ("?" + "&".join(qs)) if qs else ""
    return RedirectResponse(
        f"/admin/relationship-sessions/{session_id}{suffix}",
        status_code=303,
    )


@router.post("/relationship-sessions/{session_id}/resend-share")
async def admin_resend_share(
    request: Request,
    session_id: str,
    db: DbSession = Depends(get_db),
):
    if not _is_admin(request):
        return RedirectResponse("/admin/login", status_code=303)
    session = db.get(Session, session_id)
    if not session:
        raise HTTPException(status_code=404)
    log_relationship_event(
        db,
        session_id=session_id,
        event_type="admin_resend_share",
        payload="admin_panel",
        commit=True,
    )
    ok = await notify_initiator_answers_saved(session_id, force=True)
    return _redirect_detail(
        session_id,
        msg="Share xabari qayta yuborildi" if ok else None,
        err=None if ok else "Telegram xabar yuborilmadi",
    )


@router.post("/relationship-sessions/{session_id}/resend-result")
async def admin_resend_result(
    request: Request,
    session_id: str,
    db: DbSession = Depends(get_db),
):
    if not _is_admin(request):
        return RedirectResponse("/admin/login", status_code=303)
    session = db.get(Session, session_id)
    if not session:
        raise HTTPException(status_code=404)
    if session.status != SessionStatus.complete:
        return _redirect_detail(session_id, err="Sessiya hali completed emas")

    # Allow re-notify by clearing flags
    for p in session.participants:
        p.result_notified_at = None
    log_relationship_event(
        db,
        session_id=session_id,
        event_type="admin_resend_result",
        payload="admin_panel",
        commit=True,
    )
    await send_result_notifications(session_id, completed_by="admin")
    return _redirect_detail(session_id, msg="Natija qayta yuborish urinildi")


@router.post("/relationship-sessions/{session_id}/revoke-token")
def admin_revoke_token(
    request: Request,
    session_id: str,
    db: DbSession = Depends(get_db),
):
    if not _is_admin(request):
        return RedirectResponse("/admin/login", status_code=303)
    session = db.get(Session, session_id)
    if not session:
        raise HTTPException(status_code=404)
    revoke_invite_token(session)
    log_relationship_event(
        db,
        session_id=session_id,
        event_type="admin_revoke_token",
        payload="admin_panel",
    )
    db.commit()
    return _redirect_detail(session_id, msg="Taklif tokeni bekor qilindi")


@router.post("/relationship-sessions/{session_id}/regenerate-token")
def admin_regenerate_token(
    request: Request,
    session_id: str,
    db: DbSession = Depends(get_db),
):
    if not _is_admin(request):
        return RedirectResponse("/admin/login", status_code=303)
    session = db.get(Session, session_id)
    if not session:
        raise HTTPException(status_code=404)
    revoke_invite_token(session)
    session.invite_token = None
    token = ensure_invite_token(db, session)
    log_relationship_event(
        db,
        session_id=session_id,
        event_type="admin_regenerate_token",
        payload=f"token_len={len(token)}",
    )
    db.commit()
    return _redirect_detail(session_id, msg="Yangi taklif tokeni yaratildi")


@router.post("/relationship-sessions/{session_id}/cancel")
def admin_cancel_session(
    request: Request,
    session_id: str,
    db: DbSession = Depends(get_db),
):
    if not _is_admin(request):
        return RedirectResponse("/admin/login", status_code=303)
    session = db.get(Session, session_id)
    if not session:
        raise HTTPException(status_code=404)
    session.status = SessionStatus.cancelled
    if session.invite_token:
        revoke_invite_token(session)
    log_relationship_event(
        db,
        session_id=session_id,
        event_type="admin_cancel_session",
        payload="admin_panel",
    )
    db.commit()
    return _redirect_detail(session_id, msg="Sessiya bekor qilindi")


@router.post("/relationship-sessions/{session_id}/approve-premium")
async def admin_approve_premium(
    request: Request,
    session_id: str,
    db: DbSession = Depends(get_db),
):
    if not _is_admin(request):
        return RedirectResponse("/admin/login", status_code=303)
    session = db.get(Session, session_id)
    if not session:
        raise HTTPException(status_code=404)
    form = await request.form()
    approve_premium(db, session, actor="admin_panel")
    db.commit()
    return _redirect_after_premium_action(
        request,
        session_id,
        msg="Premium tasdiqlandi va ochildi",
        next_url=form.get("next"),
        form=dict(form),
    )


@router.post("/relationship-sessions/{session_id}/reject-premium")
async def admin_reject_premium(
    request: Request,
    session_id: str,
    db: DbSession = Depends(get_db),
):
    if not _is_admin(request):
        return RedirectResponse("/admin/login", status_code=303)
    session = db.get(Session, session_id)
    if not session:
        raise HTTPException(status_code=404)
    form = await request.form()
    reject_premium(db, session, actor="admin_panel")
    db.commit()
    return _redirect_after_premium_action(
        request,
        session_id,
        msg="To‘lov rad etildi, premium yopiq",
        next_url=form.get("next"),
        form=dict(form),
    )


@router.post("/relationship-sessions/{session_id}/reblock-premium")
async def admin_reblock_premium(
    request: Request,
    session_id: str,
    db: DbSession = Depends(get_db),
):
    if not _is_admin(request):
        return RedirectResponse("/admin/login", status_code=303)
    session = db.get(Session, session_id)
    if not session:
        raise HTTPException(status_code=404)
    form = await request.form()
    reblock_premium(db, session, actor="admin_panel")
    db.commit()
    return _redirect_after_premium_action(
        request,
        session_id,
        msg="Premium qayta bloklandi",
        next_url=form.get("next"),
        form=dict(form),
    )
