from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pytest

from app.modules.assistant import field_dictionary as field_dictionary_module
from app.modules.assistant.field_dictionary import detect_field_or_lookup_signal, search_field_dictionary, search_lookup_dictionary
from app.modules.assistant.provider import AssistantProviderRequest, AssistantProviderResult
from app.modules.assistant.schemas import AssistantMessageCreate
from app.modules.assistant.service import AssistantRuntimeConfig, AssistantService
from app.modules.assistant.tools import build_default_tool_registry
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext
from tests.modules.assistant.test_how_to_employee_create_exact_ui import _repository as page_help_repository


def _stage_like_root(tmp_path: Path) -> Path:
    root = tmp_path / "stage-backend-only"
    (root / "backend").mkdir(parents=True)
    return root


@pytest.fixture
def artifact_only_runtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    stage_root = _stage_like_root(tmp_path)
    field_dictionary_module._load_runtime_field_lookup_corpus.cache_clear()
    field_dictionary_module._build_field_lookup_corpus_from_sources.cache_clear()
    monkeypatch.setattr(field_dictionary_module, "_repo_root", lambda: stage_root)


@dataclass
class _CapturingProvider:
    requests: list[AssistantProviderRequest] = field(default_factory=list)

    def generate(self, request: AssistantProviderRequest) -> AssistantProviderResult:
        self.requests.append(request)
        return AssistantProviderResult(
            final_response={
                "answer": "Vertragsreferenz bezeichnet die Kundenvertragsreferenz im Abrechnungsprofil.",
                "confidence": "medium",
                "out_of_scope": False,
                "diagnosis": [],
                "links": [],
                "missing_permissions": [],
                "next_steps": [],
                "tool_trace_id": None,
                "source_basis": [],
            },
            raw_text="Vertragsreferenz bezeichnet die Kundenvertragsreferenz im Abrechnungsprofil.",
            provider_name="fake-openai",
            provider_mode="openai",
            model_name="gpt-test",
        )


def _context(*permissions: str) -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="assistant-session-1",
        user_id="assistant-user-1",
        tenant_id="tenant-1",
        role_keys=frozenset({"tenant_admin"}),
        permission_keys=frozenset(permissions),
        scopes=(AuthenticatedRoleScope(role_key="tenant_admin", scope_type="tenant"),),
        request_id="assistant-req-1",
    )


@pytest.mark.parametrize(
    ("question", "page_id", "route_name", "expected_key", "search_kind"),
    [
        ("was bedeutet Vertragsreferenz", "C-01", "SicherPlanCustomers", "customer.contract_reference", "field"),
        ("was bedeutet Rechtlicher Name", "C-01", "SicherPlanCustomers", "customer.legal_name", "field"),
        ("was bedeutet Kundennummer", "C-01", "SicherPlanCustomers", "customer.customer_number", "field"),
        ("was bedeutet Externe Referenz", "C-01", "SicherPlanCustomers", "customer.external_ref", "field"),
        ("was bedeutet Freigabestatus", "P-03", "SicherPlanPlanningShifts", "planning.release_state", "lookup"),
        ("was bedeutet release_ready", "P-03", "SicherPlanPlanningShifts", "planning.release_state", "lookup"),
        ("was bedeutet Schichttyp", "P-03", "SicherPlanPlanningShifts", "shift.shift_type_code", "field"),
    ],
)
def test_stage_parity_artifact_only_search_matrix(
    artifact_only_runtime: None,
    question: str,
    page_id: str,
    route_name: str,
    expected_key: str,
    search_kind: str,
) -> None:
    signal = detect_field_or_lookup_signal(question, page_id=page_id, route_name=route_name)
    assert signal is not None

    if search_kind == "field":
        matches = search_field_dictionary(
            query=question,
            language_code="de",
            page_id=page_id,
            route_name=route_name,
        )
        assert matches
        assert matches[0].field_key == expected_key
        assert matches[0].source_basis
    else:
        matches = search_lookup_dictionary(
            query=question,
            language_code="de",
            page_id=page_id,
            route_name=route_name,
        )
        assert matches
        assert matches[0].lookup_key == expected_key
        assert matches[0].source_basis


def test_stage_parity_service_path_uses_field_grounding_without_frontend_sources(
    artifact_only_runtime: None,
) -> None:
    repository = page_help_repository()
    provider = _CapturingProvider()
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale="de",
        last_route_name=None,
        last_route_path=None,
    )
    service = AssistantService(
        runtime_config=AssistantRuntimeConfig(
            enabled=True,
            provider_mode="openai",
            openai_configured=True,
            response_model="gpt-5.5-mini",
        ),
        repository=repository,
        provider=provider,
        tool_registry=build_default_tool_registry(
            audit_repository=repository,
            page_catalog_repository=repository,
            page_help_repository=repository,
        ),
    )

    response = service.add_message(
        conversation.id,
        AssistantMessageCreate(
            message="was bedeutet Vertragsreferenz",
            route_context={"page_id": "C-01", "route_name": "SicherPlanCustomers", "path": "/admin/customers"},
        ),
        _context("assistant.chat.access", "assistant.knowledge.read"),
    )

    assert response.out_of_scope is False
    assert response.response_language == "de"
    assert provider.requests
    grounding = provider.requests[0].grounding_context
    assert grounding is not None
    field_sources = [item for item in grounding["sources"] if item["source_type"] == "field_dictionary"]
    assert field_sources
    assert any(item["source_name"] == "customer.contract_reference" for item in field_sources)
