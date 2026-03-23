<script lang="ts" setup>
import type { NotificationItem } from '@vben/layouts';

import { computed, ref, watch } from 'vue';
import { useRouter } from 'vue-router';

import { AuthenticationLoginExpiredModal } from '@vben/common-ui';
import { useWatermark } from '@vben/hooks';
import {
  BasicLayout,
  LockScreen,
  Notification,
  UserDropdown,
} from '@vben/layouts';
import { preferences } from '@vben/preferences';
import { useAccessStore, useUserStore } from '@vben/stores';

import { $t } from '#/locales';
import { useAuthStore } from '#/store';
import LoginForm from '#/views/_core/authentication/login.vue';

const notifications = ref<NotificationItem[]>([]);

const router = useRouter();
const userStore = useUserStore();
const authStore = useAuthStore();
const accessStore = useAccessStore();
const { destroyWatermark, updateWatermark } = useWatermark();
const showDot = computed(() =>
  notifications.value.some((item) => !item.isRead),
);

const menus = computed(() =>
  userStore.userInfo?.roles?.includes('platform_admin')
    ? [
        {
          handler: () => {
            router.push({ name: 'SicherPlanDashboard' });
          },
          icon: 'lucide:layout-dashboard',
          text: $t('sicherplan.admin.dashboard'),
        },
        {
          handler: () => {
            router.push({ name: 'SicherPlanTenantUsers' });
          },
          icon: 'lucide:user-cog',
          text: $t('sicherplan.admin.tenantUsers'),
        },
        {
          handler: () => {
            router.push({ name: 'SicherPlanHealthDiagnostics' });
          },
          icon: 'lucide:activity',
          text: $t('sicherplan.admin.health'),
        },
      ]
    : [
        {
          handler: () => {
            router.push({ name: 'SicherPlanDashboard' });
          },
          icon: 'lucide:layout-dashboard',
          text: $t('sicherplan.admin.dashboard'),
        },
        {
          handler: () => {
            router.push({ name: 'SicherPlanPlanningShifts' });
          },
          icon: 'lucide:calendar-range',
          text: $t('sicherplan.admin.planningShifts'),
        },
        {
          handler: () => {
            router.push({ name: 'SicherPlanReporting' });
          },
          icon: 'lucide:chart-column-big',
          text: $t('sicherplan.admin.reporting'),
        },
      ],
);

const avatar = computed(() => {
  return userStore.userInfo?.avatar ?? preferences.app.defaultAvatar;
});

const userDescription = computed(
  () => userStore.userInfo?.desc || userStore.userInfo?.username || '',
);

async function handleLogout() {
  await authStore.logout(false);
}

function handleNoticeClear() {
  notifications.value = [];
}

function markRead(id: number | string) {
  const item = notifications.value.find((item) => item.id === id);
  if (item) {
    item.isRead = true;
  }
}

function remove(id: number | string) {
  notifications.value = notifications.value.filter((item) => item.id !== id);
}

function handleMakeAll() {
  notifications.value.forEach((item) => (item.isRead = true));
}
watch(
  () => ({
    enable: preferences.app.watermark,
    content: preferences.app.watermarkContent,
  }),
  async ({ enable, content }) => {
    if (enable) {
      await updateWatermark({
        content:
          content ||
          `${userStore.userInfo?.username} - ${userStore.userInfo?.realName}`,
      });
    } else {
      destroyWatermark();
    }
  },
  {
    immediate: true,
  },
);
</script>

<template>
  <BasicLayout @clear-preferences-and-logout="handleLogout">
    <template #logo-text>
      <div class="sp-logo-text">
        <span class="sp-logo-text__title">SicherPlan</span>
        <span class="sp-logo-text__subtitle">{{ $t('sicherplan.ui.shellTagline') }}</span>
      </div>
    </template>
    <template #header-left-10>
      <div class="sp-header-ribbon">
        <span class="sp-header-ribbon__label">{{ $t('sicherplan.ui.shellRibbon') }}</span>
      </div>
    </template>
    <template #user-dropdown>
      <UserDropdown
        :avatar
        :menus
        :text="userStore.userInfo?.realName"
        :description="userDescription"
        :tag-text="$t('page.layout.userTag')"
        @logout="handleLogout"
      />
    </template>
    <template #notification>
      <Notification
        :dot="showDot"
        :notifications="notifications"
        @clear="handleNoticeClear"
        @read="(item) => item.id && markRead(item.id)"
        @remove="(item) => item.id && remove(item.id)"
        @make-all="handleMakeAll"
      />
    </template>
    <template #extra>
      <AuthenticationLoginExpiredModal
        v-model:open="accessStore.loginExpired"
        :avatar
      >
        <LoginForm />
      </AuthenticationLoginExpiredModal>
    </template>
    <template #lock-screen>
      <LockScreen :avatar @to-login="handleLogout" />
    </template>
  </BasicLayout>
</template>

<style scoped>
.sp-logo-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.sp-logo-text__title {
  font-weight: 700;
  letter-spacing: 0.01em;
}

.sp-logo-text__subtitle {
  color: color-mix(in srgb, currentColor 64%, transparent);
  font-size: 0.72rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.sp-header-ribbon {
  display: none;
  align-items: center;
  padding: 0.35rem 0.75rem;
  border: 1px solid rgb(40 170 170 / 22%);
  border-radius: 999px;
  background: rgb(40 170 170 / 10%);
  color: var(--sp-color-primary-strong);
  font-size: 0.76rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

@media (min-width: 1100px) {
  .sp-header-ribbon {
    display: inline-flex;
  }
}
</style>
