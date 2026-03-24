<script lang="ts" setup>
import { computed, onMounted, reactive, ref, watch } from 'vue';

import {
  Alert,
  Button,
  Card,
  Form,
  Input,
  Modal,
  Select,
  Space,
  Table,
  Tag,
  message,
} from 'ant-design-vue';

import { $t } from '#/locales';
import ModuleWorkspacePage from '#/components/sicherplan/module-workspace-page.vue';
import SectionHeader from '#/components/sicherplan/section-header.vue';
import SectionBlock from '#/components/sicherplan/section-block.vue';
import {
  createTenantUser,
  listTenants,
  listTenantUsers,
  resetTenantUserPassword,
  updateTenantUserStatus,
  type TenantAdminUserListItem,
  type TenantListItem,
} from '#/api/sicherplan/tenant-users';

const loadingTenants = ref(false);
const loadingUsers = ref(false);
const saving = ref(false);
const tenants = ref<TenantListItem[]>([]);
const users = ref<TenantAdminUserListItem[]>([]);
const selectedTenantId = ref('');
const tenantSearch = ref('');
const modalOpen = ref(false);
const passwordModalOpen = ref(false);
const passwordTarget = ref<null | TenantAdminUserListItem>(null);
const generatedPassword = ref('');

const createForm = reactive({
  email: '',
  full_name: '',
  locale: 'de',
  status: 'active' as 'active' | 'inactive',
  temporary_password: '',
  timezone: 'Europe/Berlin',
  username: '',
});

const passwordForm = reactive({
  temporary_password: '',
});

const selectedTenant = computed(() =>
  tenants.value.find((tenant) => tenant.id === selectedTenantId.value) ?? null,
);

const filteredTenants = computed(() => {
  const search = tenantSearch.value.trim().toLowerCase();
  if (!search) {
    return tenants.value;
  }
  return tenants.value.filter((tenant) =>
    [tenant.code, tenant.name].some((value) => value.toLowerCase().includes(search)),
  );
});

const stats = computed(() => [
  {
    label: $t('sicherplan.tenantUsers.stats.tenants'),
    value: String(tenants.value.length),
  },
  {
    label: $t('sicherplan.tenantUsers.stats.users'),
    value: String(users.value.length),
  },
  {
    label: $t('sicherplan.tenantUsers.stats.active'),
    value: String(users.value.filter((user) => user.status === 'active').length),
  },
]);

async function loadTenants() {
  loadingTenants.value = true;
  try {
    tenants.value = await listTenants();
    const [firstTenant] = tenants.value;
    if (!selectedTenantId.value && firstTenant) {
      selectedTenantId.value = firstTenant.id;
    }
  } catch (error) {
    message.error(error instanceof Error ? error.message : 'Tenant load failed');
  } finally {
    loadingTenants.value = false;
  }
}

async function loadUsers() {
  if (!selectedTenantId.value) {
    users.value = [];
    return;
  }
  loadingUsers.value = true;
  try {
    users.value = await listTenantUsers(selectedTenantId.value);
  } catch (error) {
    users.value = [];
    message.error(error instanceof Error ? error.message : 'User load failed');
  } finally {
    loadingUsers.value = false;
  }
}

function resetCreateForm() {
  createForm.username = '';
  createForm.email = '';
  createForm.full_name = '';
  createForm.locale = 'de';
  createForm.status = 'active';
  createForm.temporary_password = '';
  createForm.timezone = 'Europe/Berlin';
}

async function submitCreate() {
  if (!selectedTenantId.value) {
    return;
  }
  saving.value = true;
  try {
    const response = await createTenantUser(selectedTenantId.value, {
      email: createForm.email,
      full_name: createForm.full_name,
      locale: createForm.locale,
      status: createForm.status,
      temporary_password: createForm.temporary_password || undefined,
      timezone: createForm.timezone,
      username: createForm.username,
    });
    generatedPassword.value = response.temporary_password;
    modalOpen.value = false;
    resetCreateForm();
    await loadUsers();
    message.success($t('sicherplan.tenantUsers.messages.created'));
  } catch (error) {
    message.error(error instanceof Error ? error.message : 'Create failed');
  } finally {
    saving.value = false;
  }
}

async function changeStatus(user: TenantAdminUserListItem, status: 'active' | 'inactive') {
  saving.value = true;
  try {
    await updateTenantUserStatus(user.tenant_id, user.id, status);
    await loadUsers();
    message.success($t('sicherplan.tenantUsers.messages.statusUpdated'));
  } catch (error) {
    message.error(error instanceof Error ? error.message : 'Status update failed');
  } finally {
    saving.value = false;
  }
}

function asTenantUser(record: Record<string, any>) {
  return record as TenantAdminUserListItem;
}

function openPasswordReset(user: TenantAdminUserListItem) {
  passwordTarget.value = user;
  passwordForm.temporary_password = '';
  passwordModalOpen.value = true;
}

async function submitPasswordReset() {
  if (!passwordTarget.value) {
    return;
  }
  saving.value = true;
  try {
    const response = await resetTenantUserPassword(
      passwordTarget.value.tenant_id,
      passwordTarget.value.id,
      passwordForm.temporary_password || undefined,
    );
    generatedPassword.value = response.temporary_password;
    passwordModalOpen.value = false;
    message.success($t('sicherplan.tenantUsers.messages.passwordReset'));
  } catch (error) {
    message.error(error instanceof Error ? error.message : 'Password reset failed');
  } finally {
    saving.value = false;
  }
}

watch(selectedTenantId, () => {
  void loadUsers();
});

onMounted(async () => {
  await loadTenants();
  await loadUsers();
});
</script>

<template>
  <ModuleWorkspacePage
    :badges="[{ key: 'IAM', tone: 'success' }, { key: 'Platform Admin', tone: 'warning' }, { key: 'Tenant Scope' }]"
    :description="$t('sicherplan.tenantUsers.description')"
    :eyebrow="$t('sicherplan.ui.moduleEyebrow')"
    :stats="stats"
    :title="$t('sicherplan.admin.tenantUsers')"
  >
    <template #actions>
      <Card :bordered="false">
        <SectionHeader
          :description="$t('sicherplan.tenantUsers.actionsDescription')"
          :title="$t('sicherplan.tenantUsers.actionsTitle')"
        />
        <Space wrap>
          <Button type="primary" @click="modalOpen = true">
            {{ $t('sicherplan.tenantUsers.actions.create') }}
          </Button>
          <Button :loading="loadingUsers" @click="loadUsers">
            {{ $t('sicherplan.tenantUsers.actions.refresh') }}
          </Button>
        </Space>
      </Card>
    </template>

    <template #main>
      <Card :bordered="false">
        <SectionHeader
          :description="$t('sicherplan.tenantUsers.filtersDescription')"
          :title="$t('sicherplan.tenantUsers.filtersTitle')"
        />
        <div class="sp-tenant-users__filters">
          <Input
            v-model:value="tenantSearch"
            :placeholder="$t('sicherplan.tenantUsers.filter.searchPlaceholder')"
          />
          <Select
            v-model:value="selectedTenantId"
            :loading="loadingTenants"
            :placeholder="$t('sicherplan.tenantUsers.filter.tenantPlaceholder')"
            show-search
            :filter-option="false"
          >
            <Select.Option
              v-for="tenant in filteredTenants"
              :key="tenant.id"
              :value="tenant.id"
            >
              {{ tenant.name }} ({{ tenant.code }})
            </Select.Option>
          </Select>
        </div>
        <Alert
          v-if="selectedTenant"
          class="sp-tenant-users__summary"
          type="info"
          show-icon
          :message="$t('sicherplan.tenantUsers.summary.title')"
          :description="`${selectedTenant.name} (${selectedTenant.code})`"
        />
      </Card>
    </template>

    <template #aside>
      <Card :bordered="false">
        <SectionHeader
          :description="$t('sicherplan.tenantUsers.scopeDescription')"
          :title="$t('sicherplan.tenantUsers.scopeTitle')"
        />
        <ul class="sp-tenant-users__points">
          <li>{{ $t('sicherplan.tenantUsers.points.0') }}</li>
          <li>{{ $t('sicherplan.tenantUsers.points.1') }}</li>
          <li>{{ $t('sicherplan.tenantUsers.points.2') }}</li>
        </ul>
      </Card>
      <Alert
        v-if="generatedPassword"
        type="success"
        show-icon
        :message="$t('sicherplan.tenantUsers.generatedPasswordTitle')"
        :description="generatedPassword"
      />
      <Alert
        type="warning"
        show-icon
        :message="$t('sicherplan.tenantUsers.currentScope.title')"
        :description="$t('sicherplan.tenantUsers.currentScope.body')"
      />
    </template>

    <template #workspace>
      <SectionBlock
        :description="$t('sicherplan.tenantUsers.tableDescription')"
        :title="$t('sicherplan.tenantUsers.tableTitle')"
      >
        <Alert
          class="sp-tenant-users__scope-note"
          type="info"
          show-icon
          :message="$t('sicherplan.tenantUsers.currentScope.infoTitle')"
          :description="$t('sicherplan.tenantUsers.currentScope.infoBody')"
        />
        <Card :bordered="false">
          <Table
            :columns="[
              { title: $t('sicherplan.tenantUsers.columns.username'), dataIndex: 'username', key: 'username' },
              { title: $t('sicherplan.tenantUsers.columns.fullName'), dataIndex: 'full_name', key: 'full_name' },
              { title: $t('sicherplan.tenantUsers.columns.email'), dataIndex: 'email', key: 'email' },
              { title: $t('sicherplan.tenantUsers.columns.locale'), dataIndex: 'locale', key: 'locale' },
              { title: $t('sicherplan.tenantUsers.columns.status'), key: 'status' },
              { title: $t('sicherplan.tenantUsers.columns.lastLogin'), dataIndex: 'last_login_at', key: 'last_login_at' },
              { title: $t('sicherplan.tenantUsers.columns.actions'), key: 'actions' },
            ]"
            :data-source="users"
            :loading="loadingUsers"
            row-key="id"
            size="middle"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'status'">
                <Tag :color="record.status === 'active' ? 'green' : 'default'">
                  {{ record.status }}
                </Tag>
              </template>
              <template v-else-if="column.key === 'last_login_at'">
                {{ record.last_login_at || $t('sicherplan.tenantUsers.values.never') }}
              </template>
              <template v-else-if="column.key === 'actions'">
                <Space wrap>
                  <Button
                    size="small"
                    @click="changeStatus(asTenantUser(record), record.status === 'active' ? 'inactive' : 'active')"
                  >
                    {{
                      record.status === 'active'
                        ? $t('sicherplan.tenantUsers.actions.deactivate')
                        : $t('sicherplan.tenantUsers.actions.activate')
                    }}
                  </Button>
                  <Button size="small" @click="openPasswordReset(asTenantUser(record))">
                    {{ $t('sicherplan.tenantUsers.actions.resetPassword') }}
                  </Button>
                </Space>
              </template>
            </template>
          </Table>
        </Card>
      </SectionBlock>
    </template>
  </ModuleWorkspacePage>

  <Modal
    v-model:open="modalOpen"
    :confirm-loading="saving"
    :title="$t('sicherplan.tenantUsers.modal.createTitle')"
    @ok="submitCreate"
  >
    <Form layout="vertical">
      <Form.Item :label="$t('sicherplan.tenantUsers.columns.username')">
        <Input v-model:value="createForm.username" />
      </Form.Item>
      <Form.Item :label="$t('sicherplan.tenantUsers.columns.fullName')">
        <Input v-model:value="createForm.full_name" />
      </Form.Item>
      <Form.Item :label="$t('sicherplan.tenantUsers.columns.email')">
        <Input v-model:value="createForm.email" />
      </Form.Item>
      <Form.Item :label="$t('sicherplan.tenantUsers.columns.locale')">
        <Select v-model:value="createForm.locale">
          <Select.Option value="de">de</Select.Option>
          <Select.Option value="en">en</Select.Option>
        </Select>
      </Form.Item>
      <Form.Item :label="$t('sicherplan.tenantUsers.columns.status')">
        <Select v-model:value="createForm.status">
          <Select.Option value="active">active</Select.Option>
          <Select.Option value="inactive">inactive</Select.Option>
        </Select>
      </Form.Item>
      <Form.Item :label="$t('sicherplan.tenantUsers.form.password')">
        <Input v-model:value="createForm.temporary_password" />
      </Form.Item>
    </Form>
  </Modal>

  <Modal
    v-model:open="passwordModalOpen"
    :confirm-loading="saving"
    :title="$t('sicherplan.tenantUsers.modal.passwordTitle')"
    @ok="submitPasswordReset"
  >
    <Form layout="vertical">
      <Form.Item :label="$t('sicherplan.tenantUsers.form.password')">
        <Input v-model:value="passwordForm.temporary_password" />
      </Form.Item>
    </Form>
  </Modal>
</template>

<style scoped>
.sp-tenant-users__filters {
  display: grid;
  gap: 0.75rem;
  grid-template-columns: minmax(0, 1fr) minmax(280px, 360px);
}

.sp-tenant-users__filters > * {
  min-width: 0;
}

.sp-tenant-users__summary {
  margin-top: 1rem;
}

.sp-tenant-users__points {
  display: grid;
  gap: 0.85rem;
  padding-left: 1rem;
  margin: 0;
}

.sp-tenant-users__workspace-copy {
  margin: 0;
  color: var(--sp-color-text-secondary);
  line-height: 1.6;
}

.sp-tenant-users__scope-note {
  margin-bottom: 1rem;
}

@media (max-width: 960px) {
  .sp-tenant-users__filters {
    grid-template-columns: 1fr;
  }
}
</style>
