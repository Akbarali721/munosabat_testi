"""Idempotent schema patches for SQLite (local) and PostgreSQL (Railway)."""

from __future__ import annotations

import logging

from sqlalchemy import inspect, text

from app.database import engine

logger = logging.getLogger(__name__)


def migrate_db() -> None:
    dialect = engine.dialect.name
    logger.info("Running schema migrations dialect=%s", dialect)
    migrate_session_premium_columns()
    migrate_participant_telegram_column()
    migrate_retention_columns()
    migrate_reminders_table()
    migrate_payment_orders_table()
    migrate_invite_token_column()
    migrate_participant_result_notified_column()


def _is_postgres() -> bool:
    return engine.dialect.name == "postgresql"


def _boolean_default(value: bool) -> str:
    if _is_postgres():
        return "TRUE" if value else "FALSE"
    return "1" if value else "0"


def _timestamp_type() -> str:
    return "TIMESTAMP" if _is_postgres() else "DATETIME"


def _add_column_if_missing(table: str, column: str, ddl_type: str) -> None:
    inspector = inspect(engine)
    if table not in inspector.get_table_names():
        return
    columns = {col["name"] for col in inspector.get_columns(table)}
    if column in columns:
        return
    with engine.begin() as conn:
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl_type}"))
        logger.info("Added column %s.%s", table, column)


def migrate_invite_token_column() -> None:
    inspector = inspect(engine)
    if "sessions" not in inspector.get_table_names():
        return

    columns = {col["name"] for col in inspector.get_columns("sessions")}
    with engine.begin() as conn:
        if "invite_token" not in columns:
            conn.execute(text("ALTER TABLE sessions ADD COLUMN invite_token VARCHAR(64)"))
            logger.info("Added column sessions.invite_token")

        # Unique index is idempotent on both Postgres and SQLite
        conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_sessions_invite_token "
                "ON sessions (invite_token)"
            )
        )


def migrate_participant_result_notified_column() -> None:
    _add_column_if_missing(
        "participants",
        "result_notified_at",
        _timestamp_type(),
    )


def migrate_session_premium_columns() -> None:
    inspector = inspect(engine)
    if "sessions" not in inspector.get_table_names():
        return

    columns = {col["name"] for col in inspector.get_columns("sessions")}
    statements: list[str] = []
    if "is_premium_unlocked" not in columns:
        statements.append(
            "ALTER TABLE sessions ADD COLUMN is_premium_unlocked "
            f"BOOLEAN NOT NULL DEFAULT {_boolean_default(False)}"
        )
    if "premium_unlocked_at" not in columns:
        statements.append(
            f"ALTER TABLE sessions ADD COLUMN premium_unlocked_at {_timestamp_type()}"
        )

    if not statements:
        return

    with engine.begin() as conn:
        for statement in statements:
            conn.execute(text(statement))


def migrate_participant_telegram_column() -> None:
    # BIGINT is safer for Telegram chat ids on Postgres; INTEGER remains fine on SQLite.
    ddl = "BIGINT" if _is_postgres() else "INTEGER"
    _add_column_if_missing("participants", "telegram_chat_id", ddl)


def migrate_retention_columns() -> None:
    inspector = inspect(engine)
    if "sessions" not in inspector.get_table_names():
        return

    session_columns = {col["name"] for col in inspector.get_columns("sessions")}
    session_statements: list[str] = []
    if "anniversary_date" not in session_columns:
        session_statements.append("ALTER TABLE sessions ADD COLUMN anniversary_date DATE")
    if "challenge_started_at" not in session_columns:
        session_statements.append(
            f"ALTER TABLE sessions ADD COLUMN challenge_started_at {_timestamp_type()}"
        )
    if "challenge_progress_json" not in session_columns:
        session_statements.append(
            "ALTER TABLE sessions ADD COLUMN challenge_progress_json "
            "TEXT NOT NULL DEFAULT '{}'"
        )
    if "reminders_enabled" not in session_columns:
        session_statements.append(
            "ALTER TABLE sessions ADD COLUMN reminders_enabled "
            f"BOOLEAN NOT NULL DEFAULT {_boolean_default(True)}"
        )

    participant_statements: list[str] = []
    if "participants" in inspector.get_table_names():
        participant_columns = {col["name"] for col in inspector.get_columns("participants")}
        if "birthday" not in participant_columns:
            participant_statements.append("ALTER TABLE participants ADD COLUMN birthday DATE")

    statements = session_statements + participant_statements
    if not statements:
        return

    with engine.begin() as conn:
        for statement in statements:
            conn.execute(text(statement))


def migrate_reminders_table() -> None:
    inspector = inspect(engine)
    if "reminders" in inspector.get_table_names():
        return

    ts = _timestamp_type()
    if _is_postgres():
        ddl = f"""
            CREATE TABLE reminders (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(36) NOT NULL REFERENCES sessions (id),
                participant_id VARCHAR(36) REFERENCES participants (id),
                kind VARCHAR(32) NOT NULL,
                scheduled_for {ts} NOT NULL,
                sent_at {ts},
                payload_json TEXT NOT NULL DEFAULT '{{}}',
                CONSTRAINT uq_reminder_session_participant_kind_date UNIQUE (
                    session_id, participant_id, kind, scheduled_for
                )
            )
            """
    else:
        ddl = f"""
            CREATE TABLE reminders (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                session_id VARCHAR(36) NOT NULL,
                participant_id VARCHAR(36),
                kind VARCHAR(32) NOT NULL,
                scheduled_for {ts} NOT NULL,
                sent_at {ts},
                payload_json TEXT NOT NULL DEFAULT '{{}}',
                FOREIGN KEY(session_id) REFERENCES sessions (id),
                FOREIGN KEY(participant_id) REFERENCES participants (id),
                CONSTRAINT uq_reminder_session_participant_kind_date UNIQUE (
                    session_id, participant_id, kind, scheduled_for
                )
            )
            """

    with engine.begin() as conn:
        conn.execute(text(ddl))
        logger.info("Created table reminders")


def migrate_payment_orders_table() -> None:
    inspector = inspect(engine)
    if "payment_orders" in inspector.get_table_names():
        return

    ts = _timestamp_type()
    if _is_postgres():
        ddl = f"""
            CREATE TABLE payment_orders (
                id VARCHAR(36) NOT NULL PRIMARY KEY,
                session_id VARCHAR(36) NOT NULL REFERENCES sessions (id),
                amount_uzs INTEGER NOT NULL,
                status VARCHAR(32) NOT NULL,
                provider VARCHAR(32) NOT NULL,
                external_id VARCHAR(128),
                created_at {ts} NOT NULL,
                paid_at {ts}
            )
            """
    else:
        ddl = f"""
            CREATE TABLE payment_orders (
                id VARCHAR(36) NOT NULL PRIMARY KEY,
                session_id VARCHAR(36) NOT NULL,
                amount_uzs INTEGER NOT NULL,
                status VARCHAR(32) NOT NULL,
                provider VARCHAR(32) NOT NULL,
                external_id VARCHAR(128),
                created_at {ts} NOT NULL,
                paid_at {ts},
                FOREIGN KEY(session_id) REFERENCES sessions (id)
            )
            """

    with engine.begin() as conn:
        conn.execute(text(ddl))
        logger.info("Created table payment_orders")
