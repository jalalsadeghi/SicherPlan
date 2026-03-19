import { webAppConfig } from "@/config/env";

export interface RecruitingApplicantFieldOption {
  value: string;
  label_de: string;
  label_en: string;
}

export interface RecruitingApplicantFieldConfig {
  key: string;
  type: "date" | "email" | "select" | "tel" | "text" | "textarea";
  label_de: string;
  label_en: string;
  visible: boolean;
  required: boolean;
  options: RecruitingApplicantFieldOption[];
}

export interface RecruitingApplicantFormConfig {
  tenant_id: string;
  tenant_code: string;
  tenant_name: string;
  default_locale: "de" | "en";
  source_channel: string;
  source_detail: string | null;
  gdpr_policy_ref: string;
  gdpr_policy_version: string;
  gdpr_policy_url_de: string | null;
  gdpr_policy_url_en: string | null;
  max_attachment_count: number;
  max_attachment_size_bytes: number;
  allowed_attachment_types: string[];
  allowed_embed_origins: string[];
  fields: RecruitingApplicantFieldConfig[];
  confirmation_message_key: string;
}

export interface RecruitingApplicantAttachmentPayload {
  kind: string;
  file_name: string;
  content_type: string;
  content_base64: string;
  label: string | null;
}

export interface RecruitingApplicantSubmissionPayload {
  submission_key: string;
  locale: "de" | "en";
  first_name?: string | null;
  last_name?: string | null;
  email?: string | null;
  phone?: string | null;
  desired_role?: string | null;
  availability_date?: string | null;
  message?: string | null;
  additional_fields: Record<string, unknown>;
  attachments: RecruitingApplicantAttachmentPayload[];
  gdpr_consent_confirmed: boolean;
  gdpr_policy_ref: string;
  gdpr_policy_version: string;
}

export interface RecruitingApplicantSubmissionResponse {
  applicant_id: string;
  application_no: string;
  status: string;
  message_key: string;
}

interface ApiErrorEnvelope {
  error: {
    code: string;
    message_key: string;
    request_id: string;
    details: Record<string, unknown>;
  };
}

export class RecruitingPublicApiError extends Error {
  status: number;
  code: string;
  messageKey: string;
  details: Record<string, unknown>;
  requestId: string;

  constructor(status: number, payload: ApiErrorEnvelope["error"]) {
    super(payload.message_key);
    this.status = status;
    this.code = payload.code;
    this.messageKey = payload.message_key;
    this.details = payload.details;
    this.requestId = payload.request_id;
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

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${webAppConfig.apiBaseUrl}${path}`, {
    headers: {
      "Content-Type": "application/json",
      "X-Request-Id": generateRequestId(),
      ...(init?.headers ?? {}),
    },
    ...init,
  });
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as unknown;
    if (isApiErrorEnvelope(payload)) {
      throw new RecruitingPublicApiError(response.status, payload.error);
    }
    throw new RecruitingPublicApiError(response.status, {
      code: "platform.internal",
      message_key: "errors.platform.internal",
      request_id: "",
      details: {},
    });
  }
  return (await response.json()) as T;
}

export function getRecruitingApplicantForm(tenantCode: string) {
  return request<RecruitingApplicantFormConfig>(`/api/public/recruiting/applicant-form/${tenantCode}`);
}

export function submitRecruitingApplicantForm(
  tenantCode: string,
  payload: RecruitingApplicantSubmissionPayload,
) {
  return request<RecruitingApplicantSubmissionResponse>(
    `/api/public/recruiting/applicant-form/${tenantCode}`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}
