import enum
import uuid
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _str_enum(enum_cls: type[enum.Enum]):
    """Store enum values as VARCHAR on SQLite and PostgreSQL (no native PG ENUM)."""
    return Enum(
        enum_cls,
        values_callable=lambda items: [item.value for item in items],
        native_enum=False,
        length=64,
    )


class RelationshipStage(str, enum.Enum):
    newly_meeting = "newly_meeting"
    in_relationship = "in_relationship"
    married = "married"


class Gender(str, enum.Enum):
    male = "male"
    female = "female"


class ParticipantRole(str, enum.Enum):
    user_a = "user_a"
    user_b = "user_b"


class SessionStatus(str, enum.Enum):
    awaiting_user_b = "awaiting_user_b"
    awaiting_user_b_answers = "awaiting_user_b_answers"
    complete = "complete"


class ReminderKind(str, enum.Enum):
    birthday = "birthday"
    anniversary = "anniversary"
    new_year = "new_year"
    challenge_daily = "challenge_daily"
    weekly_reflection = "weekly_reflection"


class PaymentStatus(str, enum.Enum):
    pending = "pending"
    paid = "paid"
    failed = "failed"
    cancelled = "cancelled"


class PaymentProvider(str, enum.Enum):
    demo = "demo"
    payme = "payme"


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    relationship_stage: Mapped[RelationshipStage] = mapped_column(_str_enum(RelationshipStage))
    status: Mapped[SessionStatus] = mapped_column(
        _str_enum(SessionStatus), default=SessionStatus.awaiting_user_b
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_premium_unlocked: Mapped[bool] = mapped_column(Boolean, default=False)
    premium_unlocked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    anniversary_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    challenge_started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    challenge_progress_json: Mapped[str] = mapped_column(Text, default="{}")
    reminders_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    invite_token: Mapped[str | None] = mapped_column(
        String(64), unique=True, nullable=True, index=True
    )

    participants: Mapped[list["Participant"]] = relationship(back_populates="session")
    answers: Mapped[list["Answer"]] = relationship(back_populates="session")
    reminders: Mapped[list["Reminder"]] = relationship(back_populates="session")
    payment_orders: Mapped[list["PaymentOrder"]] = relationship(back_populates="session")


class Participant(Base):
    __tablename__ = "participants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("sessions.id"))
    role: Mapped[ParticipantRole] = mapped_column(_str_enum(ParticipantRole))
    name: Mapped[str] = mapped_column(String(100))
    gender: Mapped[Gender] = mapped_column(_str_enum(Gender))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    telegram_chat_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    birthday: Mapped[date | None] = mapped_column(Date, nullable=True)
    result_notified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    session: Mapped["Session"] = relationship(back_populates="participants")
    answers: Mapped[list["Answer"]] = relationship(back_populates="participant")
    reminders: Mapped[list["Reminder"]] = relationship(back_populates="participant")


class ScenarioQuestion(Base):
    __tablename__ = "scenario_questions"
    __table_args__ = (
        UniqueConstraint("scenario_id", "gender", "stage", name="uq_scenario_gender_stage"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scenario_id: Mapped[str] = mapped_column(String(64), index=True)
    stage: Mapped[RelationshipStage] = mapped_column(_str_enum(RelationshipStage))
    gender: Mapped[Gender] = mapped_column(_str_enum(Gender))
    dimension: Mapped[str] = mapped_column(String(64))
    text: Mapped[str] = mapped_column(Text)
    options_json: Mapped[str] = mapped_column(Text)

    answers: Mapped[list["Answer"]] = relationship(back_populates="scenario_question")


class Answer(Base):
    __tablename__ = "answers"
    __table_args__ = (
        UniqueConstraint("participant_id", "scenario_id", name="uq_participant_scenario"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("sessions.id"))
    participant_id: Mapped[str] = mapped_column(String(36), ForeignKey("participants.id"))
    scenario_id: Mapped[str] = mapped_column(String(64), index=True)
    scenario_question_id: Mapped[int] = mapped_column(Integer, ForeignKey("scenario_questions.id"))
    choice_index: Mapped[int] = mapped_column(Integer)
    choice_weight: Mapped[int] = mapped_column(Integer)

    session: Mapped["Session"] = relationship(back_populates="answers")
    participant: Mapped["Participant"] = relationship(back_populates="answers")
    scenario_question: Mapped["ScenarioQuestion"] = relationship(back_populates="answers")


class Reminder(Base):
    __tablename__ = "reminders"
    __table_args__ = (
        UniqueConstraint(
            "session_id",
            "participant_id",
            "kind",
            "scheduled_for",
            name="uq_reminder_session_participant_kind_date",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("sessions.id"))
    participant_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("participants.id"), nullable=True
    )
    kind: Mapped[ReminderKind] = mapped_column(_str_enum(ReminderKind))
    scheduled_for: Mapped[datetime] = mapped_column(DateTime)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    payload_json: Mapped[str] = mapped_column(Text, default="{}")

    session: Mapped["Session"] = relationship(back_populates="reminders")
    participant: Mapped["Participant | None"] = relationship(back_populates="reminders")


class PaymentOrder(Base):
    __tablename__ = "payment_orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("sessions.id"))
    amount_uzs: Mapped[int] = mapped_column(Integer)
    status: Mapped[PaymentStatus] = mapped_column(
        _str_enum(PaymentStatus), default=PaymentStatus.pending
    )
    provider: Mapped[PaymentProvider] = mapped_column(_str_enum(PaymentProvider))
    external_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    session: Mapped["Session"] = relationship(back_populates="payment_orders")
