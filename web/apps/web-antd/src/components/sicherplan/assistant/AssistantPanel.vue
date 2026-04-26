<script lang="ts" setup>
import type { AssistantLink } from '#/api/sicherplan/assistant';
import type { AssistantFeedbackRating } from '#/api/sicherplan/assistant';
import type { AssistantUiMessage } from '#/store';

import { ref } from 'vue';

import AssistantMessageInput from './AssistantMessageInput.vue';
import AssistantMessageList from './AssistantMessageList.vue';

defineOptions({ name: 'AssistantPanel' });

defineProps<{
  assistantLabel: string;
  closeLabel: string;
  confidenceLabel: string;
  description: string;
  diagnosisTitle: string;
  draftInput: string;
  emptyBody: string;
  emptyTitle: string;
  errorBody: string;
  errorVisible?: boolean;
  inputLabel: string;
  inputPlaceholder: string;
  feedbackCommentLabel: string;
  feedbackCommentPlaceholder: string;
  feedbackErrorLabel: string;
  feedbackHelpfulLabel: string;
  feedbackNotHelpfulLabel: string;
  feedbackPromptLabel: string;
  feedbackSubmitCommentLabel: string;
  feedbackSubmittedLabel: string;
  linkActionLabel: string;
  linksTitle: string;
  loadingConversation?: boolean;
  messages: AssistantUiMessage[];
  missingPermissionsTitle: string;
  nextStepsTitle: string;
  sendingMessage?: boolean;
  severityLabels: Record<string, string>;
  submitLabel: string;
  title: string;
  userLabel: string;
}>();

const emit = defineEmits<{
  (event: 'close'): void;
  (event: 'open-link', link: AssistantLink): void;
  (
    event: 'submit-feedback',
    payload: { comment?: null | string; messageId: string; rating: AssistantFeedbackRating },
  ): void;
  (event: 'send'): void;
  (event: 'update:draftInput', value: string): void;
}>();

const inputRef = ref<InstanceType<typeof AssistantMessageInput> | null>(null);

function focusInput() {
  inputRef.value?.focus();
}

defineExpose({ focusInput });
</script>

<template>
  <section
    aria-modal="false"
    class="sp-assistant-panel"
    role="dialog"
    data-testid="assistant-panel"
  >
    <header class="sp-assistant-panel__header">
      <div class="sp-assistant-panel__title-block">
        <strong class="sp-assistant-panel__title">{{ title }}</strong>
        <p class="sp-assistant-panel__description">{{ description }}</p>
      </div>
      <button
        :aria-label="closeLabel"
        class="sp-assistant-panel__close"
        type="button"
        @click="$emit('close')"
      >
        <IconifyIcon icon="lucide:x" />
      </button>
    </header>

    <div v-if="errorVisible" class="sp-assistant-panel__error" data-testid="assistant-error-state">
      {{ errorBody }}
    </div>

    <div v-if="loadingConversation" class="sp-assistant-panel__loading" data-testid="assistant-loading-state">
      <IconifyIcon icon="lucide:loader-circle" />
    </div>

    <AssistantMessageList
      :assistant-label="assistantLabel"
      :confidence-label="confidenceLabel"
      :feedback-comment-label="feedbackCommentLabel"
      :feedback-comment-placeholder="feedbackCommentPlaceholder"
      :feedback-error-label="feedbackErrorLabel"
      :feedback-helpful-label="feedbackHelpfulLabel"
      :feedback-not-helpful-label="feedbackNotHelpfulLabel"
      :feedback-prompt-label="feedbackPromptLabel"
      :feedback-submit-comment-label="feedbackSubmitCommentLabel"
      :feedback-submitted-label="feedbackSubmittedLabel"
      :diagnosis-title="diagnosisTitle"
      :empty-body="emptyBody"
      :empty-title="emptyTitle"
      :link-action-label="linkActionLabel"
      :links-title="linksTitle"
      :messages="messages"
      :missing-permissions-title="missingPermissionsTitle"
      :next-steps-title="nextStepsTitle"
      :severity-labels="severityLabels"
      :user-label="userLabel"
      @submit-feedback="$emit('submit-feedback', $event)"
      @open-link="$emit('open-link', $event)"
    />

    <AssistantMessageInput
      ref="inputRef"
      :disabled="sendingMessage"
      :input-label="inputLabel"
      :placeholder="inputPlaceholder"
      :sending="sendingMessage"
      :submit-label="submitLabel"
      :value="draftInput"
      @submit="$emit('send')"
      @update:value="$emit('update:draftInput', $event)"
    />
  </section>
</template>

<style scoped>
.sp-assistant-panel {
  display: grid;
  gap: 0.95rem;
  width: min(28rem, calc(100vw - 1.5rem));
  max-height: 78vh;
  padding: 1rem;
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 1rem;
  background: var(--sp-color-surface-panel);
  box-shadow: 0 24px 58px rgb(10 26 30 / 0.3);
}

.sp-assistant-panel__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.9rem;
}

.sp-assistant-panel__title-block {
  min-width: 0;
  display: grid;
  gap: 0.25rem;
}

.sp-assistant-panel__title {
  color: var(--sp-color-text-primary);
  font-size: 1rem;
}

.sp-assistant-panel__description {
  margin: 0;
  color: var(--sp-color-text-secondary);
  font-size: 0.83rem;
  line-height: 1.45;
}

.sp-assistant-panel__close {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 0.7rem;
  background: transparent;
  color: var(--sp-color-text-secondary);
  cursor: pointer;
}

.sp-assistant-panel__error {
  padding: 0.75rem 0.85rem;
  border: 1px solid rgb(191 73 73 / 0.28);
  border-radius: 0.8rem;
  background: rgb(191 73 73 / 0.08);
  color: var(--sp-color-text-primary);
  font-size: 0.83rem;
  line-height: 1.45;
}

.sp-assistant-panel__loading {
  display: flex;
  justify-content: center;
  color: var(--sp-color-text-secondary);
  font-size: 1.15rem;
}

.sp-assistant-panel__loading :deep(svg) {
  animation: sp-assistant-spin 1s linear infinite;
}

@keyframes sp-assistant-spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 640px) {
  .sp-assistant-panel {
    width: calc(100vw - 1rem);
    max-height: 72vh;
    padding: 0.9rem;
  }
}
</style>
