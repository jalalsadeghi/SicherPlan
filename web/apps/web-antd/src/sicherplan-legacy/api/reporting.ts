import { webAppConfig } from "@/config/env";

export interface ReportingRow {
  [key: string]: null | number | string;
}

export interface ReportingDeliveryJob {
  completed_at: null | string;
  document_id: null | string;
  document_title: null | string;
  endpoint_id: null | string;
  job_id: string;
  job_status: string;
  report_key: string;
  requested_at: string;
  requested_by_user_id: null | string;
  row_count: number;
  scheduled_for: null | string;
  started_at: null | string;
  target_label: null | string;
  tenant_id: string;
}

export class ReportingApiError extends Error {
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
  return `reporting-${Math.random().toString(36).slice(2, 10)}`;
}

function isApiErrorEnvelope(payload: unknown): payload is { error: { message_key: string; details: Record<string, unknown> } } {
  return Boolean(payload && typeof payload === "object" && "error" in payload && typeof payload.error?.message_key === "string");
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

async function request<T>(path: string, accessToken: string): Promise<T> {
  const response = await fetch(`${webAppConfig.apiBaseUrl}${path}`, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
      "X-Request-Id": requestId(),
    },
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    if (isApiErrorEnvelope(payload)) {
      throw new ReportingApiError(response.status, payload.error);
    }
    throw new ReportingApiError(response.status, { message_key: "errors.platform.internal", details: {} });
  }
  return response.json() as Promise<T>;
}

async function requestWithBody<T>(path: string, accessToken: string, body: Record<string, unknown>): Promise<T> {
  const response = await fetch(`${webAppConfig.apiBaseUrl}${path}`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
      "X-Request-Id": requestId(),
    },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    if (isApiErrorEnvelope(payload)) {
      throw new ReportingApiError(response.status, payload.error);
    }
    throw new ReportingApiError(response.status, { message_key: "errors.platform.internal", details: {} });
  }
  return response.json() as Promise<T>;
}

export function listReportingRows(reportKey: string, tenantId: string, accessToken: string, filters: Record<string, unknown>) {
  return request<ReportingRow[]>(`/api/reporting/tenants/${tenantId}/${reportKey}${queryString(filters)}`, accessToken);
}

export async function downloadReportingCsv(reportKey: string, tenantId: string, accessToken: string, filters: Record<string, unknown>) {
  const response = await fetch(`${webAppConfig.apiBaseUrl}/api/reporting/tenants/${tenantId}/${reportKey}/export${queryString(filters)}`, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "X-Request-Id": requestId(),
    },
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    if (isApiErrorEnvelope(payload)) {
      throw new ReportingApiError(response.status, payload.error);
    }
    throw new ReportingApiError(response.status, { message_key: "errors.platform.internal", details: {} });
  }
  const content = await response.text();
  return {
    content,
    fileName: response.headers.get("content-disposition")?.match(/filename=\"?([^\";]+)\"?/)?.[1] ?? `${reportKey}.csv`,
  };
}

export function queueReportingDeliveryJob(
  reportKey: string,
  tenantId: string,
  accessToken: string,
  filters: Record<string, unknown>,
  payload: Record<string, unknown>,
) {
  return requestWithBody<ReportingDeliveryJob>(
    `/api/reporting/tenants/${tenantId}/${reportKey}/delivery-jobs${queryString(filters)}`,
    accessToken,
    payload,
  );
}

export function listReportingDeliveryJobs(
  tenantId: string,
  accessToken: string,
  params: Record<string, unknown>,
) {
  return request<ReportingDeliveryJob[]>(`/api/reporting/tenants/${tenantId}/delivery-jobs${queryString(params)}`, accessToken);
}
