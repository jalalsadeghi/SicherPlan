"""HTTP API for assistant capability reporting and persistence."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import get_db_session
from app.modules.assistant.knowledge.repository import AssistantKnowledgeRepository
from app.modules.assistant.knowledge.retriever import AssistantKnowledgeRetriever
from app.modules.assistant.page_catalog_seed import seed_assistant_page_route_catalog
from app.modules.assistant.page_help_seed import seed_assistant_page_help_manifest
from app.modules.assistant.provider import build_assistant_provider
from app.modules.assistant.repository import SqlAlchemyAssistantRepository
from app.modules.assistant.schemas import (
    AssistantCapabilitiesRead,
    AssistantConversationCreate,
    AssistantConversationRead,
    AssistantFeedbackCreate,
    AssistantFeedbackRead,
    AssistantPageHelpManifestRead,
    AssistantMessageCreate,
    AssistantProviderStatusRead,
    AssistantProviderSmokeTestRead,
    AssistantRagDebugSnapshotRead,
    AssistantStructuredResponse,
)
from app.modules.assistant.service import AssistantRuntimeConfig, AssistantService
from app.modules.assistant.tools import build_default_tool_registry
from app.modules.employees.repository import SqlAlchemyEmployeeRepository
from app.modules.iam.authz import RequestAuthorizationContext, get_request_authorization_context
from app.modules.planning.repository import SqlAlchemyPlanningRepository


router = APIRouter(prefix="/api/assistant", tags=["assistant"])


def get_assistant_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> AssistantService:
    repository = SqlAlchemyAssistantRepository(session)
    employee_repository = SqlAlchemyEmployeeRepository(session)
    planning_repository = SqlAlchemyPlanningRepository(session)
    seed_assistant_page_route_catalog(session)
    seed_assistant_page_help_manifest(session)
    return AssistantService(
        runtime_config=AssistantRuntimeConfig(
            enabled=settings.ai_enabled,
            provider_mode=settings.ai_provider,
            env=settings.env,
            openai_configured=settings.ai_openai_configured,
            mock_provider_allowed=settings.ai_mock_provider_allowed,
            response_model=settings.ai_response_model,
            store_responses=settings.ai_store_responses,
            retrieval_mode=settings.ai_effective_retrieval_mode,
            retrieval_debug=settings.ai_retrieval_debug,
            max_input_chars=settings.ai_max_input_chars,
            max_provider_input_tokens=settings.ai_max_provider_input_tokens,
            max_continuation_input_tokens=settings.ai_max_continuation_input_tokens,
            max_tool_calls=settings.ai_max_tool_calls,
            max_context_chunks=settings.ai_max_context_chunks,
            max_grounding_sources=settings.ai_max_grounding_sources,
            max_grounding_chars_per_source=settings.ai_max_grounding_chars_per_source,
            max_total_grounding_chars=settings.ai_max_total_grounding_chars,
            max_recent_messages_for_model=settings.ai_max_recent_messages_for_model,
            max_recent_messages_for_continuation=settings.ai_max_recent_messages_for_continuation,
            max_output_tokens=settings.ai_max_output_tokens,
            continuation_max_output_tokens=settings.ai_continuation_max_output_tokens,
            rate_limit_retry_seconds=settings.ai_rate_limit_retry_seconds,
            rate_limit_max_retries=settings.ai_rate_limit_max_retries,
            fallback_response_model=settings.ai_fallback_response_model,
            rag_quality_gate_mode=settings.ai_rag_quality_gate_mode,
        ),
        repository=repository,
        provider=build_assistant_provider(settings),
        knowledge_retriever=AssistantKnowledgeRetriever(
            repository=AssistantKnowledgeRepository(session),
            retrieval_mode=settings.ai_effective_retrieval_mode,
            embeddings_enabled=settings.ai_embeddings_enabled,
            max_context_chunks=settings.ai_max_context_chunks,
            max_input_chars=settings.ai_max_input_chars,
        ),
        tool_registry=build_default_tool_registry(
            audit_repository=repository,
            page_catalog_repository=repository,
            page_help_repository=repository,
            employee_repository=employee_repository,
            planning_repository=planning_repository,
        ),
    )


@router.get("/capabilities", response_model=AssistantCapabilitiesRead)
def assistant_capabilities(
    context: Annotated[RequestAuthorizationContext, Depends(get_request_authorization_context)],
    service: Annotated[AssistantService, Depends(get_assistant_service)],
) -> AssistantCapabilitiesRead:
    return service.get_capabilities(context)


@router.get("/provider/status", response_model=AssistantProviderStatusRead)
def assistant_provider_status(
    context: Annotated[RequestAuthorizationContext, Depends(get_request_authorization_context)],
    service: Annotated[AssistantService, Depends(get_assistant_service)],
) -> AssistantProviderStatusRead:
    return service.get_provider_status(context)


@router.post("/provider/smoke-test", response_model=AssistantProviderSmokeTestRead)
def assistant_provider_smoke_test(
    context: Annotated[RequestAuthorizationContext, Depends(get_request_authorization_context)],
    service: Annotated[AssistantService, Depends(get_assistant_service)],
) -> AssistantProviderSmokeTestRead:
    return service.run_provider_smoke_test(context)


@router.get("/page-help/{page_id}", response_model=AssistantPageHelpManifestRead)
def get_assistant_page_help(
    page_id: str,
    context: Annotated[RequestAuthorizationContext, Depends(get_request_authorization_context)],
    service: Annotated[AssistantService, Depends(get_assistant_service)],
    language_code: str | None = None,
) -> AssistantPageHelpManifestRead:
    return service.get_page_help_manifest(page_id=page_id, language_code=language_code, actor=context)


@router.post("/conversations", response_model=AssistantConversationRead, status_code=status.HTTP_201_CREATED)
def create_assistant_conversation(
    payload: AssistantConversationCreate,
    context: Annotated[RequestAuthorizationContext, Depends(get_request_authorization_context)],
    service: Annotated[AssistantService, Depends(get_assistant_service)],
) -> AssistantConversationRead:
    return service.create_conversation(payload, context)


@router.get("/conversations/{conversation_id}", response_model=AssistantConversationRead)
def get_assistant_conversation(
    conversation_id: UUID,
    context: Annotated[RequestAuthorizationContext, Depends(get_request_authorization_context)],
    service: Annotated[AssistantService, Depends(get_assistant_service)],
) -> AssistantConversationRead:
    return service.get_conversation(str(conversation_id), context)


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=AssistantStructuredResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_assistant_message(
    conversation_id: UUID,
    payload: AssistantMessageCreate,
    context: Annotated[RequestAuthorizationContext, Depends(get_request_authorization_context)],
    service: Annotated[AssistantService, Depends(get_assistant_service)],
) -> AssistantStructuredResponse:
    return service.add_message(str(conversation_id), payload, context)


@router.get(
    "/conversations/{conversation_id}/messages/{message_id}/rag-debug",
    response_model=AssistantRagDebugSnapshotRead,
)
def get_assistant_rag_debug_snapshot(
    conversation_id: UUID,
    message_id: UUID,
    context: Annotated[RequestAuthorizationContext, Depends(get_request_authorization_context)],
    service: Annotated[AssistantService, Depends(get_assistant_service)],
) -> AssistantRagDebugSnapshotRead:
    return service.get_rag_debug_snapshot(
        conversation_id=str(conversation_id),
        message_id=str(message_id),
        actor=context,
    )


@router.post(
    "/conversations/{conversation_id}/feedback",
    response_model=AssistantFeedbackRead,
)
def submit_assistant_feedback(
    conversation_id: UUID,
    payload: AssistantFeedbackCreate,
    context: Annotated[RequestAuthorizationContext, Depends(get_request_authorization_context)],
    service: Annotated[AssistantService, Depends(get_assistant_service)],
) -> AssistantFeedbackRead:
    return service.submit_feedback(str(conversation_id), payload, context)
