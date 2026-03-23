<template>
  <label class="locale-switcher">
    <span>{{ t("locale.label") }}</span>
    <select :value="locale" @change="onChange">
      <option value="de">{{ t("locale.de") }}</option>
      <option value="en">{{ t("locale.en") }}</option>
    </select>
  </label>
</template>

<script setup lang="ts">
import { useI18n } from "@/i18n";
import type { AppLocale } from "@/i18n/messages";

const { locale, setLocale, t } = useI18n();

async function onChange(event: Event) {
  const target = event.target as HTMLSelectElement;
  const nextLocale = target.value as AppLocale;
  if (nextLocale === locale.value) {
    return;
  }

  await setLocale(nextLocale);
}
</script>
