<template>
  <section class="module-card">
    <p class="eyebrow">{{ t("module.eyebrow") }}</p>
    <h2>{{ t(titleKey) }}</h2>
    <p>{{ t(descriptionKey) }}</p>
    <ul class="module-notes">
      <li>{{ t("module.note.navigation") }}</li>
      <li>{{ t("module.note.future") }}</li>
      <li>{{ t("module.note.compatibility") }}</li>
    </ul>
  </section>
</template>

<script setup lang="ts">
import { useI18n } from "@/i18n";
import type { MessageKey } from "@/i18n/messages";

defineProps<{
  titleKey: MessageKey;
  descriptionKey: MessageKey;
}>();

const { t } = useI18n();
</script>
