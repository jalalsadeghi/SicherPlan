<script lang="ts" setup>
import type { VbenFormSchema } from '@vben/common-ui';
import type { Recordable } from '@vben/types';

import { computed, markRaw, onBeforeUnmount, onMounted, useTemplateRef } from 'vue';

import { AuthenticationLogin, SliderCaptcha, z } from '@vben/common-ui';
import { $t } from '@vben/locales';

import { Alert } from 'ant-design-vue';

import { useAuthStore } from '#/store';
import { readRememberedLoginValues } from '#/store/auth-session';

defineOptions({ name: 'Login' });

const authStore = useAuthStore();
const loginRef =
  useTemplateRef<InstanceType<typeof AuthenticationLogin>>('loginRef');

const formSchema = computed((): VbenFormSchema[] => {
  return [
    {
      component: 'VbenInput',
      componentProps: {
        placeholder: $t('authentication.tenantCodeTip'),
      },
      fieldName: 'tenantCode',
      label: $t('authentication.tenantCode'),
      rules: z.string().min(1, { message: $t('authentication.tenantCodeTip') }),
    },
    {
      component: 'VbenInput',
      componentProps: {
        placeholder: $t('authentication.identifierTip'),
      },
      fieldName: 'identifier',
      label: $t('authentication.identifier'),
      rules: z.string().min(1, { message: $t('authentication.identifierTip') }),
    },
    {
      component: 'VbenInputPassword',
      componentProps: {
        placeholder: $t('authentication.password'),
      },
      fieldName: 'password',
      label: $t('authentication.password'),
      rules: z.string().min(1, { message: $t('authentication.passwordTip') }),
    },
    {
      component: 'VbenCheckbox',
      fieldName: 'rememberMe',
      renderComponentContent: () => ({
        default: () => $t('authentication.rememberMe'),
      }),
    },
    {
      component: markRaw(SliderCaptcha),
      fieldName: 'captcha',
      rules: z.boolean().refine((value) => value, {
        message: $t('authentication.verifyRequiredTip'),
      }),
    },
  ];
});

async function onSubmit(params: Recordable<any>) {
  authStore.authLogin(params).catch(() => {
    const formApi = loginRef.value?.getFormApi();
    formApi?.setFieldValue('captcha', false, false);
    formApi
      ?.getFieldComponentRef<InstanceType<typeof SliderCaptcha>>('captcha')
      ?.resume();
  });
}

onMounted(() => {
  authStore.clearLoginError();
  const formApi = loginRef.value?.getFormApi();
  const remembered = readRememberedLoginValues();
  formApi?.setFieldValue('tenantCode', remembered.tenantCode, false);
  formApi?.setFieldValue('identifier', remembered.identifier, false);
  formApi?.setFieldValue('rememberMe', remembered.rememberMe, false);
});

onBeforeUnmount(() => {
  authStore.clearLoginError();
});
</script>

<template>
  <div>
    <Alert
      v-if="authStore.loginErrorMessageKey"
      class="mb-4"
      show-icon
      type="error"
      :message="$t(authStore.loginErrorMessageKey)"
    />
    <AuthenticationLogin
      ref="loginRef"
      :form-schema="formSchema"
      :loading="authStore.loginLoading"
      :show-remember-me="false"
      @submit="onSubmit"
    />
  </div>
</template>
