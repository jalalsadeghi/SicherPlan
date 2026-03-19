import { webAppConfig } from "@/config/env";
import type { AppRole } from "@/types/roles";

export interface NoticeListItem {
  id: string;
  title: string;
  summary: string | null;
  language_code: string;
  mandatory_acknowledgement: boolean;
  publish_from: string | null;
  publish_until: string | null;
  published_at: string | null;
  status: string;
  acknowledged_at: string | null;
  attachment_document_ids: string[];
}

export interface NoticeRead extends NoticeListItem {
  body: string;
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
  return `sp-${Date.now()}`;
}

function buildHeaders(role: AppRole, tenantId?: string | null): HeadersInit {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "X-Actor-Role": role,
    "X-Request-Id": generateRequestId(),
  };
  if (tenantId) {
    headers["X-Tenant-Id"] = tenantId;
  }
  return headers;
}

function isApiErrorEnvelope(value: unknown): value is ApiErrorEnvelope {
  if (!value || typeof value !== "object") return false;
  const error = (value as Record<string, unknown>).error;
  return !!error && typeof error === "object" && typeof (error as Record<string, unknown>).message_key === "string";
}

async function request<T>(path: string, role: AppRole, tenantId: string | null, method = "GET", body?: unknown): Promise<T> {
  const response = await fetch(`${webAppConfig.apiBaseUrl}${path}`, {
    method,
    headers: buildHeaders(role, tenantId),
    body: body == null ? undefined : JSON.stringify(body),
  });
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as unknown;
    if (isApiErrorEnvelope(payload)) {
      throw new Error((payload as ApiErrorEnvelope).error.message_key);
    }
    throw new Error("errors.platform.internal");
  }
  return (await response.json()) as T;
}

export function listAdminNotices(tenantId: string, role: AppRole) {
  return request<NoticeListItem[]>(`/api/platform/tenants/${tenantId}/info/notices`, role, tenantId);
}

export function createNotice(
  tenantId: string,
  role: AppRole,
  payload: {
    tenant_id: string;
    title: string;
    summary?: string | null;
    body: string;
    language_code: string;
    mandatory_acknowledgement: boolean;
    audiences: Array<{ audience_kind: string; target_value?: string | null }>;
    curated_links: Array<{ label: string; url: string }>;
    attachment_document_ids: string[];
  },
) {
  return request<NoticeRead>(`/api/platform/tenants/${tenantId}/info/notices`, role, tenantId, "POST", payload);
}

export function publishNotice(tenantId: string, noticeId: string, role: AppRole) {
  return request<NoticeRead>(
    `/api/platform/tenants/${tenantId}/info/notices/${noticeId}/publish`,
    role,
    tenantId,
    "POST",
    {},
  );
}

export function listMyNoticeFeed(tenantId: string, role: AppRole) {
  return request<NoticeListItem[]>(`/api/platform/tenants/${tenantId}/info/notices/my/feed`, role, tenantId);
}

export function acknowledgeNotice(tenantId: string, noticeId: string, role: AppRole) {
  return request(
    `/api/platform/tenants/${tenantId}/info/notices/${noticeId}/acknowledge`,
    role,
    tenantId,
    "POST",
    {},
  );
}
