"""Read-only partner contracts for downstream planning, field, and finance consumers."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class SubcontractorDownstreamFilter(BaseModel):
    search: str | None = None
    branch_id: str | None = None
    mandate_id: str | None = None


class SubcontractorWorkerDownstreamFilter(BaseModel):
    search: str | None = None
    qualification_type_id: str | None = None
    credential_type: str | None = None
    ready_only: bool = False


class SubcontractorScopeContractRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    branch_id: str
    mandate_id: str | None
    valid_from: str
    valid_to: str | None


class SubcontractorPortalContactContractRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    contact_id: str
    full_name: str
    function_label: str | None
    email: str | None
    is_primary_contact: bool
    portal_enabled: bool


class SubcontractorReadinessIssueContractRead(BaseModel):
    issue_code: str
    message_key: str
    severity: str
    category: str
    reference_type: str
    reference_id: str | None
    due_on: str | None


class SubcontractorWorkerQualificationContractRead(BaseModel):
    qualification_id: str
    qualification_type_id: str
    qualification_type_code: str | None
    qualification_type_label: str | None
    valid_until: str | None
    compliance_relevant: bool
    proof_required: bool


class SubcontractorWorkerCredentialContractRead(BaseModel):
    credential_id: str
    credential_no: str
    credential_type: str
    valid_from: str
    valid_until: str | None
    status: str


class SubcontractorReadinessSummaryContractRead(BaseModel):
    readiness_status: str
    is_ready: bool
    blocking_issue_count: int
    warning_issue_count: int
    missing_proof_count: int
    expired_qualification_count: int
    expiring_qualification_count: int
    missing_credential_count: int
    issues: list[SubcontractorReadinessIssueContractRead]


class SubcontractorWorkerContractRead(BaseModel):
    worker_id: str
    subcontractor_id: str
    worker_no: str
    first_name: str
    last_name: str
    preferred_name: str | None
    status: str
    qualifications: list[SubcontractorWorkerQualificationContractRead]
    credentials: list[SubcontractorWorkerCredentialContractRead]
    readiness: SubcontractorReadinessSummaryContractRead


class SubcontractorPartnerContractRead(BaseModel):
    subcontractor_id: str
    subcontractor_number: str
    legal_name: str
    display_name: str | None
    managing_director_name: str | None
    status: str
    scopes: list[SubcontractorScopeContractRead]
    portal_contacts: list[SubcontractorPortalContactContractRead]
    readiness_summary: dict[str, int | str]


class SubcontractorCommercialSummaryRead(BaseModel):
    subcontractor_id: str
    subcontractor_number: str
    legal_name: str
    display_name: str | None
    invoice_email: str | None
    payment_terms_days: int | None
    payment_terms_note: str | None
    invoice_delivery_method_lookup_id: str | None
    invoice_delivery_method_code: str | None
    invoice_delivery_method_label: str | None
    invoice_status_mode_lookup_id: str | None
    invoice_status_mode_code: str | None
    invoice_status_mode_label: str | None
    billing_note: str | None
    primary_contact_name: str | None
    primary_contact_email: str | None
    readiness_summary: dict[str, int | str]


class SubcontractorCredentialResolutionRead(BaseModel):
    subcontractor_id: str
    subcontractor_number: str
    legal_name: str
    worker_id: str
    worker_no: str
    first_name: str
    last_name: str
    preferred_name: str | None
    credential_id: str
    credential_no: str
    credential_type: str
    credential_status: str
    valid_from: str
    valid_until: str | None
    readiness: SubcontractorReadinessSummaryContractRead
