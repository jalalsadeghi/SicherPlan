from __future__ import annotations

from app.modules.assistant.provider import AssistantProviderResult, MockAssistantProvider
from app.modules.assistant.service import AssistantRuntimeConfig, AssistantService
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext
from tests.modules.assistant.test_capabilities import _NoopAssistantRepository


def _context(*permission_keys: str) -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="assistant-session-1",
        user_id="assistant-user-1",
        tenant_id="tenant-1",
        role_keys=frozenset({"tenant_admin"}),
        permission_keys=frozenset(permission_keys),
        scopes=(AuthenticatedRoleScope(role_key="tenant_admin", scope_type="tenant"),),
        request_id="assistant-req-1",
    )


class _SmokeProvider:
    def __init__(self, *, should_fail: bool = False) -> None:
        self.should_fail = should_fail

    def generate(self, request):
        del request
        if self.should_fail:
            from app.modules.assistant.provider import AssistantProviderUnavailableError

            raise AssistantProviderUnavailableError("upstream unavailable", provider_error_type="APIConnectionError")
        return AssistantProviderResult(
            final_response={
                "answer": "provider ok",
                "confidence": "high",
                "out_of_scope": False,
                "diagnosis": [],
                "links": [],
                "missing_permissions": [],
                "next_steps": [],
                "tool_trace_id": None,
            },
            raw_text="provider ok",
            provider_mode="openai",
            model_name="gpt-4o",
        )


def _service(provider) -> AssistantService:
    return AssistantService(
        runtime_config=AssistantRuntimeConfig(
            enabled=True,
            provider_mode="openai",
            env="development",
            openai_configured=True,
            mock_provider_allowed=False,
            response_model="gpt-4o",
            store_responses=False,
        ),
        repository=_NoopAssistantRepository(),
        provider=provider,
    )


def test_provider_status_returns_safe_configuration_fields() -> None:
    payload = _service(MockAssistantProvider()).get_provider_status(_context("assistant.admin"))

    serialized = payload.model_dump(mode="json")
    assert serialized["provider_mode"] == "openai"
    assert serialized["openai_configured"] is True
    assert serialized["model"] == "gpt-4o"
    assert serialized["store_responses"] is False
    assert "sdk_available" in serialized
    assert "sdk_version" in serialized


def test_provider_smoke_test_returns_safe_success_payload() -> None:
    payload = _service(_SmokeProvider()).run_provider_smoke_test(_context("assistant.admin"))

    serialized = payload.model_dump(mode="json")
    assert serialized["ok"] is True
    assert serialized["provider_mode"] == "openai"
    assert serialized["model"] == "gpt-4o"
    assert serialized["answer"] == "provider ok"
    assert serialized["confidence"] == "high"


def test_provider_smoke_test_returns_safe_failure_payload() -> None:
    payload = _service(_SmokeProvider(should_fail=True)).run_provider_smoke_test(_context("assistant.admin"))

    serialized = payload.model_dump(mode="json")
    assert serialized["ok"] is False
    assert serialized["provider_mode"] == "openai"
    assert serialized["model"] == "gpt-4o"
    assert serialized["error_code"] == "assistant.provider.unavailable"
