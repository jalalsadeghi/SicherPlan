from __future__ import annotations

from app.modules.assistant.provider import AssistantProviderRequest
from app.modules.assistant.schemas import (
    AssistantConfidence,
    AssistantRagTraceRead,
    AssistantStructuredResponse,
)
from tests.modules.assistant.golden_qa_support import GoldenQaCase, evaluate_golden_case


def test_bad_observed_answer_fails_golden_evaluation() -> None:
    case = GoldenQaCase(
        id="de_customer_create_bad",
        language="de",
        question="Bitte erklären Sie mir genau, wie ich einen Kunden registrieren kann.",
        expected_intent="customer_create",
        expected_pages=["C-01"],
        required_concepts=["kunden-workspace", "kundenstamm", "abrechnungsprofil"],
        forbidden_patterns=["out-of-scope"],
        requires_source_basis=True,
        min_content_bearing_sources=2,
    )
    response = AssistantStructuredResponse(
        conversation_id="conv-1",
        message_id="msg-1",
        detected_language="de",
        response_language="de",
        answer="Out-of-scope. Open /admin/customers.",
        scope="tenant",
        confidence=AssistantConfidence.HIGH,
        out_of_scope=False,
        source_basis=[],
        rag_trace=AssistantRagTraceRead(
            trace_id="trace-1",
            provider_called=True,
            provider_mode="openai",
            retrieval_executed=True,
            grounding_attached=True,
            grounding_source_count=1,
            content_bearing_source_count=0,
            source_type_counts={"page_route": 1},
            top_sources=[],
            missing_context=["content_bearing_sources"],
            retrieval_plan={"workflow_intent": "customer_create"},
            query_expansion={},
        ),
    )
    request = AssistantProviderRequest(
        conversation_id="conv-1",
        user_message=case.question,
        system_instructions="grounded",
        response_language="de",
        detected_language="de",
        grounding_context={"sources": [{"source_type": "page_route"}]},
    )

    failures = evaluate_golden_case(case=case, response=response, request=request)

    assert "insufficient_content_bearing_sources" in failures
    assert "missing_source_basis" in failures
    assert any(item.startswith("missing_concept:") for item in failures)
    assert any(item.startswith("forbidden_pattern:") for item in failures)
    assert "high_confidence_without_sufficient_source_basis" in failures
