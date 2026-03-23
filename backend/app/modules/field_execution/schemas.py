"""Pydantic schemas for watchbooks and released outputs."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.platform_services.docs_schemas import DocumentRead


class WatchbookOpenRequest(BaseModel):
    tenant_id: str
    context_type: str
    log_date: date
    site_id: str | None = None
    order_id: str | None = None
    planning_record_id: str | None = None
    shift_id: str | None = None
    headline: str | None = None
    summary: str | None = None


class WatchbookEntryCreate(BaseModel):
    occurred_at: datetime | None = None
    entry_type_code: str
    narrative: str
    traffic_light_code: str | None = None
    assignment_id: str | None = None
    attachment_document_ids: list[str] = Field(default_factory=list)


class WatchbookReviewRequest(BaseModel):
    supervisor_note: str | None = None
    version_no: int | None = None


class WatchbookVisibilityUpdate(BaseModel):
    customer_visibility_released: bool | None = None
    subcontractor_visibility_released: bool | None = None
    customer_participation_enabled: bool | None = None
    subcontractor_participation_enabled: bool | None = None
    customer_personal_names_released: bool | None = None
    subcontractor_id: str | None = None
    version_no: int | None = None


class WatchbookEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    watchbook_id: str
    assignment_id: str | None
    occurred_at: datetime
    entry_type_code: str
    narrative: str
    traffic_light_code: str | None
    author_user_id: str
    author_actor_type: str
    created_at: datetime
    attachment_document_ids: list[str] = Field(default_factory=list)


class WatchbookRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    customer_id: str
    context_type: str
    log_date: date
    site_id: str | None
    order_id: str | None
    planning_record_id: str | None
    shift_id: str | None
    headline: str | None
    summary: str | None
    review_status_code: str
    reviewed_at: datetime | None
    supervisor_user_id: str | None
    supervisor_note: str | None
    closure_state_code: str
    closed_at: datetime | None
    closed_by_user_id: str | None
    pdf_document_id: str | None
    customer_visibility_released: bool
    subcontractor_visibility_released: bool
    customer_participation_enabled: bool
    subcontractor_participation_enabled: bool
    customer_personal_names_released: bool
    subcontractor_id: str | None
    status: str
    version_no: int
    created_at: datetime
    updated_at: datetime
    entries: list[WatchbookEntryRead] = Field(default_factory=list)


class WatchbookListItem(BaseModel):
    id: str
    context_type: str
    log_date: date
    headline: str | None
    review_status_code: str
    closure_state_code: str
    customer_visibility_released: bool
    subcontractor_visibility_released: bool
    customer_participation_enabled: bool
    subcontractor_participation_enabled: bool
    updated_at: datetime


class WatchbookListFilter(BaseModel):
    context_type: str | None = None
    site_id: str | None = None
    order_id: str | None = None
    planning_record_id: str | None = None
    shift_id: str | None = None
    log_date_from: date | None = None
    log_date_to: date | None = None
    closure_state_code: str | None = None
    review_status_code: str | None = None
    released_to_customer: bool | None = None
    released_to_subcontractor: bool | None = None


class WatchbookPdfRead(BaseModel):
    watchbook_id: str
    document: DocumentRead
    generated_at: datetime


class ReleasedWatchbookDocumentRead(BaseModel):
    document_id: str
    title: str
    file_name: str | None = None
    content_type: str | None = None
    current_version_no: int | None = None


class ReleasedWatchbookEntryRead(BaseModel):
    id: str
    occurred_at: datetime
    entry_type_code: str
    summary: str
    traffic_light_code: str | None = None


class ReleasedCustomerWatchbookRead(BaseModel):
    id: str
    customer_id: str
    log_date: date
    context_type: str
    headline: str | None
    summary: str | None
    reviewed_at: datetime | None
    closure_state_code: str
    pdf_document: ReleasedWatchbookDocumentRead | None = None
    entries: list[ReleasedWatchbookEntryRead] = Field(default_factory=list)


class ReleasedSubcontractorWatchbookRead(BaseModel):
    id: str
    subcontractor_id: str
    log_date: date
    context_type: str
    headline: str | None
    summary: str | None
    reviewed_at: datetime | None
    closure_state_code: str
    pdf_document: ReleasedWatchbookDocumentRead | None = None
    entries: list[ReleasedWatchbookEntryRead] = Field(default_factory=list)


class PatrolCheckpointProgressRead(BaseModel):
    checkpoint_id: str
    sequence_no: int
    checkpoint_code: str
    label: str
    scan_type_code: str
    minimum_dwell_seconds: int
    is_completed: bool
    last_event_at: datetime | None = None


class PatrolAvailableRouteRead(BaseModel):
    shift_id: str
    planning_record_id: str | None = None
    patrol_route_id: str
    route_no: str
    route_name: str
    schedule_date: date
    work_start: datetime
    work_end: datetime
    meeting_point: str | None = None
    location_label: str | None = None
    checkpoint_count: int
    checkpoints: list[PatrolCheckpointProgressRead] = Field(default_factory=list)


class PatrolRoundStartRequest(BaseModel):
    shift_id: str
    patrol_route_id: str
    offline_sync_token: str | None = Field(default=None, max_length=120)


class PatrolRoundCaptureAttachment(BaseModel):
    title: str | None = None
    file_name: str
    content_type: str
    content_base64: str


class PatrolRoundCaptureRequest(BaseModel):
    checkpoint_id: str | None = None
    scan_method_code: str
    token_value: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    note: str | None = None
    reason_code: str | None = None
    occurred_at: datetime | None = None
    offline_sequence_no: int | None = None
    client_event_id: str | None = Field(default=None, max_length=120)
    attachments: list[PatrolRoundCaptureAttachment] = Field(default_factory=list)


class PatrolRoundCompleteRequest(BaseModel):
    note: str | None = None
    occurred_at: datetime | None = None
    offline_sequence_no: int | None = None
    client_event_id: str | None = Field(default=None, max_length=120)


class PatrolRoundAbortRequest(BaseModel):
    abort_reason_code: str
    note: str | None = None
    occurred_at: datetime | None = None
    offline_sequence_no: int | None = None
    client_event_id: str | None = Field(default=None, max_length=120)
    attachments: list[PatrolRoundCaptureAttachment] = Field(default_factory=list)


class PatrolRoundEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    patrol_round_id: str
    sequence_no: int
    checkpoint_id: str | None
    occurred_at: datetime
    event_type_code: str
    scan_method_code: str | None
    token_value: str | None
    note: str | None
    reason_code: str | None
    actor_user_id: str
    is_policy_compliant: bool
    client_event_id: str | None
    attachment_document_ids: list[str] = Field(default_factory=list)


class PatrolRoundRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    employee_id: str
    shift_id: str
    planning_record_id: str | None
    patrol_route_id: str
    watchbook_id: str | None
    summary_document_id: str | None
    offline_sync_token: str | None
    round_status_code: str
    started_at: datetime
    completed_at: datetime | None
    aborted_at: datetime | None
    abort_reason_code: str | None
    completion_note: str | None
    total_checkpoint_count: int
    completed_checkpoint_count: int
    version_no: int
    events: list[PatrolRoundEventRead] = Field(default_factory=list)
    checkpoints: list[PatrolCheckpointProgressRead] = Field(default_factory=list)


class PatrolEvaluationRead(BaseModel):
    patrol_round_id: str
    tenant_id: str
    employee_id: str
    patrol_route_id: str
    round_status_code: str
    total_checkpoint_count: int
    completed_checkpoint_count: int
    exception_count: int
    manual_capture_count: int
    mismatch_count: int
    watchbook_id: str | None
    summary_document: ReleasedWatchbookDocumentRead | None = None
    completion_ratio: float
    compliance_status_code: str


class PatrolSyncEnvelope(BaseModel):
    round: PatrolRoundStartRequest
    events: list[PatrolRoundCaptureRequest] = Field(default_factory=list)
    complete_request: PatrolRoundCompleteRequest | None = None
    abort_request: PatrolRoundAbortRequest | None = None


class TimeCaptureDeviceCreate(BaseModel):
    device_code: str = Field(min_length=1, max_length=80)
    label: str = Field(min_length=1, max_length=255)
    device_type_code: str = Field(min_length=1, max_length=40)
    site_id: str | None = None
    access_key: str | None = Field(default=None, min_length=8, max_length=255)
    fixed_ip_cidr: str | None = Field(default=None, max_length=80)
    notes: str | None = None
    status: str = Field(default="active", min_length=1, max_length=20)


class TimeCaptureDeviceUpdate(BaseModel):
    label: str | None = Field(default=None, min_length=1, max_length=255)
    device_type_code: str | None = Field(default=None, min_length=1, max_length=40)
    site_id: str | None = None
    reset_site_link: bool = False
    access_key: str | None = Field(default=None, min_length=8, max_length=255)
    clear_access_key: bool = False
    fixed_ip_cidr: str | None = Field(default=None, max_length=80)
    clear_fixed_ip_cidr: bool = False
    notes: str | None = None
    status: str | None = Field(default=None, min_length=1, max_length=20)
    archived_at: datetime | None = None
    version_no: int | None = None


class TimeCaptureDeviceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    device_code: str
    label: str
    device_type_code: str
    site_id: str | None
    fixed_ip_cidr: str | None
    notes: str | None
    status: str
    has_access_key: bool = False
    archived_at: datetime | None
    version_no: int
    created_at: datetime
    updated_at: datetime


class TimeCaptureDeviceListItem(BaseModel):
    id: str
    device_code: str
    label: str
    device_type_code: str
    site_id: str | None
    fixed_ip_cidr: str | None
    status: str
    has_access_key: bool
    updated_at: datetime


class TimeCaptureDeviceFilter(BaseModel):
    site_id: str | None = None
    device_type_code: str | None = None
    status: str | None = None
    include_archived: bool = False


class TimeCapturePolicyCreate(BaseModel):
    policy_code: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=255)
    context_type_code: str = Field(min_length=1, max_length=40)
    site_id: str | None = None
    shift_id: str | None = None
    planning_record_id: str | None = None
    patrol_route_id: str | None = None
    allowed_device_id: str | None = None
    allowed_device_type_code: str | None = Field(default=None, max_length=40)
    allow_browser_capture: bool = True
    allow_mobile_capture: bool = True
    allow_terminal_capture: bool = True
    allowed_ip_cidr: str | None = Field(default=None, max_length=80)
    geofence_latitude: float | None = None
    geofence_longitude: float | None = None
    geofence_radius_meters: int | None = Field(default=None, ge=1)
    enforce_mode_code: str = Field(default="reject", min_length=1, max_length=20)
    notes: str | None = None
    status: str = Field(default="active", min_length=1, max_length=20)


class TimeCapturePolicyUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    allowed_device_id: str | None = None
    clear_allowed_device: bool = False
    allowed_device_type_code: str | None = Field(default=None, max_length=40)
    clear_allowed_device_type: bool = False
    allow_browser_capture: bool | None = None
    allow_mobile_capture: bool | None = None
    allow_terminal_capture: bool | None = None
    allowed_ip_cidr: str | None = Field(default=None, max_length=80)
    clear_allowed_ip_cidr: bool = False
    geofence_latitude: float | None = None
    geofence_longitude: float | None = None
    geofence_radius_meters: int | None = Field(default=None, ge=1)
    clear_geofence: bool = False
    enforce_mode_code: str | None = Field(default=None, min_length=1, max_length=20)
    notes: str | None = None
    status: str | None = Field(default=None, min_length=1, max_length=20)
    archived_at: datetime | None = None
    version_no: int | None = None


class TimeCapturePolicyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    policy_code: str
    title: str
    context_type_code: str
    site_id: str | None
    shift_id: str | None
    planning_record_id: str | None
    patrol_route_id: str | None
    allowed_device_id: str | None
    allowed_device_type_code: str | None
    allow_browser_capture: bool
    allow_mobile_capture: bool
    allow_terminal_capture: bool
    allowed_ip_cidr: str | None
    geofence_latitude: float | None
    geofence_longitude: float | None
    geofence_radius_meters: int | None
    enforce_mode_code: str
    notes: str | None
    status: str
    archived_at: datetime | None
    version_no: int
    created_at: datetime
    updated_at: datetime


class TimeCapturePolicyListItem(BaseModel):
    id: str
    policy_code: str
    title: str
    context_type_code: str
    site_id: str | None
    shift_id: str | None
    planning_record_id: str | None
    patrol_route_id: str | None
    enforce_mode_code: str
    status: str
    updated_at: datetime


class TimeCapturePolicyFilter(BaseModel):
    context_type_code: str | None = None
    site_id: str | None = None
    shift_id: str | None = None
    planning_record_id: str | None = None
    patrol_route_id: str | None = None
    status: str | None = None
    include_archived: bool = False


class TimeCaptureEventCapture(BaseModel):
    shift_id: str | None = None
    assignment_id: str | None = None
    event_code: str = Field(min_length=1, max_length=20)
    occurred_at: datetime | None = None
    latitude: float | None = None
    longitude: float | None = None
    note: str | None = None
    client_event_id: str | None = Field(default=None, max_length=120)
    raw_token: str | None = Field(default=None, min_length=1, max_length=255)
    scan_medium_code: str | None = Field(default=None, max_length=40)


class TimeCaptureTerminalEventCapture(TimeCaptureEventCapture):
    device_code: str = Field(min_length=1, max_length=80)
    access_key: str = Field(min_length=8, max_length=255)


class TimeCaptureValidationIssueRead(BaseModel):
    code: str
    severity: str
    message_key: str
    details: dict[str, object] = Field(default_factory=dict)


class TimeCaptureEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    actor_type_code: str
    employee_id: str | None
    subcontractor_worker_id: str | None
    shift_id: str | None
    assignment_id: str | None
    site_id: str | None
    planning_record_id: str | None
    patrol_route_id: str | None
    device_id: str | None
    policy_id: str | None
    source_channel_code: str
    event_code: str
    occurred_at: datetime
    source_ip: str | None
    latitude: float | None
    longitude: float | None
    scan_medium_code: str | None
    raw_token_suffix: str | None
    client_event_id: str | None
    note: str | None
    validation_status_code: str
    validation_message_key: str | None
    validation_details_json: dict[str, object] = Field(default_factory=dict)
    metadata_json: dict[str, object] = Field(default_factory=dict)
    status: str
    archived_at: datetime | None
    version_no: int
    created_at: datetime


class TimeCaptureEventListItem(BaseModel):
    id: str
    actor_type_code: str
    employee_id: str | None
    subcontractor_worker_id: str | None
    shift_id: str | None
    assignment_id: str | None
    source_channel_code: str
    event_code: str
    occurred_at: datetime
    device_id: str | None
    validation_status_code: str
    validation_message_key: str | None
    raw_token_suffix: str | None


class TimeCaptureEventFilter(BaseModel):
    shift_id: str | None = None
    employee_id: str | None = None
    subcontractor_worker_id: str | None = None
    source_channel_code: str | None = None
    validation_status_code: str | None = None
    device_id: str | None = None
    occurred_from: datetime | None = None
    occurred_to: datetime | None = None
    include_archived: bool = False


class TimeCaptureOwnEventCollectionRead(BaseModel):
    tenant_id: str
    employee_id: str
    items: list[TimeCaptureEventListItem] = Field(default_factory=list)


class TimeEventValidationStatusUpdate(BaseModel):
    validation_status_code: str = Field(min_length=1, max_length=20)
    reason_code: str | None = Field(default=None, max_length=120)
    note: str | None = None
    version_no: int | None = None


class AttendanceDiscrepancyIssueRead(BaseModel):
    code: str
    severity: str
    message_key: str
    source_event_ids: list[str] = Field(default_factory=list)
    details: dict[str, object] = Field(default_factory=dict)


class AttendanceRecordListFilter(BaseModel):
    shift_id: str | None = None
    assignment_id: str | None = None
    employee_id: str | None = None
    subcontractor_worker_id: str | None = None
    discrepancy_only: bool = False
    current_only: bool = True
    include_archived: bool = False


class AttendanceRecordListItem(BaseModel):
    id: str
    actor_type_code: str
    employee_id: str | None
    subcontractor_worker_id: str | None
    shift_id: str
    assignment_id: str | None
    check_in_at: datetime | None
    check_out_at: datetime | None
    break_minutes: int
    worked_minutes: int
    discrepancy_state_code: str
    discrepancy_codes_json: list[str] = Field(default_factory=list)
    derivation_status_code: str
    is_current: bool
    derived_at: datetime


class AttendanceRecordRead(AttendanceRecordListItem):
    model_config = ConfigDict(from_attributes=True)

    tenant_id: str
    source_event_count: int
    first_time_event_id: str | None
    last_time_event_id: str | None
    source_event_ids_json: list[str] = Field(default_factory=list)
    discrepancy_details_json: dict[str, object] = Field(default_factory=dict)
    discrepancies: list[AttendanceDiscrepancyIssueRead] = Field(default_factory=list)
    superseded_at: datetime | None
    superseded_by_attendance_id: str | None
    status: str
    archived_at: datetime | None
    version_no: int
    created_at: datetime
    updated_at: datetime
