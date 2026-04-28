from __future__ import annotations

from app.modules.assistant.field_dictionary import FieldSourceBasis, _sorted_unique_source_basis


def test_source_basis_entries_are_sorted_and_deduplicated_deterministically() -> None:
    items = [
        FieldSourceBasis(
            source_type="backend_schema",
            source_name="B",
            page_id="C-01",
            module_key="customers",
            evidence="zeta",
        ),
        FieldSourceBasis(
            source_type="frontend_locale",
            source_name="A",
            page_id="C-01",
            module_key="customers",
            evidence="alpha",
        ),
        FieldSourceBasis(
            source_type="backend_schema",
            source_name="B",
            page_id="C-01",
            module_key="customers",
            evidence="zeta",
        ),
    ]

    normalized = _sorted_unique_source_basis(items)

    assert normalized == [
        FieldSourceBasis(
            source_type="backend_schema",
            source_name="B",
            page_id="C-01",
            module_key="customers",
            evidence="zeta",
        ),
        FieldSourceBasis(
            source_type="frontend_locale",
            source_name="A",
            page_id="C-01",
            module_key="customers",
            evidence="alpha",
        ),
    ]
