"""Service layer for assistant capabilities and persistence."""

from __future__ import annotations

from dataclasses import dataclass, replace
import json
import logging
import re
from time import sleep
from typing import Any, Protocol
from uuid import uuid4

from app.errors import ApiException
from app.modules.assistant.classifier import AssistantClassificationResult, classify_assistant_message
from app.modules.assistant.diagnostic_prefetch import (
    AssistantDiagnosticPrefetchPlan,
    plan_diagnostic_prefetch,
)
from app.modules.assistant.diagnostics import (
    DIAGNOSTIC_TOOL_NAME,
    extract_shift_visibility_input,
    is_shift_visibility_question,
)
from app.modules.assistant.grounding import AssistantGroundingContext, AssistantGroundingSource
from app.modules.assistant.openai_client import get_openai_sdk_info
from app.modules.assistant.knowledge.retriever import AssistantKnowledgeRetriever
from app.modules.assistant.lexicon import expand_assistant_query
from app.modules.assistant.language import (
    choose_response_language,
    detect_message_language,
    out_of_scope_refusal,
    placeholder_diagnosis,
    unsafe_refusal,
)
from app.modules.assistant.page_help import (
    detect_ui_howto_intent,
)
from app.modules.assistant.page_catalog_seed import ASSISTANT_PAGE_ROUTE_SEEDS
from app.modules.assistant.prompt_builder import (
    AssistantMessageContext,
    AssistantToolDefinition as PromptToolDefinition,
    AssistantToolResultSummary,
    build_assistant_prompt,
    summarize_auth_context,
)
from app.modules.assistant.rag_orchestrator import AssistantRagOrchestrator
from app.modules.assistant.retrieval_planner import build_retrieval_plan
from app.modules.assistant.models import AssistantConversation, AssistantMessage
from app.modules.assistant.provider import (
    AssistantProvider,
    AssistantProviderConfigurationError,
    AssistantProviderAuthenticationError,
    AssistantProviderError,
    AssistantProviderInvalidRequestError,
    AssistantProviderRequest,
    AssistantProviderRateLimitError,
    AssistantProviderResult,
    AssistantProviderStructuredOutputError,
    AssistantProviderTimeoutError,
    AssistantProviderUnavailableError,
    estimate_tokens,
)
from app.modules.assistant.policy import (
    ASSISTANT_ADMIN,
    ASSISTANT_CHAT_ACCESS,
    ASSISTANT_FEEDBACK_WRITE,
    can_user_chat,
    can_user_reindex_knowledge,
    can_user_run_diagnostics,
    can_user_submit_feedback,
)
from app.modules.assistant.quality_gate import evaluate_rag_answer_quality
from app.modules.assistant.schemas import (
    AssistantCapabilitiesRead,
    AssistantClientContextInput,
    AssistantConfidence,
    AssistantConversationCreate,
    AssistantConversationRead,
    AssistantAnswerSegment,
    AssistantFeedbackCreate,
    AssistantFeedbackRead,
    AssistantKnowledgeChunkResult,
    AssistantMessageCreate,
    AssistantPageHelpManifestRead,
    AssistantProviderStatusRead,
    AssistantProviderSmokeTestRead,
    AssistantRagDebugSnapshotRead,
    AssistantRagQualityGateRead,
    AssistantRagTraceRead,
    AssistantRagTraceTopSource,
    AssistantSourceBasisItem,
    AssistantProviderStructuredOutput,
    AssistantStructuredResponse,
    AssistantRouteContextInput,
    AssistantScope,
    AssistantMissingPermission,
    AssistantNavigationLink,
)
from app.modules.assistant.tool_name_adapter import build_provider_tool_name_map
from app.modules.assistant.tools import AssistantToolExecutionContext, AssistantToolRegistry
from app.modules.assistant.workflow_help import detect_workflow_intent
from app.modules.iam.authz import RequestAuthorizationContext

logger = logging.getLogger(__name__)

_PAGE_ID_PATTERN = re.compile(r"\b[A-Z]{1,4}-\d{2}\b")
_PAGE_ID_SUFFIX_PATTERN_TEMPLATE = r"(?P<label>{label})\s*(?:\(\s*{page_id}\s*\)|[-–—]\s*{page_id})"
_WHITESPACE_BEFORE_PUNCTUATION_PATTERN = re.compile(r"\s+([,.;:!?])")
_MULTISPACE_PATTERN = re.compile(r"[ \t]{2,}")
_SPACE_AROUND_NEWLINE_PATTERN = re.compile(r" *\n *")

@dataclass(frozen=True)
class AssistantRuntimeConfig:
    enabled: bool
    provider_mode: str
    env: str = "development"
    openai_configured: bool = False
    mock_provider_allowed: bool = True
    response_model: str = ""
    store_responses: bool = False
    retrieval_mode: str = "lexical"
    retrieval_debug: bool = False
    max_input_chars: int = 12000
    max_provider_input_tokens: int = 14000
    max_continuation_input_tokens: int = 5000
    max_tool_calls: int = 8
    max_context_chunks: int = 8
    max_grounding_sources: int = 8
    max_grounding_chars_per_source: int = 700
    max_total_grounding_chars: int = 4500
    max_recent_messages_for_model: int = 6
    max_recent_messages_for_continuation: int = 0
    max_output_tokens: int = 900
    continuation_max_output_tokens: int = 700
    rate_limit_retry_seconds: int = 6
    rate_limit_max_retries: int = 2
    fallback_response_model: str = ""
    rag_quality_gate_mode: str = "off"

    @property
    def rag_enabled(self) -> bool:
        return self.enabled and self.provider_mode == "openai" and self.openai_configured


@dataclass(frozen=True)
class AssistantProviderDegradedFallbackCandidate(Exception):
    api_exception: ApiException
    grounding_context: AssistantGroundingContext
    tool_results: list[AssistantToolResultSummary]
    continuation_mode: str
    had_prior_provider_output: bool


class AssistantRepository(Protocol):
    def create_conversation(
        self,
        *,
        tenant_id: str | None,
        user_id: str,
        title: str | None,
        locale: str | None,
        last_route_name: str | None,
        last_route_path: str | None,
    ) -> AssistantConversation: ...

    def get_conversation_for_user(
        self,
        *,
        conversation_id: str,
        tenant_id: str | None,
        user_id: str,
    ) -> AssistantConversation | None: ...

    def list_messages_for_conversation(self, conversation_id: str) -> list[AssistantMessage]: ...

    def update_conversation_route_context(
        self,
        conversation: AssistantConversation,
        *,
        last_route_name: str | None,
        last_route_path: str | None,
    ) -> None: ...

    def create_messages(
        self,
        conversation: AssistantConversation,
        messages: list[AssistantMessage],
    ) -> list[AssistantMessage]: ...

    def update_message_payload(
        self,
        message: AssistantMessage,
        *,
        structured_payload: dict[str, Any],
    ) -> None: ...

    def get_message_for_conversation(
        self,
        *,
        conversation_id: str,
        message_id: str,
    ) -> AssistantMessage | None: ...

    def upsert_feedback(
        self,
        *,
        conversation_id: str,
        message_id: str,
        tenant_id: str | None,
        user_id: str,
        rating: str,
        comment: str | None,
    ): ...


class AssistantService:
    def __init__(
        self,
        runtime_config: AssistantRuntimeConfig,
        repository: AssistantRepository,
        provider: AssistantProvider,
        knowledge_retriever: AssistantKnowledgeRetriever | None = None,
        tool_registry: AssistantToolRegistry | None = None,
    ) -> None:
        self.runtime_config = runtime_config
        self.repository = repository
        self.provider = provider
        self.knowledge_retriever = knowledge_retriever
        self.tool_registry = tool_registry

    def get_capabilities(
        self,
        context: RequestAuthorizationContext,
    ) -> AssistantCapabilitiesRead:
        if not self.runtime_config.enabled:
            return AssistantCapabilitiesRead(
                enabled=False,
                provider_mode=self.runtime_config.provider_mode,
                openai_configured=self.runtime_config.openai_configured,
                mock_provider_allowed=self.runtime_config.mock_provider_allowed,
                rag_enabled=False,
                can_chat=False,
                can_run_diagnostics=False,
                can_reindex_knowledge=False,
                supported_features=[],
            )

        can_chat_value = can_user_chat(context)
        if not self._provider_runtime_usable_for_chat():
            can_chat_value = False
        can_run_diagnostics_value = can_user_run_diagnostics(context)
        can_reindex_value = can_user_reindex_knowledge(context)

        features = [
            "same_language_response",
            "structured_responses",
            "out_of_scope_policy",
        ]
        if self.runtime_config.rag_enabled:
            features.append("rag_grounding")
        if self.runtime_config.provider_mode == "mock":
            features.append("mock_provider")
            if self.runtime_config.mock_provider_allowed:
                features.append("mock_provider_allowed")
            else:
                features.append("mock_provider_blocked")
        elif self.runtime_config.provider_mode == "openai":
            if self.runtime_config.openai_configured:
                features.append("openai_provider_configured")

        return AssistantCapabilitiesRead(
            enabled=True,
            provider_mode=self.runtime_config.provider_mode,
            openai_configured=self.runtime_config.openai_configured,
            mock_provider_allowed=self.runtime_config.mock_provider_allowed,
            rag_enabled=self.runtime_config.rag_enabled,
            can_chat=can_chat_value,
            can_run_diagnostics=can_run_diagnostics_value,
            can_reindex_knowledge=can_reindex_value,
            supported_features=features,
        )

    def get_provider_status(
        self,
        context: RequestAuthorizationContext,
    ) -> AssistantProviderStatusRead:
        if "assistant.admin" not in context.permission_keys:
            raise ApiException(
                403,
                "iam.authorization.permission_denied",
                "errors.iam.authorization.permission_denied",
                {"permission_key": "assistant.admin"},
            )
        sdk_available, sdk_version = get_openai_sdk_info()
        return AssistantProviderStatusRead(
            provider_mode=self.runtime_config.provider_mode,
            openai_configured=self.runtime_config.openai_configured,
            model=self.runtime_config.response_model,
            mock_provider_allowed=self.runtime_config.mock_provider_allowed,
            store_responses=self.runtime_config.store_responses,
            rag_enabled=self.runtime_config.rag_enabled,
            sdk_available=sdk_available,
            sdk_version=sdk_version,
        )

    def run_provider_smoke_test(
        self,
        context: RequestAuthorizationContext,
    ) -> AssistantProviderSmokeTestRead:
        if "assistant.admin" not in context.permission_keys:
            raise ApiException(
                403,
                "iam.authorization.permission_denied",
                "errors.iam.authorization.permission_denied",
                {"permission_key": "assistant.admin"},
            )
        request = AssistantProviderRequest(
            conversation_id="assistant-provider-smoke-test",
            user_message="Return a valid structured assistant response saying provider ok.",
            system_instructions="Return a valid structured assistant response saying provider ok.",
            response_language="en",
            detected_language="en",
            grounding_context={
                "query": "provider smoke test",
                "sources": [],
                "auth_summary": {
                    "tenant_scope": "none",
                    "role_keys": [],
                    "permission_keys": [],
                },
            },
            available_tools=[],
            max_tool_calls=0,
            max_input_chars=256,
            metadata={"request_id": context.request_id, "tenant_id": None, "user_id": context.user_id},
        )
        try:
            result = self._call_provider(request)
        except ApiException as exc:
            return AssistantProviderSmokeTestRead(
                ok=False,
                provider_mode=self.runtime_config.provider_mode,
                model=self.runtime_config.response_model,
                error_code=exc.code,
            )
        return AssistantProviderSmokeTestRead(
            ok=True,
            provider_mode=self.runtime_config.provider_mode,
            model=self.runtime_config.response_model,
            answer=str(result.final_response.get("answer", "")) or result.raw_text,
            confidence=AssistantConfidence(str(result.final_response.get("confidence", "low"))),
            error_code=None,
        )

    def create_conversation(
        self,
        payload: AssistantConversationCreate,
        actor: RequestAuthorizationContext,
    ) -> AssistantConversationRead:
        self._require_chat_enabled(actor)
        route_context = self._sanitize_route_context(payload.initial_route)
        conversation = self.repository.create_conversation(
            tenant_id=actor.tenant_id,
            user_id=actor.user_id,
            title=self._sanitize_optional_text(payload.title, 255),
            locale=self._sanitize_optional_text(payload.locale, 16),
            last_route_name=route_context.get("route_name"),
            last_route_path=route_context.get("path"),
        )
        conversation.messages = []
        return AssistantConversationRead.model_validate(conversation)

    def get_page_help_manifest(
        self,
        *,
        page_id: str,
        language_code: str | None,
        actor: RequestAuthorizationContext,
    ) -> AssistantPageHelpManifestRead:
        self._require_chat_enabled(actor)
        result = self.execute_registered_tool(
            tool_name="assistant.get_page_help_manifest",
            input_data={"page_id": page_id, "language_code": language_code},
            actor=actor,
        )
        if not result.ok or not result.data:
            return AssistantPageHelpManifestRead(
                page_id=page_id,
                page_title=page_id,
                module_key="unknown",
                language_code=language_code,
                source_status="unverified",
            )
        return AssistantPageHelpManifestRead.model_validate(result.data)

    def list_available_tools(
        self,
        *,
        actor: RequestAuthorizationContext,
        conversation_id: str | None = None,
        message_id: str | None = None,
    ) -> list[dict[str, Any]]:
        self._require_chat_enabled(actor)
        if self.tool_registry is None:
            return []
        return self.tool_registry.list_available_tools(
            context=self._build_tool_execution_context(
                actor=actor,
                conversation_id=conversation_id,
                message_id=message_id,
            )
        )

    def execute_registered_tool(
        self,
        *,
        tool_name: str,
        input_data: dict[str, Any],
        actor: RequestAuthorizationContext,
        conversation_id: str | None = None,
        message_id: str | None = None,
    ):
        self._require_chat_enabled(actor)
        if self.tool_registry is None:
            raise ApiException(
                503,
                "assistant.tool_registry.unavailable",
                "errors.assistant.provider.unavailable",
            )
        return self.tool_registry.execute_tool(
            tool_name=tool_name,
            input_data=input_data,
            context=self._build_tool_execution_context(
                actor=actor,
                conversation_id=conversation_id,
                message_id=message_id,
            ),
        )

    def get_conversation(
        self,
        conversation_id: str,
        actor: RequestAuthorizationContext,
    ) -> AssistantConversationRead:
        self._require_chat_enabled(actor)
        conversation = self._require_conversation(conversation_id, actor)
        conversation.messages = self.repository.list_messages_for_conversation(conversation.id)
        return AssistantConversationRead.model_validate(conversation)

    def add_message(
        self,
        conversation_id: str,
        payload: AssistantMessageCreate,
        actor: RequestAuthorizationContext,
    ) -> AssistantStructuredResponse:
        self._require_chat_enabled(actor)
        conversation = self._require_conversation(conversation_id, actor)

        cleaned_message = payload.message.strip()
        if not cleaned_message:
            raise ApiException(
                400,
                "assistant.validation.message_empty",
                "errors.assistant.message.empty",
            )
        if len(cleaned_message) > self.runtime_config.max_input_chars:
            raise ApiException(
                400,
                "assistant.validation.message_too_long",
                "errors.assistant.message.too_long",
                {"max_input_chars": self.runtime_config.max_input_chars},
            )

        route_context = self._sanitize_route_context(payload.route_context)
        client_context = self._sanitize_client_context(payload.client_context)
        ui_locale = (client_context or {}).get("ui_locale") or conversation.locale
        detected_language = detect_message_language(cleaned_message, ui_locale=ui_locale)
        response_language = choose_response_language(detected_language, ui_locale=ui_locale)
        classification = classify_assistant_message(
            cleaned_message,
            route_context=route_context,
            client_context=client_context,
        )
        if route_context:
            self.repository.update_conversation_route_context(
                conversation,
                last_route_name=route_context.get("route_name"),
                last_route_path=route_context.get("path"),
            )

        user_message = AssistantMessage(
            conversation_id=conversation.id,
            tenant_id=actor.tenant_id,
            user_id=actor.user_id,
            role="user",
            content=cleaned_message,
            structured_payload=self._build_message_payload(
                route_context,
                client_context,
                detected_language=detected_language,
                response_language=response_language,
                classification=classification,
            ),
            detected_language=detected_language,
            response_language=response_language,
        )
        self.repository.create_messages(conversation, [user_message])
        if classification.is_out_of_scope:
            assistant_answer = self._build_assistant_answer(response_language, classification)
            assistant_result_payload = self._build_refusal_provider_payload(classification, assistant_answer)
            rag_trace = None
            rag_grounding_context = None
        else:
            try:
                rag_result = self._build_rag_orchestrator().run(
                    conversation=conversation,
                    cleaned_message=cleaned_message,
                    route_context=route_context,
                    detected_language=detected_language,
                    response_language=response_language,
                    actor=actor,
                )
                rag_grounding_context = rag_result.grounding_context
                assistant_result_payload = rag_result.provider_payload
            except AssistantProviderDegradedFallbackCandidate as degraded:
                rag_grounding_context = degraded.grounding_context
                if not self._can_build_provider_degraded_response(
                    classification=classification,
                    grounding_context=degraded.grounding_context,
                ):
                    raise degraded.api_exception
                assistant_result_payload = self._merge_provider_payload_with_tool_results(
                    self._build_provider_degraded_payload(
                        response_language=response_language,
                        grounding_context=degraded.grounding_context,
                        tool_results=degraded.tool_results,
                        continuation_mode=degraded.continuation_mode,
                        provider_error_code=degraded.api_exception.code,
                    ),
                    degraded.tool_results,
                )
            rag_trace = self._build_rag_trace(
                grounding_context=rag_grounding_context,
                provider_called=True,
            )
            assistant_answer = str(assistant_result_payload.get("answer", "")).strip()
            if not assistant_answer:
                raise ApiException(
                    502,
                    "assistant.provider.invalid_response",
                    "errors.assistant.provider.invalid_response",
                )

        assistant_message = AssistantMessage(
            conversation_id=conversation.id,
            tenant_id=actor.tenant_id,
            user_id=None,
            role="assistant",
            content=assistant_answer,
            structured_payload={},
            detected_language=detected_language,
            response_language=response_language,
        )
        self.repository.create_messages(conversation, [assistant_message])
        structured_response = self._build_structured_response(
            conversation=conversation,
            assistant_message=assistant_message,
            actor=actor,
            detected_language=detected_language,
            response_language=response_language,
            provider_payload=assistant_result_payload,
            classification=classification,
            grounding_context=rag_grounding_context if not classification.is_out_of_scope else None,
            rag_trace=rag_trace,
        )
        quality_gate = self._evaluate_quality_gate(
            question=cleaned_message,
            classification=classification,
            response=structured_response,
            rag_trace=rag_trace,
        )
        assistant_message.structured_payload = structured_response.model_dump(mode="json")
        assistant_message.structured_payload["classification"] = self._serialize_classification(classification)
        assistant_message.structured_payload["quality_gate"] = quality_gate.model_dump(mode="json")
        self.repository.update_message_payload(
            assistant_message,
            structured_payload=assistant_message.structured_payload,
        )
        self._handle_quality_gate_result(quality_gate)
        return structured_response

    def submit_feedback(
        self,
        conversation_id: str,
        payload: AssistantFeedbackCreate,
        actor: RequestAuthorizationContext,
    ) -> AssistantFeedbackRead:
        self._require_feedback_enabled(actor)
        conversation = self._require_conversation(conversation_id, actor)
        message = self.repository.get_message_for_conversation(
            conversation_id=conversation.id,
            message_id=payload.message_id,
        )
        if message is None:
            raise ApiException(
                404,
                "assistant.message.not_found",
                "errors.assistant.message.not_found",
            )
        if message.role != "assistant":
            raise ApiException(
                400,
                "assistant.feedback.invalid_target",
                "errors.assistant.feedback.invalid_target",
            )

        feedback = self.repository.upsert_feedback(
            conversation_id=conversation.id,
            message_id=message.id,
            tenant_id=actor.tenant_id,
            user_id=actor.user_id,
            rating=payload.rating.value,
            comment=self._sanitize_optional_text(payload.comment, 1000),
        )
        return AssistantFeedbackRead.model_validate(feedback)

    def get_rag_debug_snapshot(
        self,
        *,
        conversation_id: str,
        message_id: str,
        actor: RequestAuthorizationContext,
    ) -> AssistantRagDebugSnapshotRead:
        self._require_admin(actor)
        message = self.repository.get_message_for_conversation(
            conversation_id=conversation_id,
            message_id=message_id,
        )
        if message is None or message.role != "assistant":
            raise ApiException(
                404,
                "assistant.message.not_found",
                "errors.assistant.message.not_found",
            )
        if not actor.is_platform_admin and actor.tenant_id != message.tenant_id:
            raise ApiException(
                404,
                "assistant.message.not_found",
                "errors.assistant.message.not_found",
            )
        all_messages = self.repository.list_messages_for_conversation(conversation_id)
        question = self._find_question_for_assistant_message(all_messages=all_messages, message_id=message.id)
        structured_payload = message.structured_payload if isinstance(message.structured_payload, dict) else {}
        rag_trace_payload = structured_payload.get("rag_trace")
        rag_trace = (
            AssistantRagTraceRead.model_validate(rag_trace_payload)
            if isinstance(rag_trace_payload, dict)
            else None
        )
        response = AssistantStructuredResponse.model_validate(
            {
                "conversation_id": structured_payload.get("conversation_id", conversation_id),
                "message_id": structured_payload.get("message_id", message.id),
                "detected_language": structured_payload.get("detected_language", message.detected_language or "unknown"),
                "response_language": structured_payload.get("response_language", message.response_language or "unknown"),
                "answer": structured_payload.get("answer", message.content),
                "provider_degraded": structured_payload.get("provider_degraded", False),
                "scope": structured_payload.get("scope", "unknown"),
                "confidence": structured_payload.get("confidence", "low"),
                "out_of_scope": structured_payload.get("out_of_scope", False),
                "diagnosis": structured_payload.get("diagnosis", []),
                "links": structured_payload.get("links", []),
                "missing_permissions": structured_payload.get("missing_permissions", []),
                "next_steps": structured_payload.get("next_steps", []),
                "tool_trace_id": structured_payload.get("tool_trace_id"),
                "rag_trace_id": structured_payload.get("rag_trace_id"),
                "source_basis": structured_payload.get("source_basis", []),
                "rag_trace": rag_trace_payload,
            }
        )
        quality_gate = AssistantRagQualityGateRead.model_validate(
            structured_payload.get("quality_gate")
            or self._evaluate_quality_gate(
                question=question,
                classification=structured_payload.get("classification"),
                response=response,
                rag_trace=rag_trace,
            ).model_dump(mode="json")
        )
        return AssistantRagDebugSnapshotRead(
            question=question,
            detected_language=response.detected_language,
            classification=structured_payload.get("classification") if isinstance(structured_payload.get("classification"), dict) else {},
            retrieval_plan=rag_trace.retrieval_plan if rag_trace is not None else {},
            expanded_query=rag_trace.query_expansion if rag_trace is not None else {},
            top_sources=rag_trace.top_sources if rag_trace is not None else [],
            content_bearing_source_count=rag_trace.content_bearing_source_count if rag_trace is not None else 0,
            grounding_sent_to_provider=rag_trace.grounding_attached if rag_trace is not None else False,
            provider_called=rag_trace.provider_called if rag_trace is not None else False,
            source_basis_returned=response.source_basis,
            final_answer=response.answer,
            confidence=response.confidence,
            links=response.links,
            quality_gate=quality_gate,
        )

    def _require_chat_enabled(self, actor: RequestAuthorizationContext) -> None:
        if not self.runtime_config.enabled:
            raise ApiException(
                403,
                "assistant.disabled",
                "errors.assistant.disabled",
            )
        if not can_user_chat(actor):
            raise ApiException(
                403,
                "iam.authorization.permission_denied",
                "errors.iam.authorization.permission_denied",
                {"permission_key": ASSISTANT_CHAT_ACCESS},
            )
        if not self._provider_runtime_usable_for_chat():
            if self.runtime_config.provider_mode == "mock":
                raise ApiException(
                    503,
                    "assistant.provider.mock_not_allowed",
                    "errors.assistant.provider.mock_not_allowed",
                )
            raise ApiException(
                503,
                "assistant.provider.unavailable",
                "errors.assistant.provider.unavailable",
            )

    @staticmethod
    def _require_admin(actor: RequestAuthorizationContext) -> None:
        if actor.is_platform_admin or actor.has_permission(ASSISTANT_ADMIN):
            return
        raise ApiException(
            403,
            "iam.authorization.permission_denied",
            "errors.iam.authorization.permission_denied",
            {"permission_key": ASSISTANT_ADMIN},
        )

    @staticmethod
    def _find_question_for_assistant_message(
        *,
        all_messages: list[AssistantMessage],
        message_id: str,
    ) -> str:
        target_index = next((index for index, item in enumerate(all_messages) if item.id == message_id), -1)
        if target_index < 0:
            return ""
        for item in reversed(all_messages[:target_index]):
            if item.role == "user":
                return item.content
        return ""

    def _require_feedback_enabled(self, actor: RequestAuthorizationContext) -> None:
        if not self.runtime_config.enabled:
            raise ApiException(
                403,
                "assistant.disabled",
                "errors.assistant.disabled",
            )
        if not can_user_submit_feedback(actor):
            raise ApiException(
                403,
                "iam.authorization.permission_denied",
                "errors.iam.authorization.permission_denied",
                {"permission_key": ASSISTANT_FEEDBACK_WRITE},
            )

    def _require_conversation(
        self,
        conversation_id: str,
        actor: RequestAuthorizationContext,
    ) -> AssistantConversation:
        conversation = self.repository.get_conversation_for_user(
            conversation_id=conversation_id,
            tenant_id=actor.tenant_id,
            user_id=actor.user_id,
        )
        if conversation is None:
            raise ApiException(
                404,
                "assistant.conversation.not_found",
                "errors.assistant.conversation.not_found",
            )
        return conversation

    @staticmethod
    def _sanitize_optional_text(value: str | None, max_length: int) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            return None
        return cleaned[:max_length]

    def _sanitize_route_context(
        self,
        route_context: AssistantRouteContextInput | None,
    ) -> dict[str, Any] | None:
        if route_context is None:
            return None
        query = self._sanitize_query(route_context.query or {})
        payload = {
            "path": self._sanitize_optional_text(route_context.path, 500),
            "route_name": self._sanitize_optional_text(route_context.route_name, 255),
            "page_id": self._sanitize_optional_text(route_context.page_id, 120),
            "query": query or None,
        }
        return {key: value for key, value in payload.items() if value is not None} or None

    def _sanitize_client_context(
        self,
        client_context: AssistantClientContextInput | None,
    ) -> dict[str, Any] | None:
        if client_context is None:
            return None
        payload = {
            "timezone": self._sanitize_optional_text(client_context.timezone, 64),
            "ui_locale": self._sanitize_optional_text(client_context.ui_locale, 16),
            "visible_page_title": self._sanitize_optional_text(client_context.visible_page_title, 255),
        }
        return {key: value for key, value in payload.items() if value is not None} or None

    def _sanitize_query(self, values: dict[str, Any]) -> dict[str, Any]:
        safe: dict[str, Any] = {}
        for key, value in values.items():
            if key in {"tenant_id", "user_id"}:
                continue
            sanitized_key = self._sanitize_optional_text(str(key), 120)
            if sanitized_key is None:
                continue
            sanitized_value = self._sanitize_json_value(value)
            if sanitized_value is not None:
                safe[sanitized_key] = sanitized_value
        return safe

    def _sanitize_json_value(self, value: Any) -> Any:
        if value is None or isinstance(value, (bool, float, int)):
            return value
        if isinstance(value, str):
            return value.strip()[:255]
        if isinstance(value, list):
            sanitized_items = [self._sanitize_json_value(item) for item in value[:10]]
            return [item for item in sanitized_items if item is not None]
        return None

    @staticmethod
    def _build_message_payload(
        route_context: dict[str, Any] | None,
        client_context: dict[str, Any] | None,
        *,
        detected_language: str | None = None,
        response_language: str | None = None,
        classification: AssistantClassificationResult | None = None,
    ) -> dict[str, Any] | None:
        payload: dict[str, Any] = {}
        if detected_language is not None:
            payload["detected_language"] = detected_language
        if response_language is not None:
            payload["response_language"] = response_language
        if classification is not None:
            payload["classification"] = AssistantService._serialize_classification(classification)
        if route_context:
            payload["route_context"] = route_context
        if client_context:
            payload["client_context"] = client_context
        return payload or None

    def _build_structured_response(
        self,
        *,
        conversation: AssistantConversation,
        assistant_message: AssistantMessage,
        actor: RequestAuthorizationContext,
        detected_language: str,
        response_language: str,
        provider_payload: dict[str, Any],
        classification: AssistantClassificationResult,
        grounding_context: AssistantGroundingContext | None = None,
        rag_trace: AssistantRagTraceRead | None,
    ) -> AssistantStructuredResponse:
        validated_links = self._validate_provider_links(
            links_payload=provider_payload.get("links", []),
            actor=actor,
            conversation_id=conversation.id,
        )
        grounding_links = self._grounding_links(grounding_context)
        answer_text = str(provider_payload.get("answer", ""))
        enriched_links = self._ensure_answer_links(
            answer_text=answer_text,
            validated_links=self._merge_navigation_links(validated_links, grounding_links),
            actor=actor,
            conversation_id=conversation.id,
        )
        normalized_answer, answer_segments = self._normalize_user_facing_answer_links(
            answer_text=answer_text,
            allowed_links=enriched_links,
        )
        confidence = AssistantConfidence(
            str(provider_payload.get("confidence", classification.confidence))
        )
        if (
            rag_trace is not None
            and self._requires_content_bearing_sources(rag_trace.retrieval_plan)
            and rag_trace.content_bearing_source_count <= 0
        ):
            confidence = AssistantConfidence.LOW
        source_basis = self._build_validated_source_basis(
            provider_payload=provider_payload,
            grounding_context=grounding_context,
            rag_trace=rag_trace,
        )
        if (
            rag_trace is not None
            and str(rag_trace.retrieval_plan.get("intent_category") or "").strip() == "ui_action_question"
            and not any(item.source_type == "page_help_manifest" for item in source_basis)
        ):
            confidence = AssistantConfidence.LOW
        answer_text = str(provider_payload.get("answer", "")).casefold()
        if self._mentions_precise_ui_claim(answer_text) and not any(
            item.source_type == "page_help_manifest" for item in source_basis
        ):
            confidence = AssistantConfidence.LOW
        return AssistantStructuredResponse(
            conversation_id=conversation.id,
            message_id=assistant_message.id,
            detected_language=detected_language,
            response_language=response_language,
            answer=normalized_answer,
            provider_degraded=bool(provider_payload.get("provider_degraded", False)),
            answer_segments=answer_segments,
            scope=self._infer_scope(actor),
            confidence=confidence,
            out_of_scope=bool(provider_payload.get("out_of_scope", classification.is_out_of_scope)),
            diagnosis=provider_payload.get("diagnosis", []),
            links=enriched_links,
            missing_permissions=provider_payload.get("missing_permissions", []),
            next_steps=provider_payload.get("next_steps", []),
            tool_trace_id=provider_payload.get("tool_trace_id"),
            rag_trace_id=rag_trace.trace_id if rag_trace is not None else None,
            source_basis=source_basis,
            rag_trace=rag_trace,
        )

    @staticmethod
    def _merge_navigation_links(
        primary_links: list[dict[str, Any]],
        secondary_links: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        merged: list[dict[str, Any]] = []
        seen_keys: set[tuple[str, str]] = set()
        for row in [*primary_links, *secondary_links]:
            if not isinstance(row, dict):
                continue
            page_id = str(row.get("page_id") or "").strip()
            path = str(row.get("path") or "").strip()
            if not path:
                continue
            dedupe_key = (page_id, path)
            if dedupe_key in seen_keys:
                continue
            seen_keys.add(dedupe_key)
            merged.append(row)
        return merged

    @staticmethod
    def _grounding_links(
        grounding_context: AssistantGroundingContext | None,
    ) -> list[dict[str, Any]]:
        if grounding_context is None:
            return []
        links: list[dict[str, Any]] = []
        for source in grounding_context.sources:
            if source.source_type != "allowed_navigation_link":
                continue
            facts = source.facts if isinstance(source.facts, dict) else {}
            link = facts.get("link")
            if isinstance(link, dict):
                links.append(link)
        return links

    def _build_rag_orchestrator(self) -> AssistantRagOrchestrator:
        return AssistantRagOrchestrator(
            build_grounding_context=self._build_grounding_context,
            generate_in_scope_response=self._generate_in_scope_response,
        )

    @staticmethod
    def _build_assistant_answer(
        response_language: str,
        classification: AssistantClassificationResult,
    ) -> str:
        if classification.is_unsafe:
            return unsafe_refusal(response_language)
        if classification.is_out_of_scope:
            return out_of_scope_refusal(response_language)
        raise RuntimeError("In-scope answers must be provided by the assistant provider.")

    def _build_grounding_context(
        self,
        *,
        conversation: AssistantConversation,
        cleaned_message: str,
        route_context: dict[str, Any] | None,
        detected_language: str,
        response_language: str,
        actor: RequestAuthorizationContext,
    ) -> tuple[AssistantGroundingContext, list[AssistantToolResultSummary]]:
        plan = build_retrieval_plan(message=cleaned_message, route_context=route_context)
        diagnostic_prefetch = plan_diagnostic_prefetch(
            message=cleaned_message,
            detected_language=detected_language,
            route_context=route_context,
        )
        auth_summary = summarize_auth_context(actor)
        expanded_query = expand_assistant_query(
            cleaned_message,
            workflow_intent=plan.workflow_intent,
            ui_page_id=route_context.get("page_id") if isinstance(route_context, dict) else None,
        )
        knowledge_chunks = self._retrieve_knowledge_chunks(
            query=cleaned_message,
            response_language=response_language,
            route_context=route_context,
            actor=actor,
            workflow_intent=plan.workflow_intent,
            planned_page_ids=list(plan.likely_page_ids),
            planned_module_keys=list(plan.likely_module_keys),
        )

        sources: list[AssistantGroundingSource] = []
        missing_context: list[str] = []
        if route_context:
            sources.append(
                AssistantGroundingSource(
                    source_id=f"current_route:{route_context.get('page_id') or route_context.get('path') or 'unknown'}",
                    source_type="current_route",
                    source_name="current_route",
                    page_id=route_context.get("page_id"),
                    module_key=str(route_context.get("page_id") or "")[:1] or None,
                    title=route_context.get("route_name"),
                    content=route_context.get("path"),
                    facts=route_context,
                    score=1.0,
                    verified=False,
                    content_bearing=False,
                    permission_checked=True,
                )
            )

        for chunk in knowledge_chunks:
            sources.append(
                AssistantGroundingSource(
                    source_id=chunk.source_id or chunk.chunk_id,
                    source_type="knowledge_chunk",
                    source_name=chunk.source_name,
                    page_id=chunk.page_id,
                    module_key=chunk.module_key,
                    title=chunk.title,
                    content=chunk.content,
                    facts={
                        "rank": chunk.rank,
                        "matched_by": chunk.matched_by,
                        "source_type": chunk.source_type,
                        "source_path": chunk.source_path,
                        "source_language": chunk.source_language,
                        "content_preview": chunk.content_preview,
                        "workflow_keys": list(chunk.workflow_keys),
                        "api_families": list(chunk.api_families),
                        "domain_terms": list(chunk.domain_terms),
                        "language_aliases": list(chunk.language_aliases),
                    },
                    score=chunk.score,
                    verified=True,
                    content_bearing=True,
                    permission_checked=True,
                )
            )
        if "knowledge_chunks" in plan.required_sources and not knowledge_chunks:
            missing_context.append("knowledge_chunks")

        summaries: list[AssistantToolResultSummary] = []
        if self.tool_registry is not None:
            workflow_intent = detect_workflow_intent(cleaned_message)
            ui_intent = detect_ui_howto_intent(cleaned_message)

            if workflow_intent is not None:
                workflow_result = self.execute_registered_tool(
                    tool_name="assistant.search_workflow_help",
                    input_data={
                        "query": cleaned_message,
                        "workflow_key": workflow_intent.intent,
                        "language_code": response_language,
                        "limit": 3,
                    },
                    actor=actor,
                    conversation_id=conversation.id,
                )
                summaries.append(self._tool_result_to_summary(workflow_result))
                sources.extend(self._grounding_sources_from_tool_result("workflow", workflow_result))

            if ui_intent is not None:
                ui_result = self.execute_registered_tool(
                    tool_name="assistant.find_ui_action",
                    input_data={
                        "intent": ui_intent.intent,
                        "page_id": ui_intent.page_id,
                        "language_code": response_language,
                    },
                    actor=actor,
                    conversation_id=conversation.id,
                )
                summaries.append(self._tool_result_to_summary(ui_result))
                sources.extend(self._grounding_sources_from_tool_result("ui_action", ui_result))

            for page_id in plan.likely_page_ids[:4]:
                page_result = self.execute_registered_tool(
                    tool_name="assistant.search_accessible_pages",
                    input_data={"page_id": page_id, "limit": 1},
                    actor=actor,
                    conversation_id=conversation.id,
                )
                summaries.append(self._tool_result_to_summary(page_result))
                sources.extend(self._grounding_sources_from_tool_result("page_route", page_result))

                page_help_result = self.execute_registered_tool(
                    tool_name="assistant.get_page_help_manifest",
                    input_data={"page_id": page_id, "language_code": response_language},
                    actor=actor,
                    conversation_id=conversation.id,
                )
                summaries.append(self._tool_result_to_summary(page_help_result))
                sources.extend(self._grounding_sources_from_tool_result("page_help_manifest", page_help_result))

            if diagnostic_prefetch is not None:
                diagnostic_sources, diagnostic_summaries = self._build_diagnostic_prefetch_sources(
                    conversation=conversation,
                    actor=actor,
                    response_language=response_language,
                    plan=diagnostic_prefetch,
                )
                summaries.extend(diagnostic_summaries)
                sources.extend(diagnostic_sources)
            elif is_shift_visibility_question(cleaned_message, route_context):
                diagnostic_input = extract_shift_visibility_input(
                    message=cleaned_message,
                    detected_language=detected_language,
                    route_context=route_context,
                )
                diagnostic_result = self.execute_registered_tool(
                    tool_name=DIAGNOSTIC_TOOL_NAME,
                    input_data=diagnostic_input.model_dump(mode="json", exclude_none=True),
                    actor=actor,
                    conversation_id=conversation.id,
                )
                summaries.append(self._tool_result_to_summary(diagnostic_result))
                sources.extend(self._grounding_sources_from_tool_result("diagnostic", diagnostic_result))

        compact_sources = self._build_compact_grounding_sources(
            sources=sources,
            cleaned_message=cleaned_message,
            retrieval_plan=plan.to_dict(),
        )

        grounding_context = AssistantGroundingContext(
            detected_language=detected_language,
            response_language=response_language,
            route_context=route_context,
            auth_summary={
                "tenant_scope": auth_summary.tenant_scope,
                "scope_kind": auth_summary.scope_kind,
                "current_user_type": auth_summary.current_user_type,
                "role_keys": auth_summary.role_keys,
                "permission_keys": auth_summary.permission_keys,
            },
            retrieval_plan=plan.to_dict(),
            query_expansion={
                "original_query": expanded_query.original_query,
                "detected_terms": list(expanded_query.detected_terms),
                "expanded_terms_en": list(expanded_query.expanded_terms_en),
                "expanded_terms_de": list(expanded_query.expanded_terms_de),
                "expanded_query": expanded_query.expanded_query,
                "likely_page_ids": list(expanded_query.likely_page_ids),
                "likely_module_keys": list(expanded_query.likely_module_keys),
            },
            sources=compact_sources,
            missing_context=missing_context,
            missing_permissions=self._collect_missing_permissions_from_summaries(summaries),
        )
        if self.runtime_config.retrieval_debug:
            self._log_retrieval_debug(
                query=cleaned_message,
                plan=plan.to_dict(),
                grounding_context=grounding_context,
            )
        return grounding_context, summaries

    def _build_diagnostic_prefetch_sources(
        self,
        *,
        conversation: AssistantConversation,
        actor: RequestAuthorizationContext,
        response_language: str,
        plan: AssistantDiagnosticPrefetchPlan,
    ) -> tuple[list[AssistantGroundingSource], list[AssistantToolResultSummary]]:
        if self.tool_registry is None:
            return [], []

        summaries: list[AssistantToolResultSummary] = []
        sources: list[AssistantGroundingSource] = []
        checks_completed: list[str] = []

        capabilities_result = self.execute_registered_tool(
            tool_name="assistant.get_current_user_capabilities",
            input_data={},
            actor=actor,
            conversation_id=conversation.id,
        )
        summaries.append(self._tool_result_to_summary(capabilities_result))
        checks_completed.append("current_user_capabilities")
        sources.append(
            self._diagnostic_tool_result_source(
                source_name="Current User Capabilities",
                tool_name="assistant.get_current_user_capabilities",
                result=capabilities_result,
                title="Assistant capability and role scope",
            )
        )

        accessible_pages: list[dict[str, Any]] = []
        for page_id in plan.likely_page_ids:
            page_result = self.execute_registered_tool(
                tool_name="assistant.search_accessible_pages",
                input_data={"page_id": page_id, "limit": 1},
                actor=actor,
                conversation_id=conversation.id,
            )
            summaries.append(self._tool_result_to_summary(page_result))
            checks_completed.append(f"accessible_page:{page_id}")
            payload = page_result.data if isinstance(page_result.data, dict) else {}
            page_rows = payload.get("pages", []) if isinstance(payload.get("pages"), list) else []
            if page_rows:
                accessible_pages.extend([row for row in page_rows if isinstance(row, dict)])
            sources.append(
                self._diagnostic_tool_result_source(
                    source_name=f"Accessible page {page_id}",
                    tool_name="assistant.search_accessible_pages",
                    result=page_result,
                    title=f"Accessible page hint {page_id}",
                )
            )

        employee_ref = plan.employee_ref
        employee_display_name = plan.employee_name
        if plan.employee_name and employee_ref is None:
            employee_search = self.execute_registered_tool(
                tool_name="employees.search_employee_by_name",
                input_data={"name": plan.employee_name, "limit": 5},
                actor=actor,
                conversation_id=conversation.id,
            )
            summaries.append(self._tool_result_to_summary(employee_search))
            checks_completed.append("employee_search")
            search_payload = employee_search.data if isinstance(employee_search.data, dict) else {}
            matches = search_payload.get("matches", []) if isinstance(search_payload.get("matches"), list) else []
            if len(matches) == 1 and isinstance(matches[0], dict):
                employee_ref = str(matches[0].get("employee_ref") or "").strip() or None
                employee_display_name = str(matches[0].get("display_name") or "").strip() or employee_display_name
            sources.append(
                self._diagnostic_tool_result_source(
                    source_name="Employee search",
                    tool_name="employees.search_employee_by_name",
                    result=employee_search,
                    title="Resolved employee candidate",
                )
            )

        assignment_ref = plan.assignment_ref
        shift_ref = plan.shift_ref
        if employee_ref is not None:
            profile_result = self.execute_registered_tool(
                tool_name="employees.get_employee_operational_profile",
                input_data={"employee_ref": employee_ref},
                actor=actor,
                conversation_id=conversation.id,
            )
            summaries.append(self._tool_result_to_summary(profile_result))
            checks_completed.append("employee_operational_profile")
            sources.append(
                self._diagnostic_tool_result_source(
                    source_name="Employee operational profile",
                    tool_name="employees.get_employee_operational_profile",
                    result=profile_result,
                    title="Employee operational scope",
                )
            )

            mobile_result = self.execute_registered_tool(
                tool_name="employees.get_employee_mobile_access_status",
                input_data={"employee_ref": employee_ref},
                actor=actor,
                conversation_id=conversation.id,
            )
            summaries.append(self._tool_result_to_summary(mobile_result))
            checks_completed.append("employee_mobile_access")
            sources.append(
                self._diagnostic_tool_result_source(
                    source_name="Employee mobile access",
                    tool_name="employees.get_employee_mobile_access_status",
                    result=mobile_result,
                    title="Employee self-service and mobile access",
                )
            )

            if plan.date_iso is not None:
                readiness_result = self.execute_registered_tool(
                    tool_name="employees.get_employee_readiness_summary",
                    input_data={"employee_ref": employee_ref, "date": plan.date_iso},
                    actor=actor,
                    conversation_id=conversation.id,
                )
                summaries.append(self._tool_result_to_summary(readiness_result))
                checks_completed.append("employee_readiness")
                sources.append(
                    self._diagnostic_tool_result_source(
                        source_name="Employee readiness",
                        tool_name="employees.get_employee_readiness_summary",
                        result=readiness_result,
                        title="Employee readiness on diagnostic date",
                    )
                )

        if employee_ref is not None and plan.date_iso is not None:
            assignment_search = self.execute_registered_tool(
                tool_name="planning.find_assignments",
                input_data={"employee_ref": employee_ref, "date": plan.date_iso, "limit": 10},
                actor=actor,
                conversation_id=conversation.id,
            )
            summaries.append(self._tool_result_to_summary(assignment_search))
            checks_completed.append("planning.find_assignments")
            assignment_payload = assignment_search.data if isinstance(assignment_search.data, dict) else {}
            assignment_matches = assignment_payload.get("matches", []) if isinstance(assignment_payload.get("matches"), list) else []
            if assignment_ref is None and len(assignment_matches) == 1 and isinstance(assignment_matches[0], dict):
                assignment_ref = str(assignment_matches[0].get("assignment_ref") or "").strip() or None
                shift_ref = shift_ref or (str(assignment_matches[0].get("shift_ref") or "").strip() or None)
            sources.append(
                self._diagnostic_tool_result_source(
                    source_name="Planning assignments",
                    tool_name="planning.find_assignments",
                    result=assignment_search,
                    title="Assignment candidates on diagnostic date",
                )
            )

            shift_search = self.execute_registered_tool(
                tool_name="planning.find_shifts",
                input_data={"employee_ref": employee_ref, "date": plan.date_iso, "limit": 10},
                actor=actor,
                conversation_id=conversation.id,
            )
            summaries.append(self._tool_result_to_summary(shift_search))
            checks_completed.append("planning.find_shifts")
            shift_payload = shift_search.data if isinstance(shift_search.data, dict) else {}
            shift_matches = shift_payload.get("matches", []) if isinstance(shift_payload.get("matches"), list) else []
            if shift_ref is None and len(shift_matches) == 1 and isinstance(shift_matches[0], dict):
                shift_ref = str(shift_matches[0].get("shift_ref") or "").strip() or None
            sources.append(
                self._diagnostic_tool_result_source(
                    source_name="Planning shifts",
                    tool_name="planning.find_shifts",
                    result=shift_search,
                    title="Shift candidates on diagnostic date",
                )
            )

        if assignment_ref is not None:
            assignment_result = self.execute_registered_tool(
                tool_name="planning.inspect_assignment",
                input_data={"assignment_ref": assignment_ref},
                actor=actor,
                conversation_id=conversation.id,
            )
            summaries.append(self._tool_result_to_summary(assignment_result))
            checks_completed.append("planning.inspect_assignment")
            assignment_payload = assignment_result.data if isinstance(assignment_result.data, dict) else {}
            assignment_row = assignment_payload.get("assignment") if isinstance(assignment_payload.get("assignment"), dict) else {}
            if shift_ref is None:
                shift_ref = str(assignment_row.get("shift_ref") or "").strip() or None
            sources.append(
                self._diagnostic_tool_result_source(
                    source_name="Assignment inspection",
                    tool_name="planning.inspect_assignment",
                    result=assignment_result,
                    title="Assignment visibility status",
                )
            )

        if shift_ref is not None:
            shift_release = self.execute_registered_tool(
                tool_name="planning.inspect_shift_release_state",
                input_data={"shift_ref": shift_ref},
                actor=actor,
                conversation_id=conversation.id,
            )
            summaries.append(self._tool_result_to_summary(shift_release))
            checks_completed.append("planning.inspect_shift_release_state")
            sources.append(
                self._diagnostic_tool_result_source(
                    source_name="Shift release state",
                    tool_name="planning.inspect_shift_release_state",
                    result=shift_release,
                    title="Shift release state for employee app",
                )
            )

            shift_visibility = self.execute_registered_tool(
                tool_name="planning.inspect_shift_visibility",
                input_data={"shift_ref": shift_ref},
                actor=actor,
                conversation_id=conversation.id,
            )
            summaries.append(self._tool_result_to_summary(shift_visibility))
            checks_completed.append("planning.inspect_shift_visibility")
            sources.append(
                self._diagnostic_tool_result_source(
                    source_name="Shift visibility flags",
                    tool_name="planning.inspect_shift_visibility",
                    result=shift_visibility,
                    title="Shift visibility flags for employee audience",
                )
            )

        if employee_ref is not None and (assignment_ref is not None or shift_ref is not None or plan.date_iso is not None):
            visibility_input: dict[str, Any] = {"employee_ref": employee_ref}
            if assignment_ref is not None:
                visibility_input["assignment_ref"] = assignment_ref
            if shift_ref is not None:
                visibility_input["shift_ref"] = shift_ref
            if plan.date_iso is not None:
                visibility_input["date"] = plan.date_iso
            released_visibility = self.execute_registered_tool(
                tool_name="field.inspect_released_schedule_visibility",
                input_data=visibility_input,
                actor=actor,
                conversation_id=conversation.id,
            )
            summaries.append(self._tool_result_to_summary(released_visibility))
            checks_completed.append("field.inspect_released_schedule_visibility")
            sources.append(
                self._diagnostic_tool_result_source(
                    source_name="Released schedule visibility",
                    tool_name="field.inspect_released_schedule_visibility",
                    result=released_visibility,
                    title="Released schedule visibility in employee app",
                )
            )

        allowed_link_targets: list[dict[str, Any]] = []
        for page_id in plan.likely_page_ids:
            link_result = self.execute_registered_tool(
                tool_name="navigation.build_allowed_link",
                input_data={"page_id": page_id},
                actor=actor,
                conversation_id=conversation.id,
            )
            summaries.append(self._tool_result_to_summary(link_result))
            payload = link_result.data if isinstance(link_result.data, dict) else {}
            link_payload = payload.get("link") if isinstance(payload.get("link"), dict) else None
            if payload.get("allowed") and link_payload is not None:
                allowed_link_targets.append(link_payload)
                sources.append(
                    AssistantGroundingSource(
                        source_id=f"allowed_link:{page_id}",
                        source_type="allowed_navigation_link",
                        source_name="Allowed navigation link",
                        page_id=page_id,
                        module_key=self._module_key_from_page_id(page_id),
                        title=str(link_payload.get("label") or page_id),
                        content=str(link_payload.get("reason") or "").strip() or None,
                        facts={"link": link_payload},
                        verified=True,
                        permission_checked=True,
                    )
                )

        sources.insert(
            0,
            AssistantGroundingSource(
                source_id=f"diagnostic_prefetch:{plan.intent}",
                source_type="diagnostic_fact",
                source_name="Employee App Visibility Diagnostic",
                page_id="ES-01",
                module_key="field_execution",
                title="Shift assigned but not visible in employee app",
                content=(
                    "Possible checked causes: employee account/mobile access, assignment status, "
                    "shift release state, employee visibility flag, released schedule availability, "
                    "absence and qualification readiness."
                ),
                facts={
                    "intent": plan.intent,
                    "employee_name": employee_display_name,
                    "employee_ref": employee_ref,
                    "assignment_ref": assignment_ref,
                    "shift_ref": shift_ref,
                    "date": plan.date_iso,
                    "employee_resolved": bool(employee_ref),
                    "date_present": bool(plan.date_iso),
                    "checks_completed": checks_completed,
                    "checks_missing_input": list(plan.checks_missing_input),
                    "missing_input": list(plan.missing_inputs),
                    "generic_check_sequence": list(plan.generic_check_sequence),
                    "accessible_pages": [row.get("page_id") for row in accessible_pages if isinstance(row, dict)],
                    "allowed_link_count": len(allowed_link_targets),
                },
                verified=True,
                permission_checked=True,
                content_bearing=True,
            ),
        )
        for missing_input in plan.missing_inputs:
            sources.append(
                AssistantGroundingSource(
                    source_id=f"missing_diagnostic_input:{missing_input}",
                    source_type="missing_diagnostic_input",
                    source_name="Missing diagnostic input",
                    title=missing_input,
                    content=f"The diagnostic is missing {missing_input}.",
                    facts={"field": missing_input},
                    verified=True,
                    permission_checked=True,
                )
            )
        return sources, summaries

    def _build_rag_trace(
        self,
        *,
        grounding_context: AssistantGroundingContext,
        provider_called: bool,
    ) -> AssistantRagTraceRead:
        source_type_counts: dict[str, int] = {}
        top_sources: list[AssistantRagTraceTopSource] = []
        content_bearing_sources = [
            source for source in grounding_context.sources if self._is_content_bearing_source(source)
        ]
        for source in grounding_context.sources:
            source_type_counts[source.source_type] = source_type_counts.get(source.source_type, 0) + 1
        ordered_sources = sorted(
            grounding_context.sources,
            key=lambda item: (
                0 if self._is_content_bearing_source(item) else 1,
                self._source_priority(item.source_type),
                -(item.score or 0.0),
                item.source_type,
                item.page_id or "",
            ),
        )
        for source in ordered_sources[:5]:
            top_sources.append(
                AssistantRagTraceTopSource(
                    source_id=source.source_id,
                    source_type=source.source_type,
                    source_name=source.source_name,
                    page_id=source.page_id,
                    module_key=source.module_key,
                    title=source.title,
                    score=source.score,
                    content_preview=self._content_preview(source),
                )
            )
        missing_context = list(grounding_context.missing_context)
        if (
            self._requires_content_bearing_sources(grounding_context.retrieval_plan)
            and not content_bearing_sources
            and "content_bearing_sources" not in missing_context
        ):
            missing_context.append("content_bearing_sources")
        return AssistantRagTraceRead(
            trace_id=str(uuid4()),
            provider_called=provider_called,
            provider_mode=self.runtime_config.provider_mode,
            retrieval_executed=True,
            grounding_attached=True,
            grounding_source_count=len(grounding_context.sources),
            content_bearing_source_count=len(content_bearing_sources),
            source_type_counts=source_type_counts,
            top_sources=top_sources,
            missing_context=missing_context,
            retrieval_plan=dict(grounding_context.retrieval_plan),
            query_expansion=dict(grounding_context.query_expansion),
            grounding_trimmed=grounding_context.grounding_trimmed,
            trim_reason=grounding_context.trim_reason,
        )

    def _build_compact_grounding_sources(
        self,
        *,
        sources: list[AssistantGroundingSource],
        cleaned_message: str,
        retrieval_plan: dict[str, Any],
    ) -> list[AssistantGroundingSource]:
        likely_page_ids = {str(item) for item in retrieval_plan.get("likely_page_ids", []) if str(item).strip()}
        likely_module_keys = {str(item) for item in retrieval_plan.get("likely_module_keys", []) if str(item).strip()}
        workflow_intent = str(retrieval_plan.get("workflow_intent") or "").strip() or None
        intent_category = str(retrieval_plan.get("intent_category") or "").strip()
        lowered = cleaned_message.casefold()
        rich_pages = {
            source.page_id
            for source in sources
            if source.page_id and source.source_type in {"knowledge_chunk", "workflow", "page_help_manifest", "ui_action", "diagnostic"}
        }

        ranked: list[tuple[float, AssistantGroundingSource, list[str]]] = []
        for source in sources:
            score, reasons = self._rank_grounding_source(
                source=source,
                lowered_message=lowered,
                intent_category=intent_category,
                workflow_intent=workflow_intent,
                likely_page_ids=likely_page_ids,
                likely_module_keys=likely_module_keys,
                rich_pages=rich_pages,
            )
            if score <= 0:
                continue
            ranked.append((score, source, reasons))

        ranked.sort(
            key=lambda item: (
                -(item[0]),
                self._source_priority(item[1].source_type),
                item[1].source_type,
                item[1].page_id or "",
                item[1].title or "",
            ),
        )

        selected: list[AssistantGroundingSource] = []
        total_chars = 0
        max_sources = max(self.runtime_config.max_grounding_sources, 1)
        guaranteed_source_types = self._guaranteed_grounding_source_types(intent_category=intent_category)
        selected_ids: set[str | None] = set()

        for guaranteed_type in guaranteed_source_types:
            guaranteed_candidate = next(
                (
                    (score, source, reasons)
                    for score, source, reasons in ranked
                    if source.source_type == guaranteed_type and source.source_id not in selected_ids
                ),
                None,
            )
            if guaranteed_candidate is None or len(selected) >= max_sources:
                continue
            score, source, reasons = guaranteed_candidate
            prepared = self._prepare_grounding_source_for_prompt(
                source=source,
                score=score,
                reasons=reasons,
                remaining_chars=min(self.runtime_config.max_grounding_chars_per_source, 280),
            )
            if prepared is None:
                continue
            selected.append(prepared)
            selected_ids.add(prepared.source_id)
            total_chars += len(prepared.content or "") + len(json.dumps(prepared.facts, ensure_ascii=False))

        for score, source, reasons in ranked:
            if source.source_id in selected_ids:
                continue
            if len(selected) >= max_sources:
                break
            prepared = self._prepare_grounding_source_for_prompt(
                source=source,
                score=score,
                reasons=reasons,
                remaining_chars=max(self.runtime_config.max_total_grounding_chars - total_chars, 0),
            )
            if prepared is None:
                continue
            selected.append(prepared)
            selected_ids.add(prepared.source_id)
            total_chars += len(prepared.content or "") + len(json.dumps(prepared.facts, ensure_ascii=False))
            if total_chars >= self.runtime_config.max_total_grounding_chars:
                break
        for score, source, reasons in ranked:
            if source.source_id in selected_ids or source.source_type not in guaranteed_source_types:
                continue
            prepared = self._prepare_grounding_source_for_prompt(
                source=source,
                score=score,
                reasons=reasons,
                remaining_chars=min(self.runtime_config.max_grounding_chars_per_source, 280),
            )
            if prepared is None:
                continue
            selected.append(prepared)
            selected_ids.add(prepared.source_id)
            total_chars += len(prepared.content or "") + len(json.dumps(prepared.facts, ensure_ascii=False))
        return selected

    @staticmethod
    def _guaranteed_grounding_source_types(*, intent_category: str) -> list[str]:
        guaranteed = [
            "ui_action",
            "diagnostic",
            "diagnostic_fact",
            "missing_diagnostic_input",
            "allowed_navigation_link",
        ]
        if intent_category == "ui_action_question":
            guaranteed.append("page_help_manifest")
        return guaranteed

    def _rank_grounding_source(
        self,
        *,
        source: AssistantGroundingSource,
        lowered_message: str,
        intent_category: str,
        workflow_intent: str | None,
        likely_page_ids: set[str],
        likely_module_keys: set[str],
        rich_pages: set[str | None],
    ) -> tuple[float, list[str]]:
        score = float(source.score or 0.0)
        reasons: list[str] = []

        if self._is_content_bearing_source(source):
            score += 25.0
            reasons.append("content-bearing evidence")
        elif source.source_type in {"page_route", "current_route"}:
            reasons.append("shallow route hint")

        facts = source.facts if isinstance(source.facts, dict) else {}
        if workflow_intent:
            workflow_keys = facts.get("workflow_keys") or []
            if isinstance(workflow_keys, list) and workflow_intent in workflow_keys:
                score += 24.0
                reasons.append("exact workflow intent match")
            if source.source_type == "workflow" and source.source_name == workflow_intent:
                score += 24.0
                reasons.append("exact workflow manifest")

        if source.page_id and source.page_id in likely_page_ids:
            score += 18.0
            reasons.append(f"page match {source.page_id}")
        elif source.page_id and likely_page_ids:
            score -= 8.0

        if source.module_key and source.module_key in likely_module_keys:
            score += 12.0
            reasons.append(f"module match {source.module_key}")
        elif source.module_key and likely_module_keys:
            score -= 6.0

        if intent_category == "ui_action_question" and source.source_type == "page_help_manifest":
            score += 16.0
            reasons.append("UI manifest for UI question")
        if intent_category == "workflow_how_to" and source.source_type == "workflow":
            score += 16.0
            reasons.append("workflow manifest for process question")
        if intent_category == "workflow_how_to" and source.source_type in {"operational_handbook", "user_manual", "knowledge_chunk"}:
            score += 10.0
            reasons.append("content guidance for how-to question")
        if intent_category == "operational_diagnostic" and source.source_type in {"diagnostic_fact", "tool_result_summary", "diagnostic"}:
            score += 22.0
            reasons.append("diagnostic prefetch evidence")
        if intent_category == "operational_diagnostic" and source.source_type == "missing_diagnostic_input":
            score += 16.0
            reasons.append("missing required diagnostic input")
        if intent_category == "operational_diagnostic" and source.source_type == "allowed_navigation_link":
            score += 6.0
            reasons.append("safe navigation follow-up")
        if any(token in lowered_message for token in ("api", "endpoint", "route", "sdk", "http")) and source.source_type in {"api_export", "knowledge_chunk"}:
            score += 10.0
            reasons.append("API-oriented source")

        if source.page_id == "F-02" and "dashboard" not in lowered_message and "kpi" not in lowered_message:
            score -= 18.0
            reasons.append("dashboard source demoted")
        employee_terms = ("employee", "mitarbeiter", "personal", "staff", "workforce", "guard", "کارمند")
        if source.page_id == "E-01" and workflow_intent not in {"employee_create", "employee_assign_to_shift", "shift_release_to_employee_app"} and not any(term in lowered_message for term in employee_terms):
            score -= 18.0
            reasons.append("employee source demoted")
        if source.source_type == "page_route" and source.page_id in rich_pages:
            score -= 12.0
            reasons.append("demoted shallow page route")
        if len((source.content or "").strip()) < 24 and not facts:
            score -= 14.0
            reasons.append("tiny or empty source")
        return score, reasons

    def _prepare_grounding_source_for_prompt(
        self,
        *,
        source: AssistantGroundingSource,
        score: float,
        reasons: list[str],
        remaining_chars: int,
    ) -> AssistantGroundingSource | None:
        max_source_chars = min(self.runtime_config.max_grounding_chars_per_source, max(remaining_chars, 0))
        if max_source_chars <= 0:
            return None
        content = self._truncate_grounding_text(source.content, max_source_chars)
        trimmed_facts = self._trim_grounding_facts(
            facts=source.facts,
            max_chars=max_source_chars,
        )
        if not content and not trimmed_facts:
            return None
        return source.model_copy(
            update={
                "content": content,
                "facts": trimmed_facts,
                "score": round(score, 4),
                "why_selected": reasons[:4],
                "content_bearing": self._is_content_bearing_source(source),
            }
        )

    def _generate_in_scope_response(
        self,
        *,
        conversation: AssistantConversation,
        cleaned_message: str,
        route_context: dict[str, Any] | None,
        detected_language: str,
        response_language: str,
        actor: RequestAuthorizationContext,
        grounding_context: AssistantGroundingContext,
        initial_tool_results: list[AssistantToolResultSummary],
    ) -> dict[str, Any]:
        tool_results = list(initial_tool_results)
        provider_tool_results: list[dict[str, Any]] = []
        previous_response_id: str | None = None
        previous_output_items: list[dict[str, Any]] = []
        provider_result: AssistantProviderResult | None = None
        remaining_tool_calls = max(self.runtime_config.max_tool_calls, 0)
        request = self._build_provider_request(
            conversation=conversation,
            cleaned_message=cleaned_message,
            route_context=route_context,
            detected_language=detected_language,
            response_language=response_language,
            actor=actor,
            grounding_context=grounding_context,
            tool_results=tool_results,
            provider_tool_results=provider_tool_results,
            previous_response_id=self._continuation_response_id(previous_response_id),
            previous_output_items=previous_output_items,
        )

        while True:
            if provider_result is None:
                provider_result = self._call_provider_with_fallback_capture(
                    request=request,
                    grounding_context=grounding_context,
                    tool_results=tool_results,
                    had_prior_provider_output=bool(previous_output_items),
                )
            previous_response_id = provider_result.response_id
            previous_output_items = list(provider_result.output_items or [])
            requested_tool_calls = provider_result.requested_tool_calls or []
            if not requested_tool_calls:
                return self._merge_provider_payload_with_tool_results(
                    provider_result.final_response,
                    tool_results,
                )

            if self.tool_registry is None:
                return self._merge_provider_payload_with_tool_results(
                    provider_result.final_response,
                    tool_results,
                )

            if remaining_tool_calls <= 0:
                tool_results.append(
                    AssistantToolResultSummary(
                        tool_name="assistant.tool_loop_limit",
                        summary={
                            "code": "tool_call_limit_reached",
                            "detail": "The assistant must answer using the already collected grounded facts because the tool-call budget is exhausted.",
                        },
                    )
                )
                request = self._build_provider_request(
                    conversation=conversation,
                    cleaned_message=cleaned_message,
                    route_context=route_context,
                    detected_language=detected_language,
                    response_language=response_language,
                    actor=actor,
                    grounding_context=grounding_context,
                    tool_results=tool_results,
                    available_tools=[],
                    previous_response_id=self._continuation_response_id(previous_response_id),
                    previous_output_items=previous_output_items,
                )
                provider_result = self._call_provider_with_fallback_capture(
                    request=request,
                    grounding_context=grounding_context,
                    tool_results=tool_results,
                    had_prior_provider_output=bool(previous_output_items),
                )
                return self._merge_provider_payload_with_tool_results(
                    provider_result.final_response,
                    tool_results,
                )

            executed_any = False
            executed_call_ids: list[str] = []
            for requested_call in requested_tool_calls[:remaining_tool_calls]:
                provider_tool_name = str(
                    requested_call.get("provider_tool_name")
                    or requested_call.get("name")
                    or ""
                ).strip()
                if not provider_tool_name:
                    continue
                call_id = str(requested_call.get("call_id") or "").strip()
                tool_name = self._resolve_internal_tool_name(
                    provider_tool_name=provider_tool_name,
                    provider_tool_name_map=request.provider_tool_name_map,
                )
                if tool_name is None:
                    tool_results.append(
                        AssistantToolResultSummary(
                            tool_name="assistant.unknown_provider_tool_name",
                            summary={
                                "code": "unknown_provider_tool_name",
                                "missing_permissions": [],
                                "provider_tool_name": provider_tool_name,
                                "detail": "The provider requested an unknown tool alias. The tool was not executed.",
                            },
                        )
                    )
                    provider_tool_results.append(
                        self._unknown_provider_tool_output(
                            requested_call=requested_call,
                            provider_tool_name=provider_tool_name,
                        )
                    )
                    if call_id:
                        executed_call_ids.append(call_id)
                    remaining_tool_calls -= 1
                    executed_any = True
                    if remaining_tool_calls <= 0:
                        break
                    continue
                requested_call["internal_tool_name"] = tool_name
                arguments = self._parse_tool_call_arguments(requested_call.get("arguments"))
                tool_result = self.execute_registered_tool(
                    tool_name=tool_name,
                    input_data=arguments,
                    actor=actor,
                    conversation_id=conversation.id,
                )
                tool_results.append(self._tool_result_to_summary(tool_result))
                provider_tool_results.append(
                    self._tool_result_to_provider_output(
                        requested_call=requested_call,
                        tool_result=tool_result,
                    )
                )
                if call_id:
                    executed_call_ids.append(call_id)
                remaining_tool_calls -= 1
                executed_any = True
                if remaining_tool_calls <= 0:
                    break

            if not executed_any:
                return self._merge_provider_payload_with_tool_results(
                    provider_result.final_response,
                    tool_results,
                )

            request = self._build_provider_request(
                conversation=conversation,
                cleaned_message=cleaned_message,
                route_context=route_context,
                detected_language=detected_language,
                response_language=response_language,
                actor=actor,
                grounding_context=grounding_context,
                tool_results=tool_results,
                provider_tool_results=provider_tool_results,
                previous_response_id=self._continuation_response_id(previous_response_id),
                previous_output_items=previous_output_items,
            )
            self._log_tool_call_continuation_event(
                event="assistant_tool_call_continuation_started",
                request=request,
                response_id=previous_response_id,
                call_ids=executed_call_ids,
                provider_returned_successfully=False,
                input_tokens=None,
                output_tokens=None,
            )
            provider_result = self._call_provider_with_fallback_capture(
                request=request,
                grounding_context=grounding_context,
                tool_results=tool_results,
                had_prior_provider_output=bool(previous_output_items),
            )
            self._log_tool_call_continuation_event(
                event="assistant_tool_call_continuation_finished",
                request=request,
                response_id=previous_response_id,
                call_ids=executed_call_ids,
                provider_returned_successfully=True,
                input_tokens=provider_result.usage.input_tokens if provider_result.usage else None,
                output_tokens=provider_result.usage.output_tokens if provider_result.usage else None,
            )
            previous_response_id = provider_result.response_id
            previous_output_items = list(provider_result.output_items or [])
            requested_tool_calls = provider_result.requested_tool_calls or []
            if not requested_tool_calls:
                return self._merge_provider_payload_with_tool_results(
                    provider_result.final_response,
                    tool_results,
                )

    def _build_provider_request(
        self,
        *,
        conversation: AssistantConversation,
        cleaned_message: str,
        route_context: dict[str, Any] | None,
        detected_language: str,
        response_language: str,
        actor: RequestAuthorizationContext,
        grounding_context: AssistantGroundingContext,
        tool_results: list[AssistantToolResultSummary] | None = None,
        provider_tool_results: list[dict[str, Any]] | None = None,
        available_tools: list[dict[str, Any]] | None = None,
        previous_response_id: str | None = None,
        previous_output_items: list[dict[str, Any]] | None = None,
    ) -> AssistantProviderRequest:
        continuation_mode = self._determine_continuation_mode(
            previous_response_id=previous_response_id,
            previous_output_items=previous_output_items,
            continuation_tool_outputs=provider_tool_results,
        )
        is_continuation = continuation_mode != "initial"
        available_tools_payload = available_tools
        if available_tools_payload is None:
            available_tools_payload = self.list_available_tools(actor=actor, conversation_id=conversation.id)
        available_tools_payload = self._select_provider_available_tools(
            available_tools=available_tools_payload,
            grounding_context=grounding_context,
        )
        provider_tool_name_map = build_provider_tool_name_map(
            [tool["function"]["name"] for tool in available_tools_payload if isinstance(tool, dict)]
        )
        recent_message_limit = (
            self.runtime_config.max_recent_messages_for_continuation
            if is_continuation
            else self.runtime_config.max_recent_messages_for_model
        )
        recent_message_rows = self.repository.list_messages_for_conversation(conversation.id)
        if recent_message_limit > 0:
            recent_message_rows = recent_message_rows[-recent_message_limit:]
        else:
            recent_message_rows = []
        recent_messages = [
            AssistantMessageContext(
                role=message.role,
                content=message.content,
                detected_language=message.detected_language,
                response_language=message.response_language,
            )
            for message in recent_message_rows
        ]
        knowledge_chunks: list[AssistantKnowledgeChunkResult] = []
        prompt_payload_metadata: dict[str, Any] = {}
        system_instructions = "Use the tool outputs and prior response context to produce the final structured answer."
        user_message = cleaned_message
        prompt_recent_messages: list[dict[str, Any]] = []
        request_grounding_context: dict[str, Any] | None = None

        if not is_continuation:
            knowledge_chunks = self._retrieve_knowledge_chunks(
                query=cleaned_message,
                response_language=response_language,
                route_context=route_context,
                actor=actor,
                workflow_intent=grounding_context.retrieval_plan.get("workflow_intent"),
                planned_page_ids=list(grounding_context.retrieval_plan.get("likely_page_ids", [])),
                planned_module_keys=list(grounding_context.retrieval_plan.get("likely_module_keys", [])),
            )
            trimmed_grounding_context = self._trim_grounding_context_for_budget(grounding_context)
            prompt_payload = build_assistant_prompt(
                user_message=cleaned_message,
                detected_language=detected_language,
                response_language=response_language,
                auth_context=summarize_auth_context(actor),
                route_context=route_context,
                knowledge_chunks=knowledge_chunks,
                grounding_context=trimmed_grounding_context,
                available_tools=[
                    PromptToolDefinition(
                        name=tool["function"]["name"],
                        description=tool["function"].get("description"),
                        required_permissions=[],
                    )
                    for tool in available_tools_payload
                ],
                conversation_messages=recent_messages,
                tool_results=tool_results,
                max_context_chunks=self.runtime_config.max_context_chunks,
                max_input_chars=self.runtime_config.max_input_chars,
                max_history_messages=self.runtime_config.max_recent_messages_for_model,
            )
            system_instructions = prompt_payload.system_instructions
            user_message = prompt_payload.user_message
            prompt_recent_messages = prompt_payload.conversation_messages
            prompt_payload_metadata = dict(prompt_payload.metadata)
            request_grounding_context = trimmed_grounding_context.model_dump(mode="json")

        request = AssistantProviderRequest(
            conversation_id=conversation.id,
            user_message=user_message,
            system_instructions=system_instructions,
            response_language=response_language,
            detected_language=detected_language,
            route_context=route_context,
            recent_messages=prompt_recent_messages,
            knowledge_chunks=[item.model_dump(mode="json") for item in knowledge_chunks],
            grounding_context=request_grounding_context,
            tool_results=self._build_provider_tool_result_summaries(tool_results=tool_results),
            continuation_tool_outputs=list(provider_tool_results or []),
            previous_response_id=previous_response_id,
            previous_output_items=list(previous_output_items or []),
            available_tools=available_tools_payload,
            provider_tool_name_map=provider_tool_name_map,
            max_tool_calls=self.runtime_config.max_tool_calls,
            max_input_chars=self.runtime_config.max_input_chars,
            max_output_tokens=(
                self.runtime_config.continuation_max_output_tokens
                if is_continuation
                else self.runtime_config.max_output_tokens
            ),
            metadata={
                "request_id": actor.request_id,
                "provider_mode": self.runtime_config.provider_mode,
                "user_id": actor.user_id,
                "tenant_id": actor.tenant_id,
                "tool_name_map": dict(provider_tool_name_map),
                "continuation_mode": continuation_mode,
                **prompt_payload_metadata,
            },
        )
        return self._enforce_provider_token_budget(
            request=request,
            grounding_context=grounding_context,
        )

    @staticmethod
    def _build_provider_tool_result_summaries(
        *,
        tool_results: list[AssistantToolResultSummary] | None,
    ) -> list[dict[str, Any]]:
        return [
            {"tool_name": item.tool_name, "summary": item.summary}
            for item in (tool_results or [])
        ]

    @staticmethod
    def _determine_continuation_mode(
        *,
        previous_response_id: str | None,
        previous_output_items: list[dict[str, Any]] | None,
        continuation_tool_outputs: list[dict[str, Any]] | None,
    ) -> str:
        if previous_response_id and continuation_tool_outputs:
            return "previous_response_id"
        if previous_output_items and continuation_tool_outputs:
            return "stateless"
        return "initial"

    def _trim_grounding_context_for_budget(
        self,
        grounding_context: AssistantGroundingContext,
    ) -> AssistantGroundingContext:
        trimmed_context = grounding_context.model_copy(deep=True)
        sources = list(trimmed_context.sources)
        kept_sources = self._trim_sources_by_char_budget(
            sources=sources,
            char_budget=self.runtime_config.max_total_grounding_chars,
        )
        trimmed = len(kept_sources) < len(sources)
        if trimmed:
            grounding_context.grounding_trimmed = True
            grounding_context.trim_reason = "token_budget"
            trimmed_context.grounding_trimmed = True
            trimmed_context.trim_reason = "token_budget"
            trimmed_context.sources = kept_sources
        return trimmed_context

    def _trim_sources_by_char_budget(
        self,
        *,
        sources: list[AssistantGroundingSource],
        char_budget: int,
    ) -> list[AssistantGroundingSource]:
        if not sources:
            return []
        removable_priority = {
            "current_route": 100,
            "page_route": 90,
            "allowed_navigation_link": 80,
            "knowledge_chunk": 70,
            "tool_result_summary": 60,
            "diagnostic_fact": 10,
            "workflow": 20,
            "ui_action": 15,
            "page_help_manifest": 25,
            "diagnostic": 30,
            "missing_diagnostic_input": 12,
        }
        prepared = [
            source.model_copy(
                update={
                    "content": self._truncate_grounding_text(source.content, min(self.runtime_config.max_grounding_chars_per_source, 280)),
                    "facts": self._trim_grounding_facts(facts=source.facts, max_chars=220),
                }
            )
            for source in sources
        ]
        protected_source_ids: set[str | None] = set()
        for protected_type in ("ui_action", "diagnostic", "diagnostic_fact", "workflow"):
            first_match = next((source for source in prepared if source.source_type == protected_type), None)
            if first_match is not None:
                protected_source_ids.add(first_match.source_id)
        total = sum(
            len(source.content or "") + len(json.dumps(source.facts, ensure_ascii=False))
            for source in prepared
        )
        if total <= char_budget:
            return prepared
        ordered = sorted(
            prepared,
            key=lambda source: (
                removable_priority.get(source.source_type, 50),
                0 if self._is_content_bearing_source(source) else 1,
                source.score or 0.0,
            ),
            reverse=True,
        )
        removable_ids = [
            source.source_id
            for source in ordered
            if source.source_id not in protected_source_ids
        ]
        kept = list(prepared)
        while total > char_budget and removable_ids:
            remove_id = removable_ids.pop(0)
            next_kept = [source for source in kept if source.source_id != remove_id]
            if not next_kept:
                break
            kept = next_kept
            total = sum(
                len(source.content or "") + len(json.dumps(source.facts, ensure_ascii=False))
                for source in kept
            )
        return kept

    def _enforce_provider_token_budget(
        self,
        *,
        request: AssistantProviderRequest,
        grounding_context: AssistantGroundingContext,
    ) -> AssistantProviderRequest:
        budget = (
            self.runtime_config.max_continuation_input_tokens
            if request.metadata.get("continuation_mode") != "initial"
            else self.runtime_config.max_provider_input_tokens
        )
        adjusted = request
        metrics = self._estimate_request_token_budget(adjusted)
        while metrics["estimated_input_tokens"] > budget:
            continuation_mode = str(adjusted.metadata.get("continuation_mode") or "initial")
            if continuation_mode != "initial":
                reduced_output_tokens = max(200, adjusted.max_output_tokens - 150)
                if reduced_output_tokens == adjusted.max_output_tokens:
                    break
                adjusted = replace(adjusted, max_output_tokens=reduced_output_tokens)
            elif adjusted.recent_messages:
                adjusted = replace(adjusted, recent_messages=adjusted.recent_messages[1:])
                grounding_context.grounding_trimmed = True
                grounding_context.trim_reason = "token_budget"
            elif adjusted.grounding_context and isinstance(adjusted.grounding_context.get("sources"), list):
                current_sources = [
                    item for item in adjusted.grounding_context["sources"] if isinstance(item, dict)
                ]
                trimmed_sources = self._trim_sources_by_char_budget(
                    sources=[AssistantGroundingSource.model_validate(item) for item in current_sources],
                    char_budget=max(self.runtime_config.max_total_grounding_chars // 2, 1200),
                )
                trimmed_source_payloads = [item.model_dump(mode="json") for item in trimmed_sources]
                if trimmed_source_payloads == current_sources:
                    if len(current_sources) > 1:
                        adjusted_grounding_context = dict(adjusted.grounding_context)
                        adjusted_grounding_context["sources"] = current_sources[:-1]
                        adjusted_grounding_context["grounding_trimmed"] = True
                        adjusted_grounding_context["trim_reason"] = "token_budget"
                        adjusted = replace(adjusted, grounding_context=adjusted_grounding_context)
                        grounding_context.grounding_trimmed = True
                        grounding_context.trim_reason = "token_budget"
                        metrics = self._estimate_request_token_budget(adjusted)
                        continue
                    reduced_output_tokens = max(200, adjusted.max_output_tokens - 150)
                    if reduced_output_tokens == adjusted.max_output_tokens:
                        break
                    adjusted = replace(adjusted, max_output_tokens=reduced_output_tokens)
                    metrics = self._estimate_request_token_budget(adjusted)
                    continue
                adjusted_grounding_context = dict(adjusted.grounding_context)
                adjusted_grounding_context["sources"] = trimmed_source_payloads
                adjusted_grounding_context["grounding_trimmed"] = True
                adjusted_grounding_context["trim_reason"] = "token_budget"
                adjusted = replace(adjusted, grounding_context=adjusted_grounding_context)
                grounding_context.grounding_trimmed = True
                grounding_context.trim_reason = "token_budget"
            elif adjusted.knowledge_chunks:
                adjusted = replace(adjusted, knowledge_chunks=adjusted.knowledge_chunks[:-1])
            else:
                reduced_output_tokens = max(200, adjusted.max_output_tokens - 150)
                if reduced_output_tokens == adjusted.max_output_tokens:
                    break
                adjusted = replace(adjusted, max_output_tokens=reduced_output_tokens)
            metrics = self._estimate_request_token_budget(adjusted)
        adjusted.metadata.update(metrics)
        self._log_provider_token_budget(adjusted, metrics)
        return adjusted

    def _estimate_request_token_budget(
        self,
        request: AssistantProviderRequest,
    ) -> dict[str, Any]:
        continuation = str(request.metadata.get("continuation_mode") or "initial") != "initial"
        grounding_tokens = estimate_tokens(request.grounding_context) if not continuation else 0
        history_tokens = estimate_tokens(request.recent_messages)
        tool_result_tokens = estimate_tokens(request.tool_results) + estimate_tokens(request.continuation_tool_outputs)
        tool_definition_tokens = estimate_tokens(request.available_tools)
        instruction_tokens = estimate_tokens(request.system_instructions)
        user_tokens = estimate_tokens(request.user_message)
        previous_output_tokens = estimate_tokens(request.previous_output_items)
        estimated_input_tokens = (
            grounding_tokens
            + history_tokens
            + tool_result_tokens
            + tool_definition_tokens
            + instruction_tokens
            + user_tokens
            + previous_output_tokens
        )
        trimmed = bool(request.grounding_context and request.grounding_context.get("grounding_trimmed"))
        return {
            "estimated_input_tokens": estimated_input_tokens,
            "estimated_grounding_tokens": grounding_tokens,
            "estimated_history_tokens": history_tokens,
            "estimated_tool_result_tokens": tool_result_tokens,
            "estimated_tool_definition_tokens": tool_definition_tokens,
            "estimated_instruction_tokens": instruction_tokens,
            "estimated_previous_output_tokens": previous_output_tokens,
            "trimmed": trimmed,
            "continuation": continuation,
        }

    def _log_provider_token_budget(
        self,
        request: AssistantProviderRequest,
        metrics: dict[str, Any],
    ) -> None:
        logger.info(
            json.dumps(
                {
                    "event": "assistant_provider_token_budget",
                    "estimated_input_tokens": metrics["estimated_input_tokens"],
                    "estimated_grounding_tokens": metrics["estimated_grounding_tokens"],
                    "estimated_history_tokens": metrics["estimated_history_tokens"],
                    "estimated_tool_result_tokens": metrics["estimated_tool_result_tokens"],
                    "trimmed": metrics["trimmed"],
                    "continuation": metrics["continuation"],
                    "request_id": request.metadata.get("request_id"),
                    "conversation_id": request.conversation_id,
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )

    @staticmethod
    def _select_provider_available_tools(
        *,
        available_tools: list[dict[str, Any]],
        grounding_context: AssistantGroundingContext,
    ) -> list[dict[str, Any]]:
        diagnostic_intent = str(grounding_context.retrieval_plan.get("diagnostic_intent") or "").strip()
        if diagnostic_intent:
            return []
        return available_tools

    def _continuation_response_id(self, response_id: str | None) -> str | None:
        if not self.runtime_config.store_responses:
            return None
        return response_id

    def _retrieve_knowledge_chunks(
        self,
        *,
        query: str,
        response_language: str,
        route_context: dict[str, Any] | None,
        actor: RequestAuthorizationContext,
        workflow_intent: str | None,
        planned_page_ids: list[str] | None = None,
        planned_module_keys: list[str] | None = None,
    ) -> list[AssistantKnowledgeChunkResult]:
        if self.knowledge_retriever is None:
            return []
        expanded_query = expand_assistant_query(
            query,
            workflow_intent=workflow_intent,
            ui_page_id=None,
        )
        page_id = planned_page_ids[0] if planned_page_ids else None
        if page_id is None and route_context is not None:
            page_id = route_context.get("page_id")
        module_key = planned_module_keys[0] if planned_module_keys else None
        results = self.knowledge_retriever.retrieve_knowledge_chunks(
            query=query,
            language_code=response_language,
            module_key=module_key if isinstance(module_key, str) else None,
            page_id=page_id if isinstance(page_id, str) else None,
            module_keys=list(planned_module_keys or expanded_query.module_hints),
            page_ids=list(planned_page_ids or expanded_query.page_hints),
            workflow_intent=workflow_intent,
            role_keys=sorted(actor.role_keys),
            permission_keys=sorted(actor.permission_keys),
            limit=self.runtime_config.max_context_chunks,
        )
        return results

    @staticmethod
    def _collect_missing_permissions_from_summaries(
        summaries: list[AssistantToolResultSummary],
    ) -> list[AssistantMissingPermission]:
        seen: set[tuple[str, str]] = set()
        results: list[AssistantMissingPermission] = []
        for summary in summaries:
            rows = summary.summary.get("missing_permissions", []) if isinstance(summary.summary, dict) else []
            if not isinstance(rows, list):
                continue
            for row in rows:
                if not isinstance(row, dict):
                    continue
                permission = str(row.get("permission") or "").strip()
                reason = str(row.get("reason") or "").strip()
                if not permission:
                    continue
                key = (permission, reason)
                if key in seen:
                    continue
                seen.add(key)
                results.append(AssistantMissingPermission(permission=permission, reason=reason))
        return results

    def _diagnostic_tool_result_source(
        self,
        *,
        source_name: str,
        tool_name: str,
        result: Any,
        title: str,
    ) -> AssistantGroundingSource:
        payload = result.redacted_output if isinstance(result.redacted_output, dict) else result.data
        if not isinstance(payload, dict):
            payload = {}
        return AssistantGroundingSource(
            source_id=f"tool_result_summary:{tool_name}",
            source_type="tool_result_summary",
            source_name=source_name,
            page_id=self._first_page_id_from_payload(payload),
            module_key=self._first_module_key_from_payload(payload),
            title=title,
            content=self._compact_diagnostic_payload_text(payload),
            facts=payload,
            verified=bool(result.ok),
            permission_checked=True,
            content_bearing=bool(payload),
            score=self._diagnostic_tool_result_priority(tool_name),
        )

    @staticmethod
    def _diagnostic_tool_result_priority(tool_name: str) -> float:
        priorities = {
            "field.inspect_released_schedule_visibility": 18.0,
            "planning.inspect_shift_visibility": 16.0,
            "planning.inspect_shift_release_state": 15.0,
            "planning.inspect_assignment": 14.0,
            "employees.get_employee_mobile_access_status": 13.0,
            "employees.get_employee_readiness_summary": 12.0,
            "employees.get_employee_operational_profile": 11.0,
            "planning.find_assignments": 10.0,
            "planning.find_shifts": 9.0,
            "employees.search_employee_by_name": 8.0,
            "assistant.search_accessible_pages": 2.0,
            "assistant.get_current_user_capabilities": 2.0,
        }
        return priorities.get(tool_name, 4.0)

    @staticmethod
    def _compact_diagnostic_payload_text(payload: dict[str, Any]) -> str:
        for key in (
            "summary",
            "safe_note",
            "source_status",
            "scope_kind",
        ):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()[:220]
        for key in ("mobile_access", "readiness", "release_state", "visibility", "assignment", "employee"):
            value = payload.get(key)
            if isinstance(value, dict):
                for nested_key in ("summary", "visibility_state", "shift_release_state", "assignment_status", "status", "employee_status"):
                    nested_value = value.get(nested_key)
                    if isinstance(nested_value, str) and nested_value.strip():
                        return nested_value.strip()[:220]
        if payload.get("found") is False:
            return "No directly visible record was confirmed in the current scope."
        if isinstance(payload.get("matches"), list):
            return f"Returned {len(payload['matches'])} candidate rows."
        if isinstance(payload.get("pages"), list):
            return f"Returned {len(payload['pages'])} accessible page hints."
        return "Redacted diagnostic tool result."

    @staticmethod
    def _first_page_id_from_payload(payload: dict[str, Any]) -> str | None:
        for key in ("page_id",):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        for collection_key in ("pages", "matches"):
            rows = payload.get(collection_key)
            if isinstance(rows, list):
                for row in rows:
                    if isinstance(row, dict):
                        value = row.get("page_id")
                        if isinstance(value, str) and value.strip():
                            return value.strip()
        for nested_key in ("assignment", "release_state", "visibility", "employee"):
            nested = payload.get(nested_key)
            if isinstance(nested, dict):
                value = nested.get("page_id")
                if isinstance(value, str) and value.strip():
                    return value.strip()
        return None

    @staticmethod
    def _first_module_key_from_payload(payload: dict[str, Any]) -> str | None:
        value = payload.get("module_key")
        if isinstance(value, str) and value.strip():
            return value.strip()
        page_id = AssistantService._first_page_id_from_payload(payload)
        if page_id is None:
            return None
        return AssistantService._module_key_from_page_id(page_id)

    @staticmethod
    def _module_key_from_page_id(page_id: str) -> str:
        if page_id.startswith("PS"):
            return "platform_services"
        if page_id.startswith("FD"):
            return "field_execution"
        if page_id.startswith("FI"):
            return "finance"
        if page_id.startswith("F"):
            return "dashboard"
        if page_id.startswith("E"):
            return "employees"
        if page_id.startswith("P"):
            return "planning"
        if page_id.startswith("C"):
            return "customers"
        if page_id.startswith("S"):
            return "subcontractors"
        return "platform"

    def _validate_provider_links(
        self,
        *,
        links_payload: Any,
        actor: RequestAuthorizationContext,
        conversation_id: str,
    ) -> list[dict[str, Any]]:
        if self.tool_registry is None or not isinstance(links_payload, list) or not links_payload:
            return []
        validated: list[dict[str, Any]] = []
        seen_page_ids: set[str] = set()
        for row in links_payload:
            if not isinstance(row, dict):
                continue
            page_id = str(row.get("page_id") or "").strip()
            if not page_id or page_id in seen_page_ids:
                continue
            seen_page_ids.add(page_id)
            tool_result = self.execute_registered_tool(
                tool_name="navigation.build_allowed_link",
                input_data={
                    "page_id": page_id,
                    "reason": self._sanitize_optional_text(str(row.get("reason") or row.get("label") or ""), 240),
                },
                actor=actor,
                conversation_id=conversation_id,
            )
            link_payload = tool_result.data if isinstance(tool_result.data, dict) else {}
            if not tool_result.ok or not link_payload.get("allowed"):
                continue
            safe_link = link_payload.get("link")
            if isinstance(safe_link, dict):
                validated.append(safe_link)
        return validated

    def _ensure_answer_links(
        self,
        *,
        answer_text: str,
        validated_links: list[dict[str, Any]],
        actor: RequestAuthorizationContext,
        conversation_id: str,
    ) -> list[dict[str, Any]]:
        if self.tool_registry is None:
            return validated_links
        referenced_page_ids = self._extract_page_ids_from_answer(answer_text)
        if not referenced_page_ids:
            return validated_links
        seen_page_ids = {
            str(item.get("page_id") or "").strip()
            for item in validated_links
            if isinstance(item, dict)
        }
        enriched = list(validated_links)
        for page_id in referenced_page_ids:
            if page_id in seen_page_ids:
                continue
            tool_result = self.execute_registered_tool(
                tool_name="navigation.build_allowed_link",
                input_data={"page_id": page_id},
                actor=actor,
                conversation_id=conversation_id,
            )
            link_payload = tool_result.data if isinstance(tool_result.data, dict) else {}
            if not tool_result.ok or not link_payload.get("allowed"):
                continue
            safe_link = link_payload.get("link")
            if isinstance(safe_link, dict):
                enriched.append(safe_link)
                seen_page_ids.add(page_id)
        return enriched

    def _normalize_user_facing_answer_links(
        self,
        *,
        answer_text: str,
        allowed_links: list[dict[str, Any]],
    ) -> tuple[str, list[AssistantAnswerSegment]]:
        inline_aliases = self._collect_inline_page_aliases(answer_text)
        page_label_map = self._build_page_label_map(allowed_links)
        normalized = answer_text

        for page_id, label in page_label_map.items():
            page_pattern = re.escape(page_id)
            normalized = re.sub(rf"\(\s*{page_pattern}\s*\)", "", normalized)
            normalized = re.sub(rf"\s*[-–—]\s*{page_pattern}\b", "", normalized)
            if not label:
                continue
            label_pattern = re.escape(label)
            normalized = re.sub(
                _PAGE_ID_SUFFIX_PATTERN_TEMPLATE.format(label=label_pattern, page_id=page_pattern),
                label,
                normalized,
            )

        normalized = _PAGE_ID_PATTERN.sub(
            lambda match: page_label_map.get(match.group(0), ""),
            normalized,
        )
        normalized = _MULTISPACE_PATTERN.sub(" ", normalized)
        normalized = _SPACE_AROUND_NEWLINE_PATTERN.sub("\n", normalized)
        normalized = _WHITESPACE_BEFORE_PUNCTUATION_PATTERN.sub(r"\1", normalized)
        normalized = normalized.strip()

        segments = self._build_answer_segments(
            answer_text=normalized,
            allowed_links=allowed_links,
            inline_aliases=inline_aliases,
        )
        return normalized, segments

    def _build_answer_segments(
        self,
        *,
        answer_text: str,
        allowed_links: list[dict[str, Any]],
        inline_aliases: dict[str, str] | None = None,
    ) -> list[AssistantAnswerSegment]:
        if not answer_text:
            return []
        base_links = [
            item
            for item in (
                AssistantNavigationLink.model_validate(link)
                for link in allowed_links
                if isinstance(link, dict)
            )
            if item.label and item.path
        ]
        links = list(base_links)
        alias_map = inline_aliases or {}
        for link in base_links:
            alias = alias_map.get(str(link.page_id or "").strip())
            if alias and alias != link.label:
                links.append(link.model_copy(update={"label": alias}))
        if not links:
            return [AssistantAnswerSegment(type="text", text=answer_text)]

        ordered_links = sorted(links, key=lambda item: len(item.label), reverse=True)
        segments: list[AssistantAnswerSegment] = []
        cursor = 0
        while cursor < len(answer_text):
            next_match: tuple[int, int, AssistantNavigationLink] | None = None
            for link in ordered_links:
                start = answer_text.find(link.label, cursor)
                if start < 0:
                    continue
                end = start + len(link.label)
                if next_match is None or start < next_match[0]:
                    next_match = (start, end, link)
            if next_match is None:
                segments.append(AssistantAnswerSegment(type="text", text=answer_text[cursor:]))
                break
            start, end, link = next_match
            if start > cursor:
                segments.append(AssistantAnswerSegment(type="text", text=answer_text[cursor:start]))
            segments.append(
                AssistantAnswerSegment(
                    type="link",
                    text=answer_text[start:end],
                    link=link,
                )
            )
            cursor = end
        return [segment for segment in segments if segment.text]

    @staticmethod
    def _extract_page_ids_from_answer(answer_text: str) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for match in _PAGE_ID_PATTERN.finditer(answer_text):
            page_id = match.group(0)
            if page_id in seen:
                continue
            seen.add(page_id)
            result.append(page_id)
        return result

    @staticmethod
    def _build_page_label_map(allowed_links: list[dict[str, Any]]) -> dict[str, str]:
        page_labels = {seed.page_id: seed.label for seed in ASSISTANT_PAGE_ROUTE_SEEDS}
        for link in allowed_links:
            if not isinstance(link, dict):
                continue
            page_id = str(link.get("page_id") or "").strip()
            label = str(link.get("label") or "").strip()
            if page_id and label:
                page_labels[page_id] = label
        return page_labels

    @staticmethod
    def _collect_inline_page_aliases(answer_text: str) -> dict[str, str]:
        aliases: dict[str, str] = {}
        for match in re.finditer(rf"(?P<context>[^\n()]{{1,120}})\(\s*(?P<page_id>{_PAGE_ID_PATTERN.pattern})\s*\)", answer_text):
            page_id = str(match.group("page_id") or "").strip()
            candidate = AssistantService._extract_inline_label_candidate(str(match.group("context") or ""))
            if page_id and candidate:
                aliases[page_id] = candidate
        for match in re.finditer(rf"(?P<context>[^\n]{{1,120}})[-–—]\s*(?P<page_id>{_PAGE_ID_PATTERN.pattern})\b", answer_text):
            page_id = str(match.group("page_id") or "").strip()
            candidate = AssistantService._extract_inline_label_candidate(str(match.group("context") or ""))
            if page_id and candidate:
                aliases[page_id] = candidate
        return aliases

    @staticmethod
    def _extract_inline_label_candidate(value: str) -> str | None:
        cleaned = value.strip().strip("([{-–— ").strip()
        for separator in (".", "!", "?", ":", ";", "\n"):
            if separator in cleaned:
                cleaned = cleaned.rsplit(separator, 1)[-1].strip()
        for marker in (" im ", " in the ", " in ", " auf ", " on ", " unter ", " within "):
            if marker in cleaned:
                cleaned = cleaned.rsplit(marker, 1)[-1].strip()
        cleaned = cleaned.strip(" '\"()[]{}")
        if len(cleaned) < 2:
            return None
        return cleaned[-80:]

    @staticmethod
    def _grounding_sources_from_tool_result(
        source_type: str,
        result: Any,
    ) -> list[AssistantGroundingSource]:
        payload = result.redacted_output if result.redacted_output is not None else result.data
        if not isinstance(payload, dict):
            return []

        sources: list[AssistantGroundingSource] = []
        if source_type == "workflow":
            for workflow in payload.get("workflows", []) or []:
                if not isinstance(workflow, dict):
                    continue
                sources.append(
                    AssistantGroundingSource(
                        source_id=f"workflow:{workflow.get('workflow_key')}:{workflow.get('workflow_key')}",
                        source_type="workflow",
                        source_name=workflow.get("workflow_key"),
                        page_id=((workflow.get("linked_page_ids") or [None])[0]),
                        title=workflow.get("title"),
                        content=workflow.get("summary"),
                        facts=workflow,
                        verified=True,
                        permission_checked=True,
                    )
                )
                for step in workflow.get("steps", []) or []:
                    if not isinstance(step, dict):
                        continue
                    sources.append(
                        AssistantGroundingSource(
                            source_id=f"workflow:{workflow.get('workflow_key')}:{step.get('step_key') or step.get('page_id') or 'step'}",
                            source_type="workflow",
                            source_name=workflow.get("workflow_key"),
                            page_id=step.get("page_id"),
                            module_key=step.get("module_key"),
                            title=step.get("step_key"),
                            content=step.get("purpose"),
                            facts=step,
                            verified=True,
                            permission_checked=True,
                        )
                    )
            return sources

        if source_type == "ui_action":
            sources.append(
                AssistantGroundingSource(
                    source_id=f"ui_action:{payload.get('page_id') or 'unknown'}:{payload.get('intent') or 'action'}",
                    source_type="ui_action",
                    source_name=payload.get("intent"),
                    page_id=payload.get("page_id"),
                    title=payload.get("page_title"),
                    content=payload.get("safe_note"),
                    facts=payload,
                    verified=bool((payload.get("action") or {}).get("verified", False)),
                    permission_checked=True,
                )
            )
            return sources

        if source_type == "page_help_manifest":
            sources.append(
                AssistantGroundingSource(
                    source_id=f"page_help:{payload.get('page_id') or 'unknown'}",
                    source_type="page_help_manifest",
                    source_name=payload.get("page_title"),
                    page_id=payload.get("page_id"),
                    module_key=payload.get("module_key"),
                    title=payload.get("page_title"),
                    content=payload.get("source_status"),
                    facts=payload,
                    verified=payload.get("source_status") == "verified",
                    permission_checked=True,
                )
            )
            return sources

        if source_type == "page_route":
            for page in payload.get("pages", []) or []:
                if not isinstance(page, dict):
                    continue
                sources.append(
                    AssistantGroundingSource(
                        source_id=f"page_route:{page.get('page_id') or page.get('route_name') or 'unknown'}",
                        source_type="page_route",
                        source_name=page.get("route_name"),
                        page_id=page.get("page_id"),
                        module_key=page.get("module_key"),
                        title=page.get("label"),
                        content=page.get("path_template"),
                        facts=page,
                        verified=True,
                        permission_checked=True,
                    )
                )
            return sources

        if source_type == "diagnostic":
            sources.append(
                AssistantGroundingSource(
                    source_id=f"diagnostic:{payload.get('diagnostic_key') or 'unknown'}",
                    source_type="diagnostic",
                    source_name=payload.get("diagnostic_key"),
                    page_id=None,
                    module_key="planning",
                    title=payload.get("summary"),
                    content=payload.get("status"),
                    facts=payload,
                    verified=True,
                    permission_checked=True,
                )
            )
        return sources

    def _invoke_provider_with_retry(self, request: AssistantProviderRequest) -> AssistantProviderResult:
        current_request = request
        attempts_remaining = max(self.runtime_config.rate_limit_max_retries, 0)
        fallback_model = self.runtime_config.fallback_response_model.strip() or None
        fallback_used = False
        while True:
            try:
                return self.provider.generate(current_request)
            except AssistantProviderRateLimitError as exc:
                if attempts_remaining > 0:
                    attempts_remaining -= 1
                    current_request = self._shrink_request_for_rate_limit_retry(current_request)
                    retry_delay = min(
                        max(exc.retry_after_seconds or 0.0, 0.0),
                        max(float(self.runtime_config.rate_limit_retry_seconds), 0.0),
                    )
                    if retry_delay > 0:
                        sleep(retry_delay)
                    continue
                if fallback_model and not fallback_used:
                    fallback_used = True
                    logger.info(
                        json.dumps(
                            {
                                "event": "assistant_provider_model_fallback",
                                "conversation_id": request.conversation_id,
                                "request_id": request.metadata.get("request_id"),
                                "from_model": request.model_name_override or self.runtime_config.response_model,
                                "to_model": fallback_model,
                            },
                            ensure_ascii=False,
                            sort_keys=True,
                        )
                    )
                    current_request = self._shrink_request_for_rate_limit_retry(
                        replace(current_request, model_name_override=fallback_model)
                    )
                    continue
                raise

    def _call_provider_with_fallback_capture(
        self,
        *,
        request: AssistantProviderRequest,
        grounding_context: AssistantGroundingContext,
        tool_results: list[AssistantToolResultSummary],
        had_prior_provider_output: bool,
    ) -> AssistantProviderResult:
        try:
            return self._call_provider(request)
        except ApiException as exc:
            if not self._is_provider_degraded_fallback_error(
                exc=exc,
                continuation_mode=str(request.metadata.get("continuation_mode") or "initial"),
                had_prior_provider_output=had_prior_provider_output,
            ):
                raise
            raise AssistantProviderDegradedFallbackCandidate(
                api_exception=exc,
                grounding_context=grounding_context,
                tool_results=list(tool_results),
                continuation_mode=str(request.metadata.get("continuation_mode") or "initial"),
                had_prior_provider_output=had_prior_provider_output,
            ) from exc

    @staticmethod
    def _is_provider_degraded_fallback_error(
        *,
        exc: ApiException,
        continuation_mode: str,
        had_prior_provider_output: bool,
    ) -> bool:
        if exc.code in {
            "assistant.provider.rate_limited",
            "assistant.provider.timeout",
            "assistant.provider.unavailable",
        }:
            return True
        if exc.code in {"assistant.provider.invalid_request", "assistant.provider.invalid_response"}:
            return continuation_mode != "initial" or had_prior_provider_output
        return False

    def _can_build_provider_degraded_response(
        self,
        *,
        classification: AssistantClassificationResult,
        grounding_context: AssistantGroundingContext,
    ) -> bool:
        if classification.is_out_of_scope or classification.is_unsafe:
            return False
        return any(
            self._is_content_bearing_source(source) or source.source_type == "diagnostic_fact"
            for source in grounding_context.sources
        )

    def _build_provider_degraded_payload(
        self,
        *,
        response_language: str,
        grounding_context: AssistantGroundingContext,
        tool_results: list[AssistantToolResultSummary],
        continuation_mode: str,
        provider_error_code: str,
    ) -> dict[str, Any]:
        source_basis = self._allowed_source_basis_items(grounding_context)
        diagnosis = self._build_provider_degraded_diagnosis(
            response_language=response_language,
            tool_results=tool_results,
            provider_error_code=provider_error_code,
        )
        next_steps = self._build_provider_degraded_next_steps(
            response_language=response_language,
            grounding_context=grounding_context,
            tool_results=tool_results,
        )
        answer = self._build_provider_degraded_answer(
            response_language=response_language,
            source_basis=source_basis,
            diagnosis=diagnosis,
            has_links=bool(self._grounding_links(grounding_context)),
        )
        confidence = (
            AssistantConfidence.MEDIUM
            if len(source_basis) >= 2 or len(next_steps) >= 2
            else AssistantConfidence.LOW
        )
        return {
            "answer": answer,
            "provider_degraded": True,
            "confidence": confidence.value,
            "out_of_scope": False,
            "diagnosis": diagnosis,
            "links": [],
            "missing_permissions": self._collect_missing_permissions_from_summaries(tool_results),
            "next_steps": next_steps[:4],
            "tool_trace_id": f"provider_degraded:{continuation_mode}:{provider_error_code}",
            "source_basis": [item.model_dump(mode="json") for item in source_basis[:4]],
        }

    def _build_provider_degraded_diagnosis(
        self,
        *,
        response_language: str,
        tool_results: list[AssistantToolResultSummary],
        provider_error_code: str,
    ) -> list[dict[str, str]]:
        items: list[dict[str, str]] = [
            {
                "finding": self._provider_degraded_warning_text(response_language),
                "severity": "info",
                "evidence": self._provider_degraded_evidence_text(response_language, provider_error_code),
            }
        ]
        seen_findings = {items[0]["finding"]}
        for tool_result in tool_results:
            payload = tool_result.summary.get("data")
            if not isinstance(payload, dict):
                continue
            findings = payload.get("findings")
            if not isinstance(findings, list):
                continue
            for row in findings:
                if not isinstance(row, dict):
                    continue
                finding = str(row.get("finding") or "").strip()
                if not finding or finding in seen_findings:
                    continue
                severity = str(row.get("severity") or "info").strip() or "info"
                evidence = str(row.get("evidence") or row.get("status") or "").strip() or finding
                items.append(
                    {
                        "finding": finding,
                        "severity": severity if severity in {"info", "warning", "blocking"} else "info",
                        "evidence": evidence,
                    }
                )
                seen_findings.add(finding)
                if len(items) >= 5:
                    return items
            summary_text = str(payload.get("summary") or "").strip()
            if summary_text and summary_text not in seen_findings:
                items.append(
                    {
                        "finding": summary_text,
                        "severity": "info",
                        "evidence": str(payload.get("status") or summary_text),
                    }
                )
                seen_findings.add(summary_text)
                if len(items) >= 5:
                    return items
        return items

    def _build_provider_degraded_next_steps(
        self,
        *,
        response_language: str,
        grounding_context: AssistantGroundingContext,
        tool_results: list[AssistantToolResultSummary],
    ) -> list[str]:
        steps: list[str] = []
        seen: set[str] = set()

        def append_step(value: str) -> None:
            cleaned = value.strip()
            if not cleaned or cleaned in seen:
                return
            seen.add(cleaned)
            steps.append(cleaned)

        for tool_result in tool_results:
            payload = tool_result.summary.get("data")
            if not isinstance(payload, dict):
                continue
            next_steps = payload.get("next_steps")
            if isinstance(next_steps, list):
                for step in next_steps:
                    if isinstance(step, str):
                        append_step(step)
            missing_input = payload.get("missing_input")
            if isinstance(missing_input, list):
                for field_name in missing_input:
                    if not isinstance(field_name, str):
                        continue
                    append_step(self._missing_diagnostic_input_text(response_language, field_name))

        for source in grounding_context.sources:
            if source.source_type != "missing_diagnostic_input":
                continue
            if source.content:
                append_step(source.content)

        return steps[:4]

    def _build_provider_degraded_answer(
        self,
        *,
        response_language: str,
        source_basis: list[AssistantSourceBasisItem],
        diagnosis: list[dict[str, str]],
        has_links: bool,
    ) -> str:
        evidence_points: list[str] = []
        for item in diagnosis[1:]:
            finding = str(item.get("finding") or "").strip()
            if finding:
                evidence_points.append(finding)
            if len(evidence_points) >= 4:
                break
        if not evidence_points:
            for item in source_basis[:4]:
                evidence = item.evidence.strip()
                if evidence:
                    evidence_points.append(evidence)
        intro = self._provider_degraded_intro_text(response_language)
        if evidence_points:
            body = self._provider_degraded_points_text(response_language, evidence_points[:4])
        else:
            body = self._provider_degraded_no_points_text(response_language)
        if has_links:
            return f"{intro} {body} {self._provider_degraded_links_text(response_language)}".strip()
        return f"{intro} {body}".strip()

    @staticmethod
    def _provider_degraded_intro_text(response_language: str) -> str:
        if response_language == "de":
            return "Die Anfrage konnte nicht vollständig mit dem KI-Modell abgeschlossen werden."
        if response_language == "fa":
            return "این درخواست با مدل هوش مصنوعی به طور کامل نهایی نشد."
        return "The request could not be completed fully with the AI model."

    @staticmethod
    def _provider_degraded_points_text(response_language: str, evidence_points: list[str]) -> str:
        joined = "; ".join(point.rstrip(".") for point in evidence_points if point.strip())
        if response_language == "de":
            return f"Auf Basis der bereits geprüften SicherPlan-Kontexte sollten Sie die folgenden Punkte kontrollieren: {joined}."
        if response_language == "fa":
            return f"بر اساس کانتکست‌های از قبل بررسی‌شده SicherPlan، این موارد را بررسی کنید: {joined}."
        return f"Based on the already checked SicherPlan context, review these points: {joined}."

    @staticmethod
    def _provider_degraded_no_points_text(response_language: str) -> str:
        if response_language == "de":
            return "Es liegen bereits geprüfte SicherPlan-Kontexte vor, aber es konnten nur begrenzte sichere Hinweise zurückgegeben werden."
        if response_language == "fa":
            return "کانتکست‌های بررسی‌شده SicherPlan موجود است، اما فقط راهنمایی محدود و ایمن قابل بازگشت بود."
        return "Verified SicherPlan context is available, but only limited safe guidance could be returned."

    @staticmethod
    def _provider_degraded_links_text(response_language: str) -> str:
        if response_language == "de":
            return "Nutzen Sie bei Bedarf die freigegebenen Links unten."
        if response_language == "fa":
            return "در صورت نیاز از لینک‌های مجاز زیر استفاده کنید."
        return "Use the allowed links below if needed."

    @staticmethod
    def _provider_degraded_warning_text(response_language: str) -> str:
        if response_language == "de":
            return "Die Antwort wurde aus bereits geprüften SicherPlan-Kontexten erstellt."
        if response_language == "fa":
            return "این پاسخ از کانتکست‌های از قبل بررسی‌شده SicherPlan ساخته شد."
        return "This answer was assembled from already checked SicherPlan context."

    @staticmethod
    def _provider_degraded_evidence_text(response_language: str, provider_error_code: str) -> str:
        if response_language == "de":
            return f"Der KI-Anbieter konnte die Anfrage gerade nicht vollständig abschließen ({provider_error_code})."
        if response_language == "fa":
            return f"ارائه‌دهنده هوش مصنوعی فعلاً نتوانست درخواست را کامل کند ({provider_error_code})."
        return f"The AI provider could not complete the request fully right now ({provider_error_code})."

    @staticmethod
    def _missing_diagnostic_input_text(response_language: str, field_name: str) -> str:
        if response_language == "de":
            return f"Ergänzen Sie die fehlende Angabe: {field_name}."
        if response_language == "fa":
            return f"اطلاعات ناقص را کامل کنید: {field_name}."
        return f"Provide the missing input: {field_name}."

    def _shrink_request_for_rate_limit_retry(
        self,
        request: AssistantProviderRequest,
    ) -> AssistantProviderRequest:
        continuation_mode = str(request.metadata.get("continuation_mode") or "initial")
        reduced_output_tokens = max(
            200,
            request.max_output_tokens - 150,
        )
        updated = replace(request, max_output_tokens=reduced_output_tokens)
        if continuation_mode != "initial":
            updated = replace(
                updated,
                available_tools=[],
                recent_messages=[],
                knowledge_chunks=[],
                grounding_context=None,
            )
        elif updated.grounding_context and isinstance(updated.grounding_context.get("sources"), list):
            sources = [
                AssistantGroundingSource.model_validate(item)
                for item in updated.grounding_context["sources"]
                if isinstance(item, dict)
            ]
            trimmed_sources = self._trim_sources_by_char_budget(
                sources=sources,
                char_budget=max(self.runtime_config.max_total_grounding_chars // 2, 1000),
            )
            adjusted_grounding_context = dict(updated.grounding_context)
            adjusted_grounding_context["sources"] = [item.model_dump(mode="json") for item in trimmed_sources]
            adjusted_grounding_context["grounding_trimmed"] = True
            adjusted_grounding_context["trim_reason"] = "token_budget"
            updated = replace(updated, grounding_context=adjusted_grounding_context)
        if updated.recent_messages:
            updated = replace(updated, recent_messages=updated.recent_messages[-2:])
        metrics = self._estimate_request_token_budget(updated)
        updated.metadata.update(metrics)
        updated.metadata["rate_limit_retry_compacted"] = True
        return updated

    def _call_provider(self, request: AssistantProviderRequest) -> AssistantProviderResult:
        grounding_sources = 0
        grounding_attached = bool(request.grounding_context)
        if request.grounding_context and isinstance(request.grounding_context.get("sources"), list):
            grounding_sources = len(request.grounding_context["sources"])
        attempted_openai = self.runtime_config.provider_mode == "openai"
        self._log_provider_event(
            event="assistant_provider_call_started",
            request=request,
            grounding_attached=grounding_attached,
            grounding_sources=grounding_sources,
            openai_request_attempted=attempted_openai,
            provider_returned_successfully=False,
            provider_latency_ms=None,
            input_tokens=None,
            output_tokens=None,
        )
        try:
            result = self._invoke_provider_with_retry(request)
        except AssistantProviderConfigurationError as exc:
            self._log_provider_error(request=request, exc=exc, attempted_openai=attempted_openai)
            self._log_provider_event(
                event="assistant_provider_call_finished",
                request=request,
                grounding_attached=grounding_attached,
                grounding_sources=grounding_sources,
                openai_request_attempted=attempted_openai,
                provider_returned_successfully=False,
                provider_latency_ms=None,
                input_tokens=None,
                output_tokens=None,
            )
            raise ApiException(
                503,
                exc.code,
                "errors.assistant.provider.unavailable",
            ) from exc
        except AssistantProviderAuthenticationError as exc:
            self._log_provider_error(request=request, exc=exc, attempted_openai=attempted_openai)
            self._log_provider_event(
                event="assistant_provider_call_finished",
                request=request,
                grounding_attached=grounding_attached,
                grounding_sources=grounding_sources,
                openai_request_attempted=attempted_openai,
                provider_returned_successfully=False,
                provider_latency_ms=None,
                input_tokens=None,
                output_tokens=None,
            )
            raise ApiException(
                503,
                exc.code,
                "errors.assistant.provider.unavailable",
            ) from exc
        except AssistantProviderInvalidRequestError as exc:
            self._log_provider_error(request=request, exc=exc, attempted_openai=attempted_openai)
            self._log_provider_event(
                event="assistant_provider_call_finished",
                request=request,
                grounding_attached=grounding_attached,
                grounding_sources=grounding_sources,
                openai_request_attempted=attempted_openai,
                provider_returned_successfully=False,
                provider_latency_ms=None,
                input_tokens=None,
                output_tokens=None,
            )
            raise ApiException(
                502,
                exc.code,
                "errors.assistant.provider.invalid_response",
            ) from exc
        except AssistantProviderTimeoutError as exc:
            self._log_provider_error(request=request, exc=exc, attempted_openai=attempted_openai)
            self._log_provider_event(
                event="assistant_provider_call_finished",
                request=request,
                grounding_attached=grounding_attached,
                grounding_sources=grounding_sources,
                openai_request_attempted=attempted_openai,
                provider_returned_successfully=False,
                provider_latency_ms=None,
                input_tokens=None,
                output_tokens=None,
            )
            raise ApiException(
                504,
                exc.code,
                "errors.assistant.provider.timeout",
            ) from exc
        except AssistantProviderRateLimitError as exc:
            self._log_provider_error(request=request, exc=exc, attempted_openai=attempted_openai)
            self._log_provider_event(
                event="assistant_provider_call_finished",
                request=request,
                grounding_attached=grounding_attached,
                grounding_sources=grounding_sources,
                openai_request_attempted=attempted_openai,
                provider_returned_successfully=False,
                provider_latency_ms=None,
                input_tokens=None,
                output_tokens=None,
            )
            raise ApiException(
                503,
                exc.code,
                "errors.assistant.provider.rate_limited",
            ) from exc
        except AssistantProviderUnavailableError as exc:
            self._log_provider_error(request=request, exc=exc, attempted_openai=attempted_openai)
            self._log_provider_event(
                event="assistant_provider_call_finished",
                request=request,
                grounding_attached=grounding_attached,
                grounding_sources=grounding_sources,
                openai_request_attempted=attempted_openai,
                provider_returned_successfully=False,
                provider_latency_ms=None,
                input_tokens=None,
                output_tokens=None,
            )
            raise ApiException(
                503,
                exc.code,
                "errors.assistant.provider.unavailable",
            ) from exc
        except AssistantProviderStructuredOutputError as exc:
            self._log_provider_error(request=request, exc=exc, attempted_openai=attempted_openai)
            self._log_provider_event(
                event="assistant_provider_call_finished",
                request=request,
                grounding_attached=grounding_attached,
                grounding_sources=grounding_sources,
                openai_request_attempted=attempted_openai,
                provider_returned_successfully=False,
                provider_latency_ms=None,
                input_tokens=None,
                output_tokens=None,
            )
            raise ApiException(
                502,
                exc.code,
                "errors.assistant.provider.invalid_response",
            ) from exc

        if result.requested_tool_calls:
            self._log_provider_event(
                event="assistant_provider_call_finished",
                request=request,
                grounding_attached=grounding_attached,
                grounding_sources=grounding_sources,
                openai_request_attempted=attempted_openai,
                provider_returned_successfully=True,
                provider_latency_ms=result.latency_ms,
                input_tokens=result.usage.input_tokens if result.usage else None,
                output_tokens=result.usage.output_tokens if result.usage else None,
            )
            return result
        if not isinstance(result.final_response, dict):
            raise ApiException(
                502,
                "assistant.provider.invalid_response",
                "errors.assistant.provider.invalid_response",
            )
        try:
            validated = AssistantProviderStructuredOutput.model_validate(result.final_response)
        except Exception as exc:
            self._log_provider_event(
                event="assistant_provider_call_finished",
                request=request,
                grounding_attached=grounding_attached,
                grounding_sources=grounding_sources,
                openai_request_attempted=attempted_openai,
                provider_returned_successfully=False,
                provider_latency_ms=result.latency_ms,
                input_tokens=result.usage.input_tokens if result.usage else None,
                output_tokens=result.usage.output_tokens if result.usage else None,
            )
            raise ApiException(
                502,
                "assistant.provider.invalid_response",
                "errors.assistant.provider.invalid_response",
            ) from exc
        self._log_provider_event(
            event="assistant_provider_call_finished",
            request=request,
            grounding_attached=grounding_attached,
            grounding_sources=grounding_sources,
            openai_request_attempted=attempted_openai,
            provider_returned_successfully=True,
            provider_latency_ms=result.latency_ms,
            input_tokens=result.usage.input_tokens if result.usage else None,
            output_tokens=result.usage.output_tokens if result.usage else None,
        )
        return AssistantProviderResult(
            final_response=validated.model_dump(mode="json"),
            raw_text=result.raw_text,
            requested_tool_calls=result.requested_tool_calls,
            response_id=result.response_id,
            output_items=result.output_items,
            usage=result.usage,
            provider_name=result.provider_name,
            provider_mode=result.provider_mode,
            model_name=result.model_name,
            latency_ms=result.latency_ms,
            finish_reason=result.finish_reason,
        )

    def _provider_runtime_usable_for_chat(self) -> bool:
        if not self.runtime_config.enabled:
            return False
        if self.runtime_config.provider_mode == "openai":
            return self.runtime_config.openai_configured
        if self.runtime_config.provider_mode == "mock":
            return self.runtime_config.mock_provider_allowed
        return False

    def _log_provider_event(
        self,
        *,
        event: str,
        request: AssistantProviderRequest,
        grounding_attached: bool,
        grounding_sources: int,
        openai_request_attempted: bool,
        provider_returned_successfully: bool,
        provider_latency_ms: int | None,
        input_tokens: int | None,
        output_tokens: int | None,
    ) -> None:
        payload = {
            "event": event,
            "provider_mode": self.runtime_config.provider_mode,
            "model_name": request.model_name_override or self.runtime_config.response_model,
            "request_id": request.metadata.get("request_id"),
            "conversation_id": request.conversation_id,
            "user_id": request.metadata.get("user_id"),
            "tenant_id": request.metadata.get("tenant_id"),
            "grounding_attached": grounding_attached,
            "grounding_source_count": grounding_sources,
            "openai_request_attempted": openai_request_attempted,
            "provider_returned_successfully": provider_returned_successfully,
            "provider_latency_ms": provider_latency_ms,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "max_output_tokens": request.max_output_tokens,
        }
        logger.info(json.dumps(payload, ensure_ascii=False, sort_keys=True))

    def _log_provider_error(
        self,
        *,
        request: AssistantProviderRequest,
        exc: AssistantProviderError,
        attempted_openai: bool,
    ) -> None:
        payload = {
            "event": "assistant_provider_error",
            "provider_mode": self.runtime_config.provider_mode,
            "model_name": request.model_name_override or self.runtime_config.response_model,
            "request_id": request.metadata.get("request_id"),
            "conversation_id": request.conversation_id,
            "exception_class": type(exc).__name__,
            "provider_error_type": getattr(exc, "provider_error_type", None),
            "provider_error_code": getattr(exc, "provider_error_code", None),
            "http_status": getattr(exc, "http_status", None),
            "safe_message": getattr(exc, "safe_message", str(exc))[:240],
            "openai_request_attempted": attempted_openai,
        }
        logger.info(json.dumps(payload, ensure_ascii=False, sort_keys=True))

    def _log_tool_call_continuation_event(
        self,
        *,
        event: str,
        request: AssistantProviderRequest,
        response_id: str | None,
        call_ids: list[str],
        provider_returned_successfully: bool,
        input_tokens: int | None,
        output_tokens: int | None,
    ) -> None:
        payload = {
            "event": event,
            "provider_mode": self.runtime_config.provider_mode,
            "request_id": request.metadata.get("request_id"),
            "conversation_id": request.conversation_id,
            "response_id": response_id,
            "tool_call_count": len(call_ids),
            "call_ids": call_ids,
            "continuation_mode": request.metadata.get("continuation_mode"),
            "provider_returned_successfully": provider_returned_successfully,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        }
        logger.info(json.dumps(payload, ensure_ascii=False, sort_keys=True))

    def _log_retrieval_debug(
        self,
        *,
        query: str,
        plan: dict[str, Any],
        grounding_context: AssistantGroundingContext,
    ) -> None:
        expanded_query = expand_assistant_query(
            query,
            workflow_intent=plan.get("workflow_intent"),
            ui_page_id=None,
        )
        top_sources = [
            {
                "source_type": source.source_type,
                "source_name": source.source_name,
                "page_id": source.page_id,
                "module_key": source.module_key,
                "score": source.score,
                "why_selected": list(source.why_selected),
            }
            for source in grounding_context.sources[:8]
        ]
        payload = {
            "event": "assistant_retrieval_debug",
            "query": query,
            "expanded_query": expanded_query.expanded_query,
            "detected_terms": list(expanded_query.detected_terms),
            "expanded_terms_en": list(expanded_query.expanded_terms_en),
            "expanded_terms_de": list(expanded_query.expanded_terms_de),
            "workflow_intent": plan.get("workflow_intent"),
            "ui_intent": plan.get("ui_intent"),
            "likely_page_ids": plan.get("likely_page_ids", []),
            "likely_module_keys": plan.get("likely_module_keys", []),
            "top_sources": top_sources,
        }
        logger.info(json.dumps(payload, ensure_ascii=False, sort_keys=True))

    @staticmethod
    def _truncate_grounding_text(value: str | None, max_chars: int) -> str | None:
        if not value:
            return None
        if len(value) <= max_chars:
            return value
        return value[: max(max_chars - 3, 1)].rstrip() + "..."

    @staticmethod
    def _trim_grounding_facts(
        *,
        facts: dict[str, Any],
        max_chars: int,
    ) -> dict[str, Any]:
        if not isinstance(facts, dict) or not facts:
            return {}
        trimmed: dict[str, Any] = {}
        used = 0
        for key, value in facts.items():
            if used >= max_chars:
                break
            if isinstance(value, str):
                remaining = max(max_chars - used, 0)
                trimmed_value = value if len(value) <= remaining else value[: max(remaining - 3, 1)].rstrip() + "..."
                trimmed[key] = trimmed_value
                used += len(trimmed_value)
            elif isinstance(value, list):
                limited = value[:8]
                trimmed[key] = limited
                used += len(json.dumps(limited, ensure_ascii=False))
            elif isinstance(value, dict):
                trimmed[key] = {sub_key: sub_value for sub_key, sub_value in list(value.items())[:8]}
                used += len(json.dumps(trimmed[key], ensure_ascii=False))
            else:
                trimmed[key] = value
                used += len(str(value))
        return trimmed

    @staticmethod
    def _requires_content_bearing_sources(retrieval_plan: dict[str, Any]) -> bool:
        intent_category = str(retrieval_plan.get("intent_category") or "").strip()
        return intent_category in {"workflow_how_to", "ui_action_question"}

    @staticmethod
    def _is_content_bearing_source(source: AssistantGroundingSource) -> bool:
        content = (source.content or "").strip()
        facts = source.facts if isinstance(source.facts, dict) else {}
        if source.source_type == "knowledge_chunk":
            return bool(content)
        if source.source_type == "workflow":
            return bool(source.verified and content)
        if source.source_type == "ui_action":
            return bool(source.verified and (content or facts.get("action")))
        if source.source_type == "page_help_manifest":
            return bool(
                source.verified
                and (
                    facts.get("actions")
                    or facts.get("form_sections")
                    or facts.get("post_create_steps")
                    or facts.get("sidebar_path")
                )
            )
        if source.source_type == "diagnostic":
            return bool(
                source.verified
                and (
                    facts.get("summary")
                    or facts.get("findings")
                    or content
                )
            )
        if source.source_type == "diagnostic_fact":
            return bool(source.verified and content)
        if source.source_type == "tool_result_summary":
            return bool(source.verified and (content or facts))
        return False

    @staticmethod
    def _content_preview(source: AssistantGroundingSource) -> str | None:
        content = (source.content or "").strip()
        if source.source_type == "page_help_manifest" and content in {"active", "verified", "unverified"}:
            content = ""
        if content:
            return content[:160]
        facts = source.facts if isinstance(source.facts, dict) else {}
        if source.source_type == "ui_action":
            action = facts.get("action")
            if isinstance(action, dict):
                label = str(action.get("label") or "").strip()
                result = str(action.get("result") or "").strip()
                location = str(action.get("location") or "").strip()
                preview = " ".join(part for part in [label, location, result] if part)
                if preview:
                    return preview[:160]
        if source.source_type == "page_help_manifest":
            actions = facts.get("actions")
            if isinstance(actions, list) and actions:
                first = actions[0]
                if isinstance(first, dict):
                    label = str(first.get("label") or "").strip()
                    result = str(first.get("result") or "").strip()
                    preview = " ".join(part for part in [label, result] if part)
                    if preview:
                        return preview[:160]
        for key in ("safe_note", "summary"):
            value = str(facts.get(key) or "").strip()
            if value:
                return value[:160]
        return None

    @staticmethod
    def _source_priority(source_type: str) -> int:
        order = {
            "ui_action": 0,
            "workflow": 1,
            "diagnostic_fact": 2,
            "tool_result_summary": 3,
            "knowledge_chunk": 4,
            "page_help_manifest": 5,
            "diagnostic": 6,
            "allowed_navigation_link": 7,
            "page_route": 8,
            "current_route": 9,
        }
        return order.get(source_type, 99)

    def _build_source_basis_from_rag_trace(
        self,
        rag_trace: AssistantRagTraceRead | None,
    ) -> list[AssistantSourceBasisItem]:
        if rag_trace is None:
            return []
        result: list[AssistantSourceBasisItem] = []
        for source in rag_trace.top_sources:
            evidence = (source.content_preview or "").strip()
            if not evidence:
                continue
            result.append(
                AssistantSourceBasisItem(
                    source_type=self._normalize_source_basis_type(source.source_type),
                    source_name=source.source_name,
                    page_id=source.page_id,
                    module_key=source.module_key,
                    title=source.title,
                    evidence=evidence,
                )
            )
        return result[:4]

    def _build_validated_source_basis(
        self,
        *,
        provider_payload: dict[str, Any],
        grounding_context: AssistantGroundingContext | None,
        rag_trace: AssistantRagTraceRead | None,
    ) -> list[AssistantSourceBasisItem]:
        allowed_items = self._allowed_source_basis_items(grounding_context)
        if not allowed_items:
            return self._build_source_basis_from_rag_trace(rag_trace)

        requested = provider_payload.get("source_basis")
        if not isinstance(requested, list) or not requested:
            return allowed_items[:4]

        matched: list[AssistantSourceBasisItem] = []
        seen_keys: set[tuple[str, str | None, str | None, str | None]] = set()
        for item in requested:
            if not isinstance(item, dict):
                continue
            match_key = self._requested_source_basis_key(item)
            if match_key is None:
                continue
            allowed = next(
                (candidate for candidate in allowed_items if self._source_basis_key(candidate) == match_key),
                None,
            )
            if allowed is None:
                continue
            allowed_key = self._source_basis_key(allowed)
            if allowed_key in seen_keys:
                continue
            matched.append(allowed)
            seen_keys.add(allowed_key)
        if matched:
            return matched[:4]
        return allowed_items[:4]

    def _allowed_source_basis_items(
        self,
        grounding_context: AssistantGroundingContext | None,
    ) -> list[AssistantSourceBasisItem]:
        if grounding_context is None:
            return []
        ordered = sorted(
            grounding_context.sources,
            key=lambda item: (
                0 if self._is_content_bearing_source(item) else 1,
                self._source_priority(item.source_type),
                -(item.score or 0.0),
                item.page_id or "",
                item.title or "",
            ),
        )
        result: list[AssistantSourceBasisItem] = []
        seen_keys: set[tuple[str, str | None, str | None, str | None]] = set()
        for source in ordered:
            if not self._is_content_bearing_source(source):
                continue
            evidence = self._content_preview(source)
            if not evidence:
                continue
            item = AssistantSourceBasisItem(
                source_type=self._normalize_source_basis_type(source.source_type),
                source_name=source.source_name,
                page_id=source.page_id,
                module_key=source.module_key,
                title=source.title,
                evidence=evidence,
            )
            key = self._source_basis_key(item)
            if key in seen_keys:
                continue
            result.append(item)
            seen_keys.add(key)
            if len(result) >= 4:
                break
        return result

    @staticmethod
    def _requested_source_basis_key(
        item: dict[str, Any],
    ) -> tuple[str, str | None, str | None, str | None] | None:
        source_type = AssistantService._normalize_source_basis_type(str(item.get("source_type") or "").strip())
        if not source_type:
            return None
        source_name = str(item.get("source_name") or "").strip() or None
        page_id = str(item.get("page_id") or "").strip() or None
        title = str(item.get("title") or "").strip() or None
        return (source_type, source_name, page_id, title)

    @staticmethod
    def _source_basis_key(
        item: AssistantSourceBasisItem,
    ) -> tuple[str, str | None, str | None, str | None]:
        return (item.source_type, item.source_name, item.page_id, item.title)

    @staticmethod
    def _normalize_source_basis_type(source_type: str) -> str:
        normalized = source_type.strip()
        if normalized == "workflow":
            return "workflow_help"
        if normalized == "ui_action":
            return "page_help_manifest"
        return normalized

    @staticmethod
    def _mentions_precise_ui_claim(answer_text: str) -> bool:
        tokens = (
            "exact button",
            "button label",
            "exact label",
            "exact current ui label",
            "schaltfläche",
            "button namens",
            "genaue bezeichnung",
            "exakte bezeichnung",
        )
        return any(token in answer_text for token in tokens)

    @staticmethod
    def _evaluate_quality_gate(
        *,
        question: str,
        classification: AssistantClassificationResult | dict[str, Any] | None,
        response: AssistantStructuredResponse,
        rag_trace: AssistantRagTraceRead | None,
    ) -> AssistantRagQualityGateRead:
        classification_payload = (
            classification
            if isinstance(classification, dict)
            else AssistantService._serialize_classification(classification) if classification is not None else {}
        )
        return evaluate_rag_answer_quality(
            question=question,
            classification=classification_payload,
            response=response,
            rag_trace=rag_trace,
        )

    def _handle_quality_gate_result(
        self,
        quality_gate: AssistantRagQualityGateRead,
    ) -> None:
        if quality_gate.passed or self.runtime_config.rag_quality_gate_mode == "off":
            return
        logger.warning(
            "assistant_rag_quality_gate_failed",
            extra={"failures": list(quality_gate.failures)},
        )
        if self.runtime_config.rag_quality_gate_mode == "enforce_in_tests":
            raise ApiException(
                502,
                "assistant.rag_quality_gate.failed",
                "errors.assistant.provider.invalid_response",
                {"failures": list(quality_gate.failures)},
            )

    @staticmethod
    def _parse_tool_call_arguments(value: Any) -> dict[str, Any]:
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                return {}
            if isinstance(parsed, dict):
                return parsed
        return {}

    @staticmethod
    def _tool_result_to_summary(result: Any) -> AssistantToolResultSummary:
        summary: dict[str, Any] = {"ok": bool(result.ok)}
        summary_missing_permissions: list[dict[str, str]] = []
        if result.redacted_output is not None:
            summary["data"] = result.redacted_output
        elif result.data is not None:
            summary["data"] = result.data
        if result.error_code is not None:
            summary["error_code"] = result.error_code
        if result.error_message is not None:
            summary["error_message"] = result.error_message
        if result.missing_permissions:
            summary_missing_permissions.extend(result.missing_permissions)
        payload_data = summary.get("data")
        if isinstance(payload_data, dict):
            embedded_missing_permissions = payload_data.get("missing_permissions")
            if isinstance(embedded_missing_permissions, list):
                summary_missing_permissions.extend(
                    row for row in embedded_missing_permissions if isinstance(row, dict)
                )
        if summary_missing_permissions:
            summary["missing_permissions"] = summary_missing_permissions
        return AssistantToolResultSummary(
            tool_name=str(result.tool_name),
            summary=summary,
        )

    @staticmethod
    def _merge_provider_payload_with_tool_results(
        provider_payload: dict[str, Any],
        tool_results: list[AssistantToolResultSummary],
    ) -> dict[str, Any]:
        merged = dict(provider_payload)
        permission_rows: list[dict[str, str]] = []
        seen_permissions: set[tuple[str, str]] = set()

        for row in provider_payload.get("missing_permissions", []) or []:
            if not isinstance(row, dict):
                continue
            permission = str(row.get("permission") or "").strip()
            reason = str(row.get("reason") or "").strip()
            if not permission:
                continue
            key = (permission, reason)
            if key in seen_permissions:
                continue
            seen_permissions.add(key)
            permission_rows.append({"permission": permission, "reason": reason})

        for tool_result in tool_results:
            for row in tool_result.summary.get("missing_permissions", []) or []:
                if not isinstance(row, dict):
                    continue
                permission = str(row.get("permission") or "").strip()
                reason = str(row.get("reason") or "").strip()
                if not permission:
                    continue
                key = (permission, reason)
                if key in seen_permissions:
                    continue
                seen_permissions.add(key)
                permission_rows.append({"permission": permission, "reason": reason})

        if permission_rows:
            merged["missing_permissions"] = permission_rows
        return merged

    @staticmethod
    def _tool_result_to_provider_output(
        *,
        requested_call: dict[str, Any],
        tool_result: Any,
    ) -> dict[str, Any]:
        payload = tool_result.redacted_output
        if payload is None:
            payload = tool_result.data
        if payload is None:
            payload = {
                "ok": tool_result.ok,
                "error_code": tool_result.error_code,
                "error_message": tool_result.error_message,
                "missing_permissions": tool_result.missing_permissions,
            }
        result = {
            "type": "function_call_output",
            "tool_name": str(tool_result.tool_name),
            "output": json.dumps(payload, ensure_ascii=False, sort_keys=True),
        }
        call_id = str(requested_call.get("call_id") or "").strip()
        if call_id:
            result["call_id"] = call_id
        return result

    @staticmethod
    def _unknown_provider_tool_output(
        *,
        requested_call: dict[str, Any],
        provider_tool_name: str,
    ) -> dict[str, Any]:
        result = {
            "type": "function_call_output",
            "tool_name": "assistant.unknown_provider_tool_name",
            "output": json.dumps(
                {
                    "ok": False,
                    "error_code": "assistant.tool.unknown_provider_tool_name",
                    "error_message": "Unknown provider tool alias requested.",
                    "provider_tool_name": provider_tool_name,
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
        }
        call_id = str(requested_call.get("call_id") or "").strip()
        if call_id:
            result["call_id"] = call_id
        return result

    @staticmethod
    def _resolve_internal_tool_name(
        *,
        provider_tool_name: str,
        provider_tool_name_map: dict[str, str],
    ) -> str | None:
        return provider_tool_name_map.get(provider_tool_name)

    @staticmethod
    def _build_refusal_provider_payload(
        classification: AssistantClassificationResult,
        answer: str,
    ) -> dict[str, Any]:
        return {
            "answer": answer,
            "confidence": classification.confidence,
            "out_of_scope": True,
            "diagnosis": [],
            "links": [],
            "missing_permissions": [],
            "next_steps": [],
            "tool_trace_id": None,
        }

    @staticmethod
    def _serialize_classification(
        classification: AssistantClassificationResult,
    ) -> dict[str, str | bool]:
        return {
            "category": classification.category.value,
            "is_platform_related": classification.is_platform_related,
            "is_out_of_scope": classification.is_out_of_scope,
            "is_unsafe": classification.is_unsafe,
            "reason": classification.reason,
            "confidence": classification.confidence,
        }

    @staticmethod
    def _infer_scope(actor: RequestAuthorizationContext) -> AssistantScope:
        if actor.is_platform_admin and not actor.tenant_id:
            return AssistantScope.PLATFORM
        if actor.tenant_id:
            return AssistantScope.TENANT
        return AssistantScope.UNKNOWN

    def _build_tool_execution_context(
        self,
        *,
        actor: RequestAuthorizationContext,
        conversation_id: str | None,
        message_id: str | None,
    ) -> AssistantToolExecutionContext:
        return AssistantToolExecutionContext(
            auth_context=actor,
            tenant_id=actor.tenant_id,
            user_id=actor.user_id,
            role_keys=actor.role_keys,
            permission_keys=actor.permission_keys,
            scope_kind=self._infer_scope_kind(actor),
            conversation_id=conversation_id,
            message_id=message_id,
            request_id=actor.request_id,
        )

    @staticmethod
    def _infer_scope_kind(actor: RequestAuthorizationContext) -> str:
        if actor.is_platform_admin and not actor.tenant_id:
            return "platform"
        if any(scope.scope_type == "branch" for scope in actor.scopes):
            return "branch"
        if any(scope.scope_type == "mandate" for scope in actor.scopes):
            return "mandate"
        if any(scope.scope_type == "customer" for scope in actor.scopes):
            return "customer"
        if any(scope.scope_type == "subcontractor" for scope in actor.scopes):
            return "subcontractor"
        if "employee_user" in actor.role_keys:
            return "employee_self_service"
        if actor.tenant_id:
            return "tenant"
        return "unknown"
