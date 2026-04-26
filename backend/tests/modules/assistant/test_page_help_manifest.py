from __future__ import annotations

from dataclasses import dataclass, field
import unittest
from uuid import uuid4

from app.modules.assistant.models import AssistantPageHelpManifest, AssistantPageRouteCatalog
from app.modules.assistant.page_catalog_seed import ASSISTANT_PAGE_ROUTE_SEEDS
from app.modules.assistant.page_help_seed import ASSISTANT_PAGE_HELP_SEEDS, seed_assistant_page_help_manifest
from app.modules.assistant.provider import MockAssistantProvider
from app.modules.assistant.service import AssistantRuntimeConfig, AssistantService
from app.modules.assistant.tools import build_default_tool_registry
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext


class _FakeScalarResult:
    def __init__(self, value) -> None:  # noqa: ANN001
        self.value = value

    def one_or_none(self):  # noqa: ANN201
        return self.value


class _SeedSession:
    def __init__(self) -> None:
        self.rows: list[AssistantPageHelpManifest] = []
        self.commits = 0

    def add(self, row) -> None:  # noqa: ANN001
        self.rows.append(row)

    def commit(self) -> None:
        self.commits += 1

    def scalars(self, statement):  # noqa: ANN001
        compiled = statement.compile()
        params = compiled.params
        for row in self.rows:
            if (
                row.page_id == params.get("page_id_1")
                and row.language_code == params.get("language_code_1")
                and row.manifest_version == params.get("manifest_version_1")
            ):
                return _FakeScalarResult(row)
        return _FakeScalarResult(None)


@dataclass
class _Repository:
    page_help_rows: list[AssistantPageHelpManifest] = field(default_factory=list)
    page_routes: list[AssistantPageRouteCatalog] = field(default_factory=list)
    audits: list[object] = field(default_factory=list)

    def create_conversation(self, **kwargs): raise AssertionError("unused")  # noqa: ANN003,E704
    def get_conversation_for_user(self, **kwargs): raise AssertionError("unused")  # noqa: ANN003,E704
    def list_messages_for_conversation(self, conversation_id: str): raise AssertionError("unused")
    def update_conversation_route_context(self, conversation, **kwargs): raise AssertionError("unused")  # noqa: ANN003,E704
    def create_messages(self, conversation, messages): raise AssertionError("unused")  # noqa: ANN001,ANN201
    def update_message_payload(self, message, **kwargs): raise AssertionError("unused")  # noqa: ANN003,E704

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


def _repository() -> _Repository:
    repository = _Repository()
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


def _service(repository: _Repository) -> AssistantService:
    return AssistantService(
        runtime_config=AssistantRuntimeConfig(enabled=True, provider_mode="mock"),
        repository=repository,
        provider=MockAssistantProvider(),
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


class TestAssistantPageHelpManifest(unittest.TestCase):
    def test_seed_is_idempotent(self) -> None:
        session = _SeedSession()

        first = seed_assistant_page_help_manifest(session)
        second = seed_assistant_page_help_manifest(session)

        self.assertEqual(first["inserted"], len(ASSISTANT_PAGE_HELP_SEEDS))
        self.assertEqual(first["updated"], 0)
        self.assertEqual(second["inserted"], 0)
        self.assertEqual(second["updated"], 0)
        self.assertEqual(len(session.rows), len(ASSISTANT_PAGE_HELP_SEEDS))

    def test_get_page_help_manifest_returns_verified_employee_create_action_for_writer(self) -> None:
        repository = _repository()
        result = _service(repository).get_page_help_manifest(
            page_id="E-01",
            language_code="en",
            actor=_context("assistant.chat.access", "employees.employee.read", "employees.employee.write"),
        )

        self.assertEqual(result.page_id, "E-01")
        self.assertEqual(result.source_status, "verified")
        self.assertEqual(result.actions[0].action_key, "employees.create.open")
        self.assertEqual(result.actions[0].label, "Create employee file")

    def test_get_page_help_manifest_filters_create_action_for_read_only_user(self) -> None:
        repository = _repository()
        result = _service(repository).get_page_help_manifest(
            page_id="E-01",
            language_code="en",
            actor=_context("assistant.chat.access", "employees.employee.read"),
        )

        self.assertEqual(result.page_id, "E-01")
        self.assertEqual(result.actions, [])

    def test_find_ui_action_returns_safe_missing_permission_state(self) -> None:
        repository = _repository()
        result = _service(repository).execute_registered_tool(
            tool_name="assistant.find_ui_action",
            input_data={"intent": "create_employee", "page_id": "E-01", "language_code": "en"},
            actor=_context("assistant.chat.access", "employees.employee.read"),
        )

        self.assertTrue(result.ok)
        self.assertEqual(result.data["action"]["label"], "Create employee file")
        self.assertFalse(result.data["action"]["allowed"])
        self.assertEqual(
            result.data["missing_permissions"],
            [
                {
                    "permission": "employees.employee.write",
                    "reason": "The current user does not have the required permission for this verified UI action.",
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
