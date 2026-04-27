from __future__ import annotations

from app.modules.assistant.expert_knowledge_pack import EXPERT_KNOWLEDGE_PACK_BY_KEY
from app.modules.assistant.page_help_seed import ASSISTANT_PAGE_HELP_SEEDS
from app.modules.assistant.workflow_help import detect_workflow_intent


def test_order_and_planning_packs_cover_customer_order_plan_and_planning_record() -> None:
    order_pack = EXPERT_KNOWLEDGE_PACK_BY_KEY["customer_order_create"]
    plan_pack = EXPERT_KNOWLEDGE_PACK_BY_KEY["customer_plan_create"]
    record_pack = EXPERT_KNOWLEDGE_PACK_BY_KEY["planning_record_create"]

    assert {"C-01", "P-02"}.issubset(set(order_pack.linked_page_ids))
    assert {"C-01", "P-02", "P-03"}.issubset(set(plan_pack.linked_page_ids))
    assert {"P-02", "P-03"}.issubset(set(record_pack.linked_page_ids))
    assert any("requirement type" in fact.text_en or "requirement lines" in fact.text_en for fact in order_pack.facts)
    assert any("Planungsdatensatz" in fact.text_de for fact in plan_pack.facts)
    assert all(fact.source_basis for fact in order_pack.facts + plan_pack.facts + record_pack.facts)


def test_order_and_planning_aliases_map_to_workflow_detection() -> None:
    assert detect_workflow_intent("How do I create a new order for a customer?").intent == "customer_order_create"
    assert detect_workflow_intent("Wie erstelle ich einen neuen Planungsdatensatz?").intent == "planning_record_create"


def test_planning_orders_page_help_is_verified_but_marks_action_labels_unverified() -> None:
    manifest = next(
        item.manifest_json
        for item in ASSISTANT_PAGE_HELP_SEEDS
        if item.page_id == "P-02" and item.language_code == "en"
    )

    assert manifest["source_status"] == "verified"
    assert any(action["label_status"] == "unverified" for action in manifest["primary_actions"])
    assert any(section["section_key"] == "planning_orders.requirements" for section in manifest["form_sections"])
