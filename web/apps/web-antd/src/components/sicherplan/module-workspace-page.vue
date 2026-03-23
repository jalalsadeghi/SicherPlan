<script lang="ts" setup>
import { Page } from '@vben/common-ui';

import PageIntro from './page-intro.vue';
import SplitViewLayout from './split-view-layout.vue';
import StatsRow from './stats-row.vue';

interface StatItem {
  hint?: string;
  label: string;
  value: string;
}

withDefaults(
  defineProps<{
    badges?: Array<{ key: string; tone?: 'default' | 'success' | 'warning' }>;
    description: string;
    eyebrow?: string;
    stats?: StatItem[];
    title: string;
  }>(),
  {},
);
</script>

<template>
  <Page content-class="sp-module-page">
    <PageIntro
      :badges="badges"
      :description="description"
      :eyebrow="eyebrow"
      :title="title"
    >
      <template v-if="$slots.actions" #actions>
        <slot name="actions" />
      </template>
    </PageIntro>

    <StatsRow v-if="stats?.length" :stats="stats" />

    <SplitViewLayout v-if="$slots.main || $slots.aside">
      <template #main>
        <slot name="main" />
      </template>
      <template #aside>
        <slot name="aside" />
      </template>
    </SplitViewLayout>

    <slot
      v-if="$slots.workspace"
      name="workspace"
    />
  </Page>
</template>

<style scoped>
.sp-module-page {
  --sp-page-gap: 1.25rem;
  --sp-card-gap: 1rem;
  --sp-card-padding: 1.25rem;
  display: grid;
  gap: var(--sp-page-gap);
  min-width: 0;
  padding: var(--sp-page-gap);
  background:
    radial-gradient(circle at top left, rgb(40 170 170 / 0.09), transparent 28%),
    var(--sp-page-background);
}

.sp-module-page > * {
  min-width: 0;
}

.sp-module-page :deep(.ant-card) {
  min-width: 0;
  border-radius: 1.25rem;
}

.sp-module-page :deep(.ant-card-body) {
  min-width: 0;
  display: grid;
  gap: var(--sp-card-gap);
  box-sizing: border-box;
  padding: var(--sp-card-padding);
}

.sp-module-page :deep(.ant-card-body > .ant-space),
.sp-module-page :deep(.ant-card-body > .ant-space-wrap) {
  row-gap: 0.75rem;
  max-width: 100%;
}

.sp-module-page :deep(.ant-card-body > .ant-table-wrapper),
.sp-module-page :deep(.ant-card-body > .ant-alert),
.sp-module-page :deep(.ant-card-body > .ant-form),
.sp-module-page :deep(.ant-card-body > .ant-space),
.sp-module-page :deep(.ant-card-body > .ant-space-wrap),
.sp-module-page :deep(.ant-card-body > [class^='sp-']),
.sp-module-page :deep(.ant-card-body > [class*=' sp-']) {
  margin: 0;
  min-width: 0;
}

.sp-module-page :deep(.ant-form),
.sp-module-page :deep(.ant-form-item),
.sp-module-page :deep(.ant-input),
.sp-module-page :deep(.ant-input-affix-wrapper),
.sp-module-page :deep(.ant-input-number),
.sp-module-page :deep(.ant-input-number-group-wrapper),
.sp-module-page :deep(.ant-picker),
.sp-module-page :deep(.ant-select),
.sp-module-page :deep(textarea) {
  max-width: 100%;
  min-width: 0;
  box-sizing: border-box;
}

@media (max-width: 960px) {
  .sp-module-page {
    --sp-page-gap: 1rem;
    --sp-card-padding: 1rem;
  }
}
</style>
