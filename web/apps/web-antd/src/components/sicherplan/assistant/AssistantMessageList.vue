<script lang="ts" setup>
import type {
  AssistantLink,
  AssistantMissingPermission,
  AssistantSourceBasisItem,
} from '#/api/sicherplan/assistant';
import type { AssistantFeedbackRating } from '#/api/sicherplan/assistant';
import type { AssistantUiMessage } from '#/store';

import { nextTick, ref, watch } from 'vue';

import AssistantFeedback from './AssistantFeedback.vue';
import AssistantEvidenceList from './AssistantEvidenceList.vue';
import AssistantLinkCard from './AssistantLinkCard.vue';

defineOptions({ name: 'AssistantMessageList' });

const props = defineProps<{
  confidenceLabel: string;
  feedbackCommentLabel: string;
  feedbackCommentPlaceholder: string;
  feedbackErrorLabel: string;
  feedbackHelpfulLabel: string;
  feedbackNotHelpfulLabel: string;
  feedbackPromptLabel: string;
  feedbackSubmitCommentLabel: string;
  feedbackSubmittedLabel: string;
  diagnosisTitle: string;
  emptyBody: string;
  emptyTitle: string;
  linkActionLabel: string;
  linksTitle: string;
  messages: AssistantUiMessage[];
  missingPermissionsTitle: string;
  nextStepsTitle: string;
  sourcesTitle: string;
  severityLabels: Record<string, string>;
  userLabel: string;
  assistantLabel: string;
}>();

const emit = defineEmits<{
  (event: 'open-link', link: AssistantLink): void;
  (
    event: 'submit-feedback',
    payload: { comment?: null | string; messageId: string; rating: AssistantFeedbackRating },
  ): void;
}>();

const scrollContainer = ref<HTMLElement | null>(null);

watch(
  () => props.messages.length,
  async () => {
    await nextTick();
    const node = scrollContainer.value;
    if (node) {
      node.scrollTop = node.scrollHeight;
    }
  },
  { immediate: true },
);

function missingPermissionKey(item: AssistantMissingPermission) {
  return `${item.permission}-${item.reason || ''}`;
}

function sourceBasisKey(item: AssistantSourceBasisItem) {
  return [
    item.source_type,
    item.source_name || '',
    item.page_id || '',
    item.title || '',
  ].join(':');
}

function sourceBasisLabel(item: AssistantSourceBasisItem) {
  const head = item.page_id || item.module_key || item.source_name || item.source_type;
  const tail = item.title || item.source_name;
  if (tail && tail !== head) {
    return `${head} - ${tail}`;
  }
  return head;
}
</script>

<template>
  <div ref="scrollContainer" class="sp-assistant-messages" data-testid="assistant-message-list">
    <div v-if="!messages.length" class="sp-assistant-messages__empty" data-testid="assistant-empty-state">
      <strong>{{ emptyTitle }}</strong>
      <p>{{ emptyBody }}</p>
    </div>

    <article
      v-for="message in messages"
      :key="message.id"
      class="sp-assistant-message"
      :class="`sp-assistant-message--${message.role}`"
      data-testid="assistant-message"
    >
      <header class="sp-assistant-message__header">
        <span class="sp-assistant-message__role">
          {{ message.role === 'user' ? userLabel : assistantLabel }}
        </span>
        <span v-if="message.structured_response?.confidence" class="sp-assistant-message__confidence">
          {{ confidenceLabel }}: {{ message.structured_response.confidence }}
        </span>
      </header>

      <p class="sp-assistant-message__content">{{ message.structured_response?.answer || message.content }}</p>

      <AssistantEvidenceList
        v-if="message.role !== 'user' && message.structured_response?.diagnosis?.length"
        :items="message.structured_response?.diagnosis || []"
        :severity-labels="severityLabels"
        :title="diagnosisTitle"
      />

      <section
        v-if="message.role !== 'user' && message.structured_response?.missing_permissions?.length"
        class="sp-assistant-message__section"
      >
        <h4>{{ missingPermissionsTitle }}</h4>
        <ul class="sp-assistant-message__bullet-list">
          <li v-for="item in message.structured_response?.missing_permissions || []" :key="missingPermissionKey(item)">
            <strong>{{ item.permission }}</strong>
            <span v-if="item.reason"> - {{ item.reason }}</span>
          </li>
        </ul>
      </section>

      <section
        v-if="message.role !== 'user' && message.structured_response?.next_steps?.length"
        class="sp-assistant-message__section"
      >
        <h4>{{ nextStepsTitle }}</h4>
        <ol class="sp-assistant-message__bullet-list">
          <li v-for="step in message.structured_response?.next_steps || []" :key="step">
            {{ step }}
          </li>
        </ol>
      </section>

      <section
        v-if="message.role !== 'user' && message.structured_response?.links?.length"
        class="sp-assistant-message__section"
      >
        <h4>{{ linksTitle }}</h4>
        <div class="sp-assistant-message__links">
          <AssistantLinkCard
            v-for="link in message.structured_response?.links || []"
            :key="`${link.path}-${link.label}`"
            :action-label="linkActionLabel"
            :link="link"
            @open="emit('open-link', $event)"
          />
        </div>
      </section>

      <section
        v-if="message.role !== 'user' && message.structured_response?.source_basis?.length"
        class="sp-assistant-message__section"
        data-testid="assistant-source-basis"
      >
        <h4>{{ sourcesTitle }}</h4>
        <ul class="sp-assistant-message__bullet-list">
          <li
            v-for="item in message.structured_response?.source_basis || []"
            :key="sourceBasisKey(item)"
          >
            <strong>{{ sourceBasisLabel(item) }}</strong>
            <span v-if="item.evidence"> - {{ item.evidence }}</span>
          </li>
        </ul>
      </section>

      <AssistantFeedback
        v-if="message.role === 'assistant'"
        :comment-label="feedbackCommentLabel"
        :comment-placeholder="feedbackCommentPlaceholder"
        :error-label="feedbackErrorLabel"
        :feedback="message.feedback"
        :helpful-label="feedbackHelpfulLabel"
        :not-helpful-label="feedbackNotHelpfulLabel"
        :prompt-label="feedbackPromptLabel"
        :submit-comment-label="feedbackSubmitCommentLabel"
        :submitted-label="feedbackSubmittedLabel"
        @submit="emit('submit-feedback', { ...$event, messageId: message.id })"
      />
    </article>
  </div>
</template>

<style scoped>
.sp-assistant-messages {
  display: grid;
  gap: 0.85rem;
  min-height: 16rem;
  max-height: min(52vh, 34rem);
  overflow: auto;
  padding-right: 0.2rem;
}

.sp-assistant-messages__empty {
  display: grid;
  gap: 0.45rem;
  padding: 1rem;
  border: 1px dashed var(--sp-color-border-soft);
  border-radius: 0.9rem;
  background: rgb(255 255 255 / 0.7);
}

[data-theme='dark'] .sp-assistant-messages__empty {
  background: rgb(12 26 28 / 0.72);
}

.sp-assistant-messages__empty strong,
.sp-assistant-messages__empty p {
  margin: 0;
}

.sp-assistant-messages__empty strong {
  color: var(--sp-color-text-primary);
}

.sp-assistant-messages__empty p {
  color: var(--sp-color-text-secondary);
  line-height: 1.5;
}

.sp-assistant-message {
  display: grid;
  gap: 0.7rem;
  max-width: 100%;
  padding: 0.9rem 1rem;
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 0.95rem;
  background: rgb(255 255 255 / 0.88);
}

[data-theme='dark'] .sp-assistant-message {
  background: rgb(12 26 28 / 0.8);
}

.sp-assistant-message--user {
  margin-left: 2rem;
}

.sp-assistant-message--assistant,
.sp-assistant-message--tool,
.sp-assistant-message--system_summary {
  margin-right: 2rem;
}

.sp-assistant-message__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.sp-assistant-message__role,
.sp-assistant-message__confidence,
.sp-assistant-message__section h4 {
  color: var(--sp-color-text-secondary);
  font-size: 0.75rem;
  font-weight: 700;
}

.sp-assistant-message__content {
  margin: 0;
  color: var(--sp-color-text-primary);
  font-size: 0.9rem;
  line-height: 1.55;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.sp-assistant-message__section {
  display: grid;
  gap: 0.55rem;
}

.sp-assistant-message__section h4 {
  margin: 0;
}

.sp-assistant-message__bullet-list {
  display: grid;
  gap: 0.35rem;
  margin: 0;
  padding-left: 1.1rem;
  color: var(--sp-color-text-secondary);
  font-size: 0.83rem;
  line-height: 1.45;
}

.sp-assistant-message__links {
  display: grid;
  gap: 0.55rem;
}

@media (max-width: 640px) {
  .sp-assistant-message--user,
  .sp-assistant-message--assistant,
  .sp-assistant-message--tool,
  .sp-assistant-message--system_summary {
    margin-inline: 0;
  }
}
</style>
