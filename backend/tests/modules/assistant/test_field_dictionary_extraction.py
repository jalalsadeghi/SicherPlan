from __future__ import annotations

from app.modules.assistant.field_dictionary import build_field_lookup_corpus


def test_customer_legal_name_field_definition_is_extracted() -> None:
    corpus = build_field_lookup_corpus()

    field = next(item for item in corpus.field_definitions if item.field_key == "customer.legal_name")

    assert field.canonical_name == "legal_name"
    assert field.module_key == "customers"
    assert field.page_id == "C-01"
    assert field.entity_type == "Customer"
    assert "Rechtlicher Name" in field.labels["de"]
    assert "Legal name" in field.labels["en"]
    assert "customerAdmin.fields.legalName" in field.aliases
    assert "customerDraft.legal_name" in field.aliases
    assert field.confidence == "high"
    assert any(item.source_type == "frontend_locale" for item in field.source_basis)
    assert any(item.source_type == "frontend_component" for item in field.source_basis)
    assert any(item.source_type in {"typescript_api_interface", "backend_schema"} for item in field.source_basis)
    assert any("customerAdmin.fields.legalName" in item.evidence for item in field.source_basis)


def test_customer_legal_name_definition_text_is_grounded() -> None:
    corpus = build_field_lookup_corpus()
    field = next(item for item in corpus.field_definitions if item.field_key == "customer.legal_name")

    assert "contracts" in (field.definition_en or "").lower()
    assert "rechnungen" in (field.definition_de or "").lower()
    assert field.related_fields
