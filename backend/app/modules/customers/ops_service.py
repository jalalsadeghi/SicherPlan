"""Customer import/export, vCard generation, and history retrieval."""

from __future__ import annotations

import base64
import csv
import io
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from app.errors import ApiException
from app.modules.customers.models import Customer, CustomerAddressLink, CustomerContact, CustomerHistoryEntry
from app.modules.customers.policy import CUSTOMER_PORTAL_PRIVACY_BOUNDARY, enforce_customer_module_access
from app.modules.customers.schemas import (
    CustomerAddressCreate,
    CustomerAddressUpdate,
    CustomerContactCreate,
    CustomerContactRead,
    CustomerContactUpdate,
    CustomerCreate,
    CustomerExportRequest,
    CustomerExportResult,
    CustomerFilter,
    CustomerHistoryEntryRead,
    CustomerImportDryRunRequest,
    CustomerImportDryRunResult,
    CustomerImportExecuteRequest,
    CustomerImportExecuteResult,
    CustomerImportRowResult,
    CustomerRead,
    CustomerUpdate,
    CustomerVCardResult,
)
from app.modules.iam.audit_service import AuditActor, AuditService
from app.modules.customers.service import CustomerService
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.platform_services.docs_schemas import DocumentCreate, DocumentLinkCreate, DocumentVersionCreate
from app.modules.platform_services.docs_service import DocumentService
from app.modules.platform_services.integration_models import ImportExportJob
from app.modules.platform_services.integration_repository import SqlAlchemyIntegrationRepository


IMPORT_HEADERS = (
    "customer_number",
    "name",
    "legal_name",
    "external_ref",
    "default_branch_id",
    "default_mandate_id",
    "classification_lookup_id",
    "ranking_lookup_id",
    "customer_status_lookup_id",
    "contact_full_name",
    "contact_email",
    "contact_phone",
    "contact_mobile",
    "contact_user_id",
    "is_primary_contact",
    "is_billing_contact",
    "address_id",
    "address_type",
    "address_label",
    "is_default_address",
)


class CustomerOpsRepository(Protocol):
    def list_customers(self, tenant_id: str, filters: CustomerFilter) -> list[Customer]: ...
    def find_customer_by_number(self, tenant_id: str, customer_number: str, *, exclude_id: str | None = None) -> Customer | None: ...
    def get_customer(self, tenant_id: str, customer_id: str) -> Customer | None: ...
    def find_contact_by_email(
        self,
        tenant_id: str,
        customer_id: str,
        email: str,
        *,
        exclude_id: str | None = None,
    ) -> CustomerContact | None: ...
    def find_contact_by_name(
        self,
        tenant_id: str,
        customer_id: str,
        full_name: str,
        *,
        exclude_id: str | None = None,
    ) -> CustomerContact | None: ...
    def find_address_link_by_type(
        self,
        tenant_id: str,
        customer_id: str,
        address_type: str,
        *,
        exclude_id: str | None = None,
    ) -> CustomerAddressLink | None: ...
    def list_history_entries(self, tenant_id: str, customer_id: str) -> list[CustomerHistoryEntry]: ...


@dataclass(slots=True)
class ParsedImportRow:
    row_no: int
    data: dict[str, str]


class CustomerOpsService:
    def __init__(
        self,
        *,
        customer_service: CustomerService,
        customer_repository: CustomerOpsRepository,
        integration_repository: SqlAlchemyIntegrationRepository,
        document_service: DocumentService,
        audit_service: AuditService | None = None,
    ) -> None:
        self.customer_service = customer_service
        self.customer_repository = customer_repository
        self.integration_repository = integration_repository
        self.document_service = document_service
        self.audit_service = audit_service

    def import_dry_run(
        self,
        tenant_id: str,
        payload: CustomerImportDryRunRequest,
        actor: RequestAuthorizationContext,
    ) -> CustomerImportDryRunResult:
        self._ensure_tenant_scope(actor, tenant_id)
        self._ensure_payload_tenant(tenant_id, payload.tenant_id)
        parsed_rows = self._parse_import_csv(payload.csv_content_base64)
        results = [self._validate_import_row(tenant_id, row, actor) for row in parsed_rows]
        invalid_rows = sum(1 for row in results if row.status == "invalid")
        self._record_event(
            actor,
            event_type="customers.import.dry_run_requested",
            entity_type="crm.customer_import",
            entity_id=tenant_id,
            tenant_id=tenant_id,
            metadata_json={
                "row_count": len(parsed_rows),
                "invalid_rows": invalid_rows,
                "privacy_boundary": CUSTOMER_PORTAL_PRIVACY_BOUNDARY,
            },
        )
        return CustomerImportDryRunResult(
            tenant_id=tenant_id,
            total_rows=len(results),
            valid_rows=len(results) - invalid_rows,
            invalid_rows=invalid_rows,
            rows=results,
        )

    def execute_import(
        self,
        tenant_id: str,
        payload: CustomerImportExecuteRequest,
        actor: RequestAuthorizationContext,
    ) -> CustomerImportExecuteResult:
        self._ensure_tenant_scope(actor, tenant_id)
        self._ensure_payload_tenant(tenant_id, payload.tenant_id)
        parsed_rows = self._parse_import_csv(payload.csv_content_base64)
        job = self.integration_repository.create_job(
            ImportExportJob(
                tenant_id=tenant_id,
                endpoint_id=None,
                job_direction="import",
                job_type="customers.customer_csv",
                request_payload_json={"row_count": len(parsed_rows), "continue_on_error": payload.continue_on_error},
                requested_by_user_id=actor.user_id,
                status="started",
                started_at=datetime.now(UTC),
                created_by_user_id=actor.user_id,
                updated_by_user_id=actor.user_id,
            )
        )
        row_results: list[CustomerImportRowResult] = []
        counts = {
            "created_customers": 0,
            "updated_customers": 0,
            "created_contacts": 0,
            "updated_contacts": 0,
            "created_address_links": 0,
            "updated_address_links": 0,
        }
        for row in parsed_rows:
            preview = self._validate_import_row(tenant_id, row, actor)
            if preview.status == "invalid":
                row_results.append(preview)
                if not payload.continue_on_error:
                    break
                continue
            try:
                result = self._execute_import_row(tenant_id, row, actor)
            except ApiException as exc:
                row_results.append(
                    CustomerImportRowResult(
                        row_no=row.row_no,
                        customer_number=(row.data.get("customer_number") or None),
                        status="invalid",
                        messages=[exc.code],
                    )
                )
                if not payload.continue_on_error:
                    break
                continue
            row_results.append(result)
            for key in counts:
                counts[key] += int(key in result.messages)

        invalid_rows = sum(1 for row in row_results if row.status == "invalid")
        report_document_id, _report_version_no = self._create_result_document(
            tenant_id,
            actor,
            file_name=f"customer-import-{job.id}.csv",
            title="Customer import result",
            source_label="customer-import-result",
            owner_type="integration.import_export_job",
            owner_id=job.id,
            content=self._build_import_result_csv(row_results).encode("utf-8"),
        )
        job.completed_at = datetime.now(UTC)
        job.status = "completed"
        job.error_summary = None if invalid_rows == 0 else f"Import completed with {invalid_rows} invalid rows."
        job.result_summary_json = {
            "total_rows": len(row_results),
            "invalid_rows": invalid_rows,
            "report_document_id": report_document_id,
        }
        job.version_no += 1
        job.updated_by_user_id = actor.user_id
        self.integration_repository.save_job(job)
        self._record_event(
            actor,
            event_type="customers.import.executed",
            entity_type="integration.import_export_job",
            entity_id=job.id,
            tenant_id=tenant_id,
            after_json={"status": job.status},
            metadata_json={
                "total_rows": len(row_results),
                "invalid_rows": invalid_rows,
                "report_document_id": report_document_id,
            },
        )
        return CustomerImportExecuteResult(
            tenant_id=tenant_id,
            job_id=job.id,
            job_status=job.status,
            total_rows=len(row_results),
            invalid_rows=invalid_rows,
            result_document_ids=[report_document_id],
            rows=row_results,
            **counts,
        )

    def export_customers(
        self,
        tenant_id: str,
        payload: CustomerExportRequest,
        actor: RequestAuthorizationContext,
    ) -> CustomerExportResult:
        self._ensure_tenant_scope(actor, tenant_id)
        self._ensure_payload_tenant(tenant_id, payload.tenant_id)
        filters = CustomerFilter(
            search=payload.search,
            include_archived=payload.include_archived,
        )
        customers = self.customer_repository.list_customers(tenant_id, filters)
        job = self.integration_repository.create_job(
            ImportExportJob(
                tenant_id=tenant_id,
                endpoint_id=None,
                job_direction="export",
                job_type="customers.customer_csv",
                request_payload_json={"include_archived": payload.include_archived, "search": payload.search},
                requested_by_user_id=actor.user_id,
                status="started",
                started_at=datetime.now(UTC),
                created_by_user_id=actor.user_id,
                updated_by_user_id=actor.user_id,
            )
        )
        csv_content, row_count = self._build_export_csv(customers)
        document_id, version_no = self._create_result_document(
            tenant_id,
            actor,
            file_name=f"customers-export-{job.id}.csv",
            title="Customer export",
            source_label="customer-export",
            owner_type="integration.import_export_job",
            owner_id=job.id,
            content=csv_content.encode("utf-8"),
        )
        job.completed_at = datetime.now(UTC)
        job.status = "completed"
        job.result_summary_json = {"row_count": row_count, "document_id": document_id}
        job.version_no += 1
        job.updated_by_user_id = actor.user_id
        self.integration_repository.save_job(job)
        self._record_event(
            actor,
            event_type="customers.export.executed",
            entity_type="integration.import_export_job",
            entity_id=job.id,
            tenant_id=tenant_id,
            after_json={"status": job.status},
            metadata_json={"row_count": row_count, "document_id": document_id},
        )
        return CustomerExportResult(
            tenant_id=tenant_id,
            job_id=job.id,
            document_id=document_id,
            version_no=version_no,
            file_name=f"customers-export-{job.id}.csv",
            row_count=row_count,
        )

    def export_vcard(
        self,
        tenant_id: str,
        customer_id: str,
        contact_id: str,
        actor: RequestAuthorizationContext,
    ) -> CustomerVCardResult:
        self._ensure_tenant_scope(actor, tenant_id)
        customer = self.customer_service.get_customer(tenant_id, customer_id, actor)
        contact = next((row for row in customer.contacts if row.id == contact_id), None)
        if contact is None:
            raise ApiException(404, "customers.not_found.contact", "errors.customers.contact.not_found")
        vcard_text = self._build_vcard(customer, contact)
        file_name = f"{self._slugify(contact.full_name)}.vcf"
        document_id, version_no = self._create_result_document(
            tenant_id,
            actor,
            file_name=file_name,
            title=f"vCard {contact.full_name}",
            source_label="customer-contact-vcard",
            owner_type="crm.customer_contact",
            owner_id=contact.id,
            content=vcard_text.encode("utf-8"),
        )
        self._record_event(
            actor,
            event_type="customers.contact.vcard_exported",
            entity_type="crm.customer_contact",
            entity_id=contact.id,
            tenant_id=tenant_id,
            metadata_json={"customer_id": customer_id, "document_id": document_id, "version_no": version_no},
        )
        document = self.document_service.get_document(tenant_id, document_id, actor)
        version = document.versions[-1]
        return CustomerVCardResult(
            tenant_id=tenant_id,
            customer_id=customer_id,
            contact_id=contact_id,
            document_id=document_id,
            version_no=version.version_no,
            file_name=file_name,
            content_type=version.content_type,
            content_base64=base64.b64encode(vcard_text.encode("utf-8")).decode("ascii"),
        )

    def list_history(
        self,
        tenant_id: str,
        customer_id: str,
        actor: RequestAuthorizationContext,
    ) -> list[CustomerHistoryEntryRead]:
        self._ensure_tenant_scope(actor, tenant_id)
        self.customer_service.get_customer(tenant_id, customer_id, actor)
        return [
            CustomerHistoryEntryRead.model_validate(row)
            for row in self.customer_repository.list_history_entries(tenant_id, customer_id)
        ]

    def _validate_import_row(
        self,
        tenant_id: str,
        row: ParsedImportRow,
        actor: RequestAuthorizationContext,
    ) -> CustomerImportRowResult:
        data = row.data
        messages: list[str] = []
        customer_number = data.get("customer_number") or None
        if not customer_number:
            messages.append("customer_number is required")
        if not data.get("name"):
            messages.append("name is required")
        if data.get("contact_user_id"):
            try:
                customer_for_scope = self.customer_repository.find_customer_by_number(tenant_id, customer_number or "")
                existing_customer_id = customer_for_scope.id if customer_for_scope else "__new__"
                self.customer_service._validate_contact_constraints(  # type: ignore[attr-defined]
                    tenant_id,
                    existing_customer_id,
                    CustomerContactCreate(
                        tenant_id=tenant_id,
                        customer_id=existing_customer_id,
                        full_name=data.get("contact_full_name") or "",
                        email=data.get("contact_email") or None,
                        phone=data.get("contact_phone") or None,
                        mobile=data.get("contact_mobile") or None,
                        is_primary_contact=self._as_bool(data.get("is_primary_contact")),
                        is_billing_contact=self._as_bool(data.get("is_billing_contact")),
                        user_id=data.get("contact_user_id") or None,
                    ),
                )
            except ApiException as exc:
                messages.append(exc.code)
        if data.get("address_id") and not data.get("address_type"):
            messages.append("address_type is required when address_id is provided")
        status = "valid" if not messages else "invalid"
        return CustomerImportRowResult(
            row_no=row.row_no,
            customer_number=customer_number,
            status=status,
            messages=messages,
        )

    def _execute_import_row(
        self,
        tenant_id: str,
        row: ParsedImportRow,
        actor: RequestAuthorizationContext,
    ) -> CustomerImportRowResult:
        data = row.data
        existing_customer = self.customer_repository.find_customer_by_number(tenant_id, data["customer_number"])
        if existing_customer is None:
            customer = self.customer_service.create_customer(
                tenant_id,
                CustomerCreate(
                    tenant_id=tenant_id,
                    customer_number=data["customer_number"],
                    name=data["name"],
                    legal_name=data.get("legal_name") or None,
                    external_ref=data.get("external_ref") or None,
                    default_branch_id=data.get("default_branch_id") or None,
                    default_mandate_id=data.get("default_mandate_id") or None,
                    classification_lookup_id=data.get("classification_lookup_id") or None,
                    ranking_lookup_id=data.get("ranking_lookup_id") or None,
                    customer_status_lookup_id=data.get("customer_status_lookup_id") or None,
                ),
                actor,
            )
            customer_event = "created_customers"
        else:
            customer = self.customer_service.update_customer(
                tenant_id,
                existing_customer.id,
                CustomerUpdate(
                    name=data["name"],
                    legal_name=data.get("legal_name") or None,
                    external_ref=data.get("external_ref") or None,
                    default_branch_id=data.get("default_branch_id") or None,
                    default_mandate_id=data.get("default_mandate_id") or None,
                    classification_lookup_id=data.get("classification_lookup_id") or None,
                    ranking_lookup_id=data.get("ranking_lookup_id") or None,
                    customer_status_lookup_id=data.get("customer_status_lookup_id") or None,
                    version_no=existing_customer.version_no,
                ),
                actor,
            )
            customer_event = "updated_customers"

        messages = [customer_event]
        contact_id: str | None = None
        if data.get("contact_full_name"):
            existing_contact = None
            if data.get("contact_email"):
                existing_contact = self.customer_repository.find_contact_by_email(
                    tenant_id,
                    customer.id,
                    data["contact_email"],
                )
            if existing_contact is None:
                existing_contact = self.customer_repository.find_contact_by_name(
                    tenant_id,
                    customer.id,
                    data["contact_full_name"],
                )
            if existing_contact is None:
                contact = self.customer_service.create_contact(
                    tenant_id,
                    customer.id,
                    CustomerContactCreate(
                        tenant_id=tenant_id,
                        customer_id=customer.id,
                        full_name=data["contact_full_name"],
                        email=data.get("contact_email") or None,
                        phone=data.get("contact_phone") or None,
                        mobile=data.get("contact_mobile") or None,
                        is_primary_contact=self._as_bool(data.get("is_primary_contact")),
                        is_billing_contact=self._as_bool(data.get("is_billing_contact")),
                        user_id=data.get("contact_user_id") or None,
                    ),
                    actor,
                )
                messages.append("created_contacts")
            else:
                contact = self.customer_service.update_contact(
                    tenant_id,
                    customer.id,
                    existing_contact.id,
                    CustomerContactUpdate(
                        full_name=data["contact_full_name"],
                        email=data.get("contact_email") or None,
                        phone=data.get("contact_phone") or None,
                        mobile=data.get("contact_mobile") or None,
                        is_primary_contact=self._as_bool(data.get("is_primary_contact")),
                        is_billing_contact=self._as_bool(data.get("is_billing_contact")),
                        user_id=data.get("contact_user_id") or None,
                        version_no=existing_contact.version_no,
                    ),
                    actor,
                )
                messages.append("updated_contacts")
            contact_id = contact.id

        if data.get("address_id") and data.get("address_type"):
            existing_link = self.customer_repository.find_address_link_by_type(
                tenant_id,
                customer.id,
                data["address_type"],
            )
            if existing_link is None:
                self.customer_service.create_customer_address(
                    tenant_id,
                    customer.id,
                    CustomerAddressCreate(
                        tenant_id=tenant_id,
                        customer_id=customer.id,
                        address_id=data["address_id"],
                        address_type=data["address_type"],
                        label=data.get("address_label") or None,
                        is_default=self._as_bool(data.get("is_default_address")),
                    ),
                    actor,
                )
                messages.append("created_address_links")
            else:
                self.customer_service.update_customer_address(
                    tenant_id,
                    customer.id,
                    existing_link.id,
                    CustomerAddressUpdate(
                        address_id=data["address_id"],
                        address_type=data["address_type"],
                        label=data.get("address_label") or None,
                        is_default=self._as_bool(data.get("is_default_address")),
                        version_no=existing_link.version_no,
                    ),
                    actor,
                )
                messages.append("updated_address_links")

        return CustomerImportRowResult(
            row_no=row.row_no,
            customer_number=customer.customer_number,
            status="processed",
            messages=messages,
            customer_id=customer.id,
            contact_id=contact_id,
        )

    @staticmethod
    def _parse_import_csv(encoded: str) -> list[ParsedImportRow]:
        try:
            decoded = base64.b64decode(encoded, validate=True).decode("utf-8-sig")
        except Exception as exc:  # noqa: BLE001
            raise ApiException(400, "customers.import.invalid_content", "errors.customers.import.invalid_content") from exc
        reader = csv.DictReader(io.StringIO(decoded))
        if reader.fieldnames is None:
            raise ApiException(400, "customers.import.invalid_headers", "errors.customers.import.invalid_headers")
        missing_headers = [header for header in ("customer_number", "name") if header not in reader.fieldnames]
        if missing_headers:
            raise ApiException(
                400,
                "customers.import.invalid_headers",
                "errors.customers.import.invalid_headers",
                {"missing_headers": missing_headers},
            )
        return [
            ParsedImportRow(
                row_no=index,
                data={header: (value or "").strip() for header, value in row.items() if header},
            )
            for index, row in enumerate(reader, start=2)
        ]

    @staticmethod
    def _build_import_result_csv(rows: list[CustomerImportRowResult]) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(("row_no", "customer_number", "status", "messages", "customer_id", "contact_id"))
        for row in rows:
            writer.writerow(
                (
                    row.row_no,
                    row.customer_number or "",
                    row.status,
                    " | ".join(row.messages),
                    row.customer_id or "",
                    row.contact_id or "",
                )
            )
        return output.getvalue()

    @staticmethod
    def _build_export_csv(customers: list[Customer]) -> tuple[str, int]:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            (
                "customer_number",
                "name",
                "status",
                "default_branch_id",
                "default_mandate_id",
                "contact_full_name",
                "contact_email",
                "contact_phone",
                "contact_mobile",
                "contact_user_id",
                "is_primary_contact",
                "address_type",
                "address_id",
                "address_label",
                "is_default_address",
            )
        )
        row_count = 0
        for customer in customers:
            contacts = customer.contacts or [None]
            addresses = customer.addresses or [None]
            for contact in contacts:
                for address in addresses:
                    writer.writerow(
                        (
                            customer.customer_number,
                            customer.name,
                            customer.status,
                            customer.default_branch_id or "",
                            customer.default_mandate_id or "",
                            contact.full_name if contact else "",
                            contact.email if contact else "",
                            contact.phone if contact else "",
                            contact.mobile if contact else "",
                            contact.user_id if contact else "",
                            "true" if contact and contact.is_primary_contact else "false",
                            address.address_type if address else "",
                            address.address_id if address else "",
                            address.label if address else "",
                            "true" if address and address.is_default else "false",
                        )
                    )
                    row_count += 1
        return output.getvalue(), row_count

    def _build_vcard(self, customer: CustomerRead, contact: CustomerContactRead) -> str:
        lines = [
            "BEGIN:VCARD",
            "VERSION:3.0",
            f"N:{contact.full_name};;;;",
            f"FN:{contact.full_name}",
        ]
        if contact.email:
            lines.append(f"EMAIL;TYPE=INTERNET:{contact.email}")
        if contact.phone:
            lines.append(f"TEL;TYPE=WORK:{contact.phone}")
        if contact.mobile:
            lines.append(f"TEL;TYPE=CELL:{contact.mobile}")
        lines.append(f"ORG:{customer.name}")
        if contact.function_label:
            lines.append(f"TITLE:{contact.function_label}")
        lines.append("END:VCARD")
        return "\r\n".join(lines) + "\r\n"

    def _create_result_document(
        self,
        tenant_id: str,
        actor: RequestAuthorizationContext,
        *,
        file_name: str,
        title: str,
        source_label: str,
        owner_type: str,
        owner_id: str,
        content: bytes,
    ) -> tuple[str, int]:
        document = self.document_service.create_document(
            tenant_id,
            DocumentCreate(
                tenant_id=tenant_id,
                title=title,
                source_module="customers",
                source_label=source_label,
            ),
            actor,
        )
        version = self.document_service.add_document_version(
            tenant_id,
            document.id,
            DocumentVersionCreate(
                file_name=file_name,
                content_type="text/csv" if file_name.endswith(".csv") else "text/vcard",
                content_base64=base64.b64encode(content).decode("ascii"),
                metadata_json={"generated_by": "customers.ops"},
            ),
            actor,
        )
        self.document_service.add_document_link(
            tenant_id,
            document.id,
            DocumentLinkCreate(owner_type=owner_type, owner_id=owner_id, relation_type="attachment"),
            actor,
        )
        return document.id, version.version_no

    @staticmethod
    def _slugify(value: str) -> str:
        return "".join(char.lower() if char.isalnum() else "-" for char in value).strip("-") or "contact"

    @staticmethod
    def _as_bool(value: str | None) -> bool:
        return (value or "").strip().lower() in {"1", "true", "yes", "ja", "y"}

    @staticmethod
    def _ensure_tenant_scope(actor: RequestAuthorizationContext, tenant_id: str) -> None:
        enforce_customer_module_access(actor, tenant_id=tenant_id)

    @staticmethod
    def _ensure_payload_tenant(tenant_id: str, payload_tenant_id: str) -> None:
        if payload_tenant_id == tenant_id:
            return
        raise ApiException(
            400,
            "customers.validation.tenant_mismatch",
            "errors.customers.customer.tenant_mismatch",
            {"tenant_id": tenant_id},
        )

    def _record_event(
        self,
        actor: RequestAuthorizationContext,
        *,
        event_type: str,
        entity_type: str,
        entity_id: str,
        tenant_id: str,
        before_json: dict[str, object] | None = None,
        after_json: dict[str, object] | None = None,
        metadata_json: dict[str, object] | None = None,
    ) -> None:
        if self.audit_service is None:
            return
        self.audit_service.record_business_event(
            actor=AuditActor(
                tenant_id=tenant_id,
                user_id=actor.user_id,
                session_id=actor.session_id,
                request_id=actor.request_id,
            ),
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            tenant_id=tenant_id,
            before_json=before_json,
            after_json=after_json,
            metadata_json=metadata_json,
        )
