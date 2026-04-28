from __future__ import annotations

from app.modules.assistant.field_dictionary import build_field_lookup_corpus


def test_customer_lifecycle_status_lookup_is_indexed() -> None:
    corpus = build_field_lookup_corpus()

    lookup = next(item for item in corpus.lookup_definitions if item.lookup_key == "customer.lifecycle_status")

    assert lookup.module_key == "customers"
    assert lookup.page_id == "C-01"
    assert lookup.value_source_kind == "static"
    values = {item.value: item for item in lookup.values}
    assert {"active", "inactive", "archived"}.issubset(values)
    assert values["active"].labels["de"] == "Aktiv"
    assert values["active"].labels["en"] == "Active"
    assert lookup.confidence == "high"


def test_dynamic_customer_metadata_lookups_do_not_index_private_tenant_values() -> None:
    corpus = build_field_lookup_corpus()

    lookup = next(item for item in corpus.lookup_definitions if item.lookup_key == "customer.legal_form_lookup_id")

    assert lookup.value_source_kind == "tenant_lookup"
    assert lookup.values == []
    assert any(item.source_name == "CustomerReferenceDataRead" for item in lookup.source_basis)
