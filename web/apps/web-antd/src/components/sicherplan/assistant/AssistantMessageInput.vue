<script lang="ts" setup>
import { computed, ref } from 'vue';

defineOptions({ name: 'AssistantMessageInput' });

const props = defineProps<{
  disabled?: boolean;
  inputLabel: string;
  placeholder: string;
  sending?: boolean;
  submitLabel: string;
  value: string;
}>();

const emit = defineEmits<{
  (event: 'submit'): void;
  (event: 'update:value', value: string): void;
}>();

const textareaRef = ref<HTMLTextAreaElement | null>(null);

const model = computed({
  get: () => props.value,
  set: (value: string) => emit('update:value', value),
});

function onKeydown(event: KeyboardEvent) {
  if (event.key !== 'Enter' || event.shiftKey) {
    return;
  }
  event.preventDefault();
  if (!props.disabled && !props.sending && props.value.trim()) {
    emit('submit');
  }
}

function focus() {
  textareaRef.value?.focus();
}

defineExpose({ focus });
</script>

<template>
  <form class="sp-assistant-input" @submit.prevent="$emit('submit')">
    <label class="sp-assistant-input__field">
      <span class="sp-assistant-input__label">{{ inputLabel }}</span>
      <textarea
        ref="textareaRef"
        v-model="model"
        :aria-label="inputLabel"
        :disabled="disabled"
        :placeholder="placeholder"
        class="sp-assistant-input__textarea"
        rows="3"
        @keydown="onKeydown"
      />
    </label>
    <button
      class="sp-assistant-input__submit"
      :disabled="disabled || !value.trim()"
      type="submit"
    >
      {{ sending ? `${submitLabel}...` : submitLabel }}
    </button>
  </form>
</template>

<style scoped>
.sp-assistant-input {
  display: grid;
  gap: 0.75rem;
}

.sp-assistant-input__field {
  display: grid;
  gap: 0.4rem;
}

.sp-assistant-input__label {
  color: var(--sp-color-text-secondary);
  font-size: 0.76rem;
  font-weight: 600;
}

.sp-assistant-input__textarea {
  width: 100%;
  min-height: 5.4rem;
  resize: vertical;
  box-sizing: border-box;
  padding: 0.75rem 0.85rem;
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 0.85rem;
  background: rgb(255 255 255 / 0.86);
  color: var(--sp-color-text-primary);
  font: inherit;
  line-height: 1.45;
}

[data-theme='dark'] .sp-assistant-input__textarea {
  background: rgb(12 26 28 / 0.74);
}

.sp-assistant-input__textarea:focus-visible {
  outline: 2px solid rgb(40 170 170 / 0.34);
  outline-offset: 1px;
}

.sp-assistant-input__submit {
  justify-self: end;
  min-width: 6.5rem;
  padding: 0.7rem 0.95rem;
  border: none;
  border-radius: 0.8rem;
  background: var(--sp-color-primary);
  color: var(--sp-color-text-inverse);
  font-size: 0.84rem;
  font-weight: 700;
  cursor: pointer;
}

.sp-assistant-input__submit:disabled,
.sp-assistant-input__textarea:disabled {
  cursor: not-allowed;
  opacity: 0.72;
}
</style>
