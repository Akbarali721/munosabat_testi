from app.copy import in_relationship_pairs, newly_meeting_pairs
from app.models import RelationshipStage, ScenarioQuestion
from app.services.scenarios import get_option_value
from app.services.relationship_stage import narrative_stage_value

_PAIRED_STAGES = {
    RelationshipStage.newly_meeting.value: newly_meeting_pairs,
    RelationshipStage.in_relationship.value: in_relationship_pairs,
}


def option_value_for_choice(
    question: ScenarioQuestion | None,
    choice_index: int,
) -> str | None:
    if not question:
        return None
    return get_option_value(question, choice_index)


def pair_comparison_line(
    stage: RelationshipStage | str,
    pair_key: str,
    value_a: str | None,
    value_b: str | None,
    name_a: str,
    name_b: str,
) -> str:
    if isinstance(stage, RelationshipStage):
        stage_value = narrative_stage_value(stage)
    else:
        try:
            stage_value = narrative_stage_value(RelationshipStage(str(stage)))
        except ValueError:
            stage_value = str(stage)
    copy_mod = _PAIRED_STAGES.get(stage_value)
    if not copy_mod or not value_a or not value_b:
        return ""
    if value_a == value_b:
        return copy_mod.same_choice_line(pair_key, value_a, name_a, name_b)
    return copy_mod.different_choice_line(pair_key, value_a, value_b, name_a, name_b)
