import { webAppConfig } from "@/config/env";

export interface ApplicantListItem {
  id: string;
  tenant_id: string;
  application_no: string;
  source_channel: string;
  source_detail: string | null;
  locale: string;
  converted_employee_id: string | null;
  first_name: string;
  last_name: string;
  email: string;
  desired_role: string | null;
  availability_date: string | null;
  status: string;
  created_at: string;
  updated_at: string;
  version_no: number;
}

export interface ApplicantActivityEventRead {
  id: string;
  tenant_id: string;
  applicant_id: string;
  event_type: string;
  from_status: string | null;
  to_status: string | null;
  note: string | null;
  decision_reason: string | null;
  interview_scheduled_at: string | null;
  hiring_target_date: string | null;
  metadata_json: Record<string, unknown>;
  actor_user_id: string | null;
  created_at: string;
}

export interface ApplicantAttachmentRead {
  document_id: string;
  relation_type: string;
  label: string | null;
  title: string;
  document_type_key: string | null;
  file_name: string | null;
  content_type: string | null;
  current_version_no: number | null;
  linked_at: string | null;
}

export interface ApplicantConsentEvidenceRead {
  consent_granted: boolean;
  consent_at: string;
  policy_ref: string;
  policy_version: string;
  submitted_origin: string | null;
  submitted_ip: string | null;
  submitted_user_agent: string | null;
}

export interface ApplicantRead extends ApplicantListItem {
  submission_key: string;
  phone: string | null;
  message: string | null;
  gdpr_consent_granted: boolean;
  gdpr_consent_at: string;
  gdpr_policy_ref: string;
  gdpr_policy_version: string;
  custom_fields_json: Record<string, unknown>;
  metadata_json: Record<string, unknown>;
  submitted_ip: string | null;
  submitted_origin: string | null;
  submitted_user_agent: string | null;
  archived_at: string | null;
}

export interface ApplicantDetailRead {
  applicant: ApplicantRead;
  consent: ApplicantConsentEvidenceRead;
  attachments: ApplicantAttachmentRead[];
  events: ApplicantActivityEventRead[];
  next_allowed_statuses: string[];
}

export interface ApplicantTransitionPayload {
  to_status: string;
  note?: string | null;
  decision_reason?: string | null;
  interview_scheduled_at?: string | null;
  hiring_target_date?: string | null;
}

export interface ApplicantActivityPayload {
  activity_type: "recruiter_note" | "interview_note";
  note: string;
  decision_reason?: string | null;
  interview_scheduled_at?: string | null;
  hiring_target_date?: string | null;
}

export interface RecruitingApplicantFilterParams {
  status?: string;
  source_channel?: string;
  search?: string;
}

interface ApiErrorEnvelope {
  error: {
    code: string;
    message_key: string;
    request_id: string;
    details: Record<string, unknown>;
  };
}

export class RecruitingAdminApiError extends Error {
  readonly statusCode: number;
  readonly code: string;
  readonly messageKey: string;
  readonly details: Record<string, unknown>;

  constructor(statusCode: number, payload: ApiErrorEnvelope["error"]) {
    super(payload.message_key);
    this.statusCode = statusCode;
    this.code = payload.code;
    this.messageKey = payload.message_key;
    this.details = payload.details;
  }
}

function generateRequestId() {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }

  return `sp-recruiting-${Date.now()}`;
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
  },
): Promise<T> {
  const response = await fetch(`${webAppConfig.apiBaseUrl}${path}`, {
    method: options?.method ?? "GET",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
      "X-Request-Id": generateRequestId(),
    },
    body: options?.body == null ? undefined : JSON.stringify(options.body),
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as unknown;

    if (isApiErrorEnvelope(payload)) {
      throw new RecruitingAdminApiError(response.status, payload.error);
    }

    throw new RecruitingAdminApiError(response.status, {
      code: "platform.internal",
      message_key: "errors.platform.internal",
      request_id: "",
      details: {},
    });
  }

  return (await response.json()) as T;
}

function buildQuery(params: RecruitingApplicantFilterParams) {
  const query = new URLSearchParams();
  if (params.status) query.set("status", params.status);
  if (params.source_channel) query.set("source_channel", params.source_channel);
  if (params.search) query.set("search", params.search);
  const serialized = query.toString();
  return serialized ? `?${serialized}` : "";
}

export function listApplicants(tenantId: string, accessToken: string, params: RecruitingApplicantFilterParams) {
  return request<ApplicantListItem[]>(
    `/api/recruiting/tenants/${tenantId}/applicants${buildQuery(params)}`,
    accessToken,
  );
}

export function getApplicantDetail(tenantId: string, applicantId: string, accessToken: string) {
  return request<ApplicantDetailRead>(`/api/recruiting/tenants/${tenantId}/applicants/${applicantId}`, accessToken);
}

export function transitionApplicant(
  tenantId: string,
  applicantId: string,
  accessToken: string,
  payload: ApplicantTransitionPayload,
) {
  return request<{ applicant: ApplicantListItem; events: ApplicantActivityEventRead[] }>(
    `/api/recruiting/tenants/${tenantId}/applicants/${applicantId}/transitions`,
    accessToken,
    {
      method: "POST",
      body: payload,
    },
  );
}

export function addApplicantActivity(
  tenantId: string,
  applicantId: string,
  accessToken: string,
  payload: ApplicantActivityPayload,
) {
  return request<ApplicantActivityEventRead>(
    `/api/recruiting/tenants/${tenantId}/applicants/${applicantId}/activities`,
    accessToken,
    {
      method: "POST",
      body: payload,
    },
  );
}

function extractFileName(contentDisposition: string | null, fallback: string) {
  if (!contentDisposition) {
    return fallback;
  }

  const match = contentDisposition.match(/filename=\"?([^\";]+)\"?/i);
  return match?.[1] ?? fallback;
}

export async function downloadApplicantAttachment(
  tenantId: string,
  documentId: string,
  versionNo: number,
  accessToken: string,
) {
  const response = await fetch(
    `${webAppConfig.apiBaseUrl}/api/platform/tenants/${tenantId}/documents/${documentId}/versions/${versionNo}/download`,
    {
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "X-Request-Id": generateRequestId(),
      },
    },
  );

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as unknown;
    if (isApiErrorEnvelope(payload)) {
      throw new RecruitingAdminApiError(response.status, payload.error);
    }
    throw new RecruitingAdminApiError(response.status, {
      code: "platform.internal",
      message_key: "errors.platform.internal",
      request_id: "",
      details: {},
    });
  }

  const blob = await response.blob();
  return {
    blob,
    contentType: response.headers.get("content-type") ?? blob.type,
    fileName: extractFileName(response.headers.get("content-disposition"), `${documentId}-${versionNo}`),
  };
}
