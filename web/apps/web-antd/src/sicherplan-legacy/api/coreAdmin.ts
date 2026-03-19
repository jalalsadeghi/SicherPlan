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
    role: AppRole;
    tenantId?: string | null;
    requestId?: string;
  },
): Promise<T> {
  const response = await fetch(`${webAppConfig.apiBaseUrl}${path}`, {
    method: options.method ?? "GET",
    headers: buildHeaders(options.role, options.tenantId, options.requestId ?? generateRequestId()),
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

export function listTenants(role: AppRole, tenantId?: string | null) {
  return request<TenantListItem[]>("/api/core/admin/tenants", { role, tenantId });
}

export function getTenant(tenantId: string, role: AppRole, actorTenantId?: string | null) {
  return request<TenantRead>(`/api/core/admin/tenants/${tenantId}`, { role, tenantId: actorTenantId });
}

export function onboardTenant(payload: TenantOnboardingPayload, role: AppRole) {
  return request<{
    tenant: TenantRead;
    initial_branch: BranchRead;
    initial_mandate: MandateRead;
    initial_settings: TenantSettingRead[];
  }>("/api/core/admin/tenants/onboard", {
    method: "POST",
    body: payload,
    role,
  });
}

export function updateTenant(
  tenantId: string,
  payload: TenantUpdatePayload,
  role: AppRole,
  actorTenantId?: string | null,
) {
  return request<TenantRead>(`/api/core/admin/tenants/${tenantId}`, {
    method: "PATCH",
    body: payload,
    role,
    tenantId: actorTenantId,
  });
}

export function transitionTenantStatus(
  tenantId: string,
  status: string,
  role: AppRole,
  actorTenantId?: string | null,
) {
  return request<TenantRead>(`/api/core/admin/tenants/${tenantId}/lifecycle`, {
    method: "POST",
    body: { status },
    role,
    tenantId: actorTenantId,
  });
}

export function listBranches(tenantId: string, role: AppRole, actorTenantId?: string | null) {
  return request<BranchRead[]>(`/api/core/admin/tenants/${tenantId}/branches`, {
    role,
    tenantId: actorTenantId,
  });
}

export function createBranch(
  tenantId: string,
  payload: BranchCreatePayload,
  role: AppRole,
  actorTenantId?: string | null,
) {
  return request<BranchRead>(`/api/core/admin/tenants/${tenantId}/branches`, {
    method: "POST",
    body: payload,
    role,
    tenantId: actorTenantId,
  });
}

export function updateBranch(
  tenantId: string,
  branchId: string,
  payload: BranchUpdatePayload,
  role: AppRole,
  actorTenantId?: string | null,
) {
  return request<BranchRead>(`/api/core/admin/tenants/${tenantId}/branches/${branchId}`, {
    method: "PATCH",
    body: payload,
    role,
    tenantId: actorTenantId,
  });
}

export function listMandates(tenantId: string, role: AppRole, actorTenantId?: string | null) {
  return request<MandateRead[]>(`/api/core/admin/tenants/${tenantId}/mandates`, {
    role,
    tenantId: actorTenantId,
  });
}

export function createMandate(
  tenantId: string,
  payload: MandateCreatePayload,
  role: AppRole,
  actorTenantId?: string | null,
) {
  return request<MandateRead>(`/api/core/admin/tenants/${tenantId}/mandates`, {
    method: "POST",
    body: payload,
    role,
    tenantId: actorTenantId,
  });
}

export function updateMandate(
  tenantId: string,
  mandateId: string,
  payload: MandateUpdatePayload,
  role: AppRole,
  actorTenantId?: string | null,
) {
  return request<MandateRead>(`/api/core/admin/tenants/${tenantId}/mandates/${mandateId}`, {
    method: "PATCH",
    body: payload,
    role,
    tenantId: actorTenantId,
  });
}

export function listSettings(tenantId: string, role: AppRole, actorTenantId?: string | null) {
  return request<TenantSettingRead[]>(`/api/core/admin/tenants/${tenantId}/settings`, {
    role,
    tenantId: actorTenantId,
  });
}

export function createSetting(
  tenantId: string,
  payload: TenantSettingCreatePayload,
  role: AppRole,
  actorTenantId?: string | null,
) {
  return request<TenantSettingRead>(`/api/core/admin/tenants/${tenantId}/settings`, {
    method: "POST",
    body: payload,
    role,
    tenantId: actorTenantId,
  });
}

export function updateSetting(
  tenantId: string,
  settingId: string,
  payload: TenantSettingUpdatePayload,
  role: AppRole,
  actorTenantId?: string | null,
) {
  return request<TenantSettingRead>(`/api/core/admin/tenants/${tenantId}/settings/${settingId}`, {
    method: "PUT",
    body: payload,
    role,
    tenantId: actorTenantId,
  });
}
