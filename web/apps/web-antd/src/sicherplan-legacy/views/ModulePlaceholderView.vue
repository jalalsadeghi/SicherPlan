<template>
  <AdminPageShell :eyebrow="t('module.eyebrow')" :title="t(titleKey)" :lead="t(descriptionKey)">
    <template #stats>
      <AdminStatCard :label="t('shell.stat.modules')" :value="t(titleKey)" tone="accent" />
      <AdminStatCard :label="t('module.note.future')" :value="t('module.eyebrow')" />
    </template>
    <section class="module-card">
      <ul class="module-notes">
        <li>{{ t("module.note.navigation") }}</li>
        <li>{{ t("module.note.future") }}</li>
        <li>{{ t("module.note.compatibility") }}</li>
      </ul>
    </section>
  </AdminPageShell>
</template>

<script setup lang="ts">
import AdminPageShell from "@/components/AdminPageShell.vue";
import AdminStatCard from "@/components/AdminStatCard.vue";
import { useI18n } from "@/i18n";
import type { MessageKey } from "@/i18n/messages";

defineProps<{
  titleKey: MessageKey;
  descriptionKey: MessageKey;
}>();

const { t } = useI18n();
</script>
