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
    premium_price_label,
    SCENARIO_CLOSINGS,
    SCENARIO_CLOSINGS_MALE,
    SCENARIO_DISPLAY_TITLES,
    SESSION_QUESTION_COUNT,
    STAGE_CATEGORY_CODE,
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
from app.services.payment import payment_page_url, premium_access_granted
from app.services.premium import build_premium_result_copy
from app.services.result_experience import build_result_experience
from app.services.results import build_session_result
from app.services.invite_token import ensure_invite_token, get_session_by_invite_token
from app.services.invite_share import (
    PARTNER_SHARE_TEXT,
    RELATIONSHIP_BOT_USERNAME,
    build_partner_deep_link,
    build_telegram_share_url,
)
from app.services.session_complete import complete_partner_session
from app.services.session_telegram import set_initiator_telegram_id, set_partner_telegram_id
from app.services.events import log_relationship_event
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
    question_codes_for_questions,
    question_text_for_display,
    questions_ready,
)
from app.services.relationship_stage import START_FORM_STAGES, is_allowed_start_stage

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))


def _get_session_or_404(db: DbSession, session_id: str) -> Session:
    session = db.get(Session, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sessiya topilmadi")
    return session


def _participant_by_role(session: Session, role: ParticipantRole) -> Participant | None:
    return next((p for p in session.participants if p.role == role), None)


def _session_status_debug(status: SessionStatus) -> str:
    if status == SessionStatus.awaiting_user_b:
        return "waiting_for_partner"
    if status == SessionStatus.awaiting_user_b_answers:
        return "partner_in_progress"
    if status == SessionStatus.complete:
        return "completed"
    return status.value


def _invite_page_url(token: str) -> str:
    return f"/relationship/session/{token}/invite"


def _log_session_completion(
    *,
    session: Session,
    participant: Participant,
    participant_role: ParticipantRole,
    telegram_id: int | None,
    redirect_url: str,
    invite_link: str | None = None,
    answer_count: int = 0,
) -> None:
    user_a = _participant_by_role(session, ParticipantRole.user_a)
    user_b = _participant_by_role(session, ParticipantRole.user_b)
    answer_count = (
        answer_count
        if answer_count
        else (len(participant.answers) if participant.answers else 0)
    )
    logger.info(
        "session.completion session_token=%s session_id=%s respondent_role=%s "
        "telegram_user_id=%s answer_count=%s respondent_1_completed=%s "
        "respondent_2_completed=%s session_status=%s redirect_url=%s invite_link=%s",
        session.invite_token,
        session.id,
        participant_role.value,
        telegram_id,
        answer_count,
        bool(user_a and user_a.completed_at),
        bool(user_b and user_b.completed_at),
        _session_status_debug(session.status),
        redirect_url,
        invite_link,
    )


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
):
    """Return TelegramWebAppUser if initData valid; None if absent. Raises on invalid."""
    init_data = extract_init_data_from_request(
        header_value=request.headers.get("X-Telegram-Init-Data"),
        form_value=form_init_data,
        query_value=request.query_params.get("tgWebAppData")
        or request.query_params.get("initData"),
    )
    if not init_data:
        return None
    return validate_init_data(init_data)


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return _render(request, "index.html", {"title": "Juftlik suhbati"})


@router.get("/start", response_class=HTMLResponse)
def start_form(request: Request):
    return _render(
        request,
        "start.html",
        {
            "title": "Juftlik suhbati — boshlash",
            "start_stages": START_FORM_STAGES,
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
    telegram_username = None
    try:
        tg_user = _try_validate_init_data(request, form_init_data=init_data)
        if tg_user:
            telegram_id = tg_user.id
            telegram_username = tg_user.username
    except TelegramAuthError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    if not is_allowed_start_stage(relationship_stage):
        raise HTTPException(
            status_code=400,
            detail="Faqat «Endi tanishayapmiz» yoki «Yaqinda oila qurdik» tanlanishi mumkin.",
        )

    session = Session(relationship_stage=relationship_stage)
    if anniversary_date and anniversary_date.strip():
        try:
            from datetime import date

            session.anniversary_date = date.fromisoformat(anniversary_date.strip())
        except ValueError:
            pass
    if telegram_id:
        session.initiator_telegram_id = int(telegram_id)
    db.add(session)
    db.flush()

    participant = Participant(
        session_id=session.id,
        role=ParticipantRole.user_a,
        name=name.strip(),
        gender=gender,
        telegram_chat_id=telegram_id,
        telegram_username=telegram_username,
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
            token = ensure_invite_token(db, session)
            db.commit()
            return RedirectResponse(url=_invite_page_url(token), status_code=303)
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

    display_count = len(questions_view) if ready else SESSION_QUESTION_COUNT

    category_code = STAGE_CATEGORY_CODE.get(session.relationship_stage.value, session.relationship_stage.value)
    question_codes = question_codes_for_questions(questions) if questions else []
    logger.info(
        "questions.load category=%s respondent_gender=%s role=%s question_count=%s question_codes=%s",
        category_code,
        participant.gender.value,
        participant_role.value,
        len(questions),
        question_codes,
    )

    return _render(
        request,
        "questions.html",
        {
            "title": "Juftlik suhbati",
            "session": session,
            "participant": participant,
            "role": role,
            "questions": questions_view,
            "questions_ready": ready,
            "question_count": display_count,
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
    init_data: str | None = Form(None),
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
            token = ensure_invite_token(db, session)
            db.commit()
            return RedirectResponse(url=_invite_page_url(token), status_code=303)
        return RedirectResponse(url=f"/session/{session_id}/waiting", status_code=303)

    telegram_id = None
    try:
        tg_user = _try_validate_init_data(request, form_init_data=init_data)
        if tg_user:
            telegram_id = tg_user.id
            if tg_user.username:
                participant.telegram_username = tg_user.username
    except TelegramAuthError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

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
        set_initiator_telegram_id(session, telegram_id)
        session.status = SessionStatus.awaiting_user_b
        token = ensure_invite_token(db, session)
        log_relationship_event(
            db,
            session_id=session_id,
            event_type="initiator_test_completed",
            telegram_id=telegram_id or session.initiator_telegram_id,
        )
        db.commit()
        db.refresh(session)
        invite_link = build_partner_deep_link(token)
        redirect_url = _invite_page_url(token)
        _log_session_completion(
            session=session,
            participant=participant,
            participant_role=participant_role,
            telegram_id=telegram_id,
            redirect_url=redirect_url,
            invite_link=invite_link,
            answer_count=len(questions),
        )
        background_tasks.add_task(notify_initiator_answers_saved, session_id)
        return RedirectResponse(url=redirect_url, status_code=303)

    set_partner_telegram_id(session, telegram_id)
    db.commit()
    became_complete = complete_partner_session(db, session_id)
    db.refresh(session)
    redirect_url = f"/session/{session_id}/waiting"
    _log_session_completion(
        session=session,
        participant=participant,
        participant_role=participant_role,
        telegram_id=telegram_id,
        redirect_url=redirect_url,
        answer_count=len(questions),
    )
    if became_complete:
        logger.info(
            "session.completion both_done session_token=%s session_id=%s session_status=%s",
            session.invite_token,
            session.id,
            _session_status_debug(session.status),
        )
    # Always attempt notifications; send_result_notifications is idempotent per participant
    background_tasks.add_task(
        send_result_notifications,
        session_id,
        completed_by="user_b",
    )

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


@router.get("/invite/{session_id}")
def invite_page_legacy(session_id: str, db: DbSession = Depends(get_db)):
    """Legacy URL — redirect to token-based invite page."""
    session = _get_session_or_404(db, session_id)
    user_a = _participant_by_role(session, ParticipantRole.user_a)
    if not user_a or not user_a.completed_at:
        return RedirectResponse(
            url=f"/session/{session_id}/questions?role=user_a",
            status_code=303,
        )
    token = ensure_invite_token(db, session)
    db.commit()
    return RedirectResponse(url=_invite_page_url(token), status_code=303)


@router.get("/relationship/session/{token}/invite", response_class=HTMLResponse)
def relationship_invite_page(
    request: Request,
    token: str,
    db: DbSession = Depends(get_db),
):
    session = get_session_by_invite_token(db, token)
    if not session:
        raise HTTPException(status_code=404, detail="Taklif havolasi topilmadi")

    user_a = _participant_by_role(session, ParticipantRole.user_a)
    user_b = _participant_by_role(session, ParticipantRole.user_b)

    if not user_a or not user_a.completed_at:
        return RedirectResponse(
            url=f"/session/{session.id}/questions?role=user_a",
            status_code=303,
        )

    if session.status == SessionStatus.complete and user_b and user_b.completed_at:
        return RedirectResponse(
            url=f"/session/{session.id}/status",
            status_code=303,
        )

    invite_deep_link = build_partner_deep_link(token) or ""
    telegram_share_url = build_telegram_share_url(token) or ""
    bot_username = get_settings().resolve_bot_username() or RELATIONSHIP_BOT_USERNAME

    logger.info(
        "invite.page session_token=%s session_id=%s respondent_1_completed=%s "
        "respondent_2_completed=%s session_status=%s invite_link=%s",
        token,
        session.id,
        bool(user_a.completed_at),
        bool(user_b and user_b.completed_at),
        _session_status_debug(session.status),
        invite_deep_link,
    )

    return _render(
        request,
        "invite.html",
        {
            "title": "Juftimga yuborish",
            "session": session,
            "invite_deep_link": invite_deep_link,
            "telegram_share_url": telegram_share_url,
            "invite_share_text": PARTNER_SHARE_TEXT,
            "bot_username": bot_username,
        },
    )


@router.get("/session/{session_id}/status", response_class=HTMLResponse)
def session_status_page(
    request: Request,
    session_id: str,
    db: DbSession = Depends(get_db),
):
    session = _get_session_or_404(db, session_id)
    user_a = _participant_by_role(session, ParticipantRole.user_a)
    user_b = _participant_by_role(session, ParticipantRole.user_b)

    initiator_done = bool(user_a and user_a.completed_at)
    partner_started = bool(
        session.partner_started_at
        or session.partner_telegram_id
        or (user_b and user_b.telegram_chat_id)
    )
    partner_done = bool(user_b and user_b.completed_at)
    session_complete = session.status == SessionStatus.complete

    if session_complete:
        status_lead = "Ikkalangiz ham javob berdingiz. Suhbat natijasi tayyor."
        status_hint = "Pastdagi tugma orqali natijani ochishingiz mumkin."
    elif partner_done:
        status_lead = "Juftingiz ham tugatdi. Natija tayyorlanmoqda."
        status_hint = "Bir oz kuting — Telegram orqali ham xabar keladi."
    elif partner_started:
        status_lead = "Juftingiz o‘z qismini boshlagan. Javoblarini kutyapmiz."
        status_hint = "U tugatganda natija Telegram orqali ochiladi."
    elif initiator_done:
        status_lead = "Sizning qismingiz tayyor. Havolani juftingizga yuboring."
        status_hint = "Telegram botdagi «Juftimga yuborish» tugmasidan foydalaning."
    else:
        status_lead = "Suhbat hali yakunlanmagan."
        status_hint = "Avval o‘z savollaringizga javob bering."

    token = session.invite_token or ""
    telegram_share_url = build_telegram_share_url(token) if token else ""

    return _render(
        request,
        "status.html",
        {
            "title": "Juftlik suhbati holati",
            "session": session,
            "initiator_done": initiator_done,
            "partner_started": partner_started,
            "partner_done": partner_done,
            "session_complete": session_complete,
            "status_lead": status_lead,
            "status_hint": status_hint,
            "telegram_share_url": telegram_share_url,
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
    telegram_username = None
    try:
        tg_user = _try_validate_init_data(request, form_init_data=init_data)
        if tg_user:
            telegram_id = tg_user.id
            telegram_username = tg_user.username
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
            set_partner_telegram_id(session, telegram_id)
        if telegram_username:
            user_b.telegram_username = telegram_username
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
        telegram_username=telegram_username,
    )
    if birthday and birthday.strip():
        try:
            from datetime import date

            participant.birthday = date.fromisoformat(birthday.strip())
        except ValueError:
            pass
    db.add(participant)
    db.flush()
    set_partner_telegram_id(session, telegram_id)
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

    granted = premium_access_granted(session)
    experience = build_result_experience(
        result,
        viewer=viewer,
        stage_label=STAGE_LABELS[session.relationship_stage],
        premium_unlocked=granted,
    )

    return _render(
        request,
        "result.html",
        {
            "title": "Juftlik suhbati",
            "session": session,
            "result": result,
            "experience": experience,
            "stage_labels": STAGE_LABELS,
            "premium_price": PREMIUM_PRICE_UZS,
            "premium_price_label": premium_price_label(),
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
@router.get("/love/session/{session_id}/premium", response_class=HTMLResponse)
def premium_page(
    request: Request,
    session_id: str,
    role: str = "user_a",
    db: DbSession = Depends(get_db),
):
    session, _, _ = _require_complete_session(db, session_id)
    viewer_role = "user_b" if role == "user_b" else "user_a"

    if not premium_access_granted(session):
        return RedirectResponse(
            url=payment_page_url(session_id, role=viewer_role),
            status_code=302,
        )

    result = build_session_result(db, session)
    if not result:
        raise HTTPException(status_code=500, detail="Natijani shakllantirishda xatolik yuz berdi")

    premium = build_premium_result_copy(result)

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
            "premium_price_label": premium_price_label(),
            "paywall_headline": PAYWALL_HEADLINE,
            "paywall_lead": PAYWALL_LEAD,
            "paywall_tagline": PAYWALL_TAGLINE,
            "unlock_splash": UNLOCK_SPLASH,
            "payment_demo": False,
            "premium_granted": True,
        },
    )
