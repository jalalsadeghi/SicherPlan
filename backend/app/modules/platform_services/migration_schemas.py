"""Schemas for trial migration templates, preflight validation, and historical docs."""

from __future__ import annotations

from pydantic import BaseModel, Field


class MigrationFieldDictionaryItem(BaseModel):
    field_name: str
    required: bool
    description: str
    business_key: bool = False
    lookup_domain: str | None = None
    foreign_sheet: str | None = None


class MigrationTemplateSheetRead(BaseModel):
    sheet_key: str
    business_key_field: str
    match_actions: tuple[str, ...]
    load_order: int
    field_dictionary: list[MigrationFieldDictionaryItem]
    example_rows: list[dict[str, object]] = Field(default_factory=list)


class MigrationTemplatePackageRead(BaseModel):
    package_version: str
    sheets: list[MigrationTemplateSheetRead]
    load_order: list[str]
    document_manifest_notes: list[str] = Field(default_factory=list)


class MigrationSheetPayload(BaseModel):
    sheet_key: str
    rows: list[dict[str, object]] = Field(default_factory=list)


class MigrationPreflightRequest(BaseModel):
    tenant_id: str
    package_version: str = "v1"
    sheets: list[MigrationSheetPayload] = Field(default_factory=list)


class MigrationPreflightRowIssue(BaseModel):
    severity: str = "error"
    code: str
    message: str


class MigrationPreflightRowResult(BaseModel):
    sheet_key: str
    row_no: int
    business_key: str | None = None
    status: str
    match_result: str | None = None
    issues: list[MigrationPreflightRowIssue] = Field(default_factory=list)


class MigrationPreflightSummary(BaseModel):
    total_rows: int
    valid_rows: int
    invalid_rows: int
    create_rows: int
    update_rows: int
    conflict_rows: int


class MigrationPreflightResult(BaseModel):
    tenant_id: str
    package_version: str
    summary: MigrationPreflightSummary
    rows: list[MigrationPreflightRowResult] = Field(default_factory=list)


class HistoricalDocumentManifestEntry(BaseModel):
    manifest_row_key: str = Field(min_length=1, max_length=120)
    source_system: str = Field(min_length=1, max_length=80)
    legacy_document_id: str = Field(min_length=1, max_length=120)
    source_file_name: str = Field(min_length=1, max_length=255)
    title: str = Field(min_length=1, max_length=255)
    owner_type: str = Field(min_length=1, max_length=120)
    owner_id: str = Field(min_length=1, max_length=36)
    relation_type: str = Field(default="attachment", min_length=1, max_length=80)
    document_type_key: str | None = Field(default=None, max_length=120)
    visibility_scope_code: str = Field(default="internal", min_length=1, max_length=40)
    checksum_sha256: str = Field(min_length=64, max_length=64)
    content_base64: str | None = None
    content_type: str = Field(default="application/octet-stream", min_length=1, max_length=255)
    source_created_at: str | None = None
    metadata_json: dict[str, object] = Field(default_factory=dict)


class HistoricalDocumentImportRequest(BaseModel):
    tenant_id: str
    entries: list[HistoricalDocumentManifestEntry] = Field(default_factory=list)


class HistoricalDocumentImportRowResult(BaseModel):
    manifest_row_key: str
    status: str
    document_id: str | None = None
    issues: list[MigrationPreflightRowIssue] = Field(default_factory=list)


class HistoricalDocumentImportResult(BaseModel):
    tenant_id: str
    imported_count: int
    invalid_count: int
    rows: list[HistoricalDocumentImportRowResult] = Field(default_factory=list)


class BarcodeOutputRequest(BaseModel):
    tenant_id: str
    owner_type: str
    owner_id: str
    output_kind: str = Field(pattern="^(employee_badge|order_badge)$")
    title: str = Field(min_length=1, max_length=255)
    payload_fields: dict[str, str] = Field(default_factory=dict)
    relation_type: str = Field(default="badge_output", min_length=1, max_length=80)
    document_type_key: str | None = Field(default=None, max_length=120)


class BarcodeOutputRead(BaseModel):
    tenant_id: str
    document_id: str
    version_no: int
    owner_type: str
    owner_id: str
    output_kind: str
    payload_text: str
    file_name: str
