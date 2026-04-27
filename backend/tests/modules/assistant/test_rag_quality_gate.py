from __future__ import annotations

from app.modules.assistant.quality_gate import evaluate_rag_answer_quality
from app.modules.assistant.schemas import (
    AssistantConfidence,
    AssistantRagTraceRead,
    AssistantStructuredResponse,
)


def _response(*, answer: str, out_of_scope: bool = False, source_basis: list[dict] | None = None, confidence: str = "high") -> AssistantStructuredResponse:
    return AssistantStructuredResponse.model_validate(
        {
            "conversation_id": "conversation-1",
            "message_id": "message-1",
            "detected_language": "de",
            "response_language": "de",
            "answer": answer,
            "scope": "tenant",
            "confidence": confidence,
            "out_of_scope": out_of_scope,
            "source_basis": source_basis or [],
        }
    )


def _rag_trace(*, intent_category: str, content_bearing: int, missing_context: list[str] | None = None) -> AssistantRagTraceRead:
    return AssistantRagTraceRead.model_validate(
        {
            "trace_id": "trace-1",
            "provider_called": True,
            "provider_mode": "openai",
            "retrieval_executed": True,
            "grounding_attached": True,
            "grounding_source_count": max(content_bearing, 1),
            "content_bearing_source_count": content_bearing,
            "source_type_counts": {},
            "top_sources": [],
            "missing_context": missing_context or [],
            "retrieval_plan": {"intent_category": intent_category},
            "query_expansion": {},
        }
    )


def test_quality_gate_rejects_product_overview_out_of_scope() -> None:
    result = evaluate_rag_answer_quality(
        question="Bitte erklären Sie mir kurz und bündig, was diese Software genau macht.",
        classification={"reason": "product_overview"},
        response=_response(
            answer="Ich bin nur dafür vorgesehen, Fragen zur Plattform zu beantworten.",
            out_of_scope=True,
            confidence="medium",
        ),
        rag_trace=None,
    )

    assert result.passed is False
    assert "OVERVIEW_OUT_OF_SCOPE" in result.failures


def test_quality_gate_rejects_shallow_customer_registration_answer() -> None:
    result = evaluate_rag_answer_quality(
        question="Bitte erklären Sie mir genau, wie ich einen Kunden registrieren kann.",
        classification={"reason": "workflow_intent:customer_create"},
        response=_response(
            answer="Open the Customers workspace and look around there.",
            source_basis=[
                {
                    "source_type": "page_route",
                    "source_name": "SicherPlanCustomers",
                    "page_id": "C-01",
                    "title": "Customers Workspace",
                    "evidence": "/admin/customers",
                }
            ],
        ),
        rag_trace=_rag_trace(intent_category="workflow_how_to", content_bearing=0),
    )

    assert result.passed is False
    assert "NO_CONTENT_BEARING_SOURCES" in result.failures


def test_quality_gate_rejects_exact_ui_claim_without_page_help_basis() -> None:
    result = evaluate_rag_answer_quality(
        question="I want to create a new order. Tell me the exact button.",
        classification={"reason": "workflow_intent:customer_order_create"},
        response=_response(
            answer="Use the exact button label New Order in Orders & Planning Records.",
            source_basis=[
                {
                    "source_type": "workflow_help",
                    "source_name": "customer_order_create",
                    "page_id": "P-02",
                    "title": "Orders & Planning Records",
                    "evidence": "Workflow says to start in Orders & Planning Records.",
                }
            ],
        ),
        rag_trace=_rag_trace(intent_category="workflow_how_to", content_bearing=2),
    )

    assert result.passed is False
    assert "UNVERIFIED_EXACT_UI_CLAIM" in result.failures
