from __future__ import annotations

from app.modules.assistant.lexicon import detect_domain_concepts, expand_assistant_query
from app.modules.assistant.retrieval_planner import build_retrieval_plan


def test_german_contract_question_expands_to_contract_document_and_platform_context() -> None:
    concepts = detect_domain_concepts("Wie registriere ich einen neuen Vertrag?")
    assert "contract" in concepts

    expanded = expand_assistant_query(
        "Wie registriere ich einen neuen Vertrag?",
        workflow_intent="contract_or_document_register",
    )

    assert "PS-01" in expanded.page_hints
    assert "C-01" in expanded.page_hints
    assert "P-02" in expanded.page_hints
    assert "platform_services" in expanded.module_hints


def test_contract_retrieval_plan_uses_contract_or_document_register_intent() -> None:
    plan = build_retrieval_plan(
        message="How do I add a contract document?",
        route_context={"page_id": "F-02", "path": "/admin/dashboard"},
    )

    assert plan.workflow_intent == "contract_or_document_register"
    assert {"PS-01", "C-01", "P-02", "S-01"}.issubset(set(plan.likely_page_ids))
    assert "F-02" not in plan.likely_page_ids
