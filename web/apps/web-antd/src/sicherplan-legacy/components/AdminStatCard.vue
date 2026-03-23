<script setup lang="ts">
defineProps<{
  label: string;
  value: string | number;
  tone?: 'default' | 'accent';
}>();
</script>

<template>
  <article class="sp-stat-card" :data-tone="tone || 'default'">
    <span class="sp-stat-card__label">{{ label }}</span>
    <strong class="sp-stat-card__value">{{ value }}</strong>
    <div v-if="$slots.default" class="sp-stat-card__detail">
      <slot />
    </div>
  </article>
</template>

<style scoped>
.sp-stat-card {
  display: grid;
  gap: 0.45rem;
  padding: 1rem 1.1rem;
  border: 1px solid rgb(15 23 42 / 8%);
  border-radius: 1rem;
  background:
    linear-gradient(180deg, rgb(255 255 255 / 0.98), rgb(246 249 251 / 0.94));
  box-shadow: 0 14px 36px rgb(15 23 42 / 0.06);
}

.sp-stat-card[data-tone='accent'] {
  border-color: rgb(40 170 170 / 28%);
  background:
    linear-gradient(180deg, rgb(233 248 248 / 0.98), rgb(245 252 252 / 0.96));
}

.sp-stat-card__label {
  color: var(--vp-c-text-2, rgb(84 96 111));
  font-size: 0.82rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.sp-stat-card__value {
  font-size: 1.55rem;
  line-height: 1.1;
}

.sp-stat-card__detail {
  color: var(--vp-c-text-2, rgb(84 96 111));
  font-size: 0.92rem;
}
</style>

