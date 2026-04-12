import type { Recordable, UserInfo } from '@vben/types';

import { ref } from 'vue';

import { LOGIN_PATH } from '@vben/constants';
import { preferences } from '@vben/preferences';
import { resetAllStores, useAccessStore, useUserStore } from '@vben/stores';

import { notification } from 'ant-design-vue';
import { defineStore } from 'pinia';

import {
  getAccessCodesApi,
  getUserInfoApi,
  loginApi,
  logoutApi,
} from '#/api';
import { $t } from '#/locales';
import { refreshTokenApi, resolveLoginErrorMessageKey } from '#/api/core/auth';
import { useAuthStore as useLegacyAuthStore } from '#/sicherplan-legacy/stores/auth';

import { buildLoginLocation } from './auth-bootstrap';
import {
  clearStoredAuthSessionMetadata,
  persistAuthSessionMetadata,
  persistRememberedLoginValues,
  readStoredAuthSessionMetadata,
} from './auth-session';
import { emitAuthSessionStateChanged } from './auth-session-events';
import { isAuthSessionExpiringSoon } from './auth-session-timing';

let refreshInFlight: null | Promise<string> = null;

export const useAuthStore = defineStore('auth', () => {
  const accessStore = useAccessStore();
  const userStore = useUserStore();

  const loginLoading = ref(false);
  const loginErrorMessageKey = ref<null | string>(null);

  async function resolveRouter() {
    const { router } = await import('#/router');
    return router;
  }

  function clearSessionState() {
    accessStore.setAccessToken(null);
    accessStore.setRefreshToken(null);
    accessStore.setAccessCodes([]);
    accessStore.setAccessMenus([]);
    accessStore.setAccessRoutes([]);
    accessStore.setIsAccessChecked(false);
    accessStore.setLoginExpired(false);
    accessStore.setRememberMe(false);
    userStore.setUserInfo(null);
    clearStoredAuthSessionMetadata();
    try {
      useLegacyAuthStore().clearSession();
    } catch {
      // Ignore legacy store cleanup when Pinia is not active.
    }
    emitAuthSessionStateChanged();
  }

  function clearLoginError() {
    loginErrorMessageKey.value = null;
  }

  function applySessionTokens(
    payload: {
      accessToken: string;
      accessTokenExpiresAt: string;
      refreshToken: string;
      refreshTokenExpiresAt: string;
      sessionId: string;
    },
    options?: {
      rememberMe?: boolean;
    },
  ) {
    accessStore.setAccessToken(payload.accessToken);
    accessStore.setRefreshToken(payload.refreshToken);
    accessStore.setRememberMe(Boolean(options?.rememberMe));
    persistAuthSessionMetadata({
      accessTokenExpiresAt: payload.accessTokenExpiresAt,
      refreshTokenExpiresAt: payload.refreshTokenExpiresAt,
      rememberMe: Boolean(options?.rememberMe),
      sessionId: payload.sessionId,
    });
    try {
      useLegacyAuthStore().syncFromPrimarySession();
    } catch {
      // Ignore legacy-store sync when Pinia is not active.
    }
    emitAuthSessionStateChanged();
  }

  async function handleSessionExpired(redirectPath?: string) {
    const shouldShowExpiredModal =
      preferences.app.loginExpiredMode === 'modal'
      && accessStore.isAccessChecked;
    clearSessionState();
    if (shouldShowExpiredModal) {
      accessStore.setLoginExpired(true);
      return;
    }
    await redirectToLogin(redirectPath);
  }

  async function refreshAccessToken(options?: {
    redirectOnFailure?: boolean;
  }) {
    if (refreshInFlight) {
      return refreshInFlight;
    }

    const sessionMetadata = readStoredAuthSessionMetadata();

    refreshInFlight = (async () => {
      const refreshed = await refreshTokenApi();
      applySessionTokens(refreshed, {
        rememberMe: sessionMetadata.rememberMe,
      });
      return refreshed.accessToken;
    })()
      .catch(async (error) => {
        if (options?.redirectOnFailure) {
          await handleSessionExpired();
        } else {
          clearSessionState();
        }
        throw error;
      })
      .finally(() => {
        refreshInFlight = null;
      });

    return refreshInFlight;
  }

  async function ensureSessionReady(options?: {
    forceRefresh?: boolean;
    redirectOnFailure?: boolean;
  }) {
    const sessionMetadata = readStoredAuthSessionMetadata();
    const hasRefreshToken = Boolean(accessStore.refreshToken);
    const needsRefresh =
      options?.forceRefresh
      || !accessStore.accessToken
      || isAuthSessionExpiringSoon(sessionMetadata.accessTokenExpiresAt);

    if (!needsRefresh) {
      emitAuthSessionStateChanged();
      return true;
    }

    if (!hasRefreshToken) {
      if (options?.redirectOnFailure) {
        await handleSessionExpired();
      } else {
        clearSessionState();
      }
      return false;
    }

    if (
      sessionMetadata.refreshTokenExpiresAt
      && isAuthSessionExpiringSoon(sessionMetadata.refreshTokenExpiresAt, Date.now(), 0)
    ) {
      if (options?.redirectOnFailure) {
        await handleSessionExpired();
      } else {
        clearSessionState();
      }
      return false;
    }

    try {
      await refreshAccessToken({
        redirectOnFailure: options?.redirectOnFailure,
      });
      return true;
    } catch {
      return false;
    }
  }

  /**
   * 异步处理登录操作
   * Asynchronously handle the login process
   * @param params 登录表单数据
   */
  async function authLogin(
    params: Recordable<any>,
    onSuccess?: () => Promise<void> | void,
  ) {
    // 异步处理用户登录操作并获取 accessToken
    let userInfo: null | UserInfo = null;
    try {
      clearLoginError();
      loginLoading.value = true;
      accessStore.setRememberMe(Boolean(params.rememberMe));
      persistRememberedLoginValues(params);
      const session = await loginApi(params);

      // 如果成功获取到 accessToken
      if (session.accessToken) {
        applySessionTokens(session, {
          rememberMe: Boolean(params.rememberMe),
        });

        // 获取用户信息并存储到 accessStore 中
        const [fetchUserInfoResult, accessCodes] = await Promise.all([
          fetchUserInfo(),
          getAccessCodesApi(),
        ]);

        userInfo = fetchUserInfoResult;

        userStore.setUserInfo(userInfo);
        accessStore.setAccessCodes(accessCodes);

        if (accessStore.loginExpired) {
          accessStore.setLoginExpired(false);
        } else {
          const router = await resolveRouter();
          onSuccess
            ? await onSuccess?.()
            : await router.push(
                userInfo.homePath || preferences.app.defaultHomePath,
              );
        }

        if (userInfo?.realName) {
          notification.success({
            description: `${$t('authentication.loginSuccessDesc')}:${userInfo?.realName}`,
            duration: 3,
            message: $t('authentication.loginSuccess'),
          });
        }
      }
    } catch (error) {
      accessStore.setAccessToken(null);
      accessStore.setRefreshToken(null);
      loginErrorMessageKey.value = resolveLoginErrorMessageKey(error);
      notification.error({
        description: $t(loginErrorMessageKey.value),
        message: $t('page.auth.login'),
      });
      throw error;
    } finally {
      loginLoading.value = false;
    }

    return {
      userInfo,
    };
  }

  async function logout(redirect: boolean = true) {
    try {
      await logoutApi();
    } catch {
      // 不做任何处理
    }
    resetAllStores();
    clearSessionState();

    const router = await resolveRouter();
    await router.replace(
      buildLoginLocation(
        LOGIN_PATH,
        preferences.app.defaultHomePath,
        router.currentRoute.value.fullPath,
        redirect,
      ),
    );
  }

  async function fetchUserInfo() {
    const userInfo = await getUserInfoApi();
    userStore.setUserInfo(userInfo);
    return userInfo;
  }

  async function redirectToLogin(redirectPath?: string) {
    const router = await resolveRouter();
    await router.replace(
      buildLoginLocation(
        LOGIN_PATH,
        preferences.app.defaultHomePath,
        redirectPath,
        true,
      ),
    );
  }

  function $reset() {
    loginLoading.value = false;
    clearLoginError();
  }

  return {
    $reset,
    applySessionTokens,
    authLogin,
    clearLoginError,
    clearSessionState,
    ensureSessionReady,
    fetchUserInfo,
    handleSessionExpired,
    get hasRefreshToken() {
      return Boolean(accessStore.refreshToken);
    },
    loginErrorMessageKey,
    loginLoading,
    logout,
    refreshAccessToken,
    redirectToLogin,
  };
});
