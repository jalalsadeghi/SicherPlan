<script setup lang="ts">
import { computed } from 'vue';

import { ProfileNotificationSetting } from '@vben/common-ui';
import { $t } from '#/locales';

const formSchema = computed(() => {
  return [
    {
      value: true,
      fieldName: 'accountPassword',
      label: $t('page.profile.notifications.accountPassword'),
      description: $t('page.profile.notifications.accountPasswordDesc'),
    },
    {
      value: true,
      fieldName: 'systemMessage',
      label: $t('page.profile.notifications.systemMessage'),
      description: $t('page.profile.notifications.systemMessageDesc'),
    },
    {
      value: true,
      fieldName: 'todoTask',
      label: $t('page.profile.notifications.todoTask'),
      description: $t('page.profile.notifications.todoTaskDesc'),
    },
  ];
});
</script>
<template>
  <ProfileNotificationSetting :form-schema="formSchema" />
</template>
