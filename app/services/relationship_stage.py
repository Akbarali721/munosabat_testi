"""UI start stages vs legacy DB stages and question-bank mapping."""

from app.models import RelationshipStage

# Shown on /start; only these values are accepted when creating a new session.
START_FORM_STAGES: tuple[RelationshipStage, ...] = (
    RelationshipStage.dating,
    RelationshipStage.newly_married,
)

ALLOWED_START_STAGE_VALUES = frozenset(s.value for s in START_FORM_STAGES)

# ScenarioQuestion rows remain seeded under legacy stage values.
QUESTION_BANK_STAGE: dict[RelationshipStage, RelationshipStage] = {
    RelationshipStage.dating: RelationshipStage.newly_meeting,
    RelationshipStage.newly_married: RelationshipStage.in_relationship,
}

# Pair narrative copy modules keyed by legacy stage values.
NARRATIVE_STAGE_VALUE: dict[RelationshipStage, str] = {
    RelationshipStage.dating: RelationshipStage.newly_meeting.value,
    RelationshipStage.newly_married: RelationshipStage.in_relationship.value,
    RelationshipStage.newly_meeting: RelationshipStage.newly_meeting.value,
    RelationshipStage.in_relationship: RelationshipStage.in_relationship.value,
}


def is_allowed_start_stage(stage: RelationshipStage) -> bool:
    return stage in START_FORM_STAGES


def question_bank_stage(stage: RelationshipStage) -> RelationshipStage:
    return QUESTION_BANK_STAGE.get(stage, stage)


def narrative_stage_value(stage: RelationshipStage) -> str:
    return NARRATIVE_STAGE_VALUE.get(stage, stage.value)


def uses_pair_narrative(stage: RelationshipStage) -> bool:
    key = narrative_stage_value(stage)
    return key in (
        RelationshipStage.newly_meeting.value,
        RelationshipStage.in_relationship.value,
    )
