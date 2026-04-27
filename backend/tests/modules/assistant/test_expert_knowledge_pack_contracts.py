from __future__ import annotations

from app.modules.assistant.expert_knowledge_pack import EXPERT_KNOWLEDGE_PACK_BY_KEY
from app.modules.assistant.page_help_seed import ASSISTANT_PAGE_HELP_SEEDS
from app.modules.assistant.workflow_help import detect_workflow_intent


def test_contract_pack_is_ambiguity_aware_and_source_grounded() -> None:
    pack = EXPERT_KNOWLEDGE_PACK_BY_KEY["contract_or_document_register"]

    assert "contract" in pack.aliases_en
    assert "vertrag" in pack.aliases_de
    assert {"PS-01", "C-01", "P-02", "S-01"}.issubset(set(pack.linked_page_ids))
    assert any("standalone contract module is not verified" in fact.text_en for fact in pack.facts)
    assert any("Wenn der Nutzer nur Vertrag sagt" in fact.text_de for fact in pack.facts)
    assert all(fact.source_basis for fact in pack.facts)
    assert detect_workflow_intent("Wie registriere ich einen neuen Vertrag?").intent == "contract_or_document_register"


def test_platform_services_page_help_keeps_unverified_labels_explicit() -> None:
    manifest = next(
        item.manifest_json
        for item in ASSISTANT_PAGE_HELP_SEEDS
        if item.page_id == "PS-01" and item.language_code == "de"
    )

    assert manifest["source_status"] == "verified"
    assert any(action["verified"] is False and action["label_status"] == "unverified" for action in manifest["primary_actions"])
    assert len(manifest["form_sections"]) >= 2
