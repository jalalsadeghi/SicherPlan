<script lang="ts" setup>
import type { AssistantFeedbackRating } from '#/api/sicherplan/assistant';
import type { AssistantUiFeedbackState } from '#/store';

import { computed, ref, watch } from 'vue';

defineOptions({ name: 'AssistantFeedback' });

const props = defineProps<{
  disabled?: boolean;
  feedback?: AssistantUiFeedbackState;
  helpfulLabel: string;
  notHelpfulLabel: string;
  promptLabel: string;
  submitCommentLabel: string;
  submittedLabel: string;
  commentLabel: string;
  commentPlaceholder: string;
  errorLabel: string;
}>();

const emit = defineEmits<{
  (event: 'submit', payload: { comment?: null | string; rating: AssistantFeedbackRating }): void;
}>();

const pendingRating = ref<AssistantFeedbackRating | null>(null);
const comment = ref('');

const isSubmitted = computed(() => props.feedback?.status === 'submitted');
const isSubmitting = computed(() => props.feedback?.status === 'submitting');
const errorMessage = computed(() => props.feedback?.error || null);

watch(
  () => props.feedback?.rating,
  (rating) => {
    pendingRating.value = rating || null;
  },
  { immediate: true },
);

watch(
  () => props.feedback?.comment,
  (value) => {
    comment.value = value || '';
  },
  { immediate: true },
);

function submitHelpful() {
  if (props.disabled || isSubmitting.value || isSubmitted.value) {
    return;
  }
  pendingRating.value = 'helpful';
  emit('submit', { rating: 'helpful', comment: null });
}

function startNotHelpful() {
  if (props.disabled || isSubmitting.value || isSubmitted.value) {
    return;
  }
  pendingRating.value = 'not_helpful';
}

function submitNotHelpful() {
  if (props.disabled || isSubmitting.value || isSubmitted.value) {
    return;
  }
  emit('submit', {
    rating: 'not_helpful',
    comment: comment.value.trim() || null,
  });
}
</script>

<template>
  <section class="sp-assistant-feedback" data-testid="assistant-feedback">
    <p class="sp-assistant-feedback__prompt">{{ promptLabel }}</p>

    <div class="sp-assistant-feedback__actions">
      <button
        class="sp-assistant-feedback__action"
        :class="{ 'sp-assistant-feedback__action--active': feedback?.rating === 'helpful' }"
        :disabled="disabled || isSubmitting || isSubmitted"
        type="button"
        @click="submitHelpful"
      >
        {{ helpfulLabel }}
      </button>
      <button
        class="sp-assistant-feedback__action"
        :class="{ 'sp-assistant-feedback__action--active': pendingRating === 'not_helpful' }"
        :disabled="disabled || isSubmitting || isSubmitted"
        type="button"
        @click="startNotHelpful"
      >
        {{ notHelpfulLabel }}
      </button>
    </div>

    <label
      v-if="pendingRating === 'not_helpful' && !isSubmitted"
      class="sp-assistant-feedback__comment"
    >
      <span>{{ commentLabel }}</span>
      <textarea
        v-model="comment"
        :disabled="disabled || isSubmitting"
        :placeholder="commentPlaceholder"
        rows="3"
      />
      <button
        class="sp-assistant-feedback__submit"
        :disabled="disabled || isSubmitting"
        type="button"
        @click="submitNotHelpful"
      >
        {{ submitCommentLabel }}
      </button>
    </label>

    <p v-if="isSubmitted" class="sp-assistant-feedback__submitted">
      {{ submittedLabel }}
    </p>
    <p v-else-if="errorMessage" class="sp-assistant-feedback__error">
      {{ errorLabel }}
    </p>
  </section>
</template>

<style scoped>
.sp-assistant-feedback {
  display: grid;
  gap: 0.55rem;
  padding-top: 0.2rem;
  border-top: 1px solid rgb(127 148 151 / 0.16);
}

.sp-assistant-feedback__prompt,
.sp-assistant-feedback__submitted,
.sp-assistant-feedback__error,
.sp-assistant-feedback__comment > span {
  margin: 0;
  color: var(--sp-color-text-secondary);
  font-size: 0.78rem;
  line-height: 1.45;
}

.sp-assistant-feedback__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.sp-assistant-feedback__action,
.sp-assistant-feedback__submit {
  padding: 0.5rem 0.72rem;
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 0.7rem;
  background: transparent;
  color: var(--sp-color-text-primary);
  font-size: 0.78rem;
  font-weight: 700;
  cursor: pointer;
}

.sp-assistant-feedback__action--active,
.sp-assistant-feedback__submit {
  background: rgb(40 170 170 / 0.12);
  border-color: rgb(40 170 170 / 0.4);
}

.sp-assistant-feedback__comment {
  display: grid;
  gap: 0.45rem;
}

.sp-assistant-feedback__comment textarea {
  width: 100%;
  min-height: 4.8rem;
  box-sizing: border-box;
  resize: vertical;
  padding: 0.65rem 0.75rem;
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 0.75rem;
  background: rgb(255 255 255 / 0.82);
  color: var(--sp-color-text-primary);
  font: inherit;
  line-height: 1.45;
}

[data-theme='dark'] .sp-assistant-feedback__comment textarea {
  background: rgb(12 26 28 / 0.72);
}

.sp-assistant-feedback__submit {
  justify-self: start;
}

.sp-assistant-feedback__error {
  color: rgb(191 73 73);
}

.sp-assistant-feedback__action:disabled,
.sp-assistant-feedback__submit:disabled,
.sp-assistant-feedback__comment textarea:disabled {
  cursor: not-allowed;
  opacity: 0.7;
}
</style>
