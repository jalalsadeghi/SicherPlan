// @vitest-environment happy-dom

import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';

const primaryAccessState = {
  accessToken: '',
};

const primaryUserState = {
  userInfo: null as null | { roles?: string[] },
};

vi.mock('@vben/stores', () => ({
  useAccessStore: () => primaryAccessState,
  useUserStore: () => primaryUserState,
}));

const getCurrentSession = vi.fn();

vi.mock('../api/auth', () => ({
  AuthApiError: class AuthApiError extends Error {
    statusCode: number;

    constructor(statusCode: number) {
      super(`auth:${statusCode}`);
      this.statusCode = statusCode;
    }
  },
  getCurrentSession,
  getCustomerPortalContext: vi.fn(),
  getSubcontractorPortalContext: vi.fn(),
  login: vi.fn(),
  logout: vi.fn(),
}));

describe('legacy auth tenant scope resolution', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    window.localStorage.clear();
    primaryAccessState.accessToken = '';
    primaryUserState.userInfo = null;
    getCurrentSession.mockReset();
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
        roles: [{ role_key: 'tenant_admin', scope_type: 'tenant' }],
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
      session: {
        access_token: 'token-1',
        refresh_token: 'refresh-1',
        session_id: 'session-1',
      },
      user: {
        id: 'user-1',
        tenant_id: 'tenant-1',
        username: 'tenant-admin',
        email: 'tenant-admin@example.invalid',
        full_name: 'Tenant Admin',
        locale: 'de',
        timezone: 'Europe/Berlin',
        is_platform_user: false,
        roles: [{ role_key: 'tenant_admin', scope_type: 'tenant' }],
      },
    });

    expect(store.tenantScopeId).toBe('tenant-1');
    expect(store.effectiveTenantScopeId).toBe('tenant-1');
  });

  it('clears stale legacy session user when the primary token changes', async () => {
    window.localStorage.setItem('sicherplan-session-user', JSON.stringify({
      id: 'old-user',
      tenant_id: 'c867d853-4148-44be-9f50-35e151f9778c',
      roles: [{ role_key: 'platform_admin', scope_type: 'tenant' }],
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
          roles: [{ role_key: 'platform_admin', scope_type: 'tenant' }],
        },
        'c867d853-4148-44be-9f50-35e151f9778c',
      ),
    ).toBe('c867d853-4148-44be-9f50-35e151f9778c');
  });

  it('exposes only the effective UI role for access generation even if the account has extra roles', async () => {
    const { useAuthStore } = await import('./auth');
    const store = useAuthStore();

    store.setSession({
      session: {
        access_token: 'token-1',
        refresh_token: 'refresh-1',
        session_id: 'session-1',
      },
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
          { role_key: 'platform_admin', scope_type: 'tenant' },
          { role_key: 'tenant_admin', scope_type: 'tenant' },
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
      session: {
        access_token: 'token-1',
        refresh_token: 'refresh-1',
        session_id: 'session-1',
      },
      user: {
        id: 'user-1',
        tenant_id: 'tenant-1',
        username: 'tenant-admin',
        email: 'tenant-admin@example.invalid',
        full_name: 'Tenant Admin',
        locale: 'de',
        timezone: 'Europe/Berlin',
        is_platform_user: false,
        roles: [{ role_key: 'tenant_admin', scope_type: 'tenant' }],
      },
    });

    store.setTenantScopeId('other-tenant');

    expect(store.tenantScopeId).toBe('tenant-1');
    expect(store.effectiveTenantScopeId).toBe('tenant-1');
  });
});
