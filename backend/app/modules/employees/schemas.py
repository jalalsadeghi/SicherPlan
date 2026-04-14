"""Pydantic DTOs for operational, HR-private, note, and employee-file flows."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from app.modules.core.schemas import AddressCreate, AddressRead


class EmployeeFilter(BaseModel):
    search: str | None = None
    status: str | None = None
    default_branch_id: str | None = None
    default_mandate_id: str | None = None
    include_archived: bool = False


class EmployeeOperationalCreate(BaseModel):
    tenant_id: str
    personnel_no: str = Field(min_length=1, max_length=50)
    first_name: str = Field(min_length=1, max_length=120)
    last_name: str = Field(min_length=1, max_length=120)
    preferred_name: str | None = Field(default=None, max_length=120)
    work_email: str | None = Field(default=None, max_length=255)
    work_phone: str | None = Field(default=None, max_length=64)
    mobile_phone: str | None = Field(default=None, max_length=64)
    default_branch_id: str | None = None
    default_mandate_id: str | None = None
    hire_date: date | None = None
    termination_date: date | None = None
    status: str | None = Field(default=None, max_length=40)
    employment_type_code: str | None = Field(default=None, max_length=80)
    target_weekly_hours: float | None = None
    target_monthly_hours: float | None = None
    user_id: str | None = None
    notes: str | None = None


class EmployeeOperationalUpdate(BaseModel):
    personnel_no: str | None = Field(default=None, min_length=1, max_length=50)
    first_name: str | None = Field(default=None, min_length=1, max_length=120)
    last_name: str | None = Field(default=None, min_length=1, max_length=120)
    preferred_name: str | None = Field(default=None, max_length=120)
    work_email: str | None = Field(default=None, max_length=255)
    work_phone: str | None = Field(default=None, max_length=64)
    mobile_phone: str | None = Field(default=None, max_length=64)
    default_branch_id: str | None = None
    default_mandate_id: str | None = None
    hire_date: date | None = None
    termination_date: date | None = None
    employment_type_code: str | None = Field(default=None, max_length=80)
    target_weekly_hours: float | None = None
    target_monthly_hours: float | None = None
    user_id: str | None = None
    notes: str | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class EmployeeListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    personnel_no: str
    first_name: str
    last_name: str
    preferred_name: str | None
    work_email: str | None
    mobile_phone: str | None
    default_branch_id: str | None
    default_mandate_id: str | None
    hire_date: date | None
    termination_date: date | None
    status: str
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None
    version_no: int


class EmployeeOperationalRead(EmployeeListItem):
    model_config = ConfigDict(from_attributes=True)

    work_phone: str | None
    employment_type_code: str | None
    target_weekly_hours: float | None
    target_monthly_hours: float | None
    user_id: str | None
    notes: str | None
    group_memberships: list["EmployeeGroupMemberRead"] = Field(default_factory=list)


class EmployeePrivateProfileCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    tenant_id: str
    employee_id: str
    private_email: str | None = Field(default=None, max_length=255)
    private_phone: str | None = Field(default=None, max_length=64)
    birth_date: date | None = None
    place_of_birth: str | None = Field(default=None, max_length=255)
    nationality_country_code: str | None = Field(default=None, max_length=2)
    marital_status_code: str | None = Field(
        default=None,
        max_length=80,
        validation_alias=AliasChoices("marital_status_code", "marital_status"),
    )
    tax_id: str | None = Field(default=None, max_length=80)
    social_security_no: str | None = Field(default=None, max_length=80)
    bank_account_holder: str | None = Field(default=None, max_length=255)
    bank_iban: str | None = Field(default=None, max_length=64)
    bank_bic: str | None = Field(default=None, max_length=64)
    emergency_contact_name: str | None = Field(default=None, max_length=255)
    emergency_contact_phone: str | None = Field(default=None, max_length=64)
    notes: str | None = None


class EmployeePrivateProfileUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    private_email: str | None = Field(default=None, max_length=255)
    private_phone: str | None = Field(default=None, max_length=64)
    birth_date: date | None = None
    place_of_birth: str | None = Field(default=None, max_length=255)
    nationality_country_code: str | None = Field(default=None, max_length=2)
    marital_status_code: str | None = Field(
        default=None,
        max_length=80,
        validation_alias=AliasChoices("marital_status_code", "marital_status"),
    )
    tax_id: str | None = Field(default=None, max_length=80)
    social_security_no: str | None = Field(default=None, max_length=80)
    bank_account_holder: str | None = Field(default=None, max_length=255)
    bank_iban: str | None = Field(default=None, max_length=64)
    bank_bic: str | None = Field(default=None, max_length=64)
    emergency_contact_name: str | None = Field(default=None, max_length=255)
    emergency_contact_phone: str | None = Field(default=None, max_length=64)
    notes: str | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class EmployeePrivateProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    employee_id: str
    private_email: str | None
    private_phone: str | None
    birth_date: date | None
    place_of_birth: str | None
    nationality_country_code: str | None
    marital_status_code: str | None
    tax_id: str | None
    social_security_no: str | None
    bank_account_holder: str | None
    bank_iban: str | None
    bank_bic: str | None
    emergency_contact_name: str | None
    emergency_contact_phone: str | None
    notes: str | None
    status: str
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None
    version_no: int


class EmployeeAddressWriteAddress(BaseModel):
    street_line_1: str
    street_line_2: str | None = None
    postal_code: str
    city: str
    state_region: str | None = None
    country_code: str = Field(min_length=2, max_length=2)


class EmployeeAddressHistoryCreate(BaseModel):
    tenant_id: str
    employee_id: str
    address_id: str | None = None
    address: EmployeeAddressWriteAddress | None = None
    address_type: str = Field(default="home", max_length=40)
    valid_from: date
    valid_to: date | None = None
    is_primary: bool = True
    notes: str | None = None


class EmployeeAddressHistoryUpdate(BaseModel):
    address_id: str | None = None
    address: EmployeeAddressWriteAddress | None = None
    address_type: str | None = Field(default=None, max_length=40)
    valid_from: date | None = None
    valid_to: date | None = None
    is_primary: bool | None = None
    notes: str | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class EmployeeAddressHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    employee_id: str
    address_id: str
    address_type: str
    valid_from: date
    valid_to: date | None
    is_primary: bool
    notes: str | None
    address: AddressRead | None = None
    status: str
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None
    version_no: int


class EmployeeGroupCreate(BaseModel):
    tenant_id: str
    code: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None


class EmployeeGroupUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=80)
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class EmployeeGroupRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    code: str
    name: str
    description: str | None
    status: str
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None
    version_no: int


class EmployeeGroupMemberCreate(BaseModel):
    tenant_id: str
    employee_id: str
    group_id: str
    valid_from: date
    valid_until: date | None = None
    notes: str | None = None


class EmployeeGroupMemberUpdate(BaseModel):
    valid_from: date | None = None
    valid_until: date | None = None
    notes: str | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class EmployeeGroupMemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    employee_id: str
    group_id: str
    valid_from: date
    valid_until: date | None
    notes: str | None
    status: str
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None
    version_no: int
    group: EmployeeGroupRead | None = None


class EmployeeNoteCreate(BaseModel):
    tenant_id: str
    employee_id: str
    note_type: str = Field(default="operational_note", max_length=40)
    title: str = Field(min_length=1, max_length=255)
    body: str | None = None
    reminder_at: date | None = None


class EmployeeNoteUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    body: str | None = None
    reminder_at: date | None = None
    completed_at: date | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class EmployeeNoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    employee_id: str
    note_type: str
    title: str
    body: str | None
    reminder_at: date | None
    completed_at: date | None
    completed_by_user_id: str | None
    status: str
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None
    version_no: int


class EmployeeDocumentListItemRead(BaseModel):
    document_id: str
    relation_type: str
    label: str | None
    title: str
    document_type_key: str | None
    file_name: str | None
    content_type: str | None
    current_version_no: int | None
    linked_at: datetime | None


class EmployeeDocumentUploadCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    relation_type: str = Field(default="employee_document", min_length=1, max_length=80)
    label: str | None = Field(default=None, max_length=255)
    document_type_key: str | None = Field(default=None, max_length=120)
    file_name: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=1, max_length=255)
    content_base64: str = Field(min_length=1)
    is_revision_safe_pdf: bool = False


class EmployeeDocumentLinkCreate(BaseModel):
    document_id: str = Field(min_length=1, max_length=36)
    relation_type: str = Field(default="employee_document", min_length=1, max_length=80)
    label: str | None = Field(default=None, max_length=255)


class EmployeeDocumentVersionCreate(BaseModel):
    file_name: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=1, max_length=255)
    content_base64: str = Field(min_length=1)
    is_revision_safe_pdf: bool = False


class EmployeePhotoUpload(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    file_name: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=1, max_length=255)
    content_base64: str = Field(min_length=1)


class EmployeePhotoRead(EmployeeDocumentListItemRead):
    pass


class EmployeeImportDryRunRequest(BaseModel):
    tenant_id: str
    csv_content_base64: str = Field(min_length=1)


class EmployeeImportExecuteRequest(EmployeeImportDryRunRequest):
    continue_on_error: bool = True


class EmployeeImportRowResult(BaseModel):
    row_no: int
    personnel_no: str | None = None
    status: str
    messages: list[str] = Field(default_factory=list)
    employee_id: str | None = None


class EmployeeImportDryRunResult(BaseModel):
    tenant_id: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    rows: list[EmployeeImportRowResult]


class EmployeeImportExecuteResult(BaseModel):
    tenant_id: str
    job_id: str
    job_status: str
    total_rows: int
    invalid_rows: int
    created_employees: int
    updated_employees: int
    linked_users: int
    result_document_ids: list[str] = Field(default_factory=list)
    rows: list[EmployeeImportRowResult]


class EmployeeExportRequest(BaseModel):
    tenant_id: str
    search: str | None = None
    include_archived: bool = False


class EmployeeExportResult(BaseModel):
    tenant_id: str
    job_id: str
    document_id: str
    file_name: str
    row_count: int


class EmployeeAccessLinkRead(BaseModel):
    employee_id: str
    tenant_id: str
    user_id: str | None
    username: str | None
    email: str | None
    full_name: str | None
    app_access_enabled: bool
    role_assignment_active: bool


class EmployeeAccessCreateUserRequest(BaseModel):
    tenant_id: str
    username: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=10, max_length=255)
    full_name: str | None = Field(default=None, max_length=255)
    locale: str | None = Field(default=None, max_length=10)
    timezone: str | None = Field(default=None, max_length=64)


class EmployeeAccessAttachExistingRequest(BaseModel):
    tenant_id: str
    user_id: str | None = None
    username: str | None = Field(default=None, max_length=120)
    email: str | None = Field(default=None, max_length=255)


class EmployeeAccessUpdateUserRequest(BaseModel):
    tenant_id: str
    username: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=1, max_length=255)
    full_name: str = Field(min_length=1, max_length=255)


class EmployeeAccessResetPasswordRequest(BaseModel):
    tenant_id: str
    password: str = Field(min_length=10, max_length=255)


class EmployeeAccessDetachRequest(BaseModel):
    tenant_id: str


class EmployeeLifecycleTransitionRequest(BaseModel):
    version_no: int


class FunctionTypeCreate(BaseModel):
    tenant_id: str
    code: str = Field(min_length=1, max_length=80)
    label: str = Field(min_length=1, max_length=255)
    category: str | None = Field(default=None, max_length=120)
    description: str | None = None
    is_active: bool = True
    planning_relevant: bool = True


class FunctionTypeUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=80)
    label: str | None = Field(default=None, min_length=1, max_length=255)
    category: str | None = Field(default=None, max_length=120)
    description: str | None = None
    is_active: bool | None = None
    planning_relevant: bool | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class FunctionTypeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    code: str
    label: str
    category: str | None
    description: str | None
    is_active: bool
    planning_relevant: bool
    status: str
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None
    version_no: int


class QualificationTypeCreate(BaseModel):
    tenant_id: str
    code: str = Field(min_length=1, max_length=80)
    label: str = Field(min_length=1, max_length=255)
    category: str | None = Field(default=None, max_length=120)
    description: str | None = None
    is_active: bool = True
    planning_relevant: bool = True
    compliance_relevant: bool = False
    expiry_required: bool = False
    default_validity_days: int | None = None
    proof_required: bool = False


class QualificationTypeUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=80)
    label: str | None = Field(default=None, min_length=1, max_length=255)
    category: str | None = Field(default=None, max_length=120)
    description: str | None = None
    is_active: bool | None = None
    planning_relevant: bool | None = None
    compliance_relevant: bool | None = None
    expiry_required: bool | None = None
    default_validity_days: int | None = None
    proof_required: bool | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class QualificationTypeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    code: str
    label: str
    category: str | None
    description: str | None
    is_active: bool
    planning_relevant: bool
    compliance_relevant: bool
    expiry_required: bool
    default_validity_days: int | None
    proof_required: bool
    status: str
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None
    version_no: int


class EmployeeCatalogBootstrapRead(BaseModel):
    function_types_inserted: int
    function_types_updated: int
    qualification_types_inserted: int
    qualification_types_updated: int


class EmployeeQualificationFilter(BaseModel):
    employee_id: str | None = None
    record_kind: str | None = None
    qualification_type_id: str | None = None
    function_type_id: str | None = None
    include_archived: bool = False
    include_expired: bool = False
    valid_on: date | None = None


class EmployeeQualificationCreate(BaseModel):
    tenant_id: str
    employee_id: str
    record_kind: str = Field(min_length=1, max_length=40)
    function_type_id: str | None = None
    qualification_type_id: str | None = None
    certificate_no: str | None = Field(default=None, max_length=120)
    issued_at: date | None = None
    valid_until: date | None = None
    issuing_authority: str | None = Field(default=None, max_length=255)
    granted_internally: bool = False
    notes: str | None = None


class EmployeeQualificationUpdate(BaseModel):
    function_type_id: str | None = None
    qualification_type_id: str | None = None
    certificate_no: str | None = Field(default=None, max_length=120)
    issued_at: date | None = None
    valid_until: date | None = None
    issuing_authority: str | None = Field(default=None, max_length=255)
    granted_internally: bool | None = None
    notes: str | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class EmployeeQualificationProofUpload(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    file_name: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=1, max_length=255)
    content_base64: str = Field(min_length=1)


class EmployeeQualificationProofLinkCreate(BaseModel):
    document_id: str
    label: str | None = Field(default=None, max_length=255)


class EmployeeQualificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    employee_id: str
    record_kind: str
    function_type_id: str | None
    qualification_type_id: str | None
    certificate_no: str | None
    issued_at: date | None
    valid_until: date | None
    issuing_authority: str | None
    granted_internally: bool
    notes: str | None
    status: str
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None
    version_no: int
    function_type: FunctionTypeRead | None = None
    qualification_type: QualificationTypeRead | None = None


class EmployeeQualificationProofRead(EmployeeDocumentListItemRead):
    pass


class EmployeeAvailabilityRuleFilter(BaseModel):
    employee_id: str | None = None
    rule_kind: str | None = None
    status: str | None = None
    active_on: datetime | None = None
    include_archived: bool = False


class EmployeeAvailabilityRuleCreate(BaseModel):
    tenant_id: str
    employee_id: str
    rule_kind: str = Field(min_length=1, max_length=40)
    starts_at: datetime
    ends_at: datetime
    recurrence_type: str = Field(default="none", min_length=1, max_length=20)
    weekday_mask: str | None = Field(default=None, min_length=7, max_length=7)
    notes: str | None = None


class EmployeeAvailabilityRuleUpdate(BaseModel):
    rule_kind: str | None = Field(default=None, min_length=1, max_length=40)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    recurrence_type: str | None = Field(default=None, min_length=1, max_length=20)
    weekday_mask: str | None = Field(default=None, min_length=7, max_length=7)
    notes: str | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class EmployeeAvailabilityRuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    employee_id: str
    rule_kind: str
    starts_at: datetime
    ends_at: datetime
    recurrence_type: str
    weekday_mask: str | None
    notes: str | None
    status: str
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None
    version_no: int


class EmployeeAbsenceFilter(BaseModel):
    employee_id: str | None = None
    absence_type: str | None = None
    status: str | None = None
    starts_on_or_after: date | None = None
    ends_on_or_before: date | None = None
    include_archived: bool = False


class EmployeeAbsenceCreate(BaseModel):
    tenant_id: str
    employee_id: str
    absence_type: str = Field(min_length=1, max_length=40)
    starts_on: date
    ends_on: date
    notes: str | None = None


class EmployeeAbsenceUpdate(BaseModel):
    absence_type: str | None = Field(default=None, min_length=1, max_length=40)
    starts_on: date | None = None
    ends_on: date | None = None
    status: str | None = None
    decision_note: str | None = None
    notes: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class EmployeeAbsenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    employee_id: str
    absence_type: str
    starts_on: date
    ends_on: date
    quantity_days: float
    status: str
    requested_at: datetime
    approved_by_user_id: str | None
    approved_at: datetime | None
    decision_note: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None
    version_no: int


class EmployeeLeaveBalanceFilter(BaseModel):
    employee_id: str | None = None
    balance_year: int | None = None
    include_archived: bool = False


class EmployeeLeaveBalanceUpsert(BaseModel):
    tenant_id: str
    employee_id: str
    balance_year: int
    entitlement_days: float = 0
    carry_over_days: float = 0
    manual_adjustment_days: float = 0
    notes: str | None = None


class EmployeeLeaveBalanceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    employee_id: str
    balance_year: int
    entitlement_days: float
    carry_over_days: float
    manual_adjustment_days: float
    consumed_days: float
    pending_days: float
    notes: str | None
    status: str
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None
    version_no: int


class EmployeeEventApplicationFilter(BaseModel):
    employee_id: str | None = None
    planning_record_id: str | None = None
    status: str | None = None
    include_archived: bool = False


class EmployeeEventApplicationCreate(BaseModel):
    tenant_id: str
    employee_id: str
    planning_record_id: str
    note: str | None = None


class EmployeeEventApplicationUpdate(BaseModel):
    status: str | None = None
    note: str | None = None
    decision_note: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class EmployeeEventApplicationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    employee_id: str
    planning_record_id: str
    status: str
    applied_at: datetime
    decided_by_user_id: str | None
    decided_at: datetime | None
    note: str | None
    decision_note: str | None
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None
    version_no: int


class EmployeeTimeAccountFilter(BaseModel):
    employee_id: str | None = None
    account_type: str | None = None
    include_archived: bool = False


class EmployeeTimeAccountCreate(BaseModel):
    tenant_id: str
    employee_id: str
    account_type: str = Field(min_length=1, max_length=40)
    unit_code: str = Field(default="minutes", min_length=1, max_length=20)
    notes: str | None = None


class EmployeeTimeAccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    employee_id: str
    account_type: str
    unit_code: str
    notes: str | None
    status: str
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None
    version_no: int
    balance_minutes: int = 0


class EmployeeTimeAccountTxnCreate(BaseModel):
    tenant_id: str
    txn_type: str = Field(min_length=1, max_length=20)
    amount_minutes: int
    posted_at: datetime | None = None
    reference_type: str | None = Field(default=None, max_length=80)
    reference_id: str | None = None
    notes: str | None = None


class EmployeeTimeAccountTxnRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    time_account_id: str
    txn_type: str
    posted_at: datetime
    amount_minutes: int
    reference_type: str | None
    reference_id: str | None
    notes: str | None
    created_by_user_id: str | None


class EmployeeAllowanceFilter(BaseModel):
    employee_id: str | None = None
    basis_code: str | None = None
    function_type_id: str | None = None
    qualification_type_id: str | None = None
    active_on: date | None = None
    include_archived: bool = False


class EmployeeAllowanceCreate(BaseModel):
    tenant_id: str
    employee_id: str
    basis_code: str = Field(min_length=1, max_length=80)
    amount: float
    currency_code: str = Field(default="EUR", min_length=3, max_length=3)
    function_type_id: str | None = None
    qualification_type_id: str | None = None
    effective_from: date
    effective_until: date | None = None
    notes: str | None = None


class EmployeeAllowanceUpdate(BaseModel):
    basis_code: str | None = Field(default=None, min_length=1, max_length=80)
    amount: float | None = None
    currency_code: str | None = Field(default=None, min_length=3, max_length=3)
    function_type_id: str | None = None
    qualification_type_id: str | None = None
    effective_from: date | None = None
    effective_until: date | None = None
    notes: str | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class EmployeeAllowanceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    employee_id: str
    basis_code: str
    amount: float
    currency_code: str
    function_type_id: str | None
    qualification_type_id: str | None
    effective_from: date
    effective_until: date | None
    notes: str | None
    status: str
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None
    version_no: int
    function_type: FunctionTypeRead | None = None
    qualification_type: QualificationTypeRead | None = None


class EmployeeAdvanceFilter(BaseModel):
    employee_id: str | None = None
    status: str | None = None
    include_archived: bool = False


class EmployeeAdvanceCreate(BaseModel):
    tenant_id: str
    employee_id: str
    advance_no: str = Field(min_length=1, max_length=80)
    amount: float
    currency_code: str = Field(default="EUR", min_length=3, max_length=3)
    requested_on: date
    notes: str | None = None


class EmployeeAdvanceUpdate(BaseModel):
    status: str | None = None
    outstanding_amount: float | None = None
    disbursed_on: date | None = None
    settled_on: date | None = None
    notes: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class EmployeeAdvanceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    employee_id: str
    advance_no: str
    amount: float
    outstanding_amount: float
    currency_code: str
    status: str
    requested_on: date
    disbursed_on: date | None
    settled_on: date | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None
    version_no: int


class EmployeeCredentialFilter(BaseModel):
    employee_id: str | None = None
    credential_type: str | None = None
    status: str | None = None
    active_on: date | None = None
    include_archived: bool = False


class EmployeeCredentialCreate(BaseModel):
    tenant_id: str
    employee_id: str
    credential_no: str = Field(min_length=1, max_length=120)
    credential_type: str = Field(min_length=1, max_length=40)
    encoded_value: str = Field(min_length=1, max_length=255)
    valid_from: date
    valid_until: date | None = None
    notes: str | None = None


class EmployeeCredentialUpdate(BaseModel):
    status: str | None = None
    encoded_value: str | None = Field(default=None, min_length=1, max_length=255)
    valid_from: date | None = None
    valid_until: date | None = None
    notes: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class EmployeeCredentialRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    employee_id: str
    credential_no: str
    credential_type: str
    encoded_value: str
    valid_from: date
    valid_until: date | None
    status: str
    issued_at: datetime | None
    revoked_at: datetime | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None
    version_no: int


class EmployeeCredentialBadgeIssue(BaseModel):
    title: str | None = Field(default=None, max_length=255)


class EmployeeCredentialBadgeRead(EmployeeDocumentListItemRead):
    pass


class EmployeeSelfServiceProfileRead(BaseModel):
    employee_id: str
    tenant_id: str
    personnel_no: str
    first_name: str
    last_name: str
    preferred_name: str | None
    work_email: str | None
    mobile_phone: str | None
    active_home_address: AddressRead | None = None


class EmployeeSelfServiceProfileUpdate(BaseModel):
    preferred_name: str | None = Field(default=None, max_length=120)
    work_email: str | None = Field(default=None, max_length=255)
    mobile_phone: str | None = Field(default=None, max_length=64)


class EmployeeSelfServiceAddressUpdate(BaseModel):
    effective_from: date
    address: AddressCreate
    notes: str | None = None


class EmployeeSelfServiceAvailabilityRuleCreate(BaseModel):
    rule_kind: str = Field(min_length=1, max_length=40)
    starts_at: datetime
    ends_at: datetime
    recurrence_type: str = Field(default="none", min_length=1, max_length=20)
    weekday_mask: str | None = Field(default=None, min_length=7, max_length=7)
    notes: str | None = None


class EmployeeSelfServiceAvailabilityRuleUpdate(BaseModel):
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    recurrence_type: str | None = Field(default=None, min_length=1, max_length=20)
    weekday_mask: str | None = Field(default=None, min_length=7, max_length=7)
    notes: str | None = None
    status: str | None = None
    version_no: int | None = None


class EmployeeSelfServiceEventApplicationCreate(BaseModel):
    planning_record_id: str
    note: str | None = None


class EmployeeSelfServiceEventApplicationCancel(BaseModel):
    decision_note: str | None = None
    version_no: int | None = None


class EmployeeMobileContextRead(BaseModel):
    tenant_id: str
    user_id: str
    employee_id: str
    personnel_no: str
    full_name: str
    preferred_name: str | None = None
    work_email: str | None = None
    mobile_phone: str | None = None
    default_branch_id: str | None = None
    default_mandate_id: str | None = None
    locale: str = "de"
    timezone: str = "Europe/Berlin"
    app_role: str = "employee"
    role_keys: list[str] = Field(default_factory=list)
    has_schedule_access: bool = True
    has_document_access: bool = True
    has_notice_access: bool = True
    has_time_capture_access: bool = True
    has_watchbook_access: bool = True
    has_patrol_access: bool = True


class EmployeeReleasedScheduleDocumentRead(BaseModel):
    document_id: str
    title: str
    file_name: str | None = None
    content_type: str | None = None
    current_version_no: int | None = None
    relation_type: str = "deployment_output"


class EmployeeReleasedScheduleRead(BaseModel):
    id: str
    employee_id: str
    shift_id: str
    planning_record_id: str | None = None
    order_id: str | None = None
    site_id: str | None = None
    schedule_date: date
    shift_label: str
    work_start: datetime
    work_end: datetime
    location_label: str | None = None
    meeting_point: str | None = None
    assignment_status: str
    confirmation_status: str
    documents: list[EmployeeReleasedScheduleDocumentRead] = Field(default_factory=list)


class EmployeeReleasedScheduleCollectionRead(BaseModel):
    employee_id: str
    tenant_id: str
    released_only: bool = True
    items: list[EmployeeReleasedScheduleRead] = Field(default_factory=list)


class EmployeeReleasedScheduleResponseRequest(BaseModel):
    response_code: str = Field(min_length=1, max_length=20)
    note: str | None = Field(default=None, max_length=1000)
    version_no: int | None = None


class EmployeeMobileDocumentRead(BaseModel):
    document_id: str
    owner_type: str
    owner_id: str
    relation_type: str
    title: str
    file_name: str | None = None
    content_type: str | None = None
    current_version_no: int | None = None
    linked_at: datetime | None = None
    schedule_date: date | None = None
    shift_id: str | None = None


class EmployeeMobileDocumentCollectionRead(BaseModel):
    employee_id: str
    tenant_id: str
    items: list[EmployeeMobileDocumentRead] = Field(default_factory=list)


class EmployeeMobileCredentialRead(BaseModel):
    credential_id: str
    credential_no: str
    credential_type: str
    encoded_value: str
    valid_from: date
    valid_until: date | None = None
    status: str
    badge_document_id: str | None = None
    badge_file_name: str | None = None


class EmployeeMobileCredentialCollectionRead(BaseModel):
    employee_id: str
    tenant_id: str
    items: list[EmployeeMobileCredentialRead] = Field(default_factory=list)
