"""Pydantic schemas for public applicant intake and workflow."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ApplicantFieldType = Literal["date", "email", "select", "tel", "text", "textarea"]


class PublicApplicantFieldOption(BaseModel):
    value: str
    label_de: str
    label_en: str


class PublicApplicantExtraFieldSetting(BaseModel):
    key: str = Field(min_length=2, max_length=80)
    type: ApplicantFieldType = "text"
    label_de: str = Field(min_length=1, max_length=160)
    label_en: str = Field(min_length=1, max_length=160)
    visible: bool = True
    required: bool = False
    options: list[PublicApplicantFieldOption] = Field(default_factory=list)


class PublicApplicantFormSetting(BaseModel):
    enabled: bool = True
    source_channel: str = "public_form"
    source_detail: str | None = None
    default_locale: Literal["de", "en"] = "de"
    allowed_embed_origins: list[str] = Field(default_factory=list)
    required_fields: list[str] = Field(default_factory=lambda: ["first_name", "last_name", "email"])
    hidden_fields: list[str] = Field(default_factory=list)
    additional_fields: list[PublicApplicantExtraFieldSetting] = Field(default_factory=list)
    allowed_attachment_types: list[str] = Field(
        default_factory=lambda: [
            "application/pdf",
            "image/jpeg",
            "image/png",
        ]
    )
    max_attachment_size_bytes: int = 5 * 1024 * 1024
    max_attachment_count: int = 3
    gdpr_policy_ref: str = "privacy-policy"
    gdpr_policy_version: str = "v1"
    gdpr_policy_url_de: str | None = None
    gdpr_policy_url_en: str | None = None


class PublicApplicantFormFieldRead(BaseModel):
    key: str
    type: ApplicantFieldType
    label_de: str
    label_en: str
    visible: bool
    required: bool
    options: list[PublicApplicantFieldOption] = Field(default_factory=list)


class PublicApplicantFormConfigRead(BaseModel):
    tenant_id: str
    tenant_code: str
    tenant_name: str
    default_locale: Literal["de", "en"] = "de"
    source_channel: str
    source_detail: str | None = None
    gdpr_policy_ref: str
    gdpr_policy_version: str
    gdpr_policy_url_de: str | None = None
    gdpr_policy_url_en: str | None = None
    max_attachment_count: int
    max_attachment_size_bytes: int
    allowed_attachment_types: list[str]
    allowed_embed_origins: list[str]
    fields: list[PublicApplicantFormFieldRead]
    confirmation_message_key: str = "recruitingApplicant.feedback.submitted"


class PublicApplicantAttachmentCreate(BaseModel):
    kind: str = Field(min_length=2, max_length=80)
    file_name: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=1, max_length=255)
    content_base64: str = Field(min_length=1)
    label: str | None = Field(default=None, max_length=255)


class PublicApplicantSubmissionCreate(BaseModel):
    submission_key: str = Field(min_length=12, max_length=80)
    locale: Literal["de", "en"] = "de"
    first_name: str | None = Field(default=None, max_length=120)
    last_name: str | None = Field(default=None, max_length=120)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=64)
    desired_role: str | None = Field(default=None, max_length=255)
    availability_date: date | None = None
    message: str | None = Field(default=None, max_length=4000)
    additional_fields: dict[str, object] = Field(default_factory=dict)
    attachments: list[PublicApplicantAttachmentCreate] = Field(default_factory=list)
    gdpr_consent_confirmed: bool = False
    gdpr_policy_ref: str = Field(min_length=1, max_length=255)
    gdpr_policy_version: str = Field(min_length=1, max_length=80)


class PublicApplicantSubmissionResponse(BaseModel):
    applicant_id: str
    application_no: str
    status: str
    message_key: str


class ApplicantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    application_no: str
    submission_key: str
    source_channel: str
    source_detail: str | None
    locale: str
    converted_employee_id: str | None
    first_name: str
    last_name: str
    email: str
    phone: str | None
    desired_role: str | None
    availability_date: date | None
    message: str | None
    gdpr_consent_granted: bool
    gdpr_consent_at: datetime
    gdpr_policy_ref: str
    gdpr_policy_version: str
    custom_fields_json: dict[str, object]
    metadata_json: dict[str, object]
    submitted_ip: str | None
    submitted_origin: str | None
    submitted_user_agent: str | None
    status: str
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None
    version_no: int


ApplicantStatus = Literal[
    "submitted",
    "in_review",
    "interview_scheduled",
    "accepted",
    "rejected",
    "ready_for_conversion",
]

ApplicantActivityType = Literal[
    "status_transition",
    "interview_scheduled",
    "decision",
    "reopened",
    "ready_for_conversion",
    "converted",
    "recruiter_note",
    "interview_note",
]


class ApplicantListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    application_no: str
    source_channel: str
    source_detail: str | None
    locale: str
    converted_employee_id: str | None
    first_name: str
    last_name: str
    email: str
    desired_role: str | None
    availability_date: date | None
    status: str
    created_at: datetime
    updated_at: datetime
    version_no: int


class ApplicantTransitionRequest(BaseModel):
    to_status: ApplicantStatus
    note: str | None = Field(default=None, max_length=4000)
    decision_reason: str | None = Field(default=None, max_length=4000)
    interview_scheduled_at: datetime | None = None
    hiring_target_date: date | None = None


class ApplicantActivityCreate(BaseModel):
    activity_type: Literal["recruiter_note", "interview_note"]
    note: str = Field(min_length=1, max_length=4000)
    decision_reason: str | None = Field(default=None, max_length=4000)
    interview_scheduled_at: datetime | None = None
    hiring_target_date: date | None = None


class ApplicantActivityEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    applicant_id: str
    event_type: str
    from_status: str | None
    to_status: str | None
    note: str | None
    decision_reason: str | None
    interview_scheduled_at: datetime | None
    hiring_target_date: date | None
    metadata_json: dict[str, object]
    actor_user_id: str | None
    created_at: datetime


class ApplicantTimelineRead(BaseModel):
    applicant: ApplicantListItem
    events: list[ApplicantActivityEventRead]


class ApplicantAttachmentRead(BaseModel):
    document_id: str
    relation_type: str
    label: str | None
    title: str
    document_type_key: str | None
    file_name: str | None
    content_type: str | None
    current_version_no: int | None
    linked_at: datetime | None = None


class ApplicantConsentEvidenceRead(BaseModel):
    consent_granted: bool
    consent_at: datetime
    policy_ref: str
    policy_version: str
    submitted_origin: str | None
    submitted_ip: str | None
    submitted_user_agent: str | None


class ApplicantDetailRead(BaseModel):
    applicant: ApplicantRead
    consent: ApplicantConsentEvidenceRead
    attachments: list[ApplicantAttachmentRead]
    events: list[ApplicantActivityEventRead]
    next_allowed_statuses: list[ApplicantStatus]


class ApplicantConversionRead(BaseModel):
    applicant_id: str
    employee_id: str
    personnel_no: str
    applicant_status: str
    already_converted: bool = False
    converted_event_id: str | None = None
