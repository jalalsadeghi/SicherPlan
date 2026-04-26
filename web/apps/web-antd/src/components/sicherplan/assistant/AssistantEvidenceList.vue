<script lang="ts" setup>
import type { AssistantDiagnosisItem } from '#/api/sicherplan/assistant';

defineOptions({ name: 'AssistantEvidenceList' });

defineProps<{
  items: AssistantDiagnosisItem[];
  severityLabels: Record<string, string>;
  title: string;
}>();
</script>

<template>
  <section v-if="items.length" class="sp-assistant-evidence">
    <h4 class="sp-assistant-evidence__title">{{ title }}</h4>
    <ul class="sp-assistant-evidence__list">
      <li
        v-for="item in items"
        :key="`${item.severity}-${item.finding}`"
        class="sp-assistant-evidence__item"
        :class="`sp-assistant-evidence__item--${item.severity}`"
      >
        <span class="sp-assistant-evidence__severity">{{ severityLabels[item.severity] || item.severity }}</span>
        <strong class="sp-assistant-evidence__finding">{{ item.finding }}</strong>
        <p v-if="item.evidence" class="sp-assistant-evidence__body">{{ item.evidence }}</p>
      </li>
    </ul>
  </section>
</template>

<style scoped>
.sp-assistant-evidence {
  display: grid;
  gap: 0.55rem;
}

.sp-assistant-evidence__title {
  margin: 0;
  color: var(--sp-color-text-primary);
  font-size: 0.83rem;
  font-weight: 700;
}

.sp-assistant-evidence__list {
  display: grid;
  gap: 0.55rem;
  padding: 0;
  margin: 0;
  list-style: none;
}

.sp-assistant-evidence__item {
  display: grid;
  gap: 0.2rem;
  padding: 0.75rem 0.8rem;
  border-radius: 0.8rem;
  border: 1px solid var(--sp-color-border-soft);
  background: rgb(255 255 255 / 0.76);
}

[data-theme='dark'] .sp-assistant-evidence__item {
  background: rgb(12 26 28 / 0.72);
}

.sp-assistant-evidence__item--blocking {
  border-color: rgb(191 73 73 / 0.32);
}

.sp-assistant-evidence__item--warning {
  border-color: rgb(204 145 57 / 0.28);
}

.sp-assistant-evidence__severity {
  color: var(--sp-color-text-secondary);
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
}

.sp-assistant-evidence__finding {
  color: var(--sp-color-text-primary);
  font-size: 0.88rem;
}

.sp-assistant-evidence__body {
  margin: 0;
  color: var(--sp-color-text-secondary);
  font-size: 0.82rem;
  line-height: 1.45;
  overflow-wrap: anywhere;
}
</style>
