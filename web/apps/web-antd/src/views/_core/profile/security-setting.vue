<script setup lang="ts">
import { computed } from 'vue';

import { ProfileSecuritySetting } from '@vben/common-ui';
import { $t } from '#/locales';

const formSchema = computed(() => {
  return [
    {
      value: true,
      fieldName: 'accountPassword',
      label: $t('page.profile.security.accountPassword'),
      description: $t('page.profile.security.accountPasswordDesc'),
    },
    {
      value: true,
      fieldName: 'securityPhone',
      label: $t('page.profile.security.securityPhone'),
      description: $t('page.profile.security.securityPhoneDesc'),
    },
    {
      value: true,
      fieldName: 'securityQuestion',
      label: $t('page.profile.security.securityQuestion'),
      description: $t('page.profile.security.securityQuestionDesc'),
    },
    {
      value: true,
      fieldName: 'securityEmail',
      label: $t('page.profile.security.securityEmail'),
      description: $t('page.profile.security.securityEmailDesc'),
    },
    {
      value: false,
      fieldName: 'securityMfa',
      label: $t('page.profile.security.securityMfa'),
      description: $t('page.profile.security.securityMfaDesc'),
    },
  ];
});
</script>
<template>
  <ProfileSecuritySetting :form-schema="formSchema" />
</template>
