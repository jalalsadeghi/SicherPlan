// @vitest-environment happy-dom

import { createPinia, setActivePinia } from 'pinia';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const {
  accessStoreState,
  getAccessCodesApi,
  getUserInfoApi,
  loginApi,
  legacyAuthStoreState,
  logoutApi,
  refreshTokenApi,
  resetAllStores,
  routerReplace,
  userStoreState,
} = vi.hoisted(() => ({
  accessStoreState: {
    accessCodes: [] as string[],
    accessMenus: [] as any[],
    accessRoutes: [] as any[],
    accessToken: null as null | string,
    isAccessChecked: false,
    loginExpired: false,
    rememberMe: false,
    refreshToken: null as null | string,
    setAccessCodes: vi.fn(),
    setAccessMenus: vi.fn(),
    setAccessRoutes: vi.fn(),
    setAccessToken: vi.fn(),
    setIsAccessChecked: vi.fn(),
    setLoginExpired: vi.fn(),
    setRememberMe: vi.fn(),
    setRefreshToken: vi.fn(),
  },
  getAccessCodesApi: vi.fn(),
  getUserInfoApi: vi.fn(),
  loginApi: vi.fn(),
  legacyAuthStoreState: {
    clearSession: vi.fn(),
    syncFromPrimarySession: vi.fn(),
  },
  logoutApi: vi.fn(),
  refreshTokenApi: vi.fn(),
  resetAllStores: vi.fn(),
  routerReplace: vi.fn(),
  userStoreState: {
    setUserInfo: vi.fn(),
    userInfo: null as any,
  },
}));

accessStoreState.setAccessCodes.mockImplementation((codes: string[]) => {
  accessStoreState.accessCodes = codes;
});
accessStoreState.setAccessMenus.mockImplementation((menus: any[]) => {
  accessStoreState.accessMenus = menus;
});
accessStoreState.setAccessRoutes.mockImplementation((routes: any[]) => {
  accessStoreState.accessRoutes = routes;
});
accessStoreState.setAccessToken.mockImplementation((token: null | string) => {
  accessStoreState.accessToken = token;
});
accessStoreState.setIsAccessChecked.mockImplementation((value: boolean) => {
  accessStoreState.isAccessChecked = value;
});
accessStoreState.setLoginExpired.mockImplementation((value: boolean) => {
  accessStoreState.loginExpired = value;
});
accessStoreState.setRememberMe.mockImplementation((value: boolean) => {
  accessStoreState.rememberMe = value;
});
accessStoreState.setRefreshToken.mockImplementation((token: null | string) => {
  accessStoreState.refreshToken = token;
});

vi.mock('@vben/stores', () => ({
  resetAllStores,
  useAccessStore: () => accessStoreState,
  useUserStore: () => userStoreState,
}));

vi.mock('#/api', () => ({
  getAccessCodesApi,
  getUserInfoApi,
  loginApi,
  logoutApi,
}));

vi.mock('#/api/core/auth', () => ({
  refreshTokenApi,
  resolveLoginErrorMessageKey: vi.fn(
    () => 'sicherplan.auth.loginErrors.generic',
  ),
}));

vi.mock('#/router', () => ({
  router: {
    currentRoute: {
      value: {
        fullPath: '/admin/core',
      },
    },
    replace: routerReplace,
  },
}));

vi.mock('#/sicherplan-legacy/stores/auth', () => ({
  useAuthStore: () => legacyAuthStoreState,
}));

vi.mock('./auth-bootstrap', () => ({
  buildLoginLocation: vi.fn(() => ({
    path: '/auth/login',
    query: {},
  })),
}));

import { useAuthStore } from './auth';

describe('auth store logout flow', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    accessStoreState.accessCodes = ['core.admin.access'];
    accessStoreState.accessMenus = [{ path: '/admin/core' }];
    accessStoreState.accessRoutes = [{ path: '/admin/core' }];
    accessStoreState.accessToken = 'access-1';
    accessStoreState.isAccessChecked = true;
    accessStoreState.loginExpired = true;
    accessStoreState.rememberMe = true;
    accessStoreState.refreshToken = 'refresh-1';
    userStoreState.userInfo = { homePath: '/admin/core' };

    logoutApi.mockReset();
    refreshTokenApi.mockReset();
    loginApi.mockReset();
    getUserInfoApi.mockReset();
    getAccessCodesApi.mockReset();
    resetAllStores.mockReset();
    routerReplace.mockReset();
    userStoreState.setUserInfo.mockReset();
    legacyAuthStoreState.clearSession.mockReset();
    legacyAuthStoreState.syncFromPrimarySession.mockReset();

    accessStoreState.setAccessCodes.mockClear();
    accessStoreState.setAccessMenus.mockClear();
    accessStoreState.setAccessRoutes.mockClear();
    accessStoreState.setAccessToken.mockClear();
    accessStoreState.setIsAccessChecked.mockClear();
    accessStoreState.setLoginExpired.mockClear();
    accessStoreState.setRememberMe.mockClear();
    accessStoreState.setRefreshToken.mockClear();
  });

  it('clears remembered auth state on explicit logout', async () => {
    logoutApi.mockResolvedValue({
      message_key: 'iam.logout.success',
    });

    const store = useAuthStore();
    await store.logout(false);

    expect(logoutApi).toHaveBeenCalledTimes(1);
    expect(resetAllStores).toHaveBeenCalledTimes(1);
    expect(accessStoreState.accessToken).toBeNull();
    expect(accessStoreState.refreshToken).toBeNull();
    expect(accessStoreState.rememberMe).toBe(false);
    expect(accessStoreState.accessCodes).toEqual([]);
    expect(accessStoreState.accessMenus).toEqual([]);
    expect(accessStoreState.accessRoutes).toEqual([]);
    expect(accessStoreState.isAccessChecked).toBe(false);
    expect(accessStoreState.loginExpired).toBe(false);
    expect(userStoreState.setUserInfo).toHaveBeenCalledWith(null);
    expect(legacyAuthStoreState.clearSession).toHaveBeenCalledTimes(1);
    expect(routerReplace).toHaveBeenCalledWith({
      path: '/auth/login',
      query: {},
    });
  });

  it('restores a valid refresh-backed session when bootstrap has no access token', async () => {
    window.localStorage.setItem(
      'sicherplan.auth.session.metadata',
      JSON.stringify({
        accessTokenExpiresAt: '',
        refreshTokenExpiresAt: '2099-04-12T10:00:00Z',
        rememberMe: true,
        sessionId: 'session-1',
      }),
    );
    accessStoreState.accessToken = null;
    accessStoreState.refreshToken = 'refresh-1';
    refreshTokenApi.mockResolvedValue({
      accessToken: 'access-2',
      accessTokenExpiresAt: '2099-04-12T10:15:00Z',
      refreshToken: 'refresh-2',
      refreshTokenExpiresAt: '2099-04-19T10:15:00Z',
      sessionId: 'session-1',
    });

    const store = useAuthStore();
    await expect(store.ensureSessionReady()).resolves.toBe(true);

    expect(refreshTokenApi).toHaveBeenCalledTimes(1);
    expect(accessStoreState.accessToken).toBe('access-2');
    expect(accessStoreState.refreshToken).toBe('refresh-2');
    expect(accessStoreState.rememberMe).toBe(true);
    expect(legacyAuthStoreState.syncFromPrimarySession).toHaveBeenCalled();
  });

  it('redirects to login only after refresh truly fails', async () => {
    window.localStorage.setItem(
      'sicherplan.auth.session.metadata',
      JSON.stringify({
        accessTokenExpiresAt: '',
        refreshTokenExpiresAt: '2099-04-12T10:00:00Z',
        rememberMe: false,
        sessionId: 'session-1',
      }),
    );
    accessStoreState.accessToken = null;
    accessStoreState.refreshToken = 'refresh-1';
    refreshTokenApi.mockRejectedValue(new Error('refresh failed'));

    const store = useAuthStore();
    await expect(
      store.ensureSessionReady({ redirectOnFailure: true }),
    ).resolves.toBe(false);

    expect(routerReplace).toHaveBeenCalledWith({
      path: '/auth/login',
      query: {},
    });
    expect(accessStoreState.accessToken).toBeNull();
    expect(accessStoreState.refreshToken).toBeNull();
  });
});
