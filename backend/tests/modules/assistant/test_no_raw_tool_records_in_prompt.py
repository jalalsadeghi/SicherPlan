from __future__ import annotations

import json
from dataclasses import dataclass, field

from app.modules.assistant.provider import AssistantProviderRequest, AssistantProviderResult
from app.modules.assistant.schemas import AssistantMessageCreate
from app.modules.assistant.service import AssistantRuntimeConfig, AssistantService
from app.modules.assistant.tools import build_default_tool_registry
from tests.modules.assistant.test_shift_visibility_diagnostic import (
    _DiagnosticRepository,
    _context,
    _full_internal_permissions,
)


@dataclass
class _CapturingProvider:
    requests: list[AssistantProviderRequest] = field(default_factory=list)

    def generate(self, request: AssistantProviderRequest):  # noqa: ANN201
        self.requests.append(request)
        return AssistantProviderResult(
            final_response={
                "answer": "Ich habe die Freigabe geprüft.",
                "confidence": "medium",
                "out_of_scope": False,
                "diagnosis": [],
                "links": [],
                "missing_permissions": [],
                "next_steps": [],
                "tool_trace_id": None,
                "source_basis": [],
            },
            raw_text="Ich habe die Freigabe geprüft.",
            requested_tool_calls=[],
            response_id="resp-1",
            output_items=[],
            usage=None,
            provider_name="test",
            provider_mode="openai",
            model_name="gpt-4o",
            latency_ms=0,
            finish_reason="stop",
        )


def test_prompt_tool_result_payloads_do_not_contain_raw_records() -> None:
    repository = _DiagnosticRepository()
    provider = _CapturingProvider()
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="dispatcher-1",
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
            response_model="gpt-4o",
        ),
        repository=repository,
        provider=provider,
        tool_registry=build_default_tool_registry(
            audit_repository=repository,
            page_catalog_repository=repository,
            employee_repository=repository,
            planning_repository=repository,
        ),
    )

    service.add_message(
        conversation.id,
        AssistantMessageCreate(
            message="Ich habe Markus einer Schicht zugewiesen, aber sie ist in der mobilen App nicht sichtbar. Woran liegt das?"
        ),
        _context(role_keys=("dispatcher",), permission_keys=_full_internal_permissions()),
    )

    request = provider.requests[0]
    serialized = json.dumps(request.tool_results, ensure_ascii=False, sort_keys=True)

    assert '"matches"' not in serialized
    assert '"pages"' not in serialized
    assert '"workflows"' not in serialized
    assert '"actions"' not in serialized
    assert '"assignment"' not in serialized
    assert '"visibility"' not in serialized
    assert '"mobile_access"' not in serialized
    assert '"readiness"' not in serialized
    assert '"summary"' in serialized
    assert '"facts"' in serialized
