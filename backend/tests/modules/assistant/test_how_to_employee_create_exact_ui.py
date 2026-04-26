from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from app.modules.assistant.models import AssistantPageHelpManifest, AssistantPageRouteCatalog
from app.modules.assistant.page_catalog_seed import ASSISTANT_PAGE_ROUTE_SEEDS
from app.modules.assistant.page_help_seed import ASSISTANT_PAGE_HELP_SEEDS
from app.modules.assistant.provider import MockAssistantProvider
from app.modules.assistant.schemas import AssistantClientContextInput, AssistantMessageCreate
from app.modules.assistant.service import AssistantRuntimeConfig, AssistantService
from app.modules.assistant.tools import build_default_tool_registry
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext
from tests.modules.assistant.test_out_of_scope import InMemoryAssistantRepository


@dataclass
class _PageHelpRepository(InMemoryAssistantRepository):
    page_help_rows: list[AssistantPageHelpManifest] = field(default_factory=list)
    page_routes: list[AssistantPageRouteCatalog] = field(default_factory=list)
    audits: list[object] = field(default_factory=list)

    def create_tool_call_audit(self, *, record) -> object:  # noqa: ANN001, ANN201
        self.audits.append(record)
        return record

    def list_active_page_routes(self) -> list[AssistantPageRouteCatalog]:
        return [row for row in self.page_routes if row.active]

    def get_page_route_by_page_id(self, *, page_id: str) -> AssistantPageRouteCatalog | None:
        for row in self.page_routes:
            if row.page_id == page_id:
                return row
        return None

    def get_page_help_manifest(self, *, page_id: str, language_code: str | None = None) -> AssistantPageHelpManifest | None:
        candidates: list[str | None] = []
        if language_code:
            candidates.append(language_code)
        for fallback in ("en", "de", None):
            if fallback not in candidates:
                candidates.append(fallback)
        for candidate in candidates:
            for row in self.page_help_rows:
                if row.page_id == page_id and row.language_code == candidate and row.status in {"active", "unverified"}:
                    return row
        return None


def _repository() -> _PageHelpRepository:
    repository = _PageHelpRepository()
    repository.page_help_rows = [
        AssistantPageHelpManifest(
            id=str(uuid4()),
            page_id=seed.page_id,
            route_name=seed.route_name,
            path_template=seed.path_template,
            module_key=seed.module_key,
            language_code=seed.language_code,
            manifest_version=seed.manifest_version,
            status=seed.status,
            manifest_json=seed.manifest_json,
            verified_from=seed.verified_from,
        )
        for seed in ASSISTANT_PAGE_HELP_SEEDS
    ]
    repository.page_routes = [
        AssistantPageRouteCatalog(
            id=str(uuid4()),
            page_id=seed.page_id,
            label=seed.label,
            route_name=seed.route_name,
            path_template=seed.path_template,
            module_key=seed.module_key,
            api_families=list(seed.api_families) or None,
            required_permissions=list(seed.required_permissions) or None,
            allowed_role_keys=list(seed.allowed_role_keys) or None,
            scope_kind=seed.scope_kind,
            supports_entity_deep_link=seed.supports_entity_deep_link,
            entity_param_map=seed.entity_param_map,
            active=seed.active,
        )
        for seed in ASSISTANT_PAGE_ROUTE_SEEDS
    ]
    return repository


def _service(repository: _PageHelpRepository, provider: MockAssistantProvider) -> AssistantService:
    return AssistantService(
        runtime_config=AssistantRuntimeConfig(enabled=True, provider_mode="mock", max_input_chars=500),
        repository=repository,
        provider=provider,
        tool_registry=build_default_tool_registry(
            audit_repository=repository,
            page_catalog_repository=repository,
            page_help_repository=repository,
        ),
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


def test_verified_employee_create_guidance_uses_exact_label_and_skips_provider() -> None:
    repository = _repository()
    provider = MockAssistantProvider()
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale="fa",
        last_route_name=None,
        last_route_path=None,
    )

    response = _service(repository, provider).add_message(
        conversation.id,
        AssistantMessageCreate(
            message="چطور یک Employee جدید ثبت کنم؟",
            client_context=AssistantClientContextInput(ui_locale="fa"),
        ),
        _context("assistant.chat.access", "employees.employee.read", "employees.employee.write"),
    )

    assert response.out_of_scope is False
    assert "Create employee file" in response.answer
    assert "Create Employee or New Employee" not in response.answer
    assert provider.call_count == 0


def test_missing_permission_returns_safe_limitation_without_guessing() -> None:
    repository = _repository()
    provider = MockAssistantProvider()
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale="de",
        last_route_name=None,
        last_route_path=None,
    )

    response = _service(repository, provider).add_message(
        conversation.id,
        AssistantMessageCreate(message="Wie lege ich einen neuen Employee an?"),
        _context("assistant.chat.access", "employees.employee.read"),
    )

    assert response.out_of_scope is False
    assert "employees.employee.write" in response.answer
    assert "Create Employee or New Employee" not in response.answer
    assert provider.call_count == 0


def test_unverified_page_help_returns_safe_uncertainty_instead_of_guessed_label() -> None:
    repository = _repository()
    repository.page_help_rows = []
    provider = MockAssistantProvider()
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale="en",
        last_route_name=None,
        last_route_path=None,
    )

    response = _service(repository, provider).add_message(
        conversation.id,
        AssistantMessageCreate(message="How do I create a new Employee?"),
        _context("assistant.chat.access", "employees.employee.read", "employees.employee.write"),
    )

    assert response.out_of_scope is False
    assert "not confirmed" in response.answer
    assert "Create Employee or New Employee" not in response.answer
    assert provider.call_count == 0
