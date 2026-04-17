"""Pydantic DTOs for subcontractor master maintenance."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.modules.core.schemas import AddressCreate, AddressRead


class SubcontractorFilter(BaseModel):
    search: str | None = None
    status: str | None = None
    branch_id: str | None = None
    mandate_id: str | None = None
    include_archived: bool = False


class SubcontractorCreate(BaseModel):
    tenant_id: str
    subcontractor_number: str = Field(min_length=1, max_length=50)
    legal_name: str = Field(min_length=1, max_length=255)
    display_name: str | None = Field(default=None, max_length=255)
    legal_form_lookup_id: str | None = None
    subcontractor_status_lookup_id: str | None = None
    managing_director_name: str | None = Field(default=None, max_length=255)
    address_id: str | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    notes: str | None = None


class SubcontractorUpdate(BaseModel):
    subcontractor_number: str | None = Field(default=None, min_length=1, max_length=50)
    legal_name: str | None = Field(default=None, min_length=1, max_length=255)
    display_name: str | None = Field(default=None, max_length=255)
    legal_form_lookup_id: str | None = None
    subcontractor_status_lookup_id: str | None = None
    managing_director_name: str | None = Field(default=None, max_length=255)
    address_id: str | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    notes: str | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class SubcontractorListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    subcontractor_number: str
    legal_name: str
    display_name: str | None
    managing_director_name: str | None
    latitude: Decimal | None
    longitude: Decimal | None
    status: str
    archived_at: datetime | None
    version_no: int


class SubcontractorContactCreate(BaseModel):
    tenant_id: str
    subcontractor_id: str
    full_name: str = Field(min_length=1, max_length=255)
    title: str | None = Field(default=None, max_length=120)
    function_label: str | None = Field(default=None, max_length=120)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=64)
    mobile: str | None = Field(default=None, max_length=64)
    is_primary_contact: bool = False
    portal_enabled: bool = False
    user_id: str | None = None
    notes: str | None = None


class SubcontractorContactUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    title: str | None = Field(default=None, max_length=120)
    function_label: str | None = Field(default=None, max_length=120)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=64)
    mobile: str | None = Field(default=None, max_length=64)
    is_primary_contact: bool | None = None
    portal_enabled: bool | None = None
    user_id: str | None = None
    notes: str | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class SubcontractorContactRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    subcontractor_id: str
    full_name: str
    title: str | None
    function_label: str | None
    email: str | None
    phone: str | None
    mobile: str | None
    is_primary_contact: bool
    portal_enabled: bool
    user_id: str | None
    notes: str | None
    status: str
    archived_at: datetime | None
    version_no: int


class SubcontractorEligibleUserOptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    email: str
    full_name: str
    status: str


class SubcontractorReferenceOptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    code: str
    label: str
    description: str | None
    status: str
    archived_at: datetime | None


class SubcontractorReferenceDataRead(BaseModel):
    legal_forms: list[SubcontractorReferenceOptionRead] = Field(default_factory=list)


class SubcontractorScopeCreate(BaseModel):
    tenant_id: str
    subcontractor_id: str
    branch_id: str
    mandate_id: str | None = None
    valid_from: date
    valid_to: date | None = None
    notes: str | None = None


class SubcontractorScopeUpdate(BaseModel):
    branch_id: str | None = None
    mandate_id: str | None = None
    valid_from: date | None = None
    valid_to: date | None = None
    notes: str | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class SubcontractorScopeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    subcontractor_id: str
    branch_id: str
    mandate_id: str | None
    valid_from: date
    valid_to: date | None
    notes: str | None
    status: str
    archived_at: datetime | None
    version_no: int


class SubcontractorFinanceProfileCreate(BaseModel):
    tenant_id: str
    subcontractor_id: str
    invoice_email: str | None = Field(default=None, max_length=255)
    payment_terms_days: int | None = None
    payment_terms_note: str | None = Field(default=None, max_length=255)
    tax_number: str | None = Field(default=None, max_length=120)
    vat_id: str | None = Field(default=None, max_length=120)
    bank_account_holder: str | None = Field(default=None, max_length=255)
    bank_iban: str | None = Field(default=None, max_length=64)
    bank_bic: str | None = Field(default=None, max_length=64)
    bank_name: str | None = Field(default=None, max_length=255)
    invoice_delivery_method_lookup_id: str | None = None
    invoice_status_mode_lookup_id: str | None = None
    billing_note: str | None = None


class SubcontractorFinanceProfileUpdate(BaseModel):
    invoice_email: str | None = Field(default=None, max_length=255)
    payment_terms_days: int | None = None
    payment_terms_note: str | None = Field(default=None, max_length=255)
    tax_number: str | None = Field(default=None, max_length=120)
    vat_id: str | None = Field(default=None, max_length=120)
    bank_account_holder: str | None = Field(default=None, max_length=255)
    bank_iban: str | None = Field(default=None, max_length=64)
    bank_bic: str | None = Field(default=None, max_length=64)
    bank_name: str | None = Field(default=None, max_length=255)
    invoice_delivery_method_lookup_id: str | None = None
    invoice_status_mode_lookup_id: str | None = None
    billing_note: str | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class SubcontractorFinanceProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    subcontractor_id: str
    invoice_email: str | None
    payment_terms_days: int | None
    payment_terms_note: str | None
    tax_number: str | None
    vat_id: str | None
    bank_account_holder: str | None
    bank_iban: str | None
    bank_bic: str | None
    bank_name: str | None
    invoice_delivery_method_lookup_id: str | None
    invoice_status_mode_lookup_id: str | None
    billing_note: str | None
    status: str
    archived_at: datetime | None
    version_no: int


class SubcontractorRead(SubcontractorListItem):
    model_config = ConfigDict(from_attributes=True)

    legal_form_lookup_id: str | None
    subcontractor_status_lookup_id: str | None
    address_id: str | None
    notes: str | None
    address: AddressRead | None = None
    contacts: list[SubcontractorContactRead] = Field(default_factory=list)
    scopes: list[SubcontractorScopeRead] = Field(default_factory=list)
    finance_profile: SubcontractorFinanceProfileRead | None = None


class SubcontractorPortalCompanyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    subcontractor_number: str
    legal_name: str
    display_name: str | None
    status: str


class SubcontractorPortalContactRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    subcontractor_id: str
    full_name: str
    function_label: str | None
    email: str | None
    phone: str | None
    mobile: str | None
    portal_enabled: bool
    status: str


class SubcontractorPortalScopeRead(BaseModel):
    role_key: str
    scope_type: str
    subcontractor_id: str


class SubcontractorPortalContextRead(BaseModel):
    tenant_id: str
    user_id: str
    subcontractor_id: str
    contact_id: str
    company: SubcontractorPortalCompanyRead
    contact: SubcontractorPortalContactRead
    scopes: list[SubcontractorPortalScopeRead] = Field(default_factory=list)


class SubcontractorPortalQualificationTypeOptionRead(BaseModel):
    id: str
    code: str
    label: str
    expiry_required: bool
    default_validity_days: int | None = None
    proof_required: bool
    compliance_relevant: bool


class SubcontractorPortalWorkerCreate(BaseModel):
    worker_no: str = Field(min_length=1, max_length=80)
    first_name: str = Field(min_length=1, max_length=120)
    last_name: str = Field(min_length=1, max_length=120)
    preferred_name: str | None = Field(default=None, max_length=120)
    birth_date: date | None = None
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=64)
    mobile: str | None = Field(default=None, max_length=64)


class SubcontractorPortalWorkerUpdate(BaseModel):
    worker_no: str | None = Field(default=None, min_length=1, max_length=80)
    first_name: str | None = Field(default=None, min_length=1, max_length=120)
    last_name: str | None = Field(default=None, min_length=1, max_length=120)
    preferred_name: str | None = Field(default=None, max_length=120)
    birth_date: date | None = None
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=64)
    mobile: str | None = Field(default=None, max_length=64)
    version_no: int | None = None


class SubcontractorPortalWorkerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    subcontractor_id: str
    worker_no: str
    first_name: str
    last_name: str
    preferred_name: str | None
    email: str | None
    mobile: str | None
    status: str
    archived_at: datetime | None
    version_no: int
    birth_date: date | None
    phone: str | None
    qualifications: list[SubcontractorWorkerQualificationRead] = Field(default_factory=list)


class SubcontractorPortalWorkerQualificationCreate(BaseModel):
    qualification_type_id: str
    certificate_no: str | None = Field(default=None, max_length=120)
    issued_at: date | None = None
    valid_until: date | None = None
    issuing_authority: str | None = Field(default=None, max_length=255)
    notes: str | None = None


class SubcontractorPortalWorkerQualificationUpdate(BaseModel):
    certificate_no: str | None = Field(default=None, max_length=120)
    issued_at: date | None = None
    valid_until: date | None = None
    issuing_authority: str | None = Field(default=None, max_length=255)
    notes: str | None = None
    version_no: int | None = None


class SubcontractorPortalCollectionSourceRead(BaseModel):
    domain_key: str
    source_module_key: str
    availability_status: str
    released_only: bool = True
    subcontractor_scoped: bool = True
    docs_backed_outputs: bool = False
    message_key: str


class SubcontractorPortalDocumentRefRead(BaseModel):
    document_id: str
    title: str
    file_name: str | None = None
    content_type: str | None = None
    current_version_no: int | None = None
    relation_type: str = "deployment_output"


class SubcontractorPortalPositionRead(BaseModel):
    id: str
    subcontractor_id: str
    reference_no: str
    title: str
    branch_label: str | None = None
    mandate_label: str | None = None
    work_start: datetime
    work_end: datetime
    location_label: str | None = None
    readiness_status: str
    confirmation_status: str


class SubcontractorPortalScheduleRead(BaseModel):
    id: str
    subcontractor_id: str
    position_id: str
    shift_label: str
    schedule_date: date
    work_start: datetime
    work_end: datetime
    location_label: str | None = None
    confirmation_status: str
    documents: list[SubcontractorPortalDocumentRefRead] = Field(default_factory=list)


class SubcontractorPortalWatchbookEntryRead(BaseModel):
    id: str
    subcontractor_id: str
    log_date: date
    occurred_at: datetime
    entry_type_code: str
    summary: str
    status: str
    pdf_document_id: str | None = None


class SubcontractorPortalActualSummaryRead(BaseModel):
    id: str
    subcontractor_id: str
    period_start: date
    period_end: date
    confirmed_minutes: int
    open_minutes: int
    status: str
    attendance_status: str


class SubcontractorPortalAttendanceRead(BaseModel):
    id: str
    subcontractor_id: str
    schedule_id: str
    work_date: date
    status: str
    confirmed_at: datetime | None = None
    location_label: str | None = None
    document_count: int = 0


class SubcontractorPortalInvoiceCheckRead(BaseModel):
    id: str
    subcontractor_id: str
    period_label: str
    status: str
    submitted_invoice_ref: str | None = None
    approved_minutes: int = 0
    approved_amount: Decimal | None = None
    submitted_invoice_amount: Decimal | None = None
    last_checked_at: datetime | None = None
    variance_minutes: int | None = None
    variance_amount: Decimal | None = None


class SubcontractorPortalInvoiceCheckLineRead(BaseModel):
    id: str
    service_date: date
    label: str
    billing_unit_code: str
    approved_quantity: Decimal
    unit_price: Decimal | None = None
    approved_amount: Decimal
    variance_amount: Decimal
    variance_reason_codes_json: list[str] = Field(default_factory=list)


class SubcontractorPortalInvoiceCheckDetailRead(SubcontractorPortalInvoiceCheckRead):
    period_start: date
    period_end: date
    released_at: datetime | None = None
    lines: list[SubcontractorPortalInvoiceCheckLineRead] = Field(default_factory=list)


class SubcontractorPortalPositionCollectionRead(BaseModel):
    subcontractor_id: str
    source: SubcontractorPortalCollectionSourceRead
    items: list[SubcontractorPortalPositionRead] = Field(default_factory=list)


class SubcontractorPortalScheduleCollectionRead(BaseModel):
    subcontractor_id: str
    source: SubcontractorPortalCollectionSourceRead
    items: list[SubcontractorPortalScheduleRead] = Field(default_factory=list)


class SubcontractorPortalWatchbookCollectionRead(BaseModel):
    subcontractor_id: str
    source: SubcontractorPortalCollectionSourceRead
    items: list[SubcontractorPortalWatchbookEntryRead] = Field(default_factory=list)


class SubcontractorPortalActualSummaryCollectionRead(BaseModel):
    subcontractor_id: str
    source: SubcontractorPortalCollectionSourceRead
    items: list[SubcontractorPortalActualSummaryRead] = Field(default_factory=list)


class SubcontractorPortalAttendanceCollectionRead(BaseModel):
    subcontractor_id: str
    source: SubcontractorPortalCollectionSourceRead
    items: list[SubcontractorPortalAttendanceRead] = Field(default_factory=list)


class SubcontractorPortalInvoiceCheckCollectionRead(BaseModel):
    subcontractor_id: str
    source: SubcontractorPortalCollectionSourceRead
    items: list[SubcontractorPortalInvoiceCheckRead] = Field(default_factory=list)


class SubcontractorPortalAllocationCandidateRead(BaseModel):
    worker_id: str
    worker_no: str
    display_name: str
    readiness_status: str
    is_ready: bool
    blocking_issue_count: int
    warning_issue_count: int
    issues: list[SubcontractorWorkerReadinessIssueRead] = Field(default_factory=list)


class SubcontractorPortalAllocationCandidateCollectionRead(BaseModel):
    subcontractor_id: str
    items: list[SubcontractorPortalAllocationCandidateRead] = Field(default_factory=list)


class SubcontractorPortalAllocationRequest(BaseModel):
    position_id: str = Field(min_length=1, max_length=120)
    worker_id: str = Field(min_length=1, max_length=120)
    action: str = Field(default="assign", pattern="^(assign|reassign|unassign|confirm)$")


class SubcontractorPortalAllocationPreviewRead(BaseModel):
    subcontractor_id: str
    position_id: str
    worker_id: str
    action: str
    command_status: str
    validation_scope: str
    can_submit: bool
    issues: list[SubcontractorWorkerReadinessIssueRead] = Field(default_factory=list)


class SubcontractorPortalAllocationResultRead(BaseModel):
    subcontractor_id: str
    position_id: str
    worker_id: str
    action: str
    command_status: str
    message_key: str
    acted_by_user_id: str
    confirmed_at: datetime | None = None
    issues: list[SubcontractorWorkerReadinessIssueRead] = Field(default_factory=list)


class SubcontractorHistoryEntryCreate(BaseModel):
    tenant_id: str
    subcontractor_id: str
    entry_type: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=255)
    body: str = Field(min_length=1)
    occurred_at: datetime | None = None
    related_contact_id: str | None = None
    metadata_json: dict[str, object] = Field(default_factory=dict)


class SubcontractorHistoryAttachmentRead(BaseModel):
    document_id: str
    title: str
    document_type_key: str | None = None
    file_name: str | None = None
    content_type: str | None = None
    current_version_no: int | None = None


class SubcontractorHistoryAttachmentLinkCreate(BaseModel):
    document_id: str
    label: str | None = None


class SubcontractorHistoryEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    subcontractor_id: str
    entry_type: str
    title: str
    body: str
    occurred_at: datetime
    actor_user_id: str | None
    related_contact_id: str | None
    metadata_json: dict[str, object]
    created_at: datetime
    attachments: list[SubcontractorHistoryAttachmentRead] = Field(default_factory=list)


class SubcontractorLifecycleTransitionRequest(BaseModel):
    version_no: int


class SubcontractorWorkerFilter(BaseModel):
    search: str | None = None
    status: str | None = None
    include_archived: bool = False


class SubcontractorWorkerReadinessFilter(BaseModel):
    search: str | None = None
    status: str | None = None
    include_archived: bool = False
    readiness_status: str | None = None
    issue_severity: str | None = None


class SubcontractorWorkerReadinessIssueRead(BaseModel):
    issue_code: str
    message_key: str
    severity: str
    category: str
    reference_type: str
    reference_id: str | None = None
    title: str
    due_on: date | None = None
    metadata_json: dict[str, object] = Field(default_factory=dict)


class SubcontractorWorkerReadinessListItem(BaseModel):
    worker_id: str
    tenant_id: str
    subcontractor_id: str
    worker_no: str
    first_name: str
    last_name: str
    preferred_name: str | None = None
    status: str
    archived_at: datetime | None = None
    readiness_status: str
    is_ready: bool
    blocking_issue_count: int
    warning_issue_count: int
    missing_proof_count: int
    expired_qualification_count: int
    expiring_qualification_count: int
    missing_credential_count: int
    issues: list[SubcontractorWorkerReadinessIssueRead] = Field(default_factory=list)


class SubcontractorWorkerReadinessRead(SubcontractorWorkerReadinessListItem):
    qualification_count: int
    credential_count: int
    checked_at: datetime


class SubcontractorWorkforceReadinessSummaryRead(BaseModel):
    tenant_id: str
    subcontractor_id: str
    total_workers: int
    ready_workers: int
    warning_only_workers: int
    not_ready_workers: int
    missing_proof_workers: int
    expired_qualification_workers: int
    expiring_qualification_workers: int
    missing_credential_workers: int
    checked_at: datetime


class SubcontractorWorkerImportDryRunRequest(BaseModel):
    tenant_id: str
    subcontractor_id: str
    csv_content_base64: str = Field(min_length=1)


class SubcontractorWorkerImportExecuteRequest(SubcontractorWorkerImportDryRunRequest):
    continue_on_error: bool = True


class SubcontractorWorkerImportRowResult(BaseModel):
    row_no: int
    worker_no: str | None = None
    status: str
    messages: list[str] = Field(default_factory=list)
    worker_id: str | None = None


class SubcontractorWorkerImportDryRunResult(BaseModel):
    tenant_id: str
    subcontractor_id: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    rows: list[SubcontractorWorkerImportRowResult]


class SubcontractorWorkerImportExecuteResult(BaseModel):
    tenant_id: str
    subcontractor_id: str
    job_id: str
    job_status: str
    total_rows: int
    invalid_rows: int
    created_workers: int
    updated_workers: int
    result_document_ids: list[str] = Field(default_factory=list)
    rows: list[SubcontractorWorkerImportRowResult]


class SubcontractorWorkerExportRequest(BaseModel):
    tenant_id: str
    subcontractor_id: str
    search: str | None = None
    status: str | None = None
    include_archived: bool = False


class SubcontractorWorkerExportResult(BaseModel):
    tenant_id: str
    subcontractor_id: str
    job_id: str
    document_id: str
    file_name: str
    row_count: int


class SubcontractorWorkerCreate(BaseModel):
    tenant_id: str
    subcontractor_id: str
    worker_no: str = Field(min_length=1, max_length=80)
    first_name: str = Field(min_length=1, max_length=120)
    last_name: str = Field(min_length=1, max_length=120)
    preferred_name: str | None = Field(default=None, max_length=120)
    birth_date: date | None = None
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=64)
    mobile: str | None = Field(default=None, max_length=64)
    notes: str | None = None


class SubcontractorWorkerUpdate(BaseModel):
    worker_no: str | None = Field(default=None, min_length=1, max_length=80)
    first_name: str | None = Field(default=None, min_length=1, max_length=120)
    last_name: str | None = Field(default=None, min_length=1, max_length=120)
    preferred_name: str | None = Field(default=None, max_length=120)
    birth_date: date | None = None
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=64)
    mobile: str | None = Field(default=None, max_length=64)
    notes: str | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class SubcontractorWorkerListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    subcontractor_id: str
    worker_no: str
    first_name: str
    last_name: str
    preferred_name: str | None
    email: str | None
    mobile: str | None
    status: str
    archived_at: datetime | None
    version_no: int


class SubcontractorWorkerQualificationProofRead(BaseModel):
    document_id: str
    title: str
    document_type_key: str | None = None
    file_name: str | None = None
    content_type: str | None = None
    current_version_no: int | None = None
    relation_type: str = "proof_document"


class SubcontractorWorkerQualificationCreate(BaseModel):
    tenant_id: str
    subcontractor_id: str
    worker_id: str
    qualification_type_id: str
    certificate_no: str | None = Field(default=None, max_length=120)
    issued_at: date | None = None
    valid_until: date | None = None
    issuing_authority: str | None = Field(default=None, max_length=255)
    notes: str | None = None


class SubcontractorWorkerQualificationUpdate(BaseModel):
    certificate_no: str | None = Field(default=None, max_length=120)
    issued_at: date | None = None
    valid_until: date | None = None
    issuing_authority: str | None = Field(default=None, max_length=255)
    notes: str | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class SubcontractorWorkerQualificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    worker_id: str
    qualification_type_id: str
    qualification_type_code: str | None = None
    qualification_type_label: str | None = None
    certificate_no: str | None
    issued_at: date | None
    valid_until: date | None
    issuing_authority: str | None
    notes: str | None
    status: str
    archived_at: datetime | None
    version_no: int
    proofs: list[SubcontractorWorkerQualificationProofRead] = Field(default_factory=list)


class SubcontractorWorkerQualificationProofUpload(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    file_name: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=1, max_length=255)
    content_base64: str = Field(min_length=1)


class SubcontractorWorkerQualificationProofLinkCreate(BaseModel):
    document_id: str
    label: str | None = None


class SubcontractorWorkerCredentialCreate(BaseModel):
    tenant_id: str
    subcontractor_id: str
    worker_id: str
    credential_no: str = Field(min_length=1, max_length=120)
    credential_type: str = Field(min_length=1, max_length=40)
    encoded_value: str = Field(min_length=1, max_length=255)
    valid_from: date
    valid_until: date | None = None
    notes: str | None = None


class SubcontractorWorkerCredentialUpdate(BaseModel):
    encoded_value: str | None = Field(default=None, min_length=1, max_length=255)
    valid_from: date | None = None
    valid_until: date | None = None
    notes: str | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class SubcontractorWorkerCredentialRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    worker_id: str
    credential_no: str
    credential_type: str
    encoded_value: str
    valid_from: date
    valid_until: date | None
    issued_at: datetime | None
    revoked_at: datetime | None
    notes: str | None
    status: str
    archived_at: datetime | None
    version_no: int


class SubcontractorWorkerRead(SubcontractorWorkerListItem):
    model_config = ConfigDict(from_attributes=True)

    birth_date: date | None
    phone: str | None
    notes: str | None
    qualifications: list[SubcontractorWorkerQualificationRead] = Field(default_factory=list)
    credentials: list[SubcontractorWorkerCredentialRead] = Field(default_factory=list)
