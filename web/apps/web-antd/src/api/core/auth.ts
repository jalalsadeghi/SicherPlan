import { useAccessStore } from '@vben/stores';

import type { SicherPlanCurrentSessionResponse } from './auth.mappers';

interface ApiErrorPayload {
  error?: {
    code?: string;
    message_key?: string;
  };
}

export class AuthApiError extends Error {
  code: string;
  messageKey: string;
  status: number;

  constructor(
    status: number,
    code: string,
    messageKey: string,
  ) {
    super(messageKey);
    this.name = 'AuthApiError';
    this.status = status;
    this.code = code;
    this.messageKey = messageKey;
  }
}

function getApiBaseUrl() {
  return import.meta.env.VITE_GLOB_API_URL || '/api';
}

async function readApiErrorPayload(response: Response): Promise<ApiErrorPayload> {
  return (await response.json().catch(() => null)) as ApiErrorPayload;
}

function buildAuthApiError(
  status: number,
  payload?: ApiErrorPayload | null,
) {
  return new AuthApiError(
    status,
    payload?.error?.code || `HTTP_${status}`,
    payload?.error?.message_key || 'errors.platform.internal',
  );
}

export function resolveLoginErrorMessageKey(error: unknown) {
  if (error instanceof AuthApiError) {
    switch (error.messageKey) {
      case 'errors.iam.auth.invalid_credentials': {
        return 'sicherplan.auth.loginErrors.invalidCredentials';
      }
      case 'errors.iam.auth.rate_limited': {
        return 'sicherplan.auth.loginErrors.rateLimited';
      }
      case 'errors.platform.database_unavailable': {
        return 'sicherplan.auth.loginErrors.serverUnavailable';
      }
      default: {
        if (error.status === 401) {
          return 'sicherplan.auth.loginErrors.invalidCredentials';
        }
        if (error.status >= 500) {
          return 'sicherplan.auth.loginErrors.serverUnavailable';
        }
      }
    }
  }

  if (error instanceof TypeError) {
    return 'sicherplan.auth.loginErrors.serverUnavailable';
  }

  return 'sicherplan.auth.loginErrors.generic';
}

async function sicherPlanRequest<T>(
  path: string,
  options?: {
    accessToken?: null | string;
    body?: unknown;
    method?: string;
  },
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${getApiBaseUrl()}${path}`, {
      method: options?.method ?? 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...(options?.accessToken
          ? { Authorization: `Bearer ${options.accessToken}` }
          : {}),
      },
      body: options?.body == null ? undefined : JSON.stringify(options.body),
    });
  } catch (error) {
    if (error instanceof Error) {
      throw error;
    }
    throw new AuthApiError(
      0,
      'platform.network_unavailable',
      'errors.platform.network_unavailable',
    );
  }

  if (!response.ok) {
    const payload = await readApiErrorPayload(response);
    throw buildAuthApiError(response.status, payload);
  }

  if (response.status === 204) {
    return null as T;
  }

  return (await response.json()) as T;
}

export namespace AuthApi {
  /** 登录接口参数 */
  export interface LoginParams {
    identifier?: string;
    password?: string;
    tenantCode?: string;
  }

  /** 登录接口返回值 */
  export interface LoginResult {
    accessToken: string;
  }

  export interface CurrentSessionResult extends SicherPlanCurrentSessionResponse {}

  export interface RefreshTokenResult {
    data: string;
    status: number;
  }
}

/**
 * 登录
 */
export async function loginApi(data: AuthApi.LoginParams) {
  const response = await sicherPlanRequest<{
    session: { access_token: string };
  }>('/auth/login', {
    body: {
      identifier: data.identifier,
      password: data.password,
      tenant_code: data.tenantCode,
    },
    method: 'POST',
  });

  return { accessToken: response.session.access_token };
}

/**
 * 刷新accessToken
 */
export async function refreshTokenApi() {
  throw new Error('SicherPlan refresh-token flow is not wired into the Vben shell yet.');
}

/**
 * 退出登录
 */
export async function logoutApi() {
  const accessStore = useAccessStore();
  return sicherPlanRequest<{ message_key: string }>('/auth/logout', {
    accessToken: accessStore.accessToken,
    method: 'POST',
  });
}

/**
 * 获取用户权限码
 */
export async function getAccessCodesApi() {
  const accessStore = useAccessStore();
  const response = await sicherPlanRequest<{ items: string[] }>('/auth/codes', {
    accessToken: accessStore.accessToken,
  });
  return response.items;
}

export async function getCurrentSessionApi() {
  const accessStore = useAccessStore();
  return sicherPlanRequest<AuthApi.CurrentSessionResult>('/auth/me', {
    accessToken: accessStore.accessToken,
  });
}
