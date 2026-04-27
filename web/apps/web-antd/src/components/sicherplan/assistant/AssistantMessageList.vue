<script lang="ts" setup>
import type {
  AssistantAnswerSegment,
  AssistantLink,
  AssistantMissingPermission,
} from '#/api/sicherplan/assistant';
import type { AssistantFeedbackRating } from '#/api/sicherplan/assistant';
import type { AssistantUiMessage } from '#/store';

import { nextTick, ref, watch } from 'vue';

import AssistantFeedback from './AssistantFeedback.vue';
import AssistantEvidenceList from './AssistantEvidenceList.vue';
import AssistantLinkCard from './AssistantLinkCard.vue';
import AssistantSourceBasis from './AssistantSourceBasis.vue';

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
  degradedWarning: string;
  emptyBody: string;
  emptyTitle: string;
  linkActionLabel: string;
  linksTitle: string;
  messages: AssistantUiMessage[];
  missingPermissionsTitle: string;
  nextStepsTitle: string;
  processingLabel: string;
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

function answerSegments(message: AssistantUiMessage): AssistantAnswerSegment[] {
  const structured = message.structured_response;
  if (structured?.answer_segments?.length) {
    return structured.answer_segments;
  }
  return [
    {
      type: 'text',
      text: structured?.answer || message.content,
    },
  ];
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

      <div
        v-if="message.pending"
        class="sp-assistant-message__pending"
        data-testid="assistant-pending-indicator"
        role="status"
        aria-live="polite"
      >
        <span aria-hidden="true" class="sp-assistant-message__pending-dot" />
        <span>{{ processingLabel }}</span>
      </div>

      <p v-else class="sp-assistant-message__content">
        <template
          v-for="(segment, index) in answerSegments(message)"
          :key="`${message.id}-segment-${index}`"
        >
          <a
            v-if="segment.type === 'link' && segment.link?.path"
            class="sp-assistant-message__inline-link"
            :aria-label="segment.link.label"
            :href="segment.link.path"
            @click.prevent="emit('open-link', segment.link)"
          >
            {{ segment.text }}
          </a>
          <span v-else>{{ segment.text }}</span>
        </template>
      </p>

      <AssistantEvidenceList
        v-if="message.role !== 'user' && message.structured_response?.diagnosis?.length"
        :items="message.structured_response?.diagnosis || []"
        :severity-labels="severityLabels"
        :title="diagnosisTitle"
      />

      <div
        v-if="message.role !== 'user' && message.structured_response?.provider_degraded"
        class="sp-assistant-message__degraded"
        data-testid="assistant-provider-degraded"
      >
        {{ degradedWarning }}
      </div>

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

      <AssistantSourceBasis
        v-if="message.role !== 'user' && message.structured_response?.source_basis?.length"
        :items="message.structured_response?.source_basis || []"
        :message-id="message.id"
        :title="sourcesTitle"
      />

      <AssistantFeedback
        v-if="message.role === 'assistant' && !message.pending"
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

.sp-assistant-message__pending {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  width: fit-content;
  max-width: 100%;
  padding: 0.3rem 0.55rem;
  border: 1px solid color-mix(in srgb, var(--sp-color-primary-strong) 22%, transparent);
  border-radius: 999px;
  background: color-mix(in srgb, var(--sp-color-primary-muted) 70%, white);
  color: var(--sp-color-primary-strong);
  font-size: 0.75rem;
  font-weight: 700;
}

[data-theme='dark'] .sp-assistant-message__pending {
  background: color-mix(in srgb, var(--sp-color-primary-muted) 58%, rgb(13 24 26));
}

.sp-assistant-message__pending-dot {
  width: 0.42rem;
  height: 0.42rem;
  border-radius: 999px;
  background: currentColor;
  flex: 0 0 auto;
  animation: sp-assistant-message-pending-pulse 1s ease-in-out infinite;
}

.sp-assistant-message__degraded {
  padding: 0.65rem 0.75rem;
  border: 1px solid rgb(196 146 24 / 0.22);
  border-radius: 0.75rem;
  background: rgb(196 146 24 / 0.08);
  color: var(--sp-color-text-secondary);
  font-size: 0.78rem;
  line-height: 1.45;
}

.sp-assistant-message__inline-link {
  color: var(--sp-color-primary);
  text-decoration: underline;
  text-underline-offset: 0.14em;
  cursor: pointer;
}

.sp-assistant-message__inline-link:hover {
  color: var(--sp-color-primary);
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

@keyframes sp-assistant-message-pending-pulse {
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

@media (max-width: 640px) {
  .sp-assistant-message--user,
  .sp-assistant-message--assistant,
  .sp-assistant-message--tool,
  .sp-assistant-message--system_summary {
    margin-inline: 0;
  }
}
</style>
