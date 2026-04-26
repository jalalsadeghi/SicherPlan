"""Service layer for assistant capabilities and persistence."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Protocol

from app.errors import ApiException
from app.modules.assistant.classifier import AssistantClassificationResult, classify_assistant_message
from app.modules.assistant.diagnostics import (
    DIAGNOSTIC_TOOL_NAME,
    extract_shift_visibility_input,
    is_shift_visibility_question,
)
from app.modules.assistant.grounding import AssistantGroundingContext, AssistantGroundingSource
from app.modules.assistant.knowledge.retriever import AssistantKnowledgeRetriever
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
from app.modules.assistant.prompt_builder import (
    AssistantMessageContext,
    AssistantToolDefinition as PromptToolDefinition,
    AssistantToolResultSummary,
    build_assistant_prompt,
    summarize_auth_context,
)
from app.modules.assistant.retrieval_planner import build_retrieval_plan
from app.modules.assistant.models import AssistantConversation, AssistantMessage
from app.modules.assistant.provider import (
    AssistantProvider,
    AssistantProviderConfigurationError,
    AssistantProviderRequest,
    AssistantProviderRateLimitError,
    AssistantProviderResult,
    AssistantProviderStructuredOutputError,
    AssistantProviderTimeoutError,
    AssistantProviderUnavailableError,
)
from app.modules.assistant.policy import (
    ASSISTANT_CHAT_ACCESS,
    ASSISTANT_FEEDBACK_WRITE,
    can_user_chat,
    can_user_reindex_knowledge,
    can_user_run_diagnostics,
    can_user_submit_feedback,
)
from app.modules.assistant.schemas import (
    AssistantCapabilitiesRead,
    AssistantClientContextInput,
    AssistantConfidence,
    AssistantConversationCreate,
    AssistantConversationRead,
    AssistantFeedbackCreate,
    AssistantFeedbackRead,
    AssistantKnowledgeChunkResult,
    AssistantMessageCreate,
    AssistantPageHelpManifestRead,
    AssistantProviderStructuredOutput,
    AssistantStructuredResponse,
    AssistantRouteContextInput,
    AssistantScope,
    AssistantMissingPermission,
)
from app.modules.assistant.tools import AssistantToolExecutionContext, AssistantToolRegistry
from app.modules.assistant.workflow_help import detect_workflow_intent
from app.modules.iam.authz import RequestAuthorizationContext


@dataclass(frozen=True)
class AssistantRuntimeConfig:
    enabled: bool
    provider_mode: str
    max_input_chars: int = 12000
    max_tool_calls: int = 8
    max_context_chunks: int = 8


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
                can_chat=False,
                can_run_diagnostics=False,
                can_reindex_knowledge=False,
                supported_features=[],
            )

        can_chat_value = can_user_chat(context)
        can_run_diagnostics_value = can_user_run_diagnostics(context)
        can_reindex_value = can_user_reindex_knowledge(context)

        features = [
            "same_language_response",
            "structured_responses",
            "out_of_scope_policy",
        ]
        if self.runtime_config.provider_mode == "mock":
            features.append("mock_provider")
            features.append("mock_provider_ready")
        elif self.runtime_config.provider_mode == "openai":
            features.append("openai_provider_configured")

        return AssistantCapabilitiesRead(
            enabled=True,
            provider_mode=self.runtime_config.provider_mode,
            can_chat=can_chat_value,
            can_run_diagnostics=can_run_diagnostics_value,
            can_reindex_knowledge=can_reindex_value,
            supported_features=features,
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
        else:
            grounding_context, initial_tool_results = self._build_grounding_context(
                conversation=conversation,
                cleaned_message=cleaned_message,
                route_context=route_context,
                detected_language=detected_language,
                response_language=response_language,
                actor=actor,
            )
            assistant_result_payload = self._generate_in_scope_response(
                conversation=conversation,
                cleaned_message=cleaned_message,
                route_context=route_context,
                detected_language=detected_language,
                response_language=response_language,
                actor=actor,
                grounding_context=grounding_context,
                initial_tool_results=initial_tool_results,
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
        )
        assistant_message.structured_payload = structured_response.model_dump(mode="json")
        assistant_message.structured_payload["classification"] = self._serialize_classification(classification)
        self.repository.update_message_payload(
            assistant_message,
            structured_payload=assistant_message.structured_payload,
        )
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
    ) -> AssistantStructuredResponse:
        return AssistantStructuredResponse(
            conversation_id=conversation.id,
            message_id=assistant_message.id,
            detected_language=detected_language,
            response_language=response_language,
            answer=str(provider_payload.get("answer", "")),
            scope=self._infer_scope(actor),
            confidence=AssistantConfidence(
                str(provider_payload.get("confidence", classification.confidence))
            ),
            out_of_scope=bool(provider_payload.get("out_of_scope", classification.is_out_of_scope)),
            diagnosis=provider_payload.get("diagnosis", []),
            links=provider_payload.get("links", []),
            missing_permissions=provider_payload.get("missing_permissions", []),
            next_steps=provider_payload.get("next_steps", []),
            tool_trace_id=provider_payload.get("tool_trace_id"),
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
        auth_summary = summarize_auth_context(actor)
        knowledge_chunks = self._retrieve_knowledge_chunks(
            query=cleaned_message,
            response_language=response_language,
            route_context=route_context,
            actor=actor,
            planned_page_ids=list(plan.likely_page_ids),
            planned_module_keys=list(plan.likely_module_keys),
        )

        sources: list[AssistantGroundingSource] = []
        missing_context: list[str] = []
        if route_context:
            sources.append(
                AssistantGroundingSource(
                    source_type="current_route",
                    source_name="current_route",
                    page_id=route_context.get("page_id"),
                    module_key=str(route_context.get("page_id") or "")[:1] or None,
                    title=route_context.get("route_name"),
                    content=route_context.get("path"),
                    facts=route_context,
                    relevance_score=1.0,
                    verified=False,
                    permission_checked=True,
                )
            )

        for chunk in knowledge_chunks:
            sources.append(
                AssistantGroundingSource(
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
                    },
                    relevance_score=chunk.score,
                    verified=True,
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
                        "intent": workflow_intent.intent,
                        "language_code": response_language,
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

            if is_shift_visibility_question(cleaned_message, route_context):
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
            sources=sources[:20],
            missing_context=missing_context,
            missing_permissions=self._collect_missing_permissions_from_summaries(summaries),
        )
        return grounding_context, summaries

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
        )

        while True:
            provider_result = self._call_provider(request)
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
                )
                provider_result = self._call_provider(request)
                return self._merge_provider_payload_with_tool_results(
                    provider_result.final_response,
                    tool_results,
                )

            executed_any = False
            for requested_call in requested_tool_calls[:remaining_tool_calls]:
                tool_name = str(requested_call.get("name") or "").strip()
                if not tool_name:
                    continue
                arguments = self._parse_tool_call_arguments(requested_call.get("arguments"))
                tool_result = self.execute_registered_tool(
                    tool_name=tool_name,
                    input_data=arguments,
                    actor=actor,
                    conversation_id=conversation.id,
                )
                tool_results.append(self._tool_result_to_summary(tool_result))
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
        available_tools: list[dict[str, Any]] | None = None,
    ) -> AssistantProviderRequest:
        recent_messages = [
            AssistantMessageContext(
                role=message.role,
                content=message.content,
                detected_language=message.detected_language,
                response_language=message.response_language,
            )
            for message in self.repository.list_messages_for_conversation(conversation.id)[-10:]
        ]
        knowledge_chunks = self._retrieve_knowledge_chunks(
            query=cleaned_message,
            response_language=response_language,
            route_context=route_context,
            actor=actor,
            planned_page_ids=list(grounding_context.retrieval_plan.get("likely_page_ids", [])),
            planned_module_keys=list(grounding_context.retrieval_plan.get("likely_module_keys", [])),
        )
        available_tools_payload = available_tools
        if available_tools_payload is None:
            available_tools_payload = self.list_available_tools(actor=actor, conversation_id=conversation.id)
        prompt_payload = build_assistant_prompt(
            user_message=cleaned_message,
            detected_language=detected_language,
            response_language=response_language,
            auth_context=summarize_auth_context(actor),
            route_context=route_context,
            knowledge_chunks=knowledge_chunks,
            grounding_context=grounding_context,
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
        )
        return AssistantProviderRequest(
            conversation_id=conversation.id,
            user_message=prompt_payload.user_message,
            system_instructions=prompt_payload.system_instructions,
            response_language=response_language,
            detected_language=detected_language,
            route_context=route_context,
            recent_messages=prompt_payload.conversation_messages,
            knowledge_chunks=[item.model_dump(mode="json") for item in knowledge_chunks],
            grounding_context=grounding_context.model_dump(mode="json"),
            tool_results=[{"tool_name": item.tool_name, "summary": item.summary} for item in (tool_results or [])],
            available_tools=available_tools_payload,
            max_tool_calls=self.runtime_config.max_tool_calls,
            max_input_chars=self.runtime_config.max_input_chars,
            metadata={
                "request_id": actor.request_id,
                "provider_mode": self.runtime_config.provider_mode,
                **prompt_payload.metadata,
            },
        )

    def _retrieve_knowledge_chunks(
        self,
        *,
        query: str,
        response_language: str,
        route_context: dict[str, Any] | None,
        actor: RequestAuthorizationContext,
        planned_page_ids: list[str] | None = None,
        planned_module_keys: list[str] | None = None,
    ) -> list[AssistantKnowledgeChunkResult]:
        if self.knowledge_retriever is None:
            return []
        page_id = None
        if route_context is not None:
            page_id = route_context.get("page_id")
        if page_id is None and planned_page_ids:
            page_id = planned_page_ids[0]
        module_key = planned_module_keys[0] if planned_module_keys else None
        results = self.knowledge_retriever.retrieve_knowledge_chunks(
            query=query,
            language_code=response_language,
            module_key=module_key if isinstance(module_key, str) else None,
            page_id=page_id if isinstance(page_id, str) else None,
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
            for fact in payload.get("facts", []) or []:
                if not isinstance(fact, dict):
                    continue
                sources.append(
                    AssistantGroundingSource(
                        source_type="workflow",
                        source_name=payload.get("intent"),
                        page_id=fact.get("page_id"),
                        title=fact.get("title"),
                        content=fact.get("detail"),
                        facts=fact,
                        verified=bool(fact.get("verified", False)),
                        permission_checked=True,
                    )
                )
            return sources

        if source_type == "ui_action":
            sources.append(
                AssistantGroundingSource(
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

    def _call_provider(self, request: AssistantProviderRequest) -> AssistantProviderResult:
        try:
            result = self.provider.generate(request)
        except AssistantProviderConfigurationError as exc:
            raise ApiException(
                503,
                "assistant.provider.unavailable",
                "errors.assistant.provider.unavailable",
            ) from exc
        except AssistantProviderTimeoutError as exc:
            raise ApiException(
                504,
                "assistant.provider.timeout",
                "errors.assistant.provider.timeout",
            ) from exc
        except AssistantProviderRateLimitError as exc:
            raise ApiException(
                503,
                "assistant.provider.rate_limited",
                "errors.assistant.provider.rate_limited",
            ) from exc
        except AssistantProviderUnavailableError as exc:
            raise ApiException(
                503,
                "assistant.provider.unavailable",
                "errors.assistant.provider.unavailable",
            ) from exc
        except AssistantProviderStructuredOutputError as exc:
            raise ApiException(
                502,
                "assistant.provider.invalid_response",
                "errors.assistant.provider.invalid_response",
            ) from exc

        if not isinstance(result.final_response, dict):
            raise ApiException(
                502,
                "assistant.provider.invalid_response",
                "errors.assistant.provider.invalid_response",
            )
        try:
            validated = AssistantProviderStructuredOutput.model_validate(result.final_response)
        except Exception as exc:
            raise ApiException(
                502,
                "assistant.provider.invalid_response",
                "errors.assistant.provider.invalid_response",
            ) from exc
        return AssistantProviderResult(
            final_response=validated.model_dump(mode="json"),
            raw_text=result.raw_text,
            requested_tool_calls=result.requested_tool_calls,
            usage=result.usage,
            provider_name=result.provider_name,
            provider_mode=result.provider_mode,
            model_name=result.model_name,
            latency_ms=result.latency_ms,
            finish_reason=result.finish_reason,
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
