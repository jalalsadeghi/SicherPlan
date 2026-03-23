<script lang="ts" setup>
defineProps<{
  title: string;
  description: string;
}>();
</script>

<template>
  <div class="sp-empty-state">
    <h3 class="sp-empty-state__title">{{ title }}</h3>
    <p class="sp-empty-state__description">{{ description }}</p>
  </div>
</template>

<style scoped>
.sp-empty-state {
  padding: 2rem;
  border: 1px dashed var(--sp-color-border-soft);
  border-radius: 1rem;
  background: rgb(255 255 255 / 0.46);
  text-align: center;
}

[data-theme='dark'] .sp-empty-state {
  background: rgb(12 26 28 / 0.62);
}

.sp-empty-state__title {
  margin: 0;
  color: var(--sp-color-text-primary);
  font-size: 1rem;
  font-weight: 700;
}

.sp-empty-state__description {
  margin: 0.6rem 0 0;
  color: var(--sp-color-text-secondary);
  line-height: 1.6;
}
</style>
