from __future__ import annotations

import unittest

from sqlalchemy import CheckConstraint, Index, UniqueConstraint

from app.db import Base
from app.modules.assistant.models import (
    AssistantConversation,
    AssistantFeedback,
    AssistantKnowledgeChunk,
    AssistantKnowledgeSource,
    AssistantMessage,
    AssistantPageHelpManifest,
    AssistantPageRouteCatalog,
    AssistantPromptPolicyVersion,
    AssistantToolCall,
)


class TestAssistantMetadata(unittest.TestCase):
    def test_assistant_tables_are_registered(self) -> None:
        expected_tables = {
            "assistant.conversation",
            "assistant.message",
            "assistant.tool_call",
            "assistant.feedback",
            "assistant.knowledge_source",
            "assistant.knowledge_chunk",
            "assistant.page_route_catalog",
            "assistant.page_help_manifest",
            "assistant.prompt_policy_version",
        }
        self.assertTrue(expected_tables.issubset(set(Base.metadata.tables)))

    def test_assistant_conversation_constraints(self) -> None:
        constraints = {
            constraint.name
            for constraint in AssistantConversation.__table__.constraints
            if isinstance(constraint, CheckConstraint)
        }
        indexes = {
            index.name
            for index in AssistantConversation.__table__.indexes
            if isinstance(index, Index)
        }
        self.assertIn("ck_conversation_assistant_conversation_status_valid", constraints)
        self.assertIn("ix_assistant_conversation_tenant_user_updated", indexes)
        self.assertIn("ix_assistant_conversation_user_status", indexes)

    def test_assistant_message_role_constraints(self) -> None:
        constraints = {
            constraint.name
            for constraint in AssistantMessage.__table__.constraints
            if isinstance(constraint, CheckConstraint)
        }
        indexes = {index.name for index in AssistantMessage.__table__.indexes if isinstance(index, Index)}
        self.assertIn("ck_message_assistant_message_role_valid", constraints)
        self.assertIn("ix_assistant_message_conversation_created", indexes)

    def test_assistant_tool_call_permission_decision_constraints(self) -> None:
        constraints = {
            constraint.name
            for constraint in AssistantToolCall.__table__.constraints
            if isinstance(constraint, CheckConstraint)
        }
        indexes = {index.name for index in AssistantToolCall.__table__.indexes if isinstance(index, Index)}
        self.assertIn("ck_tool_call_assistant_tool_call_permission_decision_valid", constraints)
        self.assertIn("ix_assistant_tool_call_conversation_created", indexes)
        self.assertIn("ix_assistant_tool_call_tenant_user_created", indexes)
        self.assertIn("ix_assistant_tool_call_tool_name_created", indexes)

    def test_assistant_feedback_rating_constraints(self) -> None:
        constraints = {
            constraint.name
            for constraint in AssistantFeedback.__table__.constraints
            if isinstance(constraint, CheckConstraint)
        }
        indexes = {index.name for index in AssistantFeedback.__table__.indexes if isinstance(index, Index)}
        self.assertIn("ck_feedback_assistant_feedback_rating_valid", constraints)
        self.assertIn("ix_assistant_feedback_conversation_message", indexes)
        self.assertIn("ix_assistant_feedback_tenant_user_created", indexes)

    def test_assistant_knowledge_source_unique_path_hash(self) -> None:
        unique_constraints = {
            constraint.name
            for constraint in AssistantKnowledgeSource.__table__.constraints
            if isinstance(constraint, UniqueConstraint)
        }
        indexes = {index.name for index in AssistantKnowledgeSource.__table__.indexes if isinstance(index, Index)}
        self.assertIn("uq_assistant_knowledge_source_path_hash", unique_constraints)
        self.assertIn("ix_assistant_knowledge_source_path_status", indexes)
        self.assertIn("ix_assistant_knowledge_source_type_status", indexes)

    def test_assistant_knowledge_chunk_unique_source_index(self) -> None:
        unique_constraints = {
            constraint.name
            for constraint in AssistantKnowledgeChunk.__table__.constraints
            if isinstance(constraint, UniqueConstraint)
        }
        indexes = {index.name for index in AssistantKnowledgeChunk.__table__.indexes if isinstance(index, Index)}
        self.assertIn("uq_assistant_knowledge_chunk_source_index", unique_constraints)
        self.assertIn("ix_assistant_knowledge_chunk_source_index", indexes)
        self.assertIn("ix_assistant_knowledge_chunk_module_page", indexes)
        self.assertIn("ix_assistant_knowledge_chunk_language", indexes)
        column_names = {column.name for column in AssistantKnowledgeChunk.__table__.columns}
        self.assertIn("content_preview", column_names)
        self.assertIn("workflow_keys", column_names)
        self.assertIn("api_families", column_names)
        self.assertIn("domain_terms", column_names)
        self.assertIn("language_aliases", column_names)

    def test_assistant_knowledge_source_has_source_language(self) -> None:
        column_names = {column.name for column in AssistantKnowledgeSource.__table__.columns}
        self.assertIn("source_language", column_names)

    def test_assistant_page_route_unique_page_path(self) -> None:
        unique_constraints = {
            constraint.name
            for constraint in AssistantPageRouteCatalog.__table__.constraints
            if isinstance(constraint, UniqueConstraint)
        }
        indexes = {index.name for index in AssistantPageRouteCatalog.__table__.indexes if isinstance(index, Index)}
        self.assertIn("uq_assistant_page_route_page_path", unique_constraints)
        self.assertIn("ix_assistant_page_route_catalog_page_active", indexes)
        self.assertIn("ix_assistant_page_route_catalog_module_active", indexes)

    def test_assistant_page_help_manifest_constraints(self) -> None:
        unique_constraints = {
            constraint.name
            for constraint in AssistantPageHelpManifest.__table__.constraints
            if isinstance(constraint, UniqueConstraint)
        }
        constraints = {
            constraint.name
            for constraint in AssistantPageHelpManifest.__table__.constraints
            if isinstance(constraint, CheckConstraint)
        }
        indexes = {index.name for index in AssistantPageHelpManifest.__table__.indexes if isinstance(index, Index)}
        self.assertIn("uq_assistant_page_help_manifest_page_lang_version", unique_constraints)
        self.assertIn("ck_page_help_manifest_assistant_page_help_manifest_status_valid", constraints)
        self.assertIn("ix_assistant_page_help_manifest_page_active", indexes)
        self.assertIn("ix_assistant_page_help_manifest_module", indexes)

    def test_assistant_prompt_policy_unique_key_version(self) -> None:
        unique_constraints = {
            constraint.name
            for constraint in AssistantPromptPolicyVersion.__table__.constraints
            if isinstance(constraint, UniqueConstraint)
        }
        indexes = {index.name for index in AssistantPromptPolicyVersion.__table__.indexes if isinstance(index, Index)}
        self.assertIn("uq_assistant_prompt_policy_key_version", unique_constraints)
        self.assertIn("ix_assistant_prompt_policy_key_active", indexes)


if __name__ == "__main__":
    unittest.main()
