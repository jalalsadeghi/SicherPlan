import { webAppConfig } from "@/config/env";

import { AuthApiError } from "@/api/auth";

export interface CustomerPortalCollectionSourceRead {
  domain_key: string;
  source_module_key: string;
  availability_status: string;
  released_only: boolean;
  customer_scoped: boolean;
  docs_backed_outputs: boolean;
  message_key: string;
}

export interface CustomerPortalDocumentRefRead {
  document_id: string;
  title: string;
  document_type_key: string | null;
  file_name: string | null;
  content_type: string | null;
  current_version_no: number | null;
}

export interface CustomerPortalHistoryEntryRead {
  id: string;
  entry_type: string;
  title: string;
  summary: string;
  created_at: string;
  attachments: CustomerPortalDocumentRefRead[];
}

export interface CustomerPortalHistoryCollectionRead {
  customer_id: string;
  items: CustomerPortalHistoryEntryRead[];
}

export interface CustomerPortalOrderListItemRead {
  id: string;
  customer_id: string;
  order_number: string;
  title: string;
  service_from: string | null;
  service_to: string | null;
  released_at: string;
  status: string;
}

export interface CustomerPortalScheduleListItemRead {
  id: string;
  customer_id: string;
  order_id: string;
  schedule_date: string;
  shift_label: string;
  site_label: string | null;
  released_at: string;
  status: string;
}

export interface CustomerPortalWatchbookEntryRead {
  id: string;
  customer_id: string;
  log_date: string;
  occurred_at: string;
  entry_type_code: string | null;
  summary: string;
  status: string;
  personal_names_released: boolean;
  pdf_document_id: string | null;
}

export interface CustomerPortalWatchbookEntryCreate {
  entry_type_code: "customer_note";
  narrative: string;
}

export interface CustomerPortalTimesheetRead {
  id: string;
  customer_id: string;
  period_start: string;
  period_end: string;
  released_at: string;
  status: string;
  total_minutes: number | null;
  documents: CustomerPortalDocumentRefRead[];
}

export interface CustomerPortalInvoiceRead {
  id: string;
  customer_id: string;
  invoice_no: string;
  issue_date: string;
  due_date: string;
  released_at: string | null;
  status: string;
  currency_code: string;
  total_amount: number;
  documents: CustomerPortalDocumentRefRead[];
}

export interface CustomerPortalReportPackageRead {
  id: string;
  customer_id: string;
  title: string;
  category_code: string | null;
  published_at: string;
  status: string;
  documents: CustomerPortalDocumentRefRead[];
}

export interface CustomerPortalOrderCollectionRead {
  customer_id: string;
  source: CustomerPortalCollectionSourceRead;
  items: CustomerPortalOrderListItemRead[];
}

export interface CustomerPortalScheduleCollectionRead {
  customer_id: string;
  source: CustomerPortalCollectionSourceRead;
  items: CustomerPortalScheduleListItemRead[];
}

export interface CustomerPortalWatchbookCollectionRead {
  customer_id: string;
  source: CustomerPortalCollectionSourceRead;
  items: CustomerPortalWatchbookEntryRead[];
}

export interface CustomerPortalTimesheetCollectionRead {
  customer_id: string;
  source: CustomerPortalCollectionSourceRead;
  items: CustomerPortalTimesheetRead[];
}

export interface CustomerPortalInvoiceCollectionRead {
  customer_id: string;
  source: CustomerPortalCollectionSourceRead;
  items: CustomerPortalInvoiceRead[];
}

export interface CustomerPortalReportPackageCollectionRead {
  customer_id: string;
  source: CustomerPortalCollectionSourceRead;
  items: CustomerPortalReportPackageRead[];
}

interface ApiErrorEnvelope {
  error: {
    code: string;
    message_key: string;
    request_id: string;
    details: Record<string, unknown>;
  };
}

function generateRequestId() {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }

  return `sp-portal-${Date.now()}`;
}

function isApiErrorEnvelope(value: unknown): value is ApiErrorEnvelope {
  if (!value || typeof value !== "object") {
    return false;
  }

  const error = (value as Record<string, unknown>).error;
  return !!error && typeof error === "object" && typeof (error as Record<string, unknown>).message_key === "string";
}

async function request<T>(path: string, accessToken: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${webAppConfig.apiBaseUrl}${path}`, {
    method: init?.method ?? "GET",
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
      "X-Request-Id": generateRequestId(),
      ...(init?.headers ?? {}),
    },
    body: init?.body,
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as unknown;
    if (isApiErrorEnvelope(payload)) {
      throw new AuthApiError(response.status, payload.error);
    }
    throw new AuthApiError(response.status, {
      code: "platform.internal",
      message_key: "errors.platform.internal",
      request_id: "",
      details: {},
    });
  }

  return (await response.json()) as T;
}

export function getCustomerPortalOrders(accessToken: string) {
  return request<CustomerPortalOrderCollectionRead>("/api/portal/customer/orders", accessToken);
}

export function getCustomerPortalSchedules(accessToken: string) {
  return request<CustomerPortalScheduleCollectionRead>("/api/portal/customer/schedules", accessToken);
}

export function getCustomerPortalWatchbooks(accessToken: string) {
  return request<CustomerPortalWatchbookCollectionRead>("/api/portal/customer/watchbooks", accessToken);
}

export function getCustomerPortalTimesheets(accessToken: string) {
  return request<CustomerPortalTimesheetCollectionRead>("/api/portal/customer/timesheets", accessToken);
}

export function getCustomerPortalInvoices(accessToken: string) {
  return request<CustomerPortalInvoiceCollectionRead>("/api/portal/customer/invoices", accessToken);
}

export function getCustomerPortalReports(accessToken: string) {
  return request<CustomerPortalReportPackageCollectionRead>("/api/portal/customer/reports", accessToken);
}

export function getCustomerPortalHistory(accessToken: string) {
  return request<CustomerPortalHistoryCollectionRead>("/api/portal/customer/history", accessToken);
}

async function download(path: string, accessToken: string) {
  const response = await fetch(`${webAppConfig.apiBaseUrl}${path}`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "X-Request-Id": generateRequestId(),
    },
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as unknown;
    if (isApiErrorEnvelope(payload)) {
      throw new AuthApiError(response.status, payload.error);
    }
    throw new AuthApiError(response.status, {
      code: "platform.internal",
      message_key: "errors.platform.internal",
      request_id: "",
      details: {},
    });
  }

  return {
    blob: await response.blob(),
    fileName: response.headers.get("content-disposition")?.match(/filename=\"?([^"]+)\"?/)?.[1] ?? "document.pdf",
  };
}

export function downloadCustomerPortalTimesheetDocument(
  accessToken: string,
  timesheetId: string,
  documentId: string,
  versionNo: number,
) {
  return download(`/api/portal/customer/timesheets/${timesheetId}/documents/${documentId}/versions/${versionNo}/download`, accessToken);
}

export function downloadCustomerPortalInvoiceDocument(
  accessToken: string,
  invoiceId: string,
  documentId: string,
  versionNo: number,
) {
  return download(`/api/portal/customer/invoices/${invoiceId}/documents/${documentId}/versions/${versionNo}/download`, accessToken);
}

export function createCustomerPortalWatchbookEntry(
  accessToken: string,
  watchbookId: string,
  payload: CustomerPortalWatchbookEntryCreate,
) {
  return request(`/api/portal/customer/watchbooks/${watchbookId}/entries`, accessToken, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
