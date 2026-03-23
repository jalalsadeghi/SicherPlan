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
import { resolveLoginErrorMessageKey } from '#/api/core/auth';

import { buildLoginLocation } from './auth-bootstrap';

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
    userStore.setUserInfo(null);
  }

  function clearLoginError() {
    loginErrorMessageKey.value = null;
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
      const { accessToken } = await loginApi(params);

      // 如果成功获取到 accessToken
      if (accessToken) {
        accessStore.setAccessToken(accessToken);

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
    authLogin,
    clearLoginError,
    clearSessionState,
    fetchUserInfo,
    loginErrorMessageKey,
    loginLoading,
    logout,
    redirectToLogin,
  };
});
