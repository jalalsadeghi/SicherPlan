"""Assistant API schemas."""

from __future__ import annotations

from datetime import date as date_type
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AssistantCapabilitiesRead(BaseModel):
    enabled: bool
    provider_mode: str
    openai_configured: bool = False
    mock_provider_allowed: bool = False
    rag_enabled: bool = False
    can_chat: bool
    can_run_diagnostics: bool
    can_reindex_knowledge: bool
    supported_features: list[str] = Field(default_factory=list)


class AssistantProviderStatusRead(BaseModel):
    provider_mode: str
    openai_configured: bool
    model: str
    mock_provider_allowed: bool
    store_responses: bool
    rag_enabled: bool
    sdk_available: bool
    sdk_version: str | None = None


class AssistantProviderSmokeTestRead(BaseModel):
    ok: bool
    provider_mode: str
    model: str
    answer: str | None = None
    confidence: AssistantConfidence | None = None
    error_code: str | None = None


class AssistantFieldDictionaryStatusRead(BaseModel):
    artifact_loaded: bool
    artifact_version: str | None = None
    field_count: int
    lookup_count: int
    term_count: int = 0
    counts_by_module: dict[str, int] = Field(default_factory=dict)


class AssistantRouteContextInput(BaseModel):
    path: str | None = None
    route_name: str | None = None
    page_id: str | None = None
    query: dict[str, Any] | None = None


class AssistantClientContextInput(BaseModel):
    timezone: str | None = None
    ui_locale: str | None = None
    visible_page_title: str | None = None


class AssistantConversationCreate(BaseModel):
    initial_route: AssistantRouteContextInput | None = None
    locale: str | None = None
    title: str | None = None


class AssistantMessageCreate(BaseModel):
    message: str
    route_context: AssistantRouteContextInput | None = None
    client_context: AssistantClientContextInput | None = None


class AssistantFeedbackRating(str, Enum):
    HELPFUL = "helpful"
    NOT_HELPFUL = "not_helpful"


class AssistantFeedbackCreate(BaseModel):
    message_id: str = Field(min_length=1, max_length=120)
    rating: AssistantFeedbackRating
    comment: str | None = Field(default=None, max_length=1000)


class AssistantFeedbackRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    conversation_id: str
    message_id: str
    rating: AssistantFeedbackRating
    created_at: datetime


class AssistantScope(str, Enum):
    PLATFORM = "platform"
    TENANT = "tenant"
    BRANCH = "branch"
    MANDATE = "mandate"
    CUSTOMER = "customer"
    SUBCONTRACTOR = "subcontractor"
    EMPLOYEE_SELF_SERVICE = "employee_self_service"
    UNKNOWN = "unknown"


class AssistantConfidence(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AssistantDiagnosisSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    BLOCKING = "blocking"


class AssistantDiagnosisItem(BaseModel):
    finding: str
    severity: AssistantDiagnosisSeverity
    evidence: str


class AssistantNavigationLink(BaseModel):
    label: str
    path: str
    route_name: str | None = None
    page_id: str | None = None
    reason: str | None = None


class AssistantAnswerSegment(BaseModel):
    type: str
    text: str
    link: AssistantNavigationLink | None = None


class AssistantMissingPermission(BaseModel):
    permission: str
    reason: str


class AssistantSourceBasisItem(BaseModel):
    source_type: str
    source_name: str | None = None
    page_id: str | None = None
    module_key: str | None = None
    title: str | None = None
    evidence: str


class AssistantRagTraceTopSource(BaseModel):
    source_id: str | None = None
    source_type: str
    source_name: str | None = None
    page_id: str | None = None
    module_key: str | None = None
    title: str | None = None
    score: float | None = None
    content_preview: str | None = None


class AssistantRagTraceRead(BaseModel):
    trace_id: str
    provider_called: bool
    provider_mode: str
    retrieval_executed: bool
    grounding_attached: bool
    grounding_source_count: int
    content_bearing_source_count: int
    source_type_counts: dict[str, int] = Field(default_factory=dict)
    top_sources: list[AssistantRagTraceTopSource] = Field(default_factory=list)
    missing_context: list[str] = Field(default_factory=list)
    retrieval_plan: dict[str, Any] = Field(default_factory=dict)
    query_expansion: dict[str, Any] = Field(default_factory=dict)
    tool_result_count: int = 0
    tool_result_chars: int = 0
    estimated_tool_result_tokens: int = 0
    tool_result_trimmed: bool = False
    tool_result_trim_reason: str | None = None
    grounding_trimmed: bool = False
    trim_reason: str | None = None


class AssistantRagQualityGateRead(BaseModel):
    passed: bool
    failures: list[str] = Field(default_factory=list)


class AssistantRagDebugSnapshotRead(BaseModel):
    question: str
    detected_language: str | None = None
    classification: dict[str, Any] = Field(default_factory=dict)
    retrieval_plan: dict[str, Any] = Field(default_factory=dict)
    expanded_query: dict[str, Any] = Field(default_factory=dict)
    top_sources: list[AssistantRagTraceTopSource] = Field(default_factory=list)
    content_bearing_source_count: int = 0
    grounding_sent_to_provider: bool = False
    provider_called: bool = False
    source_basis_returned: list[AssistantSourceBasisItem] = Field(default_factory=list)
    final_answer: str = ""
    confidence: AssistantConfidence | None = None
    links: list[AssistantNavigationLink] = Field(default_factory=list)
    quality_gate: AssistantRagQualityGateRead


class AssistantStructuredResponse(BaseModel):
    conversation_id: str
    message_id: str
    detected_language: str
    response_language: str
    answer: str
    provider_degraded: bool = False
    answer_segments: list[AssistantAnswerSegment] = Field(default_factory=list)
    scope: AssistantScope
    confidence: AssistantConfidence
    out_of_scope: bool = False
    diagnosis: list[AssistantDiagnosisItem] = Field(default_factory=list)
    links: list[AssistantNavigationLink] = Field(default_factory=list)
    missing_permissions: list[AssistantMissingPermission] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    tool_trace_id: str | None = None
    rag_trace_id: str | None = None
    source_basis: list[AssistantSourceBasisItem] = Field(default_factory=list)
    rag_trace: AssistantRagTraceRead | None = None


class AssistantProviderStructuredOutput(BaseModel):
    answer: str
    provider_degraded: bool = False
    confidence: AssistantConfidence
    out_of_scope: bool = False
    diagnosis: list[AssistantDiagnosisItem] = Field(default_factory=list)
    links: list[AssistantNavigationLink] = Field(default_factory=list)
    missing_permissions: list[AssistantMissingPermission] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    tool_trace_id: str | None = None
    source_basis: list[AssistantSourceBasisItem] = Field(default_factory=list)


class AssistantKnowledgeIngestionFailureRead(BaseModel):
    source_path: str
    error: str


class AssistantKnowledgeIngestionResultRead(BaseModel):
    sources_seen: int
    sources_indexed: int
    sources_skipped: int
    sources_failed: int
    chunks_created: int
    failures: list[AssistantKnowledgeIngestionFailureRead] = Field(default_factory=list)


class AssistantKnowledgeChunkResult(BaseModel):
    chunk_id: str
    source_id: str
    source_name: str
    source_type: str
    source_path: str | None = None
    source_language: str | None = None
    title: str | None = None
    content: str
    content_preview: str | None = None
    language_code: str | None = None
    module_key: str | None = None
    page_id: str | None = None
    workflow_keys: list[str] = Field(default_factory=list)
    role_keys: list[str] = Field(default_factory=list)
    permission_keys: list[str] = Field(default_factory=list)
    api_families: list[str] = Field(default_factory=list)
    domain_terms: list[str] = Field(default_factory=list)
    language_aliases: list[str] = Field(default_factory=list)
    score: float
    rank: int
    matched_by: str


class AssistantCurrentUserCapabilitiesInput(BaseModel):
    pass


class AssistantCapabilitiesFlagsRead(BaseModel):
    can_chat: bool
    can_run_diagnostics: bool
    can_use_knowledge: bool
    can_reindex_knowledge: bool
    can_receive_navigation_links: bool


class AssistantScopeSummaryRead(BaseModel):
    branch_ids: list[str] = Field(default_factory=list)
    mandate_ids: list[str] = Field(default_factory=list)
    customer_ids: list[str] = Field(default_factory=list)
    subcontractor_ids: list[str] = Field(default_factory=list)


class AssistantCurrentUserCapabilitiesRead(BaseModel):
    user_id: str
    tenant_id: str | None = None
    scope_kind: str
    role_keys: list[str] = Field(default_factory=list)
    permission_keys: list[str] = Field(default_factory=list)
    assistant_capabilities: AssistantCapabilitiesFlagsRead
    scope_summary: AssistantScopeSummaryRead
    redactions_applied: bool = True


class AssistantCurrentPageContextInput(BaseModel):
    path: str | None = None
    route_name: str | None = None
    page_id: str | None = None
    query: dict[str, Any] | None = None
    ui_locale: str | None = None
    timezone: str | None = None
    visible_page_title: str | None = None


class AssistantCurrentPageContextRead(BaseModel):
    path: str | None = None
    route_name: str | None = None
    page_id: str | None = None
    module_hint: str | None = None
    ui_locale: str | None = None
    timezone: str | None = None
    safe_query: dict[str, Any] = Field(default_factory=dict)
    is_known_page: bool
    is_authoritative: bool = False
    notes: list[str] = Field(default_factory=list)


class AssistantAccessiblePagesSearchInput(BaseModel):
    query: str | None = Field(default=None, max_length=120)
    module_key: str | None = Field(default=None, max_length=120)
    page_id: str | None = Field(default=None, max_length=120)
    limit: int = Field(default=10, ge=1, le=10)


class AssistantAccessiblePageRead(BaseModel):
    page_id: str
    label: str
    route_name: str | None = None
    path_template: str
    module_key: str
    can_access: bool
    reason: str


class AssistantAccessiblePagesSearchRead(BaseModel):
    pages: list[AssistantAccessiblePageRead] = Field(default_factory=list)
    truncated: bool = False


class AssistantPageHelpSidebarItemRead(BaseModel):
    label: str
    verified: bool = True


class AssistantPageHelpFieldRead(BaseModel):
    field_key: str
    label: str
    required: bool = False
    verified: bool = True


class AssistantPageHelpFormSectionRead(BaseModel):
    section_key: str
    title: str
    verified: bool = True
    fields: list[AssistantPageHelpFieldRead] = Field(default_factory=list)


class AssistantPageHelpActionRead(BaseModel):
    action_key: str
    label: str
    label_status: str = "verified"
    action_type: str = "button"
    selector: str | None = None
    test_id: str | None = None
    location: str | None = None
    required_permissions: list[str] = Field(default_factory=list)
    opens: str | None = None
    result: str | None = None
    verified: bool = True
    allowed: bool = True


class AssistantPageHelpPostStepRead(BaseModel):
    step_key: str
    label: str
    page_id: str | None = None
    verified: bool = True


class AssistantPageHelpVerifiedFromRead(BaseModel):
    file: str
    evidence: str


class AssistantPageHelpSourceBasisRead(BaseModel):
    source_type: str
    source_name: str | None = None
    page_id: str | None = None
    module_key: str | None = None
    evidence: str


class AssistantPageHelpManifestRead(BaseModel):
    page_id: str
    page_title: str
    route_name: str | None = None
    path_template: str | None = None
    module_key: str
    language_code: str | None = None
    source_status: str = "unverified"
    page_purpose: str | None = None
    sidebar_path: list[AssistantPageHelpSidebarItemRead] = Field(default_factory=list)
    workflow_keys: list[str] = Field(default_factory=list)
    api_families: list[str] = Field(default_factory=list)
    actions: list[AssistantPageHelpActionRead] = Field(default_factory=list)
    form_sections: list[AssistantPageHelpFormSectionRead] = Field(default_factory=list)
    post_create_steps: list[AssistantPageHelpPostStepRead] = Field(default_factory=list)
    source_basis: list[AssistantPageHelpSourceBasisRead] = Field(default_factory=list)
    verified_from: list[AssistantPageHelpVerifiedFromRead] = Field(default_factory=list)


class AssistantPageHelpManifestInput(BaseModel):
    page_id: str | None = Field(default=None, min_length=1, max_length=120)
    route_name: str | None = Field(default=None, max_length=255)
    language_code: str | None = Field(default=None, max_length=16)


class AssistantFindUiActionInput(BaseModel):
    intent: str = Field(min_length=1, max_length=120)
    page_id: str | None = Field(default=None, max_length=120)
    language_code: str | None = Field(default=None, max_length=16)


class AssistantFindUiActionRead(BaseModel):
    page_id: str | None = None
    page_title: str | None = None
    route_name: str | None = None
    path_template: str | None = None
    source_status: str = "unverified"
    intent: str
    action: AssistantPageHelpActionRead | None = None
    form_sections: list[AssistantPageHelpFormSectionRead] = Field(default_factory=list)
    sidebar_path: list[AssistantPageHelpSidebarItemRead] = Field(default_factory=list)
    missing_permissions: list[AssistantMissingPermission] = Field(default_factory=list)
    safe_note: str | None = None


class AssistantGroundingFactRead(BaseModel):
    kind: str
    code: str
    title: str
    detail: str
    page_id: str | None = None
    action_key: str | None = None
    verified: bool = True


class AssistantWorkflowHelpInput(BaseModel):
    query: str | None = Field(default=None, max_length=400)
    language_code: str | None = Field(default=None, max_length=16)
    workflow_key: str | None = Field(default=None, max_length=120)
    intent: str | None = Field(default=None, max_length=120)
    limit: int = Field(default=5, ge=1, le=5)


class AssistantWorkflowSourceBasisRead(BaseModel):
    source_type: str
    source_name: str
    page_id: str | None = None
    module_key: str | None = None
    evidence: str


class AssistantWorkflowStepRead(BaseModel):
    step_key: str
    sequence: int
    title: str | None = None
    title_en: str | None = None
    title_de: str | None = None
    page_id: str | None = None
    module_key: str | None = None
    purpose: str
    purpose_en: str
    purpose_de: str
    required_context: list[str] = Field(default_factory=list)
    creates_or_updates: list[str] = Field(default_factory=list)
    important_fields: list[str] = Field(default_factory=list)
    api_functions: list[str] = Field(default_factory=list)
    required_permissions: list[str] = Field(default_factory=list)
    source_basis: list[AssistantWorkflowSourceBasisRead] = Field(default_factory=list)


class AssistantWorkflowKnowledgeRead(BaseModel):
    workflow_key: str
    title: str
    title_en: str
    title_de: str
    summary: str
    summary_en: str
    summary_de: str
    intent_aliases_en: list[str] = Field(default_factory=list)
    intent_aliases_de: list[str] = Field(default_factory=list)
    route_path: str | None = None
    route_aliases: list[str] = Field(default_factory=list)
    entry_points: list[str] = Field(default_factory=list)
    steps: list[AssistantWorkflowStepRead] = Field(default_factory=list)
    linked_page_ids: list[str] = Field(default_factory=list)
    api_families: list[str] = Field(default_factory=list)
    ambiguity_notes: list[str] = Field(default_factory=list)
    source_basis: list[AssistantWorkflowSourceBasisRead] = Field(default_factory=list)


class AssistantWorkflowHelpRead(BaseModel):
    workflows: list[AssistantWorkflowKnowledgeRead] = Field(default_factory=list)
    matched_workflow_keys: list[str] = Field(default_factory=list)
    safe_note: str | None = None


class AssistantFieldDictionarySearchInput(BaseModel):
    query: str = Field(min_length=1, max_length=160)
    language_code: str | None = Field(default=None, max_length=16)
    page_id: str | None = Field(default=None, max_length=120)
    route_name: str | None = Field(default=None, max_length=255)
    limit: int = Field(default=5, ge=1, le=10)


class AssistantFieldDictionarySourceBasisRead(BaseModel):
    source_type: str
    source_name: str
    evidence: str
    page_id: str | None = None
    module_key: str | None = None


class AssistantFieldDictionaryMatchRead(BaseModel):
    field_key: str
    label: str
    entity_type: str | None = None
    module_key: str | None = None
    page_id: str | None = None
    definition: str | None = None
    required: bool | None = None
    confidence: str
    score: float
    source_basis: list[AssistantFieldDictionarySourceBasisRead] = Field(default_factory=list)


class AssistantFieldDictionarySearchRead(BaseModel):
    matches: list[AssistantFieldDictionaryMatchRead] = Field(default_factory=list)
    ambiguous: bool = False
    safe_note: str | None = None


class AssistantPlatformTermSearchInput(BaseModel):
    query: str = Field(min_length=1, max_length=160)
    language_code: str | None = Field(default=None, max_length=16)
    page_id: str | None = Field(default=None, max_length=120)
    route_name: str | None = Field(default=None, max_length=255)
    limit: int = Field(default=5, ge=1, le=10)


class AssistantPlatformTermMatchRead(BaseModel):
    term_key: str
    label: str
    module_key: str | None = None
    page_id: str | None = None
    concept_type: str
    ui_term_type: str
    definition: str | None = None
    ui_contexts: list[str] = Field(default_factory=list)
    related_terms: list[str] = Field(default_factory=list)
    confidence: str
    score: float
    source_basis: list[AssistantFieldDictionarySourceBasisRead] = Field(default_factory=list)


class AssistantPlatformTermSearchRead(BaseModel):
    matches: list[AssistantPlatformTermMatchRead] = Field(default_factory=list)
    ambiguous: bool = False
    safe_note: str | None = None


class AssistantLookupDictionarySearchInput(BaseModel):
    query: str = Field(min_length=1, max_length=160)
    language_code: str | None = Field(default=None, max_length=16)
    page_id: str | None = Field(default=None, max_length=120)
    route_name: str | None = Field(default=None, max_length=255)
    limit: int = Field(default=5, ge=1, le=10)


class AssistantLookupDictionaryValueRead(BaseModel):
    value: str
    labels: dict[str, str] = Field(default_factory=dict)
    meaning_de: str | None = None
    meaning_en: str | None = None


class AssistantLookupDictionaryMatchRead(BaseModel):
    lookup_key: str
    label: str
    entity_type: str | None = None
    module_key: str | None = None
    page_id: str | None = None
    value_source_kind: str
    values: list[AssistantLookupDictionaryValueRead] = Field(default_factory=list)
    source_basis: list[AssistantFieldDictionarySourceBasisRead] = Field(default_factory=list)
    confidence: str
    score: float


class AssistantLookupDictionarySearchRead(BaseModel):
    matches: list[AssistantLookupDictionaryMatchRead] = Field(default_factory=list)
    ambiguous: bool = False
    safe_note: str | None = None


class AssistantLookupExplanationInput(BaseModel):
    query: str = Field(min_length=1, max_length=160)
    language_code: str | None = Field(default=None, max_length=16)
    page_id: str | None = Field(default=None, max_length=120)
    route_name: str | None = Field(default=None, max_length=255)
    limit: int = Field(default=5, ge=1, le=10)


class AssistantLookupExplanationValueRead(BaseModel):
    value: str
    labels: dict[str, str] = Field(default_factory=dict)
    meaning_de: str | None = None
    meaning_en: str | None = None
    matched: bool = False


class AssistantLookupExplanationMatchRead(BaseModel):
    lookup_key: str
    label: str
    entity_type: str | None = None
    module_key: str | None = None
    page_id: str | None = None
    value_source_kind: str
    value_resolution: str = "static"
    confidence: str
    score: float
    values: list[AssistantLookupExplanationValueRead] = Field(default_factory=list)
    matched_values: list[AssistantLookupExplanationValueRead] = Field(default_factory=list)
    source_basis: list[AssistantFieldDictionarySourceBasisRead] = Field(default_factory=list)


class AssistantLookupExplanationRead(BaseModel):
    matches: list[AssistantLookupExplanationMatchRead] = Field(default_factory=list)
    ambiguous: bool = False
    missing_permissions: list[AssistantMissingPermission] = Field(default_factory=list)
    safe_note: str | None = None


class AssistantNavigationEntityContextInput(BaseModel):
    employee_id: str | None = None
    shift_id: str | None = None
    assignment_id: str | None = None
    planning_record_id: str | None = None
    shift_plan_id: str | None = None
    order_id: str | None = None
    customer_id: str | None = None
    subcontractor_id: str | None = None
    date: str | None = None
    tab: str | None = None


class AssistantNavigationLinkBuildInput(BaseModel):
    page_id: str = Field(min_length=1, max_length=120)
    entity_context: AssistantNavigationEntityContextInput | None = None
    reason: str | None = Field(default=None, max_length=240)


class AssistantAllowedNavigationLinkRead(BaseModel):
    allowed: bool
    link: AssistantNavigationLink | None = None
    missing_permissions: list[AssistantMissingPermission] = Field(default_factory=list)


class AssistantEmployeeSearchInput(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    limit: int = Field(default=5, ge=1, le=5)
    include_archived: bool = False


class AssistantEmployeeSearchMatchRead(BaseModel):
    employee_ref: str
    display_name: str
    personnel_no: str | None = None
    status: str
    is_active: bool
    visibility_scope: str
    match_confidence: str


class AssistantEmployeeSearchRead(BaseModel):
    matches: list[AssistantEmployeeSearchMatchRead] = Field(default_factory=list)
    match_count: int
    truncated: bool = False
    safe_message_key: str | None = None


class AssistantEmployeeOperationalProfileInput(BaseModel):
    employee_ref: str = Field(min_length=1, max_length=120)


class AssistantEmployeeOperationalProfileItemRead(BaseModel):
    employee_ref: str
    display_name: str
    personnel_no: str | None = None
    status: str
    is_active: bool
    default_branch_ref: str | None = None
    default_mandate_ref: str | None = None
    has_user_link: bool
    user_status: str | None = None
    operational_notes_available: bool = False


class AssistantEmployeeOperationalProfileRead(BaseModel):
    found: bool
    employee: AssistantEmployeeOperationalProfileItemRead | None = None
    redactions: list[str] = Field(default_factory=list)


class AssistantEmployeeMobileAccessStatusInput(BaseModel):
    employee_ref: str = Field(min_length=1, max_length=120)


class AssistantEmployeeBlockingReasonRead(BaseModel):
    code: str
    severity: str
    message: str


class AssistantEmployeeMobileAccessRead(BaseModel):
    has_linked_user_account: bool
    linked_user_status: str | None = None
    self_service_enabled: bool
    mobile_context_available: bool
    can_receive_released_schedules: bool
    blocking_reasons: list[AssistantEmployeeBlockingReasonRead] = Field(default_factory=list)


class AssistantEmployeeMobileAccessStatusRead(BaseModel):
    found: bool
    mobile_access: AssistantEmployeeMobileAccessRead | None = None
    missing_permissions: list[AssistantMissingPermission] = Field(default_factory=list)


class AssistantEmployeeReadinessInput(BaseModel):
    employee_ref: str = Field(min_length=1, max_length=120)
    date: str | None = Field(default=None, max_length=10)
    include_qualifications: bool = True
    include_absences: bool = True
    include_availability: bool = True


class AssistantEmployeeQualificationSummaryRead(BaseModel):
    has_expired_qualifications: bool
    has_missing_required_qualification: bool
    details_redacted: bool = True


class AssistantEmployeeCredentialSummaryRead(BaseModel):
    has_active_credential: bool
    has_expired_credential: bool
    details_redacted: bool = True


class AssistantEmployeeReadinessItemRead(BaseModel):
    employee_status: str
    has_active_absence_on_date: bool
    availability_summary: str
    qualification_summary: AssistantEmployeeQualificationSummaryRead
    credential_summary: AssistantEmployeeCredentialSummaryRead
    blocking_reasons: list[AssistantEmployeeBlockingReasonRead] = Field(default_factory=list)


class AssistantEmployeeReadinessRead(BaseModel):
    found: bool
    readiness: AssistantEmployeeReadinessItemRead | None = None
    missing_permissions: list[AssistantMissingPermission] = Field(default_factory=list)


class AssistantPlanningShiftSearchInput(BaseModel):
    date: date_type | None = None
    date_from: date_type | None = None
    date_to: date_type | None = None
    employee_ref: str | None = Field(default=None, max_length=120)
    planning_record_ref: str | None = Field(default=None, max_length=120)
    shift_plan_ref: str | None = Field(default=None, max_length=120)
    customer_ref: str | None = Field(default=None, max_length=120)
    limit: int = Field(default=10, ge=1, le=50)
    include_archived: bool = False


class AssistantPlanningShiftMatchRead(BaseModel):
    shift_ref: str
    shift_plan_ref: str | None = None
    planning_record_ref: str | None = None
    customer_ref: str | None = None
    starts_at: datetime
    ends_at: datetime
    status: str
    release_state: str
    employee_visible: bool
    customer_visible: bool
    subcontractor_visible: bool
    location_label: str | None = None
    match_reason: str


class AssistantPlanningShiftSearchRead(BaseModel):
    matches: list[AssistantPlanningShiftMatchRead] = Field(default_factory=list)
    match_count: int
    truncated: bool = False
    missing_permissions: list[AssistantMissingPermission] = Field(default_factory=list)


class AssistantPlanningAssignmentSearchInput(BaseModel):
    employee_ref: str | None = Field(default=None, max_length=120)
    shift_ref: str | None = Field(default=None, max_length=120)
    date: date_type | None = None
    date_from: date_type | None = None
    date_to: date_type | None = None
    assignment_status: str | None = Field(default=None, max_length=40)
    limit: int = Field(default=10, ge=1, le=50)
    include_archived: bool = False


class AssistantPlanningAssignmentMatchRead(BaseModel):
    assignment_ref: str
    shift_ref: str
    employee_ref: str | None = None
    subcontractor_worker_ref: str | None = None
    actor_type: str
    assignment_status: str
    source_code: str | None = None
    offered_at: datetime | None = None
    confirmed_at: datetime | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    shift_release_state: str
    is_visible_candidate_for_employee_app: bool


class AssistantPlanningAssignmentSearchRead(BaseModel):
    matches: list[AssistantPlanningAssignmentMatchRead] = Field(default_factory=list)
    match_count: int
    truncated: bool = False
    missing_permissions: list[AssistantMissingPermission] = Field(default_factory=list)


class AssistantPlanningAssignmentInspectInput(BaseModel):
    assignment_ref: str = Field(min_length=1, max_length=120)


class AssistantPlanningBlockingReasonRead(BaseModel):
    code: str
    severity: str
    message: str


class AssistantPlanningAssignmentInspectItemRead(BaseModel):
    assignment_ref: str
    shift_ref: str
    demand_group_ref: str | None = None
    employee_ref: str | None = None
    subcontractor_worker_ref: str | None = None
    actor_type: str
    assignment_status: str
    offered_at: datetime | None = None
    confirmed_at: datetime | None = None
    team_ref: str | None = None
    is_active_for_schedule_visibility: bool
    blocking_reasons: list[AssistantPlanningBlockingReasonRead] = Field(default_factory=list)


class AssistantPlanningAssignmentInspectRead(BaseModel):
    found: bool
    assignment: AssistantPlanningAssignmentInspectItemRead | None = None
    redactions: list[str] = Field(default_factory=list)


class AssistantPlanningShiftRefInput(BaseModel):
    shift_ref: str = Field(min_length=1, max_length=120)


class AssistantPlanningShiftReleaseStateItemRead(BaseModel):
    shift_ref: str
    shift_status: str
    shift_release_state: str
    shift_plan_ref: str | None = None
    shift_plan_status: str | None = None
    planning_record_ref: str | None = None
    planning_record_status: str | None = None
    planning_record_release_state: str | None = None
    is_released_for_internal_execution: bool
    is_released_for_employee_app: bool
    blocking_reasons: list[AssistantPlanningBlockingReasonRead] = Field(default_factory=list)


class AssistantPlanningShiftReleaseStateRead(BaseModel):
    found: bool
    release_state: AssistantPlanningShiftReleaseStateItemRead | None = None
    missing_permissions: list[AssistantMissingPermission] = Field(default_factory=list)


class AssistantPlanningShiftVisibilityInput(BaseModel):
    shift_ref: str = Field(min_length=1, max_length=120)
    target_audience: str | None = Field(default=None, max_length=40)


class AssistantPlanningShiftVisibilityItemRead(BaseModel):
    shift_ref: str
    target_audience: str
    employee_visible: bool
    customer_visible_flag: bool
    subcontractor_visible_flag: bool
    stealth_mode_flag: bool
    dispatch_output_required: bool
    dispatch_output_present: bool
    visibility_state: str
    blocking_reasons: list[AssistantPlanningBlockingReasonRead] = Field(default_factory=list)


class AssistantPlanningShiftVisibilityRead(BaseModel):
    found: bool
    visibility: AssistantPlanningShiftVisibilityItemRead | None = None
    missing_permissions: list[AssistantMissingPermission] = Field(default_factory=list)


class AssistantPlanningValidationInput(BaseModel):
    assignment_ref: str = Field(min_length=1, max_length=120)


class AssistantPlanningValidationItemRead(BaseModel):
    code: str
    severity: str
    status: str
    summary: str
    override_present: bool = False


class AssistantPlanningAssignmentValidationsRead(BaseModel):
    found: bool
    validations: list[AssistantPlanningValidationItemRead] = Field(default_factory=list)
    blocking_count: int = 0
    warning_count: int = 0
    missing_permissions: list[AssistantMissingPermission] = Field(default_factory=list)


class AssistantPlanningReleaseValidationInput(BaseModel):
    shift_ref: str | None = Field(default=None, max_length=120)
    planning_record_ref: str | None = Field(default=None, max_length=120)


class AssistantPlanningReleaseValidationItemRead(BaseModel):
    code: str
    severity: str
    status: str
    summary: str


class AssistantPlanningReleaseValidationsRead(BaseModel):
    found: bool
    release_validations: list[AssistantPlanningReleaseValidationItemRead] = Field(default_factory=list)
    blocking_count: int = 0
    warning_count: int = 0
    missing_permissions: list[AssistantMissingPermission] = Field(default_factory=list)


class AssistantFieldReleasedScheduleVisibilityInput(BaseModel):
    employee_ref: str | None = Field(default=None, max_length=120)
    assignment_ref: str | None = Field(default=None, max_length=120)
    shift_ref: str | None = Field(default=None, max_length=120)
    date: date_type | None = None
    date_from: date_type | None = None
    date_to: date_type | None = None
    target_channel: str | None = Field(default=None, max_length=40)


class AssistantFieldVisibilityMatchRead(BaseModel):
    assignment_ref: str | None = None
    shift_ref: str | None = None
    employee_ref: str | None = None
    schedule_date: date_type | None = None


class AssistantFieldScheduleWindowRead(BaseModel):
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class AssistantFieldCheckedRuleRead(BaseModel):
    code: str
    status: str
    severity: str
    summary: str


class AssistantFieldBlockingReasonRead(BaseModel):
    code: str
    severity: str
    message: str


class AssistantFieldReleasedScheduleVisibilityItemRead(BaseModel):
    target_channel: str
    employee_ref: str | None = None
    assignment_ref: str | None = None
    shift_ref: str | None = None
    visible: bool
    visibility_state: str
    confidence: AssistantConfidence
    schedule_window: AssistantFieldScheduleWindowRead
    checked_rules: list[AssistantFieldCheckedRuleRead] = Field(default_factory=list)
    blocking_reasons: list[AssistantFieldBlockingReasonRead] = Field(default_factory=list)
    missing_permissions: list[AssistantMissingPermission] = Field(default_factory=list)


class AssistantFieldReleasedScheduleVisibilityRead(BaseModel):
    found: bool
    visibility: AssistantFieldReleasedScheduleVisibilityItemRead | None = None
    matches: list[AssistantFieldVisibilityMatchRead] = Field(default_factory=list)
    redactions: list[str] = Field(default_factory=list)


class AssistantShiftVisibilityDiagnosticInput(BaseModel):
    employee_name: str | None = Field(default=None, max_length=120)
    employee_ref: str | None = Field(default=None, max_length=120)
    date: date_type | None = None
    date_from: date_type | None = None
    date_to: date_type | None = None
    assignment_ref: str | None = Field(default=None, max_length=120)
    shift_ref: str | None = Field(default=None, max_length=120)
    question_language: str | None = Field(default=None, max_length=16)
    route_context: AssistantRouteContextInput | None = None


class AssistantShiftVisibilityDiagnosticEntityRead(BaseModel):
    employee_ref: str | None = None
    display_name: str | None = None
    status: str | None = None
    match_state: str


class AssistantShiftVisibilityDiagnosticAssignmentRead(BaseModel):
    assignment_ref: str | None = None
    status: str | None = None
    match_state: str


class AssistantShiftVisibilityDiagnosticShiftRead(BaseModel):
    shift_ref: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    status: str | None = None
    release_state: str | None = None


class AssistantShiftVisibilityFindingRead(BaseModel):
    code: str
    severity: str
    status: str
    evidence: str
    source_tool: str | None = None


class AssistantShiftVisibilityCauseRead(BaseModel):
    code: str
    severity: str
    explanation: str


class AssistantShiftVisibilityDiagnosticRead(BaseModel):
    diagnostic_key: str = "employee_shift_visibility"
    status: str
    confidence: AssistantConfidence
    summary: str
    employee: AssistantShiftVisibilityDiagnosticEntityRead
    assignment: AssistantShiftVisibilityDiagnosticAssignmentRead
    shift: AssistantShiftVisibilityDiagnosticShiftRead
    findings: list[AssistantShiftVisibilityFindingRead] = Field(default_factory=list)
    most_likely_causes: list[AssistantShiftVisibilityCauseRead] = Field(default_factory=list)
    missing_permissions: list[AssistantMissingPermission] = Field(default_factory=list)
    links: list[AssistantNavigationLink] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    redactions: list[str] = Field(default_factory=list)


class AssistantMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    conversation_id: str
    role: str
    content: str
    structured_payload: dict[str, Any] | None = None
    detected_language: str | None = None
    response_language: str | None = None
    created_at: datetime


class AssistantConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str | None = None
    user_id: str
    title: str | None = None
    locale: str | None = None
    status: str
    last_route_name: str | None = None
    last_route_path: str | None = None
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None = None
    messages: list[AssistantMessageRead] = Field(default_factory=list)
