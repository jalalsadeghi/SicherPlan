<template>
  <section class="planning-shifts-page">
    <section v-if="!props.embedded" class="module-card planning-shifts-hero">
      <div>
        <p class="eyebrow">{{ tp("eyebrow") }}</p>
        <h2>{{ tp("title") }}</h2>
        <p class="planning-shifts-lead">{{ tp("lead") }}</p>
      </div>
      <div class="module-card planning-shifts-scope">
        <label class="field-stack">
          <span>{{ tp("scopeLabel") }}</span>
          <input v-model="tenantScopeInput" :placeholder="tp('scopePlaceholder')" />
        </label>
        <label class="field-stack">
          <span>{{ tp("tokenLabel") }}</span>
          <input v-model="accessTokenInput" type="password" :placeholder="tp('tokenPlaceholder')" />
        </label>
        <p class="field-help">{{ tp("tokenHelp") }}</p>
        <div class="cta-row">
          <button class="cta-button" type="button" @click="rememberScopeAndToken">{{ tp("actionsRemember") }}</button>
          <button class="cta-button cta-secondary" type="button" :disabled="!canRead" @click="refreshAll">{{ tp("actionsRefresh") }}</button>
        </div>
      </div>
    </section>

    <section v-if="feedback.message" class="planning-orders-feedback" :data-tone="feedback.tone">
      <div>
        <strong>{{ feedback.title }}</strong>
        <span>{{ feedback.message }}</span>
      </div>
      <button type="button" @click="clearFeedback">{{ tp("actionsClearFeedback") }}</button>
    </section>

    <section v-if="!tenantScopeId || !accessToken" class="module-card planning-orders-empty">
      <p class="eyebrow">{{ tp("missingScopeTitle") }}</p>
      <h3>{{ tp("missingScopeBody") }}</h3>
    </section>

    <section v-else-if="!canRead" class="module-card planning-orders-empty">
      <p class="eyebrow">{{ tp("missingPermissionTitle") }}</p>
      <h3>{{ tp("missingPermissionBody") }}</h3>
    </section>

    <div v-else class="planning-shifts-workspace" data-testid="planning-shifts-workspace">
      <section v-if="props.embedded" class="module-card planning-shifts-controls">
        <div class="planning-shifts-panel__header">
          <div>
            <p class="eyebrow">{{ tp("eyebrow") }}</p>
            <h3>{{ tp("title") }}</h3>
          </div>
          <StatusBadge :status="canRead ? 'active' : 'inactive'" />
        </div>
        <div class="planning-shifts-form-grid planning-shifts-form-grid--controls">
          <label class="field-stack">
            <span>{{ tp("scopeLabel") }}</span>
            <input v-model="tenantScopeInput" :placeholder="tp('scopePlaceholder')" />
          </label>
          <label class="field-stack">
            <span>{{ tp("tokenLabel") }}</span>
            <input v-model="accessTokenInput" type="password" :placeholder="tp('tokenPlaceholder')" />
          </label>
        </div>
        <p class="field-help">{{ tp("tokenHelp") }}</p>
        <div class="cta-row">
          <button class="cta-button" type="button" @click="rememberScopeAndToken">{{ tp("actionsRemember") }}</button>
          <button class="cta-button cta-secondary" type="button" :disabled="!canRead" @click="refreshAll">{{ tp("actionsRefresh") }}</button>
        </div>
      </section>

      <nav class="planning-shifts-tabs" data-testid="planning-shifts-tabs">
        <button
          v-for="tab in workspaceTabs"
          :key="tab.id"
          type="button"
          class="planning-shifts-tab"
          :class="{ active: activeWorkspaceTab === tab.id }"
          :data-testid="`planning-shifts-tab-${tab.id}`"
          @click="activeWorkspaceTab = tab.id"
        >
          {{ tab.label }}
        </button>
      </nav>

      <section
        v-show="activeWorkspaceTab === 'templates'"
        class="module-card planning-shifts-panel planning-shifts-tab-panel"
        data-testid="planning-shifts-tab-panel-templates"
      >
        <div class="planning-orders-panel__header">
          <div>
            <p class="eyebrow">{{ tp("templatesTitle") }}</p>
            <h3>{{ tp("templatesTitle") }}</h3>
          </div>
          <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canCreateTemplate" @click="startCreateTemplate">{{ tp("actionsCreateTemplate") }}</button>
        </div>
        <div class="planning-orders-list">
          <button
            v-for="template in templates"
            :key="template.id"
            type="button"
            class="planning-orders-row"
            :class="{ selected: template.id === selectedTemplateId }"
            @click="selectTemplate(template.id)"
          >
            <div>
              <strong>{{ template.code }}</strong>
              <span>{{ template.label }}</span>
            </div>
          </button>
        </div>
        <p v-if="!templates.length" class="planning-orders-list-empty">{{ tp("listEmpty") }}</p>
        <form class="planning-orders-form" @submit.prevent="submitTemplate">
          <div class="planning-orders-form-grid">
            <label class="field-stack"><span>{{ tp("fieldsCode") }}</span><input v-model="templateDraft.code" required /></label>
            <label class="field-stack"><span>{{ tp("fieldsLabel") }}</span><input v-model="templateDraft.label" required /></label>
            <label class="field-stack"><span>{{ tp("fieldsStartTime") }}</span><input v-model="templateDraft.local_start_time" type="time" required /></label>
            <label class="field-stack"><span>{{ tp("fieldsEndTime") }}</span><input v-model="templateDraft.local_end_time" type="time" required /></label>
            <label class="field-stack"><span>{{ tp("fieldsBreakMinutes") }}</span><input v-model.number="templateDraft.default_break_minutes" type="number" min="0" /></label>
            <label class="field-stack"><span>{{ tp("fieldsShiftType") }}</span><input v-model="templateDraft.shift_type_code" required /></label>
            <label class="field-stack"><span>{{ tp("fieldsMeetingPoint") }}</span><input v-model="templateDraft.meeting_point" /></label>
            <label class="field-stack"><span>{{ tp("fieldsLocationText") }}</span><input v-model="templateDraft.location_text" /></label>
            <label class="field-stack field-stack--wide"><span>{{ tp("fieldsNotes") }}</span><textarea v-model="templateDraft.notes" rows="2" /></label>
          </div>
          <div class="cta-row">
            <button class="cta-button" type="submit" :disabled="!actionState.canCreateTemplate">{{ tp("actionsSave") }}</button>
            <button class="cta-button cta-secondary" type="button" @click="resetTemplateDraft">{{ tp("actionsReset") }}</button>
          </div>
        </form>
      </section>

      <section
        v-show="activeWorkspaceTab === 'plans'"
        class="module-card planning-shifts-panel planning-shifts-tab-panel"
        data-testid="planning-shifts-tab-panel-plans"
      >
        <div class="planning-orders-panel__header">
          <div>
            <p class="eyebrow">{{ tp("plansTitle") }}</p>
            <h3>{{ tp("plansTitle") }}</h3>
          </div>
          <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canCreatePlan" @click="startCreatePlan">{{ tp("actionsCreatePlan") }}</button>
        </div>
        <div class="planning-orders-form-grid">
          <label class="field-stack"><span>{{ tp("filtersPlanningRecord") }}</span><input v-model="planFilters.planning_record_id" /></label>
        </div>
        <div class="cta-row">
          <button class="cta-button cta-secondary" type="button" @click="refreshPlans">{{ tp("actionsRefresh") }}</button>
        </div>
        <div class="planning-orders-list">
          <button
            v-for="plan in shiftPlans"
            :key="plan.id"
            type="button"
            class="planning-orders-row"
            :class="{ selected: plan.id === selectedShiftPlanId }"
            @click="selectShiftPlan(plan.id)"
          >
            <div>
              <strong>{{ plan.name }}</strong>
              <span>{{ workforceLabel(plan.workforce_scope_code) }}</span>
            </div>
          </button>
        </div>
        <p v-if="!shiftPlans.length" class="planning-orders-list-empty">{{ tp("listEmpty") }}</p>
        <form class="planning-orders-form" @submit.prevent="submitShiftPlan">
          <div class="planning-orders-form-grid">
            <label class="field-stack"><span>{{ tp("fieldsPlanningRecordId") }}</span><input v-model="shiftPlanDraft.planning_record_id" required /></label>
            <label class="field-stack"><span>{{ tp("fieldsName") }}</span><input v-model="shiftPlanDraft.name" required /></label>
            <label class="field-stack">
              <span>{{ tp("fieldsWorkforceScope") }}</span>
              <select v-model="shiftPlanDraft.workforce_scope_code">
                <option value="internal">{{ tp("workforceInternal") }}</option>
                <option value="subcontractor">{{ tp("workforceSubcontractor") }}</option>
                <option value="mixed">{{ tp("workforceMixed") }}</option>
              </select>
            </label>
            <label class="field-stack"><span>{{ tp("fieldsPlanningFrom") }}</span><input v-model="shiftPlanDraft.planning_from" type="date" required /></label>
            <label class="field-stack"><span>{{ tp("fieldsPlanningTo") }}</span><input v-model="shiftPlanDraft.planning_to" type="date" required /></label>
            <label class="field-stack field-stack--wide"><span>{{ tp("fieldsNotes") }}</span><textarea v-model="shiftPlanDraft.remarks" rows="2" /></label>
          </div>
          <div class="cta-row">
            <button class="cta-button" type="submit" :disabled="!actionState.canCreatePlan">{{ tp("actionsSave") }}</button>
            <button class="cta-button cta-secondary" type="button" @click="resetShiftPlanDraft">{{ tp("actionsReset") }}</button>
          </div>
        </form>
      </section>

      <section
        v-show="activeWorkspaceTab === 'series'"
        class="module-card planning-shifts-panel planning-shifts-tab-panel"
        data-testid="planning-shifts-tab-panel-series"
      >
        <div class="planning-orders-panel__header">
          <div>
            <p class="eyebrow">{{ tp("seriesTitle") }}</p>
            <h3>{{ tp("seriesTitle") }}</h3>
          </div>
          <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canCreateSeries" @click="startCreateSeries">{{ tp("actionsCreateSeries") }}</button>
        </div>
        <div class="planning-orders-list">
          <button
            v-for="series in seriesRows"
            :key="series.id"
            type="button"
            class="planning-orders-row"
            :class="{ selected: series.id === selectedSeriesId }"
            @click="selectSeries(series.id)"
          >
            <div>
              <strong>{{ series.label }}</strong>
              <span>{{ recurrenceLabelText(series.recurrence_code) }}</span>
            </div>
          </button>
        </div>
        <p v-if="!seriesRows.length" class="planning-orders-list-empty">{{ tp("listEmpty") }}</p>
        <form class="planning-orders-form" @submit.prevent="submitSeries">
          <div class="planning-orders-form-grid">
            <label class="field-stack"><span>{{ tp("fieldsLabel") }}</span><input v-model="seriesDraft.label" required /></label>
            <label class="field-stack">
              <span>{{ tp("fieldsRecurrence") }}</span>
              <select v-model="seriesDraft.recurrence_code">
                <option value="daily">{{ tp("recurrenceDaily") }}</option>
                <option value="weekly">{{ tp("recurrenceWeekly") }}</option>
              </select>
            </label>
            <label class="field-stack"><span>{{ tp("fieldsInterval") }}</span><input v-model.number="seriesDraft.interval_count" type="number" min="1" /></label>
            <label class="field-stack"><span>{{ tp("fieldsWeekdayMask") }}</span><input v-model="seriesDraft.weekday_mask" /></label>
            <label class="field-stack"><span>{{ tp("fieldsTimezone") }}</span><input v-model="seriesDraft.timezone" required /></label>
            <label class="field-stack"><span>{{ tp("fieldsPlanningFrom") }}</span><input v-model="seriesDraft.date_from" type="date" required /></label>
            <label class="field-stack"><span>{{ tp("fieldsPlanningTo") }}</span><input v-model="seriesDraft.date_to" type="date" required /></label>
            <label class="field-stack"><span>{{ tp("fieldsReleaseState") }}</span>
              <select v-model="seriesDraft.release_state">
                <option value="draft">{{ tp("statusDraft") }}</option>
                <option value="release_ready">{{ tp("statusReleaseReady") }}</option>
                <option value="released">{{ tp("statusReleased") }}</option>
              </select>
            </label>
            <label class="field-stack"><span>{{ tp("fieldsShiftType") }}</span><input v-model="seriesDraft.shift_type_code" /></label>
            <label class="field-stack"><span>{{ tp("fieldsMeetingPoint") }}</span><input v-model="seriesDraft.meeting_point" /></label>
            <label class="field-stack"><span>{{ tp("fieldsLocationText") }}</span><input v-model="seriesDraft.location_text" /></label>
            <label class="field-stack"><span>{{ tp("fieldsBreakMinutes") }}</span><input v-model.number="seriesDraft.default_break_minutes" type="number" min="0" /></label>
            <label class="planning-orders-checkbox"><input v-model="seriesDraft.customer_visible_flag" type="checkbox" /><span>{{ tp("fieldsVisibilityCustomer") }}</span></label>
            <label class="planning-orders-checkbox"><input v-model="seriesDraft.subcontractor_visible_flag" type="checkbox" /><span>{{ tp("fieldsVisibilitySubcontractor") }}</span></label>
            <label class="planning-orders-checkbox"><input v-model="seriesDraft.stealth_mode_flag" type="checkbox" /><span>{{ tp("fieldsVisibilityStealth") }}</span></label>
          </div>
          <div class="cta-row">
            <button class="cta-button" type="submit" :disabled="!actionState.canCreateSeries">{{ tp("actionsSave") }}</button>
            <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canGenerateSeries" @click="generateSelectedSeries">{{ tp("actionsGenerate") }}</button>
          </div>
        </form>
        <form v-if="selectedSeriesId" class="planning-orders-form" @submit.prevent="submitException">
          <div class="planning-orders-form-grid">
            <label class="field-stack"><span>{{ tp("fieldsOccurrenceDate") }}</span><input v-model="exceptionDraft.exception_date" type="date" required /></label>
            <label class="field-stack">
              <span>{{ tp("fieldsActionCode") }}</span>
              <select v-model="exceptionDraft.action_code">
                <option value="skip">{{ tp("exceptionSkip") }}</option>
                <option value="override">{{ tp("exceptionOverride") }}</option>
              </select>
            </label>
            <label class="field-stack"><span>{{ tp("fieldsOverrideStart") }}</span><input v-model="exceptionDraft.override_local_start_time" type="time" /></label>
            <label class="field-stack"><span>{{ tp("fieldsOverrideEnd") }}</span><input v-model="exceptionDraft.override_local_end_time" type="time" /></label>
          </div>
          <div class="cta-row">
            <button class="cta-button cta-secondary" type="submit" :disabled="!actionState.canManageExceptions">{{ tp("actionsCreateException") }}</button>
          </div>
        </form>
      </section>

      <section
        v-show="activeWorkspaceTab === 'shifts'"
        class="module-card planning-shifts-panel planning-shifts-tab-panel"
        data-testid="planning-shifts-tab-panel-shifts"
      >
        <div class="planning-orders-panel__header">
          <div>
            <p class="eyebrow">{{ tp("shiftsTitle") }}</p>
            <h3>{{ tp("shiftsTitle") }}</h3>
          </div>
          <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canCreateShift" @click="startCreateShift">{{ tp("actionsCreateShift") }}</button>
        </div>
        <div class="planning-orders-form-grid">
          <label class="field-stack"><span>{{ tp("filtersDateFrom") }}</span><input v-model="shiftFilters.date_from" type="date" /></label>
          <label class="field-stack"><span>{{ tp("filtersDateTo") }}</span><input v-model="shiftFilters.date_to" type="date" /></label>
          <label class="field-stack"><span>{{ tp("filtersVisibility") }}</span><input v-model="shiftFilters.visibility_state" /></label>
        </div>
        <div class="cta-row">
          <button class="cta-button cta-secondary" type="button" @click="refreshShifts">{{ tp("actionsRefresh") }}</button>
          <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canCopy" @click="copyOneDay">{{ tp("actionsCopyDay") }}</button>
          <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canCopy" @click="copyOneWeek">{{ tp("actionsCopyWeek") }}</button>
        </div>
        <div class="planning-orders-list">
          <button
            v-for="shift in shifts"
            :key="shift.id"
            type="button"
            class="planning-orders-row"
            :class="{ selected: shift.id === selectedShiftId }"
            @click="selectShift(shift.id)"
          >
            <div>
              <strong>{{ shift.shift_type_code }}</strong>
              <span>{{ shift.starts_at }}</span>
            </div>
          </button>
        </div>
        <p v-if="!shifts.length" class="planning-orders-list-empty">{{ tp("listEmpty") }}</p>
        <form class="planning-orders-form" @submit.prevent="submitShift">
          <div class="planning-orders-form-grid">
            <label class="field-stack"><span>{{ tp("fieldsStartsAt") }}</span><input v-model="shiftDraft.starts_at" type="datetime-local" required /></label>
            <label class="field-stack"><span>{{ tp("fieldsEndsAt") }}</span><input v-model="shiftDraft.ends_at" type="datetime-local" required /></label>
            <label class="field-stack"><span>{{ tp("fieldsBreakMinutes") }}</span><input v-model.number="shiftDraft.break_minutes" type="number" min="0" /></label>
            <label class="field-stack"><span>{{ tp("fieldsShiftType") }}</span><input v-model="shiftDraft.shift_type_code" required /></label>
            <label class="field-stack"><span>{{ tp("fieldsMeetingPoint") }}</span><input v-model="shiftDraft.meeting_point" /></label>
            <label class="field-stack"><span>{{ tp("fieldsLocationText") }}</span><input v-model="shiftDraft.location_text" /></label>
            <label class="field-stack"><span>{{ tp("fieldsReleaseState") }}</span>
              <select v-model="shiftDraft.release_state">
                <option value="draft">{{ tp("statusDraft") }}</option>
                <option value="release_ready">{{ tp("statusReleaseReady") }}</option>
                <option value="released">{{ tp("statusReleased") }}</option>
              </select>
            </label>
            <label class="planning-orders-checkbox"><input v-model="shiftDraft.customer_visible_flag" type="checkbox" /><span>{{ tp("fieldsVisibilityCustomer") }}</span></label>
            <label class="planning-orders-checkbox"><input v-model="shiftDraft.subcontractor_visible_flag" type="checkbox" /><span>{{ tp("fieldsVisibilitySubcontractor") }}</span></label>
            <label class="planning-orders-checkbox"><input v-model="shiftDraft.stealth_mode_flag" type="checkbox" /><span>{{ tp("fieldsVisibilityStealth") }}</span></label>
          </div>
          <div class="cta-row">
            <button class="cta-button" type="submit" :disabled="!actionState.canCreateShift">{{ tp("actionsSave") }}</button>
            <button class="cta-button cta-secondary" type="button" @click="resetShiftDraft">{{ tp("actionsReset") }}</button>
          </div>
        </form>
      </section>

      <section
        v-show="activeWorkspaceTab === 'board'"
        class="module-card planning-shifts-panel planning-shifts-board planning-shifts-tab-panel"
        data-testid="planning-shifts-tab-panel-board"
      >
        <div class="planning-orders-panel__header">
          <div>
            <p class="eyebrow">{{ tp("boardTitle") }}</p>
            <h3>{{ tp("boardTitle") }}</h3>
          </div>
        </div>
        <div class="planning-orders-form-grid">
          <label class="field-stack"><span>{{ tp("filtersDateFrom") }}</span><input v-model="boardFilters.date_from" type="datetime-local" /></label>
          <label class="field-stack"><span>{{ tp("filtersDateTo") }}</span><input v-model="boardFilters.date_to" type="datetime-local" /></label>
          <label class="field-stack"><span>{{ tp("filtersReleaseState") }}</span><input v-model="boardFilters.release_state" /></label>
        </div>
        <div class="cta-row">
          <button class="cta-button cta-secondary" type="button" @click="refreshBoard">{{ tp("actionsRefresh") }}</button>
        </div>
        <div class="planning-orders-list">
          <div v-for="row in boardRows" :key="row.id" class="planning-orders-row planning-orders-row--static">
            <div>
              <strong>{{ row.order_no }} · {{ row.planning_record_name }}</strong>
              <span>{{ row.starts_at }} · {{ row.shift_type_code }}</span>
            </div>
            <span>{{ workforceLabel(row.workforce_scope_code) }}</span>
          </div>
        </div>
        <p v-if="!boardRows.length" class="planning-orders-list-empty">{{ tp("listEmpty") }}</p>
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from "vue";

import {
  createShift,
  createShiftPlan,
  createShiftSeries,
  createShiftSeriesException,
  createShiftTemplate,
  generateShiftSeries,
  getShiftPlan,
  listBoardShifts,
  listShiftPlans,
  listShiftSeries,
  listShiftTemplates,
  listShifts,
  updateShift,
  updateShiftPlan,
  updateShiftSeries,
  updateShiftTemplate,
  copyShiftSlice,
  type PlanningBoardShiftListItem,
  type ShiftListItem,
  type ShiftPlanListItem,
  type ShiftSeriesListItem,
  type ShiftTemplateListItem,
  PlanningShiftsApiError,
} from "@/api/planningShifts";
import { planningShiftsMessages } from "@/i18n/planningShifts.messages";
import { useAuthStore } from "@/stores/auth";
import { useLocaleStore } from "@/stores/locale";
import StatusBadge from "@/components/StatusBadge.vue";
import {
  derivePlanningShiftActionState,
  mapPlanningShiftApiMessage,
  recurrenceLabel,
} from "@/features/planning/planningShifts.helpers";

const props = withDefaults(defineProps<{ embedded?: boolean }>(), {
  embedded: false,
});

const authStore = useAuthStore();
const localeStore = useLocaleStore();
const currentLocale = computed(() => (localeStore.locale === "en" ? "en" : "de"));
const role = computed(() => authStore.effectiveRole || "tenant_admin");
const tenantScopeInput = ref(authStore.tenantScopeId || "");
const accessTokenInput = ref(authStore.accessToken || "");
const tenantScopeId = ref(authStore.tenantScopeId || "");
const accessToken = ref(authStore.accessToken || "");

const templates = ref<ShiftTemplateListItem[]>([]);
const shiftPlans = ref<ShiftPlanListItem[]>([]);
const seriesRows = ref<ShiftSeriesListItem[]>([]);
const shifts = ref<ShiftListItem[]>([]);
const boardRows = ref<PlanningBoardShiftListItem[]>([]);

const selectedTemplateId = ref("");
const selectedShiftPlanId = ref("");
const selectedSeriesId = ref("");
const selectedShiftId = ref("");
const planFilters = reactive<any>({ planning_record_id: "" });

const templateDraft = reactive<any>(createEmptyTemplateDraft());
const shiftPlanDraft = reactive<any>(createEmptyShiftPlanDraft());
const seriesDraft = reactive<any>(createEmptySeriesDraft());
const exceptionDraft = reactive<any>(createEmptyExceptionDraft());
const shiftDraft = reactive<any>(createEmptyShiftDraft());
const shiftFilters = reactive<any>({ date_from: "", date_to: "", visibility_state: "" });
const boardFilters = reactive<any>({
  date_from: toDateTimeLocal(new Date(Date.UTC(2026, 3, 1, 0, 0))),
  date_to: toDateTimeLocal(new Date(Date.UTC(2026, 3, 8, 0, 0))),
  release_state: "",
});
const feedback = reactive({ tone: "info", title: "", message: "" });
const activeWorkspaceTab = ref("templates");
const workspaceTabs = computed(() => [
  { id: "templates", label: tp("templatesTitle") },
  { id: "plans", label: tp("plansTitle") },
  { id: "series", label: tp("seriesTitle") },
  { id: "shifts", label: tp("shiftsTitle") },
  { id: "board", label: tp("boardTitle") },
]);

const actionState = computed(() =>
  derivePlanningShiftActionState(
    role.value,
    selectedShiftPlanId.value ? { id: selectedShiftPlanId.value } : null,
    selectedSeriesId.value ? { id: selectedSeriesId.value } : null,
    selectedShiftId.value ? { id: selectedShiftId.value } : null,
  ),
);
const canRead = computed(() => actionState.value.canRead);

function tp(key: keyof typeof planningShiftsMessages.de) {
  return planningShiftsMessages[currentLocale.value][key] ?? planningShiftsMessages.de[key] ?? key;
}

function rememberScopeAndToken() {
  tenantScopeId.value = tenantScopeInput.value.trim();
  accessToken.value = accessTokenInput.value.trim();
  authStore.tenantScopeId = tenantScopeId.value;
  authStore.accessToken = accessToken.value;
}

function setFeedback(tone: string, title: string, message: string) {
  feedback.tone = tone;
  feedback.title = title;
  feedback.message = message;
}

function clearFeedback() {
  feedback.tone = "info";
  feedback.title = "";
  feedback.message = "";
}

function createEmptyTemplateDraft() {
  return {
    tenant_id: tenantScopeId.value || "",
    code: "",
    label: "",
    local_start_time: "08:00",
    local_end_time: "16:00",
    default_break_minutes: 30,
    shift_type_code: "day",
    meeting_point: "",
    location_text: "",
    notes: "",
    version_no: 0,
  };
}

function createEmptyShiftPlanDraft(planningRecordId = "") {
  return {
    tenant_id: tenantScopeId.value || "",
    planning_record_id: planningRecordId,
    name: "",
    workforce_scope_code: "internal",
    planning_from: "",
    planning_to: "",
    remarks: "",
    version_no: 0,
  };
}

function createEmptySeriesDraft() {
  return {
    tenant_id: tenantScopeId.value || "",
    shift_plan_id: selectedShiftPlanId.value || "",
    shift_template_id: selectedTemplateId.value || "",
    label: "",
    recurrence_code: "daily",
    interval_count: 1,
    weekday_mask: "1111100",
    timezone: "Europe/Berlin",
    date_from: "",
    date_to: "",
    default_break_minutes: 30,
    shift_type_code: "",
    meeting_point: "",
    location_text: "",
    customer_visible_flag: false,
    subcontractor_visible_flag: false,
    stealth_mode_flag: false,
    release_state: "draft",
    version_no: 0,
  };
}

function createEmptyExceptionDraft() {
  return {
    tenant_id: tenantScopeId.value || "",
    exception_date: "",
    action_code: "skip",
    override_local_start_time: "",
    override_local_end_time: "",
  };
}

function createEmptyShiftDraft() {
  return {
    tenant_id: tenantScopeId.value || "",
    shift_plan_id: selectedShiftPlanId.value || "",
    shift_series_id: null,
    occurrence_date: "",
    starts_at: "",
    ends_at: "",
    break_minutes: 30,
    shift_type_code: "day",
    location_text: "",
    meeting_point: "",
    release_state: "draft",
    customer_visible_flag: false,
    subcontractor_visible_flag: false,
    stealth_mode_flag: false,
    source_kind_code: "manual",
    version_no: 0,
  };
}

function resetTemplateDraft() {
  Object.assign(templateDraft, createEmptyTemplateDraft());
}

function resetShiftPlanDraft() {
  Object.assign(shiftPlanDraft, createEmptyShiftPlanDraft(planFilters.planning_record_id || ""));
}

function resetSeriesDraft() {
  Object.assign(seriesDraft, createEmptySeriesDraft());
}

function resetShiftDraft() {
  Object.assign(shiftDraft, createEmptyShiftDraft());
}

function selectTemplate(templateId: string) {
  selectedTemplateId.value = templateId;
  const row = templates.value.find((entry) => entry.id === templateId);
  if (row) {
    Object.assign(templateDraft, { ...row, tenant_id: tenantScopeId.value, meeting_point: "", location_text: "", notes: "" });
  }
}

async function selectShiftPlan(shiftPlanId: string) {
  selectedShiftPlanId.value = shiftPlanId;
  await refreshPlanDetails();
}

function selectSeries(seriesId: string) {
  selectedSeriesId.value = seriesId;
  const row = seriesRows.value.find((entry) => entry.id === seriesId);
  if (row) {
    Object.assign(seriesDraft, { ...row, tenant_id: tenantScopeId.value });
  }
}

function selectShift(shiftId: string) {
  selectedShiftId.value = shiftId;
  const row = shifts.value.find((entry) => entry.id === shiftId);
  if (row) {
    Object.assign(shiftDraft, {
      ...row,
      tenant_id: tenantScopeId.value,
      starts_at: normalizeDateTimeLocal(row.starts_at),
      ends_at: normalizeDateTimeLocal(row.ends_at),
    });
  }
}

function startCreateTemplate() { resetTemplateDraft(); selectedTemplateId.value = ""; }
function startCreatePlan() { resetShiftPlanDraft(); selectedShiftPlanId.value = ""; seriesRows.value = []; shifts.value = []; }
function startCreateSeries() { resetSeriesDraft(); selectedSeriesId.value = ""; }
function startCreateShift() { resetShiftDraft(); selectedShiftId.value = ""; }

async function refreshAll() {
  await Promise.all([refreshTemplates(), refreshPlans()]);
  await refreshBoard();
}

async function refreshTemplates() {
  templates.value = await listShiftTemplates(tenantScopeId.value, accessToken.value, {});
}

async function refreshPlans() {
  shiftPlans.value = await listShiftPlans(tenantScopeId.value, accessToken.value, planFilters);
}

async function refreshPlanDetails() {
  if (!selectedShiftPlanId.value) return;
  const plan = await getShiftPlan(tenantScopeId.value, selectedShiftPlanId.value, accessToken.value);
  seriesRows.value = await listShiftSeries(tenantScopeId.value, selectedShiftPlanId.value, accessToken.value);
  shifts.value = await listShifts(tenantScopeId.value, accessToken.value, { ...shiftFilters, shift_plan_id: selectedShiftPlanId.value });
  Object.assign(shiftPlanDraft, { ...plan, tenant_id: tenantScopeId.value });
}

async function refreshShifts() {
  if (!selectedShiftPlanId.value) return;
  shifts.value = await listShifts(tenantScopeId.value, accessToken.value, { ...shiftFilters, shift_plan_id: selectedShiftPlanId.value });
}

async function refreshBoard() {
  boardRows.value = await listBoardShifts(tenantScopeId.value, accessToken.value, {
    date_from: fromDateTimeLocal(boardFilters.date_from),
    date_to: fromDateTimeLocal(boardFilters.date_to),
    release_state: boardFilters.release_state,
  });
}

async function submitTemplate() {
  try {
    templateDraft.tenant_id = tenantScopeId.value;
    if (selectedTemplateId.value) {
      await updateShiftTemplate(tenantScopeId.value, selectedTemplateId.value, accessToken.value, templateDraft);
    } else {
      await createShiftTemplate(tenantScopeId.value, accessToken.value, templateDraft);
    }
    await refreshTemplates();
    setFeedback("success", tp("successTitle"), tp("saved"));
  } catch (error) {
    handleApiError(error);
  }
}

async function submitShiftPlan() {
  try {
    shiftPlanDraft.tenant_id = tenantScopeId.value;
    if (selectedShiftPlanId.value) {
      await updateShiftPlan(tenantScopeId.value, selectedShiftPlanId.value, accessToken.value, shiftPlanDraft);
    } else {
      const created = await createShiftPlan(tenantScopeId.value, accessToken.value, shiftPlanDraft);
      selectedShiftPlanId.value = created.id;
    }
    await refreshPlans();
    await refreshPlanDetails();
    setFeedback("success", tp("successTitle"), tp("saved"));
  } catch (error) {
    handleApiError(error);
  }
}

async function submitSeries() {
  try {
    seriesDraft.tenant_id = tenantScopeId.value;
    seriesDraft.shift_plan_id = selectedShiftPlanId.value;
    if (!seriesDraft.shift_template_id && selectedTemplateId.value) {
      seriesDraft.shift_template_id = selectedTemplateId.value;
    }
    if (selectedSeriesId.value) {
      await updateShiftSeries(tenantScopeId.value, selectedSeriesId.value, accessToken.value, seriesDraft);
    } else {
      const created = await createShiftSeries(tenantScopeId.value, selectedShiftPlanId.value, accessToken.value, seriesDraft);
      selectedSeriesId.value = created.id;
    }
    seriesRows.value = await listShiftSeries(tenantScopeId.value, selectedShiftPlanId.value, accessToken.value);
    setFeedback("success", tp("successTitle"), tp("saved"));
  } catch (error) {
    handleApiError(error);
  }
}

async function generateSelectedSeries() {
  if (!selectedSeriesId.value) return;
  try {
    await generateShiftSeries(tenantScopeId.value, selectedSeriesId.value, accessToken.value, {});
    await refreshShifts();
    await refreshBoard();
    setFeedback("success", tp("successTitle"), tp("generated"));
  } catch (error) {
    handleApiError(error);
  }
}

async function submitException() {
  if (!selectedSeriesId.value) return;
  try {
    exceptionDraft.tenant_id = tenantScopeId.value;
    await createShiftSeriesException(tenantScopeId.value, selectedSeriesId.value, accessToken.value, exceptionDraft);
    seriesRows.value = await listShiftSeries(tenantScopeId.value, selectedShiftPlanId.value, accessToken.value);
    setFeedback("success", tp("successTitle"), tp("saved"));
  } catch (error) {
    handleApiError(error);
  }
}

async function submitShift() {
  if (!selectedShiftPlanId.value) return;
  try {
    shiftDraft.tenant_id = tenantScopeId.value;
    shiftDraft.shift_plan_id = selectedShiftPlanId.value;
    shiftDraft.starts_at = fromDateTimeLocal(shiftDraft.starts_at);
    shiftDraft.ends_at = fromDateTimeLocal(shiftDraft.ends_at);
    if (selectedShiftId.value) {
      await updateShift(tenantScopeId.value, selectedShiftId.value, accessToken.value, shiftDraft);
    } else {
      await createShift(tenantScopeId.value, accessToken.value, shiftDraft);
    }
    await refreshShifts();
    await refreshBoard();
    setFeedback("success", tp("successTitle"), tp("saved"));
  } catch (error) {
    handleApiError(error);
  }
}

async function copyOneDay() {
  await executeCopy(1);
}

async function copyOneWeek() {
  await executeCopy(7);
}

async function executeCopy(deltaDays: number) {
  if (!selectedShiftPlanId.value || !shiftFilters.date_from) return;
  try {
    const source = shiftFilters.date_from;
    const target = addDays(source, deltaDays);
    await copyShiftSlice(tenantScopeId.value, selectedShiftPlanId.value, accessToken.value, {
      source_from: source,
      source_to: source,
      target_from: target,
      duplicate_mode: "skip_existing",
    });
    await refreshShifts();
    await refreshBoard();
    setFeedback("success", tp("successTitle"), tp("copied"));
  } catch (error) {
    handleApiError(error);
  }
}

function workforceLabel(value: string) {
  if (value === "internal") return tp("workforceInternal");
  if (value === "subcontractor") return tp("workforceSubcontractor");
  return tp("workforceMixed");
}

function recurrenceLabelText(value: string) {
  const key = recurrenceLabel(value);
  if (key === "daily") return tp("recurrenceDaily");
  if (key === "weekly") return tp("recurrenceWeekly");
  return value;
}

function handleApiError(error: unknown) {
  const messageKey = error instanceof PlanningShiftsApiError ? error.messageKey : "error";
  setFeedback("error", tp("errorTitle"), tp(mapPlanningShiftApiMessage(messageKey) as keyof typeof planningShiftsMessages.de));
}

function normalizeDateTimeLocal(value: string) {
  return value.slice(0, 16);
}

function fromDateTimeLocal(value: string) {
  return new Date(value).toISOString();
}

function toDateTimeLocal(value: Date) {
  return value.toISOString().slice(0, 16);
}

function addDays(value: string, delta: number) {
  const parsed = new Date(`${value}T00:00:00Z`);
  parsed.setUTCDate(parsed.getUTCDate() + delta);
  return parsed.toISOString().slice(0, 10);
}
</script>

<style scoped>
.planning-shifts-page {
  display: grid;
  gap: 1rem;
}

.planning-shifts-workspace {
  display: grid;
  gap: 1rem;
}

.planning-shifts-hero,
.planning-shifts-controls,
.planning-shifts-panel,
.planning-orders-feedback,
.planning-orders-empty {
  border-radius: 18px;
  border: 1px solid var(--sp-color-border);
  background: color-mix(in srgb, var(--sp-color-surface-card) 94%, white);
  box-shadow: 0 18px 50px rgb(15 23 42 / 7%);
}

.planning-shifts-hero {
  display: flex;
  justify-content: space-between;
  gap: 1.25rem;
  align-items: flex-start;
}

.planning-shifts-controls,
.planning-shifts-panel {
  display: grid;
  gap: 1rem;
}

.planning-shifts-board {
  grid-column: 1 / -1;
}

.planning-shifts-lead {
  max-width: 70ch;
}

.planning-shifts-scope {
  display: grid;
  gap: 0.75rem;
}

.planning-shifts-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem;
}

.planning-shifts-tab {
  border: 1px solid var(--sp-color-border-soft);
  background: color-mix(in srgb, var(--sp-color-surface-card) 88%, white);
  color: var(--sp-color-text-secondary);
  border-radius: 999px;
  padding: 0.65rem 1rem;
  font: inherit;
  cursor: pointer;
  transition:
    border-color 0.18s ease,
    background-color 0.18s ease,
    color 0.18s ease,
    box-shadow 0.18s ease;
}

.planning-shifts-tab.active {
  border-color: rgb(40 170 170 / 45%);
  background: color-mix(in srgb, rgb(40 170 170) 12%, white);
  color: var(--sp-color-text-primary);
  box-shadow: 0 10px 24px rgb(40 170 170 / 12%);
}

.planning-shifts-panel__header,
.planning-orders-panel__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}

.planning-shifts-panel__header > div,
.planning-orders-panel__header > div {
  display: grid;
  gap: 0.25rem;
}

.planning-orders-form {
  display: grid;
  gap: 0.9rem;
  padding: 1rem;
  border-radius: 18px;
  border: 1px solid var(--sp-color-border-soft);
  background: color-mix(in srgb, var(--sp-color-surface-card) 92%, white);
}

.planning-orders-form-grid,
.planning-shifts-form-grid {
  display: grid;
  gap: 0.9rem;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.planning-shifts-form-grid--controls {
  grid-template-columns: repeat(2, minmax(0, 1fr));
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

.planning-orders-list {
  display: grid;
  gap: 0.75rem;
}

.planning-orders-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 0.9rem;
  width: 100%;
  text-align: left;
  border-radius: 18px;
  border: 1px solid var(--sp-color-border-soft);
  background: color-mix(in srgb, var(--sp-color-surface-card) 90%, white);
  padding: 1rem;
  cursor: pointer;
  transition:
    border-color 0.18s ease,
    box-shadow 0.18s ease,
    transform 0.18s ease;
}

.planning-orders-row:hover {
  border-color: rgb(40 170 170 / 28%);
  box-shadow: 0 14px 34px rgb(15 23 42 / 8%);
  transform: translateY(-1px);
}

.planning-orders-row.selected {
  border-color: rgb(40 170 170 / 44%);
  box-shadow: 0 0 0 3px rgb(40 170 170 / 12%);
}

.planning-orders-row > div {
  display: grid;
  gap: 0.22rem;
}

.planning-orders-row strong {
  color: var(--sp-color-text-primary);
}

.planning-orders-row span {
  color: var(--sp-color-text-secondary);
}

.planning-orders-row--static {
  cursor: default;
}

.planning-orders-row--static:hover {
  transform: none;
}

.planning-orders-list-empty {
  margin: 0;
  padding: 1rem;
  border-radius: 16px;
  border: 1px dashed color-mix(in srgb, var(--sp-color-border) 72%, var(--sp-color-primary));
  background: color-mix(in srgb, var(--sp-color-surface-weak) 88%, white);
  color: var(--sp-color-text-secondary);
}

.planning-orders-checkbox {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--sp-color-text-secondary);
}

.planning-orders-feedback,
.planning-orders-empty {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}

.cta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  align-items: center;
}

@media (max-width: 960px) {
  .planning-shifts-hero,
  .planning-shifts-panel__header,
  .planning-orders-panel__header,
  .planning-orders-feedback,
  .planning-orders-empty {
    flex-direction: column;
    align-items: stretch;
  }

  .planning-orders-form-grid,
  .planning-shifts-form-grid,
  .planning-shifts-form-grid--controls {
    grid-template-columns: 1fr;
  }
}
</style>
