import { useAccessStore } from '@vben/stores';


function getApiBaseUrl() {
  return import.meta.env.VITE_GLOB_API_URL || '/api';
}

async function apiRequest<T>(path: string, options?: { body?: unknown; method?: string }): Promise<T> {
  const accessStore = useAccessStore();
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    method: options?.method ?? 'GET',
    headers: {
      Authorization: `Bearer ${accessStore.accessToken}`,
      'Content-Type': 'application/json',
    },
    body: options?.body == null ? undefined : JSON.stringify(options.body),
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as
      | null
      | { error?: { message_key?: string } };
    throw new Error(payload?.error?.message_key || `HTTP_${response.status}`);
  }

  return (await response.json()) as T;
}

export interface TenantListItem {
  id: string;
  code: string;
  name: string;
  status: string;
}

export interface TenantAdminUserListItem {
  id: string;
  tenant_id: string;
  username: string;
  email: string;
  full_name: string;
  locale: string;
  timezone: string;
  status: string;
  last_login_at: null | string;
  role_assignment_status: string;
  role_key: string;
  scope_type: string;
}

export interface TenantAdminUserCreatePayload {
  email: string;
  full_name: string;
  locale: string;
  status: 'active' | 'inactive';
  temporary_password?: string;
  timezone: string;
  username: string;
}

export interface TenantAdminPasswordResponse {
  message_key: string;
  temporary_password: string;
}

export function listTenants() {
  return apiRequest<TenantListItem[]>('/core/admin/tenants');
}

export function listTenantUsers(tenantId: string) {
  return apiRequest<TenantAdminUserListItem[]>(`/iam/admin/tenants/${tenantId}/tenant-users`);
}

export function createTenantUser(tenantId: string, payload: TenantAdminUserCreatePayload) {
  return apiRequest<TenantAdminPasswordResponse>(`/iam/admin/tenants/${tenantId}/tenant-users`, {
    body: { ...payload, tenant_id: tenantId },
    method: 'POST',
  });
}

export function updateTenantUserStatus(tenantId: string, userId: string, status: 'active' | 'inactive') {
  return apiRequest<TenantAdminUserListItem>(`/iam/admin/tenants/${tenantId}/tenant-users/${userId}/status`, {
    body: { status },
    method: 'POST',
  });
}

export function resetTenantUserPassword(tenantId: string, userId: string, temporaryPassword?: string) {
  return apiRequest<TenantAdminPasswordResponse>(
    `/iam/admin/tenants/${tenantId}/tenant-users/${userId}/password-reset`,
    {
      body: { temporary_password: temporaryPassword || null },
      method: 'POST',
    },
  );
}
