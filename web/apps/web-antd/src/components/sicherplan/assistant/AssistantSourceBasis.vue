<script lang="ts" setup>
import type { AssistantSourceBasisItem } from '#/api/sicherplan/assistant';

import { computed, ref } from 'vue';

defineOptions({ name: 'AssistantSourceBasis' });

const props = withDefaults(defineProps<{
  initiallyExpanded?: boolean;
  items: AssistantSourceBasisItem[];
  messageId: string;
  title: string;
}>(), {
  initiallyExpanded: false,
});

const expanded = ref(props.initiallyExpanded);

const panelId = computed(() => `assistant-source-panel-${props.messageId}`);

function sourceBasisKey(item: AssistantSourceBasisItem) {
  return [
    item.source_type,
    item.source_name || '',
    item.page_id || '',
    item.title || '',
  ].join(':');
}

function sourceBasisLabel(item: AssistantSourceBasisItem) {
  const head = item.title || item.source_name || item.module_key || item.source_type;
  const tail = item.source_name && item.source_name !== head ? item.source_name : item.module_key;
  if (tail && tail !== head) {
    return `${head} — ${tail}`;
  }
  return head;
}

function toggleExpanded() {
  expanded.value = !expanded.value;
}
</script>

<template>
  <section
    v-if="items.length"
    class="sp-assistant-source-basis"
    data-testid="assistant-source-basis"
  >
    <button
      :aria-controls="panelId"
      :aria-expanded="expanded ? 'true' : 'false'"
      class="sp-assistant-source-basis__toggle"
      type="button"
      @click="toggleExpanded"
    >
      <span class="sp-assistant-source-basis__chevron" aria-hidden="true">
        {{ expanded ? '▾' : '▸' }}
      </span>
      <span>{{ title }}</span>
    </button>

    <div
      v-if="expanded"
      :id="panelId"
      class="sp-assistant-source-basis__panel"
      data-testid="assistant-source-basis-panel"
    >
      <ul class="sp-assistant-source-basis__list">
        <li
          v-for="item in items"
          :key="sourceBasisKey(item)"
          class="sp-assistant-source-basis__item"
        >
          <strong :title="item.page_id || undefined">{{ sourceBasisLabel(item) }}</strong>
          <span v-if="item.evidence"> - {{ item.evidence }}</span>
        </li>
      </ul>
    </div>
  </section>
</template>

<style scoped>
.sp-assistant-source-basis {
  display: grid;
  gap: 0.45rem;
}

.sp-assistant-source-basis__toggle {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  width: fit-content;
  padding: 0;
  border: none;
  background: transparent;
  color: var(--sp-color-text-secondary);
  font-size: 0.75rem;
  font-weight: 700;
  cursor: pointer;
}

.sp-assistant-source-basis__chevron {
  width: 0.7rem;
  text-align: center;
}

.sp-assistant-source-basis__panel {
  display: grid;
}

.sp-assistant-source-basis__list {
  display: grid;
  gap: 0.35rem;
  margin: 0;
  padding-left: 1.1rem;
  color: var(--sp-color-text-secondary);
  font-size: 0.83rem;
  line-height: 1.45;
}

.sp-assistant-source-basis__item {
  overflow-wrap: anywhere;
}
</style>
