<script lang="ts" setup>
import { computed } from 'vue';
import { watchEffect } from 'vue';

import { useAntdDesignTokens } from '@vben/hooks';
import { preferences, usePreferences } from '@vben/preferences';

import { App, ConfigProvider, theme } from 'ant-design-vue';

import { antdLocale } from '#/locales';
import { useLocaleStore } from '@/stores/locale';
import { useThemeStore } from '@/stores/theme';
import { themeTokens } from '@/theme/tokens';

defineOptions({ name: 'App' });

const { isDark } = usePreferences();
const { tokens } = useAntdDesignTokens();
const legacyThemeStore = useThemeStore();
const legacyLocaleStore = useLocaleStore();
const normalizedLocale = computed(() =>
  preferences.app.locale === 'en-US' ? 'en' : 'de',
);

const tokenTheme = computed(() => {
  const algorithm = isDark.value
    ? [theme.darkAlgorithm]
    : [theme.defaultAlgorithm];

  // antd 紧凑模式算法
  if (preferences.app.compact) {
    algorithm.push(theme.compactAlgorithm);
  }

  return {
    algorithm,
    token: tokens,
  };
});

watchEffect(() => {
  const root = document.documentElement;
  const mode = isDark.value ? 'dark' : 'light';
  const activeLocale = normalizedLocale.value;
  const legacyTokens = themeTokens[mode];

  if (legacyThemeStore.mode !== mode) {
    legacyThemeStore.$patch({ mode });
  }

  if (legacyLocaleStore.locale !== activeLocale) {
    legacyLocaleStore.$patch({ locale: activeLocale });
  }

  root.dataset.theme = legacyTokens.mode;
  root.lang = preferences.app.locale;
  root.style.setProperty('--sp-color-primary', legacyTokens.primary);
  root.style.setProperty('--sp-color-primary-strong', legacyTokens.primaryStrong);
  root.style.setProperty('--sp-color-primary-muted', legacyTokens.primaryMuted);
  root.style.setProperty('--sp-color-success', legacyTokens.success);
  root.style.setProperty('--sp-color-warning', legacyTokens.warning);
  root.style.setProperty('--sp-color-danger', legacyTokens.danger);
  root.style.setProperty('--sp-color-surface-page', legacyTokens.surfacePage);
  root.style.setProperty('--sp-color-surface-panel', legacyTokens.surfacePanel);
  root.style.setProperty('--sp-color-surface-card', legacyTokens.surfaceCard);
  root.style.setProperty('--sp-color-surface-sidebar', legacyTokens.surfaceSidebar);
  root.style.setProperty('--sp-color-border-soft', legacyTokens.borderSoft);
  root.style.setProperty('--sp-color-text-primary', legacyTokens.textPrimary);
  root.style.setProperty('--sp-color-text-secondary', legacyTokens.textSecondary);
  root.style.setProperty('--sp-color-text-inverse', legacyTokens.textInverse);
  root.style.setProperty('--sp-shadow-card', legacyTokens.shadowCard);
  root.style.setProperty('--sp-gradient-hero', legacyTokens.heroGradient);
  root.style.setProperty('--sp-page-background', legacyTokens.pageBackground);
});
</script>

<template>
  <ConfigProvider :locale="antdLocale" :theme="tokenTheme">
    <App>
      <RouterView />
    </App>
  </ConfigProvider>
</template>
