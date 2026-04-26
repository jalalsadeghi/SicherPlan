"""Central RAG orchestration for in-scope assistant answers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from app.modules.assistant.grounding import AssistantGroundingContext
from app.modules.assistant.prompt_builder import AssistantToolResultSummary


@dataclass(frozen=True)
class AssistantRagRunResult:
    grounding_context: AssistantGroundingContext
    initial_tool_results: list[AssistantToolResultSummary]
    provider_payload: dict[str, Any]


class AssistantRagOrchestrator:
    """Coordinates retrieval, grounding, provider generation, and final validation."""

    def __init__(
        self,
        *,
        build_grounding_context: Callable[..., tuple[AssistantGroundingContext, list[AssistantToolResultSummary]]],
        generate_in_scope_response: Callable[..., dict[str, Any]],
    ) -> None:
        self._build_grounding_context = build_grounding_context
        self._generate_in_scope_response = generate_in_scope_response

    def run(
        self,
        *,
        conversation: Any,
        cleaned_message: str,
        route_context: dict[str, Any] | None,
        detected_language: str,
        response_language: str,
        actor: Any,
    ) -> AssistantRagRunResult:
        grounding_context, initial_tool_results = self._build_grounding_context(
            conversation=conversation,
            cleaned_message=cleaned_message,
            route_context=route_context,
            detected_language=detected_language,
            response_language=response_language,
            actor=actor,
        )
        provider_payload = self._generate_in_scope_response(
            conversation=conversation,
            cleaned_message=cleaned_message,
            route_context=route_context,
            detected_language=detected_language,
            response_language=response_language,
            actor=actor,
            grounding_context=grounding_context,
            initial_tool_results=initial_tool_results,
        )
        return AssistantRagRunResult(
            grounding_context=grounding_context,
            initial_tool_results=initial_tool_results,
            provider_payload=provider_payload,
        )
