"""Released planning output generation backed by the shared docs service."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from app.errors import ApiException
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.planning.schemas import PlanningOutputDocumentRead, PlanningOutputGenerateRequest
from app.modules.platform_services.docs_schemas import DocumentCreate, DocumentLinkCreate, DocumentVersionCreate
from app.modules.platform_services.docs_service import DocumentService


class PlanningOutputRepository(Protocol):
    def get_shift(self, tenant_id: str, row_id: str): ...  # noqa: ANN001
    def list_assignments_in_shift(self, tenant_id: str, shift_id: str) -> list[object]: ...
    def list_documents_for_owner(self, tenant_id: str, owner_type: str, owner_id: str) -> list[object]: ...


@dataclass(frozen=True, slots=True)
class _RenderedOutput:
    title: str
    file_name: str
    body: bytes


class PlanningOutputService:
    VARIANT_CODES = frozenset({"deployment_plan", "deployment_protocol"})
    AUDIENCE_CODES = frozenset({"internal", "customer"})

    def __init__(self, repository: PlanningOutputRepository, *, document_service: DocumentService) -> None:
        self.repository = repository
        self.document_service = document_service

    def list_shift_outputs(
        self,
        tenant_id: str,
        shift_id: str,
        actor: RequestAuthorizationContext,
    ) -> list[PlanningOutputDocumentRead]:
        shift = self._require_shift(tenant_id, shift_id)
        documents = self.repository.list_documents_for_owner(tenant_id, "ops.shift", shift.id)
        rows: list[PlanningOutputDocumentRead] = []
        for document in documents:
            metadata = document.metadata_json or {}
            if metadata.get("generated_kind") != "planning_output":
                continue
            version = next((item for item in document.versions if item.version_no == document.current_version_no), None)
            rows.append(
                PlanningOutputDocumentRead(
                    document_id=document.id,
                    owner_type="ops.shift",
                    owner_id=shift.id,
                    variant_code=str(metadata.get("variant_code", "")),
                    audience_code=str(metadata.get("audience_code", "internal")),
                    title=document.title,
                    relation_type="deployment_output",
                    current_version_no=document.current_version_no,
                    file_name=version.file_name if version is not None else f"{document.id}.pdf",
                    content_type=version.content_type if version is not None else "application/pdf",
                    generated_at=version.uploaded_at if version is not None else document.updated_at,
                    is_revision_safe_pdf=bool(version.is_revision_safe_pdf) if version is not None else True,
                )
            )
        return sorted(rows, key=lambda row: (row.variant_code, row.audience_code, row.generated_at), reverse=True)

    def generate_shift_output(
        self,
        tenant_id: str,
        shift_id: str,
        payload: PlanningOutputGenerateRequest,
        actor: RequestAuthorizationContext,
    ) -> PlanningOutputDocumentRead:
        self._ensure_tenant_scope(tenant_id, payload.tenant_id)
        if payload.variant_code not in self.VARIANT_CODES:
            raise ApiException(400, "planning.output.invalid_variant", "errors.planning.output.invalid_variant")
        if payload.audience_code not in self.AUDIENCE_CODES:
            raise ApiException(400, "planning.output.invalid_audience", "errors.planning.output.invalid_audience")
        shift = self._require_shift(tenant_id, shift_id)
        if shift.release_state != "released":
            raise ApiException(409, "planning.output.release_required", "errors.planning.output.release_required")
        rendered = self._render_output(tenant_id, shift, payload)
        existing = next(
            (
                item
                for item in self.list_shift_outputs(tenant_id, shift_id, actor)
                if item.variant_code == payload.variant_code and item.audience_code == payload.audience_code
            ),
            None,
        )
        if existing is not None and not payload.regenerate:
            return existing
        if existing is None:
            document = self.document_service.create_document(
                tenant_id,
                DocumentCreate(
                    tenant_id=tenant_id,
                    title=rendered.title,
                    source_module="planning",
                    source_label="released_output",
                    metadata_json={
                        "generated_kind": "planning_output",
                        "variant_code": payload.variant_code,
                        "audience_code": payload.audience_code,
                        "shift_id": shift.id,
                    },
                ),
                actor,
            )
            self.document_service.add_document_link(
                tenant_id,
                document.id,
                DocumentLinkCreate(owner_type="ops.shift", owner_id=shift.id, relation_type="deployment_output", label=payload.variant_code),
                actor,
            )
            document_id = document.id
        else:
            document_id = existing.document_id
        version = self.document_service.add_document_version(
            tenant_id,
            document_id,
            DocumentVersionCreate(
                file_name=rendered.file_name,
                content_type="application/pdf",
                content_base64=base64.b64encode(rendered.body).decode("ascii"),
                is_revision_safe_pdf=True,
                metadata_json={
                    "generated_kind": "planning_output",
                    "variant_code": payload.variant_code,
                    "audience_code": payload.audience_code,
                    "shift_id": shift.id,
                    "released_at": shift.released_at.isoformat() if shift.released_at is not None else None,
                },
            ),
            actor,
        )
        return PlanningOutputDocumentRead(
            document_id=document_id,
            owner_type="ops.shift",
            owner_id=shift.id,
            variant_code=payload.variant_code,
            audience_code=payload.audience_code,
            title=rendered.title,
            relation_type="deployment_output",
            current_version_no=version.version_no,
            file_name=version.file_name,
            content_type=version.content_type,
            generated_at=version.uploaded_at,
            is_revision_safe_pdf=version.is_revision_safe_pdf,
        )

    def _render_output(self, tenant_id: str, shift, payload: PlanningOutputGenerateRequest) -> _RenderedOutput:  # noqa: ANN001
        planning_record = shift.shift_plan.planning_record
        order = planning_record.order if planning_record is not None else None
        assignments = self.repository.list_assignments_in_shift(tenant_id, shift.id)
        audience_is_customer = payload.audience_code == "customer"
        lines = [
            "%PDF-1.4",
            f"variant={payload.variant_code}",
            f"audience={payload.audience_code}",
            f"shift_id={shift.id}",
            f"planning_record={planning_record.name if planning_record is not None else ''}",
            f"order_no={order.order_no if order is not None else ''}",
            f"shift_type={shift.shift_type_code}",
            f"starts_at={shift.starts_at.isoformat()}",
            f"ends_at={shift.ends_at.isoformat()}",
            f"location={self._redact_value(shift.location_text, audience_is_customer)}",
            f"meeting_point={self._redact_value(shift.meeting_point, audience_is_customer)}",
            "assignments:",
        ]
        for item in sorted(assignments, key=lambda row: row.id):
            actor_label = "name_hidden" if audience_is_customer else self._assignment_actor_label(item)
            lines.append(f"- {actor_label}:{item.assignment_status_code}")
        body = ("\n".join(lines) + "\n%%EOF").encode("utf-8")
        base_name = f"{payload.variant_code}-{shift.starts_at.date().isoformat()}-{shift.id[:8]}"
        return _RenderedOutput(
            title=f"{payload.variant_code}:{planning_record.name if planning_record is not None else shift.shift_type_code}",
            file_name=f"{base_name}.pdf",
            body=body,
        )

    @staticmethod
    def _redact_value(value: str | None, redact: bool) -> str:
        if not value:
            return ""
        return "redacted" if redact else value

    @staticmethod
    def _assignment_actor_label(assignment) -> str:  # noqa: ANN001
        if getattr(assignment, "employee_id", None):
            return f"employee:{assignment.employee_id}"
        if getattr(assignment, "subcontractor_worker_id", None):
            return f"worker:{assignment.subcontractor_worker_id}"
        return "unassigned"

    def _require_shift(self, tenant_id: str, shift_id: str):
        row = self.repository.get_shift(tenant_id, shift_id)
        if row is None:
            raise ApiException(404, "planning.shift.not_found", "errors.planning.shift.not_found")
        return row

    @staticmethod
    def _ensure_tenant_scope(tenant_id: str, payload_tenant_id: str) -> None:
        if tenant_id != payload_tenant_id:
            raise ApiException(400, "planning.shift.scope_mismatch", "errors.planning.shift.scope_mismatch")
