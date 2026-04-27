"""Types and constants for assistant knowledge ingestion."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


SUPPORTED_SOURCE_TYPES = {
    "markdown",
    "text",
    "json",
    "openapi",
    "sprint_doc",
    "engineering_doc",
    "security_doc",
    "runbook",
    "api_export",
    "repository_docs",
    "manual",
    "page_route_catalog",
    "page_help_manifest",
    "workflow_help",
    "ui_action_catalog",
    "api_endpoint_map",
    "role_page_coverage",
    "operational_handbook",
    "user_manual",
    "implementation_data_model",
}

DEFERRED_SOURCE_TYPES = {"pdf", "xlsx"}

DEFAULT_MAX_FILE_SIZE_BYTES = 512_000
DEFAULT_MAX_CHUNK_CHARS = 5_500
DEFAULT_MIN_CHUNK_CHARS = 2_400
DEFAULT_CHUNK_OVERLAP_CHARS = 700

PAGE_ID_TO_MODULE_KEY = {
    "F-02": "dashboard",
    "PS-01": "platform_services",
    "C-01": "customers",
    "E-01": "employees",
    "S-01": "subcontractors",
    "P-02": "planning",
    "P-03": "planning",
    "P-04": "planning",
    "P-05": "planning",
    "FD-01": "field_execution",
    "FI-01": "finance_actuals",
    "FI-02": "finance_billing",
    "FI-03": "finance_payroll",
    "FI-04": "finance_subcontractor_invoice_checks",
    "REP-01": "reporting",
    "ES-01": "employee_self_service",
    "CP-01": "customer_portal",
    "SP-01": "subcontractor_portal",
}


class AssistantKnowledgeError(RuntimeError):
    """Base knowledge-ingestion error."""


class KnowledgeSourceNotAllowedError(AssistantKnowledgeError):
    """Source path is not allowed for ingestion."""


class KnowledgeSourceTooLargeError(AssistantKnowledgeError):
    """Source exceeds configured max size."""


class UnsupportedKnowledgeSourceError(AssistantKnowledgeError):
    """Source type or file type is not implemented."""


@dataclass(frozen=True)
class LoadedKnowledgeSource:
    source_type: str
    source_name: str
    source_path: str
    content: str
    source_hash: str
    source_version: str | None
    language_code: str | None = None


@dataclass(frozen=True)
class ChunkMetadata:
    title: str | None
    language_code: str | None
    module_key: str | None
    page_id: str | None
    content_preview: str | None = None
    workflow_keys: list[str] = field(default_factory=list)
    role_keys: list[str] = field(default_factory=list)
    permission_keys: list[str] = field(default_factory=list)
    api_families: list[str] = field(default_factory=list)
    domain_terms: list[str] = field(default_factory=list)
    language_aliases: list[str] = field(default_factory=list)
    token_count: int | None = None


@dataclass(frozen=True)
class ChunkedKnowledgeDocument:
    chunk_index: int
    title: str | None
    content: str
    metadata: ChunkMetadata


@dataclass(frozen=True)
class KnowledgeChunkCandidate:
    chunk_id: str
    source_id: str
    source_name: str
    source_type: str
    source_path: str
    chunk_index: int
    source_language: str | None
    title: str | None
    content: str
    language_code: str | None
    module_key: str | None
    page_id: str | None
    content_preview: str | None = None
    workflow_keys: list[str] = field(default_factory=list)
    role_keys: list[str] = field(default_factory=list)
    permission_keys: list[str] = field(default_factory=list)
    api_families: list[str] = field(default_factory=list)
    domain_terms: list[str] = field(default_factory=list)
    language_aliases: list[str] = field(default_factory=list)
    token_count: int | None = None


@dataclass(frozen=True)
class KnowledgeSourceRegistration:
    source_type: str
    source_name: str
    source_path: str

    @property
    def path_obj(self) -> Path:
        return Path(self.source_path)
