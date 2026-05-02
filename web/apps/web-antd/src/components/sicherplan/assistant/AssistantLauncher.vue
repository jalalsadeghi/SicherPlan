<script lang="ts" setup>
import { ref } from 'vue';

defineOptions({ name: 'AssistantLauncher' });

const props = defineProps<{
  disabled?: boolean;
  dragHint?: string;
  dragging?: boolean;
  loading?: boolean;
  open?: boolean;
  showHint?: boolean;
  title: string;
}>();

const emit = defineEmits<{
  (event: 'dismiss-hint'): void;
  (
    event: 'drag-end',
    payload: {
      clientX: number;
      clientY: number;
      deltaX: number;
      deltaY: number;
    },
  ): void;
  (
    event: 'drag-move',
    payload: {
      clientX: number;
      clientY: number;
      deltaX: number;
      deltaY: number;
    },
  ): void;
  (
    event: 'drag-start',
    payload: {
      clientX: number;
      clientY: number;
      originHeight: number;
      originWidth: number;
    },
  ): void;
  (event: 'move-keyboard', payload: { dx: number; dy: number }): void;
  (event: 'toggle'): void;
}>();

const buttonRef = ref<HTMLButtonElement | null>(null);
const suppressClick = ref(false);
const activePointerId = ref<number | null>(null);
const dragStarted = ref(false);
const pointerOrigin = ref({ x: 0, y: 0 });

const DRAG_THRESHOLD_PX = 6;

function resetPointerState() {
  activePointerId.value = null;
  dragStarted.value = false;
  pointerOrigin.value = { x: 0, y: 0 };
}

function resolveKeyboardDelta(event: KeyboardEvent) {
  const distance = event.shiftKey ? 48 : 16;
  switch (event.key) {
    case 'ArrowDown': {
      return { dx: 0, dy: distance };
    }
    case 'ArrowLeft': {
      return { dx: -distance, dy: 0 };
    }
    case 'ArrowRight': {
      return { dx: distance, dy: 0 };
    }
    case 'ArrowUp': {
      return { dx: 0, dy: -distance };
    }
    default: {
      return null;
    }
  }
}

function handleClick(event: MouseEvent) {
  if (suppressClick.value) {
    event.preventDefault();
    event.stopPropagation();
    suppressClick.value = false;
    return;
  }
  emit('dismiss-hint');
  emit('toggle');
}

function handleKeydown(event: KeyboardEvent) {
  const delta = resolveKeyboardDelta(event);
  if (!delta || props.disabled) {
    return;
  }
  event.preventDefault();
  emit('dismiss-hint');
  emit('move-keyboard', delta);
}

function handlePointerDown(event: PointerEvent) {
  if (props.disabled) {
    return;
  }
  activePointerId.value = event.pointerId;
  pointerOrigin.value = { x: event.clientX, y: event.clientY };
  buttonRef.value?.setPointerCapture?.(event.pointerId);
}

function handlePointerMove(event: PointerEvent) {
  if (activePointerId.value !== event.pointerId || props.disabled) {
    return;
  }
  const deltaX = event.clientX - pointerOrigin.value.x;
  const deltaY = event.clientY - pointerOrigin.value.y;
  const movedEnough =
    Math.abs(deltaX) >= DRAG_THRESHOLD_PX || Math.abs(deltaY) >= DRAG_THRESHOLD_PX;

  if (!dragStarted.value && movedEnough) {
    dragStarted.value = true;
    suppressClick.value = true;
    emit('dismiss-hint');
    emit('drag-start', {
      clientX: event.clientX,
      clientY: event.clientY,
      originHeight: buttonRef.value?.offsetHeight ?? 0,
      originWidth: buttonRef.value?.offsetWidth ?? 0,
    });
  }
  if (!dragStarted.value) {
    return;
  }
  emit('drag-move', {
    clientX: event.clientX,
    clientY: event.clientY,
    deltaX,
    deltaY,
  });
}

function finishPointerInteraction(event: PointerEvent) {
  if (activePointerId.value !== event.pointerId) {
    return;
  }
  buttonRef.value?.releasePointerCapture?.(event.pointerId);
  if (dragStarted.value) {
    emit('drag-end', {
      clientX: event.clientX,
      clientY: event.clientY,
      deltaX: event.clientX - pointerOrigin.value.x,
      deltaY: event.clientY - pointerOrigin.value.y,
    });
  }
  resetPointerState();
}

defineExpose({
  getElement: () => buttonRef.value,
});
</script>

<template>
  <div class="sp-assistant-launcher-shell">
    <button
      ref="buttonRef"
      :aria-label="dragHint ? `${title}. ${dragHint}` : title"
      class="sp-assistant-launcher"
      :class="{
        'sp-assistant-launcher--disabled': disabled,
        'sp-assistant-launcher--dragging': dragging,
        'sp-assistant-launcher--open': open,
      }"
      :disabled="disabled"
      :title="dragHint ? `${title} — ${dragHint}` : title"
      type="button"
      @click="handleClick"
      @keydown="handleKeydown"
      @pointercancel="finishPointerInteraction"
      @pointerdown="handlePointerDown"
      @pointermove="handlePointerMove"
      @pointerup="finishPointerInteraction"
    >
      <span class="sp-assistant-launcher__handle" aria-hidden="true">
        <IconifyIcon class="sp-assistant-launcher__handle-icon" icon="lucide:grip-horizontal" />
      </span>
      <IconifyIcon class="sp-assistant-launcher__icon" :icon="loading ? 'lucide:loader-circle' : 'lucide:messages-square'" />
      <span class="sp-assistant-launcher__label">{{ title }}</span>
    </button>
    <div
      v-if="showHint"
      class="sp-assistant-launcher__hint"
      data-testid="assistant-launcher-drag-hint"
      role="status"
    >
      {{ dragHint }}
    </div>
  </div>
</template>

<style scoped>
.sp-assistant-launcher-shell {
  position: relative;
  display: inline-flex;
}

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
  cursor: grab;
  user-select: none;
  -webkit-user-select: none;
  touch-action: none;
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

.sp-assistant-launcher--dragging {
  cursor: grabbing;
  transform: none;
}

.sp-assistant-launcher__handle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.15rem;
  height: 1.15rem;
  border-radius: 999px;
  background: rgb(255 255 255 / 0.16);
  color: inherit;
  flex: 0 0 auto;
}

.sp-assistant-launcher__handle-icon {
  font-size: 0.82rem;
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

.sp-assistant-launcher__hint {
  position: absolute;
  right: 0;
  bottom: calc(100% + 0.5rem);
  max-width: 11rem;
  padding: 0.4rem 0.6rem;
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 0.7rem;
  background: var(--sp-color-surface-panel);
  color: var(--sp-color-text-primary);
  box-shadow: 0 12px 30px rgb(14 31 34 / 0.18);
  font-size: 0.76rem;
  font-weight: 600;
  line-height: 1.35;
  white-space: normal;
}

@media (max-width: 640px) {
  .sp-assistant-launcher {
    min-height: 2.85rem;
    padding: 0.75rem 0.9rem;
  }

  .sp-assistant-launcher__label {
    font-size: 0.9rem;
  }

  .sp-assistant-launcher__hint {
    max-width: 9rem;
    font-size: 0.72rem;
  }
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
