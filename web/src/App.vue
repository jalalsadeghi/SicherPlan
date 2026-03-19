<template>
  <RouterView />
</template>

<script setup lang="ts">
import { computed, watchEffect } from "vue";

import { useI18n } from "@/i18n";
import { useThemeStore } from "@/stores/theme";
import { themeTokens } from "@/theme/tokens";

const themeStore = useThemeStore();
const { locale, t } = useI18n();

const activeTokens = computed(() => themeTokens[themeStore.mode]);

watchEffect(() => {
  const root = document.documentElement;
  const tokens = activeTokens.value;

  root.dataset.theme = tokens.mode;
  root.lang = locale.value;
  document.title = t("app.title");
  root.style.setProperty("--sp-color-primary", tokens.primary);
  root.style.setProperty("--sp-color-primary-strong", tokens.primaryStrong);
  root.style.setProperty("--sp-color-primary-muted", tokens.primaryMuted);
  root.style.setProperty("--sp-color-success", tokens.success);
  root.style.setProperty("--sp-color-warning", tokens.warning);
  root.style.setProperty("--sp-color-danger", tokens.danger);
  root.style.setProperty("--sp-color-surface-page", tokens.surfacePage);
  root.style.setProperty("--sp-color-surface-panel", tokens.surfacePanel);
  root.style.setProperty("--sp-color-surface-card", tokens.surfaceCard);
  root.style.setProperty("--sp-color-surface-sidebar", tokens.surfaceSidebar);
  root.style.setProperty("--sp-color-border-soft", tokens.borderSoft);
  root.style.setProperty("--sp-color-text-primary", tokens.textPrimary);
  root.style.setProperty("--sp-color-text-secondary", tokens.textSecondary);
  root.style.setProperty("--sp-color-text-inverse", tokens.textInverse);
  root.style.setProperty("--sp-shadow-card", tokens.shadowCard);
  root.style.setProperty("--sp-gradient-hero", tokens.heroGradient);
  root.style.setProperty("--sp-page-background", tokens.pageBackground);
});
</script>
