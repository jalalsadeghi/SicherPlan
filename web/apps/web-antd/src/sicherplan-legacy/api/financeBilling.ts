import { webAppConfig } from "@/config/env";

export interface FinanceBillingTimesheetLineRead {
  id: string;
  actual_record_id: string;
  shift_id: string;
  order_id: null | string;
  planning_record_id: null | string;
  sort_order: number;
  service_date: string;
  planning_mode_code: null | string;
  line_label: string;
  line_description: string;
  planned_minutes: number;
  actual_minutes: number;
  billable_minutes: number;
  quantity: number;
  unit_code: string;
  customer_safe_flag: boolean;
  personal_names_released: boolean;
}

export interface FinanceBillingTimesheetRead {
  id: string;
  customer_id: string;
  order_id: null | string;
  planning_record_id: null | string;
  billing_granularity_code: string;
  period_start: string;
  period_end: string;
  headline: string;
  total_planned_minutes: number;
  total_actual_minutes: number;
  total_billable_minutes: number;
  release_state_code: string;
  customer_visible_flag: boolean;
  released_at: null | string;
  source_document_id: null | string;
  version_no: number;
  lines: FinanceBillingTimesheetLineRead[];
}

export interface FinanceBillingInvoiceLineRead {
  id: string;
  timesheet_line_id: null | string;
  source_actual_id: null | string;
  sort_order: number;
  line_kind_code: string;
  description: string;
  quantity: number;
  unit_code: string;
  unit_price: number;
  tax_rate: number;
  net_amount: number;
  tax_amount: number;
  gross_amount: number;
}

export interface FinanceBillingInvoiceRead {
  id: string;
  customer_id: string;
  timesheet_id: null | string;
  invoice_no: string;
  issue_date: string;
  due_date: string;
  period_start: string;
  period_end: string;
  currency_code: string;
  layout_code: null | string;
  invoice_status_code: string;
  subtotal_amount: number;
  tax_amount: number;
  total_amount: number;
  customer_visible_flag: boolean;
  issued_at: null | string;
  released_at: null | string;
  delivery_status_code: string;
  version_no: number;
  invoice_email: null | string;
  dispatch_method_code: null | string;
  e_invoice_enabled: boolean;
  leitweg_id: null | string;
  payment_terms_days: null | number;
  invoice_party_snapshot_json: Record<string, unknown>;
  billing_profile_snapshot_json: Record<string, unknown>;
  delivery_context_json: Record<string, unknown>;
  lines: FinanceBillingInvoiceLineRead[];
}

export class FinanceBillingApiError extends Error {
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
  return `finance-billing-${Math.random().toString(36).slice(2, 10)}`;
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
      throw new FinanceBillingApiError(response.status, payload.error);
    }
    throw new FinanceBillingApiError(response.status, { message_key: "errors.platform.internal", details: {} });
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

export function listFinanceBillingTimesheets(tenantId: string, accessToken: string, filters: Record<string, unknown>) {
  return request<FinanceBillingTimesheetRead[]>(`/api/finance/tenants/${tenantId}/billing/timesheets${queryString(filters)}`, accessToken);
}

export function generateFinanceBillingTimesheet(tenantId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<FinanceBillingTimesheetRead>(`/api/finance/tenants/${tenantId}/billing/timesheets`, accessToken, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function releaseFinanceBillingTimesheet(tenantId: string, timesheetId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<FinanceBillingTimesheetRead>(`/api/finance/tenants/${tenantId}/billing/timesheets/${timesheetId}/release`, accessToken, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listFinanceBillingInvoices(tenantId: string, accessToken: string, filters: Record<string, unknown>) {
  return request<FinanceBillingInvoiceRead[]>(`/api/finance/tenants/${tenantId}/billing/invoices${queryString(filters)}`, accessToken);
}

export function generateFinanceBillingInvoice(tenantId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<FinanceBillingInvoiceRead>(`/api/finance/tenants/${tenantId}/billing/invoices`, accessToken, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function issueFinanceBillingInvoice(tenantId: string, invoiceId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<FinanceBillingInvoiceRead>(`/api/finance/tenants/${tenantId}/billing/invoices/${invoiceId}/issue`, accessToken, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function releaseFinanceBillingInvoice(tenantId: string, invoiceId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<FinanceBillingInvoiceRead>(`/api/finance/tenants/${tenantId}/billing/invoices/${invoiceId}/release`, accessToken, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function queueFinanceBillingInvoiceDispatch(tenantId: string, invoiceId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<FinanceBillingInvoiceRead>(`/api/finance/tenants/${tenantId}/billing/invoices/${invoiceId}/queue-dispatch`, accessToken, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
