<script lang="ts" setup>
defineOptions({ name: 'AssistantLauncher' });

defineProps<{
  disabled?: boolean;
  loading?: boolean;
  open?: boolean;
  title: string;
}>();

defineEmits<{
  (event: 'toggle'): void;
}>();
</script>

<template>
  <button
    :aria-label="title"
    class="sp-assistant-launcher"
    :class="{
      'sp-assistant-launcher--disabled': disabled,
      'sp-assistant-launcher--open': open,
    }"
    :disabled="disabled"
    type="button"
    @click="$emit('toggle')"
  >
    <IconifyIcon class="sp-assistant-launcher__icon" :icon="loading ? 'lucide:loader-circle' : 'lucide:messages-square'" />
    <span class="sp-assistant-launcher__label">{{ title }}</span>
  </button>
</template>

<style scoped>
.sp-assistant-launcher {
  display: inline-flex;
  align-items: center;
  gap: 0.55rem;
  min-height: 3rem;
  padding: 0.8rem 1rem;
  border: 1px solid rgb(255 255 255 / 0.24);
  border-radius: 999px;
  background: linear-gradient(135deg, var(--sp-color-primary), var(--sp-color-primary-strong));
  color: var(--sp-color-text-inverse);
  box-shadow: 0 16px 38px rgb(14 31 34 / 0.28);
  cursor: pointer;
  transition:
    transform 0.18s ease,
    box-shadow 0.18s ease,
    opacity 0.18s ease;
}

.sp-assistant-launcher:hover:not(:disabled),
.sp-assistant-launcher:focus-visible:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 20px 42px rgb(14 31 34 / 0.32);
}

.sp-assistant-launcher:focus-visible {
  outline: 2px solid rgb(255 255 255 / 0.68);
  outline-offset: 2px;
}

.sp-assistant-launcher--disabled {
  opacity: 0.8;
  cursor: default;
}

.sp-assistant-launcher__icon {
  font-size: 1.1rem;
}

.sp-assistant-launcher--disabled .sp-assistant-launcher__icon {
  animation: sp-assistant-spin 1s linear infinite;
}

.sp-assistant-launcher__label {
  font-size: 0.95rem;
  font-weight: 700;
  line-height: 1;
}

@keyframes sp-assistant-spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
