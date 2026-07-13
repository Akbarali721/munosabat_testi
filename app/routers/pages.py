import logging
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, Form, Header, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session as DbSession

from app.bot.handlers import PENDING_PARTNER_NAME
from app.config import get_settings

logger = logging.getLogger(__name__)

INVITE_SHARE_TEXT = (
    "Men munosabatlarimizni yaxshiroq tushunish uchun ushbu savollarga javob berdim. "
    "Endi sizning navbatingiz 😊"
)
from app.models import (
    Answer,
    Gender,
    Participant,
    ParticipantRole,
    RelationshipStage,
    Session,
    SessionStatus,
)
from app.constants import (
    GENDER_LABELS,
    LOADING_MESSAGES,
    PREMIUM_PRICE_UZS,
    SCENARIO_CLOSINGS,
    SCENARIO_CLOSINGS_MALE,
    SCENARIO_DISPLAY_TITLES,
    SESSION_QUESTION_COUNT,
    STAGE_ICONS,
    STAGE_LABELS,
    STAGE_DESCRIPTIONS,
)
from app.database import get_db
from app.services.notifications import (
    notify_initiator_answers_saved,
    send_result_notifications,
)
from app.services.retention import schedule_session_reminders
from app.copy.premium_experience import PAYWALL_HEADLINE, PAYWALL_LEAD, PAYWALL_TAGLINE, UNLOCK_SPLASH
from app.services.premium import build_premium_result_copy
from app.services.result_experience import build_result_experience
from app.services.results import build_session_result
from app.services.invite_token import ensure_invite_token
from app.services.session_complete import complete_partner_session
from app.services.telegram_auth import (
    TelegramAuthError,
    extract_init_data_from_request,
    validate_init_data,
)
from app.ui import random_footer_quote
from app.services.scenarios import (
    get_option_weight,
    get_questions_for_participant,
    parse_options,
    question_text_for_display,
    questions_ready,
)

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))


def _get_session_or_404(db: DbSession, session_id: str) -> Session:
    session = db.get(Session, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sessiya topilmadi")
    return session


def _participant_by_role(session: Session, role: ParticipantRole) -> Participant | None:
    return next((p for p in session.participants if p.role == role), None)


def _render(
    request: Request,
    template_name: str,
    context: dict | None = None,
    status_code: int = 200,
):
    if context is None:
        context = {}
    else:
        context = dict(context)
    context["request"] = request
    context.setdefault("footer_quote", random_footer_quote())
    return templates.TemplateResponse(
        template_name,
        context,
        status_code=status_code,
    )


def _try_validate_init_data(
    request: Request,
    *,
    form_init_data: str | None = None,
) -> int | None:
    """Return telegram user id if initData valid; None if absent. Raises on invalid."""
    init_data = extract_init_data_from_request(
        header_value=request.headers.get("X-Telegram-Init-Data"),
        form_value=form_init_data,
        query_value=request.query_params.get("tgWebAppData")
        or request.query_params.get("initData"),
    )
    if not init_data:
        return None
    user = validate_init_data(init_data)
    return user.id


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return _render(request, "index.html", {"title": "Qadam — Munosabat tahlili"})


@router.get("/start", response_class=HTMLResponse)
def start_form(request: Request):
    return _render(
        request,
        "start.html",
        {
            "title": "Tahlilni boshlash",
            "stages": RelationshipStage,
            "stage_labels": STAGE_LABELS,
            "stage_icons": STAGE_ICONS,
            "stage_descriptions": STAGE_DESCRIPTIONS,
            "genders": Gender,
            "gender_labels": GENDER_LABELS,
        },
    )


@router.post("/start")
async def start_session(
    request: Request,
    name: str = Form(...),
    gender: Gender = Form(...),
    relationship_stage: RelationshipStage = Form(...),
    anniversary_date: str | None = Form(None),
    init_data: str | None = Form(None),
    db: DbSession = Depends(get_db),
):
    telegram_id = None
    try:
        telegram_id = _try_validate_init_data(request, form_init_data=init_data)
    except TelegramAuthError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    session = Session(relationship_stage=relationship_stage)
    if anniversary_date and anniversary_date.strip():
        try:
            from datetime import date

            session.anniversary_date = date.fromisoformat(anniversary_date.strip())
        except ValueError:
            pass
    db.add(session)
    db.flush()

    participant = Participant(
        session_id=session.id,
        role=ParticipantRole.user_a,
        name=name.strip(),
        gender=gender,
        telegram_chat_id=telegram_id,
    )
    db.add(participant)
    db.commit()

    return RedirectResponse(
        url=f"/session/{session.id}/questions?role=user_a",
        status_code=303,
    )


@router.get("/session/{session_id}/questions", response_class=HTMLResponse)
def questions_form(
    request: Request,
    session_id: str,
    role: str = "user_a",
    db: DbSession = Depends(get_db),
):
    session = _get_session_or_404(db, session_id)
    participant_role = ParticipantRole.user_a if role == "user_a" else ParticipantRole.user_b
    participant = _participant_by_role(session, participant_role)

    if not participant:
        if participant_role == ParticipantRole.user_b:
            return RedirectResponse(url=f"/session/{session_id}/join", status_code=303)
        raise HTTPException(status_code=404, detail="Ishtirokchi topilmadi")

    if participant.name == PENDING_PARTNER_NAME and participant_role == ParticipantRole.user_b:
        return RedirectResponse(url=f"/session/{session_id}/join", status_code=303)

    if participant.completed_at:
        if participant_role == ParticipantRole.user_a:
            return RedirectResponse(url=f"/invite/{session_id}", status_code=303)
        return RedirectResponse(
            url=f"/session/{session_id}/waiting",
            status_code=303,
        )

    ready = questions_ready(db, session.relationship_stage, participant.gender)
    questions = get_questions_for_participant(
        db, session.relationship_stage, participant.gender
    ) if ready else []

    closings = (
        SCENARIO_CLOSINGS_MALE
        if participant.gender == Gender.male
        else SCENARIO_CLOSINGS
    )
    questions_view = []
    for question in questions:
        questions_view.append(
            {
                "scenario_id": question.scenario_id,
                "dimension": question.dimension,
                "text": question_text_for_display(question, participant.gender),
                "options": parse_options(question, gender=participant.gender),
                "closing": closings.get(
                    question.scenario_id, "Sizning birinchi fikringiz?"
                ),
            }
        )

    return _render(
        request,
        "questions.html",
        {
            "title": "Hayotiy vaziyatlar",
            "session": session,
            "participant": participant,
            "role": role,
            "questions": questions_view,
            "questions_ready": ready,
            "question_count": SESSION_QUESTION_COUNT,
            "stage_labels": STAGE_LABELS,
            "scenario_titles": SCENARIO_DISPLAY_TITLES,
            "loading_messages": LOADING_MESSAGES,
        },
    )


@router.post("/session/{session_id}/questions")
async def submit_answers(
    request: Request,
    session_id: str,
    background_tasks: BackgroundTasks,
    role: str = Form("user_a"),
    db: DbSession = Depends(get_db),
):
    session = _get_session_or_404(db, session_id)
    participant_role = ParticipantRole.user_a if role == "user_a" else ParticipantRole.user_b
    participant = _participant_by_role(session, participant_role)

    if not participant:
        raise HTTPException(status_code=404, detail="Ishtirokchi topilmadi")

    if not questions_ready(db, session.relationship_stage, participant.gender):
        raise HTTPException(
            status_code=400,
            detail="Bu bosqich uchun savollar hali tayyor emas",
        )

    # Idempotent: already completed
    if participant.completed_at:
        if participant_role == ParticipantRole.user_a:
            return RedirectResponse(url=f"/invite/{session_id}", status_code=303)
        return RedirectResponse(url=f"/session/{session_id}/waiting", status_code=303)

    form = await request.form()
    questions = get_questions_for_participant(
        db, session.relationship_stage, participant.gender
    )

    for question in questions:
        field_name = f"scenario_{question.scenario_id}"
        raw_value = form.get(field_name)
        if raw_value is None:
            raise HTTPException(
                status_code=400,
                detail=f"{question.scenario_id}-vaziyat uchun javob kiritilmagan",
            )
        choice_index = int(raw_value)
        options = parse_options(question, gender=participant.gender)
        if choice_index < 0 or choice_index >= len(options):
            raise HTTPException(status_code=400, detail="Noto‘g‘ri javob qiymati")

        choice_weight = get_option_weight(question, choice_index)

        existing = (
            db.query(Answer)
            .filter(
                Answer.participant_id == participant.id,
                Answer.scenario_id == question.scenario_id,
            )
            .first()
        )
        if existing:
            existing.choice_index = choice_index
            existing.choice_weight = choice_weight
        else:
            db.add(
                Answer(
                    session_id=session.id,
                    participant_id=participant.id,
                    scenario_id=question.scenario_id,
                    scenario_question_id=question.id,
                    choice_index=choice_index,
                    choice_weight=choice_weight,
                )
            )

    participant.completed_at = datetime.utcnow()

    if participant_role == ParticipantRole.user_a:
        session.status = SessionStatus.awaiting_user_b
        ensure_invite_token(db, session)
        db.commit()
        background_tasks.add_task(notify_initiator_answers_saved, session_id)
        return RedirectResponse(url=f"/invite/{session_id}", status_code=303)

    db.commit()
    newly_completed = complete_partner_session(db, session_id)
    if newly_completed:
        background_tasks.add_task(send_result_notifications, session_id)
    else:
        # Already complete — still retry any missing per-participant notifications
        background_tasks.add_task(send_result_notifications, session_id)

    return RedirectResponse(
        url=f"/session/{session_id}/waiting",
        status_code=303,
    )


@router.get("/session/{session_id}/waiting", response_class=HTMLResponse)
def waiting_page(
    request: Request,
    session_id: str,
    db: DbSession = Depends(get_db),
):
    session = _get_session_or_404(db, session_id)
    user_b = _participant_by_role(session, ParticipantRole.user_b)
    if not user_b or not user_b.completed_at:
        raise HTTPException(status_code=400, detail="Test hali tugallanmagan")
    return _render(request, "waiting.html", {"title": "Javoblar qabul qilindi", "session": session})


@router.get("/invite/{session_id}", response_class=HTMLResponse)
def invite_page(
    request: Request,
    session_id: str,
    db: DbSession = Depends(get_db),
):
    session = _get_session_or_404(db, session_id)
    user_a = _participant_by_role(session, ParticipantRole.user_a)

    if not user_a or not user_a.completed_at:
        return RedirectResponse(
            url=f"/session/{session_id}/questions?role=user_a",
            status_code=303,
        )

    token = ensure_invite_token(db, session)
    db.commit()

    settings = get_settings()
    invite_deep_link = ""
    if not token:
        logger.error(
            "invite_page: empty invite_token; cannot build share link session_id=%s",
            session_id,
        )
    elif not (settings.telegram_bot_username or "").strip():
        logger.error(
            "invite_page: TELEGRAM_BOT_USERNAME missing; cannot build share link "
            "session_id=%s",
            session_id,
        )
    else:
        invite_deep_link = settings.bot_link_url(f"rel_invite_{token}") or ""
        if not invite_deep_link:
            logger.error(
                "invite_page: bot_link_url returned empty session_id=%s username=%r",
                session_id,
                settings.telegram_bot_username,
            )

    return _render(
        request,
        "invite.html",
        {
            "title": "Sherikka yuborish",
            "session": session,
            "invite_deep_link": invite_deep_link,
            "invite_share_text": INVITE_SHARE_TEXT,
            "telegram_linked": bool(user_a.telegram_chat_id),
        },
    )


@router.get("/session/{session_id}/join", response_class=HTMLResponse, name="join_form")
def join_form(
    request: Request,
    session_id: str,
    db: DbSession = Depends(get_db),
):
    session = _get_session_or_404(db, session_id)
    user_a = _participant_by_role(session, ParticipantRole.user_a)
    user_b = _participant_by_role(session, ParticipantRole.user_b)

    if not user_a or not user_a.completed_at:
        raise HTTPException(status_code=400, detail="Birinchi ishtirokchi hali tahlilni tugatmagan")

    if user_b:
        if user_b.completed_at:
            return RedirectResponse(
                url=f"/session/{session_id}/waiting",
                status_code=303,
            )
        if user_b.name != PENDING_PARTNER_NAME:
            return RedirectResponse(
                url=f"/session/{session_id}/questions?role=user_b",
                status_code=303,
            )
        # Pending profile — show join form to set name/gender

    return _render(
        request,
        "join.html",
        {
            "title": "Tahlilga qo‘shilish",
            "session": session,
            "user_a": user_a,
            "genders": Gender,
            "gender_labels": GENDER_LABELS,
            "stage_labels": STAGE_LABELS,
        },
    )


@router.post("/session/{session_id}/join")
async def join_session(
    request: Request,
    session_id: str,
    name: str = Form(...),
    gender: Gender = Form(...),
    birthday: str | None = Form(None),
    init_data: str | None = Form(None),
    db: DbSession = Depends(get_db),
):
    session = _get_session_or_404(db, session_id)
    user_b = _participant_by_role(session, ParticipantRole.user_b)

    telegram_id = None
    try:
        telegram_id = _try_validate_init_data(request, form_init_data=init_data)
    except TelegramAuthError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    if user_b and user_b.name != PENDING_PARTNER_NAME:
        return RedirectResponse(
            url=f"/session/{session_id}/questions?role=user_b",
            status_code=303,
        )

    if user_b and user_b.name == PENDING_PARTNER_NAME:
        if telegram_id and user_b.telegram_chat_id and user_b.telegram_chat_id != telegram_id:
            raise HTTPException(status_code=403, detail="Bu test boshqa ishtirokchiga biriktirilgan")
        user_b.name = name.strip()
        user_b.gender = gender
        if telegram_id:
            user_b.telegram_chat_id = telegram_id
        if birthday and birthday.strip():
            try:
                from datetime import date

                user_b.birthday = date.fromisoformat(birthday.strip())
            except ValueError:
                pass
        session.status = SessionStatus.awaiting_user_b_answers
        db.commit()
        schedule_session_reminders(db, session)
        db.commit()
        return RedirectResponse(
            url=f"/session/{session_id}/questions?role=user_b",
            status_code=303,
        )

    participant = Participant(
        session_id=session.id,
        role=ParticipantRole.user_b,
        name=name.strip(),
        gender=gender,
        telegram_chat_id=telegram_id,
    )
    if birthday and birthday.strip():
        try:
            from datetime import date

            participant.birthday = date.fromisoformat(birthday.strip())
        except ValueError:
            pass
    db.add(participant)
    session.status = SessionStatus.awaiting_user_b_answers
    db.commit()

    schedule_session_reminders(db, session)
    db.commit()

    return RedirectResponse(
        url=f"/session/{session_id}/questions?role=user_b",
        status_code=303,
    )


@router.get("/session/{session_id}/result", response_class=HTMLResponse)
async def result_page(
    request: Request,
    session_id: str,
    role: str | None = None,
    db: DbSession = Depends(get_db),
    x_telegram_init_data: str | None = Header(default=None, alias="X-Telegram-Init-Data"),
):
    session = _get_session_or_404(db, session_id)
    user_a = _participant_by_role(session, ParticipantRole.user_a)
    user_b = _participant_by_role(session, ParticipantRole.user_b)

    init_data = extract_init_data_from_request(
        header_value=x_telegram_init_data,
        query_value=request.query_params.get("tgWebAppData")
        or request.query_params.get("initData"),
    )

    # Shell page: Telegram WebApp JS will re-request with initData via POST bootstrap
    # For GET without initData, render bootstrap that posts initData
    if not init_data:
        return _render(
            request,
            "result_bootstrap.html",
            {
                "title": "Natija",
                "session": session,
            },
        )

    try:
        tg_user = validate_init_data(init_data)
    except TelegramAuthError:
        return _render(
            request,
            "security.html",
            {
                "title": "Ruxsat yo‘q",
                "title_text": "Tekshiruvdan o‘tmadi",
                "message": "Telegram orqali qayta oching. initData yaroqsiz yoki eskirgan.",
            },
            status_code=403,
        )

    if not user_a or not user_b or not user_a.completed_at or not user_b.completed_at:
        return _render(
            request,
            "security.html",
            {
                "title": "Natija tayyor emas",
                "title_text": "Natija hali tayyor emas",
                "message": "Ikkala ishtirokchi ham testni tugatishi kerak.",
            },
            status_code=403,
        )

    if session.status != SessionStatus.complete:
        return _render(
            request,
            "security.html",
            {
                "title": "Natija tayyor emas",
                "title_text": "Natija hali tayyor emas",
                "message": "Natija Telegram orqali yuborilganda ochiladi.",
            },
            status_code=403,
        )

    allowed_ids = {
        uid
        for uid in (user_a.telegram_chat_id, user_b.telegram_chat_id)
        if uid is not None
    }
    if tg_user.id not in allowed_ids:
        return _render(
            request,
            "security.html",
            {
                "title": "Ruxsat yo‘q",
                "title_text": "Siz bu natijani ko‘ra olmaysiz",
                "message": "Natija faqat shu juftlikdagi ishtirokchilarga ochiladi.",
            },
            status_code=403,
        )

    result = build_session_result(db, session)
    if not result:
        raise HTTPException(status_code=500, detail="Natijani shakllantirishda xatolik yuz berdi")

    if user_b.telegram_chat_id == tg_user.id:
        viewer = user_b
        viewer_role = ParticipantRole.user_b
    else:
        viewer = user_a
        viewer_role = ParticipantRole.user_a

    experience = build_result_experience(
        result,
        viewer=viewer,
        stage_label=STAGE_LABELS[session.relationship_stage],
        premium_unlocked=bool(session.is_premium_unlocked),
    )

    return _render(
        request,
        "result.html",
        {
            "title": "Munosabat tahlili",
            "session": session,
            "result": result,
            "experience": experience,
            "stage_labels": STAGE_LABELS,
            "premium_price": PREMIUM_PRICE_UZS,
            "viewer_role": viewer_role.value,
        },
    )


def _require_complete_session(db: DbSession, session_id: str) -> tuple[Session, Participant, Participant]:
    session = _get_session_or_404(db, session_id)
    user_a = _participant_by_role(session, ParticipantRole.user_a)
    user_b = _participant_by_role(session, ParticipantRole.user_b)
    if not user_a or not user_b or not user_a.completed_at or not user_b.completed_at:
        raise HTTPException(
            status_code=400,
            detail="Ikkala ishtirokchi ham savollarni tugatishi kerak",
        )
    return session, user_a, user_b


@router.get("/session/{session_id}/premium", response_class=HTMLResponse)
def premium_page(
    request: Request,
    session_id: str,
    db: DbSession = Depends(get_db),
):
    session = _get_session_or_404(db, session_id)
    user_a = _participant_by_role(session, ParticipantRole.user_a)
    user_b = _participant_by_role(session, ParticipantRole.user_b)
    if not user_a or not user_b or not user_a.completed_at or not user_b.completed_at:
        raise HTTPException(status_code=400, detail="Ikkala ishtirokchi ham savollarni tugatishi kerak")

    result = build_session_result(db, session)
    if not result:
        raise HTTPException(status_code=500, detail="Natijani shakllantirishda xatolik yuz berdi")

    premium = build_premium_result_copy(result) if session.is_premium_unlocked else None
    settings = get_settings()

    return _render(
        request,
        "premium.html",
        {
            "title": "Premium tahlil",
            "session": session,
            "result": result,
            "premium": premium,
            "stage_labels": STAGE_LABELS,
            "premium_price": PREMIUM_PRICE_UZS,
            "paywall_headline": PAYWALL_HEADLINE,
            "paywall_lead": PAYWALL_LEAD,
            "paywall_tagline": PAYWALL_TAGLINE,
            "unlock_splash": UNLOCK_SPLASH,
            "payment_demo": settings.payment_demo,
        },
    )
