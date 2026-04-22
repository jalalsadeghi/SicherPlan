"""SQLAlchemy repository for tenant-scoped document metadata."""

from __future__ import annotations

from sqlalchemy import Select, String, cast, delete, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.modules.core.models import Branch, Mandate, Tenant, TenantSetting
from app.modules.customers.models import Customer, CustomerContact, CustomerHistoryEntry
from app.modules.employees.models import Employee, EmployeeQualification
from app.modules.field_execution.models import PatrolRound, PatrolRoundEvent, Watchbook, WatchbookEntry
from app.modules.finance.models import CustomerInvoice, PayrollExportBatch, PayrollPayslipArchive, Timesheet
from app.modules.recruiting.models import Applicant
from app.modules.subcontractors.models import (
    Subcontractor,
    SubcontractorHistoryEntry,
    SubcontractorWorker,
    SubcontractorWorkerQualification,
)
from app.modules.platform_services.comm_models import OutboundMessage
from app.modules.platform_services.info_models import Notice
from app.modules.platform_services.integration_models import ImportExportJob
from app.modules.planning.models import CustomerOrder, PlanningRecord, Shift
from app.modules.platform_services.docs_models import (
    Document,
    DocumentLink,
    DocumentType,
    DocumentVersion,
)


class SqlAlchemyDocumentRepository:
    SUPPORTED_OWNER_TYPES = frozenset(
        {
            "core.tenant",
            "core.branch",
            "core.mandate",
            "core.tenant_setting",
            "crm.customer",
            "crm.customer_contact",
            "crm.customer_history_entry",
            "hr.applicant",
            "hr.employee",
            "hr.employee_qualification",
            "partner.subcontractor",
            "partner.subcontractor_history_entry",
            "partner.subcontractor_worker",
            "partner.subcontractor_worker_qualification",
            "comm.outbound_message",
            "info.notice",
            "integration.import_export_job",
            "ops.customer_order",
            "ops.planning_record",
            "ops.shift",
            "finance.payroll_export_batch",
            "finance.payroll_payslip_archive",
            "finance.timesheet",
            "finance.customer_invoice",
            "field.watchbook",
            "field.watchbook_entry",
            "field.patrol_round",
            "field.patrol_round_event",
        }
    )

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_document_type_by_key(self, key: str) -> DocumentType | None:
        return self.session.scalars(select(DocumentType).where(DocumentType.key == key)).one_or_none()

    def create_document(self, row: Document) -> Document:
        self.session.add(row)
        self.session.commit()
        return self.get_document(row.tenant_id, row.id) or row

    def get_document(self, tenant_id: str, document_id: str) -> Document | None:
        statement = self._document_query().where(Document.tenant_id == tenant_id, Document.id == document_id)
        return self.session.scalars(statement).unique().one_or_none()

    def list_documents(
        self,
        tenant_id: str,
        *,
        search: str | None = None,
        document_type_key: str | None = None,
        linked_entity: str | None = None,
        limit: int = 25,
    ) -> list[Document]:
        statement = self._document_query().where(Document.tenant_id == tenant_id, Document.archived_at.is_(None))
        if search or document_type_key:
            statement = statement.outerjoin(DocumentType, Document.document_type_id == DocumentType.id)
        if search:
            pattern = f"%{search.strip()}%"
            statement = statement.outerjoin(DocumentVersion).where(
                or_(
                    cast(Document.id, String).ilike(pattern),
                    Document.title.ilike(pattern),
                    Document.source_label.ilike(pattern),
                    Document.source_module.ilike(pattern),
                    DocumentVersion.file_name.ilike(pattern),
                    DocumentType.key.ilike(pattern),
                    DocumentType.name.ilike(pattern),
                )
            )
        if document_type_key:
            statement = statement.where(DocumentType.key == document_type_key)
        if linked_entity:
            owner_type, _, owner_id = linked_entity.partition(":")
            if owner_type and owner_id:
                statement = statement.join(DocumentLink, DocumentLink.document_id == Document.id).where(
                    DocumentLink.tenant_id == tenant_id,
                    DocumentLink.owner_type == owner_type,
                    DocumentLink.owner_id == owner_id,
                )
        statement = statement.limit(limit)
        return list(self.session.scalars(statement).unique().all())

    def find_document_by_source_reference(
        self,
        tenant_id: str,
        *,
        source_module: str,
        source_label: str,
    ) -> Document | None:
        statement = self._document_query().where(
            Document.tenant_id == tenant_id,
            Document.source_module == source_module,
            Document.source_label == source_label,
        )
        return self.session.scalars(statement).unique().one_or_none()

    def list_document_versions(self, tenant_id: str, document_id: str) -> list[DocumentVersion]:
        statement = (
            select(DocumentVersion)
            .where(DocumentVersion.tenant_id == tenant_id, DocumentVersion.document_id == document_id)
            .order_by(DocumentVersion.version_no)
        )
        return list(self.session.scalars(statement).all())

    def create_document_version(self, document: Document, row: DocumentVersion) -> DocumentVersion:
        document.current_version_no = row.version_no
        document.updated_by_user_id = row.uploaded_by_user_id
        document.version_no += 1
        self.session.add(row)
        self.session.add(document)
        self.session.commit()
        self.session.refresh(row)
        return row

    def get_document_version(
        self,
        tenant_id: str,
        document_id: str,
        version_no: int,
    ) -> DocumentVersion | None:
        statement = (
            select(DocumentVersion)
            .where(
                DocumentVersion.tenant_id == tenant_id,
                DocumentVersion.document_id == document_id,
                DocumentVersion.version_no == version_no,
            )
        )
        return self.session.scalars(statement).one_or_none()

    def create_document_link(self, row: DocumentLink) -> DocumentLink:
        self.session.add(row)
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            raise
        self.session.refresh(row)
        return row

    def delete_document_link(self, tenant_id: str, document_id: str, owner_type: str, owner_id: str) -> bool:
        result = self.session.execute(
            delete(DocumentLink).where(
                DocumentLink.tenant_id == tenant_id,
                DocumentLink.document_id == document_id,
                DocumentLink.owner_type == owner_type,
                DocumentLink.owner_id == owner_id,
            )
        )
        self.session.commit()
        return bool(result.rowcount)

    def owner_exists(self, tenant_id: str, owner_type: str, owner_id: str) -> bool:
        if owner_type not in self.SUPPORTED_OWNER_TYPES:
            return False
        model = {
            "core.tenant": Tenant,
            "core.branch": Branch,
            "core.mandate": Mandate,
            "core.tenant_setting": TenantSetting,
            "crm.customer": Customer,
            "crm.customer_contact": CustomerContact,
            "crm.customer_history_entry": CustomerHistoryEntry,
            "hr.applicant": Applicant,
            "hr.employee": Employee,
            "hr.employee_qualification": EmployeeQualification,
            "partner.subcontractor": Subcontractor,
            "partner.subcontractor_history_entry": SubcontractorHistoryEntry,
            "partner.subcontractor_worker": SubcontractorWorker,
            "partner.subcontractor_worker_qualification": SubcontractorWorkerQualification,
            "comm.outbound_message": OutboundMessage,
            "info.notice": Notice,
            "integration.import_export_job": ImportExportJob,
            "ops.customer_order": CustomerOrder,
            "ops.planning_record": PlanningRecord,
            "ops.shift": Shift,
            "finance.payroll_export_batch": PayrollExportBatch,
            "finance.payroll_payslip_archive": PayrollPayslipArchive,
            "finance.timesheet": Timesheet,
            "finance.customer_invoice": CustomerInvoice,
            "field.watchbook": Watchbook,
            "field.watchbook_entry": WatchbookEntry,
            "field.patrol_round": PatrolRound,
            "field.patrol_round_event": PatrolRoundEvent,
        }[owner_type]
        statement: Select[tuple[object]] = select(model).where(model.id == owner_id)
        if model is not Tenant:
            statement = statement.where(model.tenant_id == tenant_id)
        else:
            statement = statement.where(Tenant.id == tenant_id)
        return self.session.scalars(statement).one_or_none() is not None

    def list_documents_for_owner(
        self,
        tenant_id: str,
        owner_type: str,
        owner_id: str,
    ) -> list[Document]:
        statement = (
            self._document_query()
            .join(DocumentLink, DocumentLink.document_id == Document.id)
            .where(
                Document.tenant_id == tenant_id,
                DocumentLink.tenant_id == tenant_id,
                DocumentLink.owner_type == owner_type,
                DocumentLink.owner_id == owner_id,
            )
        )
        return list(self.session.scalars(statement).unique().all())

    @staticmethod
    def _document_query() -> Select[tuple[Document]]:
        return (
            select(Document)
            .options(joinedload(Document.document_type))
            .options(joinedload(Document.versions))
            .options(joinedload(Document.links))
            .order_by(Document.created_at)
        )
