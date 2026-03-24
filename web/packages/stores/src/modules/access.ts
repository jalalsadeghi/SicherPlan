import type { RouteRecordRaw } from 'vue-router';

import type { MenuRecordRaw } from '@vben-core/typings';

import { acceptHMRUpdate, defineStore } from 'pinia';

type AccessToken = null | string;
type StorageLike = Pick<Storage, 'getItem' | 'removeItem' | 'setItem'>;

const noopStorage: StorageLike = {
  getItem() {
    return null;
  },
  removeItem() {},
  setItem() {},
};

function resolveBrowserStorage(kind: 'local' | 'session'): StorageLike {
  if (typeof window === 'undefined') {
    return noopStorage;
  }

  return kind === 'local' ? window.localStorage : window.sessionStorage;
}

const accessStateStorage: StorageLike = {
  getItem(key) {
    return resolveBrowserStorage('local').getItem(key)
      ?? resolveBrowserStorage('session').getItem(key);
  },
  removeItem(key) {
    resolveBrowserStorage('local').removeItem(key);
    resolveBrowserStorage('session').removeItem(key);
  },
  setItem(key, value) {
    let rememberMe = false;

    try {
      rememberMe = JSON.parse(value).rememberMe === true;
    } catch {
      rememberMe = false;
    }

    const nextStorage = resolveBrowserStorage(rememberMe ? 'local' : 'session');
    const staleStorage = resolveBrowserStorage(rememberMe ? 'session' : 'local');

    staleStorage.removeItem(key);
    nextStorage.setItem(key, value);
  },
};

interface AccessState {
  /**
   * 权限码
   */
  accessCodes: string[];
  /**
   * 可访问的菜单列表
   */
  accessMenus: MenuRecordRaw[];
  /**
   * 可访问的路由列表
   */
  accessRoutes: RouteRecordRaw[];
  /**
   * 登录 accessToken
   */
  accessToken: AccessToken;
  /**
   * 是否已经检查过权限
   */
  isAccessChecked: boolean;
  /**
   * 是否锁屏状态
   */
  isLockScreen: boolean;
  /**
   * 锁屏密码
   */
  lockScreenPassword?: string;
  /**
   * 登录是否过期
   */
  loginExpired: boolean;
  /**
   * 登录 accessToken
   */
  refreshToken: AccessToken;
  /**
   * 是否持久化当前登录会话
   */
  rememberMe: boolean;
}

/**
 * @zh_CN 访问权限相关
 */
export const useAccessStore = defineStore('core-access', {
  actions: {
    getMenuByPath(path: string) {
      function findMenu(
        menus: MenuRecordRaw[],
        path: string,
      ): MenuRecordRaw | undefined {
        for (const menu of menus) {
          if (menu.path === path) {
            return menu;
          }
          if (menu.children) {
            const matched = findMenu(menu.children, path);
            if (matched) {
              return matched;
            }
          }
        }
      }
      return findMenu(this.accessMenus, path);
    },
    lockScreen(password: string) {
      this.isLockScreen = true;
      this.lockScreenPassword = password;
    },
    setAccessCodes(codes: string[]) {
      this.accessCodes = codes;
    },
    setAccessMenus(menus: MenuRecordRaw[]) {
      this.accessMenus = menus;
    },
    setAccessRoutes(routes: RouteRecordRaw[]) {
      this.accessRoutes = routes;
    },
    setAccessToken(token: AccessToken) {
      this.accessToken = token;
    },
    setIsAccessChecked(isAccessChecked: boolean) {
      this.isAccessChecked = isAccessChecked;
    },
    setLoginExpired(loginExpired: boolean) {
      this.loginExpired = loginExpired;
    },
    setRememberMe(rememberMe: boolean) {
      this.rememberMe = rememberMe;
    },
    setRefreshToken(token: AccessToken) {
      this.refreshToken = token;
    },
    unlockScreen() {
      this.isLockScreen = false;
      this.lockScreenPassword = undefined;
    },
  },
  persist: {
    storage: accessStateStorage,
    pick: [
      'accessToken',
      'refreshToken',
      'accessCodes',
      'isLockScreen',
      'lockScreenPassword',
      'rememberMe',
    ],
  },
  state: (): AccessState => ({
    accessCodes: [],
    accessMenus: [],
    accessRoutes: [],
    accessToken: null,
    isAccessChecked: false,
    isLockScreen: false,
    lockScreenPassword: undefined,
    loginExpired: false,
    rememberMe: false,
    refreshToken: null,
  }),
});

// 解决热更新问题
const hot = import.meta.hot;
if (hot) {
  hot.accept(acceptHMRUpdate(useAccessStore, hot));
}
