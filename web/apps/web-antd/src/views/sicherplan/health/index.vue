<script lang="ts" setup>
import { computed, onMounted, ref } from 'vue';

import { Button, Card, Descriptions, Space, Tag, message } from 'ant-design-vue';

import { $t } from '#/locales';
import ModuleWorkspacePage from '#/components/sicherplan/module-workspace-page.vue';
import SectionBlock from '#/components/sicherplan/section-block.vue';
import SectionHeader from '#/components/sicherplan/section-header.vue';

interface LivePayload {
  env?: string;
  service?: string;
  status?: string;
}

interface ReadyPayload {
  checks?: Record<string, { reason?: string; status?: string }>;
  service?: string;
  status?: string;
}

interface VersionPayload {
  env?: string;
  name?: string;
  version?: string;
}

const loading = ref(false);
const live = ref<LivePayload | null>(null);
const ready = ref<ReadyPayload | null>(null);
const version = ref<VersionPayload | null>(null);

function getHealthBaseUrl() {
  const apiBase = import.meta.env.VITE_GLOB_API_URL || '/api';
  return apiBase.endsWith('/api') ? apiBase.slice(0, -4) || '/' : apiBase;
}

async function readHealth<T>(path: string): Promise<T> {
  const response = await fetch(`${getHealthBaseUrl()}${path}`);
  if (!response.ok) {
    throw new Error(`HTTP_${response.status}`);
  }
  return (await response.json()) as T;
}

async function loadHealth() {
  loading.value = true;
  try {
    const [livePayload, readyPayload, versionPayload] = await Promise.all([
      readHealth<LivePayload>('/health/live'),
      readHealth<ReadyPayload>('/health/ready'),
      readHealth<VersionPayload>('/health/version'),
    ]);
    live.value = livePayload;
    ready.value = readyPayload;
    version.value = versionPayload;
  } catch (error) {
    message.error(error instanceof Error ? error.message : $t('sicherplan.health.loadFailed'));
  } finally {
    loading.value = false;
  }
}

function statusColor(status?: string) {
  switch (status) {
    case 'configured':
    case 'live':
    case 'ok':
    case 'ready': {
      return 'success';
    }
    case 'error':
    case 'not_ready': {
      return 'error';
    }
    default: {
      return 'default';
    }
  }
}

const stats = computed(() => [
  { label: $t('sicherplan.health.live'), value: live.value?.status ?? $t('sicherplan.health.unknown') },
  { label: $t('sicherplan.health.ready'), value: ready.value?.status ?? $t('sicherplan.health.unknown') },
  { label: $t('sicherplan.health.version'), value: version.value?.version ?? $t('sicherplan.health.unknown') },
]);

const checkItems = computed(() => Object.entries(ready.value?.checks ?? {}));

onMounted(() => {
  void loadHealth();
});
</script>

<template>
  <ModuleWorkspacePage
    :badges="[{ key: 'Health', tone: 'success' }, { key: 'Support' }, { key: 'Platform Admin', tone: 'warning' }]"
    :description="$t('sicherplan.health.description')"
    :eyebrow="$t('sicherplan.ui.moduleEyebrow')"
    :stats="stats"
    :title="$t('sicherplan.admin.health')"
  >
    <template #actions>
      <Card :bordered="false">
        <SectionHeader
          :description="$t('sicherplan.health.actionsDescription')"
          :title="$t('sicherplan.health.actionsTitle')"
        />
        <Space wrap>
          <Button type="primary" :loading="loading" @click="loadHealth">
            {{ $t('sicherplan.health.refresh') }}
          </Button>
        </Space>
      </Card>
    </template>

    <template #main>
      <SectionBlock
        :description="$t('sicherplan.health.statusDescription')"
        :title="$t('sicherplan.health.statusTitle')"
      >
        <Card :bordered="false">
          <Descriptions :column="1" bordered size="small">
            <Descriptions.Item :label="$t('sicherplan.health.service')">
              {{ version?.name ?? live?.service ?? ready?.service ?? $t('sicherplan.health.unknown') }}
            </Descriptions.Item>
            <Descriptions.Item :label="$t('sicherplan.health.environment')">
              {{ version?.env ?? live?.env ?? $t('sicherplan.health.unknown') }}
            </Descriptions.Item>
            <Descriptions.Item :label="$t('sicherplan.health.live')">
              <Tag :color="statusColor(live?.status)">{{ live?.status ?? $t('sicherplan.health.unknown') }}</Tag>
            </Descriptions.Item>
            <Descriptions.Item :label="$t('sicherplan.health.ready')">
              <Tag :color="statusColor(ready?.status)">{{ ready?.status ?? $t('sicherplan.health.unknown') }}</Tag>
            </Descriptions.Item>
            <Descriptions.Item :label="$t('sicherplan.health.version')">
              {{ version?.version ?? $t('sicherplan.health.unknown') }}
            </Descriptions.Item>
          </Descriptions>
        </Card>
      </SectionBlock>
    </template>

    <template #aside>
      <Card :bordered="false">
        <SectionHeader
          :description="$t('sicherplan.health.statusDescription')"
          :title="$t('sicherplan.health.checks')"
        />
        <div class="sp-health__checks">
          <div
            v-for="[name, check] in checkItems"
            :key="name"
            class="sp-health__check"
          >
            <div class="sp-health__check-header">
              <strong>{{ name }}</strong>
              <Tag :color="statusColor(check.status)">{{ check.status ?? $t('sicherplan.health.unknown') }}</Tag>
            </div>
            <p v-if="check.reason">{{ check.reason }}</p>
          </div>
        </div>
      </Card>
    </template>
  </ModuleWorkspacePage>
</template>

<style scoped>
.sp-health__checks {
  display: grid;
  gap: 0.85rem;
}

.sp-health__check {
  display: grid;
  gap: 0.5rem;
  padding: 0.9rem 1rem;
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 1rem;
  background: var(--sp-color-surface-card);
}

.sp-health__check-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.sp-health__check p {
  margin: 0;
  color: var(--sp-color-text-secondary);
  line-height: 1.55;
}
</style>
