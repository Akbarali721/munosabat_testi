"""Result page, access, and premium unlock tests."""

from __future__ import annotations

import json
import unittest
import uuid
from datetime import datetime
from unittest.mock import MagicMock

from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import (
    Answer,
    Gender,
    Participant,
    ParticipantRole,
    RelationshipStage,
    ScenarioQuestion,
    Session,
    SessionStatus,
)
from app.question_seeds import ALL_QUESTIONS
from app.services.payment import unlock_premium_session
from app.services.result_experience import build_result_experience
from app.services.results import ScenarioComparison, SessionResult, build_session_result
from app.services.telegram_auth import TelegramWebAppUser


def _seed_questions(db) -> None:
    for item in ALL_QUESTIONS:
        stage = RelationshipStage(item["stage"])
        gender = Gender(item["gender_target"])
        db.add(
            ScenarioQuestion(
                scenario_id=item["scenario_id"],
                stage=stage,
                gender=gender,
                dimension=item["dimension"],
                text=item["text"],
                options_json=json.dumps(item["options"], ensure_ascii=False),
            )
        )
    db.commit()


def _comparison(
    scenario_id: str,
    dimension: str,
    weight_a: int,
    weight_b: int,
    title: str | None = None,
) -> ScenarioComparison:
    return ScenarioComparison(
        scenario_id=scenario_id,
        title=title or dimension,
        dimension=dimension,
        user_a_weight=weight_a,
        user_b_weight=weight_b,
        user_a_label=f"A:{weight_a}",
        user_b_label=f"B:{weight_b}",
        difference=abs(weight_a - weight_b),
        user_a_prompt="prompt a",
        user_b_prompt="prompt b",
    )


def _mock_participant(name: str, role: ParticipantRole) -> Participant:
    p = MagicMock(spec=Participant)
    p.name = name
    p.role = role
    p.gender = Gender.male if role == ParticipantRole.user_a else Gender.female
    return p


def _session_result(
    comparisons: list[ScenarioComparison],
    *,
    score: int | None = None,
) -> SessionResult:
    user_a = _mock_participant("Akbarali", ParticipantRole.user_a)
    user_b = _mock_participant("Shaxnoza", ParticipantRole.user_b)
    by_align = sorted(comparisons, key=lambda c: c.difference)
    gaps = sorted(comparisons, key=lambda c: c.difference, reverse=True)
    if score is None:
        max_diff = 3
        avg = sum(c.difference for c in comparisons) / len(comparisons)
        score = max(0, min(100, round(100 - (avg / max_diff * 100))))
    return SessionResult(
        compatibility_score=score,
        compatibility_summary="summary",
        strongest_areas=by_align[:3],
        misunderstanding_areas=gaps[:3],
        comparisons=comparisons,
        suggestions=["Suhbat qiling."],
        dimension_scores=[],
        talk_topics=[c.title for c in gaps[:3]],
        user_a=user_a,
        user_b=user_b,
    )


class ResultExperienceUnitTests(unittest.TestCase):
    def test_free_blocks_are_four(self):
        result = _session_result(
            [
                _comparison("apology", "conflict_style", 4, 4),
                _comparison("initiative", "communication_initiative", 4, 1),
                _comparison("compliment", "attention", 3, 3),
            ]
        )
        viewer = _mock_participant("Akbarali", ParticipantRole.user_a)
        exp = build_result_experience(
            result, viewer=viewer, stage_label="Yangi turmush qurganlar", premium_unlocked=False
        )
        self.assertEqual(len(exp.free_blocks), 4)
        self.assertEqual(exp.free_blocks[0].title, "Sizlarning kuchli tomoningiz")
        self.assertEqual(exp.free_blocks[1].title, "Qarashlaringiz farq qiladigan nuqta")
        self.assertIn("Akbarali", exp.personal_body)
        self.assertEqual(len(exp.premium_blocks), 7)
        self.assertTrue(all(b.locked for b in exp.premium_blocks))

    def test_personal_sentence_differs_by_viewer(self):
        comparisons = [
            _comparison("apology", "conflict_style", 4, 2),
            _comparison("support_day", "attention", 2, 4),
            _comparison("money_talk", "money_values", 4, 2),
            _comparison("quality_time", "respect_listening", 2, 4),
        ]
        result = _session_result(comparisons)
        exp_a = build_result_experience(
            result,
            viewer=_mock_participant("Akbarali", ParticipantRole.user_a),
            stage_label="Yangi turmush qurganlar",
            premium_unlocked=False,
        )
        exp_b = build_result_experience(
            result,
            viewer=_mock_participant("Shaxnoza", ParticipantRole.user_b),
            stage_label="Yangi turmush qurganlar",
            premium_unlocked=False,
        )
        self.assertIn("Akbarali", exp_a.personal_body)
        self.assertIn("Shaxnoza", exp_b.personal_body)
        self.assertNotEqual(exp_a.personal_body, exp_b.personal_body)

    def test_score_bands_change_strength_copy(self):
        comps = [
            _comparison("apology", "conflict_style", 4, 4),
            _comparison("initiative", "communication_initiative", 3, 3),
        ]
        high = build_result_experience(
            _session_result(comps, score=90),
            viewer=_mock_participant("Akbarali", ParticipantRole.user_a),
            stage_label="X",
            premium_unlocked=False,
        )
        low = build_result_experience(
            _session_result(comps, score=40),
            viewer=_mock_participant("Akbarali", ParticipantRole.user_a),
            stage_label="X",
            premium_unlocked=False,
        )
        self.assertNotEqual(high.free_blocks[0].body, low.free_blocks[0].body)

    def test_premium_unlock_reveals_content(self):
        result = _session_result(
            [
                _comparison("apology", "conflict_style", 4, 1),
                _comparison("future_step", "future_vision", 4, 4),
                _comparison("compliment", "attention", 3, 2),
            ]
        )
        locked = build_result_experience(
            result,
            viewer=_mock_participant("Akbarali", ParticipantRole.user_a),
            stage_label="X",
            premium_unlocked=False,
        )
        unlocked = build_result_experience(
            result,
            viewer=_mock_participant("Akbarali", ParticipantRole.user_a),
            stage_label="X",
            premium_unlocked=True,
        )
        self.assertTrue(all(b.locked for b in locked.premium_blocks))
        self.assertTrue(all(not b.locked for b in unlocked.premium_blocks))
        self.assertEqual(len(unlocked.premium_blocks), 7)
        self.assertTrue(any(b.items for b in unlocked.premium_blocks))
        titles = [b.title for b in unlocked.premium_blocks]
        self.assertTrue(any("Akbarali" in t for t in titles))
        self.assertTrue(any("Shaxnoza" in t for t in titles))

    def test_seven_teasers(self):
        result = _session_result(
            [_comparison("apology", "conflict_style", 3, 3)]
        )
        exp = build_result_experience(
            result,
            viewer=_mock_participant("Akbarali", ParticipantRole.user_a),
            stage_label="X",
            premium_unlocked=False,
        )
        teasers = [b.teaser for b in exp.premium_blocks]
        self.assertEqual(len(teasers), 7)
        self.assertEqual(len(set(teasers)), 7)


class InMemoryDbMixin:
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db = self.SessionLocal()
        _seed_questions(self.db)

        def override_get_db():
            try:
                yield self.db
            finally:
                pass

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app, raise_server_exceptions=True)

    def tearDown(self):
        app.dependency_overrides.clear()
        self.db.close()
        self.engine.dispose()

    def _create_complete_session(
        self,
        *,
        weight_a: int = 4,
        weight_b: int = 2,
        premium: bool = False,
    ) -> Session:
        session = Session(
            id=str(uuid.uuid4()),
            relationship_stage=RelationshipStage.in_relationship,
            status=SessionStatus.complete,
        )
        user_a = Participant(
            session_id=session.id,
            role=ParticipantRole.user_a,
            name="Akbarali",
            gender=Gender.male,
            completed_at=datetime.utcnow(),
            telegram_chat_id=1001,
        )
        user_b = Participant(
            session_id=session.id,
            role=ParticipantRole.user_b,
            name="Shaxnoza",
            gender=Gender.female,
            completed_at=datetime.utcnow(),
            telegram_chat_id=2002,
        )
        self.db.add(session)
        self.db.add(user_a)
        self.db.add(user_b)
        self.db.flush()

        questions_a = (
            self.db.query(ScenarioQuestion)
            .filter_by(stage=RelationshipStage.in_relationship, gender=Gender.male)
            .all()
        )
        questions_b = (
            self.db.query(ScenarioQuestion)
            .filter_by(stage=RelationshipStage.in_relationship, gender=Gender.female)
            .all()
        )
        by_sid_b = {q.scenario_id: q for q in questions_b}

        for q in questions_a:
            qb = by_sid_b[q.scenario_id]
            self.db.add(
                Answer(
                    session_id=session.id,
                    participant_id=user_a.id,
                    scenario_id=q.scenario_id,
                    scenario_question_id=q.id,
                    choice_index=0,
                    choice_weight=weight_a,
                )
            )
            self.db.add(
                Answer(
                    session_id=session.id,
                    participant_id=user_b.id,
                    scenario_id=q.scenario_id,
                    scenario_question_id=qb.id,
                    choice_index=0,
                    choice_weight=weight_b,
                )
            )

        if premium:
            unlock_premium_session(self.db, session)

        self.db.commit()
        self.db.refresh(session)
        return session

    def _get_result(self, session_id: str, telegram_id: int = 1001):
        with patch("app.routers.pages.validate_init_data") as mock_val:
            mock_val.return_value = TelegramWebAppUser(id=telegram_id)
            return self.client.get(
                f"/session/{session_id}/result",
                headers={"X-Telegram-Init-Data": "test"},
            )


class ResultAccessIntegrationTests(InMemoryDbMixin, unittest.TestCase):
    def test_incomplete_session_blocked(self):
        session = Session(
            id=str(uuid.uuid4()),
            relationship_stage=RelationshipStage.in_relationship,
            status=SessionStatus.awaiting_user_b,
        )
        user_a = Participant(
            session_id=session.id,
            role=ParticipantRole.user_a,
            name="Akbarali",
            gender=Gender.male,
            completed_at=datetime.utcnow(),
            telegram_chat_id=1001,
        )
        self.db.add(session)
        self.db.add(user_a)
        self.db.commit()

        response = self._get_result(session.id, 1001)
        self.assertEqual(response.status_code, 403)

    def test_only_user_a_done_blocked(self):
        session = Session(
            id=str(uuid.uuid4()),
            relationship_stage=RelationshipStage.in_relationship,
            status=SessionStatus.awaiting_user_b_answers,
        )
        user_a = Participant(
            session_id=session.id,
            role=ParticipantRole.user_a,
            name="Akbarali",
            gender=Gender.male,
            completed_at=datetime.utcnow(),
            telegram_chat_id=1001,
        )
        user_b = Participant(
            session_id=session.id,
            role=ParticipantRole.user_b,
            name="Shaxnoza",
            gender=Gender.female,
            completed_at=None,
            telegram_chat_id=2002,
        )
        self.db.add_all([session, user_a, user_b])
        self.db.commit()

        response = self._get_result(session.id, 1001)
        self.assertEqual(response.status_code, 403)
        response_b = self._get_result(session.id, 2002)
        self.assertEqual(response_b.status_code, 403)

    def test_both_users_can_open_result(self):
        session = self._create_complete_session()
        for telegram_id in (1001, 2002):
            response = self._get_result(session.id, telegram_id)
            self.assertEqual(response.status_code, 200, telegram_id)
            self.assertIn("Sizlarning munosabat tahlili tayyor", response.text)
            self.assertIn("Davom etish", response.text)
            self.assertIn("Sizlarning kuchli tomoningiz", response.text)
            self.assertIn("Sizlarning to‘liq tahlilingiz tayyor", response.text)
            self.assertIn("To‘liq tahlilni ikkalangiz uchun ochish", response.text)

    def test_personal_block_matches_viewer(self):
        session = self._create_complete_session()
        ra = self._get_result(session.id, 1001)
        rb = self._get_result(session.id, 2002)
        self.assertIn("Akbarali uchun shaxsiy xulosa", ra.text)
        self.assertIn("Shaxnoza uchun shaxsiy xulosa", rb.text)

    def test_premium_locked_shows_teasers_not_cta_when_unlocked(self):
        locked_session = self._create_complete_session(premium=False)
        unlocked_session = self._create_complete_session(premium=True)

        locked = self._get_result(locked_session.id, 1001)
        unlocked = self._get_result(unlocked_session.id, 2002)

        self.assertIn("To‘liq tahlilni ikkalangiz uchun ochish", locked.text)
        self.assertIn("qd-result-premium--locked", locked.text)
        self.assertNotIn("To‘liq tahlilni ikkalangiz uchun ochish", unlocked.text)
        self.assertIn("To‘liq tahlil ochilgan", unlocked.text)

    def test_user_a_unlock_opens_for_user_b(self):
        session = self._create_complete_session(premium=False)
        unlock = self.client.post(
            f"/session/{session.id}/premium/unlock",
            data={"role": "user_a"},
            follow_redirects=False,
        )
        self.assertEqual(unlock.status_code, 303)
        self.assertIn("role=user_a", unlock.headers["location"])
        self.assertIn("opened=1", unlock.headers["location"])

        for telegram_id in (1001, 2002):
            page = self._get_result(session.id, telegram_id)
            self.assertIn("To‘liq tahlil ochilgan", page.text)
            self.assertNotIn("To‘liq tahlilni ikkalangiz uchun ochish", page.text)

    def test_user_b_unlock_opens_for_user_a(self):
        session = self._create_complete_session(premium=False)
        unlock = self.client.post(
            f"/session/{session.id}/premium/unlock",
            data={"role": "user_b"},
            follow_redirects=False,
        )
        self.assertEqual(unlock.status_code, 303)
        self.assertIn("role=user_b", unlock.headers["location"])

        page_a = self._get_result(session.id, 1001)
        self.assertIn("To‘liq tahlil ochilgan", page_a.text)

    def test_second_unlock_does_not_break(self):
        session = self._create_complete_session(premium=True)
        again = self.client.post(
            f"/session/{session.id}/premium/unlock",
            data={"role": "user_b"},
            follow_redirects=False,
        )
        self.assertEqual(again.status_code, 303)
        page = self._get_result(session.id, 1001)
        self.assertEqual(page.status_code, 200)

    def test_invite_shows_share_when_partner_pending(self):
        session = self._create_complete_session()
        # Mark partner incomplete so invite page is shown
        user_b = (
            self.db.query(Participant)
            .filter_by(session_id=session.id, role=ParticipantRole.user_b)
            .one()
        )
        user_b.completed_at = None
        session.status = SessionStatus.awaiting_user_b_answers
        self.db.commit()
        with (
            patch("app.routers.pages.get_settings") as mock_pages_settings,
            patch("app.services.invite_share.get_settings") as mock_share_settings,
        ):
            for mock_settings in (mock_pages_settings, mock_share_settings):
                settings = mock_settings.return_value
                settings.telegram_bot_username = "bot"
                settings.resolve_bot_username.return_value = "bot"
                settings.webapp_base_url = "https://app.example"
            response = self.client.get(f"/invite/{session.id}", follow_redirects=False)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Birinchi qism tayyor", response.text)
        self.assertIn("Havolani ulashish", response.text)
        self.assertIn("Test holatini ko‘rish", response.text)

    def test_scoring_unchanged_by_experience_layer(self):
        session = self._create_complete_session(weight_a=4, weight_b=1)
        scored = build_session_result(self.db, session)
        self.assertIsNotNone(scored)
        assert scored is not None
        self.assertEqual(scored.compatibility_score, 0)

        aligned = self._create_complete_session(weight_a=3, weight_b=3)
        scored_ok = build_session_result(self.db, aligned)
        assert scored_ok is not None
        self.assertEqual(scored_ok.compatibility_score, 100)


if __name__ == "__main__":
    unittest.main()
