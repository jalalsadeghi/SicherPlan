<template>
  <button class="theme-toggle" type="button" @click="themeStore.toggleMode()">
    <span class="theme-toggle__label">{{ themeLabel }}</span>
    <span class="theme-toggle__badge">{{ themeBadge }}</span>
  </button>
</template>

<script setup lang="ts">
import { computed } from "vue";

import { useI18n } from "@/i18n";
import { useThemeStore } from "@/stores/theme";

const themeStore = useThemeStore();
const { t } = useI18n();

const themeLabel = computed(() =>
  themeStore.mode === "light" ? t("theme.toggle.light") : t("theme.toggle.dark"),
);

const themeBadge = computed(() =>
  themeStore.mode === "light" ? t("theme.mode.light") : t("theme.mode.dark"),
);
</script>
