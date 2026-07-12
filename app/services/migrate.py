from sqlalchemy import inspect, text

from app.database import engine


def migrate_db() -> None:
    migrate_session_premium_columns()
    migrate_participant_telegram_column()
    migrate_retention_columns()
    migrate_reminders_table()
    migrate_payment_orders_table()
    migrate_invite_token_column()
    migrate_participant_result_notified_column()


def migrate_invite_token_column() -> None:
    inspector = inspect(engine)
    if "sessions" not in inspector.get_table_names():
        return

    columns = {col["name"] for col in inspector.get_columns("sessions")}
    with engine.begin() as conn:
        if "invite_token" not in columns:
            conn.execute(text("ALTER TABLE sessions ADD COLUMN invite_token VARCHAR(64)"))

        # Idempotent unique index (Postgres + SQLite)
        dialect = engine.dialect.name
        if dialect == "sqlite":
            conn.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS uq_sessions_invite_token "
                    "ON sessions (invite_token)"
                )
            )
        else:
            conn.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS uq_sessions_invite_token "
                    "ON sessions (invite_token)"
                )
            )


def migrate_participant_result_notified_column() -> None:
    inspector = inspect(engine)
    if "participants" not in inspector.get_table_names():
        return

    columns = {col["name"] for col in inspector.get_columns("participants")}
    if "result_notified_at" in columns:
        return

    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE participants ADD COLUMN result_notified_at TIMESTAMP"))


def migrate_session_premium_columns() -> None:
    inspector = inspect(engine)
    if "sessions" not in inspector.get_table_names():
        return

    columns = {col["name"] for col in inspector.get_columns("sessions")}
    statements: list[str] = []
    if "is_premium_unlocked" not in columns:
        statements.append(
            "ALTER TABLE sessions ADD COLUMN is_premium_unlocked BOOLEAN NOT NULL DEFAULT 0"
        )
    if "premium_unlocked_at" not in columns:
        statements.append("ALTER TABLE sessions ADD COLUMN premium_unlocked_at DATETIME")

    if not statements:
        return

    with engine.begin() as conn:
        for statement in statements:
            conn.execute(text(statement))


def migrate_participant_telegram_column() -> None:
    inspector = inspect(engine)
    if "participants" not in inspector.get_table_names():
        return

    columns = {col["name"] for col in inspector.get_columns("participants")}
    if "telegram_chat_id" in columns:
        return

    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE participants ADD COLUMN telegram_chat_id INTEGER"))


def migrate_retention_columns() -> None:
    inspector = inspect(engine)
    if "sessions" not in inspector.get_table_names():
        return

    session_columns = {col["name"] for col in inspector.get_columns("sessions")}
    session_statements: list[str] = []
    if "anniversary_date" not in session_columns:
        session_statements.append("ALTER TABLE sessions ADD COLUMN anniversary_date DATE")
    if "challenge_started_at" not in session_columns:
        session_statements.append("ALTER TABLE sessions ADD COLUMN challenge_started_at DATETIME")
    if "challenge_progress_json" not in session_columns:
        session_statements.append(
            "ALTER TABLE sessions ADD COLUMN challenge_progress_json TEXT NOT NULL DEFAULT '{}'"
        )
    if "reminders_enabled" not in session_columns:
        session_statements.append(
            "ALTER TABLE sessions ADD COLUMN reminders_enabled BOOLEAN NOT NULL DEFAULT 1"
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

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE reminders (
                    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    session_id VARCHAR(36) NOT NULL,
                    participant_id VARCHAR(36),
                    kind VARCHAR(32) NOT NULL,
                    scheduled_for DATETIME NOT NULL,
                    sent_at DATETIME,
                    payload_json TEXT NOT NULL DEFAULT '{}',
                    FOREIGN KEY(session_id) REFERENCES sessions (id),
                    FOREIGN KEY(participant_id) REFERENCES participants (id),
                    CONSTRAINT uq_reminder_session_participant_kind_date UNIQUE (
                        session_id, participant_id, kind, scheduled_for
                    )
                )
                """
            )
        )


def migrate_payment_orders_table() -> None:
    inspector = inspect(engine)
    if "payment_orders" in inspector.get_table_names():
        return

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE payment_orders (
                    id VARCHAR(36) NOT NULL PRIMARY KEY,
                    session_id VARCHAR(36) NOT NULL,
                    amount_uzs INTEGER NOT NULL,
                    status VARCHAR(32) NOT NULL,
                    provider VARCHAR(32) NOT NULL,
                    external_id VARCHAR(128),
                    created_at DATETIME NOT NULL,
                    paid_at DATETIME,
                    FOREIGN KEY(session_id) REFERENCES sessions (id)
                )
                """
            )
        )
