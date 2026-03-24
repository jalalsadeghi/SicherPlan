<template>
  <div class="core-admin-page">
    <div
      v-if="chromeVisibility.showTenantScopeCard"
      class="module-card core-admin-scope-card"
      :class="{ 'core-admin-scope-card--embedded': embedded }"
    >
      <div class="core-admin-scope-card__row">
        <label class="field-stack">
          <span>{{ t("coreAdmin.scope.label") }}</span>
          <input
            v-model="tenantScopeInput"
            :placeholder="t('coreAdmin.scope.placeholder')"
            :disabled="scopeState.scopeFieldDisabled"
          />
        </label>
        <StatusBadge :status="scopeState.scopeBadgeStatus" />
      </div>
      <div class="cta-row">
        <button
          v-if="scopeState.canLoadScopedTenant"
          class="cta-button"
          type="button"
          :disabled="loading.refresh"
          :data-action-key="ACTION_KEYS.scopeLoad"
          @click="loadScopedTenant"
        >
          {{ t("coreAdmin.actions.loadScopedTenant") }}
        </button>
        <button
          class="cta-button cta-secondary"
          type="button"
          :disabled="loading.refresh"
          @click="refreshAll"
        >
          {{ t("coreAdmin.actions.refresh") }}
        </button>
      </div>
    </div>

    <section v-if="feedback.message" class="core-admin-feedback" :data-tone="feedback.tone">
      <div>
        <strong>{{ feedback.title }}</strong>
        <span>{{ feedback.message }}</span>
      </div>
      <button type="button" @click="clearFeedback">
        {{ t("coreAdmin.actions.clearFeedback") }}
      </button>
    </section>

    <section
      v-if="effectiveRole === 'tenant_admin' && !scopeState.actorTenantId"
      class="module-card core-admin-empty-state"
    >
      <p class="eyebrow">{{ t("coreAdmin.scope.emptyTitle") }}</p>
      <h3>{{ t("coreAdmin.scope.emptyBody") }}</h3>
    </section>

    <div v-else class="core-admin-grid">
      <section class="module-card core-admin-panel">
        <div class="core-admin-panel__header">
          <div>
            <p class="eyebrow">{{ t("coreAdmin.tenants.eyebrow") }}</p>
            <h3>{{ t("coreAdmin.tenants.title") }}</h3>
          </div>
          <StatusBadge :status="loading.tenants ? 'inactive' : 'active'" />
        </div>

        <label class="field-stack">
          <span>{{ t("coreAdmin.tenants.title") }}</span>
          <input v-model="tenantFilter" :placeholder="t('coreAdmin.tenants.filterPlaceholder')" />
        </label>

        <div v-if="filteredTenants.length > 0" class="core-admin-list">
          <button
            v-for="tenant in filteredTenants"
            :key="tenant.id"
            type="button"
            class="core-admin-row"
            :class="{ selected: tenant.id === selectedTenantId }"
            @click="selectTenant(tenant.id)"
          >
            <div>
              <strong>{{ tenant.name }}</strong>
              <span>{{ tenant.code }}</span>
            </div>
            <StatusBadge :status="tenant.status" />
          </button>
        </div>
        <p v-else class="core-admin-list-empty">
          {{
            effectiveRole === "tenant_admin"
              ? t("coreAdmin.tenants.scopeOnly")
              : t("coreAdmin.tenants.empty")
          }}
        </p>

        <form
          v-if="effectiveRole === 'platform_admin'"
          class="core-admin-form"
          @submit.prevent="submitOnboarding"
        >
          <div class="core-admin-panel__header">
            <div>
              <p class="eyebrow">{{ t("coreAdmin.onboarding.eyebrow") }}</p>
              <h3>{{ t("coreAdmin.onboarding.title") }}</h3>
            </div>
          </div>

          <div class="core-admin-form-grid">
            <label class="field-stack">
              <span>{{ t("coreAdmin.fields.tenantCode") }}</span>
              <input v-model="onboarding.tenant.code" required />
            </label>
            <label class="field-stack">
              <span>{{ t("coreAdmin.fields.tenantName") }}</span>
              <input v-model="onboarding.tenant.name" required />
            </label>
            <label class="field-stack">
              <span>{{ t("coreAdmin.fields.legalName") }}</span>
              <input v-model="onboarding.tenant.legal_name" />
            </label>
            <label class="field-stack">
              <span>{{ t("coreAdmin.fields.defaultLocale") }}</span>
              <input v-model="onboarding.tenant.default_locale" required />
            </label>
            <label class="field-stack">
              <span>{{ t("coreAdmin.fields.defaultCurrency") }}</span>
              <input v-model="onboarding.tenant.default_currency" required />
            </label>
            <label class="field-stack">
              <span>{{ t("coreAdmin.fields.timezone") }}</span>
              <input v-model="onboarding.tenant.timezone" required />
            </label>
            <label class="field-stack">
              <span>{{ t("coreAdmin.fields.branchCode") }}</span>
              <input v-model="onboarding.initial_branch.code" required />
            </label>
            <label class="field-stack">
              <span>{{ t("coreAdmin.fields.branchName") }}</span>
              <input v-model="onboarding.initial_branch.name" required />
            </label>
            <label class="field-stack">
              <span>{{ t("coreAdmin.fields.branchEmail") }}</span>
              <input v-model="onboarding.initial_branch.contact_email" />
            </label>
            <label class="field-stack">
              <span>{{ t("coreAdmin.fields.branchPhone") }}</span>
              <input v-model="onboarding.initial_branch.contact_phone" />
            </label>
            <label class="field-stack">
              <span>{{ t("coreAdmin.fields.mandateCode") }}</span>
              <input v-model="onboarding.initial_mandate.code" required />
            </label>
            <label class="field-stack">
              <span>{{ t("coreAdmin.fields.mandateName") }}</span>
              <input v-model="onboarding.initial_mandate.name" required />
            </label>
            <label class="field-stack">
              <span>{{ t("coreAdmin.fields.settingKey") }}</span>
              <input v-model="onboarding.initial_setting_key" />
            </label>
            <label class="field-stack field-stack--wide">
              <span>{{ t("coreAdmin.fields.settingValue") }}</span>
              <textarea v-model="onboarding.initial_setting_value" rows="4" />
            </label>
          </div>

          <div class="cta-row">
            <button
              class="cta-button"
              type="submit"
              :data-action-key="ACTION_KEYS.tenantCreate"
              :disabled="loading.onboarding"
            >
              {{ t("coreAdmin.actions.createTenant") }}
            </button>
          </div>
        </form>
      </section>

      <section class="module-card core-admin-panel core-admin-detail">
        <div class="core-admin-panel__header">
          <div>
            <p class="eyebrow">{{ t("coreAdmin.detail.eyebrow") }}</p>
            <h3>{{ selectedTenant ? selectedTenant.name : t("coreAdmin.detail.emptyTitle") }}</h3>
          </div>
          <StatusBadge v-if="selectedTenant" :status="selectedTenant.status" />
        </div>

        <template v-if="selectedTenant">
          <div class="core-admin-lifecycle">
            <div>
              <strong>{{ t("coreAdmin.lifecycle.title") }}</strong>
              <p class="field-help" v-if="selectedTenant.archived_at">
                {{ t("coreAdmin.lifecycle.archivedHint") }}
              </p>
            </div>
            <div class="cta-row">
              <button
                v-if="selectedTenant.status === 'inactive'"
                class="cta-button"
                type="button"
                :data-action-key="ACTION_KEYS.tenantActivate"
                @click="setTenantStatus('active')"
              >
                {{ t("coreAdmin.actions.reactivate") }}
              </button>
              <button
                v-if="selectedTenant.status === 'active'"
                class="cta-button"
                type="button"
                :data-action-key="ACTION_KEYS.tenantDeactivate"
                @click="setTenantStatus('inactive')"
              >
                {{ t("coreAdmin.actions.deactivate") }}
              </button>
              <button
                v-if="!selectedTenant.archived_at"
                class="cta-button cta-secondary"
                type="button"
                :data-action-key="ACTION_KEYS.tenantArchive"
                @click="archiveTenant"
              >
                {{ t("coreAdmin.actions.archive") }}
              </button>
            </div>
          </div>

          <form class="core-admin-form" @submit.prevent="submitTenantUpdate">
            <div class="core-admin-form-grid">
              <label class="field-stack">
                <span>{{ t("coreAdmin.fields.tenantCode") }}</span>
                <input :value="selectedTenant.code" disabled />
              </label>
              <label class="field-stack">
                <span>{{ t("coreAdmin.fields.tenantName") }}</span>
                <input v-model="tenantDraft.name" required />
              </label>
              <label class="field-stack">
                <span>{{ t("coreAdmin.fields.legalName") }}</span>
                <input v-model="tenantDraft.legal_name" />
              </label>
              <label class="field-stack">
                <span>{{ t("coreAdmin.fields.defaultLocale") }}</span>
                <input v-model="tenantDraft.default_locale" required />
              </label>
              <label class="field-stack">
                <span>{{ t("coreAdmin.fields.defaultCurrency") }}</span>
                <input v-model="tenantDraft.default_currency" required />
              </label>
              <label class="field-stack">
                <span>{{ t("coreAdmin.fields.timezone") }}</span>
                <input v-model="tenantDraft.timezone" required />
              </label>
            </div>

            <div class="cta-row">
              <button
                class="cta-button"
                type="submit"
                :data-action-key="ACTION_KEYS.tenantSave"
                :disabled="loading.tenant"
              >
                {{ t("coreAdmin.actions.saveTenant") }}
              </button>
            </div>
          </form>

          <section class="core-admin-section">
            <div class="core-admin-panel__header">
              <div>
                <p class="eyebrow">{{ t("coreAdmin.branches.eyebrow") }}</p>
                <h3>{{ t("coreAdmin.branches.title") }}</h3>
              </div>
              <StatusBadge :status="branches.length > 0 ? 'active' : 'inactive'" />
            </div>

            <div v-if="branches.length > 0" class="core-admin-list">
              <article v-for="branch in branches" :key="branch.id" class="core-admin-record">
                <div>
                  <strong>{{ branch.name }}</strong>
                  <span>{{ branch.code }}</span>
                </div>
                <div class="core-admin-record__actions">
                  <StatusBadge :status="branch.status" />
                  <button type="button" @click="editBranch(branch)">
                    {{ t("coreAdmin.actions.edit") }}
                  </button>
                  <button
                    v-if="branch.status === 'active'"
                    type="button"
                    :data-action-key="ACTION_KEYS.branchDeactivate"
                    @click="setBranchStatus(branch, 'inactive')"
                  >
                    {{ t("coreAdmin.actions.deactivate") }}
                  </button>
                  <button
                    v-if="branch.status === 'inactive' && !branch.archived_at"
                    type="button"
                    :data-action-key="ACTION_KEYS.branchActivate"
                    @click="setBranchStatus(branch, 'active')"
                  >
                    {{ t("coreAdmin.actions.reactivate") }}
                  </button>
                  <button
                    v-if="!branch.archived_at"
                    type="button"
                    :data-action-key="ACTION_KEYS.branchArchive"
                    @click="setBranchStatus(branch, 'archived')"
                  >
                    {{ t("coreAdmin.actions.archive") }}
                  </button>
                </div>
              </article>
            </div>
            <p v-else class="core-admin-list-empty">{{ t("coreAdmin.branches.empty") }}</p>

            <form class="core-admin-form" @submit.prevent="submitBranch">
              <div class="core-admin-form-grid">
                <label class="field-stack">
                  <span>{{ t("coreAdmin.fields.branchCode") }}</span>
                  <input v-model="branchDraft.code" :disabled="Boolean(branchDraft.id)" required />
                </label>
                <label class="field-stack">
                  <span>{{ t("coreAdmin.fields.branchName") }}</span>
                  <input v-model="branchDraft.name" required />
                </label>
                <label class="field-stack">
                  <span>{{ t("coreAdmin.fields.branchEmail") }}</span>
                  <input v-model="branchDraft.contact_email" />
                </label>
                <label class="field-stack">
                  <span>{{ t("coreAdmin.fields.branchPhone") }}</span>
                  <input v-model="branchDraft.contact_phone" />
                </label>
              </div>

              <div class="cta-row">
                <button
                  class="cta-button"
                  type="submit"
                  :data-action-key="branchDraft.id ? ACTION_KEYS.branchSave : ACTION_KEYS.branchCreate"
                  :disabled="loading.branch"
                >
                  {{
                    branchDraft.id
                      ? t("coreAdmin.actions.saveBranch")
                      : t("coreAdmin.actions.createBranch")
                  }}
                </button>
                <button
                  v-if="branchDraft.id"
                  class="cta-button cta-secondary"
                  type="button"
                  @click="resetBranchDraft"
                >
                  {{ t("coreAdmin.actions.cancel") }}
                </button>
              </div>
            </form>
          </section>

          <section class="core-admin-section">
            <div class="core-admin-panel__header">
              <div>
                <p class="eyebrow">{{ t("coreAdmin.mandates.eyebrow") }}</p>
                <h3>{{ t("coreAdmin.mandates.title") }}</h3>
              </div>
              <StatusBadge :status="mandates.length > 0 ? 'active' : 'inactive'" />
            </div>

            <div v-if="mandates.length > 0" class="core-admin-list">
              <article v-for="mandate in mandates" :key="mandate.id" class="core-admin-record">
                <div>
                  <strong>{{ mandate.name }}</strong>
                  <span>{{ mandate.code }}</span>
                </div>
                <div class="core-admin-record__actions">
                  <StatusBadge :status="mandate.status" />
                  <button type="button" @click="editMandate(mandate)">
                    {{ t("coreAdmin.actions.edit") }}
                  </button>
                  <button
                    v-if="mandate.status === 'active'"
                    type="button"
                    :data-action-key="ACTION_KEYS.mandateDeactivate"
                    @click="setMandateStatus(mandate, 'inactive')"
                  >
                    {{ t("coreAdmin.actions.deactivate") }}
                  </button>
                  <button
                    v-if="mandate.status === 'inactive' && !mandate.archived_at"
                    type="button"
                    :data-action-key="ACTION_KEYS.mandateActivate"
                    @click="setMandateStatus(mandate, 'active')"
                  >
                    {{ t("coreAdmin.actions.reactivate") }}
                  </button>
                  <button
                    v-if="!mandate.archived_at"
                    type="button"
                    :data-action-key="ACTION_KEYS.mandateArchive"
                    @click="setMandateStatus(mandate, 'archived')"
                  >
                    {{ t("coreAdmin.actions.archive") }}
                  </button>
                </div>
              </article>
            </div>
            <p v-else class="core-admin-list-empty">{{ t("coreAdmin.mandates.empty") }}</p>

            <form class="core-admin-form" @submit.prevent="submitMandate">
              <div class="core-admin-form-grid">
                <label class="field-stack">
                  <span>{{ t("coreAdmin.fields.branch") }}</span>
                  <select v-model="mandateDraft.branch_id" required>
                    <option value="" disabled>{{ t("coreAdmin.fields.branchPlaceholder") }}</option>
                    <option v-for="branch in branches" :key="branch.id" :value="branch.id">
                      {{ branch.name }}
                    </option>
                  </select>
                </label>
                <label class="field-stack">
                  <span>{{ t("coreAdmin.fields.mandateCode") }}</span>
                  <input v-model="mandateDraft.code" :disabled="Boolean(mandateDraft.id)" required />
                </label>
                <label class="field-stack">
                  <span>{{ t("coreAdmin.fields.mandateName") }}</span>
                  <input v-model="mandateDraft.name" required />
                </label>
                <label class="field-stack">
                  <span>{{ t("coreAdmin.fields.externalRef") }}</span>
                  <input v-model="mandateDraft.external_ref" />
                </label>
                <label class="field-stack field-stack--wide">
                  <span>{{ t("coreAdmin.fields.notes") }}</span>
                  <textarea v-model="mandateDraft.notes" rows="3" />
                </label>
              </div>

              <div class="cta-row">
                <button
                  class="cta-button"
                  type="submit"
                  :data-action-key="mandateDraft.id ? ACTION_KEYS.mandateSave : ACTION_KEYS.mandateCreate"
                  :disabled="loading.mandate"
                >
                  {{
                    mandateDraft.id
                      ? t("coreAdmin.actions.saveMandate")
                      : t("coreAdmin.actions.createMandate")
                  }}
                </button>
                <button
                  v-if="mandateDraft.id"
                  class="cta-button cta-secondary"
                  type="button"
                  @click="resetMandateDraft"
                >
                  {{ t("coreAdmin.actions.cancel") }}
                </button>
              </div>
            </form>
          </section>

          <section class="core-admin-section">
            <div class="core-admin-panel__header">
              <div>
                <p class="eyebrow">{{ t("coreAdmin.settings.eyebrow") }}</p>
                <h3>{{ t("coreAdmin.settings.title") }}</h3>
              </div>
              <StatusBadge :status="settings.length > 0 ? 'active' : 'inactive'" />
            </div>

            <div v-if="settings.length > 0" class="core-admin-list">
              <article v-for="setting in settings" :key="setting.id" class="core-admin-record">
                <div>
                  <strong>{{ setting.key }}</strong>
                  <span>{{ stringifyValue(setting.value_json) }}</span>
                </div>
                <div class="core-admin-record__actions">
                  <span class="core-admin-version">
                    {{ t("coreAdmin.settings.version") }} {{ setting.version_no }}
                  </span>
                  <StatusBadge :status="setting.status" />
                  <button type="button" @click="editSetting(setting)">
                    {{ t("coreAdmin.actions.edit") }}
                  </button>
                  <button
                    v-if="setting.status === 'active'"
                    type="button"
                    :data-action-key="ACTION_KEYS.settingDeactivate"
                    @click="setSettingStatus(setting, 'inactive')"
                  >
                    {{ t("coreAdmin.actions.deactivate") }}
                  </button>
                  <button
                    v-if="setting.status === 'inactive' && !setting.archived_at"
                    type="button"
                    :data-action-key="ACTION_KEYS.settingActivate"
                    @click="setSettingStatus(setting, 'active')"
                  >
                    {{ t("coreAdmin.actions.reactivate") }}
                  </button>
                  <button
                    v-if="!setting.archived_at"
                    type="button"
                    :data-action-key="ACTION_KEYS.settingArchive"
                    @click="setSettingStatus(setting, 'archived')"
                  >
                    {{ t("coreAdmin.actions.archive") }}
                  </button>
                </div>
              </article>
            </div>
            <p v-else class="core-admin-list-empty">{{ t("coreAdmin.settings.empty") }}</p>

            <form class="core-admin-form" @submit.prevent="submitSetting">
              <div class="core-admin-form-grid">
                <label class="field-stack">
                  <span>{{ t("coreAdmin.fields.settingKey") }}</span>
                  <input v-model="settingDraft.key" :disabled="Boolean(settingDraft.id)" required />
                </label>
                <label class="field-stack field-stack--wide">
                  <span>{{ t("coreAdmin.fields.settingValueJson") }}</span>
                  <textarea v-model="settingDraft.valueJsonText" rows="4" required />
                </label>
              </div>

              <div class="cta-row">
                <button
                  class="cta-button"
                  type="submit"
                  :data-action-key="settingDraft.id ? ACTION_KEYS.settingSave : ACTION_KEYS.settingCreate"
                  :disabled="loading.setting"
                >
                  {{
                    settingDraft.id
                      ? t("coreAdmin.actions.saveSetting")
                      : t("coreAdmin.actions.createSetting")
                  }}
                </button>
                <button
                  v-if="settingDraft.id"
                  class="cta-button cta-secondary"
                  type="button"
                  @click="resetSettingDraft"
                >
                  {{ t("coreAdmin.actions.cancel") }}
                </button>
              </div>
            </form>
          </section>
        </template>

        <div v-else class="core-admin-empty-state">
          <p class="eyebrow">{{ t("coreAdmin.detail.emptyTitle") }}</p>
          <h3>{{ t("coreAdmin.detail.emptyState") }}</h3>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import StatusBadge from "@/components/StatusBadge.vue";
import {
  CoreAdminApiError,
  createBranch,
  createMandate,
  createSetting,
  getTenant,
  listBranches,
  listMandates,
  listSettings,
  listTenants,
  onboardTenant,
  transitionTenantStatus,
  updateBranch,
  updateMandate,
  updateSetting,
  updateTenant,
  type BranchRead,
  type LifecycleStatus,
  type MandateRead,
  type TenantListItem,
  type TenantRead,
  type TenantSettingRead,
} from "@/api/coreAdmin";
import {
  resolveCoreAdminChromeVisibility,
  resolveCoreAdminScopeState,
  resolveCoreAdminTenantIdToLoad,
} from "@/features/core/coreAdmin.helpers.js";
import { useI18n } from "@/i18n";
import { useAuthStore } from "@/stores/auth";

withDefaults(defineProps<{ embedded?: boolean }>(), {
  embedded: false,
});

const ACTION_KEYS = {
  scopeLoad: "core.admin.scope.load",
  tenantCreate: "core.admin.tenant.create",
  tenantSave: "core.admin.tenant.write",
  tenantActivate: "core.admin.tenant.activate",
  tenantDeactivate: "core.admin.tenant.deactivate",
  tenantArchive: "core.admin.tenant.archive",
  branchCreate: "core.admin.branch.create",
  branchSave: "core.admin.branch.write",
  branchActivate: "core.admin.branch.activate",
  branchDeactivate: "core.admin.branch.deactivate",
  branchArchive: "core.admin.branch.archive",
  mandateCreate: "core.admin.mandate.create",
  mandateSave: "core.admin.mandate.write",
  mandateActivate: "core.admin.mandate.activate",
  mandateDeactivate: "core.admin.mandate.deactivate",
  mandateArchive: "core.admin.mandate.archive",
  settingCreate: "core.admin.setting.create",
  settingSave: "core.admin.setting.write",
  settingActivate: "core.admin.setting.activate",
  settingDeactivate: "core.admin.setting.deactivate",
  settingArchive: "core.admin.setting.archive",
} as const;

const API_ERROR_KEYS = {
  "errors.core.authorization.forbidden": "coreAdmin.api.errors.authorization.forbidden",
  "errors.core.tenant.not_found": "coreAdmin.api.errors.tenant.not_found",
  "errors.core.branch.not_found": "coreAdmin.api.errors.branch.not_found",
  "errors.core.mandate.not_found": "coreAdmin.api.errors.mandate.not_found",
  "errors.core.tenant_setting.not_found": "coreAdmin.api.errors.setting.not_found",
  "errors.core.tenant.duplicate_code": "coreAdmin.api.errors.tenant.duplicate_code",
  "errors.core.branch.duplicate_code": "coreAdmin.api.errors.branch.duplicate_code",
  "errors.core.mandate.duplicate_code": "coreAdmin.api.errors.mandate.duplicate_code",
  "errors.core.setting.duplicate_key": "coreAdmin.api.errors.setting.duplicate_key",
  "errors.core.setting.stale_version": "coreAdmin.api.errors.setting.stale_version",
  "errors.core.mandate.invalid_branch_scope": "coreAdmin.api.errors.mandate.invalid_branch_scope",
  "errors.core.lifecycle.archived_record": "coreAdmin.api.errors.lifecycle.archived_record",
  "errors.core.conflict.integrity": "coreAdmin.api.errors.conflict.integrity",
  "errors.platform.internal": "api.errors.platform.internal",
} as const;

const route = useRoute();
const router = useRouter();
const { t } = useI18n();
const authStore = useAuthStore();

const tenants = ref<TenantListItem[]>([]);
const selectedTenantId = ref(readQueryValue(route.query.tenant) ?? authStore.tenantScopeId);
const selectedTenant = ref<TenantRead | null>(null);
const branches = ref<BranchRead[]>([]);
const mandates = ref<MandateRead[]>([]);
const settings = ref<TenantSettingRead[]>([]);

const tenantFilter = ref(readQueryValue(route.query.filter) ?? "");
const tenantScopeInput = ref(readQueryValue(route.query.scope) ?? authStore.tenantScopeId);

const feedback = reactive({
  tone: "info" as "info" | "success" | "danger",
  title: "",
  message: "",
});

const loading = reactive({
  refresh: false,
  tenants: false,
  tenantContext: false,
  onboarding: false,
  tenant: false,
  branch: false,
  mandate: false,
  setting: false,
});

const onboarding = reactive({
  tenant: {
    code: "",
    name: "",
    legal_name: "",
    default_locale: "de",
    default_currency: "EUR",
    timezone: "Europe/Berlin",
  },
  initial_branch: {
    code: "",
    name: "",
    contact_email: "",
    contact_phone: "",
  },
  initial_mandate: {
    code: "",
    name: "",
    external_ref: "",
    notes: "",
  },
  initial_setting_key: "ui.theme",
  initial_setting_value: "{\"mode\":\"light\"}",
});

const tenantDraft = reactive({
  name: "",
  legal_name: "",
  default_locale: "de",
  default_currency: "EUR",
  timezone: "Europe/Berlin",
});

const branchDraft = reactive({
  id: "",
  code: "",
  name: "",
  contact_email: "",
  contact_phone: "",
});

const mandateDraft = reactive({
  id: "",
  branch_id: "",
  code: "",
  name: "",
  external_ref: "",
  notes: "",
});

const settingDraft = reactive({
  id: "",
  key: "",
  version_no: 0,
  valueJsonText: "{\"mode\":\"light\"}",
});

const effectiveRole = computed(() => authStore.effectiveRole);
const effectiveAccessToken = computed(() => authStore.effectiveAccessToken);
const chromeVisibility = computed(() => resolveCoreAdminChromeVisibility(effectiveRole.value));
const scopeState = computed(() =>
  resolveCoreAdminScopeState({
    effectiveRole: effectiveRole.value,
    tenantScopeInput: tenantScopeInput.value,
    rememberedTenantScopeId: authStore.tenantScopeId,
    sessionTenantId: authStore.sessionUser?.tenant_id ?? authStore.effectiveTenantScopeId,
  }),
);
const actorTenantId = computed(() => scopeState.value.actorTenantId);

const filteredTenants = computed(() => {
  const filterValue = tenantFilter.value.trim().toLowerCase();
  if (!filterValue) {
    return tenants.value;
  }

  return tenants.value.filter((tenant) =>
    [tenant.code, tenant.name].some((value) => value.toLowerCase().includes(filterValue)),
  );
});

function readQueryValue(value: unknown) {
  return typeof value === "string" ? value : null;
}

function clearFeedback() {
  feedback.title = "";
  feedback.message = "";
}

function setFeedback(
  tone: "info" | "success" | "danger",
  title: string,
  message: string,
) {
  feedback.tone = tone;
  feedback.title = title;
  feedback.message = message;
}

function syncRouteState() {
  const query = {
    ...route.query,
    filter: tenantFilter.value || undefined,
    tenant: selectedTenantId.value || undefined,
    scope: scopeState.value.scopeQueryValue,
  };

  void router.replace({ query });
}

function hydrateTenantDraft() {
  if (!selectedTenant.value) {
    return;
  }

  tenantDraft.name = selectedTenant.value.name;
  tenantDraft.legal_name = selectedTenant.value.legal_name ?? "";
  tenantDraft.default_locale = selectedTenant.value.default_locale;
  tenantDraft.default_currency = selectedTenant.value.default_currency;
  tenantDraft.timezone = selectedTenant.value.timezone;
}

function resetBranchDraft() {
  branchDraft.id = "";
  branchDraft.code = "";
  branchDraft.name = "";
  branchDraft.contact_email = "";
  branchDraft.contact_phone = "";
}

function resetMandateDraft() {
  mandateDraft.id = "";
  mandateDraft.branch_id = branches.value[0]?.id ?? "";
  mandateDraft.code = "";
  mandateDraft.name = "";
  mandateDraft.external_ref = "";
  mandateDraft.notes = "";
}

function resetSettingDraft() {
  settingDraft.id = "";
  settingDraft.key = "";
  settingDraft.version_no = 0;
  settingDraft.valueJsonText = "{\"mode\":\"light\"}";
}

function selectTenant(tenantId: string) {
  selectedTenantId.value = tenantId;
  authStore.setTenantScopeId(tenantId);
}

async function refreshAll() {
  authStore.syncFromPrimarySession();

  if (effectiveRole.value === "tenant_admin" && !actorTenantId.value) {
    tenants.value = [];
    selectedTenant.value = null;
    branches.value = [];
    mandates.value = [];
    settings.value = [];
    return;
  }

  loading.refresh = true;
  clearFeedback();

  try {
    await loadTenants();
    const tenantIdToLoad = resolveCoreAdminTenantIdToLoad(
      selectedTenantId.value,
      effectiveRole.value,
      actorTenantId.value,
    );

    if (tenantIdToLoad) {
      selectedTenantId.value = tenantIdToLoad;
      await loadTenantContext(tenantIdToLoad);
    }
  } finally {
    loading.refresh = false;
  }
}

async function loadScopedTenant() {
  if (effectiveRole.value === "tenant_admin") {
    return;
  }

  const scopedTenantId = tenantScopeInput.value.trim();
  if (!scopedTenantId) {
    setFeedback("info", t("coreAdmin.feedback.info"), t("coreAdmin.scope.emptyBody"));
    return;
  }

  authStore.setTenantScopeId(scopedTenantId);
  selectedTenantId.value = scopedTenantId;
  await refreshAll();
  setFeedback("success", t("coreAdmin.feedback.success"), t("coreAdmin.feedback.scopeRemembered"));
}

async function loadTenants() {
  loading.tenants = true;

  try {
    tenants.value = await listTenants(effectiveAccessToken.value, effectiveRole.value, actorTenantId.value);

    if (tenants.value.length === 0) {
      selectedTenantId.value = effectiveRole.value === "tenant_admin" ? actorTenantId.value ?? "" : "";
      return;
    }

    const selectedStillVisible = tenants.value.some((tenant) => tenant.id === selectedTenantId.value);
    if (!selectedStillVisible) {
      selectedTenantId.value = tenants.value[0]?.id ?? "";
    }
  } catch (error) {
    handleError(error);
  } finally {
    loading.tenants = false;
  }
}

async function loadTenantContext(tenantId: string) {
  loading.tenantContext = true;

  try {
    const [tenantRecord, branchRecords, mandateRecords, settingRecords] = await Promise.all([
      getTenant(effectiveAccessToken.value, tenantId, effectiveRole.value, actorTenantId.value),
      listBranches(effectiveAccessToken.value, tenantId, effectiveRole.value, actorTenantId.value),
      listMandates(effectiveAccessToken.value, tenantId, effectiveRole.value, actorTenantId.value),
      listSettings(effectiveAccessToken.value, tenantId, effectiveRole.value, actorTenantId.value),
    ]);

    selectedTenant.value = tenantRecord;
    branches.value = branchRecords;
    mandates.value = mandateRecords;
    settings.value = settingRecords;
    authStore.setTenantScopeId(tenantRecord.id);
    tenantScopeInput.value = effectiveRole.value === "tenant_admin" ? tenantRecord.id : tenantScopeInput.value;
    hydrateTenantDraft();
    resetMandateDraft();
  } catch (error) {
    handleError(error);
  } finally {
    loading.tenantContext = false;
  }
}

async function submitOnboarding() {
  loading.onboarding = true;

  try {
    const tenantIdPlaceholder = "00000000-0000-0000-0000-000000000000";
    const result = await onboardTenant(
      effectiveAccessToken.value,
      {
        tenant: {
          code: onboarding.tenant.code,
          name: onboarding.tenant.name,
          legal_name: onboarding.tenant.legal_name || null,
          default_locale: onboarding.tenant.default_locale,
          default_currency: onboarding.tenant.default_currency,
          timezone: onboarding.tenant.timezone,
        },
        initial_branch: {
          tenant_id: tenantIdPlaceholder,
          code: onboarding.initial_branch.code,
          name: onboarding.initial_branch.name,
          contact_email: onboarding.initial_branch.contact_email || null,
          contact_phone: onboarding.initial_branch.contact_phone || null,
        },
        initial_mandate: {
          tenant_id: tenantIdPlaceholder,
          branch_id: tenantIdPlaceholder,
          code: onboarding.initial_mandate.code,
          name: onboarding.initial_mandate.name,
          external_ref: onboarding.initial_mandate.external_ref || null,
          notes: onboarding.initial_mandate.notes || null,
        },
        initial_settings: onboarding.initial_setting_key
          ? [
              {
                tenant_id: tenantIdPlaceholder,
                key: onboarding.initial_setting_key,
                value_json: parseJsonObject(onboarding.initial_setting_value),
              },
            ]
          : [],
      },
      effectiveRole.value,
    );

    setFeedback("success", t("coreAdmin.feedback.success"), t("coreAdmin.feedback.tenantCreated"));
    await loadTenants();
    selectTenant(result.tenant.id);
    await loadTenantContext(result.tenant.id);
  } catch (error) {
    handleError(error);
  } finally {
    loading.onboarding = false;
  }
}

async function submitTenantUpdate() {
  if (!selectedTenant.value) {
    return;
  }

  loading.tenant = true;

  try {
    selectedTenant.value = await updateTenant(
      effectiveAccessToken.value,
      selectedTenant.value.id,
      {
        name: tenantDraft.name,
        legal_name: tenantDraft.legal_name || null,
        default_locale: tenantDraft.default_locale,
        default_currency: tenantDraft.default_currency,
        timezone: tenantDraft.timezone,
      },
      effectiveRole.value,
      actorTenantId.value,
    );

    syncTenantListItem(selectedTenant.value);
    setFeedback("success", t("coreAdmin.feedback.success"), t("coreAdmin.feedback.tenantSaved"));
  } catch (error) {
    handleError(error);
  } finally {
    loading.tenant = false;
  }
}

async function setTenantStatus(status: LifecycleStatus) {
  if (!selectedTenant.value) {
    return;
  }

  loading.tenant = true;

  try {
    selectedTenant.value = await transitionTenantStatus(
      effectiveAccessToken.value,
      selectedTenant.value.id,
      status,
      effectiveRole.value,
      actorTenantId.value,
    );
    syncTenantListItem(selectedTenant.value);
    setFeedback("success", t("coreAdmin.feedback.success"), t("coreAdmin.feedback.tenantStatusSaved"));
  } catch (error) {
    handleError(error);
  } finally {
    loading.tenant = false;
  }
}

async function archiveTenant() {
  if (!selectedTenant.value) {
    return;
  }

  loading.tenant = true;

  try {
    selectedTenant.value = await updateTenant(
      effectiveAccessToken.value,
      selectedTenant.value.id,
      {
        status: "archived",
        archived_at: new Date().toISOString(),
      },
      effectiveRole.value,
      actorTenantId.value,
    );
    syncTenantListItem(selectedTenant.value);
    setFeedback("success", t("coreAdmin.feedback.success"), t("coreAdmin.feedback.tenantStatusSaved"));
  } catch (error) {
    handleError(error);
  } finally {
    loading.tenant = false;
  }
}

async function submitBranch() {
  if (!selectedTenant.value) {
    return;
  }

  loading.branch = true;

  try {
    if (branchDraft.id) {
      await updateBranch(
        effectiveAccessToken.value,
        selectedTenant.value.id,
        branchDraft.id,
        {
          name: branchDraft.name,
          contact_email: branchDraft.contact_email || null,
          contact_phone: branchDraft.contact_phone || null,
        },
        effectiveRole.value,
        actorTenantId.value,
      );
    } else {
      await createBranch(
        effectiveAccessToken.value,
        selectedTenant.value.id,
        {
          tenant_id: selectedTenant.value.id,
          code: branchDraft.code,
          name: branchDraft.name,
          address_id: null,
          contact_email: branchDraft.contact_email || null,
          contact_phone: branchDraft.contact_phone || null,
        },
        effectiveRole.value,
        actorTenantId.value,
      );
    }

    await loadTenantContext(selectedTenant.value.id);
    resetBranchDraft();
    setFeedback("success", t("coreAdmin.feedback.success"), t("coreAdmin.feedback.branchSaved"));
  } catch (error) {
    handleError(error);
  } finally {
    loading.branch = false;
  }
}

async function setBranchStatus(branch: BranchRead, status: LifecycleStatus) {
  if (!selectedTenant.value) {
    return;
  }

  loading.branch = true;

  try {
    await updateBranch(
      effectiveAccessToken.value,
      selectedTenant.value.id,
      branch.id,
      {
        status,
        archived_at: status === "archived" ? new Date().toISOString() : null,
      },
      effectiveRole.value,
      actorTenantId.value,
    );

    await loadTenantContext(selectedTenant.value.id);
    setFeedback("success", t("coreAdmin.feedback.success"), t("coreAdmin.feedback.branchStatusSaved"));
  } catch (error) {
    handleError(error);
  } finally {
    loading.branch = false;
  }
}

async function submitMandate() {
  if (!selectedTenant.value) {
    return;
  }

  loading.mandate = true;

  try {
    if (mandateDraft.id) {
      await updateMandate(
        effectiveAccessToken.value,
        selectedTenant.value.id,
        mandateDraft.id,
        {
          name: mandateDraft.name,
          external_ref: mandateDraft.external_ref || null,
          notes: mandateDraft.notes || null,
        },
        effectiveRole.value,
        actorTenantId.value,
      );
    } else {
      await createMandate(
        effectiveAccessToken.value,
        selectedTenant.value.id,
        {
          tenant_id: selectedTenant.value.id,
          branch_id: mandateDraft.branch_id,
          code: mandateDraft.code,
          name: mandateDraft.name,
          external_ref: mandateDraft.external_ref || null,
          notes: mandateDraft.notes || null,
        },
        effectiveRole.value,
        actorTenantId.value,
      );
    }

    await loadTenantContext(selectedTenant.value.id);
    resetMandateDraft();
    setFeedback("success", t("coreAdmin.feedback.success"), t("coreAdmin.feedback.mandateSaved"));
  } catch (error) {
    handleError(error);
  } finally {
    loading.mandate = false;
  }
}

async function setMandateStatus(mandate: MandateRead, status: LifecycleStatus) {
  if (!selectedTenant.value) {
    return;
  }

  loading.mandate = true;

  try {
    await updateMandate(
      effectiveAccessToken.value,
      selectedTenant.value.id,
      mandate.id,
      {
        status,
        archived_at: status === "archived" ? new Date().toISOString() : null,
      },
      effectiveRole.value,
      actorTenantId.value,
    );

    await loadTenantContext(selectedTenant.value.id);
    setFeedback("success", t("coreAdmin.feedback.success"), t("coreAdmin.feedback.mandateStatusSaved"));
  } catch (error) {
    handleError(error);
  } finally {
    loading.mandate = false;
  }
}

async function submitSetting() {
  if (!selectedTenant.value) {
    return;
  }

  loading.setting = true;

  try {
    if (settingDraft.id) {
      await updateSetting(
        effectiveAccessToken.value,
        selectedTenant.value.id,
        settingDraft.id,
        {
          value_json: parseJsonObject(settingDraft.valueJsonText),
          version_no: settingDraft.version_no,
        },
        effectiveRole.value,
        actorTenantId.value,
      );
    } else {
      await createSetting(
        effectiveAccessToken.value,
        selectedTenant.value.id,
        {
          tenant_id: selectedTenant.value.id,
          key: settingDraft.key,
          value_json: parseJsonObject(settingDraft.valueJsonText),
        },
        effectiveRole.value,
        actorTenantId.value,
      );
    }

    await loadTenantContext(selectedTenant.value.id);
    resetSettingDraft();
    setFeedback("success", t("coreAdmin.feedback.success"), t("coreAdmin.feedback.settingSaved"));
  } catch (error) {
    handleError(error);
  } finally {
    loading.setting = false;
  }
}

async function setSettingStatus(setting: TenantSettingRead, status: LifecycleStatus) {
  if (!selectedTenant.value) {
    return;
  }

  loading.setting = true;

  try {
    await updateSetting(
      effectiveAccessToken.value,
      selectedTenant.value.id,
      setting.id,
      {
        value_json: setting.value_json,
        version_no: setting.version_no,
        status,
        archived_at: status === "archived" ? new Date().toISOString() : null,
      },
      effectiveRole.value,
      actorTenantId.value,
    );

    await loadTenantContext(selectedTenant.value.id);
    setFeedback("success", t("coreAdmin.feedback.success"), t("coreAdmin.feedback.settingStatusSaved"));
  } catch (error) {
    handleError(error);
  } finally {
    loading.setting = false;
  }
}

function editBranch(branch: BranchRead) {
  branchDraft.id = branch.id;
  branchDraft.code = branch.code;
  branchDraft.name = branch.name;
  branchDraft.contact_email = branch.contact_email ?? "";
  branchDraft.contact_phone = branch.contact_phone ?? "";
}

function editMandate(mandate: MandateRead) {
  mandateDraft.id = mandate.id;
  mandateDraft.branch_id = mandate.branch_id;
  mandateDraft.code = mandate.code;
  mandateDraft.name = mandate.name;
  mandateDraft.external_ref = mandate.external_ref ?? "";
  mandateDraft.notes = mandate.notes ?? "";
}

function editSetting(setting: TenantSettingRead) {
  settingDraft.id = setting.id;
  settingDraft.key = setting.key;
  settingDraft.version_no = setting.version_no;
  settingDraft.valueJsonText = JSON.stringify(setting.value_json, null, 2);
}

function parseJsonObject(value: string) {
  let parsed: unknown;

  try {
    parsed = JSON.parse(value);
  } catch {
    throw new Error("invalid_json");
  }

  if (!parsed || Array.isArray(parsed) || typeof parsed !== "object") {
    throw new Error("invalid_json");
  }

  return parsed as Record<string, unknown>;
}

function stringifyValue(value: Record<string, unknown>) {
  return JSON.stringify(value);
}

function syncTenantListItem(tenant: TenantRead) {
  tenants.value = tenants.value.map((entry) =>
    entry.id === tenant.id
      ? {
          ...entry,
          name: tenant.name,
          status: tenant.status,
          version_no: tenant.version_no,
        }
      : entry,
  );
}

function handleError(error: unknown) {
  if (error instanceof CoreAdminApiError) {
    const messageKey =
      API_ERROR_KEYS[error.messageKey as keyof typeof API_ERROR_KEYS] ?? "coreAdmin.feedback.unexpected";

    setFeedback("danger", t("coreAdmin.feedback.error"), t(messageKey as never));
    return;
  }

  if (error instanceof Error && error.message === "invalid_json") {
    setFeedback("danger", t("coreAdmin.feedback.error"), t("coreAdmin.feedback.invalidJson"));
    return;
  }

  setFeedback("danger", t("coreAdmin.feedback.error"), t("coreAdmin.feedback.unexpected"));
}

watch(
  [tenantFilter, selectedTenantId, tenantScopeInput, () => effectiveRole.value],
  () => {
    syncRouteState();

    if (effectiveRole.value === "tenant_admin") {
      tenantScopeInput.value = scopeState.value.scopeFieldValue;
    }
  },
);

watch(
  () => selectedTenantId.value,
  async (tenantId, previousTenantId) => {
    if (!tenantId || tenantId === previousTenantId) {
      return;
    }

    await loadTenantContext(tenantId);
  },
);

watch(
  () => effectiveRole.value,
  async () => {
    clearFeedback();
    tenantScopeInput.value = scopeState.value.scopeFieldValue;

    selectedTenantId.value =
      effectiveRole.value === "tenant_admin" ? actorTenantId.value ?? "" : selectedTenantId.value;
    await refreshAll();
  },
);

onMounted(async () => {
  authStore.syncFromPrimarySession();
  if (effectiveRole.value === "tenant_admin" && effectiveAccessToken.value && !authStore.sessionUser) {
    try {
      await authStore.loadCurrentSession();
    } catch {
      // keep current empty-state feedback path
    }
  }
  tenantScopeInput.value = scopeState.value.scopeFieldValue;
  resetBranchDraft();
  resetMandateDraft();
  resetSettingDraft();
  await refreshAll();
});
</script>

<style scoped>
.core-admin-page {
  display: grid;
  gap: 1.25rem;
  min-width: 0;
}

.core-admin-scope-card,
.core-admin-panel,
.core-admin-empty-state {
  min-width: 0;
  background: var(--sp-color-surface-panel);
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 24px;
  box-shadow: var(--sp-shadow-card);
}

.core-admin-scope-card,
.core-admin-panel {
  padding: 1.25rem;
}

.core-admin-scope-card__row {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 1rem;
  min-width: 0;
}

.core-admin-scope-card__row > .field-stack {
  flex: 1 1 18rem;
}

.core-admin-scope-card--embedded {
  margin-bottom: 0.25rem;
}

.core-admin-grid {
  display: grid;
  grid-template-columns: minmax(320px, 0.85fr) minmax(0, 1.35fr);
  gap: 1.25rem;
  align-items: start;
  min-width: 0;
}

.core-admin-detail {
  gap: 1.1rem;
}

.core-admin-panel,
.core-admin-section {
  display: grid;
  gap: 1rem;
  min-width: 0;
}

.core-admin-panel__header,
.core-admin-record,
.core-admin-lifecycle {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  min-width: 0;
}

.core-admin-feedback {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  min-width: 0;
  padding: 1rem 1.2rem;
  border-radius: 20px;
  border: 1px solid var(--sp-color-border-soft);
  background: var(--sp-color-surface-card);
  box-shadow: var(--sp-shadow-card);
}

.core-admin-feedback[data-tone="success"] {
  border-color: color-mix(in srgb, var(--sp-color-success) 35%, var(--sp-color-border-soft));
}

.core-admin-feedback[data-tone="danger"] {
  border-color: color-mix(in srgb, var(--sp-color-danger) 35%, var(--sp-color-border-soft));
}

.core-admin-feedback strong,
.core-admin-record strong {
  display: block;
}

.core-admin-feedback span,
.core-admin-record span,
.core-admin-list-empty,
.field-help {
  color: var(--sp-color-text-secondary);
}

.core-admin-feedback button,
.core-admin-record__actions button {
  border: 0;
  background: transparent;
  color: var(--sp-color-primary-strong);
  font-weight: 700;
  cursor: pointer;
}

.core-admin-list {
  display: grid;
  gap: 0.75rem;
  min-width: 0;
}

.core-admin-row,
.core-admin-record {
  min-width: 0;
  padding: 0.9rem 1rem;
  border-radius: 18px;
  border: 1px solid var(--sp-color-border-soft);
  background: var(--sp-color-surface-card);
}

.core-admin-row {
  width: 100%;
  text-align: left;
  cursor: pointer;
  transition:
    transform 0.2s ease,
    border-color 0.2s ease;
}

.core-admin-row.selected,
.core-admin-row:hover {
  transform: translateY(-1px);
  border-color: color-mix(in srgb, var(--sp-color-primary) 40%, var(--sp-color-border-soft));
}

.core-admin-record__actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 0.55rem;
  min-width: 0;
}

.core-admin-version {
  font-size: 0.82rem;
  color: var(--sp-color-text-secondary);
}

.core-admin-form {
  display: grid;
  gap: 1rem;
  padding-top: 0.25rem;
  min-width: 0;
}

.core-admin-form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.9rem;
  min-width: 0;
}

.field-stack {
  display: grid;
  gap: 0.42rem;
  font-size: 0.9rem;
  min-width: 0;
}

.field-stack--wide {
  grid-column: 1 / -1;
}

.field-stack input,
.field-stack select,
.field-stack textarea {
  width: 100%;
  max-width: 100%;
  min-width: 0;
  box-sizing: border-box;
  border-radius: 14px;
  border: 1px solid var(--sp-color-border-soft);
  background: var(--sp-color-surface-card);
  color: var(--sp-color-text-primary);
  padding: 0.78rem 0.9rem;
  font: inherit;
}

.field-stack input:disabled {
  opacity: 0.72;
  cursor: not-allowed;
}

.field-help {
  margin: 0;
  font-size: 0.85rem;
}

.core-admin-empty-state {
  padding: 1.4rem;
}

@media (max-width: 1180px) {
  .core-admin-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .core-admin-form-grid {
    grid-template-columns: 1fr;
  }

  .core-admin-panel__header,
  .core-admin-scope-card__row,
  .core-admin-record,
  .core-admin-lifecycle,
  .core-admin-feedback {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
