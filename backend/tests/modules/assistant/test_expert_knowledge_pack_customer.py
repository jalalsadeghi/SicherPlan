from __future__ import annotations

from app.modules.assistant.expert_knowledge_pack import EXPERT_KNOWLEDGE_PACK_BY_KEY
from app.modules.assistant.page_help_seed import ASSISTANT_PAGE_HELP_SEEDS
from app.modules.assistant.workflow_help import detect_workflow_intent


def _manifest(page_id: str, language_code: str) -> dict[str, object]:
    seed = next(
        item for item in ASSISTANT_PAGE_HELP_SEEDS if item.page_id == page_id and item.language_code == language_code
    )
    return seed.manifest_json


def test_customer_create_pack_contains_rich_customer_facts_and_aliases() -> None:
    pack = EXPERT_KNOWLEDGE_PACK_BY_KEY["customer_create"]

    assert "register customer" in pack.aliases_en
    assert "kunden registrieren" in pack.aliases_de
    assert any("billing profile" in fact.text_en for fact in pack.facts)
    assert any("Preislisten" in fact.text_de or "Preislogik" in fact.text_de for fact in pack.facts)
    assert all(fact.source_basis for fact in pack.facts)
    assert detect_workflow_intent("Wie kann ich einen Kunden registrieren?").intent == "customer_create"


def test_customer_workspace_page_help_includes_verified_create_action_and_sections() -> None:
    manifest_en = _manifest("C-01", "en")
    manifest_de = _manifest("C-01", "de")

    actions_en = manifest_en["primary_actions"]
    actions_de = manifest_de["primary_actions"]

    assert manifest_en["source_status"] == "verified"
    assert any(action["action_key"] == "customers.create.open" and action["verified"] is True for action in actions_en)
    assert any(action["label"] == "New customer" and action["label_status"] == "verified" for action in actions_en)
    assert any(action["label"] == "Neuer Kunde" and action["label_status"] == "verified" for action in actions_de)
    assert len(manifest_en["form_sections"]) >= 2
    assert len(manifest_de["post_create_steps"]) >= 2
