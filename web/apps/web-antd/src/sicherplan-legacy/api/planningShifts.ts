import { AuthApiError } from "@/api/auth";

import { legacySessionRequest } from "./sessionRequest";

export interface ShiftTemplateListItem {
  id: string;
  tenant_id: string;
  code: string;
  label: string;
  local_start_time: string;
  local_end_time: string;
  default_break_minutes: number;
  shift_type_code: string;
  status: string;
  version_no: number;
}

export interface ShiftTemplateRead extends ShiftTemplateListItem {
  meeting_point: string | null;
  location_text: string | null;
  notes: string | null;
}

export interface ShiftTypeOption {
  code: string;
  label: string;
}

export interface ShiftPlanListItem {
  id: string;
  tenant_id: string;
  planning_record_id: string;
  name: string;
  workforce_scope_code: string;
  planning_from: string;
  planning_to: string;
  status: string;
  version_no: number;
}

export interface ShiftSeriesExceptionRead {
  id: string;
  tenant_id: string;
  shift_series_id: string;
  exception_date: string;
  action_code: string;
  override_local_start_time?: string | null;
  override_local_end_time?: string | null;
  override_break_minutes?: number | null;
  override_shift_type_code?: string | null;
  override_meeting_point?: string | null;
  override_location_text?: string | null;
  customer_visible_flag?: boolean | null;
  subcontractor_visible_flag?: boolean | null;
  stealth_mode_flag?: boolean | null;
  notes?: string | null;
  version_no?: number;
}

export interface ShiftSeriesListItem {
  id: string;
  tenant_id: string;
  shift_plan_id: string;
  shift_template_id: string;
  label: string;
  recurrence_code: string;
  interval_count: number;
  weekday_mask: string | null;
  timezone: string;
  date_from: string;
  date_to: string;
  release_state: string;
  customer_visible_flag: boolean;
  subcontractor_visible_flag: boolean;
  stealth_mode_flag: boolean;
  status: string;
  version_no: number;
}

export interface ShiftSeriesRead extends ShiftSeriesListItem {
  default_break_minutes?: number | null;
  shift_type_code?: string | null;
  meeting_point?: string | null;
  location_text?: string | null;
  notes?: string | null;
  exceptions: ShiftSeriesExceptionRead[];
}

export interface ShiftListItem {
  id: string;
  tenant_id: string;
  shift_plan_id: string;
  shift_series_id: string | null;
  occurrence_date: string | null;
  starts_at: string;
  ends_at: string;
  break_minutes: number;
  shift_type_code: string;
  location_text: string | null;
  meeting_point: string | null;
  release_state: string;
  customer_visible_flag: boolean;
  subcontractor_visible_flag: boolean;
  stealth_mode_flag: boolean;
  source_kind_code: string;
  status: string;
  version_no: number;
}

export interface ShiftRead extends ShiftListItem {
  released_at: string | null;
  released_by_user_id: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
  created_by_user_id: string | null;
  updated_by_user_id: string | null;
  archived_at: string | null;
}

export interface ShiftReleaseDiagnosticsIssue {
  scope: string;
  code: string;
  severity: string;
  message: string;
  metadata_json?: Record<string, unknown>;
}

export interface ShiftReleaseDiagnosticsRead {
  tenant_id: string;
  shift_id: string;
  release_state: string;
  customer_visible_flag: boolean;
  subcontractor_visible_flag: boolean;
  employee_visible: boolean;
  blocking_count: number;
  warning_count: number;
  issues: ShiftReleaseDiagnosticsIssue[];
}

export interface ShiftPlanRead extends ShiftPlanListItem {
  remarks?: string | null;
  series_rows: ShiftSeriesListItem[];
  shifts: ShiftListItem[];
}

export interface PlanningBoardShiftListItem {
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
  customer_visible_flag: boolean;
  subcontractor_visible_flag: boolean;
  stealth_mode_flag: boolean;
  location_text: string | null;
  meeting_point: string | null;
}

export interface ShiftCopyResult {
  source_from: string;
  source_to: string;
  target_from: string;
  copied_count: number;
  skipped_count: number;
}

export class PlanningShiftsApiError extends Error {
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
  return `planning-shifts-${Math.random().toString(36).slice(2, 10)}`;
}

function isApiErrorEnvelope(payload: unknown): payload is { error: { message_key: string; details: Record<string, unknown> } } {
  if (!payload || typeof payload !== "object" || !("error" in payload)) {
    return false;
  }
  const error = (payload as { error?: unknown }).error;
  return Boolean(error && typeof error === "object" && "message_key" in error && typeof (error as { message_key?: unknown }).message_key === "string");
}

async function request<T>(
  path: string,
  accessToken: string,
  options: Omit<RequestInit, "body"> & { body?: unknown } = {},
): Promise<T> {
  let response: Response;
  try {
    const { body, ...requestOptions } = options;
    response = await legacySessionRequest(path, {
      ...requestOptions,
      accessToken,
      headers: {
        "Content-Type": "application/json",
        "X-Request-Id": generateRequestId(),
        ...(options.headers ?? {}),
      },
      jsonBody: body,
    });
  } catch (error) {
    if (error instanceof AuthApiError) {
      throw new PlanningShiftsApiError(error.statusCode, {
        message_key: error.messageKey,
        details: error.details,
      });
    }
    throw error;
  }

  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    if (isApiErrorEnvelope(payload)) {
      throw new PlanningShiftsApiError(response.status, payload.error);
    }
    throw new PlanningShiftsApiError(response.status, { message_key: "errors.platform.internal", details: {} });
  }

  return (response.status === 204 ? undefined : response.json()) as T;
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

export function listShiftTemplates(tenantId: string, accessToken: string, filters: Record<string, unknown>) {
  return request<ShiftTemplateListItem[]>(`/api/planning/tenants/${tenantId}/ops/shift-templates${queryString(filters)}`, accessToken);
}

export function listShiftTypeOptions(tenantId: string, accessToken: string) {
  return request<ShiftTypeOption[]>(`/api/planning/tenants/${tenantId}/ops/shift-type-options`, accessToken);
}

export function createShiftTemplate(tenantId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<ShiftTemplateRead>(`/api/planning/tenants/${tenantId}/ops/shift-templates`, accessToken, { method: "POST", body: payload });
}

export function getShiftTemplate(tenantId: string, templateId: string, accessToken: string) {
  return request<ShiftTemplateRead>(`/api/planning/tenants/${tenantId}/ops/shift-templates/${templateId}`, accessToken);
}

export function updateShiftTemplate(tenantId: string, templateId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<ShiftTemplateRead>(`/api/planning/tenants/${tenantId}/ops/shift-templates/${templateId}`, accessToken, { method: "PATCH", body: payload });
}

export function listShiftPlans(tenantId: string, accessToken: string, filters: Record<string, unknown>) {
  return request<ShiftPlanListItem[]>(`/api/planning/tenants/${tenantId}/ops/shift-plans${queryString(filters)}`, accessToken);
}

export function createShiftPlan(tenantId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<ShiftPlanRead>(`/api/planning/tenants/${tenantId}/ops/shift-plans`, accessToken, { method: "POST", body: payload });
}

export function getShiftPlan(tenantId: string, shiftPlanId: string, accessToken: string) {
  return request<ShiftPlanRead>(`/api/planning/tenants/${tenantId}/ops/shift-plans/${shiftPlanId}`, accessToken);
}

export function updateShiftPlan(tenantId: string, shiftPlanId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<ShiftPlanRead>(`/api/planning/tenants/${tenantId}/ops/shift-plans/${shiftPlanId}`, accessToken, { method: "PATCH", body: payload });
}

export function listShiftSeries(tenantId: string, shiftPlanId: string, accessToken: string) {
  return request<ShiftSeriesListItem[]>(`/api/planning/tenants/${tenantId}/ops/shift-plans/${shiftPlanId}/series`, accessToken);
}

export function createShiftSeries(tenantId: string, shiftPlanId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<ShiftSeriesRead>(`/api/planning/tenants/${tenantId}/ops/shift-plans/${shiftPlanId}/series`, accessToken, { method: "POST", body: payload });
}

export function getShiftSeries(tenantId: string, shiftSeriesId: string, accessToken: string) {
  return request<ShiftSeriesRead>(`/api/planning/tenants/${tenantId}/ops/shift-series/${shiftSeriesId}`, accessToken);
}

export function updateShiftSeries(tenantId: string, shiftSeriesId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<ShiftSeriesRead>(`/api/planning/tenants/${tenantId}/ops/shift-series/${shiftSeriesId}`, accessToken, { method: "PATCH", body: payload });
}

export function generateShiftSeries(tenantId: string, shiftSeriesId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<ShiftRead[]>(`/api/planning/tenants/${tenantId}/ops/shift-series/${shiftSeriesId}/generate`, accessToken, { method: "POST", body: payload });
}

export function createShiftSeriesException(tenantId: string, shiftSeriesId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<ShiftSeriesExceptionRead>(`/api/planning/tenants/${tenantId}/ops/shift-series/${shiftSeriesId}/exceptions`, accessToken, { method: "POST", body: payload });
}

export function listShiftSeriesExceptions(tenantId: string, shiftSeriesId: string, accessToken: string) {
  return request<ShiftSeriesExceptionRead[]>(`/api/planning/tenants/${tenantId}/ops/shift-series/${shiftSeriesId}/exceptions`, accessToken);
}

export function updateShiftSeriesException(tenantId: string, rowId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<ShiftSeriesExceptionRead>(`/api/planning/tenants/${tenantId}/ops/shift-series-exceptions/${rowId}`, accessToken, { method: "PATCH", body: payload });
}

export function deleteShiftSeriesException(tenantId: string, rowId: string, accessToken: string) {
  return request<void>(`/api/planning/tenants/${tenantId}/ops/shift-series-exceptions/${rowId}`, accessToken, { method: "DELETE" });
}

export function listShifts(tenantId: string, accessToken: string, filters: Record<string, unknown>) {
  return request<ShiftListItem[]>(`/api/planning/tenants/${tenantId}/ops/shifts${queryString(filters)}`, accessToken);
}

export function createShift(tenantId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<ShiftRead>(`/api/planning/tenants/${tenantId}/ops/shifts`, accessToken, { method: "POST", body: payload });
}

export function getShift(tenantId: string, shiftId: string, accessToken: string) {
  return request<ShiftRead>(`/api/planning/tenants/${tenantId}/ops/shifts/${shiftId}`, accessToken);
}

export function getShiftReleaseDiagnostics(tenantId: string, shiftId: string, accessToken: string) {
  return request<ShiftReleaseDiagnosticsRead>(`/api/planning/tenants/${tenantId}/ops/shifts/${shiftId}/release-diagnostics`, accessToken);
}

export function updateShift(tenantId: string, shiftId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<ShiftRead>(`/api/planning/tenants/${tenantId}/ops/shifts/${shiftId}`, accessToken, { method: "PATCH", body: payload });
}

export function setShiftReleaseState(tenantId: string, shiftId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<ShiftRead>(`/api/planning/tenants/${tenantId}/ops/shifts/${shiftId}/release-state`, accessToken, { method: "POST", body: payload });
}

export function updateShiftVisibility(tenantId: string, shiftId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<ShiftRead>(`/api/planning/tenants/${tenantId}/ops/shifts/${shiftId}/visibility`, accessToken, { method: "POST", body: payload });
}

export function copyShiftSlice(tenantId: string, shiftPlanId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<ShiftCopyResult>(`/api/planning/tenants/${tenantId}/ops/shift-plans/${shiftPlanId}/copy`, accessToken, { method: "POST", body: payload });
}

export function listBoardShifts(tenantId: string, accessToken: string, filters: Record<string, unknown>) {
  return request<PlanningBoardShiftListItem[]>(`/api/planning/tenants/${tenantId}/ops/board/shifts${queryString(filters)}`, accessToken);
}
