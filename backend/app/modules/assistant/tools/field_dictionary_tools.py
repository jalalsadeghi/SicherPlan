"""Assistant tools for deterministic field and lookup dictionary search."""

from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel

from app.modules.assistant.field_dictionary import (
    explain_lookup_query,
    get_lookup_definition,
    get_platform_term_definition,
    search_field_dictionary,
    search_lookup_dictionary,
    search_platform_terms,
)
from app.modules.assistant.schemas import (
    AssistantFieldDictionaryMatchRead,
    AssistantFieldDictionarySearchInput,
    AssistantFieldDictionarySearchRead,
    AssistantFieldDictionarySourceBasisRead,
    AssistantLookupExplanationInput,
    AssistantLookupExplanationMatchRead,
    AssistantLookupExplanationRead,
    AssistantLookupExplanationValueRead,
    AssistantLookupDictionaryMatchRead,
    AssistantLookupDictionarySearchInput,
    AssistantLookupDictionarySearchRead,
    AssistantLookupDictionaryValueRead,
    AssistantMissingPermission,
    AssistantPlatformTermMatchRead,
    AssistantPlatformTermSearchInput,
    AssistantPlatformTermSearchRead,
)
from app.modules.assistant.tools import (
    AssistantToolClassification,
    AssistantToolDefinition,
    AssistantToolExecutionContext,
    AssistantToolResult,
    AssistantToolScopeBehavior,
)
from app.modules.customers.service import CustomerService
from app.modules.subcontractors.service import SubcontractorService


CUSTOMER_READ_PERMISSION = "customers.customer.read"
SUBCONTRACTOR_READ_PERMISSION = "subcontractors.company.read"


class AssistantLookupRepository(Protocol):
    def list_lookup_values(self, tenant_id: str | None, domain: str): ...  # noqa: ANN001


class SearchFieldDictionaryTool:
    def __init__(self) -> None:
        self.definition = AssistantToolDefinition(
            name="assistant.search_field_dictionary",
            description="Search the verified SicherPlan field dictionary for field labels, meanings, and page context.",
            input_schema=AssistantFieldDictionarySearchInput,
            output_schema=AssistantFieldDictionarySearchRead,
            required_permissions=["assistant.chat.access"],
            scope_behavior=AssistantToolScopeBehavior.CURRENT_USER,
            classification=AssistantToolClassification.READ_ONLY,
        )

    def execute(
        self,
        *,
        input_data: BaseModel,
        context: AssistantToolExecutionContext,
    ) -> AssistantToolResult:
        del context
        matches = search_field_dictionary(
            query=str(getattr(input_data, "query", "") or ""),
            language_code=getattr(input_data, "language_code", None),
            page_id=getattr(input_data, "page_id", None),
            route_name=getattr(input_data, "route_name", None),
            limit=int(getattr(input_data, "limit", 5) or 5),
        )
        payload = AssistantFieldDictionarySearchRead(
            matches=[
                AssistantFieldDictionaryMatchRead(
                    field_key=item.field_key,
                    label=item.label,
                    entity_type=item.entity_type,
                    module_key=item.module_key,
                    page_id=item.page_id,
                    definition=item.definition,
                    required=item.required,
                    confidence=item.confidence,
                    score=item.score,
                    source_basis=[
                        AssistantFieldDictionarySourceBasisRead(
                            source_type=basis.source_type,
                            source_name=basis.source_name,
                            evidence=basis.evidence,
                            page_id=basis.page_id,
                            module_key=basis.module_key,
                        )
                        for basis in item.source_basis
                    ],
                )
                for item in matches
            ],
            ambiguous=_is_ambiguous_field_result(matches),
            safe_note=None if matches else "No verified field definition matched this query.",
        ).model_dump(mode="json")
        return AssistantToolResult(ok=True, tool_name=self.definition.name, data=payload)


class ExplainLookupOrOptionTool:
    def __init__(
        self,
        *,
        customer_repository: AssistantLookupRepository | None = None,
        subcontractor_repository: AssistantLookupRepository | None = None,
        core_repository: AssistantLookupRepository | None = None,
    ) -> None:
        self.customer_repository = customer_repository
        self.subcontractor_repository = subcontractor_repository
        self.core_repository = core_repository
        self.definition = AssistantToolDefinition(
            name="assistant.explain_lookup_or_option",
            description="Explain verified SicherPlan lookup catalogs and option meanings, including authorized tenant-specific catalogs when available.",
            input_schema=AssistantLookupExplanationInput,
            output_schema=AssistantLookupExplanationRead,
            required_permissions=["assistant.chat.access"],
            scope_behavior=AssistantToolScopeBehavior.CURRENT_USER,
            classification=AssistantToolClassification.READ_ONLY,
        )

    def execute(
        self,
        *,
        input_data: BaseModel,
        context: AssistantToolExecutionContext,
    ) -> AssistantToolResult:
        matches = explain_lookup_query(
            query=str(getattr(input_data, "query", "") or ""),
            language_code=getattr(input_data, "language_code", None),
            page_id=getattr(input_data, "page_id", None),
            route_name=getattr(input_data, "route_name", None),
            limit=int(getattr(input_data, "limit", 5) or 5),
        )
        missing_permissions: list[AssistantMissingPermission] = []
        payload_matches: list[AssistantLookupExplanationMatchRead] = []
        for match in matches:
            values = list(match.values)
            matched_values = list(match.matched_values)
            value_resolution = match.value_resolution
            definition = get_lookup_definition(match.lookup_key)
            if definition is not None and definition.value_source_kind == "tenant_lookup":
                values, matched_values, value_resolution, permission_row = self._resolve_dynamic_values(
                    lookup_key=match.lookup_key,
                    query=str(getattr(input_data, "query", "") or ""),
                    context=context,
                )
                if permission_row is not None:
                    missing_permissions.append(permission_row)
            payload_matches.append(
                AssistantLookupExplanationMatchRead(
                    lookup_key=match.lookup_key,
                    label=match.label,
                    entity_type=match.entity_type,
                    module_key=match.module_key,
                    page_id=match.page_id,
                    value_source_kind=match.value_source_kind,
                    value_resolution=value_resolution,
                    confidence=match.confidence,
                    score=match.score,
                    values=[
                        AssistantLookupExplanationValueRead(
                            value=value.value,
                            labels=dict(value.labels),
                            meaning_de=value.meaning_de,
                            meaning_en=value.meaning_en,
                            matched=any(item.value == value.value for item in matched_values),
                        )
                        for value in values
                    ],
                    matched_values=[
                        AssistantLookupExplanationValueRead(
                            value=value.value,
                            labels=dict(value.labels),
                            meaning_de=value.meaning_de,
                            meaning_en=value.meaning_en,
                            matched=True,
                        )
                        for value in matched_values
                    ],
                    source_basis=[
                        AssistantFieldDictionarySourceBasisRead(
                            source_type=basis.source_type,
                            source_name=basis.source_name,
                            evidence=basis.evidence,
                            page_id=basis.page_id,
                            module_key=basis.module_key,
                        )
                        for basis in match.source_basis
                    ],
                )
            )

        payload = AssistantLookupExplanationRead(
            matches=payload_matches,
            ambiguous=_is_ambiguous_lookup_explanation(payload_matches),
            missing_permissions=_dedupe_missing_permissions(missing_permissions),
            safe_note=None if payload_matches else "No verified lookup or option meaning matched this query.",
        ).model_dump(mode="json")
        return AssistantToolResult(ok=True, tool_name=self.definition.name, data=payload)

    def _resolve_dynamic_values(
        self,
        *,
        lookup_key: str,
        query: str,
        context: AssistantToolExecutionContext,
    ) -> tuple[list[Any], list[Any], str, AssistantMissingPermission | None]:
        permission: str | None = None
        repository: AssistantLookupRepository | None = None
        domain: str | None = None
        if lookup_key.startswith("customer."):
            field_name = lookup_key.split(".", 1)[1]
            domain = CustomerService.LOOKUP_DOMAINS.get(field_name)
            permission = CUSTOMER_READ_PERMISSION
            repository = self.customer_repository or self.core_repository
        elif lookup_key.startswith("subcontractor."):
            field_name = lookup_key.split(".", 1)[1]
            domain = SubcontractorService.LOOKUP_DOMAINS.get(field_name)
            permission = SUBCONTRACTOR_READ_PERMISSION
            repository = self.subcontractor_repository or self.core_repository
        if not domain or repository is None:
            return [], [], "unavailable", None
        if permission and permission not in context.permission_keys:
            return [], [], "permission_limited", AssistantMissingPermission(
                permission=permission,
                reason="The current user is not allowed to read the tenant-specific lookup catalog for this field.",
            )
        rows = repository.list_lookup_values(context.tenant_id, domain)
        values = [_lookup_value_from_dynamic_row(row) for row in rows]
        matched_values = _match_dynamic_values(values, query)
        return values, matched_values, "dynamic", None


class SearchPlatformTermsTool:
    def __init__(self) -> None:
        self.definition = AssistantToolDefinition(
            name="assistant.search_platform_terms",
            description="Search verified SicherPlan platform UI terms and domain concepts such as Demand groups.",
            input_schema=AssistantPlatformTermSearchInput,
            output_schema=AssistantPlatformTermSearchRead,
            required_permissions=["assistant.chat.access"],
            scope_behavior=AssistantToolScopeBehavior.CURRENT_USER,
            classification=AssistantToolClassification.READ_ONLY,
        )

    def execute(
        self,
        *,
        input_data: BaseModel,
        context: AssistantToolExecutionContext,
    ) -> AssistantToolResult:
        del context
        matches = search_platform_terms(
            query=str(getattr(input_data, "query", "") or ""),
            language_code=getattr(input_data, "language_code", None),
            page_id=getattr(input_data, "page_id", None),
            route_name=getattr(input_data, "route_name", None),
            limit=int(getattr(input_data, "limit", 5) or 5),
        )
        payload = AssistantPlatformTermSearchRead(
            matches=[
                AssistantPlatformTermMatchRead(
                    term_key=item.term_key,
                    label=item.label,
                    module_key=item.module_key,
                    page_id=item.page_id,
                    concept_type=item.concept_type,
                    ui_term_type=item.ui_term_type,
                    definition=item.definition,
                    ui_contexts=list(getattr(get_platform_term_definition(item.term_key), "ui_contexts", [])),
                    related_terms=list(getattr(get_platform_term_definition(item.term_key), "related_terms", [])),
                    confidence=item.confidence,
                    score=item.score,
                    source_basis=[
                        AssistantFieldDictionarySourceBasisRead(
                            source_type=basis.source_type,
                            source_name=basis.source_name,
                            evidence=basis.evidence,
                            page_id=basis.page_id,
                            module_key=basis.module_key,
                        )
                        for basis in item.source_basis
                    ],
                )
                for item in matches
            ],
            ambiguous=_is_ambiguous_platform_term_result(matches),
            safe_note=None if matches else "No verified platform term matched this query.",
        ).model_dump(mode="json")
        return AssistantToolResult(ok=True, tool_name=self.definition.name, data=payload)

class SearchLookupDictionaryTool:
    def __init__(self) -> None:
        self.definition = AssistantToolDefinition(
            name="assistant.search_lookup_dictionary",
            description="Search the verified SicherPlan lookup and status dictionary for option meanings and context.",
            input_schema=AssistantLookupDictionarySearchInput,
            output_schema=AssistantLookupDictionarySearchRead,
            required_permissions=["assistant.chat.access"],
            scope_behavior=AssistantToolScopeBehavior.CURRENT_USER,
            classification=AssistantToolClassification.READ_ONLY,
        )

    def execute(
        self,
        *,
        input_data: BaseModel,
        context: AssistantToolExecutionContext,
    ) -> AssistantToolResult:
        del context
        matches = search_lookup_dictionary(
            query=str(getattr(input_data, "query", "") or ""),
            language_code=getattr(input_data, "language_code", None),
            page_id=getattr(input_data, "page_id", None),
            route_name=getattr(input_data, "route_name", None),
            limit=int(getattr(input_data, "limit", 5) or 5),
        )
        payload = AssistantLookupDictionarySearchRead(
            matches=[
                AssistantLookupDictionaryMatchRead(
                    lookup_key=item.lookup_key,
                    label=item.label,
                    entity_type=item.entity_type,
                    module_key=item.module_key,
                    page_id=item.page_id,
                    value_source_kind=item.value_source_kind,
                    score=item.score,
                    values=[
                        AssistantLookupDictionaryValueRead(
                            value=value.value,
                            labels=dict(value.labels),
                            meaning_de=value.meaning_de,
                            meaning_en=value.meaning_en,
                        )
                        for value in _lookup_values(item.lookup_key)
                    ],
                    source_basis=[
                        AssistantFieldDictionarySourceBasisRead(
                            source_type=basis.source_type,
                            source_name=basis.source_name,
                            evidence=basis.evidence,
                            page_id=basis.page_id,
                            module_key=basis.module_key,
                        )
                        for basis in item.source_basis
                    ],
                    confidence=_lookup_confidence(item.lookup_key),
                )
                for item in matches
            ],
            ambiguous=_is_ambiguous_lookup_result(matches),
            safe_note=None if matches else "No verified lookup definition matched this query.",
        ).model_dump(mode="json")
        return AssistantToolResult(ok=True, tool_name=self.definition.name, data=payload)


def _is_ambiguous_field_result(matches) -> bool:  # noqa: ANN001, ANN202
    if len(matches) < 2:
        return False
    return matches[0].score == matches[1].score and matches[0].field_key != matches[1].field_key


def _is_ambiguous_lookup_result(matches) -> bool:  # noqa: ANN001, ANN202
    if len(matches) < 2:
        return False
    return matches[0].score == matches[1].score and matches[0].lookup_key != matches[1].lookup_key


def _is_ambiguous_platform_term_result(matches) -> bool:  # noqa: ANN001, ANN202
    if len(matches) < 2:
        return False
    return matches[0].score == matches[1].score and matches[0].term_key != matches[1].term_key


def _is_ambiguous_lookup_explanation(matches: list[AssistantLookupExplanationMatchRead]) -> bool:
    if len(matches) < 2:
        return False
    return matches[0].lookup_key != matches[1].lookup_key and matches[0].label == matches[1].label


def _lookup_values(lookup_key: str):  # noqa: ANN201
    from app.modules.assistant.field_dictionary import build_field_lookup_corpus

    for definition in build_field_lookup_corpus().lookup_definitions:
        if definition.lookup_key == lookup_key:
            return definition.values
    return []


def _lookup_confidence(lookup_key: str) -> str:
    from app.modules.assistant.field_dictionary import build_field_lookup_corpus

    for definition in build_field_lookup_corpus().lookup_definitions:
        if definition.lookup_key == lookup_key:
            return definition.confidence
    return "low"


def _lookup_value_from_dynamic_row(row: Any) -> AssistantLookupDictionaryValueRead:
    code = str(getattr(row, "code", "") or "").strip()
    label = str(getattr(row, "label", code) or code).strip()
    description = str(getattr(row, "description", "") or "").strip()
    return AssistantLookupDictionaryValueRead(
        value=code,
        labels={"de": label, "en": label},
        meaning_de=description or None,
        meaning_en=description or None,
    )


def _match_dynamic_values(values: list[AssistantLookupDictionaryValueRead], query: str) -> list[AssistantLookupDictionaryValueRead]:
    normalized_query = _normalize_lookup_query(query)
    matches: list[AssistantLookupDictionaryValueRead] = []
    for value in values:
        haystacks = [value.value, *(value.labels.values())]
        for candidate in haystacks:
            normalized = _normalize_lookup_query(candidate)
            if not normalized:
                continue
            if normalized == normalized_query or normalized in normalized_query or normalized_query in normalized:
                matches.append(value)
                break
    return matches


def _normalize_lookup_query(value: str) -> str:
    return " ".join(str(value or "").strip().lower().replace("_", " ").split())


def _dedupe_missing_permissions(
    rows: list[AssistantMissingPermission],
) -> list[AssistantMissingPermission]:
    result: list[AssistantMissingPermission] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        key = (row.permission, row.reason)
        if key in seen:
            continue
        seen.add(key)
        result.append(row)
    return result
