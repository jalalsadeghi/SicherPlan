import { webAppConfig } from '@/config/env';
import { CustomerAdminApiError } from '@/api/customers';

interface ApiErrorEnvelope {
  error: {
    code: string;
    message_key: string;
    request_id: string;
    details: Record<string, unknown>;
  };
}

export interface CustomerPortalAccessListItem {
  user_id: string;
  contact_id: string;
  contact_name: string;
  username: string;
  email: string;
  full_name: string;
  locale: string;
  role_key: string;
  status: string;
  role_assignment_status: string;
  is_password_login_enabled: boolean;
  last_login_at: null | string;
  created_at: string;
  updated_at: string;
}

export interface CustomerPortalAccessCreatePayload {
  tenant_id: string;
  customer_id: string;
  contact_id: string;
  username: string;
  email: string;
  full_name: string;
  locale: string;
  timezone: string;
  status: 'active' | 'inactive';
  temporary_password?: string | null;
}

export interface CustomerPortalAccessStatusPayload {
  status: 'active' | 'inactive';
}

export interface CustomerPortalAccessPasswordResetPayload {
  temporary_password?: string | null;
}

export interface CustomerPortalAccessPasswordResponse {
  message_key: string;
  temporary_password: string;
}

export interface CustomerPortalAccessUnlinkResponse {
  message_key: string;
}

function generateRequestId() {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID();
  }
  return `sp-${Date.now()}`;
}

function isApiErrorEnvelope(value: unknown): value is ApiErrorEnvelope {
  if (!value || typeof value !== 'object') {
    return false;
  }
  const error = (value as Record<string, unknown>).error;
  return !!error && typeof error === 'object' && typeof (error as Record<string, unknown>).message_key === 'string';
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
    method: options?.method ?? 'GET',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${accessToken}`,
      'X-Request-Id': generateRequestId(),
    },
    body: options?.body == null ? undefined : JSON.stringify(options.body),
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as unknown;
    if (isApiErrorEnvelope(payload)) {
      throw new CustomerAdminApiError(response.status, payload.error);
    }
    throw new CustomerAdminApiError(response.status, {
      code: 'platform.internal',
      message_key: 'errors.platform.internal',
      request_id: '',
      details: {},
    });
  }

  return (await response.json()) as T;
}

export function listCustomerPortalAccess(tenantId: string, customerId: string, accessToken: string) {
  return request<CustomerPortalAccessListItem[]>(
    `/api/customers/tenants/${tenantId}/customers/${customerId}/portal-access`,
    accessToken,
  );
}

export function createCustomerPortalAccess(
  tenantId: string,
  customerId: string,
  accessToken: string,
  payload: CustomerPortalAccessCreatePayload,
) {
  return request<CustomerPortalAccessPasswordResponse>(
    `/api/customers/tenants/${tenantId}/customers/${customerId}/portal-access`,
    accessToken,
    {
      method: 'POST',
      body: payload,
    },
  );
}

export function updateCustomerPortalAccessStatus(
  tenantId: string,
  customerId: string,
  userId: string,
  accessToken: string,
  payload: CustomerPortalAccessStatusPayload,
) {
  return request<CustomerPortalAccessListItem>(
    `/api/customers/tenants/${tenantId}/customers/${customerId}/portal-access/${userId}/status`,
    accessToken,
    {
      method: 'POST',
      body: payload,
    },
  );
}

export function resetCustomerPortalAccessPassword(
  tenantId: string,
  customerId: string,
  userId: string,
  accessToken: string,
  payload?: CustomerPortalAccessPasswordResetPayload,
) {
  return request<CustomerPortalAccessPasswordResponse>(
    `/api/customers/tenants/${tenantId}/customers/${customerId}/portal-access/${userId}/password-reset`,
    accessToken,
    {
      method: 'POST',
      body: payload ?? { temporary_password: null },
    },
  );
}

export function unlinkCustomerPortalAccess(
  tenantId: string,
  customerId: string,
  userId: string,
  accessToken: string,
) {
  return request<CustomerPortalAccessUnlinkResponse>(
    `/api/customers/tenants/${tenantId}/customers/${customerId}/portal-access/${userId}`,
    accessToken,
    {
      method: 'DELETE',
    },
  );
}
