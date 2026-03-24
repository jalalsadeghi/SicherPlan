<script lang="ts" setup>
import { computed } from 'vue';
import { useRoute } from 'vue-router';

import { $t } from '#/locales';
import { useAuthStore } from '#/sicherplan-legacy/stores/auth';
import EmptyState from '#/components/sicherplan/empty-state.vue';
import ModuleWorkspacePage from '#/components/sicherplan/module-workspace-page.vue';
import SectionBlock from '#/components/sicherplan/section-block.vue';
import ForbiddenView from '#/views/_core/fallback/forbidden.vue';

import { moduleRegistry } from './module-registry';

const route = useRoute();
const authStore = useAuthStore();

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

const showPageIntro = computed(() => config.value?.showPageIntro !== false);
const isModuleAllowedForRole = computed(() => {
  const allowedRoles = config.value?.allowedRoles;
  if (!allowedRoles?.length) {
    return true;
  }
  return allowedRoles.includes(authStore.effectiveRole);
});
const showWorkspaceSectionHeader = computed(
  () =>
    config.value?.showWorkspaceSectionHeader !== false &&
    !config.value?.hideWorkspaceSectionHeaderForRoles?.includes(authStore.effectiveRole),
);
</script>

<template>
  <EmptyState
    v-if="!config"
    :description="$t('sicherplan.ui.moduleMissing.description')"
    :title="$t('sicherplan.ui.moduleMissing.title')"
  />

  <ForbiddenView v-else-if="!isModuleAllowedForRole" />

  <ModuleWorkspacePage
    v-else
    :badges="badges"
    :show-intro="showPageIntro"
    :description="showPageIntro ? $t(config.descriptionKey) : ''"
    :eyebrow="showPageIntro ? $t('sicherplan.ui.moduleEyebrow') : ''"
    :title="showPageIntro ? $t(config.titleKey) : ''"
  >
    <template #workspace>
      <SectionBlock
        :description="showWorkspaceSectionHeader ? $t(config.workspaceDescriptionKey) : undefined"
        :show-header="showWorkspaceSectionHeader"
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
