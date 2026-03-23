<script lang="ts" setup>
import { computed } from 'vue';
import { useRoute } from 'vue-router';

import { $t } from '#/locales';
import EmptyState from '#/components/sicherplan/empty-state.vue';
import ModuleWorkspacePage from '#/components/sicherplan/module-workspace-page.vue';
import SectionBlock from '#/components/sicherplan/section-block.vue';

import { moduleRegistry } from './module-registry';

const route = useRoute();

const config = computed(() => {
  const moduleKey = route.meta?.moduleKey;
  if (typeof moduleKey !== 'string') {
    return null;
  }
  return moduleRegistry[moduleKey] ?? null;
});

const badges = computed(() =>
  config.value
    ? config.value.badges.map((badge) => ({
        key: badge.key,
        tone: badge.tone,
      }))
    : [],
);
</script>

<template>
  <EmptyState
    v-if="!config"
    :description="$t('sicherplan.ui.moduleMissing.description')"
    :title="$t('sicherplan.ui.moduleMissing.title')"
  />

  <ModuleWorkspacePage
    v-else
    :badges="badges"
    :description="$t(config.descriptionKey)"
    :eyebrow="$t('sicherplan.ui.moduleEyebrow')"
    :title="$t(config.titleKey)"
  >
    <template #workspace>
      <SectionBlock
        :description="$t(config.workspaceDescriptionKey)"
        :title="$t('sicherplan.ui.workspaceTitle')"
      >
        <div class="sp-module-workspace">
          <component :is="config.component" v-bind="{ embedded: true }" />
        </div>
      </SectionBlock>
    </template>
  </ModuleWorkspacePage>
</template>

<style scoped>
.sp-module-workspace {
  display: grid;
  gap: 1rem;
}
</style>
