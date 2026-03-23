import { webAppConfig } from "@/config/env";

export interface PayrollTariffTableListItem {
  id: string;
  code: string;
  title: string;
  region_code: string;
  status: string;
  effective_from: string;
  effective_until: null | string;
  version_no: number;
  archived_at: null | string;
}

export interface PayrollTariffRateRead {
  id: string;
  function_type_id: null | string;
  qualification_type_id: null | string;
  employment_type_code: null | string;
  pay_unit_code: string;
  currency_code: string;
  base_amount: number;
  payroll_code: null | string;
  notes: null | string;
  version_no: number;
}

export interface PayrollSurchargeRuleRead {
  id: string;
  surcharge_type_code: string;
  custom_code: null | string;
  weekday_mask: number;
  start_minute_local: number;
  end_minute_local: number;
  holiday_region_code: null | string;
  function_type_id: null | string;
  qualification_type_id: null | string;
  employment_type_code: null | string;
  percent_value: null | number;
  fixed_amount: null | number;
  currency_code: null | string;
  payroll_code: null | string;
  notes: null | string;
  version_no: number;
}

export interface PayrollTariffTableRead extends PayrollTariffTableListItem {
  rates: PayrollTariffRateRead[];
  surcharge_rules: PayrollSurchargeRuleRead[];
  notes: null | string;
}

export interface EmployeePayProfileRead {
  id: string;
  employee_id: string;
  tariff_table_id: null | string;
  payroll_region_code: string;
  employment_type_code: string;
  pay_cycle_code: string;
  pay_unit_code: string;
  currency_code: string;
  export_employee_code: null | string;
  cost_center_code: null | string;
  base_rate_override: null | number;
  override_reason: null | string;
  effective_from: string;
  effective_until: null | string;
  notes: null | string;
  version_no: number;
  archived_at: null | string;
}

export interface PayrollExportBatchListItem {
  id: string;
  batch_no: string;
  provider_key: string;
  status: string;
  period_start: string;
  period_end: string;
  item_count: number;
  total_amount: number;
  currency_code: string;
  generated_at: null | string;
  queued_at: null | string;
  dispatched_at: null | string;
}

export interface PayrollExportItemRead {
  id: string;
  actual_record_id: string;
  employee_id: null | string;
  pay_code: string;
  description: null | string;
  quantity: number;
  unit_code: string;
  amount_total: number;
  currency_code: string;
  payload_json: Record<string, unknown>;
  source_ref_json: Record<string, unknown>;
}

export interface PayrollExportBatchRead extends PayrollExportBatchListItem {
  endpoint_id: null | string;
  job_id: null | string;
  source_hash: string;
  notes: null | string;
  version_no: number;
  items: PayrollExportItemRead[];
  document_ids: string[];
}

export interface PayrollPayslipArchiveRead {
  id: string;
  employee_id: string;
  export_batch_id: null | string;
  provider_key: string;
  period_start: string;
  period_end: string;
  archive_status_code: string;
  source_document_id: null | string;
  notes: null | string;
  superseded_by_archive_id: null | string;
  version_no: number;
}

export interface PayrollReconciliationRowRead {
  employee_id: string;
  export_employee_code: null | string;
  pay_profile_id: null | string;
  approved_actual_count: number;
  exported_item_count: number;
  archived_payslip_count: number;
  payable_minutes: number;
  exported_amount_total: number;
  allowance_amount_total: number;
  outstanding_advance_total: number;
  overtime_balance_minutes: number;
  missing_export: boolean;
  missing_payslip: boolean;
  mismatch_codes: string[];
}

export class FinancePayrollApiError extends Error {
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
  return `finance-payroll-${Math.random().toString(36).slice(2, 10)}`;
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
      throw new FinancePayrollApiError(response.status, payload.error);
    }
    throw new FinancePayrollApiError(response.status, { message_key: "errors.platform.internal", details: {} });
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

export function listPayrollTariffTables(tenantId: string, accessToken: string, filters: Record<string, unknown>) {
  return request<PayrollTariffTableListItem[]>(`/api/finance/tenants/${tenantId}/payroll/tariff-tables${queryString(filters)}`, accessToken);
}

export function createPayrollTariffTable(tenantId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<PayrollTariffTableRead>(`/api/finance/tenants/${tenantId}/payroll/tariff-tables`, accessToken, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function addPayrollTariffRate(tenantId: string, tariffTableId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<PayrollTariffTableRead>(`/api/finance/tenants/${tenantId}/payroll/tariff-tables/${tariffTableId}/rates`, accessToken, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function addPayrollSurchargeRule(tenantId: string, tariffTableId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<PayrollTariffTableRead>(`/api/finance/tenants/${tenantId}/payroll/tariff-tables/${tariffTableId}/surcharge-rules`, accessToken, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listEmployeePayProfiles(tenantId: string, accessToken: string, filters: Record<string, unknown>) {
  return request<EmployeePayProfileRead[]>(`/api/finance/tenants/${tenantId}/payroll/pay-profiles${queryString(filters)}`, accessToken);
}

export function createEmployeePayProfile(tenantId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<EmployeePayProfileRead>(`/api/finance/tenants/${tenantId}/payroll/pay-profiles`, accessToken, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listPayrollExportBatches(tenantId: string, accessToken: string, filters: Record<string, unknown>) {
  return request<PayrollExportBatchListItem[]>(`/api/finance/tenants/${tenantId}/payroll/export-batches${queryString(filters)}`, accessToken);
}

export function generatePayrollExportBatch(tenantId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<PayrollExportBatchRead>(`/api/finance/tenants/${tenantId}/payroll/export-batches`, accessToken, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listPayrollPayslipArchives(tenantId: string, accessToken: string, filters: Record<string, unknown>) {
  return request<PayrollPayslipArchiveRead[]>(`/api/finance/tenants/${tenantId}/payroll/payslip-archives${queryString(filters)}`, accessToken);
}

export function createPayrollPayslipArchive(tenantId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<PayrollPayslipArchiveRead>(`/api/finance/tenants/${tenantId}/payroll/payslip-archives`, accessToken, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listPayrollReconciliationRows(tenantId: string, accessToken: string, filters: Record<string, unknown>) {
  return request<PayrollReconciliationRowRead[]>(`/api/finance/tenants/${tenantId}/payroll/reconciliation${queryString(filters)}`, accessToken);
}
