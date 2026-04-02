<template>
  <div
    class="sp-loading-overlay"
    :aria-busy="visible"
    :data-busy="visible ? 'true' : 'false'"
    :data-testid="busyTestid"
  >
    <div class="sp-loading-overlay__content" :class="{ 'sp-loading-overlay__content--busy': visible }">
      <slot />
    </div>

    <transition name="sp-loading-overlay-fade">
      <div
        v-if="visible"
        class="sp-loading-overlay__layer"
        role="status"
        :aria-label="ariaLabel || text || undefined"
        aria-live="polite"
      >
        <div class="sp-loading-overlay__panel">
          <Spinner :spinning="visible" class="sp-loading-overlay__spinner" />
          <span v-if="text" class="sp-loading-overlay__text">{{ text }}</span>
        </div>
      </div>
    </transition>
  </div>
</template>

<script lang="ts" setup>
import { Spinner } from "@vben/common-ui";
import { onBeforeUnmount, ref, watch } from "vue";

const props = withDefaults(
  defineProps<{
    ariaLabel?: string;
    busy?: boolean;
    busyTestid?: string;
    minVisibleMs?: number;
    text?: string;
  }>(),
  {
    ariaLabel: "",
    busy: false,
    busyTestid: "sicherplan-loading-overlay",
    minVisibleMs: 250,
    text: "",
  },
);

const visible = ref(Boolean(props.busy));
let hideTimer: ReturnType<typeof setTimeout> | null = null;
let shownAt = props.busy ? Date.now() : 0;

function clearHideTimer() {
  if (hideTimer) {
    clearTimeout(hideTimer);
    hideTimer = null;
  }
}

watch(
  () => props.busy,
  (busy) => {
    clearHideTimer();
    if (busy) {
      shownAt = Date.now();
      visible.value = true;
      return;
    }
    const elapsed = Date.now() - shownAt;
    const remaining = Math.max(props.minVisibleMs - elapsed, 0);
    if (remaining === 0) {
      visible.value = false;
      return;
    }
    hideTimer = setTimeout(() => {
      visible.value = false;
      hideTimer = null;
    }, remaining);
  },
  { immediate: true },
);

onBeforeUnmount(() => {
  clearHideTimer();
});
</script>

<style scoped>
.sp-loading-overlay {
  position: relative;
}

.sp-loading-overlay__content {
  transition: opacity 0.18s ease;
}

.sp-loading-overlay__content--busy {
  opacity: 0.58;
}

.sp-loading-overlay__layer {
  position: absolute;
  inset: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: inherit;
  background:
    linear-gradient(180deg, rgb(255 255 255 / 58%), rgb(255 255 255 / 68%));
  backdrop-filter: blur(2px);
  pointer-events: all;
}

.sp-loading-overlay__panel {
  display: inline-flex;
  align-items: center;
  gap: 0.7rem;
  max-width: min(18rem, calc(100% - 2rem));
  padding: 0.85rem 1rem;
  border: 1px solid rgb(35 56 78 / 10%);
  border-radius: 999px;
  background: rgb(255 255 255 / 92%);
  box-shadow: 0 18px 40px rgb(15 23 42 / 12%);
  color: var(--sp-color-text);
}

.sp-loading-overlay__spinner {
  min-height: 0;
}

.sp-loading-overlay__text {
  font-size: 0.95rem;
  font-weight: 600;
  line-height: 1.2;
}

.sp-loading-overlay-fade-enter-active,
.sp-loading-overlay-fade-leave-active {
  transition: opacity 0.18s ease;
}

.sp-loading-overlay-fade-enter-from,
.sp-loading-overlay-fade-leave-to {
  opacity: 0;
}

@media (prefers-color-scheme: dark) {
  .sp-loading-overlay__layer {
    background:
      linear-gradient(180deg, rgb(11 18 32 / 42%), rgb(11 18 32 / 52%));
  }

  .sp-loading-overlay__panel {
    border-color: rgb(148 163 184 / 18%);
    background: rgb(16 23 37 / 90%);
    box-shadow: 0 18px 40px rgb(2 6 23 / 28%);
  }
}
</style>
