// @vitest-environment happy-dom

import { createPinia, setActivePinia } from 'pinia';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const {
  accessStoreState,
  legacyAuthStoreState,
  logoutApi,
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
  legacyAuthStoreState: {
    clearSession: vi.fn(),
  },
  logoutApi: vi.fn(),
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
  getAccessCodesApi: vi.fn(),
  getUserInfoApi: vi.fn(),
  loginApi: vi.fn(),
  logoutApi,
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
    resetAllStores.mockReset();
    routerReplace.mockReset();
    userStoreState.setUserInfo.mockReset();
    legacyAuthStoreState.clearSession.mockReset();

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
});
