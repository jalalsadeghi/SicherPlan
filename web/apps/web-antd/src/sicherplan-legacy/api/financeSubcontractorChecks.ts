import { webAppConfig } from "@/config/env";

export interface FinanceSubcontractorInvoiceCheckLineRead {
  id: string;
  assignment_id: string | null;
  actual_record_id: string | null;
  service_date: string;
  label: string;
  billing_unit_code: string;
  assigned_minutes: number;
  actual_minutes: number;
  approved_minutes: number;
  expected_quantity: string;
  actual_quantity: string;
  approved_quantity: string;
  unit_price: string | null;
  expected_amount: string;
  approved_amount: string;
  variance_amount: string;
  comparison_state_code: string;
  variance_reason_codes_json: string[];
}

export interface FinanceSubcontractorInvoiceCheckNoteRead {
  id: string;
  note_kind_code: string;
  note_text: string;
  created_at: string;
  created_by_user_id: string | null;
}

export interface FinanceSubcontractorInvoiceCheckRead {
  id: string;
  subcontractor_id: string;
  check_no: string;
  period_start: string;
  period_end: string;
  period_label: string;
  status_code: string;
  assigned_minutes_total: number;
  actual_minutes_total: number;
  approved_minutes_total: number;
  expected_amount_total: string;
  approved_amount_total: string;
  comparison_variance_amount: string;
  submitted_invoice_ref: string | null;
  submitted_invoice_amount: string | null;
  submitted_variance_amount: string | null;
  submitted_invoice_currency_code: string | null;
  review_reason_codes_json: string[];
  last_generated_at: string | null;
  approved_at: string | null;
  released_at: string | null;
  lines: FinanceSubcontractorInvoiceCheckLineRead[];
  notes: FinanceSubcontractorInvoiceCheckNoteRead[];
}

export class FinanceSubcontractorChecksApiError extends Error {
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
  return `finance-subcontractor-checks-${Math.random().toString(36).slice(2, 10)}`;
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
      throw new FinanceSubcontractorChecksApiError(response.status, payload.error);
    }
    throw new FinanceSubcontractorChecksApiError(response.status, { message_key: "errors.platform.internal", details: {} });
  }
  return response.json() as Promise<T>;
}

function queryString(params: Record<string, unknown>) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === null || value === undefined || value === "") {
      return;
    }
    query.set(key, String(value));
  });
  const serialized = query.toString();
  return serialized ? `?${serialized}` : "";
}

export function listFinanceSubcontractorInvoiceChecks(tenantId: string, accessToken: string, filters: Record<string, unknown>) {
  return request<FinanceSubcontractorInvoiceCheckRead[]>(
    `/api/finance/tenants/${tenantId}/subcontractor-invoice-checks${queryString(filters)}`,
    accessToken,
  );
}

export function getFinanceSubcontractorInvoiceCheck(tenantId: string, invoiceCheckId: string, accessToken: string) {
  return request<FinanceSubcontractorInvoiceCheckRead>(
    `/api/finance/tenants/${tenantId}/subcontractor-invoice-checks/${invoiceCheckId}`,
    accessToken,
  );
}

export function generateFinanceSubcontractorInvoiceCheck(tenantId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<FinanceSubcontractorInvoiceCheckRead>(`/api/finance/tenants/${tenantId}/subcontractor-invoice-checks/generate`, accessToken, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateFinanceSubcontractorSubmittedInvoice(tenantId: string, invoiceCheckId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<FinanceSubcontractorInvoiceCheckRead>(
    `/api/finance/tenants/${tenantId}/subcontractor-invoice-checks/${invoiceCheckId}/submitted-invoice`,
    accessToken,
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export function addFinanceSubcontractorInvoiceCheckNote(tenantId: string, invoiceCheckId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<FinanceSubcontractorInvoiceCheckRead>(
    `/api/finance/tenants/${tenantId}/subcontractor-invoice-checks/${invoiceCheckId}/notes`,
    accessToken,
    { method: "POST", body: JSON.stringify(payload) },
  );
}

export function changeFinanceSubcontractorInvoiceCheckStatus(tenantId: string, invoiceCheckId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<FinanceSubcontractorInvoiceCheckRead>(
    `/api/finance/tenants/${tenantId}/subcontractor-invoice-checks/${invoiceCheckId}/status`,
    accessToken,
    { method: "POST", body: JSON.stringify(payload) },
  );
}
