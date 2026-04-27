from __future__ import annotations

from app.modules.assistant.schemas import AssistantMessageCreate
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext
from tests.modules.assistant.test_how_to_employee_create_exact_ui import (
    _GroundedCapturingProvider,
    _context,
    _repository,
    _service,
)


def _admin_context() -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="assistant-admin-session",
        user_id="assistant-admin",
        tenant_id="tenant-1",
        role_keys=frozenset({"platform_admin"}),
        permission_keys=frozenset({"assistant.admin"}),
        scopes=(AuthenticatedRoleScope(role_key="platform_admin", scope_type="platform"),),
        request_id="assistant-admin-req",
    )


def test_rag_debug_snapshot_returns_quality_gate_and_grounding_details() -> None:
    repository = _repository()
    provider = _GroundedCapturingProvider(answer="Verifizierte Workflow-Hinweise zeigen auf den Kunden-Workspace.")
    service = _service(repository, provider, provider_mode="openai")
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale="de",
        last_route_name=None,
        last_route_path=None,
    )
    response = service.add_message(
        conversation.id,
        AssistantMessageCreate(message="Bitte erklären Sie mir genau, wie ich einen Kunden registrieren kann."),
        _context("assistant.chat.access", "customers.customer.read"),
    )

    snapshot = service.get_rag_debug_snapshot(
        conversation_id=conversation.id,
        message_id=response.message_id,
        actor=_admin_context(),
    )

    assert snapshot.question == "Bitte erklären Sie mir genau, wie ich einen Kunden registrieren kann."
    assert snapshot.classification["reason"] == "workflow_intent:customer_create"
    assert snapshot.retrieval_plan["workflow_intent"] == "customer_create"
    assert snapshot.content_bearing_source_count > 0
    assert snapshot.provider_called is True
    assert snapshot.grounding_sent_to_provider is True
    assert snapshot.source_basis_returned
    assert snapshot.quality_gate.passed is True
