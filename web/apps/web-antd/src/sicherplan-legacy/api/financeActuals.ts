import { webAppConfig } from "@/config/env";

export interface FinanceActualListItem {
  id: string;
  assignment_id: string;
  shift_id: string;
  attendance_record_id: null | string;
  actor_type_code: string;
  employee_id: null | string;
  subcontractor_worker_id: null | string;
  planned_start_at: null | string;
  planned_end_at: null | string;
  actual_start_at: null | string;
  actual_end_at: null | string;
  payable_minutes: number;
  billable_minutes: number;
  discrepancy_state_code: string;
  discrepancy_codes_json: string[];
  derivation_status_code: string;
  approval_stage_code: string;
  is_current: boolean;
  derived_at: string;
}

export interface FinanceActualApprovalItem {
  id: string;
  stage_code: string;
  actor_scope_code: string;
  note_text: null | string;
  source_ref_json: Record<string, unknown>;
  created_at: string;
  created_by_user_id: null | string;
}

export interface FinanceActualReconciliationItem {
  id: string;
  reconciliation_kind_code: string;
  reason_code: string;
  note_text: null | string;
  payroll_minutes_delta: number;
  billable_minutes_delta: number;
  customer_adjustment_minutes_delta: number;
  replacement_actor_type_code: null | string;
  replacement_employee_id: null | string;
  replacement_subcontractor_worker_id: null | string;
  source_ref_json: Record<string, unknown>;
  created_at: string;
  created_by_user_id: null | string;
}

export interface FinanceActualLineItem {
  id: string;
  reason_code: string;
  quantity: number;
  unit_code: null | string;
  amount_total: number;
  currency_code: string;
  note_text: null | string;
  created_at: string;
  created_by_user_id: null | string;
}

export interface FinanceActualAllowanceItem extends FinanceActualLineItem {
  line_type_code: string;
  source_ref_json: Record<string, unknown>;
}

export interface FinanceActualExpenseItem extends FinanceActualLineItem {
  expense_type_code: string;
  source_ref_json: Record<string, unknown>;
}

export interface FinanceActualCommentItem {
  id: string;
  visibility_code: string;
  note_text: string;
  created_at: string;
  created_by_user_id: null | string;
}

export interface FinanceAuditEvent {
  id: string;
  actor_user_id: null | string;
  actor_session_id: null | string;
  event_type: string;
  entity_type: string;
  entity_id: string;
  request_id: null | string;
  source: string;
  before_json: Record<string, unknown>;
  after_json: Record<string, unknown>;
  metadata_json: Record<string, unknown>;
  created_at: string;
}

export interface FinanceActualDiscrepancy {
  code: string;
  severity: string;
  message_key: string;
  attendance_record_id: null | string;
  source_event_ids: string[];
  details: Record<string, unknown>;
}

export interface FinanceActualRead extends FinanceActualListItem {
  tenant_id: string;
  planned_break_minutes: number;
  actual_break_minutes: number;
  customer_adjustment_minutes: number;
  discrepancy_details_json: Record<string, unknown>;
  discrepancies: FinanceActualDiscrepancy[];
  superseded_at: null | string;
  superseded_by_actual_id: null | string;
  status: string;
  archived_at: null | string;
  version_no: number;
  created_at: string;
  updated_at: string;
  approvals: FinanceActualApprovalItem[];
  reconciliations: FinanceActualReconciliationItem[];
  allowances: FinanceActualAllowanceItem[];
  expenses: FinanceActualExpenseItem[];
  comments: FinanceActualCommentItem[];
  audit_history: FinanceAuditEvent[];
}

export class FinanceActualsApiError extends Error {
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

function requestId() {
  return `finance-actuals-${Math.random().toString(36).slice(2, 10)}`;
}

function isApiErrorEnvelope(payload: unknown): payload is { error: { message_key: string; details: Record<string, unknown> } } {
  return Boolean(payload && typeof payload === "object" && "error" in payload && typeof payload.error?.message_key === "string");
}

async function request<T>(path: string, accessToken: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${webAppConfig.apiBaseUrl}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
      "X-Request-Id": requestId(),
      ...(init.headers ?? {}),
    },
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    if (isApiErrorEnvelope(payload)) {
      throw new FinanceActualsApiError(response.status, payload.error);
    }
    throw new FinanceActualsApiError(response.status, { message_key: "errors.platform.internal", details: {} });
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

export function listFinanceActuals(tenantId: string, accessToken: string, filters: Record<string, unknown>) {
  return request<FinanceActualListItem[]>(`/api/finance/tenants/${tenantId}/actual-records${queryString(filters)}`, accessToken);
}

export function getFinanceActual(tenantId: string, actualId: string, accessToken: string) {
  return request<FinanceActualRead>(`/api/finance/tenants/${tenantId}/actual-records/${actualId}`, accessToken);
}

export function getFinanceActualAuditHistory(tenantId: string, actualId: string, accessToken: string) {
  return request<FinanceAuditEvent[]>(`/api/finance/tenants/${tenantId}/actual-records/${actualId}/audit-history`, accessToken);
}

export function submitPreliminaryActual(tenantId: string, actualId: string, accessToken: string, noteText: string) {
  return request<FinanceActualRead>(`/api/finance/tenants/${tenantId}/actual-records/${actualId}/preliminary-submit`, accessToken, {
    method: "POST",
    body: JSON.stringify({ note_text: noteText || null }),
  });
}

export function confirmOperationalActual(tenantId: string, actualId: string, accessToken: string, noteText: string) {
  return request<FinanceActualRead>(`/api/finance/tenants/${tenantId}/actual-records/${actualId}/operational-confirm`, accessToken, {
    method: "POST",
    body: JSON.stringify({ note_text: noteText || null }),
  });
}

export function financeSignoffActual(tenantId: string, actualId: string, accessToken: string, noteText: string) {
  return request<FinanceActualRead>(`/api/finance/tenants/${tenantId}/actual-records/${actualId}/finance-signoff`, accessToken, {
    method: "POST",
    body: JSON.stringify({ note_text: noteText || null }),
  });
}

export function createFinanceReconciliation(tenantId: string, actualId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<FinanceActualRead>(`/api/finance/tenants/${tenantId}/actual-records/${actualId}/reconciliations`, accessToken, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createFinanceAllowance(tenantId: string, actualId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<FinanceActualRead>(`/api/finance/tenants/${tenantId}/actual-records/${actualId}/allowances`, accessToken, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createFinanceExpense(tenantId: string, actualId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<FinanceActualRead>(`/api/finance/tenants/${tenantId}/actual-records/${actualId}/expenses`, accessToken, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createFinanceComment(tenantId: string, actualId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<FinanceActualRead>(`/api/finance/tenants/${tenantId}/actual-records/${actualId}/comments`, accessToken, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
