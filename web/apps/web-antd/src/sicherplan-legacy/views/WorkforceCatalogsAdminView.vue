<template>
  <section class="employee-catalogs-page">
    <section v-if="!embedded" class="module-card employee-catalogs-hero">
      <div>
        <p class="eyebrow">{{ t("employeeAdmin.catalogs.eyebrow") }}</p>
        <h2>{{ t("employeeAdmin.catalogs.title") }}</h2>
        <p class="employee-catalogs-lead">{{ t("employeeAdmin.catalogs.pageLead") }}</p>
      </div>
    </section>

    <div v-if="!embedded && isPlatformAdmin" class="module-card employee-catalogs-scope">
      <label class="field-stack">
        <span>{{ t("employeeAdmin.scope.label") }}</span>
        <input v-model="tenantScopeInput" :disabled="!isPlatformAdmin" :placeholder="t('employeeAdmin.scope.placeholder')" />
      </label>
      <p class="field-help">{{ t("employeeAdmin.scope.help") }}</p>
      <div class="cta-row">
        <button class="cta-button" type="button" @click="rememberScope">
          {{ t("employeeAdmin.actions.rememberScope") }}
        </button>
        <button class="cta-button cta-secondary" type="button" :disabled="!canRead" @click="refreshCatalogs">
          {{ t("employeeAdmin.actions.refresh") }}
        </button>
      </div>
    </div>

    <section v-if="isSessionResolving && !resolvedTenantScopeId" class="module-card employee-catalogs-empty">
      <p class="eyebrow">{{ t("employeeAdmin.scope.reconcilingTitle") }}</p>
      <h3>{{ t("employeeAdmin.scope.reconcilingBody") }}</h3>
    </section>

    <section v-else-if="!resolvedTenantScopeId" class="module-card employee-catalogs-empty">
      <p class="eyebrow">{{ t("employeeAdmin.scope.missingTitle") }}</p>
      <h3>{{ t("employeeAdmin.scope.missingBody") }}</h3>
    </section>

    <section v-else-if="!canRead" class="module-card employee-catalogs-empty">
      <p class="eyebrow">{{ t("employeeAdmin.permission.missingTitle") }}</p>
      <h3>{{ t("employeeAdmin.permission.missingBody") }}</h3>
    </section>

    <SicherPlanLoadingOverlay
      v-else
      :aria-label="workspaceLoadingText"
      :busy="workspaceBusy"
      :text="workspaceLoadingText"
      busy-testid="workforce-catalogs-loading-overlay"
    >
      <div class="employee-catalogs-grid" data-testid="workforce-catalogs-layout">
        <section class="module-card employee-catalogs-panel" data-testid="workforce-function-types-section">
          <div class="employee-catalogs-panel__header">
            <div>
              <p class="eyebrow">{{ t("employeeAdmin.catalogs.functionTypesEyebrow") }}</p>
              <h3>{{ t("employeeAdmin.catalogs.functionTypesTitle") }}</h3>
            </div>
            <StatusBadge :status="loading.list ? 'inactive' : 'active'" />
          </div>
          <p class="field-help">{{ t("employeeAdmin.catalogs.functionTypesLead") }}</p>

          <div v-if="functionTypes.length" class="employee-catalogs-record-list">
            <article
              v-for="row in functionTypes"
              :key="row.id"
              class="employee-catalogs-record"
              :class="{ selected: row.id === editingFunctionTypeId }"
              :data-testid="`workforce-function-type-record-${row.id}`"
            >
              <button
                type="button"
                class="employee-catalogs-record__body"
                :data-testid="`workforce-function-type-select-${row.id}`"
                @click="editFunctionType(row)"
              >
                <strong>{{ row.code }} · {{ row.label }}</strong>
                <span class="employee-catalogs-record__meta">
                  {{ row.category || t("employeeAdmin.summary.none") }} ·
                  {{ row.is_active ? t("employeeAdmin.catalogs.activeLabel") : t("employeeAdmin.catalogs.inactiveLabel") }}
                </span>
              </button>
              <div class="employee-catalogs-record__actions">
                <StatusBadge :status="row.status" />
                <button
                  class="cta-button cta-secondary"
                  type="button"
                  :disabled="!canManageCatalogs"
                  :data-testid="`workforce-function-type-edit-${row.id}`"
                  @click="editFunctionType(row)"
                >
                  {{ t("employeeAdmin.actions.editFunctionType") }}
                </button>
              </div>
            </article>
          </div>
          <p v-else class="employee-catalogs-empty-copy">{{ t("employeeAdmin.catalogs.functionTypesEmpty") }}</p>

          <form class="employee-catalogs-form" @submit.prevent="submitFunctionTypeCatalog">
            <div class="employee-catalogs-panel__header">
              <div>
                <p class="eyebrow">
                  {{ editingFunctionTypeId ? t("employeeAdmin.catalogs.functionTypeEditorEditEyebrow") : t("employeeAdmin.catalogs.functionTypeEditorCreateEyebrow") }}
                </p>
                <h4>
                  {{ editingFunctionTypeId ? t("employeeAdmin.catalogs.functionTypeEditorEditTitle") : t("employeeAdmin.catalogs.functionTypeEditorCreateTitle") }}
                </h4>
              </div>
            </div>
            <div class="employee-catalogs-form-grid">
              <label class="field-stack">
                <span>{{ t("employeeAdmin.catalogs.fields.code") }}</span>
                <input v-model="functionTypeDraft.code" :disabled="!canManageCatalogs" />
              </label>
              <label class="field-stack">
                <span>{{ t("employeeAdmin.catalogs.fields.label") }}</span>
                <input v-model="functionTypeDraft.label" :disabled="!canManageCatalogs" />
              </label>
              <label class="field-stack">
                <span>{{ t("employeeAdmin.catalogs.fields.category") }}</span>
                <input v-model="functionTypeDraft.category" :disabled="!canManageCatalogs" />
              </label>
              <label class="field-stack field-stack--wide">
                <span>{{ t("employeeAdmin.catalogs.fields.description") }}</span>
                <textarea v-model="functionTypeDraft.description" :disabled="!canManageCatalogs" rows="3" />
              </label>
            </div>
            <label class="employee-catalogs-checkbox">
              <input v-model="functionTypeDraft.planning_relevant" :disabled="!canManageCatalogs" type="checkbox" />
              <span>{{ t("employeeAdmin.catalogs.fields.planningRelevant") }}</span>
            </label>
            <label class="employee-catalogs-checkbox">
              <input v-model="functionTypeDraft.is_active" :disabled="!canManageCatalogs" type="checkbox" />
              <span>{{ t("employeeAdmin.catalogs.fields.isActive") }}</span>
            </label>
            <div class="cta-row">
              <button class="cta-button" type="submit" :disabled="!canManageCatalogs">
                {{ editingFunctionTypeId ? t("employeeAdmin.actions.saveFunctionType") : t("employeeAdmin.actions.createFunctionType") }}
              </button>
              <button class="cta-button cta-secondary" type="button" @click="resetFunctionTypeDraft">
                {{ t("employeeAdmin.actions.resetFunctionType") }}
              </button>
            </div>
          </form>
        </section>

        <section class="module-card employee-catalogs-panel" data-testid="workforce-qualification-types-section">
          <div class="employee-catalogs-panel__header">
            <div>
              <p class="eyebrow">{{ t("employeeAdmin.catalogs.qualificationTypesEyebrow") }}</p>
              <h3>{{ t("employeeAdmin.catalogs.qualificationTypesTitle") }}</h3>
            </div>
            <StatusBadge :status="loading.list ? 'inactive' : 'active'" />
          </div>
          <p class="field-help">{{ t("employeeAdmin.catalogs.qualificationTypesLead") }}</p>

          <div v-if="qualificationTypes.length" class="employee-catalogs-record-list">
            <article
              v-for="row in qualificationTypes"
              :key="row.id"
              class="employee-catalogs-record"
              :class="{ selected: row.id === editingQualificationTypeId }"
              :data-testid="`workforce-qualification-type-record-${row.id}`"
            >
              <button
                type="button"
                class="employee-catalogs-record__body"
                :data-testid="`workforce-qualification-type-select-${row.id}`"
                @click="editQualificationTypeCatalog(row)"
              >
                <strong>{{ row.code }} · {{ row.label }}</strong>
                <span class="employee-catalogs-record__meta">
                  {{ row.category || t("employeeAdmin.summary.none") }} ·
                  {{ row.is_active ? t("employeeAdmin.catalogs.activeLabel") : t("employeeAdmin.catalogs.inactiveLabel") }}
                </span>
              </button>
              <div class="employee-catalogs-record__actions">
                <StatusBadge :status="row.status" />
                <button
                  class="cta-button cta-secondary"
                  type="button"
                  :disabled="!canManageCatalogs"
                  :data-testid="`workforce-qualification-type-edit-${row.id}`"
                  @click="editQualificationTypeCatalog(row)"
                >
                  {{ t("employeeAdmin.actions.editQualificationType") }}
                </button>
              </div>
            </article>
          </div>
          <p v-else class="employee-catalogs-empty-copy">{{ t("employeeAdmin.catalogs.qualificationTypesEmpty") }}</p>

          <form class="employee-catalogs-form" @submit.prevent="submitQualificationTypeCatalog">
            <div class="employee-catalogs-panel__header">
              <div>
                <p class="eyebrow">
                  {{ editingQualificationTypeId ? t("employeeAdmin.catalogs.qualificationTypeEditorEditEyebrow") : t("employeeAdmin.catalogs.qualificationTypeEditorCreateEyebrow") }}
                </p>
                <h4>
                  {{ editingQualificationTypeId ? t("employeeAdmin.catalogs.qualificationTypeEditorEditTitle") : t("employeeAdmin.catalogs.qualificationTypeEditorCreateTitle") }}
                </h4>
              </div>
            </div>
            <div class="employee-catalogs-form-grid">
              <label class="field-stack">
                <span>{{ t("employeeAdmin.catalogs.fields.code") }}</span>
                <input v-model="qualificationTypeCatalogDraft.code" :disabled="!canManageCatalogs" />
              </label>
              <label class="field-stack">
                <span>{{ t("employeeAdmin.catalogs.fields.label") }}</span>
                <input v-model="qualificationTypeCatalogDraft.label" :disabled="!canManageCatalogs" />
              </label>
              <label class="field-stack">
                <span>{{ t("employeeAdmin.catalogs.fields.category") }}</span>
                <input v-model="qualificationTypeCatalogDraft.category" :disabled="!canManageCatalogs" />
              </label>
              <label class="field-stack">
                <span>{{ t("employeeAdmin.catalogs.fields.defaultValidityDays") }}</span>
                <input
                  v-model="qualificationTypeCatalogDraft.default_validity_days"
                  :disabled="!canManageCatalogs"
                  inputmode="numeric"
                />
              </label>
              <label class="field-stack field-stack--wide">
                <span>{{ t("employeeAdmin.catalogs.fields.description") }}</span>
                <textarea v-model="qualificationTypeCatalogDraft.description" :disabled="!canManageCatalogs" rows="3" />
              </label>
            </div>
            <div class="employee-catalogs-form-grid">
              <label class="employee-catalogs-checkbox">
                <input v-model="qualificationTypeCatalogDraft.is_active" :disabled="!canManageCatalogs" type="checkbox" />
                <span>{{ t("employeeAdmin.catalogs.fields.isActive") }}</span>
              </label>
              <label class="employee-catalogs-checkbox">
                <input v-model="qualificationTypeCatalogDraft.planning_relevant" :disabled="!canManageCatalogs" type="checkbox" />
                <span>{{ t("employeeAdmin.catalogs.fields.planningRelevant") }}</span>
              </label>
              <label class="employee-catalogs-checkbox">
                <input v-model="qualificationTypeCatalogDraft.compliance_relevant" :disabled="!canManageCatalogs" type="checkbox" />
                <span>{{ t("employeeAdmin.catalogs.fields.complianceRelevant") }}</span>
              </label>
              <label class="employee-catalogs-checkbox">
                <input v-model="qualificationTypeCatalogDraft.expiry_required" :disabled="!canManageCatalogs" type="checkbox" />
                <span>{{ t("employeeAdmin.catalogs.fields.expiryRequired") }}</span>
              </label>
              <label class="employee-catalogs-checkbox">
                <input v-model="qualificationTypeCatalogDraft.proof_required" :disabled="!canManageCatalogs" type="checkbox" />
                <span>{{ t("employeeAdmin.catalogs.fields.proofRequired") }}</span>
              </label>
            </div>
            <div class="cta-row">
              <button class="cta-button" type="submit" :disabled="!canManageCatalogs">
                {{ editingQualificationTypeId ? t("employeeAdmin.actions.saveQualificationType") : t("employeeAdmin.actions.createQualificationType") }}
              </button>
              <button class="cta-button cta-secondary" type="button" @click="resetQualificationTypeCatalogDraft">
                {{ t("employeeAdmin.actions.resetQualificationType") }}
              </button>
            </div>
          </form>
        </section>
      </div>
    </SicherPlanLoadingOverlay>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";

import {
  createFunctionType,
  createQualificationType,
  EmployeeAdminApiError,
  listFunctionTypes,
  listQualificationTypes,
  type FunctionTypeCreatePayload,
  type FunctionTypeRead,
  type FunctionTypeUpdatePayload,
  type QualificationTypeCreatePayload,
  type QualificationTypeRead,
  type QualificationTypeUpdatePayload,
  updateFunctionType,
  updateQualificationType,
} from "@/api/employeeAdmin";
import SicherPlanLoadingOverlay from "@/components/SicherPlanLoadingOverlay.vue";
import StatusBadge from "@/components/StatusBadge.vue";
import { useSicherPlanFeedback } from "@/composables/useSicherPlanFeedback";
import {
  buildEmployeeFunctionTypePayload,
  buildEmployeeQualificationTypePayload,
  deriveEmployeeActionState,
  mapEmployeeApiMessage,
  validateEmployeeFunctionTypeDraft,
  validateEmployeeQualificationTypeDraft,
} from "@/features/employees/employeeAdmin.helpers.js";
import { useI18n } from "@/i18n";
import { useAuthStore } from "@/stores/auth";

withDefaults(defineProps<{ embedded?: boolean }>(), {
  embedded: false,
});

const { t } = useI18n();
const authStore = useAuthStore();
const { showFeedbackToast } = useSicherPlanFeedback();

const loading = reactive({
  action: false,
  list: false,
});

const tenantScopeInput = ref(authStore.effectiveTenantScopeId || authStore.tenantScopeId || "");
const functionTypes = ref<FunctionTypeRead[]>([]);
const qualificationTypes = ref<QualificationTypeRead[]>([]);
const editingFunctionTypeId = ref("");
const editingQualificationTypeId = ref("");

const functionTypeDraft = reactive({
  code: "",
  label: "",
  category: "",
  description: "",
  is_active: true,
  planning_relevant: true,
});

const qualificationTypeCatalogDraft = reactive({
  code: "",
  label: "",
  category: "",
  description: "",
  is_active: true,
  planning_relevant: true,
  compliance_relevant: false,
  expiry_required: false,
  default_validity_days: "",
  proof_required: false,
});

const effectiveRole = computed(() => authStore.effectiveRole);
const isPlatformAdmin = computed(() => effectiveRole.value === "platform_admin");
const actionState = computed(() => deriveEmployeeActionState(effectiveRole.value, null));
const canRead = computed(() => actionState.value.canRead);
const canManageCatalogs = computed(() => actionState.value.canManageCatalogs);
const isSessionResolving = computed(() => authStore.isSessionResolving);
const resolvedTenantScopeId = computed(() => authStore.effectiveTenantScopeId);
const workspaceBusy = computed(() => isSessionResolving.value || loading.action);
const workspaceLoadingText = computed(() =>
  workspaceBusy.value
    ? t(isSessionResolving.value ? "workspace.loading.reconcilingSession" : "workspace.loading.processing")
    : "",
);
const selectedFunctionTypeCatalog = computed(
  () => functionTypes.value.find((row) => row.id === editingFunctionTypeId.value) ?? null,
);
const selectedQualificationTypeCatalog = computed(
  () => qualificationTypes.value.find((row) => row.id === editingQualificationTypeId.value) ?? null,
);

function setFeedback(tone: "error" | "neutral" | "success", title: string, message: string) {
  showFeedbackToast({
    key: "workforce-catalogs-feedback",
    title,
    message,
    tone,
  });
}

function rememberScope() {
  authStore.setTenantScopeId(tenantScopeInput.value);
  void refreshCatalogs();
}

function resetFunctionTypeDraft() {
  functionTypeDraft.code = "";
  functionTypeDraft.label = "";
  functionTypeDraft.category = "";
  functionTypeDraft.description = "";
  functionTypeDraft.is_active = true;
  functionTypeDraft.planning_relevant = true;
  editingFunctionTypeId.value = "";
}

function editFunctionType(row: FunctionTypeRead) {
  editingFunctionTypeId.value = row.id;
  functionTypeDraft.code = row.code;
  functionTypeDraft.label = row.label;
  functionTypeDraft.category = row.category || "";
  functionTypeDraft.description = row.description || "";
  functionTypeDraft.is_active = row.is_active;
  functionTypeDraft.planning_relevant = row.planning_relevant;
}

function resetQualificationTypeCatalogDraft() {
  qualificationTypeCatalogDraft.code = "";
  qualificationTypeCatalogDraft.label = "";
  qualificationTypeCatalogDraft.category = "";
  qualificationTypeCatalogDraft.description = "";
  qualificationTypeCatalogDraft.is_active = true;
  qualificationTypeCatalogDraft.planning_relevant = true;
  qualificationTypeCatalogDraft.compliance_relevant = false;
  qualificationTypeCatalogDraft.expiry_required = false;
  qualificationTypeCatalogDraft.default_validity_days = "";
  qualificationTypeCatalogDraft.proof_required = false;
  editingQualificationTypeId.value = "";
}

function editQualificationTypeCatalog(row: QualificationTypeRead) {
  editingQualificationTypeId.value = row.id;
  qualificationTypeCatalogDraft.code = row.code;
  qualificationTypeCatalogDraft.label = row.label;
  qualificationTypeCatalogDraft.category = row.category || "";
  qualificationTypeCatalogDraft.description = row.description || "";
  qualificationTypeCatalogDraft.is_active = row.is_active;
  qualificationTypeCatalogDraft.planning_relevant = row.planning_relevant;
  qualificationTypeCatalogDraft.compliance_relevant = row.compliance_relevant;
  qualificationTypeCatalogDraft.expiry_required = row.expiry_required;
  qualificationTypeCatalogDraft.default_validity_days = row.default_validity_days == null ? "" : String(row.default_validity_days);
  qualificationTypeCatalogDraft.proof_required = row.proof_required;
}

async function refreshCatalogs() {
  if (!resolvedTenantScopeId.value || !authStore.accessToken || !canRead.value) {
    functionTypes.value = [];
    qualificationTypes.value = [];
    return;
  }
  loading.list = true;
  try {
    const [functionTypeRows, qualificationTypeRows] = await Promise.all([
      listFunctionTypes(resolvedTenantScopeId.value, authStore.accessToken),
      listQualificationTypes(resolvedTenantScopeId.value, authStore.accessToken),
    ]);
    functionTypes.value = functionTypeRows;
    qualificationTypes.value = qualificationTypeRows;
    if (editingFunctionTypeId.value && !functionTypeRows.some((row) => row.id === editingFunctionTypeId.value)) {
      resetFunctionTypeDraft();
    }
    if (editingQualificationTypeId.value && !qualificationTypeRows.some((row) => row.id === editingQualificationTypeId.value)) {
      resetQualificationTypeCatalogDraft();
    }
  } catch (error) {
    functionTypes.value = [];
    qualificationTypes.value = [];
    const key = error instanceof EmployeeAdminApiError ? mapEmployeeApiMessage(error.messageKey) : "employeeAdmin.feedback.error";
    setFeedback("error", t("employeeAdmin.feedback.titleError"), t(key as never));
  } finally {
    loading.list = false;
  }
}

async function submitFunctionTypeCatalog() {
  if (!resolvedTenantScopeId.value || !authStore.accessToken || !canManageCatalogs.value) {
    return;
  }
  const validationKey = validateEmployeeFunctionTypeDraft(functionTypeDraft);
  if (validationKey) {
    setFeedback("error", t("employeeAdmin.feedback.titleError"), t(validationKey as never));
    return;
  }
  const createPayload: FunctionTypeCreatePayload = buildEmployeeFunctionTypePayload(functionTypeDraft, {
    tenantId: resolvedTenantScopeId.value,
  });
  loading.action = true;
  try {
    if (editingFunctionTypeId.value && selectedFunctionTypeCatalog.value) {
      const updatePayload: FunctionTypeUpdatePayload = {
        code: createPayload.code,
        label: createPayload.label,
        category: createPayload.category,
        description: createPayload.description,
        is_active: createPayload.is_active,
        planning_relevant: createPayload.planning_relevant,
        version_no: selectedFunctionTypeCatalog.value.version_no,
      };
      await updateFunctionType(resolvedTenantScopeId.value, editingFunctionTypeId.value, authStore.accessToken, updatePayload);
    } else {
      await createFunctionType(resolvedTenantScopeId.value, authStore.accessToken, createPayload);
    }
    resetFunctionTypeDraft();
    await refreshCatalogs();
    setFeedback("success", t("employeeAdmin.feedback.titleSuccess"), t("employeeAdmin.feedback.functionTypeSaved"));
  } catch (error) {
    const key = error instanceof EmployeeAdminApiError ? mapEmployeeApiMessage(error.messageKey) : "employeeAdmin.feedback.error";
    setFeedback("error", t("employeeAdmin.feedback.titleError"), t(key as never));
  } finally {
    loading.action = false;
  }
}

async function submitQualificationTypeCatalog() {
  if (!resolvedTenantScopeId.value || !authStore.accessToken || !canManageCatalogs.value) {
    return;
  }
  const validationKey = validateEmployeeQualificationTypeDraft(qualificationTypeCatalogDraft);
  if (validationKey) {
    setFeedback("error", t("employeeAdmin.feedback.titleError"), t(validationKey as never));
    return;
  }
  const createPayload: QualificationTypeCreatePayload = buildEmployeeQualificationTypePayload(qualificationTypeCatalogDraft, {
    tenantId: resolvedTenantScopeId.value,
  });
  loading.action = true;
  try {
    if (editingQualificationTypeId.value && selectedQualificationTypeCatalog.value) {
      const updatePayload: QualificationTypeUpdatePayload = {
        code: createPayload.code,
        label: createPayload.label,
        category: createPayload.category,
        description: createPayload.description,
        is_active: createPayload.is_active,
        planning_relevant: createPayload.planning_relevant,
        compliance_relevant: createPayload.compliance_relevant,
        expiry_required: createPayload.expiry_required,
        default_validity_days: createPayload.default_validity_days,
        proof_required: createPayload.proof_required,
        version_no: selectedQualificationTypeCatalog.value.version_no,
      };
      await updateQualificationType(
        resolvedTenantScopeId.value,
        editingQualificationTypeId.value,
        authStore.accessToken,
        updatePayload,
      );
    } else {
      await createQualificationType(resolvedTenantScopeId.value, authStore.accessToken, createPayload);
    }
    resetQualificationTypeCatalogDraft();
    await refreshCatalogs();
    setFeedback("success", t("employeeAdmin.feedback.titleSuccess"), t("employeeAdmin.feedback.qualificationTypeSaved"));
  } catch (error) {
    const key = error instanceof EmployeeAdminApiError ? mapEmployeeApiMessage(error.messageKey) : "employeeAdmin.feedback.error";
    setFeedback("error", t("employeeAdmin.feedback.titleError"), t(key as never));
  } finally {
    loading.action = false;
  }
}

watch(
  () => [authStore.effectiveRole, authStore.effectiveTenantScopeId] as const,
  () => {
    if (!isPlatformAdmin.value) {
      tenantScopeInput.value = authStore.effectiveTenantScopeId || authStore.tenantScopeId;
    }
  },
  { immediate: true },
);

onMounted(async () => {
  authStore.syncFromPrimarySession();
  try {
    await authStore.ensureSessionReady();
  } catch {
    // store handles redirect/recovery
  }
  tenantScopeInput.value = authStore.effectiveTenantScopeId || authStore.tenantScopeId;
  await refreshCatalogs();
});
</script>

<style scoped>
.employee-catalogs-page,
.employee-catalogs-grid,
.employee-catalogs-record-list,
.employee-catalogs-form-grid {
  display: grid;
  gap: 1rem;
  min-width: 0;
}

.employee-catalogs-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  align-items: start;
}

.employee-catalogs-panel,
.employee-catalogs-empty,
.employee-catalogs-hero,
.employee-catalogs-scope {
  display: grid;
  gap: 1rem;
}

.employee-catalogs-panel__header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: start;
}

.employee-catalogs-panel__header > * {
  min-width: 0;
}

.employee-catalogs-record {
  display: grid;
  gap: 0.75rem;
  padding: 1rem;
  border-radius: 18px;
  border: 1px solid var(--sp-color-border-soft);
  background: var(--sp-color-surface, #fff);
}

.employee-catalogs-record.selected {
  border-color: var(--sp-color-primary, rgb(40, 170, 170));
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--sp-color-primary, rgb(40, 170, 170)) 35%, transparent);
}

.employee-catalogs-record__body {
  display: grid;
  gap: 0.35rem;
  border: 0;
  padding: 0;
  margin: 0;
  background: transparent;
  text-align: left;
  cursor: pointer;
}

.employee-catalogs-record__meta {
  color: var(--sp-color-text-muted, #667085);
  font-size: 0.95rem;
}

.employee-catalogs-record__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  align-items: center;
}

.employee-catalogs-form {
  display: grid;
  gap: 1rem;
  padding: 1rem 1.1rem;
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 18px;
  background: color-mix(in srgb, var(--sp-color-surface-page) 76%, white 24%);
  min-width: 0;
}

.employee-catalogs-form .employee-catalogs-panel__header {
  gap: 0.5rem;
}

.employee-catalogs-form-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.85rem 1rem;
}

.employee-catalogs-form-grid > * {
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
  transition:
    border-color 0.18s ease,
    box-shadow 0.18s ease,
    background-color 0.18s ease;
}

.field-stack textarea {
  min-height: 6.5rem;
  resize: vertical;
}

.field-stack input:focus,
.field-stack select:focus,
.field-stack textarea:focus {
  outline: none;
  border-color: rgb(40 170 170 / 55%);
  box-shadow: 0 0 0 3px rgb(40 170 170 / 14%);
}

.field-stack input:disabled,
.field-stack select:disabled,
.field-stack textarea:disabled {
  opacity: 0.72;
  cursor: not-allowed;
}

.employee-catalogs-checkbox {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  min-width: 0;
  padding: 0.2rem 0;
  color: var(--sp-color-text-secondary);
}

.employee-catalogs-checkbox input[type='checkbox'] {
  width: 1rem;
  height: 1rem;
  margin: 0;
  flex: 0 0 auto;
  accent-color: var(--sp-color-primary);
}

.employee-catalogs-checkbox span {
  min-width: 0;
}

.employee-catalogs-form :deep(.cta-row) {
  align-items: center;
  gap: 0.75rem;
  margin-top: 0.15rem;
}

.employee-catalogs-form :deep(.cta-button) {
  justify-content: center;
}

.employee-catalogs-empty-copy,
.employee-catalogs-lead {
  color: var(--sp-color-text-muted, #667085);
}

@media (max-width: 1100px) {
  .employee-catalogs-grid {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (max-width: 820px) {
  .employee-catalogs-form-grid {
    grid-template-columns: 1fr;
  }

  .employee-catalogs-form :deep(.cta-row) {
    align-items: stretch;
  }
}
</style>
