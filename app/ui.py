import random

from fastapi import Request

from app.constants import FOOTER_QUOTES


def random_footer_quote() -> str:
    return random.choice(FOOTER_QUOTES)


def template_context(request: Request, extra: dict | None = None) -> dict:
    ctx = {
        "request": request,
        "footer_quote": random_footer_quote(),
    }
    if extra:
        ctx.update(extra)
    return ctx
