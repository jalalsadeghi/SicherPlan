"""Import tooling for planning operational masters."""

from __future__ import annotations

import base64
import csv
import io
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from typing import Protocol

from app.errors import ApiException
from app.modules.iam.audit_service import AuditActor, AuditService
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.planning.schemas import (
    EquipmentItemCreate,
    EquipmentItemUpdate,
    EventVenueCreate,
    EventVenueUpdate,
    PatrolRouteCreate,
    PatrolRouteUpdate,
    PlanningOpsImportDryRunRequest,
    PlanningOpsImportDryRunResult,
    PlanningOpsImportExecuteRequest,
    PlanningOpsImportExecuteResult,
    PlanningOpsImportRowResult,
    RequirementTypeCreate,
    RequirementTypeUpdate,
    ServiceCategoryCreate,
    ServiceCategoryUpdate,
    SiteCreate,
    SiteUpdate,
    TradeFairCreate,
    TradeFairUpdate,
)
from app.modules.planning.service import PlanningService
from app.modules.platform_services.docs_schemas import DocumentCreate, DocumentLinkCreate, DocumentVersionCreate
from app.modules.platform_services.docs_service import DocumentService
from app.modules.platform_services.integration_models import ImportExportJob


IMPORT_HEADERS = {
    "requirement_type": ("code", "label", "default_planning_mode_code", "notes", "status"),
    "equipment_item": ("code", "label", "unit_of_measure_code", "notes", "status"),
    "service_category": ("code", "label", "sort_order", "notes", "status"),
    "site": ("customer_id", "site_no", "name", "address_id", "timezone", "latitude", "longitude", "watchbook_enabled", "notes", "status"),
    "event_venue": ("customer_id", "venue_no", "name", "address_id", "timezone", "latitude", "longitude", "notes", "status"),
    "trade_fair": ("customer_id", "venue_id", "fair_no", "name", "address_id", "timezone", "latitude", "longitude", "start_date", "end_date", "notes", "status"),
    "patrol_route": ("customer_id", "site_id", "meeting_address_id", "route_no", "name", "start_point_text", "end_point_text", "travel_policy_code", "notes", "status"),
}

LEGACY_IMPORT_HEADERS = {
    "requirement_type": ("code", "label", "default_planning_mode_code", "description", "status"),
    "equipment_item": ("code", "label", "unit_of_measure_code", "description", "status"),
    "service_category": ("code", "label", "sort_order", "description", "status"),
}


@dataclass(slots=True)
class ParsedImportRow:
    row_no: int
    data: dict[str, str]


class PlanningOpsImportRepository(Protocol):
    def create_job(self, row: ImportExportJob) -> ImportExportJob: ...
    def save_job(self, row: ImportExportJob) -> ImportExportJob: ...


class PlanningOpsService:
    def __init__(
        self,
        *,
        planning_service: PlanningService,
        repository: PlanningOpsImportRepository,
        document_service: DocumentService,
        audit_service: AuditService | None = None,
    ) -> None:
        self.planning_service = planning_service
        self.repository = repository
        self.document_service = document_service
        self.audit_service = audit_service

    def import_dry_run(
        self,
        tenant_id: str,
        payload: PlanningOpsImportDryRunRequest,
        actor: RequestAuthorizationContext,
    ) -> PlanningOpsImportDryRunResult:
        self._ensure_tenant(tenant_id, payload.tenant_id)
        rows = self._parse_rows(payload.entity_key, payload.csv_content_base64)
        results = [self._validate_row(tenant_id, payload.entity_key, row, actor) for row in rows]
        invalid_rows = sum(1 for row in results if row.status == "invalid")
        return PlanningOpsImportDryRunResult(
            tenant_id=tenant_id,
            entity_key=payload.entity_key,
            total_rows=len(results),
            valid_rows=len(results) - invalid_rows,
            invalid_rows=invalid_rows,
            rows=results,
        )

    def import_execute(
        self,
        tenant_id: str,
        payload: PlanningOpsImportExecuteRequest,
        actor: RequestAuthorizationContext,
    ) -> PlanningOpsImportExecuteResult:
        self._ensure_tenant(tenant_id, payload.tenant_id)
        rows = self._parse_rows(payload.entity_key, payload.csv_content_base64)
        job = self.repository.create_job(
            ImportExportJob(
                tenant_id=tenant_id,
                endpoint_id=None,
                job_direction="import",
                job_type=f"planning.{payload.entity_key}_csv",
                request_payload_json={"row_count": len(rows), "entity_key": payload.entity_key},
                requested_by_user_id=actor.user_id,
                status="started",
                started_at=datetime.now(UTC),
                created_by_user_id=actor.user_id,
                updated_by_user_id=actor.user_id,
            )
        )
        row_results: list[PlanningOpsImportRowResult] = []
        created_rows = 0
        updated_rows = 0
        for row in rows:
            preview = self._validate_row(tenant_id, payload.entity_key, row, actor)
            if preview.status == "invalid":
                row_results.append(preview)
                if not payload.continue_on_error:
                    break
                continue
            result = self._execute_row(tenant_id, payload.entity_key, row, actor)
            row_results.append(result)
            if "created" in result.messages:
                created_rows += 1
            if "updated" in result.messages:
                updated_rows += 1
        invalid_rows = sum(1 for row in row_results if row.status == "invalid")
        report_document_id = self._create_result_document(
            tenant_id=tenant_id,
            actor=actor,
            owner_id=job.id,
            entity_key=payload.entity_key,
            rows=row_results,
        )
        job.completed_at = datetime.now(UTC)
        job.status = "completed"
        job.result_summary_json = {
            "entity_key": payload.entity_key,
            "total_rows": len(row_results),
            "invalid_rows": invalid_rows,
            "report_document_id": report_document_id,
        }
        job.version_no += 1
        job.updated_by_user_id = actor.user_id
        self.repository.save_job(job)
        return PlanningOpsImportExecuteResult(
            tenant_id=tenant_id,
            entity_key=payload.entity_key,
            job_id=job.id,
            job_status=job.status,
            total_rows=len(row_results),
            invalid_rows=invalid_rows,
            created_rows=created_rows,
            updated_rows=updated_rows,
            result_document_ids=[report_document_id],
            rows=row_results,
        )

    def _ensure_tenant(self, tenant_id: str, payload_tenant_id: str) -> None:
        if tenant_id != payload_tenant_id:
            raise ApiException(400, "planning.import.scope_mismatch", "errors.planning.import.scope_mismatch")

    def _parse_rows(self, entity_key: str, content_base64: str) -> list[ParsedImportRow]:
        headers = IMPORT_HEADERS.get(entity_key)
        if headers is None:
            raise ApiException(400, "planning.import.invalid_entity_key", "errors.planning.import.invalid_entity_key")
        try:
            raw = base64.b64decode(content_base64)
            text = raw.decode("utf-8")
        except (ValueError, UnicodeDecodeError) as exc:
            raise ApiException(400, "planning.import.invalid_csv", "errors.planning.import.invalid_csv") from exc
        reader = csv.DictReader(io.StringIO(text))
        fieldnames = tuple(reader.fieldnames or ())
        accepted_headers = {headers, LEGACY_IMPORT_HEADERS.get(entity_key)}
        accepted_headers.discard(None)
        if fieldnames not in accepted_headers:
            raise ApiException(400, "planning.import.invalid_headers", "errors.planning.import.invalid_headers")
        rows: list[ParsedImportRow] = []
        for index, row in enumerate(reader, start=2):
            normalized = {key: (value or "").strip() for key, value in row.items()}
            if "description" in normalized and "notes" not in normalized:
                normalized["notes"] = normalized["description"]
            rows.append(
                ParsedImportRow(
                    row_no=index,
                    data=normalized,
                )
            )
        return rows

    def _validate_row(
        self,
        tenant_id: str,
        entity_key: str,
        row: ParsedImportRow,
        actor: RequestAuthorizationContext,
    ) -> PlanningOpsImportRowResult:
        try:
            payload = self._build_payload(tenant_id, entity_key, row)
            if entity_key == "equipment_item":
                existing = self.planning_service.repository.find_equipment_item_by_code(tenant_id, payload.code)
                self.planning_service.ensure_equipment_unit_of_measure_code(
                    tenant_id,
                    payload.unit_of_measure_code,
                    current_value=existing.unit_of_measure_code if existing is not None else None,
                )
        except ApiException as exc:
            return PlanningOpsImportRowResult(
                row_no=row.row_no,
                entity_ref=self._row_ref(entity_key, row.data),
                status="invalid",
                messages=[exc.message_key],
            )
        return PlanningOpsImportRowResult(
            row_no=row.row_no,
            entity_ref=self._row_ref(entity_key, row.data),
            status="valid",
            messages=[],
        )

    def _execute_row(
        self,
        tenant_id: str,
        entity_key: str,
        row: ParsedImportRow,
        actor: RequestAuthorizationContext,
    ) -> PlanningOpsImportRowResult:
        payload = self._build_payload(tenant_id, entity_key, row)
        entity_ref = self._row_ref(entity_key, row.data)
        if entity_key == "requirement_type":
            existing = self.planning_service.repository.find_requirement_type_by_code(tenant_id, payload.code)
            if existing is None:
                created = self.planning_service.create_requirement_type(tenant_id, payload, actor)
                return PlanningOpsImportRowResult(row_no=row.row_no, entity_ref=entity_ref, status="applied", messages=["created"], entity_id=created.id)
            updated = self.planning_service.update_requirement_type(
                tenant_id,
                existing.id,
                RequirementTypeUpdate(**payload.model_dump(), version_no=existing.version_no),
                actor,
            )
            return PlanningOpsImportRowResult(row_no=row.row_no, entity_ref=entity_ref, status="applied", messages=["updated"], entity_id=updated.id)
        if entity_key == "equipment_item":
            existing = self.planning_service.repository.find_equipment_item_by_code(tenant_id, payload.code)
            if existing is None:
                created = self.planning_service.create_equipment_item(tenant_id, payload, actor)
                return PlanningOpsImportRowResult(row_no=row.row_no, entity_ref=entity_ref, status="applied", messages=["created"], entity_id=created.id)
            updated = self.planning_service.update_equipment_item(
                tenant_id,
                existing.id,
                EquipmentItemUpdate(**payload.model_dump(), version_no=existing.version_no),
                actor,
            )
            return PlanningOpsImportRowResult(row_no=row.row_no, entity_ref=entity_ref, status="applied", messages=["updated"], entity_id=updated.id)
        if entity_key == "service_category":
            existing = self.planning_service.repository.find_service_category_by_code(tenant_id, payload.code)
            if existing is None:
                created = self.planning_service.create_service_category(tenant_id, payload, actor)
                return PlanningOpsImportRowResult(row_no=row.row_no, entity_ref=entity_ref, status="applied", messages=["created"], entity_id=created.id)
            updated = self.planning_service.update_service_category(
                tenant_id,
                existing.id,
                ServiceCategoryUpdate(**payload.model_dump(), version_no=existing.version_no),
                actor,
            )
            return PlanningOpsImportRowResult(row_no=row.row_no, entity_ref=entity_ref, status="applied", messages=["updated"], entity_id=updated.id)
        if entity_key == "site":
            existing = self.planning_service.repository.find_site_by_no(tenant_id, payload.site_no)
            if existing is None:
                created = self.planning_service.create_site(tenant_id, payload, actor)
                return PlanningOpsImportRowResult(row_no=row.row_no, entity_ref=entity_ref, status="applied", messages=["created"], entity_id=created.id)
            updated = self.planning_service.update_site(
                tenant_id,
                existing.id,
                SiteUpdate(**payload.model_dump(), version_no=existing.version_no),
                actor,
            )
            return PlanningOpsImportRowResult(row_no=row.row_no, entity_ref=entity_ref, status="applied", messages=["updated"], entity_id=updated.id)
        if entity_key == "event_venue":
            existing = self.planning_service.repository.find_event_venue_by_no(tenant_id, payload.venue_no)
            if existing is None:
                created = self.planning_service.create_event_venue(tenant_id, payload, actor)
                return PlanningOpsImportRowResult(row_no=row.row_no, entity_ref=entity_ref, status="applied", messages=["created"], entity_id=created.id)
            updated = self.planning_service.update_event_venue(
                tenant_id,
                existing.id,
                EventVenueUpdate(**payload.model_dump(), version_no=existing.version_no),
                actor,
            )
            return PlanningOpsImportRowResult(row_no=row.row_no, entity_ref=entity_ref, status="applied", messages=["updated"], entity_id=updated.id)
        if entity_key == "trade_fair":
            existing = self.planning_service.repository.find_trade_fair_by_no(tenant_id, payload.fair_no)
            if existing is None:
                created = self.planning_service.create_trade_fair(tenant_id, payload, actor)
                return PlanningOpsImportRowResult(row_no=row.row_no, entity_ref=entity_ref, status="applied", messages=["created"], entity_id=created.id)
            updated = self.planning_service.update_trade_fair(
                tenant_id,
                existing.id,
                TradeFairUpdate(**payload.model_dump(), version_no=existing.version_no),
                actor,
            )
            return PlanningOpsImportRowResult(row_no=row.row_no, entity_ref=entity_ref, status="applied", messages=["updated"], entity_id=updated.id)
        existing = self.planning_service.repository.find_patrol_route_by_no(tenant_id, payload.route_no)
        if existing is None:
            created = self.planning_service.create_patrol_route(tenant_id, payload, actor)
            return PlanningOpsImportRowResult(row_no=row.row_no, entity_ref=entity_ref, status="applied", messages=["created"], entity_id=created.id)
        updated = self.planning_service.update_patrol_route(
            tenant_id,
            existing.id,
            PatrolRouteUpdate(**payload.model_dump(), version_no=existing.version_no),
            actor,
        )
        return PlanningOpsImportRowResult(row_no=row.row_no, entity_ref=entity_ref, status="applied", messages=["updated"], entity_id=updated.id)

    def _build_payload(self, tenant_id: str, entity_key: str, row: ParsedImportRow):
        data = row.data
        if entity_key == "requirement_type":
            return RequirementTypeCreate(
                tenant_id=tenant_id,
                code=self._required(data, "code"),
                label=self._required(data, "label"),
                default_planning_mode_code=self._required(data, "default_planning_mode_code"),
                notes=data.get("notes") or data.get("description") or None,
            )
        if entity_key == "equipment_item":
            return EquipmentItemCreate(
                tenant_id=tenant_id,
                code=self._required(data, "code"),
                label=self._required(data, "label"),
                unit_of_measure_code=self._required(data, "unit_of_measure_code"),
                notes=data.get("notes") or data.get("description") or None,
            )
        if entity_key == "service_category":
            return ServiceCategoryCreate(
                tenant_id=tenant_id,
                code=self._required(data, "code"),
                label=self._required(data, "label"),
                sort_order=int(data.get("sort_order") or 100),
                notes=data.get("notes") or data.get("description") or None,
            )
        if entity_key == "site":
            return SiteCreate(
                tenant_id=tenant_id,
                customer_id=self._required(data, "customer_id"),
                site_no=self._required(data, "site_no"),
                name=self._required(data, "name"),
                address_id=data.get("address_id") or None,
                timezone=data.get("timezone") or None,
                latitude=self._decimal(data.get("latitude")),
                longitude=self._decimal(data.get("longitude")),
                watchbook_enabled=self._bool(data.get("watchbook_enabled")),
                notes=data.get("notes") or None,
            )
        if entity_key == "event_venue":
            return EventVenueCreate(
                tenant_id=tenant_id,
                customer_id=self._required(data, "customer_id"),
                venue_no=self._required(data, "venue_no"),
                name=self._required(data, "name"),
                address_id=data.get("address_id") or None,
                timezone=data.get("timezone") or None,
                latitude=self._decimal(data.get("latitude")),
                longitude=self._decimal(data.get("longitude")),
                notes=data.get("notes") or None,
            )
        if entity_key == "trade_fair":
            return TradeFairCreate(
                tenant_id=tenant_id,
                customer_id=self._required(data, "customer_id"),
                venue_id=data.get("venue_id") or None,
                fair_no=self._required(data, "fair_no"),
                name=self._required(data, "name"),
                address_id=data.get("address_id") or None,
                timezone=data.get("timezone") or None,
                latitude=self._decimal(data.get("latitude")),
                longitude=self._decimal(data.get("longitude")),
                start_date=self._date(self._required(data, "start_date")),
                end_date=self._date(self._required(data, "end_date")),
                notes=data.get("notes") or None,
            )
        if entity_key == "patrol_route":
            return PatrolRouteCreate(
                tenant_id=tenant_id,
                customer_id=self._required(data, "customer_id"),
                site_id=data.get("site_id") or None,
                meeting_address_id=data.get("meeting_address_id") or None,
                route_no=self._required(data, "route_no"),
                name=self._required(data, "name"),
                start_point_text=data.get("start_point_text") or None,
                end_point_text=data.get("end_point_text") or None,
                travel_policy_code=data.get("travel_policy_code") or None,
                notes=data.get("notes") or None,
            )
        raise ApiException(400, "planning.import.invalid_entity_key", "errors.planning.import.invalid_entity_key")

    @staticmethod
    def _required(data: dict[str, str], key: str) -> str:
        value = (data.get(key) or "").strip()
        if not value:
            raise ApiException(400, "planning.import.missing_value", "errors.planning.import.missing_value", {"field": key})
        return value

    @staticmethod
    def _decimal(value: str | None) -> Decimal | None:
        if not value:
            return None
        try:
            return Decimal(value)
        except InvalidOperation as exc:
            raise ApiException(400, "planning.import.invalid_number", "errors.planning.import.invalid_number") from exc

    @staticmethod
    def _date(value: str) -> date:
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise ApiException(400, "planning.import.invalid_date", "errors.planning.import.invalid_date") from exc

    @staticmethod
    def _bool(value: str | None) -> bool:
        if not value:
            return False
        return value.strip().lower() in {"1", "true", "yes", "ja"}

    @staticmethod
    def _row_ref(entity_key: str, data: dict[str, str]) -> str | None:
        ref_fields = {
            "requirement_type": "code",
            "equipment_item": "code",
            "service_category": "code",
            "site": "site_no",
            "event_venue": "venue_no",
            "trade_fair": "fair_no",
            "patrol_route": "route_no",
        }
        field_name = ref_fields.get(entity_key)
        return data.get(field_name, "") or None

    def _create_result_document(
        self,
        *,
        tenant_id: str,
        actor: RequestAuthorizationContext,
        owner_id: str,
        entity_key: str,
        rows: list[PlanningOpsImportRowResult],
    ) -> str:
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(["row_no", "entity_ref", "status", "messages", "entity_id"])
        for row in rows:
            writer.writerow([row.row_no, row.entity_ref or "", row.status, "|".join(row.messages), row.entity_id or ""])
        document = self.document_service.create_document(
            tenant_id,
            DocumentCreate(
                tenant_id=tenant_id,
                title=f"Planning import result {entity_key}",
                source_module="planning",
                source_label=f"planning-{entity_key}-import-result",
            ),
            actor,
        )
        self.document_service.add_document_version(
            tenant_id,
            document.id,
            DocumentVersionCreate(
                file_name=f"planning-{entity_key}-import-result.csv",
                content_type="text/csv",
                content_base64=base64.b64encode(csv_buffer.getvalue().encode("utf-8")).decode("ascii"),
            ),
            actor,
        )
        self.document_service.add_document_link(
            tenant_id,
            document.id,
            DocumentLinkCreate(
                owner_type="integration.import_export_job",
                owner_id=owner_id,
                relation_type="result",
                label=f"{entity_key} import result",
            ),
            actor,
        )
        if self.audit_service is not None:
            self.audit_service.record_business_event(
                actor=AuditActor(
                    tenant_id=tenant_id,
                    user_id=actor.user_id,
                    session_id=actor.session_id,
                    request_id=actor.request_id,
                ),
                event_type="planning.import.executed",
                entity_type="integration.import_export_job",
                entity_id=owner_id,
                tenant_id=tenant_id,
                metadata_json={"entity_key": entity_key, "result_document_id": document.id},
            )
        return document.id
