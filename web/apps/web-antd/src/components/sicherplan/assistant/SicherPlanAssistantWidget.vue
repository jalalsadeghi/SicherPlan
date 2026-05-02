<script lang="ts" setup>
import type { AssistantLink } from '#/api/sicherplan/assistant';
import type { AssistantFloatingPosition } from './assistant-floating';

import { LOGIN_PATH } from '@vben/constants';
import { useAccessStore } from '@vben/stores';

import { computed, nextTick, onBeforeUnmount, onMounted, watch } from 'vue';
import { ref } from 'vue';

import { $t } from '#/locales';
import { router } from '#/router';
import { useAuthStore as useLegacyAuthStore } from '#/sicherplan-legacy/stores/auth';
import { useAssistantStore } from '#/store';

import AssistantLauncher from './AssistantLauncher.vue';
import AssistantPanel from './AssistantPanel.vue';
import {
  clampAssistantFloatingPosition,
  clearAssistantFloatingPosition,
  getAssistantViewportMetrics,
  persistAssistantFloatingHintDismissed,
  persistAssistantFloatingPosition,
  readAssistantFloatingHintDismissed,
  readAssistantFloatingPosition,
  resolveAssistantDefaultFloatingPosition,
  snapAssistantFloatingPosition,
} from './assistant-floating';
import {
  queryAssistantAvoidRects,
  readAssistantSafeAreaInsets,
  resolveAssistantAutoPlacement,
} from './assistant-placement';

defineOptions({ name: 'SicherPlanAssistantWidget' });

const accessStore = useAccessStore();
const legacyAuthStore = useLegacyAuthStore();
const assistantStore = useAssistantStore();
const panelRef = ref<InstanceType<typeof AssistantPanel> | null>(null);
const launcherRef = ref<InstanceType<typeof AssistantLauncher> | null>(null);
const floatingPosition = ref<AssistantFloatingPosition>(
  resolveAssistantDefaultFloatingPosition(getAssistantViewportMetrics()),
);
const showDragHint = ref(!readAssistantFloatingHintDismissed());
const showAutoMoveHint = ref(false);
const draggingLauncher = ref(false);
const dragOrigin = ref<AssistantFloatingPosition | null>(null);
let autoMoveHintTimeout: null | number = null;
let pendingAutoPlacementFrame = 0;
let avoidZoneResizeObserver: null | ResizeObserver = null;

const currentRoute = computed(() => router.currentRoute.value);
const isPublicRoute = computed(() => {
  const route = currentRoute.value;
  return route.path === LOGIN_PATH || route.meta?.ignoreAccess === true;
});
const hasSessionContext = computed(() =>
  Boolean(
    accessStore.accessToken
    || legacyAuthStore.effectiveAccessToken
    || legacyAuthStore.sessionUser
    || legacyAuthStore.sessionId,
  ),
);

const shouldCheckCapabilities = computed(() => !isPublicRoute.value && hasSessionContext.value);
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
const dragHintLabel = computed(() => $t('assistant.widget.dragHint'));
const autoMoveHintLabel = computed(() => $t('assistant.widget.autoMovedHint'));

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

const widgetDockSide = computed(() => floatingPosition.value.dockSide);
const widgetPinnedLeft = computed(() => widgetDockSide.value.endsWith('left'));
const widgetPanelBelow = computed(() => widgetDockSide.value.startsWith('top'));
const widgetStyle = computed(() => ({
  left: `${Math.round(floatingPosition.value.x)}px`,
  top: `${Math.round(floatingPosition.value.y)}px`,
}));

function resolveLauncherMetrics() {
  const element = launcherRef.value?.getElement?.();
  return {
    height: element?.offsetHeight ?? 0,
    width: element?.offsetWidth ?? 0,
  };
}

function syncFloatingPosition(options?: {
  autoPlace?: boolean;
  persist?: boolean;
  reset?: boolean;
  source?: 'system' | 'user';
}) {
  const viewport = getAssistantViewportMetrics();
  const launcherMetrics = resolveLauncherMetrics();
  let nextPosition = options?.reset
    ? resolveAssistantDefaultFloatingPosition(viewport, launcherMetrics)
    : readAssistantFloatingPosition()
      ?? floatingPosition.value
      ?? resolveAssistantDefaultFloatingPosition(viewport, launcherMetrics);
  nextPosition = options?.reset
    ? nextPosition
    : clampAssistantFloatingPosition(nextPosition, viewport, launcherMetrics);
  if (options?.source) {
    nextPosition = {
      ...nextPosition,
      lastMovedBy: options.source,
    };
  }
  if (options?.autoPlace) {
    const result = resolveAssistantAutoPlacement({
      avoidRects: queryAssistantAvoidRects(),
      launcherSize: launcherMetrics,
      position: nextPosition,
      safeAreaInsets: readAssistantSafeAreaInsets(),
      viewport,
    });
    nextPosition = result.position;
    if (result.autoMoved && nextPosition.lastMovedBy === 'system') {
      showTransientAutoMoveHint();
    }
  }
  floatingPosition.value = nextPosition;
  if (options?.persist) {
    persistAssistantFloatingPosition(nextPosition);
  }
}

function dismissDragHint() {
  if (!showDragHint.value) {
    return;
  }
  showDragHint.value = false;
  persistAssistantFloatingHintDismissed(true);
}

function resetFloatingPosition() {
  dismissDragHint();
  clearAssistantFloatingPosition();
  syncFloatingPosition({ autoPlace: true, persist: true, reset: true, source: 'system' });
}

function clearAutoMoveHintTimer() {
  if (autoMoveHintTimeout !== null && typeof window !== 'undefined') {
    window.clearTimeout(autoMoveHintTimeout);
  }
  autoMoveHintTimeout = null;
}

function showTransientAutoMoveHint() {
  if (typeof window === 'undefined') {
    return;
  }
  showAutoMoveHint.value = true;
  clearAutoMoveHintTimer();
  autoMoveHintTimeout = window.setTimeout(() => {
    showAutoMoveHint.value = false;
    autoMoveHintTimeout = null;
  }, 2600);
}

function handleLauncherDragStart() {
  dragOrigin.value = { ...floatingPosition.value };
  draggingLauncher.value = true;
  dismissDragHint();
  if (typeof document !== 'undefined') {
    document.body.style.userSelect = 'none';
  }
}

function handleLauncherDragMove(payload: { deltaX: number; deltaY: number }) {
  if (!dragOrigin.value) {
    dragOrigin.value = { ...floatingPosition.value };
  }
  const viewport = getAssistantViewportMetrics();
  const launcherMetrics = resolveLauncherMetrics();
  floatingPosition.value = clampAssistantFloatingPosition(
    {
      ...floatingPosition.value,
      dockSide: 'custom',
      lastMovedBy: 'user',
      userPinned: true,
      x: dragOrigin.value.x + payload.deltaX,
      y: dragOrigin.value.y + payload.deltaY,
    },
    viewport,
    launcherMetrics,
  );
}

function handleLauncherDragEnd() {
  const viewport = getAssistantViewportMetrics();
  const launcherMetrics = resolveLauncherMetrics();
  floatingPosition.value = snapAssistantFloatingPosition(
    {
      ...floatingPosition.value,
      dockSide: 'custom',
      userPinned: true,
    },
    viewport,
    launcherMetrics,
  );
  persistAssistantFloatingPosition(floatingPosition.value);
  draggingLauncher.value = false;
  dragOrigin.value = null;
  if (typeof document !== 'undefined') {
    document.body.style.userSelect = '';
  }
}

function handleLauncherKeyboardMove(payload: { dx: number; dy: number }) {
  dismissDragHint();
  const viewport = getAssistantViewportMetrics();
  const launcherMetrics = resolveLauncherMetrics();
  floatingPosition.value = snapAssistantFloatingPosition(
    {
      ...floatingPosition.value,
      dockSide: 'custom',
      lastMovedBy: 'user',
      userPinned: true,
      x: floatingPosition.value.x + payload.dx,
      y: floatingPosition.value.y + payload.dy,
    },
    viewport,
    launcherMetrics,
  );
  persistAssistantFloatingPosition(floatingPosition.value);
}

function disconnectAvoidZoneObserver() {
  avoidZoneResizeObserver?.disconnect();
  avoidZoneResizeObserver = null;
}

function reconnectAvoidZoneObserver() {
  disconnectAvoidZoneObserver();
  if (typeof ResizeObserver === 'undefined' || typeof document === 'undefined') {
    return;
  }
  const nodes = document.querySelectorAll<HTMLElement>('[data-assistant-avoid], .sp-assistant-avoid');
  if (!nodes.length) {
    return;
  }
  avoidZoneResizeObserver = new ResizeObserver(() => {
    scheduleAutoPlacement();
  });
  nodes.forEach((node) => avoidZoneResizeObserver?.observe(node));
}

function scheduleAutoPlacement() {
  if (draggingLauncher.value || typeof window === 'undefined') {
    return;
  }
  if (pendingAutoPlacementFrame) {
    window.cancelAnimationFrame(pendingAutoPlacementFrame);
  }
  pendingAutoPlacementFrame = window.requestAnimationFrame(async () => {
    pendingAutoPlacementFrame = 0;
    await nextTick();
    syncFloatingPosition({ autoPlace: true, persist: true });
    reconnectAvoidZoneObserver();
  });
}

async function ensureCapabilities() {
  if (isPublicRoute.value) {
    return;
  }
  if (assistantStore.loadingCapabilities) {
    return;
  }
  try {
    legacyAuthStore.syncFromPrimarySession();
    if (!accessStore.accessToken && !legacyAuthStore.effectiveAccessToken) {
      await legacyAuthStore.ensureSessionReady().catch(() => null);
      legacyAuthStore.syncFromPrimarySession();
    }
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
  dismissDragHint();
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
  () => [
    accessStore.accessToken,
    legacyAuthStore.effectiveAccessToken,
    legacyAuthStore.sessionId,
    legacyAuthStore.sessionUser?.id ?? '',
    legacyAuthStore.isSessionResolving,
  ] as const,
  async () => {
    if (isPublicRoute.value) {
      return;
    }
    if (!hasSessionContext.value && !legacyAuthStore.isSessionResolving) {
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
  await nextTick();
  syncFloatingPosition({ autoPlace: true });
  reconnectAvoidZoneObserver();
  if (typeof window !== 'undefined') {
    window.addEventListener('resize', handleViewportResize);
  }
  if (!shouldCheckCapabilities.value) {
    return;
  }
  await ensureCapabilities();
  if (assistantStore.isOpen) {
    await assistantStore.restorePersistedConversation().catch(() => undefined);
  }
});

onBeforeUnmount(() => {
  clearAutoMoveHintTimer();
  disconnectAvoidZoneObserver();
  if (typeof window !== 'undefined') {
    window.removeEventListener('resize', handleViewportResize);
    if (pendingAutoPlacementFrame) {
      window.cancelAnimationFrame(pendingAutoPlacementFrame);
      pendingAutoPlacementFrame = 0;
    }
  }
  if (typeof document !== 'undefined') {
    document.body.style.userSelect = '';
  }
});

function handleViewportResize() {
  syncFloatingPosition({ autoPlace: true, persist: true });
}

watch(
  shouldShowLauncher,
  async (visible) => {
    if (!visible) {
      return;
    }
    await nextTick();
    syncFloatingPosition({ autoPlace: true, persist: true });
    reconnectAvoidZoneObserver();
  },
);

watch(
  () => currentRoute.value.fullPath,
  async () => {
    await nextTick();
    scheduleAutoPlacement();
  },
);

watch(panelVisible, async () => {
  await nextTick();
  scheduleAutoPlacement();
});
</script>

<template>
  <div
    v-if="shouldShowLauncher"
    class="sp-assistant-widget"
    :class="{
      'sp-assistant-widget--dragging': draggingLauncher,
      'sp-assistant-widget--panel-below': widgetPanelBelow,
      'sp-assistant-widget--panel-left': widgetPinnedLeft,
      'sp-assistant-widget--panel-right': !widgetPinnedLeft,
    }"
    :data-dock-side="widgetDockSide"
    :style="widgetStyle"
    data-testid="assistant-widget"
  >
    <Transition name="sp-assistant-panel">
      <div
        v-if="panelVisible"
        class="sp-assistant-widget__panel-shell"
        :class="{
          'sp-assistant-widget__panel-shell--below': widgetPanelBelow,
          'sp-assistant-widget__panel-shell--left': widgetPinnedLeft,
          'sp-assistant-widget__panel-shell--right': !widgetPinnedLeft,
        }"
        data-testid="assistant-panel-shell"
      >
        <AssistantPanel
          ref="panelRef"
          :assistant-label="$t('assistant.widget.assistantLabel')"
          :close-label="$t('assistant.widget.closeLabel')"
          :confidence-label="$t('assistant.widget.confidence')"
          :description="description"
          :degraded-warning="$t('assistant.widget.degradedWarning')"
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
          :processing-label="$t('assistant.widget.processing')"
          :reset-position-label="$t('assistant.widget.resetPosition')"
          :sources-title="$t('assistant.widget.sourcesTitle')"
          :sending-message="assistantStore.sendingMessage"
          :severity-labels="severityLabels"
          :submit-label="$t('assistant.widget.send')"
          :sending-label="$t('assistant.widget.sending')"
          :title="title"
          :user-label="$t('assistant.widget.userLabel')"
          @close="closePanel"
          @open-link="openLink"
          @reset-position="resetFloatingPosition"
          @send="submitMessage"
          @submit-feedback="submitFeedback"
          @update:draft-input="updateDraft"
        />
      </div>
    </Transition>

    <AssistantLauncher
      ref="launcherRef"
      :disabled="assistantStore.loadingCapabilities"
      :drag-hint="dragHintLabel"
      :dragging="draggingLauncher"
      :loading="assistantStore.loadingCapabilities"
      :open="assistantStore.isOpen"
      :show-hint="showDragHint && !panelVisible"
      :title="launcherLabel"
      @dismiss-hint="dismissDragHint"
      @drag-end="handleLauncherDragEnd"
      @drag-move="handleLauncherDragMove"
      @drag-start="handleLauncherDragStart"
      @move-keyboard="handleLauncherKeyboardMove"
      @toggle="togglePanel"
    />
    <div
      v-if="showAutoMoveHint"
      class="sp-assistant-widget__auto-move-hint"
      data-testid="assistant-auto-move-hint"
      role="status"
    >
      {{ autoMoveHintLabel }}
    </div>
  </div>
</template>

<style scoped>
:global(:root) {
  --sp-safe-area-top: env(safe-area-inset-top, 0px);
  --sp-safe-area-right: env(safe-area-inset-right, 0px);
  --sp-safe-area-bottom: env(safe-area-inset-bottom, 0px);
  --sp-safe-area-left: env(safe-area-inset-left, 0px);
}

.sp-assistant-widget {
  position: fixed;
  z-index: 1050;
  width: max-content;
  max-width: calc(100vw - 1rem - var(--sp-safe-area-left) - var(--sp-safe-area-right));
  pointer-events: none;
  transform: translate3d(0, 0, 0);
}

.sp-assistant-widget > * {
  pointer-events: auto;
}

.sp-assistant-widget--dragging {
  z-index: 1060;
}

.sp-assistant-widget__panel-shell {
  position: absolute;
  width: min(28rem, calc(100vw - 1rem - var(--sp-safe-area-left) - var(--sp-safe-area-right)));
  max-width: min(28rem, calc(100vw - 1rem - var(--sp-safe-area-left) - var(--sp-safe-area-right)));
}

.sp-assistant-widget__panel-shell--left {
  left: 0;
}

.sp-assistant-widget__panel-shell--right {
  right: 0;
}

.sp-assistant-widget__panel-shell:not(.sp-assistant-widget__panel-shell--below) {
  bottom: calc(100% + 0.85rem);
}

.sp-assistant-widget__panel-shell--below {
  top: calc(100% + 0.85rem);
}

.sp-assistant-widget__auto-move-hint {
  position: absolute;
  right: 0;
  top: calc(100% + 0.5rem);
  max-width: 12rem;
  padding: 0.45rem 0.65rem;
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 0.75rem;
  background: var(--sp-color-surface-panel);
  color: var(--sp-color-text-primary);
  box-shadow: 0 12px 28px rgb(14 31 34 / 0.16);
  font-size: 0.75rem;
  font-weight: 600;
  line-height: 1.35;
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
    max-width: calc(100vw - 0.5rem - var(--sp-safe-area-left) - var(--sp-safe-area-right));
  }

  .sp-assistant-widget__panel-shell {
    width: min(28rem, calc(100vw - 0.5rem - var(--sp-safe-area-left) - var(--sp-safe-area-right)));
    max-width: min(28rem, calc(100vw - 0.5rem - var(--sp-safe-area-left) - var(--sp-safe-area-right)));
  }

  .sp-assistant-widget__auto-move-hint {
    max-width: 10rem;
    font-size: 0.72rem;
  }
}
</style>
