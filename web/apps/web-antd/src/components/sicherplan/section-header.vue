<script lang="ts" setup>
defineProps<{
  title: string;
  description?: string;
}>();
</script>

<template>
  <div class="sp-section-header">
    <div>
      <h2 class="sp-section-header__title">{{ title }}</h2>
      <p v-if="description" class="sp-section-header__description">
        {{ description }}
      </p>
    </div>
    <div v-if="$slots.action" class="sp-section-header__action">
      <slot name="action" />
    </div>
  </div>
</template>

<style scoped>
.sp-section-header {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 1rem;
}

.sp-section-header__title {
  margin: 0;
  color: var(--sp-color-text-primary);
  font-size: 1.05rem;
  font-weight: 700;
}

.sp-section-header__description {
  margin: 0.35rem 0 0;
  color: var(--sp-color-text-secondary);
  line-height: 1.55;
}

.sp-section-header__action {
  flex-shrink: 0;
}
</style>
