"""Assistant permission keys and policy helpers."""

from __future__ import annotations

from app.modules.iam.authz import RequestAuthorizationContext


ASSISTANT_CHAT_ACCESS = "assistant.chat.access"
ASSISTANT_DIAGNOSTICS_READ = "assistant.diagnostics.read"
ASSISTANT_FEEDBACK_WRITE = "assistant.feedback.write"
ASSISTANT_KNOWLEDGE_READ = "assistant.knowledge.read"
ASSISTANT_KNOWLEDGE_REINDEX = "assistant.knowledge.reindex"
ASSISTANT_ADMIN = "assistant.admin"


def can_user_chat(context: RequestAuthorizationContext) -> bool:
    return context.has_permission(ASSISTANT_CHAT_ACCESS)


def can_user_run_diagnostics(context: RequestAuthorizationContext) -> bool:
    return context.has_permission(ASSISTANT_DIAGNOSTICS_READ)


def can_user_submit_feedback(context: RequestAuthorizationContext) -> bool:
    return context.has_permission(ASSISTANT_FEEDBACK_WRITE)


def can_user_use_knowledge(context: RequestAuthorizationContext) -> bool:
    return context.has_permission(ASSISTANT_KNOWLEDGE_READ)


def can_user_reindex_knowledge(context: RequestAuthorizationContext) -> bool:
    return context.has_permission(ASSISTANT_KNOWLEDGE_REINDEX)


def can_user_receive_navigation_links(context: RequestAuthorizationContext) -> bool:
    return can_user_chat(context)
