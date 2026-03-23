<template>
  <section class="planning-admin-page">
    <section class="module-card planning-admin-hero">
      <div>
        <p class="eyebrow">{{ tp("eyebrow") }}</p>
        <h2>{{ tp("title") }}</h2>
        <p class="planning-admin-lead">{{ tp("lead") }}</p>
        <div class="planning-admin-meta">
          <span class="planning-admin-meta__pill">{{ tp("read") }}: {{ canRead ? "on" : "off" }}</span>
          <span class="planning-admin-meta__pill">{{ tp("write") }}: {{ canWrite ? "on" : "off" }}</span>
        </div>
      </div>

      <div class="module-card planning-admin-scope">
        <label class="field-stack">
          <span>{{ tp("scopeLabel") }}</span>
          <input v-model="tenantScopeInput" :disabled="!isPlatformAdmin" :placeholder="tp('scopePlaceholder')" />
        </label>
        <p class="field-help">{{ tp("scopeHelp") }}</p>
        <div class="cta-row">
          <button class="cta-button" type="button" @click="rememberScope">{{ tp("actionsRememberScope") }}</button>
          <button class="cta-button cta-secondary" type="button" :disabled="!canRead" @click="refreshRecords">
            {{ tp("actionsRefresh") }}
          </button>
        </div>
      </div>
    </section>

    <section v-if="feedback.message" class="planning-admin-feedback" :data-tone="feedback.tone">
      <div>
        <strong>{{ feedback.title }}</strong>
        <span>{{ feedback.message }}</span>
      </div>
      <button type="button" @click="clearFeedback">{{ tp("actionsClearFeedback") }}</button>
    </section>

    <section v-if="!resolvedTenantScopeId" class="module-card planning-admin-empty">
      <p class="eyebrow">{{ tp("scopeMissingTitle") }}</p>
      <h3>{{ tp("scopeMissingBody") }}</h3>
    </section>

    <section v-else-if="!canRead" class="module-card planning-admin-empty">
      <p class="eyebrow">{{ tp("permissionMissingTitle") }}</p>
      <h3>{{ tp("permissionMissingBody") }}</h3>
    </section>

    <div v-else class="planning-admin-grid">
      <section class="module-card planning-admin-panel">
        <div class="planning-admin-panel__header">
          <div>
            <p class="eyebrow">{{ tp("listTitle") }}</p>
            <h3>{{ entityLabel }}</h3>
          </div>
          <StatusBadge :status="loading.list ? 'inactive' : 'active'" />
        </div>

        <div class="planning-admin-form-grid">
          <label class="field-stack">
            <span>{{ tp("entityLabel") }}</span>
            <select v-model="entityKey" @change="changeEntity">
              <option v-for="option in entityOptions" :key="option" :value="option">{{ entityName(option) }}</option>
            </select>
          </label>
          <label class="field-stack">
            <span>{{ tp("search") }}</span>
            <input v-model="filters.search" :placeholder="tp('searchPlaceholder')" />
          </label>
          <label class="field-stack">
            <span>{{ tp("customerId") }}</span>
            <input v-model="filters.customer_id" />
          </label>
          <label class="field-stack">
            <span>{{ tp("status") }}</span>
            <select v-model="filters.lifecycle_status">
              <option value="">{{ tp("allStatuses") }}</option>
              <option value="active">{{ tp("statusActive") }}</option>
              <option value="inactive">{{ tp("statusInactive") }}</option>
              <option value="archived">{{ tp("statusArchived") }}</option>
            </select>
          </label>
        </div>

        <label class="planning-admin-checkbox">
          <input v-model="filters.include_archived" type="checkbox" />
          <span>{{ tp("includeArchived") }}</span>
        </label>

        <div class="cta-row">
          <button class="cta-button" type="button" @click="refreshRecords">{{ tp("actionsSearch") }}</button>
          <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canCreate" @click="startCreateRecord">
            {{ tp("actionsNewRecord") }}
          </button>
        </div>

        <section class="planning-admin-import">
          <div class="planning-admin-panel__header">
            <div>
              <p class="eyebrow">{{ tp("importTitle") }}</p>
              <h3>{{ entityLabel }}</h3>
            </div>
          </div>
          <input type="file" accept=".csv,text/csv" :disabled="!actionState.canImport" @change="onImportSelected" />
          <div class="cta-row">
            <button class="cta-button cta-secondary" type="button" :disabled="!pendingImportFile || !actionState.canImport" @click="loadImportFile">
              {{ tp("actionsLoadImportFile") }}
            </button>
            <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canImport" @click="resetImportTemplate">
              {{ tp("actionsResetImportTemplate") }}
            </button>
          </div>
          <label class="field-stack">
            <span>{{ tp("importCsvLabel") }}</span>
            <textarea v-model="importDraft.csv_text" rows="6" :disabled="!actionState.canImport" />
          </label>
          <label class="planning-admin-checkbox">
            <input v-model="importDraft.continue_on_error" type="checkbox" :disabled="!actionState.canImport" />
            <span>{{ tp("importContinueOnError") }}</span>
          </label>
          <div class="cta-row">
            <button class="cta-button" type="button" :disabled="!actionState.canImport" @click="runImportDryRun">{{ tp("actionsImportDryRun") }}</button>
            <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canImport" @click="runImportExecute">{{ tp("actionsImportExecute") }}</button>
          </div>
          <p v-if="importDryRunResult" class="field-help">{{ tp("importDryRunSummary", { total: importDryRunResult.total_rows, invalid: importDryRunResult.invalid_rows }) }}</p>
          <p v-if="lastImportResult" class="field-help">{{ tp("importExecuteSummary", { total: lastImportResult.total_rows, created: lastImportResult.created_rows, updated: lastImportResult.updated_rows }) }}</p>
        </section>

        <div v-if="records.length" class="planning-admin-list">
          <button
            v-for="record in records"
            :key="record.id"
            type="button"
            class="planning-admin-row"
            :class="{ selected: record.id === selectedRecordId }"
            @click="selectRecord(record.id)"
          >
            <div>
              <strong>{{ recordTitle(record) }}</strong>
              <span>{{ record.customer_id || tp("none") }}</span>
            </div>
            <StatusBadge :status="record.status" />
          </button>
        </div>
        <p v-else class="planning-admin-list-empty">{{ tp("listEmpty") }}</p>
      </section>

      <section class="module-card planning-admin-panel planning-admin-detail">
        <div class="planning-admin-panel__header">
          <div>
            <p class="eyebrow">{{ tp("detailTitle") }}</p>
            <h3>{{ isCreatingRecord ? tp("newTitle") : selectedRecord ? recordTitle(selectedRecord) : tp("detailEmptyTitle") }}</h3>
          </div>
          <StatusBadge v-if="selectedRecord && !isCreatingRecord" :status="selectedRecord.status" />
        </div>

        <template v-if="isCreatingRecord || selectedRecord">
          <form class="planning-admin-form" @submit.prevent="submitRecord">
            <div class="planning-admin-form-grid">
              <label class="field-stack">
                <span>{{ tp("fieldsCustomerId") }}</span>
                <input v-model="draft.customer_id" required />
              </label>

              <template v-if="entityKey === 'requirement_type'">
                <label class="field-stack"><span>{{ tp("fieldsCode") }}</span><input v-model="draft.code" required /></label>
                <label class="field-stack"><span>{{ tp("fieldsLabel") }}</span><input v-model="draft.label" required /></label>
                <label class="field-stack"><span>{{ tp("fieldsDefaultPlanningMode") }}</span><input v-model="draft.default_planning_mode_code" required /></label>
              </template>

              <template v-if="entityKey === 'equipment_item'">
                <label class="field-stack"><span>{{ tp("fieldsCode") }}</span><input v-model="draft.code" required /></label>
                <label class="field-stack"><span>{{ tp("fieldsLabel") }}</span><input v-model="draft.label" required /></label>
                <label class="field-stack"><span>{{ tp("fieldsUnitOfMeasure") }}</span><input v-model="draft.unit_of_measure_code" required /></label>
              </template>

              <template v-if="entityKey === 'site'">
                <label class="field-stack"><span>{{ tp("fieldsSiteNo") }}</span><input v-model="draft.site_no" required /></label>
                <label class="field-stack"><span>{{ tp("fieldsName") }}</span><input v-model="draft.name" required /></label>
                <label class="field-stack"><span>{{ tp("fieldsAddressId") }}</span><input v-model="draft.address_id" /></label>
                <label class="field-stack"><span>{{ tp("fieldsTimezone") }}</span><input v-model="draft.timezone" /></label>
                <label class="field-stack"><span>{{ tp("fieldsLatitude") }}</span><input v-model="draft.latitude" type="number" step="0.000001" /></label>
                <label class="field-stack"><span>{{ tp("fieldsLongitude") }}</span><input v-model="draft.longitude" type="number" step="0.000001" /></label>
                <label class="planning-admin-checkbox planning-admin-checkbox--inline"><input v-model="draft.watchbook_enabled" type="checkbox" /><span>{{ tp("fieldsWatchbookEnabled") }}</span></label>
              </template>

              <template v-if="entityKey === 'event_venue'">
                <label class="field-stack"><span>{{ tp("fieldsVenueNo") }}</span><input v-model="draft.venue_no" required /></label>
                <label class="field-stack"><span>{{ tp("fieldsName") }}</span><input v-model="draft.name" required /></label>
                <label class="field-stack"><span>{{ tp("fieldsAddressId") }}</span><input v-model="draft.address_id" /></label>
                <label class="field-stack"><span>{{ tp("fieldsTimezone") }}</span><input v-model="draft.timezone" /></label>
                <label class="field-stack"><span>{{ tp("fieldsLatitude") }}</span><input v-model="draft.latitude" type="number" step="0.000001" /></label>
                <label class="field-stack"><span>{{ tp("fieldsLongitude") }}</span><input v-model="draft.longitude" type="number" step="0.000001" /></label>
              </template>

              <template v-if="entityKey === 'trade_fair'">
                <label class="field-stack"><span>{{ tp("fieldsFairNo") }}</span><input v-model="draft.fair_no" required /></label>
                <label class="field-stack"><span>{{ tp("fieldsName") }}</span><input v-model="draft.name" required /></label>
                <label class="field-stack"><span>{{ tp("fieldsVenueId") }}</span><input v-model="draft.venue_id" /></label>
                <label class="field-stack"><span>{{ tp("fieldsAddressId") }}</span><input v-model="draft.address_id" /></label>
                <label class="field-stack"><span>{{ tp("fieldsTimezone") }}</span><input v-model="draft.timezone" /></label>
                <label class="field-stack"><span>{{ tp("fieldsLatitude") }}</span><input v-model="draft.latitude" type="number" step="0.000001" /></label>
                <label class="field-stack"><span>{{ tp("fieldsLongitude") }}</span><input v-model="draft.longitude" type="number" step="0.000001" /></label>
                <label class="field-stack"><span>{{ tp("fieldsStartDate") }}</span><input v-model="draft.start_date" type="date" required /></label>
                <label class="field-stack"><span>{{ tp("fieldsEndDate") }}</span><input v-model="draft.end_date" type="date" required /></label>
              </template>

              <template v-if="entityKey === 'patrol_route'">
                <label class="field-stack"><span>{{ tp("fieldsRouteNo") }}</span><input v-model="draft.route_no" required /></label>
                <label class="field-stack"><span>{{ tp("fieldsName") }}</span><input v-model="draft.name" required /></label>
                <label class="field-stack"><span>{{ tp("fieldsSiteId") }}</span><input v-model="draft.site_id" /></label>
                <label class="field-stack"><span>{{ tp("fieldsMeetingAddressId") }}</span><input v-model="draft.meeting_address_id" /></label>
                <label class="field-stack"><span>{{ tp("fieldsStartPointText") }}</span><input v-model="draft.start_point_text" /></label>
                <label class="field-stack"><span>{{ tp("fieldsEndPointText") }}</span><input v-model="draft.end_point_text" /></label>
                <label class="field-stack"><span>{{ tp("fieldsTravelPolicyCode") }}</span><input v-model="draft.travel_policy_code" /></label>
              </template>

              <label class="field-stack field-stack--wide"><span>{{ tp("fieldsNotes") }}</span><textarea v-model="draft.notes" rows="4" /></label>
            </div>

            <div class="cta-row">
              <button class="cta-button" type="submit" :disabled="!actionState.canCreate && !actionState.canEdit">{{ tp("actionsSaveRecord") }}</button>
              <button class="cta-button cta-secondary" type="button" @click="resetDraft">{{ tp("actionsResetRecord") }}</button>
            </div>
          </form>

          <section v-if="entityKey === 'trade_fair' && selectedRecord && !isCreatingRecord" class="planning-admin-section">
            <div class="planning-admin-panel__header"><h3>{{ tp("zonesTitle") }}</h3></div>
            <div v-if="tradeFairZones.length" class="planning-admin-list">
              <button v-for="zone in tradeFairZones" :key="zone.id" type="button" class="planning-admin-row" @click="selectZone(zone)">
                <div><strong>{{ zone.zone_code }} · {{ zone.label }}</strong><span>{{ zone.zone_type_code }}</span></div>
                <StatusBadge :status="zone.status" />
              </button>
            </div>
            <p v-else class="planning-admin-list-empty">{{ tp("zonesEmpty") }}</p>
            <form class="planning-admin-form" @submit.prevent="submitZone">
              <div class="planning-admin-form-grid">
                <label class="field-stack"><span>{{ tp("fieldsZoneTypeCode") }}</span><input v-model="zoneDraft.zone_type_code" required /></label>
                <label class="field-stack"><span>{{ tp("fieldsZoneCode") }}</span><input v-model="zoneDraft.zone_code" required /></label>
                <label class="field-stack"><span>{{ tp("fieldsLabel") }}</span><input v-model="zoneDraft.label" required /></label>
                <label class="field-stack field-stack--wide"><span>{{ tp("fieldsNotes") }}</span><textarea v-model="zoneDraft.notes" rows="3" /></label>
              </div>
              <button class="cta-button" type="submit" :disabled="!actionState.canManageChildren">{{ tp("actionsAddZone") }}</button>
            </form>
          </section>

          <section v-if="entityKey === 'patrol_route' && selectedRecord && !isCreatingRecord" class="planning-admin-section">
            <div class="planning-admin-panel__header"><h3>{{ tp("checkpointsTitle") }}</h3></div>
            <div v-if="patrolCheckpoints.length" class="planning-admin-list">
              <button v-for="checkpoint in patrolCheckpoints" :key="checkpoint.id" type="button" class="planning-admin-row" @click="selectCheckpoint(checkpoint)">
                <div><strong>{{ checkpoint.sequence_no }} · {{ checkpoint.label }}</strong><span>{{ checkpoint.checkpoint_code }}</span></div>
                <StatusBadge :status="checkpoint.status" />
              </button>
            </div>
            <p v-else class="planning-admin-list-empty">{{ tp("checkpointsEmpty") }}</p>
            <form class="planning-admin-form" @submit.prevent="submitCheckpoint">
              <div class="planning-admin-form-grid">
                <label class="field-stack"><span>{{ tp("fieldsSequenceNo") }}</span><input v-model="checkpointDraft.sequence_no" type="number" min="1" required /></label>
                <label class="field-stack"><span>{{ tp("fieldsCheckpointCode") }}</span><input v-model="checkpointDraft.checkpoint_code" required /></label>
                <label class="field-stack"><span>{{ tp("fieldsLabel") }}</span><input v-model="checkpointDraft.label" required /></label>
                <label class="field-stack"><span>{{ tp("fieldsLatitude") }}</span><input v-model="checkpointDraft.latitude" type="number" step="0.000001" required /></label>
                <label class="field-stack"><span>{{ tp("fieldsLongitude") }}</span><input v-model="checkpointDraft.longitude" type="number" step="0.000001" required /></label>
                <label class="field-stack"><span>{{ tp("fieldsScanTypeCode") }}</span><input v-model="checkpointDraft.scan_type_code" required /></label>
                <label class="field-stack"><span>{{ tp("fieldsExpectedTokenValue") }}</span><input v-model="checkpointDraft.expected_token_value" /></label>
                <label class="field-stack"><span>{{ tp("fieldsMinimumDwellSeconds") }}</span><input v-model="checkpointDraft.minimum_dwell_seconds" type="number" min="0" required /></label>
                <label class="field-stack field-stack--wide"><span>{{ tp("fieldsNotes") }}</span><textarea v-model="checkpointDraft.notes" rows="3" /></label>
              </div>
              <button class="cta-button" type="submit" :disabled="!actionState.canManageChildren">{{ tp("actionsAddCheckpoint") }}</button>
            </form>
          </section>
        </template>

        <section v-else class="planning-admin-empty">
          <h3>{{ tp("detailEmptyTitle") }}</h3>
          <p>{{ tp("detailEmptyBody") }}</p>
        </section>
      </section>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";

import StatusBadge from "@/components/StatusBadge.vue";
import { useAuthStore } from "@/stores/auth";
import {
  createPatrolCheckpoint,
  createPlanningRecord,
  createTradeFairZone,
  getPlanningRecord,
  importPlanningDryRun,
  importPlanningExecute,
  listPatrolCheckpoints,
  listPlanningRecords,
  listTradeFairZones,
  PlanningAdminApiError,
  updatePatrolCheckpoint,
  updatePlanningRecord,
  updateTradeFairZone,
} from "@/api/planningAdmin";
import {
  buildPlanningImportTemplate,
  derivePlanningActionState,
  mapPlanningApiMessage,
  PLANNING_ENTITY_OPTIONS,
} from "@/features/planning/planningAdmin.helpers.js";
import { planningAdminMessages } from "@/i18n/planningAdmin.messages";
import { useLocaleStore } from "@/stores/locale";

const authStore = useAuthStore();
const localeStore = useLocaleStore();

const loading = reactive({ list: false, detail: false, action: false });
const feedback = reactive({ tone: "neutral", title: "", message: "" });
const filters = reactive({ search: "", customer_id: "", lifecycle_status: "", include_archived: false });
const entityOptions = PLANNING_ENTITY_OPTIONS;
const entityKey = ref("site");
const tenantScopeInput = ref(authStore.tenantScopeId || authStore.sessionUser?.tenant_id || "");
const records = ref([]);
const selectedRecordId = ref("");
const selectedRecord = ref(null);
const tradeFairZones = ref([]);
const patrolCheckpoints = ref([]);
const isCreatingRecord = ref(false);
const editingZoneId = ref("");
const editingCheckpointId = ref("");
const pendingImportFile = ref(null);
const importDryRunResult = ref(null);
const lastImportResult = ref(null);

const draft = reactive({
  customer_id: "",
  code: "",
  label: "",
  default_planning_mode_code: "",
  unit_of_measure_code: "",
  site_no: "",
  venue_no: "",
  fair_no: "",
  route_no: "",
  name: "",
  address_id: "",
  timezone: "",
  latitude: "",
  longitude: "",
  watchbook_enabled: false,
  notes: "",
  venue_id: "",
  start_date: "",
  end_date: "",
  site_id: "",
  meeting_address_id: "",
  start_point_text: "",
  end_point_text: "",
  travel_policy_code: "",
});

const zoneDraft = reactive({ zone_type_code: "", zone_code: "", label: "", notes: "", version_no: 0 });
const checkpointDraft = reactive({
  sequence_no: 1,
  checkpoint_code: "",
  label: "",
  latitude: "",
  longitude: "",
  scan_type_code: "",
  expected_token_value: "",
  minimum_dwell_seconds: 0,
  notes: "",
  version_no: 0,
});

const importDraft = reactive({ csv_text: buildPlanningImportTemplate(entityKey.value), continue_on_error: true });

const effectiveRole = computed(() => authStore.effectiveRole);
const isPlatformAdmin = computed(() => effectiveRole.value === "platform_admin");
const resolvedTenantScopeId = computed(() => isPlatformAdmin.value ? authStore.tenantScopeId : (authStore.sessionUser?.tenant_id ?? authStore.tenantScopeId));
const actionState = computed(() => derivePlanningActionState(effectiveRole.value, entityKey.value, selectedRecord.value));
const canRead = computed(() => actionState.value.canRead);
const canWrite = computed(() => actionState.value.canWrite);
const currentLocale = computed(() => (localeStore.locale === "en" ? "en" : "de"));

function tp(key, params = {}) {
  let text = planningAdminMessages[currentLocale.value][key] ?? planningAdminMessages.de[key] ?? key;
  Object.entries(params).forEach(([paramKey, value]) => {
    text = text.replace(`{${paramKey}}`, String(value));
  });
  return text;
}

const entityLabel = computed(() => entityName(entityKey.value));

function entityName(key) {
  return tp(
    {
      requirement_type: "entityRequirementType",
      equipment_item: "entityEquipmentItem",
      site: "entitySite",
      event_venue: "entityEventVenue",
      trade_fair: "entityTradeFair",
      patrol_route: "entityPatrolRoute",
    }[key],
  );
}

function setFeedback(tone, title, message) {
  feedback.tone = tone;
  feedback.title = title;
  feedback.message = message;
}

function clearFeedback() {
  setFeedback("neutral", "", "");
}

function rememberScope() {
  authStore.setTenantScopeId(tenantScopeInput.value);
  void refreshRecords();
}

function resetDraft() {
  Object.assign(draft, {
    customer_id: "",
    code: "",
    label: "",
    default_planning_mode_code: "",
    unit_of_measure_code: "",
    site_no: "",
    venue_no: "",
    fair_no: "",
    route_no: "",
    name: "",
    address_id: "",
    timezone: "",
    latitude: "",
    longitude: "",
    watchbook_enabled: false,
    notes: "",
    venue_id: "",
    start_date: "",
    end_date: "",
    site_id: "",
    meeting_address_id: "",
    start_point_text: "",
    end_point_text: "",
    travel_policy_code: "",
  });
}

function resetImportTemplate() {
  importDraft.csv_text = buildPlanningImportTemplate(entityKey.value);
}

function resetZoneDraft() {
  Object.assign(zoneDraft, { zone_type_code: "", zone_code: "", label: "", notes: "", version_no: 0 });
  editingZoneId.value = "";
}

function resetCheckpointDraft() {
  Object.assign(checkpointDraft, { sequence_no: 1, checkpoint_code: "", label: "", latitude: "", longitude: "", scan_type_code: "", expected_token_value: "", minimum_dwell_seconds: 0, notes: "", version_no: 0 });
  editingCheckpointId.value = "";
}

function recordTitle(record) {
  return record.code || record.site_no || record.venue_no || record.fair_no || record.route_no || record.name || record.label || record.id;
}

function syncDraft(record) {
  resetDraft();
  Object.assign(draft, {
    customer_id: record.customer_id || "",
    code: record.code || "",
    label: record.label || "",
    default_planning_mode_code: record.default_planning_mode_code || "",
    unit_of_measure_code: record.unit_of_measure_code || "",
    site_no: record.site_no || "",
    venue_no: record.venue_no || "",
    fair_no: record.fair_no || "",
    route_no: record.route_no || "",
    name: record.name || "",
    address_id: record.address_id || "",
    timezone: record.timezone || "",
    latitude: record.latitude ?? "",
    longitude: record.longitude ?? "",
    watchbook_enabled: !!record.watchbook_enabled,
    notes: record.notes || "",
    venue_id: record.venue_id || "",
    start_date: record.start_date || "",
    end_date: record.end_date || "",
    site_id: record.site_id || "",
    meeting_address_id: record.meeting_address_id || "",
    start_point_text: record.start_point_text || "",
    end_point_text: record.end_point_text || "",
    travel_policy_code: record.travel_policy_code || "",
  });
}

function buildRecordPayload() {
  const base = { tenant_id: resolvedTenantScopeId.value, customer_id: draft.customer_id, notes: draft.notes || null };
  if (entityKey.value === "requirement_type") return { ...base, code: draft.code, label: draft.label, default_planning_mode_code: draft.default_planning_mode_code };
  if (entityKey.value === "equipment_item") return { ...base, code: draft.code, label: draft.label, unit_of_measure_code: draft.unit_of_measure_code };
  if (entityKey.value === "site") return { ...base, site_no: draft.site_no, name: draft.name, address_id: draft.address_id || null, timezone: draft.timezone || null, latitude: draft.latitude || null, longitude: draft.longitude || null, watchbook_enabled: draft.watchbook_enabled };
  if (entityKey.value === "event_venue") return { ...base, venue_no: draft.venue_no, name: draft.name, address_id: draft.address_id || null, timezone: draft.timezone || null, latitude: draft.latitude || null, longitude: draft.longitude || null };
  if (entityKey.value === "trade_fair") return { ...base, fair_no: draft.fair_no, name: draft.name, venue_id: draft.venue_id || null, address_id: draft.address_id || null, timezone: draft.timezone || null, latitude: draft.latitude || null, longitude: draft.longitude || null, start_date: draft.start_date, end_date: draft.end_date };
  return { ...base, route_no: draft.route_no, name: draft.name, site_id: draft.site_id || null, meeting_address_id: draft.meeting_address_id || null, start_point_text: draft.start_point_text || null, end_point_text: draft.end_point_text || null, travel_policy_code: draft.travel_policy_code || null };
}

async function refreshRecords() {
  if (!resolvedTenantScopeId.value || !authStore.accessToken || !canRead.value) return;
  loading.list = true;
  try {
    records.value = await listPlanningRecords(entityKey.value, resolvedTenantScopeId.value, authStore.accessToken, filters);
    if (selectedRecordId.value) {
      const stillSelected = records.value.find((record) => record.id === selectedRecordId.value);
      if (!stillSelected) {
        selectedRecord.value = null;
        selectedRecordId.value = "";
      }
    }
  } catch (error) {
    handleError(error);
  } finally {
    loading.list = false;
  }
}

async function selectRecord(recordId) {
  if (!resolvedTenantScopeId.value || !authStore.accessToken) return;
  loading.detail = true;
  try {
    selectedRecord.value = await getPlanningRecord(entityKey.value, resolvedTenantScopeId.value, recordId, authStore.accessToken);
    selectedRecordId.value = recordId;
    isCreatingRecord.value = false;
    syncDraft(selectedRecord.value);
    tradeFairZones.value = entityKey.value === "trade_fair" ? await listTradeFairZones(resolvedTenantScopeId.value, recordId, authStore.accessToken) : [];
    patrolCheckpoints.value = entityKey.value === "patrol_route" ? await listPatrolCheckpoints(resolvedTenantScopeId.value, recordId, authStore.accessToken) : [];
    resetZoneDraft();
    resetCheckpointDraft();
  } catch (error) {
    handleError(error);
  } finally {
    loading.detail = false;
  }
}

function startCreateRecord() {
  isCreatingRecord.value = true;
  selectedRecord.value = null;
  selectedRecordId.value = "";
  tradeFairZones.value = [];
  patrolCheckpoints.value = [];
  resetDraft();
  draft.customer_id = filters.customer_id || "";
}

async function submitRecord() {
  if (!resolvedTenantScopeId.value || !authStore.accessToken) return;
  loading.action = true;
  try {
    const payload = buildRecordPayload();
    if (isCreatingRecord.value || !selectedRecord.value) {
      selectedRecord.value = await createPlanningRecord(entityKey.value, resolvedTenantScopeId.value, authStore.accessToken, payload);
      selectedRecordId.value = selectedRecord.value.id;
      isCreatingRecord.value = false;
    } else {
      selectedRecord.value = await updatePlanningRecord(entityKey.value, resolvedTenantScopeId.value, selectedRecord.value.id, authStore.accessToken, {
        ...payload,
        version_no: selectedRecord.value.version_no,
      });
    }
    syncDraft(selectedRecord.value);
    await refreshRecords();
    setFeedback("success", tp("successTitle"), tp("recordSaved"));
  } catch (error) {
    handleError(error);
  } finally {
    loading.action = false;
  }
}

function selectZone(zone) {
  editingZoneId.value = zone.id;
  Object.assign(zoneDraft, { zone_type_code: zone.zone_type_code, zone_code: zone.zone_code, label: zone.label, notes: zone.notes || "", version_no: zone.version_no });
}

function selectCheckpoint(checkpoint) {
  editingCheckpointId.value = checkpoint.id;
  Object.assign(checkpointDraft, {
    sequence_no: checkpoint.sequence_no,
    checkpoint_code: checkpoint.checkpoint_code,
    label: checkpoint.label,
    latitude: checkpoint.latitude,
    longitude: checkpoint.longitude,
    scan_type_code: checkpoint.scan_type_code,
    expected_token_value: checkpoint.expected_token_value || "",
    minimum_dwell_seconds: checkpoint.minimum_dwell_seconds,
    notes: checkpoint.notes || "",
    version_no: checkpoint.version_no,
  });
}

async function submitZone() {
  if (!resolvedTenantScopeId.value || !authStore.accessToken || !selectedRecord.value) return;
  try {
    const payload = {
      tenant_id: resolvedTenantScopeId.value,
      trade_fair_id: selectedRecord.value.id,
      zone_type_code: zoneDraft.zone_type_code,
      zone_code: zoneDraft.zone_code,
      label: zoneDraft.label,
      notes: zoneDraft.notes || null,
    };
    if (editingZoneId.value) {
      await updateTradeFairZone(resolvedTenantScopeId.value, selectedRecord.value.id, editingZoneId.value, authStore.accessToken, { ...payload, version_no: zoneDraft.version_no });
    } else {
      await createTradeFairZone(resolvedTenantScopeId.value, selectedRecord.value.id, authStore.accessToken, payload);
    }
    tradeFairZones.value = await listTradeFairZones(resolvedTenantScopeId.value, selectedRecord.value.id, authStore.accessToken);
    resetZoneDraft();
    setFeedback("success", tp("successTitle"), tp("childSaved"));
  } catch (error) {
    handleError(error);
  }
}

async function submitCheckpoint() {
  if (!resolvedTenantScopeId.value || !authStore.accessToken || !selectedRecord.value) return;
  try {
    const payload = {
      tenant_id: resolvedTenantScopeId.value,
      patrol_route_id: selectedRecord.value.id,
      sequence_no: Number(checkpointDraft.sequence_no),
      checkpoint_code: checkpointDraft.checkpoint_code,
      label: checkpointDraft.label,
      latitude: checkpointDraft.latitude,
      longitude: checkpointDraft.longitude,
      scan_type_code: checkpointDraft.scan_type_code,
      expected_token_value: checkpointDraft.expected_token_value || null,
      minimum_dwell_seconds: Number(checkpointDraft.minimum_dwell_seconds),
      notes: checkpointDraft.notes || null,
    };
    if (editingCheckpointId.value) {
      await updatePatrolCheckpoint(resolvedTenantScopeId.value, selectedRecord.value.id, editingCheckpointId.value, authStore.accessToken, { ...payload, version_no: checkpointDraft.version_no });
    } else {
      await createPatrolCheckpoint(resolvedTenantScopeId.value, selectedRecord.value.id, authStore.accessToken, payload);
    }
    patrolCheckpoints.value = await listPatrolCheckpoints(resolvedTenantScopeId.value, selectedRecord.value.id, authStore.accessToken);
    resetCheckpointDraft();
    setFeedback("success", tp("successTitle"), tp("childSaved"));
  } catch (error) {
    handleError(error);
  }
}

function changeEntity() {
  selectedRecord.value = null;
  selectedRecordId.value = "";
  isCreatingRecord.value = false;
  resetDraft();
  resetZoneDraft();
  resetCheckpointDraft();
  resetImportTemplate();
  tradeFairZones.value = [];
  patrolCheckpoints.value = [];
  void refreshRecords();
}

function onImportSelected(event) {
  pendingImportFile.value = event.target.files?.[0] || null;
}

async function loadImportFile() {
  if (!pendingImportFile.value) return;
  importDraft.csv_text = await pendingImportFile.value.text();
}

async function runImportDryRun() {
  if (!resolvedTenantScopeId.value || !authStore.accessToken) return;
  try {
    importDryRunResult.value = await importPlanningDryRun(resolvedTenantScopeId.value, authStore.accessToken, {
      tenant_id: resolvedTenantScopeId.value,
      entity_key: entityKey.value,
      csv_content_base64: btoa(unescape(encodeURIComponent(importDraft.csv_text))),
    });
    setFeedback("success", tp("successTitle"), tp("importDryRunReady"));
  } catch (error) {
    handleError(error);
  }
}

async function runImportExecute() {
  if (!resolvedTenantScopeId.value || !authStore.accessToken) return;
  try {
    lastImportResult.value = await importPlanningExecute(resolvedTenantScopeId.value, authStore.accessToken, {
      tenant_id: resolvedTenantScopeId.value,
      entity_key: entityKey.value,
      csv_content_base64: btoa(unescape(encodeURIComponent(importDraft.csv_text))),
      continue_on_error: importDraft.continue_on_error,
    });
    await refreshRecords();
    setFeedback("success", tp("successTitle"), tp("importExecuted"));
  } catch (error) {
    handleError(error);
  }
}

function handleError(error) {
  const key = error instanceof PlanningAdminApiError ? mapPlanningApiMessage(error.messageKey) : "error";
  setFeedback("error", tp("errorTitle"), tp(key));
}

onMounted(() => {
  resetImportTemplate();
  void refreshRecords();
});
</script>

<style scoped>
.planning-admin-page,
.planning-admin-grid,
.planning-admin-form,
.planning-admin-form-grid,
.planning-admin-list,
.planning-admin-row,
.planning-admin-meta,
.planning-admin-feedback,
.planning-admin-panel,
.planning-admin-panel__header,
.planning-admin-section,
.planning-admin-import {
  display: grid;
  gap: 1rem;
}

.planning-admin-grid {
  grid-template-columns: minmax(320px, 420px) minmax(0, 1fr);
}

.planning-admin-hero {
  grid-template-columns: minmax(0, 1fr) 320px;
}

.planning-admin-form-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.field-stack--wide {
  grid-column: 1 / -1;
}

.planning-admin-row,
.planning-admin-meta__pill,
.planning-admin-feedback,
.planning-admin-checkbox {
  border: 1px solid var(--border-color, #d9d9d9);
  border-radius: 12px;
  padding: 0.75rem 1rem;
}

.planning-admin-row {
  align-items: center;
  background: var(--card-bg, #fff);
  grid-template-columns: minmax(0, 1fr) auto;
  text-align: left;
}

.planning-admin-row.selected {
  border-color: var(--primary-color, rgb(40,170,170));
}

.planning-admin-empty,
.planning-admin-list-empty {
  color: var(--text-secondary, #666);
}

.cta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.field-stack {
  display: grid;
  gap: 0.35rem;
}

input,
select,
textarea,
button {
  font: inherit;
}

input,
select,
textarea {
  border: 1px solid var(--border-color, #d9d9d9);
  border-radius: 10px;
  padding: 0.7rem 0.85rem;
}

.cta-button {
  background: var(--primary-color, rgb(40,170,170));
  border: 0;
  border-radius: 999px;
  color: white;
  cursor: pointer;
  padding: 0.7rem 1rem;
}

.cta-button.cta-secondary {
  background: transparent;
  border: 1px solid var(--border-color, #d9d9d9);
  color: inherit;
}

@media (max-width: 1100px) {
  .planning-admin-grid,
  .planning-admin-hero,
  .planning-admin-form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
