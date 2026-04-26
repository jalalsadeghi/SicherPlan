<script lang="ts" setup>
import type { AssistantLink } from '#/api/sicherplan/assistant';

defineOptions({ name: 'AssistantLinkCard' });

defineProps<{
  actionLabel: string;
  link: AssistantLink;
}>();

defineEmits<{
  (event: 'open', link: AssistantLink): void;
}>();
</script>

<template>
  <article class="sp-assistant-link-card">
    <div class="sp-assistant-link-card__body">
      <strong class="sp-assistant-link-card__label">{{ link.label }}</strong>
      <p v-if="link.reason" class="sp-assistant-link-card__reason">{{ link.reason }}</p>
      <small class="sp-assistant-link-card__path">{{ link.path }}</small>
    </div>
    <button class="sp-assistant-link-card__action" type="button" @click="$emit('open', link)">
      {{ actionLabel }}
    </button>
  </article>
</template>

<style scoped>
.sp-assistant-link-card {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 0.85rem;
  align-items: center;
  padding: 0.8rem 0.9rem;
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 0.8rem;
  background: rgb(255 255 255 / 0.8);
}

[data-theme='dark'] .sp-assistant-link-card {
  background: rgb(12 26 28 / 0.72);
}

.sp-assistant-link-card__body {
  min-width: 0;
  display: grid;
  gap: 0.25rem;
}

.sp-assistant-link-card__label {
  color: var(--sp-color-text-primary);
  font-size: 0.9rem;
}

.sp-assistant-link-card__reason,
.sp-assistant-link-card__path {
  margin: 0;
  min-width: 0;
  color: var(--sp-color-text-secondary);
  overflow-wrap: anywhere;
}

.sp-assistant-link-card__reason {
  font-size: 0.84rem;
  line-height: 1.45;
}

.sp-assistant-link-card__path {
  font-size: 0.76rem;
}

.sp-assistant-link-card__action {
  padding: 0.58rem 0.78rem;
  border: none;
  border-radius: 0.7rem;
  background: var(--sp-color-primary);
  color: var(--sp-color-text-inverse);
  font-size: 0.82rem;
  font-weight: 700;
  cursor: pointer;
}
</style>
