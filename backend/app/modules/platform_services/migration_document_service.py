"""Pilot migration document import and deterministic badge/code outputs."""

from __future__ import annotations

import base64
import hashlib
from typing import Protocol

from app.errors import ApiException
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.platform_services.docs_schemas import DocumentCreate, DocumentLinkCreate, DocumentVersionCreate
from app.modules.platform_services.docs_service import DocumentService
from app.modules.platform_services.migration_schemas import (
    BarcodeOutputRead,
    BarcodeOutputRequest,
    HistoricalDocumentImportRequest,
    HistoricalDocumentImportResult,
    HistoricalDocumentImportRowResult,
    MigrationPreflightRowIssue,
)


class MigrationDocumentRepository(Protocol):
    SUPPORTED_OWNER_TYPES: frozenset[str]

    def find_document_by_source_reference(
        self,
        tenant_id: str,
        *,
        source_module: str,
        source_label: str,
    ): ...  # noqa: ANN001


class MigrationDocumentPilotService:
    def __init__(self, *, document_service: DocumentService, repository: MigrationDocumentRepository) -> None:
        self.document_service = document_service
        self.repository = repository

    def import_historical_documents(
        self,
        tenant_id: str,
        payload: HistoricalDocumentImportRequest,
        actor: RequestAuthorizationContext,
    ) -> HistoricalDocumentImportResult:
        rows: list[HistoricalDocumentImportRowResult] = []
        imported = 0
        seen_manifest_keys: set[str] = set()
        for entry in payload.entries:
            issues: list[MigrationPreflightRowIssue] = []
            if entry.manifest_row_key in seen_manifest_keys:
                issues.append(MigrationPreflightRowIssue(code="duplicate_manifest_key", message="Manifestschluessel ist doppelt."))
            else:
                seen_manifest_keys.add(entry.manifest_row_key)
            if not entry.content_base64:
                issues.append(MigrationPreflightRowIssue(code="missing_file_content", message="Pilotimport erwartet Base64-Dateiinhalt."))
            if entry.owner_type not in self.repository.SUPPORTED_OWNER_TYPES:
                issues.append(MigrationPreflightRowIssue(code="unsupported_owner_type", message="Owner-Typ wird vom Docs-Backbone nicht unterstuetzt."))
            source_label = self._source_label(entry.source_system, entry.legacy_document_id)
            if self.repository.find_document_by_source_reference(
                tenant_id,
                source_module="migration_import",
                source_label=source_label,
            ) is not None:
                issues.append(MigrationPreflightRowIssue(code="duplicate_manifest_reference", message="Legacy-Dokument wurde bereits importiert."))
            if issues:
                rows.append(HistoricalDocumentImportRowResult(manifest_row_key=entry.manifest_row_key, status="invalid", issues=issues))
                continue
            content = self._decode(entry.content_base64)
            checksum = hashlib.sha256(content).hexdigest()
            if checksum != entry.checksum_sha256:
                rows.append(
                    HistoricalDocumentImportRowResult(
                        manifest_row_key=entry.manifest_row_key,
                        status="invalid",
                        issues=[MigrationPreflightRowIssue(code="checksum_mismatch", message="Checksumme stimmt nicht mit dem Payload ueberein.")],
                    )
                )
                continue
            try:
                document = self.document_service.create_document(
                    tenant_id,
                    DocumentCreate(
                        tenant_id=tenant_id,
                        title=entry.title,
                        document_type_key=entry.document_type_key,
                        source_module="migration_import",
                        source_label=source_label,
                        metadata_json={
                            "migration": {
                                "manifest_row_key": entry.manifest_row_key,
                                "source_system": entry.source_system,
                                "legacy_document_id": entry.legacy_document_id,
                                "source_file_name": entry.source_file_name,
                                "source_created_at": entry.source_created_at,
                                "visibility_scope_code": entry.visibility_scope_code,
                            },
                            **entry.metadata_json,
                        },
                    ),
                    actor,
                )
                self.document_service.add_document_version(
                    tenant_id,
                    document.id,
                    DocumentVersionCreate(
                        file_name=entry.source_file_name,
                        content_type=entry.content_type,
                        content_base64=entry.content_base64,
                        metadata_json={
                            "migration": {
                                "checksum_sha256": entry.checksum_sha256,
                                "source_file_name": entry.source_file_name,
                            }
                        },
                    ),
                    actor,
                )
                self.document_service.add_document_link(
                    tenant_id,
                    document.id,
                    DocumentLinkCreate(
                        owner_type=entry.owner_type,
                        owner_id=entry.owner_id,
                        relation_type=entry.relation_type,
                        label=entry.title,
                        metadata_json={"migration_manifest_row_key": entry.manifest_row_key},
                    ),
                    actor,
                )
            except ApiException as exc:
                rows.append(
                    HistoricalDocumentImportRowResult(
                        manifest_row_key=entry.manifest_row_key,
                        status="invalid",
                        issues=[MigrationPreflightRowIssue(code=exc.code, message=exc.message_key)],
                    )
                )
                continue
            rows.append(HistoricalDocumentImportRowResult(manifest_row_key=entry.manifest_row_key, status="imported", document_id=document.id))
            imported += 1
        invalid = sum(1 for row in rows if row.status == "invalid")
        return HistoricalDocumentImportResult(tenant_id=tenant_id, imported_count=imported, invalid_count=invalid, rows=rows)

    def generate_barcode_output(
        self,
        tenant_id: str,
        payload: BarcodeOutputRequest,
        actor: RequestAuthorizationContext,
    ) -> BarcodeOutputRead:
        if payload.owner_type not in self.repository.SUPPORTED_OWNER_TYPES:
            raise ApiException(400, "docs.document_link.unsupported_owner_type", "errors.docs.document_link.unsupported_owner_type")
        payload_text = self._build_payload_text(payload)
        encoded_content = base64.b64encode(payload_text.encode("utf-8")).decode("ascii")
        document = self.document_service.create_document(
            tenant_id,
            DocumentCreate(
                tenant_id=tenant_id,
                title=payload.title,
                document_type_key=payload.document_type_key,
                source_module="generated_output",
                source_label=f"{payload.output_kind}:{payload.owner_type}",
                metadata_json={
                    "generated_output": {
                        "output_kind": payload.output_kind,
                        "payload_format": "SP|1",
                    }
                },
            ),
            actor,
        )
        version = self.document_service.add_document_version(
            tenant_id,
            document.id,
            DocumentVersionCreate(
                file_name=f"{payload.output_kind}-{payload.owner_id}.txt",
                content_type="text/plain",
                content_base64=encoded_content,
                metadata_json={"generated_output": {"payload_text": payload_text}},
            ),
            actor,
        )
        self.document_service.add_document_link(
            tenant_id,
            document.id,
            DocumentLinkCreate(
                owner_type=payload.owner_type,
                owner_id=payload.owner_id,
                relation_type=payload.relation_type,
                label=payload.title,
                metadata_json={"output_kind": payload.output_kind},
            ),
            actor,
        )
        return BarcodeOutputRead(
            tenant_id=tenant_id,
            document_id=document.id,
            version_no=version.version_no,
            owner_type=payload.owner_type,
            owner_id=payload.owner_id,
            output_kind=payload.output_kind,
            payload_text=payload_text,
            file_name=version.file_name,
        )

    @staticmethod
    def _source_label(source_system: str, legacy_document_id: str) -> str:
        return f"historical:{source_system}:{legacy_document_id}"

    @staticmethod
    def _decode(encoded: str) -> bytes:
        try:
            return base64.b64decode(encoded, validate=True)
        except Exception as exc:  # noqa: BLE001
            raise ApiException(400, "docs.document_version.invalid_content", "errors.docs.document_version.invalid_content") from exc

    @staticmethod
    def _build_payload_text(payload: BarcodeOutputRequest) -> str:
        allowed_fields = tuple(sorted(f"{key}={value}" for key, value in payload.payload_fields.items()))
        joined = "|".join(allowed_fields)
        return f"SP|1|{payload.output_kind}|{payload.owner_type}|{payload.owner_id}|{joined}"
