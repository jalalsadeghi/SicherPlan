import { webAppConfig } from "@/config/env";
import type { AppRole } from "@/types/roles";

export type LifecycleStatus = "active" | "inactive" | "archived";

export interface TenantListItem {
  id: string;
  code: string;
  name: string;
  status: LifecycleStatus | string;
  version_no: number;
}

export interface TenantRead extends TenantListItem {
  legal_name: string | null;
  default_locale: string;
  default_currency: string;
  timezone: string;
  archived_at: string | null;
}

export interface BranchRead {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  address_id: string | null;
  contact_email: string | null;
  contact_phone: string | null;
  status: LifecycleStatus | string;
  version_no: number;
  archived_at: string | null;
}

export interface MandateRead {
  id: string;
  tenant_id: string;
  branch_id: string;
  code: string;
  name: string;
  external_ref: string | null;
  notes: string | null;
  status: LifecycleStatus | string;
  version_no: number;
  archived_at: string | null;
}

export interface TenantSettingRead {
  id: string;
  tenant_id: string;
  key: string;
  value_json: Record<string, unknown>;
  status: LifecycleStatus | string;
  version_no: number;
  archived_at: string | null;
}

export interface LookupValueRead {
  id: string;
  tenant_id: string | null;
  domain: string;
  code: string;
  label: string;
  description: string | null;
  sort_order: number;
  status: LifecycleStatus | string;
  version_no: number;
  archived_at: string | null;
}

export interface TenantOnboardingPayload {
  tenant: {
    code: string;
    name: string;
    legal_name?: string | null;
    default_locale: string;
    default_currency: string;
    timezone: string;
  };
  initial_branch: {
    tenant_id: string;
    code: string;
    name: string;
    address_id?: string | null;
    contact_email?: string | null;
    contact_phone?: string | null;
  };
  initial_mandate: {
    tenant_id: string;
    branch_id: string;
    code: string;
    name: string;
    external_ref?: string | null;
    notes?: string | null;
  };
  initial_settings: Array<{
    tenant_id: string;
    key: string;
    value_json: Record<string, unknown>;
  }>;
}

export interface TenantUpdatePayload {
  name?: string | null;
  legal_name?: string | null;
  default_locale?: string | null;
  default_currency?: string | null;
  timezone?: string | null;
  status?: LifecycleStatus | string | null;
  archived_at?: string | null;
  version_no?: number | null;
}

export interface BranchCreatePayload {
  tenant_id: string;
  code: string;
  name: string;
  address_id?: string | null;
  contact_email?: string | null;
  contact_phone?: string | null;
}

export interface BranchUpdatePayload {
  name?: string | null;
  address_id?: string | null;
  contact_email?: string | null;
  contact_phone?: string | null;
  status?: LifecycleStatus | string | null;
  archived_at?: string | null;
  version_no?: number | null;
}

export interface MandateCreatePayload {
  tenant_id: string;
  branch_id: string;
  code: string;
  name: string;
  external_ref?: string | null;
  notes?: string | null;
}

export interface MandateUpdatePayload {
  name?: string | null;
  external_ref?: string | null;
  notes?: string | null;
  status?: LifecycleStatus | string | null;
  archived_at?: string | null;
  version_no?: number | null;
}

export interface TenantSettingCreatePayload {
  tenant_id: string;
  key: string;
  value_json: Record<string, unknown>;
}

export interface TenantSettingUpdatePayload {
  value_json?: Record<string, unknown>;
  version_no: number;
  status?: LifecycleStatus | string | null;
  archived_at?: string | null;
}

export interface LookupValueCreatePayload {
  tenant_id?: string | null;
  domain: string;
  code: string;
  label: string;
  description?: string | null;
  sort_order?: number;
}

export interface LookupValueUpdatePayload {
  label?: string | null;
  description?: string | null;
  sort_order?: number | null;
  version_no: number;
  status?: LifecycleStatus | string | null;
  archived_at?: string | null;
}

export interface ApiErrorEnvelope {
  error: {
    code: string;
    message_key: string;
    request_id: string;
    details: Record<string, unknown>;
  };
}

export class CoreAdminApiError extends Error {
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

  return `sp-${Date.now()}`;
}

function buildHeaders(role: AppRole, tenantId?: string | null, requestId?: string): HeadersInit {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "X-Actor-Role": role,
  };

  if (tenantId) {
    headers["X-Tenant-Id"] = tenantId;
  }

  if (requestId) {
    headers["X-Request-Id"] = requestId;
  }

  return headers;
}

function isApiErrorEnvelope(value: unknown): value is ApiErrorEnvelope {
  if (!value || typeof value !== "object") {
    return false;
  }

  const error = (value as Record<string, unknown>).error;
  if (!error || typeof error !== "object") {
    return false;
  }

  return typeof (error as Record<string, unknown>).message_key === "string";
}

async function request<T>(
  path: string,
  options: {
    method?: string;
    body?: unknown;
    accessToken: string;
    role: AppRole;
    tenantId?: string | null;
    requestId?: string;
  },
): Promise<T> {
  const response = await fetch(`${webAppConfig.apiBaseUrl}${path}`, {
    method: options.method ?? "GET",
    headers: {
      ...buildHeaders(options.role, options.tenantId, options.requestId ?? generateRequestId()),
      Authorization: `Bearer ${options.accessToken}`,
    },
    body: options.body == null ? undefined : JSON.stringify(options.body),
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as unknown;

    if (isApiErrorEnvelope(payload)) {
      throw new CoreAdminApiError(response.status, payload.error);
    }

    throw new CoreAdminApiError(response.status, {
      code: "platform.internal",
      message_key: "errors.platform.internal",
      request_id: "",
      details: {},
    });
  }

  return (await response.json()) as T;
}

export function listTenants(accessToken: string, role: AppRole, tenantId?: string | null) {
  return request<TenantListItem[]>("/api/core/admin/tenants", { accessToken, role, tenantId });
}

export function getTenant(accessToken: string, tenantId: string, role: AppRole, actorTenantId?: string | null) {
  return request<TenantRead>(`/api/core/admin/tenants/${tenantId}`, { accessToken, role, tenantId: actorTenantId });
}

export function onboardTenant(accessToken: string, payload: TenantOnboardingPayload, role: AppRole) {
  return request<{
    tenant: TenantRead;
    initial_branch: BranchRead;
    initial_mandate: MandateRead;
    initial_settings: TenantSettingRead[];
  }>("/api/core/admin/tenants/onboard", {
    accessToken,
    method: "POST",
    body: payload,
    role,
  });
}

export function updateTenant(
  accessToken: string,
  tenantId: string,
  payload: TenantUpdatePayload,
  role: AppRole,
  actorTenantId?: string | null,
) {
  return request<TenantRead>(`/api/core/admin/tenants/${tenantId}`, {
    accessToken,
    method: "PATCH",
    body: payload,
    role,
    tenantId: actorTenantId,
  });
}

export function transitionTenantStatus(
  accessToken: string,
  tenantId: string,
  status: string,
  role: AppRole,
  actorTenantId?: string | null,
) {
  return request<TenantRead>(`/api/core/admin/tenants/${tenantId}/lifecycle`, {
    accessToken,
    method: "POST",
    body: { status },
    role,
    tenantId: actorTenantId,
  });
}

export function listBranches(accessToken: string, tenantId: string, role: AppRole, actorTenantId?: string | null) {
  return request<BranchRead[]>(`/api/core/admin/tenants/${tenantId}/branches`, {
    accessToken,
    role,
    tenantId: actorTenantId,
  });
}

export function createBranch(
  accessToken: string,
  tenantId: string,
  payload: BranchCreatePayload,
  role: AppRole,
  actorTenantId?: string | null,
) {
  return request<BranchRead>(`/api/core/admin/tenants/${tenantId}/branches`, {
    accessToken,
    method: "POST",
    body: payload,
    role,
    tenantId: actorTenantId,
  });
}

export function updateBranch(
  accessToken: string,
  tenantId: string,
  branchId: string,
  payload: BranchUpdatePayload,
  role: AppRole,
  actorTenantId?: string | null,
) {
  return request<BranchRead>(`/api/core/admin/tenants/${tenantId}/branches/${branchId}`, {
    accessToken,
    method: "PATCH",
    body: payload,
    role,
    tenantId: actorTenantId,
  });
}

export function listMandates(accessToken: string, tenantId: string, role: AppRole, actorTenantId?: string | null) {
  return request<MandateRead[]>(`/api/core/admin/tenants/${tenantId}/mandates`, {
    accessToken,
    role,
    tenantId: actorTenantId,
  });
}

export function createMandate(
  accessToken: string,
  tenantId: string,
  payload: MandateCreatePayload,
  role: AppRole,
  actorTenantId?: string | null,
) {
  return request<MandateRead>(`/api/core/admin/tenants/${tenantId}/mandates`, {
    accessToken,
    method: "POST",
    body: payload,
    role,
    tenantId: actorTenantId,
  });
}

export function updateMandate(
  accessToken: string,
  tenantId: string,
  mandateId: string,
  payload: MandateUpdatePayload,
  role: AppRole,
  actorTenantId?: string | null,
) {
  return request<MandateRead>(`/api/core/admin/tenants/${tenantId}/mandates/${mandateId}`, {
    accessToken,
    method: "PATCH",
    body: payload,
    role,
    tenantId: actorTenantId,
  });
}

export function listSettings(accessToken: string, tenantId: string, role: AppRole, actorTenantId?: string | null) {
  return request<TenantSettingRead[]>(`/api/core/admin/tenants/${tenantId}/settings`, {
    accessToken,
    role,
    tenantId: actorTenantId,
  });
}

export function createSetting(
  accessToken: string,
  tenantId: string,
  payload: TenantSettingCreatePayload,
  role: AppRole,
  actorTenantId?: string | null,
) {
  return request<TenantSettingRead>(`/api/core/admin/tenants/${tenantId}/settings`, {
    accessToken,
    method: "POST",
    body: payload,
    role,
    tenantId: actorTenantId,
  });
}

export function updateSetting(
  accessToken: string,
  tenantId: string,
  settingId: string,
  payload: TenantSettingUpdatePayload,
  role: AppRole,
  actorTenantId?: string | null,
) {
  return request<TenantSettingRead>(`/api/core/admin/tenants/${tenantId}/settings/${settingId}`, {
    accessToken,
    method: "PUT",
    body: payload,
    role,
    tenantId: actorTenantId,
  });
}

export function listLookupValues(
  accessToken: string,
  tenantId: string,
  domain: string,
  role: AppRole,
  actorTenantId?: string | null,
) {
  const query = new URLSearchParams({ domain });
  return request<LookupValueRead[]>(`/api/core/admin/tenants/${tenantId}/lookup-values?${query.toString()}`, {
    accessToken,
    role,
    tenantId: actorTenantId,
  });
}

export function createLookupValue(
  accessToken: string,
  tenantId: string,
  payload: LookupValueCreatePayload,
  role: AppRole,
  actorTenantId?: string | null,
) {
  return request<LookupValueRead>(`/api/core/admin/tenants/${tenantId}/lookup-values`, {
    accessToken,
    method: "POST",
    body: payload,
    role,
    tenantId: actorTenantId,
  });
}

export function updateLookupValue(
  accessToken: string,
  tenantId: string,
  lookupValueId: string,
  payload: LookupValueUpdatePayload,
  role: AppRole,
  actorTenantId?: string | null,
) {
  return request<LookupValueRead>(`/api/core/admin/tenants/${tenantId}/lookup-values/${lookupValueId}`, {
    accessToken,
    method: "PATCH",
    body: payload,
    role,
    tenantId: actorTenantId,
  });
}
