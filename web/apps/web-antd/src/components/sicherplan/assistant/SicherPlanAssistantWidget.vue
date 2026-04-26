<script lang="ts" setup>
import type { AssistantLink } from '#/api/sicherplan/assistant';

import { LOGIN_PATH } from '@vben/constants';
import { useAccessStore } from '@vben/stores';

import { computed, nextTick, onMounted, watch } from 'vue';
import { ref } from 'vue';

import { $t } from '#/locales';
import { router } from '#/router';
import { useAssistantStore } from '#/store';

import AssistantLauncher from './AssistantLauncher.vue';
import AssistantPanel from './AssistantPanel.vue';

defineOptions({ name: 'SicherPlanAssistantWidget' });

const accessStore = useAccessStore();
const assistantStore = useAssistantStore();
const panelRef = ref<InstanceType<typeof AssistantPanel> | null>(null);

const currentRoute = computed(() => router.currentRoute.value);
const isAuthenticated = computed(() => Boolean(accessStore.accessToken));
const isPublicRoute = computed(() => {
  const route = currentRoute.value;
  return route.path === LOGIN_PATH || route.meta?.ignoreAccess === true;
});

const shouldCheckCapabilities = computed(() => isAuthenticated.value && !isPublicRoute.value);
const shouldShowLauncher = computed(() => {
  if (!shouldCheckCapabilities.value) {
    return false;
  }
  if (assistantStore.loadingCapabilities) {
    return true;
  }
  return assistantStore.enabled && assistantStore.canChat;
});

const panelVisible = computed(() => shouldShowLauncher.value && assistantStore.isOpen);

const title = computed(() => $t('assistant.widget.title'));
const description = computed(() => $t('assistant.widget.description'));
const launcherLabel = computed(() =>
  assistantStore.loadingCapabilities
    ? $t('assistant.widget.loadingLabel')
    : $t('assistant.widget.launcherLabel'),
);
const providerWarning = computed(() => {
  const capabilities = assistantStore.capabilities;
  if (
    capabilities?.provider_mode === 'mock'
    && capabilities.mock_provider_allowed
  ) {
    return $t('assistant.widget.mockModeWarning');
  }
  return null;
});

const severityLabels = computed<Record<string, string>>(() => ({
  blocking: $t('assistant.widget.severity.blocking'),
  info: $t('assistant.widget.severity.info'),
  warning: $t('assistant.widget.severity.warning'),
}));

async function ensureCapabilities() {
  if (!shouldCheckCapabilities.value) {
    return;
  }
  if (assistantStore.loadingCapabilities) {
    return;
  }
  try {
    await assistantStore.loadCapabilities();
  } catch {
    // The widget falls back to a safe hidden/error state via store flags.
  }
}

async function openPanel() {
  if (!shouldCheckCapabilities.value) {
    return;
  }
  await ensureCapabilities();
  await assistantStore.openAssistant();
  if (assistantStore.isOpen) {
    await assistantStore.restorePersistedConversation().catch(() => undefined);
    await nextTick();
    panelRef.value?.focusInput();
  }
}

function closePanel() {
  assistantStore.closeAssistant();
}

async function togglePanel() {
  if (assistantStore.isOpen) {
    closePanel();
    return;
  }
  await openPanel();
}

async function submitMessage() {
  assistantStore.captureCurrentRouteContext();
  await assistantStore.sendMessage(assistantStore.draftInput);
}

async function submitFeedback(payload: {
  comment?: null | string;
  messageId: string;
  rating: 'helpful' | 'not_helpful';
}) {
  try {
    await assistantStore.submitFeedback(payload.messageId, payload.rating, payload.comment);
  } catch {
    // Per-message feedback state already carries the safe error label.
  }
}

function updateDraft(value: string) {
  assistantStore.setDraftInput(value);
}

async function openLink(link: AssistantLink) {
  if (!link.path) {
    return;
  }
  await router.push(link.path);
}

watch(
  shouldCheckCapabilities,
  async (allowed) => {
    if (!allowed) {
      assistantStore.closeAssistant();
      return;
    }
    await ensureCapabilities();
  },
  { immediate: true },
);

watch(
  () => currentRoute.value.fullPath,
  () => {
    if (!shouldCheckCapabilities.value) {
      return;
    }
    assistantStore.captureCurrentRouteContext();
  },
);

onMounted(async () => {
  if (!shouldCheckCapabilities.value) {
    return;
  }
  await ensureCapabilities();
  if (assistantStore.isOpen) {
    await assistantStore.restorePersistedConversation().catch(() => undefined);
  }
});
</script>

<template>
  <div v-if="shouldShowLauncher" class="sp-assistant-widget" data-testid="assistant-widget">
    <Transition name="sp-assistant-panel">
      <AssistantPanel
        ref="panelRef"
        v-if="panelVisible"
        :assistant-label="$t('assistant.widget.assistantLabel')"
        :close-label="$t('assistant.widget.closeLabel')"
        :confidence-label="$t('assistant.widget.confidence')"
        :description="description"
        :diagnosis-title="$t('assistant.widget.diagnosisTitle')"
        :draft-input="assistantStore.draftInput"
        :empty-body="$t('assistant.widget.emptyBody')"
        :empty-title="$t('assistant.widget.emptyTitle')"
        :error-body="$t('assistant.widget.errorBody')"
        :error-visible="Boolean(assistantStore.error)"
        :feedback-comment-label="$t('assistant.widget.feedback.commentLabel')"
        :feedback-comment-placeholder="$t('assistant.widget.feedback.commentPlaceholder')"
        :feedback-error-label="$t('assistant.widget.feedback.error')"
        :feedback-helpful-label="$t('assistant.widget.feedback.helpful')"
        :feedback-not-helpful-label="$t('assistant.widget.feedback.notHelpful')"
        :feedback-prompt-label="$t('assistant.widget.feedback.prompt')"
        :feedback-submit-comment-label="$t('assistant.widget.feedback.submit')"
        :feedback-submitted-label="$t('assistant.widget.feedback.submitted')"
        :input-label="$t('assistant.widget.inputLabel')"
        :input-placeholder="$t('assistant.widget.inputPlaceholder')"
        :link-action-label="$t('assistant.widget.openLink')"
        :links-title="$t('assistant.widget.linksTitle')"
        :loading-conversation="assistantStore.loadingConversation"
        :messages="assistantStore.messages"
        :missing-permissions-title="$t('assistant.widget.missingPermissionsTitle')"
        :provider-warning="providerWarning"
        :next-steps-title="$t('assistant.widget.nextStepsTitle')"
        :sending-message="assistantStore.sendingMessage"
        :severity-labels="severityLabels"
        :submit-label="$t('assistant.widget.send')"
        :title="title"
        :user-label="$t('assistant.widget.userLabel')"
        @close="closePanel"
        @open-link="openLink"
        @send="submitMessage"
        @submit-feedback="submitFeedback"
        @update:draft-input="updateDraft"
      />
    </Transition>

    <AssistantLauncher
      :disabled="assistantStore.loadingCapabilities"
      :loading="assistantStore.loadingCapabilities"
      :open="assistantStore.isOpen"
      :title="launcherLabel"
      @toggle="togglePanel"
    />
  </div>
</template>

<style scoped>
.sp-assistant-widget {
  position: fixed;
  right: 1rem;
  bottom: 1rem;
  z-index: 1050;
  display: grid;
  justify-items: end;
  gap: 0.85rem;
  max-width: calc(100vw - 1rem);
}

.sp-assistant-panel-enter-active,
.sp-assistant-panel-leave-active {
  transition:
    opacity 0.18s ease,
    transform 0.18s ease;
}

.sp-assistant-panel-enter-from,
.sp-assistant-panel-leave-to {
  opacity: 0;
  transform: translateY(8px);
}

@media (max-width: 640px) {
  .sp-assistant-widget {
    right: 0.5rem;
    bottom: 0.5rem;
  }
}
</style>
