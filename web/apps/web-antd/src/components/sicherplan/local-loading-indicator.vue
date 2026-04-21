<script setup lang="ts">
defineProps<{
  label: string;
  testId?: string;
}>();
</script>

<template>
  <div
    aria-live="polite"
    class="sp-customer-plan-wizard-step__local-loading sp-local-loading-indicator"
    :data-testid="testId"
    role="status"
  >
    <span aria-hidden="true" class="sp-local-loading-indicator__dot" />
    {{ label }}
  </div>
</template>

<style scoped>
.sp-customer-plan-wizard-step__local-loading,
.sp-local-loading-indicator {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  width: fit-content;
  padding: 0.3rem 0.55rem;
  border: 1px solid color-mix(in srgb, var(--sp-color-primary-strong) 22%, transparent);
  border-radius: 999px;
  background: color-mix(in srgb, var(--sp-color-primary-muted) 70%, white);
  color: var(--sp-color-primary-strong);
  font-size: 0.75rem;
  font-weight: 700;
}

.sp-local-loading-indicator__dot {
  width: 0.42rem;
  height: 0.42rem;
  border-radius: 999px;
  background: currentColor;
  animation: sp-local-loading-pulse 1s ease-in-out infinite;
}

@keyframes sp-local-loading-pulse {
  0%,
  100% {
    opacity: 0.38;
    transform: scale(0.85);
  }

  50% {
    opacity: 1;
    transform: scale(1);
  }
}
</style>
