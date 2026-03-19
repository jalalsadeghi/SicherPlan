import { useAccessStore } from '@vben/stores';

import type { SicherPlanCurrentSessionResponse } from './auth.mappers';


function getApiBaseUrl() {
  return import.meta.env.VITE_GLOB_API_URL || '/api';
}

async function sicherPlanRequest<T>(
  path: string,
  options?: {
    accessToken?: null | string;
    body?: unknown;
    method?: string;
  },
): Promise<T> {
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    method: options?.method ?? 'GET',
    headers: {
      'Content-Type': 'application/json',
      ...(options?.accessToken
        ? { Authorization: `Bearer ${options.accessToken}` }
        : {}),
    },
    body: options?.body == null ? undefined : JSON.stringify(options.body),
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as
      | null
      | { error?: { message_key?: string } };
    throw new Error(payload?.error?.message_key || `HTTP_${response.status}`);
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
