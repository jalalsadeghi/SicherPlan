// @vitest-environment happy-dom

import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';

const primaryAccessState = {
  accessToken: '',
  refreshToken: '',
  setAccessToken: vi.fn((token: null | string) => {
    primaryAccessState.accessToken = token ?? '';
  }),
  setRefreshToken: vi.fn((token: null | string) => {
    primaryAccessState.refreshToken = token ?? '';
  }),
};

const primaryUserState = {
  userInfo: null as null | { roles?: string[] },
};

vi.mock('@vben/stores', () => ({
  useAccessStore: () => primaryAccessState,
  useUserStore: () => primaryUserState,
}));

const getCurrentSession = vi.fn();
const refreshSession = vi.fn();

vi.mock('../api/auth', () => ({
  AuthApiError: class AuthApiError extends Error {
    statusCode: number;
    code: string;
    messageKey: string;
    details: Record<string, unknown>;

    constructor(statusCode: number, payload?: { code?: string; details?: Record<string, unknown>; message_key?: string }) {
      super(`auth:${statusCode}`);
      this.statusCode = statusCode;
      this.code = payload?.code ?? '';
      this.messageKey = payload?.message_key ?? '';
      this.details = payload?.details ?? {};
    }
  },
  getCurrentSession,
  getCustomerPortalContext: vi.fn(),
  getSubcontractorPortalContext: vi.fn(),
  login: vi.fn(),
  logout: vi.fn(),
  refreshSession,
}));

function makeSessionTokenPair(accessToken: string, refreshToken: string, sessionId: string) {
  return {
    access_token: accessToken,
    access_token_type: 'Bearer',
    access_token_expires_at: '2026-01-01T00:15:00Z',
    refresh_token: refreshToken,
    refresh_token_expires_at: '2026-01-01T01:00:00Z',
    session_id: sessionId,
    mfa_required: false,
    sso_hints: [],
  };
}

function makeRoleScope(roleKey: string, scopeType: string, customerId: null | string = null) {
  return {
    role_key: roleKey,
    scope_type: scopeType,
    branch_id: null,
    mandate_id: null,
    customer_id: customerId,
    subcontractor_id: null,
  };
}

describe('legacy auth tenant scope resolution', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    window.localStorage.clear();
    primaryAccessState.accessToken = '';
    primaryAccessState.refreshToken = '';
    primaryAccessState.setAccessToken.mockClear();
    primaryAccessState.setRefreshToken.mockClear();
    primaryUserState.userInfo = null;
    getCurrentSession.mockReset();
    refreshSession.mockReset();
  });

  it('uses the authenticated tenant for tenant admin even when remembered scope is stale', async () => {
    window.localStorage.setItem('sicherplan-tenant-scope', 'c867d853-4148-44be-9f50-35e151f9778c');
    primaryAccessState.accessToken = 'fresh-token';
    primaryUserState.userInfo = { roles: ['tenant_admin'] };
    getCurrentSession.mockResolvedValue({
      user: {
        id: 'user-1',
        tenant_id: 'a5b14732-65dc-4e14-8dd5-e0aec799d3f2',
        username: 'tenant-admin',
        email: 'tenant-admin@example.invalid',
        full_name: 'Tenant Admin',
        locale: 'de',
        timezone: 'Europe/Berlin',
        is_platform_user: false,
        roles: [makeRoleScope('tenant_admin', 'tenant')],
      },
      session: { id: 'session-1' },
    });

    const { useAuthStore } = await import('./auth');
    const store = useAuthStore();

    await store.loadCurrentSession();

    expect(store.effectiveTenantScopeId).toBe('a5b14732-65dc-4e14-8dd5-e0aec799d3f2');
    expect(store.tenantScopeId).toBe('a5b14732-65dc-4e14-8dd5-e0aec799d3f2');
  });

  it('hydrates tenantScopeId from the login session for tenant admin', async () => {
    const { useAuthStore } = await import('./auth');
    const store = useAuthStore();

    store.setSession({
      session: makeSessionTokenPair('token-1', 'refresh-1', 'session-1'),
      user: {
        id: 'user-1',
        tenant_id: 'tenant-1',
        username: 'tenant-admin',
        email: 'tenant-admin@example.invalid',
        full_name: 'Tenant Admin',
        locale: 'de',
        timezone: 'Europe/Berlin',
        is_platform_user: false,
        roles: [makeRoleScope('tenant_admin', 'tenant')],
      },
    });

    expect(store.tenantScopeId).toBe('tenant-1');
    expect(store.effectiveTenantScopeId).toBe('tenant-1');
  });

  it('clears stale legacy session user when the primary token changes', async () => {
    window.localStorage.setItem('sicherplan-session-user', JSON.stringify({
      id: 'old-user',
      tenant_id: 'c867d853-4148-44be-9f50-35e151f9778c',
      roles: [makeRoleScope('platform_admin', 'tenant')],
    }));
    window.localStorage.setItem('sicherplan-session-id', 'old-session');
    window.localStorage.setItem('sicherplan-tenant-scope', 'c867d853-4148-44be-9f50-35e151f9778c');

    const { useAuthStore } = await import('./auth');
    const store = useAuthStore();

    primaryAccessState.accessToken = 'new-token';
    primaryUserState.userInfo = { roles: ['tenant_admin'] };

    store.syncFromPrimarySession();

    expect(store.sessionUser).toBeNull();
    expect(store.sessionId).toBe('');
    expect(store.accessToken).toBe('new-token');
    expect(store.effectiveTenantScopeId).toBe('');
  });

  it('preserves an explicit customer portal session when a stale primary token still exists', async () => {
    primaryAccessState.accessToken = 'stale-admin-token';
    primaryUserState.userInfo = { roles: ['tenant_admin'] };

    const { useAuthStore } = await import('./auth');
    const store = useAuthStore();

    store.setSession({
      session: makeSessionTokenPair('portal-token', 'portal-refresh', 'portal-session'),
      user: {
        id: 'portal-user-1',
        tenant_id: 'tenant-portal',
        username: 'customer.portal',
        email: 'customer.portal@example.invalid',
        full_name: 'Customer Portal',
        locale: 'de',
        timezone: 'Europe/Berlin',
        is_platform_user: false,
        roles: [makeRoleScope('customer_user', 'customer', 'customer-1')],
      },
    });

    store.syncFromPrimarySession();

    expect(store.accessToken).toBe('portal-token');
    expect(store.sessionUser?.id).toBe('portal-user-1');
    expect(store.effectiveRole).toBe('customer_user');
  });

  it('platform admin still uses the remembered tenant scope', async () => {
    const { resolveTenantScopeIdForRole } = await import('./auth');

    expect(
      resolveTenantScopeIdForRole(
        'platform_admin',
        {
          id: 'user-1',
          tenant_id: 'a5b14732-65dc-4e14-8dd5-e0aec799d3f2',
          username: 'sysadmin',
          email: 'sysadmin@example.invalid',
          full_name: 'System Admin',
          locale: 'de',
          timezone: 'Europe/Berlin',
          is_platform_user: true,
          roles: [makeRoleScope('platform_admin', 'tenant')],
        },
        'c867d853-4148-44be-9f50-35e151f9778c',
      ),
    ).toBe('c867d853-4148-44be-9f50-35e151f9778c');
  });

  it('exposes only the effective UI role for access generation even if the account has extra roles', async () => {
    const { useAuthStore } = await import('./auth');
    const store = useAuthStore();

    store.setSession({
      session: makeSessionTokenPair('token-1', 'refresh-1', 'session-1'),
      user: {
        id: 'user-1',
        tenant_id: 'tenant-1',
        username: 'sysadmin',
        email: 'sysadmin@example.invalid',
        full_name: 'System Admin',
        locale: 'de',
        timezone: 'Europe/Berlin',
        is_platform_user: true,
        roles: [
          makeRoleScope('platform_admin', 'tenant'),
          makeRoleScope('tenant_admin', 'tenant'),
        ],
      },
    });

    expect(store.effectiveRole).toBe('platform_admin');
    expect(store.accessRoles).toEqual(['platform_admin']);
  });

  it('ignores a manual tenant scope override for tenant admin once the session tenant is known', async () => {
    const { useAuthStore } = await import('./auth');
    const store = useAuthStore();

    store.setSession({
      session: makeSessionTokenPair('token-1', 'refresh-1', 'session-1'),
      user: {
        id: 'user-1',
        tenant_id: 'tenant-1',
        username: 'tenant-admin',
        email: 'tenant-admin@example.invalid',
        full_name: 'Tenant Admin',
        locale: 'de',
        timezone: 'Europe/Berlin',
        is_platform_user: false,
        roles: [makeRoleScope('tenant_admin', 'tenant')],
      },
    });

    store.setTenantScopeId('other-tenant');

    expect(store.tenantScopeId).toBe('tenant-1');
    expect(store.effectiveTenantScopeId).toBe('tenant-1');
  });

  it('refreshes legacy session tokens and syncs them into the primary access store', async () => {
    const { useAuthStore } = await import('./auth');
    const store = useAuthStore();

    store.refreshToken = 'refresh-1';
    refreshSession.mockResolvedValue({
      session: makeSessionTokenPair('fresh-access', 'refresh-2', 'session-2'),
    });

    const accessToken = await store.refreshSessionTokens();

    expect(accessToken).toBe('fresh-access');
    expect(store.accessToken).toBe('fresh-access');
    expect(store.refreshToken).toBe('refresh-2');
    expect(store.sessionId).toBe('session-2');
    expect(primaryAccessState.setAccessToken).toHaveBeenCalledWith('fresh-access');
    expect(primaryAccessState.setRefreshToken).toHaveBeenCalledWith('refresh-2');
  });

  it('ensureSessionReady refreshes first when only a refresh token is left', async () => {
    const { useAuthStore } = await import('./auth');
    const store = useAuthStore();

    store.refreshToken = 'refresh-1';
    refreshSession.mockResolvedValue({
      session: makeSessionTokenPair('fresh-access', 'refresh-2', 'session-2'),
    });
    getCurrentSession.mockResolvedValue({
      user: {
        id: 'user-1',
        tenant_id: 'tenant-1',
        username: 'tenant-admin',
        email: 'tenant-admin@example.invalid',
        full_name: 'Tenant Admin',
        locale: 'de',
        timezone: 'Europe/Berlin',
        is_platform_user: false,
        roles: [makeRoleScope('tenant_admin', 'tenant')],
      },
      session: { id: 'session-2' },
    });

    const sessionUser = await store.ensureSessionReady();

    expect(refreshSession).toHaveBeenCalledWith('refresh-1');
    expect(getCurrentSession).toHaveBeenCalledWith('fresh-access');
    expect(sessionUser?.id).toBe('user-1');
    expect(store.sessionUser?.id).toBe('user-1');
  });
});
