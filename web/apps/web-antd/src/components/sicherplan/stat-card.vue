<script lang="ts" setup>
defineProps<{
  label: string;
  value: string;
  hint?: string;
}>();
</script>

<template>
  <article class="sp-stat-card">
    <span class="sp-stat-card__label">{{ label }}</span>
    <strong class="sp-stat-card__value">{{ value }}</strong>
    <span v-if="hint" class="sp-stat-card__hint">{{ hint }}</span>
  </article>
</template>

<style scoped>
.sp-stat-card {
  display: grid;
  gap: 0.35rem;
  min-width: 0;
  padding: 1rem 1.1rem;
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 1rem;
  background: var(--sp-color-surface-card);
  box-shadow: var(--sp-shadow-card);
}

.sp-stat-card__label,
.sp-stat-card__hint {
  color: var(--sp-color-text-secondary);
  font-size: 0.84rem;
}

.sp-stat-card__value {
  color: var(--sp-color-text-primary);
  font-size: 1.1rem;
  font-weight: 700;
}
</style>
