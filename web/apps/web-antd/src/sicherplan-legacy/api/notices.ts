import { webAppConfig } from "@/config/env";

import { AuthApiError } from "@/api/auth";

export interface NoticeAttachmentRead {
  document_id: string;
  title: string;
  file_name: string | null;
  content_type: string | null;
  current_version_no: number | null;
}

export interface NoticeLinkRead {
  id: string;
  label: string;
  url: string;
  link_type: string;
}

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
  opened_at: string | null;
  attachment_document_ids: string[];
  attachments: NoticeAttachmentRead[];
  links: NoticeLinkRead[];
}

export interface NoticeRead extends NoticeListItem {
  body: string;
}

export interface NoticeFeedStatusRead {
  total_count: number;
  unread_count: number;
  mandatory_unacknowledged_count: number;
  blocking_required: boolean;
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
  return `sp-notice-${Date.now()}`;
}

function isApiErrorEnvelope(value: unknown): value is ApiErrorEnvelope {
  if (!value || typeof value !== "object") {
    return false;
  }
  const error = (value as Record<string, unknown>).error;
  return !!error && typeof error === "object" && typeof (error as Record<string, unknown>).message_key === "string";
}

async function request<T>(
  path: string,
  accessToken: string,
  options?: {
    method?: string;
    body?: unknown;
    responseType?: "json" | "blob";
  },
): Promise<T> {
  const response = await fetch(`${webAppConfig.apiBaseUrl}${path}`, {
    method: options?.method ?? "GET",
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
      "X-Request-Id": generateRequestId(),
    },
    body: options?.body == null ? undefined : JSON.stringify(options.body),
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
  if (options?.responseType === "blob") {
    return (await response.blob()) as T;
  }
  return (await response.json()) as T;
}

export function listAdminNotices(tenantId: string, accessToken: string) {
  return request<NoticeListItem[]>(`/api/platform/tenants/${tenantId}/info/notices`, accessToken);
}

export function listMyNoticeFeed(tenantId: string, accessToken: string) {
  return request<NoticeListItem[]>(`/api/platform/tenants/${tenantId}/info/notices/my/feed`, accessToken);
}

export function getMyNoticeFeedStatus(tenantId: string, accessToken: string) {
  return request<NoticeFeedStatusRead>(`/api/platform/tenants/${tenantId}/info/notices/my/feed/status`, accessToken);
}

export function getVisibleNotice(tenantId: string, noticeId: string, accessToken: string) {
  return request<NoticeRead>(`/api/platform/tenants/${tenantId}/info/notices/my/feed/${noticeId}`, accessToken);
}

export function createNotice(
  tenantId: string,
  accessToken: string,
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
  return request<NoticeRead>(`/api/platform/tenants/${tenantId}/info/notices`, accessToken, {
    method: "POST",
    body: payload,
  });
}

export function publishNotice(tenantId: string, noticeId: string, accessToken: string) {
  return request<NoticeRead>(`/api/platform/tenants/${tenantId}/info/notices/${noticeId}/publish`, accessToken, {
    method: "POST",
    body: {},
  });
}

export function acknowledgeNotice(tenantId: string, noticeId: string, accessToken: string, acknowledgementText?: string) {
  return request(`/api/platform/tenants/${tenantId}/info/notices/${noticeId}/acknowledge`, accessToken, {
    method: "POST",
    body: { acknowledgement_text: acknowledgementText ?? null },
  });
}

export function openNotice(tenantId: string, noticeId: string, accessToken: string) {
  return request(`/api/platform/tenants/${tenantId}/info/notices/${noticeId}/open`, accessToken, {
    method: "POST",
    body: {},
  });
}

export function downloadNoticeAttachment(tenantId: string, documentId: string, versionNo: number, accessToken: string) {
  return request<Blob>(
    `/api/platform/tenants/${tenantId}/documents/${documentId}/versions/${versionNo}/download`,
    accessToken,
    { responseType: "blob" },
  );
}
