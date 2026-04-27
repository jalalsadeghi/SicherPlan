from __future__ import annotations

from app.modules.assistant.grounding import AssistantGroundingContext, AssistantGroundingSource
from app.modules.assistant.provider import MockAssistantProvider
from app.modules.assistant.service import AssistantRuntimeConfig, AssistantService
from tests.modules.assistant.test_out_of_scope import InMemoryAssistantRepository


def test_grounding_context_trimming_drops_shallow_sources_first() -> None:
    service = AssistantService(
        runtime_config=AssistantRuntimeConfig(
            enabled=True,
            provider_mode="openai",
            openai_configured=True,
            response_model="gpt-4o",
            max_total_grounding_chars=500,
            max_grounding_chars_per_source=260,
        ),
        repository=InMemoryAssistantRepository(),
        provider=MockAssistantProvider(),
    )
    grounding_context = AssistantGroundingContext(
        detected_language="de",
        response_language="de",
        auth_summary={"scope_kind": "tenant"},
        retrieval_plan={"intent_category": "workflow_how_to"},
        sources=[
            AssistantGroundingSource(
                source_id="route-1",
                source_type="page_route",
                source_name="route",
                page_id="C-01",
                title="Customers Workspace",
                content="route hint " * 80,
                facts={"path": "/admin/customers"},
            ),
            AssistantGroundingSource(
                source_id="current-1",
                source_type="current_route",
                source_name="current",
                page_id="F-02",
                content="current route " * 80,
                facts={"path": "/admin/dashboard"},
            ),
            AssistantGroundingSource(
                source_id="workflow-1",
                source_type="workflow",
                source_name="customer_create",
                page_id="C-01",
                module_key="customers",
                title="Customer create",
                content="verified workflow fact " * 80,
                facts={"workflow_keys": ["customer_create"]},
                content_bearing=True,
                verified=True,
            ),
        ],
    )

    trimmed = service._trim_grounding_context_for_budget(grounding_context)  # noqa: SLF001

    kept_types = [source.source_type for source in trimmed.sources]
    assert "workflow" in kept_types
    assert trimmed.grounding_trimmed is True
    assert trimmed.trim_reason == "token_budget"
    assert "current_route" not in kept_types
