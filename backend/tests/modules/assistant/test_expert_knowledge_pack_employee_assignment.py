from __future__ import annotations

from app.modules.assistant.expert_knowledge_pack import EXPERT_KNOWLEDGE_PACK_BY_KEY
from app.modules.assistant.workflow_help import WORKFLOW_HELP_SEEDS, detect_workflow_intent


def test_employee_assignment_pack_covers_readiness_validations_and_release() -> None:
    pack = EXPERT_KNOWLEDGE_PACK_BY_KEY["employee_assign_to_shift"]

    assert {"E-01", "P-03", "P-04", "P-05", "ES-01"}.issubset(set(pack.linked_page_ids))
    assert any("qualification mismatch" in fact.text_en for fact in pack.facts)
    assert any("Mitarbeiter-App" in fact.text_de for fact in pack.facts)
    assert all(fact.source_basis for fact in pack.facts)


def test_employee_assignment_workflow_seed_and_aliases_are_complete() -> None:
    workflow = WORKFLOW_HELP_SEEDS["employee_assign_to_shift"]

    assert detect_workflow_intent("How do I assign an employee to a shift?").intent == "employee_assign_to_shift"
    assert detect_workflow_intent("Wie weise ich einen Mitarbeiter einer Schicht zu?").intent == "employee_assign_to_shift"
    assert [step.page_id for step in workflow.steps] == ["E-01", "P-03", "P-04", "P-05"]
    assert all(step.source_basis for step in workflow.steps)
