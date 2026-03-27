<template>
  <nav
    class="internal-card-tabs"
    :aria-label="ariaLabel"
    role="tablist"
    :data-testid="testId"
    @keydown="onKeydown"
  >
    <button
      v-for="tab in tabs"
      :id="tabButtonId(tab.id)"
      :key="tab.id"
      type="button"
      role="tab"
      class="internal-card-tab"
      :class="{ active: tab.id === modelValue }"
      :aria-selected="String(tab.id === modelValue)"
      :aria-controls="tabPanelId(tab.id)"
      :tabindex="tab.id === modelValue ? 0 : -1"
      :data-tab-id="tab.id"
      @click="selectTab(tab.id)"
    >
      {{ tab.label }}
    </button>
  </nav>
</template>

<script setup>
const props = defineProps({
  ariaLabel: {
    type: String,
    default: "Detail sections",
  },
  modelValue: {
    type: String,
    required: true,
  },
  panelIdPrefix: {
    type: String,
    default: "internal-card-tab-panel",
  },
  tabIdPrefix: {
    type: String,
    default: "internal-card-tab",
  },
  tabs: {
    type: Array,
    required: true,
  },
  testId: {
    type: String,
    default: "",
  },
});

const emit = defineEmits(["update:modelValue"]);

function selectTab(tabId) {
  emit("update:modelValue", tabId);
}

function tabButtonId(tabId) {
  return `${props.tabIdPrefix}-${tabId}`;
}

function tabPanelId(tabId) {
  return `${props.panelIdPrefix}-${tabId}`;
}

function focusTab(tabId) {
  const button = document.getElementById(tabButtonId(tabId));
  button?.focus();
}

function onKeydown(event) {
  const tabCount = props.tabs.length;
  if (!tabCount) {
    return;
  }

  const currentIndex = props.tabs.findIndex((tab) => tab.id === props.modelValue);
  const safeIndex = currentIndex >= 0 ? currentIndex : 0;

  if (event.key === "ArrowRight" || event.key === "ArrowDown") {
    event.preventDefault();
    const nextTab = props.tabs[(safeIndex + 1) % tabCount];
    selectTab(nextTab.id);
    focusTab(nextTab.id);
    return;
  }

  if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
    event.preventDefault();
    const previousTab = props.tabs[(safeIndex - 1 + tabCount) % tabCount];
    selectTab(previousTab.id);
    focusTab(previousTab.id);
    return;
  }

  if (event.key === "Home") {
    event.preventDefault();
    const firstTab = props.tabs[0];
    selectTab(firstTab.id);
    focusTab(firstTab.id);
    return;
  }

  if (event.key === "End") {
    event.preventDefault();
    const lastTab = props.tabs[tabCount - 1];
    selectTab(lastTab.id);
    focusTab(lastTab.id);
  }
}
</script>

<style scoped>
.internal-card-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.internal-card-tab {
  border: 1px solid var(--sp-color-border-soft);
  background: var(--sp-color-surface-page);
  color: var(--sp-color-text-secondary);
  border-radius: 999px;
  padding: 0.6rem 1rem;
  font: inherit;
  cursor: pointer;
  transition:
    border-color 0.18s ease,
    color 0.18s ease,
    background-color 0.18s ease,
    box-shadow 0.18s ease;
  min-width: 0;
}

.internal-card-tab.active {
  border-color: var(--sp-color-primary);
  color: var(--sp-color-primary-strong);
  background: color-mix(in srgb, var(--sp-color-primary-muted) 70%, white);
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--sp-color-primary) 28%, transparent);
}

.internal-card-tab:focus-visible {
  outline: none;
  border-color: var(--sp-color-primary);
  box-shadow: 0 0 0 3px rgb(40 170 170 / 14%);
}
</style>
