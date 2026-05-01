<script lang="ts" setup>
import { ref } from 'vue';

import ModuleWorkspacePage from '#/components/sicherplan/module-workspace-page.vue';
import SectionBlock from '#/components/sicherplan/section-block.vue';
import { $t } from '#/locales';

import CustomerOrderWorkspacePanel from './customer-order-workspace-panel.vue';

const panelRef = ref<InstanceType<typeof CustomerOrderWorkspacePanel> | null>(null);

defineExpose({
  get wizardState() {
    return panelRef.value?.wizardState;
  },
});
</script>

<template>
  <ModuleWorkspacePage
    :description="$t('sicherplan.customerPlansWizard.description')"
    :eyebrow="$t('sicherplan.admin.customers')"
    :show-intro="false"
    :title="$t('sicherplan.customerPlansWizard.title')"
  >
    <template #workspace>
      <SectionBlock :show-header="false" title="">
        <CustomerOrderWorkspacePanel ref="panelRef" />
      </SectionBlock>
    </template>
  </ModuleWorkspacePage>
</template>
