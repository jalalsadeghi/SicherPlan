import { webAppConfig } from "@/config/env";

export interface CoverageDemandGroupItem {
  demand_group_id: string;
  function_type_id: string;
  qualification_type_id: null | string;
  min_qty: number;
  target_qty: number;
  assigned_count: number;
  confirmed_count: number;
  released_partner_qty: number;
  coverage_state: string;
}

export interface CoverageShiftItem {
  shift_id: string;
  planning_record_id: string;
  shift_plan_id: string;
  order_id: string;
  order_no: string;
  planning_record_name: string;
  planning_mode_code: string;
  workforce_scope_code: string;
  starts_at: string;
  ends_at: string;
  shift_type_code: string;
  location_text: null | string;
  meeting_point: null | string;
  min_required_qty: number;
  target_required_qty: number;
  assigned_count: number;
  confirmed_count: number;
  released_partner_qty: number;
  coverage_state: string;
  demand_groups: CoverageDemandGroupItem[];
}

export interface CoverageFilterParams {
  customer_id?: null | string;
  planning_record_id?: null | string;
  shift_plan_id?: null | string;
  order_id?: null | string;
  date_from: string;
  date_to: string;
  planning_mode_code?: null | string;
  workforce_scope_code?: null | string;
  function_type_id?: null | string;
  qualification_type_id?: null | string;
  release_state?: null | string;
  visibility_state?: null | string;
  confirmation_state?: null | string;
}

export interface StaffingBoardAssignmentItem {
  id: string;
  shift_id: string;
  demand_group_id: string;
  team_id: null | string;
  employee_id: null | string;
  subcontractor_worker_id: null | string;
  assignment_status_code: string;
  assignment_source_code: string;
  confirmed_at: null | string;
  version_no: number;
}

export interface AssignmentRead {
  id: string;
  tenant_id: string;
  shift_id: string;
  demand_group_id: string;
  team_id: null | string;
  employee_id: null | string;
  subcontractor_worker_id: null | string;
  assignment_status_code: string;
  assignment_source_code: string;
  offered_at: null | string;
  confirmed_at: null | string;
  remarks: null | string;
  status: string;
  version_no: number;
  created_at: string;
  updated_at: string;
  archived_at: null | string;
}

export interface StaffingBoardDemandGroupItem {
  id: string;
  shift_id: string;
  function_type_id: string;
  qualification_type_id: null | string;
  min_qty: number;
  target_qty: number;
  mandatory_flag: boolean;
  assigned_count: number;
  confirmed_count: number;
  released_partner_qty: number;
}

export interface DemandGroupRead {
  id: string;
  tenant_id: string;
  shift_id: string;
  function_type_id: string;
  qualification_type_id: null | string;
  min_qty: number;
  target_qty: number;
  mandatory_flag: boolean;
  sort_order: number;
  remark: null | string;
  status: string;
  version_no: number;
  created_at: string;
  updated_at: string;
  archived_at: null | string;
}

export interface DemandGroupCreate {
  tenant_id: string;
  shift_id: string;
  function_type_id: string;
  qualification_type_id?: null | string;
  min_qty: number;
  target_qty: number;
  mandatory_flag?: boolean;
  sort_order?: number;
  remark?: null | string;
}

export interface DemandGroupBulkTemplate {
  function_type_id: string;
  qualification_type_id?: null | string;
  min_qty: number;
  target_qty: number;
  mandatory_flag?: boolean;
  sort_order?: null | number;
  remark?: null | string;
}

export interface DemandGroupBulkApplyRequest {
  tenant_id: string;
  shift_plan_id: string;
  shift_series_id?: null | string;
  date_from?: null | string;
  date_to?: null | string;
  apply_mode?: "create_missing" | "upsert_matching";
  demand_groups: DemandGroupBulkTemplate[];
}

export interface DemandGroupBulkApplyShiftResult {
  shift_id: string;
  created_count: number;
  updated_count: number;
  skipped_count: number;
  errors: string[];
}

export interface DemandGroupBulkApplyResult {
  tenant_id: string;
  shift_plan_id: string;
  shift_series_id: null | string;
  apply_mode: "create_missing" | "upsert_matching";
  target_shift_count: number;
  template_count: number;
  created_count: number;
  updated_count: number;
  skipped_count: number;
  affected_demand_group_ids: string[];
  results: DemandGroupBulkApplyShiftResult[];
}

export interface DemandGroupBulkUpdateMatch {
  function_type_id: string;
  qualification_type_id?: null | string;
  min_qty?: null | number;
  target_qty?: null | number;
  mandatory_flag?: null | boolean;
  sort_order?: null | number;
  remark?: null | string;
}

export interface DemandGroupBulkUpdatePatch {
  function_type_id?: null | string;
  qualification_type_id?: null | string;
  min_qty?: null | number;
  target_qty?: null | number;
  mandatory_flag?: null | boolean;
  sort_order?: null | number;
  remark?: null | string;
  status?: null | string;
}

export interface DemandGroupBulkUpdateRequest {
  tenant_id: string;
  shift_plan_id: string;
  shift_series_id?: null | string;
  date_from?: null | string;
  date_to?: null | string;
  match: DemandGroupBulkUpdateMatch;
  patch: DemandGroupBulkUpdatePatch;
  expected_demand_group_ids?: string[];
  expected_target_shift_count?: null | number;
}

export interface DemandGroupBulkUpdateItemResult {
  demand_group_id: string;
  shift_id: string;
  outcome_code: "updated" | "skipped" | "conflict";
  reason_codes: string[];
}

export interface DemandGroupBulkUpdateResult {
  tenant_id: string;
  shift_plan_id: string;
  shift_series_id: null | string;
  matched_count: number;
  updated_count: number;
  skipped_count: number;
  conflict_count: number;
  updated_demand_group_ids: string[];
  results: DemandGroupBulkUpdateItemResult[];
}

export interface DemandGroupUpdate {
  function_type_id?: null | string;
  qualification_type_id?: null | string;
  min_qty?: null | number;
  target_qty?: null | number;
  mandatory_flag?: null | boolean;
  sort_order?: null | number;
  remark?: null | string;
  status?: null | string;
  archived_at?: null | string;
  version_no?: null | number;
}

export interface StaffingBoardShiftItem {
  id: string;
  tenant_id: string;
  planning_record_id: string;
  shift_plan_id: string;
  order_id: string;
  order_no: string;
  planning_record_name: string;
  planning_mode_code: string;
  workforce_scope_code: string;
  starts_at: string;
  ends_at: string;
  shift_type_code: string;
  release_state: string;
  status: string;
  location_text: null | string;
  meeting_point: null | string;
  demand_groups: StaffingBoardDemandGroupItem[];
  assignments: StaffingBoardAssignmentItem[];
}

export interface TeamMemberRead {
  id: string;
  tenant_id: string;
  team_id: string;
  employee_id: null | string;
  subcontractor_worker_id: null | string;
  role_label: null | string;
  is_team_lead: boolean;
  valid_from: string;
  valid_to: null | string;
  status: string;
  version_no: number;
  notes: null | string;
}

export interface TeamRead {
  id: string;
  tenant_id: string;
  planning_record_id: null | string;
  shift_id: null | string;
  name: string;
  role_label: null | string;
  status: string;
  version_no: number;
  notes: null | string;
  members: TeamMemberRead[];
}

export interface TeamCreate {
  tenant_id: string;
  planning_record_id?: null | string;
  shift_id?: null | string;
  name: string;
  role_label?: null | string;
  notes?: null | string;
}

export interface TeamUpdate {
  planning_record_id?: null | string;
  shift_id?: null | string;
  name?: null | string;
  role_label?: null | string;
  notes?: null | string;
  status?: null | string;
  archived_at?: null | string;
  version_no?: null | number;
}

export interface TeamMemberCreate {
  tenant_id: string;
  team_id: string;
  employee_id?: null | string;
  subcontractor_worker_id?: null | string;
  role_label?: null | string;
  is_team_lead?: boolean;
  valid_from: string;
  valid_to?: null | string;
  notes?: null | string;
}

export interface TeamMemberUpdate {
  employee_id?: null | string;
  subcontractor_worker_id?: null | string;
  role_label?: null | string;
  is_team_lead?: null | boolean;
  valid_from?: null | string;
  valid_to?: null | string;
  notes?: null | string;
  status?: null | string;
  archived_at?: null | string;
  version_no?: null | number;
}

export interface SubcontractorReleaseRead {
  id: string;
  tenant_id: string;
  shift_id: string;
  demand_group_id: null | string;
  subcontractor_id: string;
  released_qty: number;
  release_status_code: string;
  released_at: null | string;
  revoked_at: null | string;
  status: string;
  version_no: number;
  remarks: null | string;
}

export interface StaffingAssignCommand {
  tenant_id: string;
  shift_id: string;
  demand_group_id: string;
  team_id?: null | string;
  employee_id?: null | string;
  subcontractor_worker_id?: null | string;
  assignment_source_code?: string;
  offered_at?: null | string;
  confirmed_at?: null | string;
  remarks?: null | string;
}

export interface AssignmentCreate {
  tenant_id: string;
  shift_id: string;
  demand_group_id: string;
  team_id?: null | string;
  employee_id?: null | string;
  subcontractor_worker_id?: null | string;
  assignment_status_code?: string;
  assignment_source_code?: string;
  offered_at?: null | string;
  confirmed_at?: null | string;
  remarks?: null | string;
}

export interface StaffingUnassignCommand {
  tenant_id: string;
  assignment_id: string;
  version_no: number;
  remarks?: null | string;
}

export interface StaffingSubstituteCommand {
  tenant_id: string;
  assignment_id: string;
  version_no: number;
  replacement_team_id?: null | string;
  replacement_employee_id?: null | string;
  replacement_subcontractor_worker_id?: null | string;
  assignment_source_code?: string;
  remarks?: null | string;
}

export interface StaffingCommandResult {
  tenant_id: string;
  shift_id: string;
  assignment_id: null | string;
  outcome_code: string;
  validation_codes: string[];
  conflict_code: null | string;
  assignment: null | StaffingBoardAssignmentItem;
}

export interface PlanningValidationResult {
  rule_code: string;
  severity: string;
  message_key: string;
  summary: null | string;
  actor_type: null | string;
  actor_id: null | string;
  assignment_id: null | string;
  shift_id: string;
  demand_group_id: null | string;
  source_refs: Record<string, unknown>;
  policy_code: null | string;
  override_allowed: boolean;
  metadata: Record<string, unknown>;
}

export interface AssignmentValidationRead {
  tenant_id: string;
  assignment_id: string;
  shift_id: string;
  blocking_count: number;
  warning_count: number;
  info_count: number;
  issues: PlanningValidationResult[];
}

export interface ShiftReleaseValidationRead {
  tenant_id: string;
  shift_id: string;
  blocking_count: number;
  warning_count: number;
  issues: PlanningValidationResult[];
}

export interface AssignmentValidationOverrideRead {
  id: string;
  tenant_id: string;
  assignment_id: string;
  rule_code: string;
  reason_text: string;
  created_at: string;
  created_by_user_id: null | string;
}

export interface AssignmentValidationOverrideCreate {
  tenant_id: string;
  rule_code: string;
  reason_text: string;
}

export interface PlanningDispatchRecipientPreviewRead {
  recipient_kind: string;
  audience_code: string;
  audience_ref: string;
  destination: string;
  display_name: null | string;
  redacted: boolean;
  metadata_json: Record<string, unknown>;
}

export interface PlanningDispatchPreviewRead {
  tenant_id: string;
  shift_id: string;
  channel: string;
  template_key: string;
  language_code: string;
  audience_codes: string[];
  subject_preview: null | string;
  body_preview: string;
  redacted: boolean;
  recipients: PlanningDispatchRecipientPreviewRead[];
}

export interface PlanningDispatchCreate {
  tenant_id: string;
  shift_id: string;
  channel?: string;
  language_code?: string;
  template_key?: string;
  audience_codes: string[];
  team_ids?: string[];
  attachment_document_ids?: string[];
  extra_placeholders?: Record<string, unknown>;
}

export interface PlanningOutputDocumentRead {
  document_id: string;
  owner_type: string;
  owner_id: string;
  variant_code: string;
  audience_code: string;
  title: string;
  relation_type: string;
  current_version_no: number;
  file_name: string;
  content_type: string;
  generated_at: string;
  is_revision_safe_pdf: boolean;
}

export interface PlanningOutputGenerateRequest {
  tenant_id: string;
  variant_code: string;
  audience_code: string;
  regenerate?: boolean;
}

export interface AssignmentUpdate {
  team_id?: null | string;
  employee_id?: null | string;
  subcontractor_worker_id?: null | string;
  assignment_status_code?: null | string;
  assignment_source_code?: null | string;
  offered_at?: null | string;
  confirmed_at?: null | string;
  remarks?: null | string;
  status?: null | string;
  archived_at?: null | string;
  version_no?: null | number;
}

export class PlanningStaffingApiError extends Error {
  status: number;
  messageKey: string;
  details: Record<string, unknown>;

  constructor(status: number, payload: { message_key: string; details: Record<string, unknown> }) {
    super(payload.message_key);
    this.status = status;
    this.messageKey = payload.message_key;
    this.details = payload.details;
  }
}

function generateRequestId() {
  return `planning-staffing-${Math.random().toString(36).slice(2, 10)}`;
}

function isApiErrorEnvelope(payload: unknown): payload is { error: { message_key: string; details: Record<string, unknown> } } {
  if (!payload || typeof payload !== "object" || !("error" in payload)) {
    return false;
  }
  const error = (payload as { error?: { message_key?: unknown } }).error;
  return typeof error?.message_key === "string";
}

async function request<T>(path: string, accessToken: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${webAppConfig.apiBaseUrl}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
      "X-Request-Id": generateRequestId(),
      ...(init.headers ?? {}),
    },
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    if (isApiErrorEnvelope(payload)) {
      throw new PlanningStaffingApiError(response.status, payload.error);
    }
    throw new PlanningStaffingApiError(response.status, { message_key: "errors.platform.internal", details: {} });
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

function queryString(params: Record<string, unknown>) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === null || value === undefined || value === "" || value === false) {
      return;
    }
    query.set(key, String(value));
  });
  const serialized = query.toString();
  return serialized ? `?${serialized}` : "";
}

export function listStaffingCoverage(tenantId: string, accessToken: string, filters: CoverageFilterParams) {
  return request<CoverageShiftItem[]>(
    `/api/planning/tenants/${tenantId}/ops/coverage${queryString(filters as unknown as Record<string, unknown>)}`,
    accessToken,
  );
}

export function listStaffingBoard(
  tenantId: string,
  accessToken: string,
  filters: CoverageFilterParams | Record<string, unknown>,
) {
  return request<StaffingBoardShiftItem[]>(
    `/api/planning/tenants/${tenantId}/ops/staffing-board${queryString(filters as Record<string, unknown>)}`,
    accessToken,
  );
}

export function listTeams(tenantId: string, accessToken: string, filters: Record<string, unknown>) {
  return request<TeamRead[]>(
    `/api/planning/tenants/${tenantId}/ops/teams${queryString(filters)}`,
    accessToken,
  );
}

export function createTeam(tenantId: string, accessToken: string, payload: TeamCreate) {
  return request<TeamRead>(
    `/api/planning/tenants/${tenantId}/ops/teams`,
    accessToken,
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export function getTeam(tenantId: string, accessToken: string, teamId: string) {
  return request<TeamRead>(
    `/api/planning/tenants/${tenantId}/ops/teams/${teamId}`,
    accessToken,
  );
}

export function updateTeam(tenantId: string, accessToken: string, teamId: string, payload: TeamUpdate) {
  return request<TeamRead>(
    `/api/planning/tenants/${tenantId}/ops/teams/${teamId}`,
    accessToken,
    { method: "PATCH", body: JSON.stringify(payload) },
  );
}

export function listDemandGroups(tenantId: string, accessToken: string, filters: Record<string, unknown>) {
  return request<DemandGroupRead[]>(
    `/api/planning/tenants/${tenantId}/ops/demand-groups${queryString(filters)}`,
    accessToken,
  );
}

export function createDemandGroup(tenantId: string, accessToken: string, payload: DemandGroupCreate) {
  return request<DemandGroupRead>(
    `/api/planning/tenants/${tenantId}/ops/demand-groups`,
    accessToken,
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export function bulkApplyDemandGroups(tenantId: string, accessToken: string, payload: DemandGroupBulkApplyRequest) {
  return request<DemandGroupBulkApplyResult>(
    `/api/planning/tenants/${tenantId}/ops/demand-groups/bulk-apply`,
    accessToken,
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export function bulkUpdateDemandGroups(tenantId: string, accessToken: string, payload: DemandGroupBulkUpdateRequest) {
  return request<DemandGroupBulkUpdateResult>(
    `/api/planning/tenants/${tenantId}/ops/demand-groups/bulk-update`,
    accessToken,
    { method: "PATCH", body: JSON.stringify(payload) },
  );
}

export function updateDemandGroup(tenantId: string, accessToken: string, demandGroupId: string, payload: DemandGroupUpdate) {
  return request<DemandGroupRead>(
    `/api/planning/tenants/${tenantId}/ops/demand-groups/${demandGroupId}`,
    accessToken,
    { method: "PATCH", body: JSON.stringify(payload) },
  );
}

export function listTeamMembers(tenantId: string, accessToken: string, filters: Record<string, unknown>) {
  return request<TeamMemberRead[]>(
    `/api/planning/tenants/${tenantId}/ops/team-members${queryString(filters)}`,
    accessToken,
  );
}

export function createTeamMember(tenantId: string, accessToken: string, payload: TeamMemberCreate) {
  return request<TeamMemberRead>(
    `/api/planning/tenants/${tenantId}/ops/team-members`,
    accessToken,
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export function updateTeamMember(tenantId: string, accessToken: string, teamMemberId: string, payload: TeamMemberUpdate) {
  return request<TeamMemberRead>(
    `/api/planning/tenants/${tenantId}/ops/team-members/${teamMemberId}`,
    accessToken,
    { method: "PATCH", body: JSON.stringify(payload) },
  );
}

export function listSubcontractorReleases(tenantId: string, accessToken: string, filters: Record<string, unknown>) {
  return request<SubcontractorReleaseRead[]>(
    `/api/planning/tenants/${tenantId}/ops/subcontractor-releases${queryString(filters)}`,
    accessToken,
  );
}

export function getShiftReleaseValidations(tenantId: string, accessToken: string, shiftId: string) {
  return request<ShiftReleaseValidationRead>(
    `/api/planning/tenants/${tenantId}/ops/shifts/${shiftId}/release-validations`,
    accessToken,
  );
}

export function getAssignmentValidations(tenantId: string, accessToken: string, assignmentId: string) {
  return request<AssignmentValidationRead>(
    `/api/planning/tenants/${tenantId}/ops/assignments/${assignmentId}/validations`,
    accessToken,
  );
}

export function getAssignment(tenantId: string, accessToken: string, assignmentId: string) {
  return request<AssignmentRead>(
    `/api/planning/tenants/${tenantId}/ops/assignments/${assignmentId}`,
    accessToken,
  );
}

export function createAssignment(tenantId: string, accessToken: string, payload: AssignmentCreate) {
  return request<AssignmentRead>(
    `/api/planning/tenants/${tenantId}/ops/assignments`,
    accessToken,
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export function updateAssignment(tenantId: string, accessToken: string, assignmentId: string, payload: AssignmentUpdate) {
  return request<AssignmentRead>(
    `/api/planning/tenants/${tenantId}/ops/assignments/${assignmentId}`,
    accessToken,
    { method: "PATCH", body: JSON.stringify(payload) },
  );
}

export function listAssignmentValidationOverrides(tenantId: string, accessToken: string, assignmentId: string) {
  return request<AssignmentValidationOverrideRead[]>(
    `/api/planning/tenants/${tenantId}/ops/assignments/${assignmentId}/validation-overrides`,
    accessToken,
  );
}

export function createAssignmentValidationOverride(
  tenantId: string,
  accessToken: string,
  assignmentId: string,
  payload: AssignmentValidationOverrideCreate,
) {
  return request<AssignmentValidationOverrideRead>(
    `/api/planning/tenants/${tenantId}/ops/assignments/${assignmentId}/validation-overrides`,
    accessToken,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export function getShiftReleaseDiagnostics(tenantId: string, accessToken: string, shiftId: string) {
  return request<ShiftReleaseValidationRead & {
    release_state: string;
    customer_visible_flag: boolean;
    subcontractor_visible_flag: boolean;
    employee_visible: boolean;
  }>(
    `/api/planning/tenants/${tenantId}/ops/shifts/${shiftId}/release-diagnostics`,
    accessToken,
  );
}

export function previewShiftDispatchMessage(
  tenantId: string,
  accessToken: string,
  shiftId: string,
  payload: PlanningDispatchCreate,
) {
  return request<PlanningDispatchPreviewRead>(
    `/api/planning/tenants/${tenantId}/ops/shifts/${shiftId}/dispatch-preview`,
    accessToken,
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export function assignStaffing(tenantId: string, accessToken: string, payload: StaffingAssignCommand) {
  return request<StaffingCommandResult>(
    `/api/planning/tenants/${tenantId}/ops/staffing-board/assign`,
    accessToken,
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export function unassignStaffing(tenantId: string, accessToken: string, payload: StaffingUnassignCommand) {
  return request<StaffingCommandResult>(
    `/api/planning/tenants/${tenantId}/ops/staffing-board/unassign`,
    accessToken,
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export function substituteStaffing(tenantId: string, accessToken: string, payload: StaffingSubstituteCommand) {
  return request<StaffingCommandResult>(
    `/api/planning/tenants/${tenantId}/ops/staffing-board/substitute`,
    accessToken,
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export function queueShiftDispatchMessage(
  tenantId: string,
  accessToken: string,
  shiftId: string,
  payload: PlanningDispatchCreate,
) {
  return request<{ id: string } & Record<string, unknown>>(
    `/api/planning/tenants/${tenantId}/ops/shifts/${shiftId}/dispatch-messages`,
    accessToken,
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export function listShiftOutputs(tenantId: string, accessToken: string, shiftId: string) {
  return request<PlanningOutputDocumentRead[]>(
    `/api/planning/tenants/${tenantId}/ops/shifts/${shiftId}/outputs`,
    accessToken,
  );
}

export function generateShiftOutput(
  tenantId: string,
  accessToken: string,
  shiftId: string,
  payload: PlanningOutputGenerateRequest,
) {
  return request<PlanningOutputDocumentRead>(
    `/api/planning/tenants/${tenantId}/ops/shifts/${shiftId}/outputs`,
    accessToken,
    { method: "POST", body: JSON.stringify(payload) },
  );
}
