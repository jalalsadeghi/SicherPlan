import { webAppConfig } from "@/config/env";

export interface AuthenticatedRoleScope {
  role_key: string;
  scope_type: string;
  branch_id: string | null;
  mandate_id: string | null;
  customer_id: string | null;
  subcontractor_id: string | null;
}

export interface AuthenticatedUser {
  id: string;
  tenant_id: string;
  username: string;
  email: string;
  full_name: string;
  locale: string;
  timezone: string;
  is_platform_user: boolean;
  roles: AuthenticatedRoleScope[];
}

export interface SessionTokenPair {
  access_token: string;
  access_token_type: string;
  access_token_expires_at: string;
  refresh_token: string;
  refresh_token_expires_at: string;
  session_id: string;
  mfa_required: boolean;
  sso_hints: string[];
}

export interface LoginPayload {
  tenant_code: string;
  identifier: string;
  password: string;
  device_label?: string | null;
  device_id?: string | null;
}

export interface LoginResponse {
  user: AuthenticatedUser;
  session: SessionTokenPair;
}

export interface CurrentSessionResponse {
  user: AuthenticatedUser;
  session: {
    id: string;
    tenant_id: string;
    refresh_token_family: string;
    status: string;
    issued_at: string;
    expires_at: string;
    last_seen_at: string | null;
    revoked_at: string | null;
    device_label: string | null;
    device_id: string | null;
    ip_address: string | null;
    user_agent: string | null;
    is_current: boolean;
  };
}

export interface CustomerPortalContextRead {
  tenant_id: string;
  user_id: string;
  customer_id: string;
  contact_id: string;
  customer: {
    id: string;
    tenant_id: string;
    customer_number: string;
    name: string;
    status: string;
  };
  contact: {
    id: string;
    tenant_id: string;
    customer_id: string;
    full_name: string;
    function_label: string | null;
    email: string | null;
    phone: string | null;
    mobile: string | null;
    status: string;
  };
  scopes: Array<{
    role_key: string;
    scope_type: string;
    customer_id: string;
  }>;
}

interface ApiErrorEnvelope {
  error: {
    code: string;
    message_key: string;
    request_id: string;
    details: Record<string, unknown>;
  };
}

export class AuthApiError extends Error {
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

  return `sp-auth-${Date.now()}`;
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
  options?: {
    method?: string;
    accessToken?: string;
    body?: unknown;
  },
): Promise<T> {
  const response = await fetch(`${webAppConfig.apiBaseUrl}${path}`, {
    method: options?.method ?? "GET",
    headers: {
      "Content-Type": "application/json",
      "X-Request-Id": generateRequestId(),
      ...(options?.accessToken ? { Authorization: `Bearer ${options.accessToken}` } : {}),
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

  if (response.status === 204) {
    return null as T;
  }

  return (await response.json()) as T;
}

export function login(payload: LoginPayload) {
  return request<LoginResponse>("/api/auth/login", {
    method: "POST",
    body: payload,
  });
}

export function getCurrentSession(accessToken: string) {
  return request<CurrentSessionResponse>("/api/auth/me", { accessToken });
}

export function logout(accessToken: string) {
  return request<{ message_key: string }>("/api/auth/logout", {
    method: "POST",
    accessToken,
  });
}

export function getCustomerPortalContext(accessToken: string) {
  return request<CustomerPortalContextRead>("/api/portal/customer/context", { accessToken });
}
