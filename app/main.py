from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.database import ensure_schema, get_db
from app.routers import admin, challenge, cron, pages, payment, telegram
from app.services import seed_scenarios

BASE_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_schema()
    db = next(get_db())
    try:
        seed_scenarios(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="Juftlik suhbati",
    description="Juftliklar uchun samimiy suhbat va bir-birini yaxshiroq tushunishga yordam beradigan platforma",
    lifespan=lifespan,
)

# Railway / reverse-proxy: trust X-Forwarded-Proto so url_for uses https
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)
app.include_router(pages.router)
app.include_router(challenge.router)
app.include_router(payment.router)
app.include_router(cron.router)
app.include_router(telegram.router)
app.include_router(admin.router)
