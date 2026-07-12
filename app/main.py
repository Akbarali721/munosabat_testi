from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.database import Base, engine, get_db
from app.routers import challenge, cron, pages, payment, telegram
from app.services import seed_scenarios
from app.services.migrate import migrate_db

BASE_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    migrate_db()
    db = next(get_db())
    try:
        seed_scenarios(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="Qadam — Munosabat tahlili",
    description="Juftliklarga bir-birini yaxshiroq tushunish va munosabatlarini mustahkamlashga yordam beradigan platforma",
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
