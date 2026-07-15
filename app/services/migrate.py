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
    migrate_session_telegram_id_columns()
    backfill_session_telegram_ids_from_participants()
    migrate_session_share_tracking_columns()
    migrate_relationship_events_table()


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
    if "premium_payment_status" not in columns:
        statements.append(
            "ALTER TABLE sessions ADD COLUMN premium_payment_status "
            "VARCHAR(64) NOT NULL DEFAULT 'pending'"
        )

    if not statements:
        return

    with engine.begin() as conn:
        for statement in statements:
            conn.execute(text(statement))
        # First introduction: old sessions stay locked until admin approval
        if any("premium_payment_status" in s for s in statements):
            conn.execute(
                text(
                    "UPDATE sessions SET is_premium_unlocked = "
                    f"{_boolean_default(False)}, "
                    "premium_unlocked_at = NULL, "
                    "premium_payment_status = 'pending'"
                )
            )

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


def migrate_session_telegram_id_columns() -> None:
    ddl = "BIGINT" if _is_postgres() else "INTEGER"
    _add_column_if_missing("sessions", "initiator_telegram_id", ddl)
    _add_column_if_missing("sessions", "partner_telegram_id", ddl)


def backfill_session_telegram_ids_from_participants() -> None:
    """Fill empty session telegram fields from participant rows (idempotent)."""
    inspector = inspect(engine)
    if "sessions" not in inspector.get_table_names():
        return
    session_cols = {col["name"] for col in inspector.get_columns("sessions")}
    if "initiator_telegram_id" not in session_cols or "partner_telegram_id" not in session_cols:
        return
    if "participants" not in inspector.get_table_names():
        return

    with engine.begin() as conn:
        rows = conn.execute(
            text(
                """
                SELECT s.id, s.initiator_telegram_id, s.partner_telegram_id,
                       a.telegram_chat_id AS initiator_from_participant,
                       b.telegram_chat_id AS partner_from_participant
                FROM sessions s
                LEFT JOIN participants a
                  ON a.session_id = s.id AND a.role = 'user_a'
                LEFT JOIN participants b
                  ON b.session_id = s.id AND b.role = 'user_b'
                """
            )
        ).mappings().all()

        for row in rows:
            if row["initiator_telegram_id"] is None and row["initiator_from_participant"] is not None:
                conn.execute(
                    text(
                        "UPDATE sessions SET initiator_telegram_id = :tid WHERE id = :sid"
                    ),
                    {"tid": row["initiator_from_participant"], "sid": row["id"]},
                )
            if row["partner_telegram_id"] is None and row["partner_from_participant"] is not None:
                conn.execute(
                    text(
                        "UPDATE sessions SET partner_telegram_id = :tid WHERE id = :sid"
                    ),
                    {"tid": row["partner_from_participant"], "sid": row["id"]},
                )






def migrate_session_share_tracking_columns() -> None:
    _add_column_if_missing("sessions", "partner_started_at", _timestamp_type())
    _add_column_if_missing("sessions", "initiator_share_notified_at", _timestamp_type())
    _add_column_if_missing("sessions", "invite_token_created_at", _timestamp_type())
    _add_column_if_missing("sessions", "invite_token_used_at", _timestamp_type())
    _add_column_if_missing("sessions", "invite_revoked_at", _timestamp_type())
    _add_column_if_missing("participants", "telegram_username", "VARCHAR(64)")


def migrate_relationship_events_table() -> None:
    inspector = inspect(engine)
    if "relationship_events" in inspector.get_table_names():
        return

    ts = _timestamp_type()
    if _is_postgres():
        ddl = f"""
            CREATE TABLE relationship_events (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(36) NOT NULL REFERENCES sessions (id),
                event_type VARCHAR(64) NOT NULL,
                telegram_id BIGINT,
                payload TEXT NOT NULL DEFAULT '',
                created_at {ts} NOT NULL
            )
            """
    else:
        ddl = f"""
            CREATE TABLE relationship_events (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                session_id VARCHAR(36) NOT NULL,
                event_type VARCHAR(64) NOT NULL,
                telegram_id INTEGER,
                payload TEXT NOT NULL DEFAULT '',
                created_at {ts} NOT NULL,
                FOREIGN KEY(session_id) REFERENCES sessions (id)
            )
            """

    with engine.begin() as conn:
        conn.execute(text(ddl))
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_relationship_events_session_id "
                "ON relationship_events (session_id)"
            )
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_relationship_events_event_type "
                "ON relationship_events (event_type)"
            )
        )
        logger.info("Created table relationship_events")


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
