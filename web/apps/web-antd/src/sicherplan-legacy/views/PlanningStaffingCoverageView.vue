<template>
  <section class="planning-staffing-page">
    <section class="module-card planning-staffing-hero">
      <div>
        <p class="eyebrow">{{ tp("eyebrow") }}</p>
        <h2>{{ tp("title") }}</h2>
        <p class="planning-staffing-lead">{{ tp("lead") }}</p>
        <div class="planning-staffing-meta">
          <span class="planning-staffing-meta__pill">{{ tp("permissionRead") }}: {{ actionState.canReadCoverage ? "on" : "off" }}</span>
          <span class="planning-staffing-meta__pill">{{ tp("permissionWrite") }}: {{ actionState.canWriteStaffing ? "on" : "off" }}</span>
          <span class="planning-staffing-meta__pill">{{ tp("permissionOverride") }}: {{ actionState.canOverrideValidation ? "on" : "off" }}</span>
        </div>
      </div>

      <div class="module-card planning-staffing-scope">
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
          <button class="cta-button" type="button" @click="rememberScopeAndToken">{{ tp("remember") }}</button>
          <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canRefresh || loading" @click="refreshAll">{{ tp("refresh") }}</button>
        </div>
      </div>
    </section>

    <section v-if="feedback.message" class="planning-staffing-feedback" :data-tone="feedback.tone">
      <div>
        <strong>{{ feedback.title }}</strong>
        <span>{{ feedback.message }}</span>
      </div>
      <button type="button" @click="clearFeedback">{{ tp("clearFeedback") }}</button>
    </section>

    <section v-if="!tenantScopeId || !accessToken" class="module-card planning-staffing-empty">
      <p class="eyebrow">{{ tp("missingScopeTitle") }}</p>
      <h3>{{ tp("missingScopeBody") }}</h3>
    </section>

    <section v-else-if="!actionState.canReadCoverage" class="module-card planning-staffing-empty">
      <p class="eyebrow">{{ tp("missingPermissionTitle") }}</p>
      <h3>{{ tp("missingPermissionBody") }}</h3>
    </section>

    <div v-else class="planning-staffing-grid">
      <section class="module-card planning-staffing-panel">
        <div class="planning-staffing-filter-grid">
          <label class="field-stack">
            <span>{{ tp("filtersWindowFrom") }}</span>
            <input v-model="filters.date_from" type="datetime-local" />
          </label>
          <label class="field-stack">
            <span>{{ tp("filtersWindowTo") }}</span>
            <input v-model="filters.date_to" type="datetime-local" />
          </label>
          <label class="field-stack">
            <span>{{ tp("filtersPlanningRecord") }}</span>
            <input v-model="filters.planning_record_id" />
          </label>
          <label class="field-stack">
            <span>{{ tp("filtersPlanningMode") }}</span>
            <select v-model="filters.planning_mode_code">
              <option value=""></option>
              <option value="event">event</option>
              <option value="site">site</option>
              <option value="trade_fair">trade_fair</option>
              <option value="patrol">patrol</option>
            </select>
          </label>
          <label class="field-stack">
            <span>{{ tp("filtersWorkforceScope") }}</span>
            <select v-model="filters.workforce_scope_code">
              <option value=""></option>
              <option value="internal">internal</option>
              <option value="subcontractor">subcontractor</option>
              <option value="mixed">mixed</option>
            </select>
          </label>
          <label class="field-stack">
            <span>{{ tp("filtersConfirmation") }}</span>
            <select v-model="filters.confirmation_state">
              <option value=""></option>
              <option value="confirmed_only">confirmed_only</option>
            </select>
          </label>
        </div>

        <div class="planning-staffing-summary">
          <article class="planning-staffing-summary__card">
            <strong>{{ summary.total }}</strong>
            <span>{{ tp("summaryTotal") }}</span>
          </article>
          <article class="planning-staffing-summary__card" data-tone="good">
            <strong>{{ summary.green }}</strong>
            <span>{{ tp("summaryGreen") }}</span>
          </article>
          <article class="planning-staffing-summary__card" data-tone="warn">
            <strong>{{ summary.yellow }}</strong>
            <span>{{ tp("summaryYellow") }}</span>
          </article>
          <article class="planning-staffing-summary__card" data-tone="bad">
            <strong>{{ summary.red }}</strong>
            <span>{{ tp("summaryRed") }}</span>
          </article>
        </div>
      </section>

      <section class="module-card planning-staffing-panel">
        <div class="planning-staffing-panel__header">
          <div>
            <p class="eyebrow">{{ tp("listTitle") }}</p>
            <h3>{{ tp("listTitle") }}</h3>
          </div>
        </div>
        <div v-if="coverageRows.length" class="planning-staffing-list">
          <button
            v-for="row in coverageRows"
            :key="row.shift_id"
            type="button"
            class="planning-staffing-row"
            :class="{ selected: row.shift_id === selectedShiftId }"
            @click="selectedShiftId = row.shift_id"
          >
            <div>
              <strong>{{ row.starts_at }} · {{ row.shift_type_code }}</strong>
              <span>{{ tp("columnOrder") }}: {{ row.order_no }}</span>
              <span>{{ tp("columnPlanning") }}: {{ row.planning_record_name }}</span>
            </div>
            <span class="planning-staffing-state" :data-tone="coverageTone(row.coverage_state)">
              {{ tp(statusKey(row.coverage_state)) }}
            </span>
          </button>
        </div>
        <p v-else class="planning-staffing-list-empty">{{ tp("listEmpty") }}</p>
      </section>

      <section class="module-card planning-staffing-panel planning-staffing-detail">
        <div class="planning-staffing-panel__header">
          <div>
            <p class="eyebrow">{{ tp("detailTitle") }}</p>
            <h3>{{ selectedShift ? `${selectedShift.order_no} · ${selectedShift.shift_type_code}` : tp("detailTitle") }}</h3>
          </div>
          <span v-if="selectedShift" class="planning-staffing-state" :data-tone="coverageTone(selectedShift.coverage_state)">
            {{ tp(statusKey(selectedShift.coverage_state)) }}
          </span>
        </div>

        <template v-if="selectedShift">
          <div class="planning-staffing-metrics">
            <span>{{ tp("columnMin") }}: {{ selectedShift.min_required_qty }}</span>
            <span>{{ tp("columnTarget") }}: {{ selectedShift.target_required_qty }}</span>
            <span>{{ tp("columnAssigned") }}: {{ selectedShift.assigned_count }}</span>
            <span>{{ tp("columnConfirmed") }}: {{ selectedShift.confirmed_count }}</span>
            <span>{{ tp("columnReleased") }}: {{ selectedShift.released_partner_qty }}</span>
          </div>

          <section class="module-card planning-staffing-subpanel">
            <div class="planning-staffing-panel__header">
              <div>
                <p class="eyebrow">{{ tp("validationTitle") }}</p>
                <h4>{{ tp("validationTitle") }}</h4>
              </div>
              <div class="planning-staffing-metrics">
                <span>{{ tp("validationBlock") }}: {{ shiftValidationSummary.blocking }}</span>
                <span>{{ tp("validationWarn") }}: {{ shiftValidationSummary.warnings }}</span>
                <span>{{ tp("validationInfo") }}: {{ shiftValidationSummary.infos }}</span>
                <span>{{ tp("validationOverrideable") }}: {{ shiftValidationSummary.overrideable }}</span>
              </div>
            </div>
            <div v-if="shiftValidations?.issues?.length" class="planning-staffing-issues">
              <article v-for="issue in shiftValidations.issues" :key="`shift-${issue.rule_code}-${issue.demand_group_id ?? 'all'}`" class="planning-staffing-issue" :data-tone="validationTone(issue.severity)">
                <strong>{{ ruleText(issue.rule_code) }}</strong>
                <span>{{ issue.message_key }}</span>
              </article>
            </div>
            <p v-else class="planning-staffing-list-empty">{{ tp("validationEmpty") }}</p>
          </section>

          <section class="module-card planning-staffing-subpanel">
            <div class="planning-staffing-panel__header">
              <div>
                <p class="eyebrow">{{ tp("assignmentsTitle") }}</p>
                <h4>{{ tp("assignmentsTitle") }}</h4>
              </div>
            </div>
            <div v-if="selectedBoardShift?.assignments?.length" class="planning-staffing-list">
              <button
                v-for="assignment in selectedBoardShift.assignments"
                :key="assignment.id"
                type="button"
                class="planning-staffing-row"
                :class="{ selected: assignment.id === selectedAssignmentId }"
                @click="selectedAssignmentId = assignment.id"
              >
                <div>
                  <strong>{{ actorLabel(assignment) }}</strong>
                  <span>{{ assignment.assignment_status_code }} · {{ assignment.assignment_source_code }}</span>
                </div>
              </button>
            </div>
            <p v-else class="planning-staffing-list-empty">{{ tp("assignmentsEmpty") }}</p>
          </section>

          <section class="module-card planning-staffing-subpanel">
            <div class="planning-staffing-panel__header">
              <div>
                <p class="eyebrow">{{ tp("assignmentValidationTitle") }}</p>
                <h4>{{ selectedAssignmentId ? selectedAssignmentId : tp("assignmentValidationTitle") }}</h4>
              </div>
              <div class="planning-staffing-metrics">
                <span>{{ tp("validationBlock") }}: {{ assignmentValidationSummary.blocking }}</span>
                <span>{{ tp("validationWarn") }}: {{ assignmentValidationSummary.warnings }}</span>
                <span>{{ tp("validationInfo") }}: {{ assignmentValidationSummary.infos }}</span>
                <span>{{ tp("validationOverrideable") }}: {{ assignmentValidationSummary.overrideable }}</span>
              </div>
            </div>

            <div v-if="assignmentValidations?.issues?.length" class="planning-staffing-issues">
              <article v-for="issue in assignmentValidations.issues" :key="`assignment-${issue.rule_code}`" class="planning-staffing-issue" :data-tone="validationTone(issue.severity)">
                <div class="planning-staffing-panel__header">
                  <div>
                    <strong>{{ ruleText(issue.rule_code) }}</strong>
                    <span>{{ issue.message_key }}</span>
                  </div>
                  <button
                    v-if="actionState.canOverrideValidation && issue.override_allowed"
                    class="cta-button cta-secondary"
                    type="button"
                    @click="startOverride(issue.rule_code)"
                  >
                    {{ tp("overrideAction") }}
                  </button>
                </div>
                <span v-if="!issue.override_allowed && issue.severity === 'block'">{{ tp("overrideUnavailable") }}</span>
              </article>
            </div>
            <p v-else class="planning-staffing-list-empty">{{ tp("assignmentValidationEmpty") }}</p>
          </section>

          <section class="module-card planning-staffing-subpanel">
            <div class="planning-staffing-panel__header">
              <div>
                <p class="eyebrow">{{ tp("assignmentOverridesTitle") }}</p>
                <h4>{{ tp("assignmentOverridesTitle") }}</h4>
              </div>
            </div>
            <div v-if="assignmentOverrides.length" class="planning-staffing-issues">
              <article v-for="row in assignmentOverrides" :key="row.id" class="planning-staffing-issue" data-tone="neutral">
                <strong>{{ ruleText(row.rule_code) }}</strong>
                <span>{{ row.reason_text }}</span>
                <span>{{ row.created_at }}</span>
              </article>
            </div>
            <p v-else class="planning-staffing-list-empty">{{ tp("assignmentOverridesEmpty") }}</p>
          </section>

          <section class="module-card planning-staffing-subpanel">
            <div class="planning-staffing-panel__header">
              <div>
                <p class="eyebrow">{{ tp("outputsTitle") }}</p>
                <h4>{{ tp("outputsTitle") }}</h4>
              </div>
              <div class="cta-row">
                <button class="cta-button cta-secondary" type="button" :disabled="!selectedShiftId || loading" @click="generateOutput('internal')">
                  {{ tp("generateInternalOutput") }}
                </button>
                <button class="cta-button cta-secondary" type="button" :disabled="!selectedShiftId || loading" @click="generateOutput('customer')">
                  {{ tp("generateCustomerOutput") }}
                </button>
              </div>
            </div>
            <div v-if="shiftOutputs.length" class="planning-staffing-issues">
              <article v-for="output in shiftOutputs" :key="output.document_id" class="planning-staffing-issue" data-tone="neutral">
                <strong>{{ output.title }}</strong>
                <span>{{ output.variant_code }} · {{ output.audience_code }}</span>
                <span>{{ output.file_name }}</span>
              </article>
            </div>
            <p v-else class="planning-staffing-list-empty">{{ tp("outputsEmpty") }}</p>
          </section>

          <section class="module-card planning-staffing-subpanel">
            <div class="planning-staffing-panel__header">
              <div>
                <p class="eyebrow">{{ tp("dispatchTitle") }}</p>
                <h4>{{ tp("dispatchTitle") }}</h4>
              </div>
            </div>
            <div class="cta-row">
              <label><input v-model="dispatchAudienceEmployees" type="checkbox" /> {{ tp("dispatchAudienceEmployees") }}</label>
              <label><input v-model="dispatchAudienceSubcontractors" type="checkbox" /> {{ tp("dispatchAudienceSubcontractors") }}</label>
            </div>
            <div class="cta-row">
              <button class="cta-button cta-secondary" type="button" :disabled="!selectedShiftId || loading" @click="loadDispatchPreview">
                {{ tp("dispatchPreviewAction") }}
              </button>
              <button class="cta-button" type="button" :disabled="!selectedShiftId || loading" @click="queueDispatch">
                {{ tp("dispatchQueueAction") }}
              </button>
            </div>
            <div v-if="dispatchPreview" class="planning-staffing-issues">
              <article class="planning-staffing-issue" :data-tone="dispatchPreview.redacted ? 'warn' : 'neutral'">
                <strong>{{ dispatchPreview.subject_preview || tp("dispatchTitle") }}</strong>
                <span>{{ dispatchPreview.body_preview }}</span>
                <span>{{ tp("dispatchRecipients") }}: {{ dispatchPreview.recipients.length }}</span>
              </article>
            </div>
            <p v-else class="planning-staffing-list-empty">{{ tp("dispatchPreviewEmpty") }}</p>
          </section>

          <section v-if="overrideRuleCode" class="module-card planning-staffing-subpanel">
            <div class="planning-staffing-panel__header">
              <div>
                <p class="eyebrow">{{ tp("overrideTitle") }}</p>
                <h4>{{ ruleText(overrideRuleCode) }}</h4>
              </div>
            </div>
            <label class="field-stack">
              <span>{{ tp("overrideReasonLabel") }}</span>
              <textarea v-model="overrideReason" rows="4" :placeholder="tp('overrideReasonPlaceholder')" />
            </label>
            <p class="field-help">{{ tp("overrideHint") }}</p>
            <div class="cta-row">
              <button class="cta-button" type="button" :disabled="!actionState.canOverrideValidation || overrideReason.trim().length < 3 || savingOverride" @click="submitOverride">
                {{ tp("overrideAction") }}
              </button>
              <button class="cta-button cta-secondary" type="button" :disabled="savingOverride" @click="cancelOverride">
                {{ tp("clearFeedback") }}
              </button>
            </div>
          </section>
        </template>

        <p v-else class="planning-staffing-list-empty">{{ tp("noSelection") }}</p>
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";

import {
  createAssignmentValidationOverride,
  generateShiftOutput,
  getAssignmentValidations,
  listShiftOutputs,
  previewShiftDispatchMessage,
  queueShiftDispatchMessage,
  getShiftReleaseValidations,
  listAssignmentValidationOverrides,
  listStaffingBoard,
  listStaffingCoverage,
  PlanningStaffingApiError,
  type AssignmentValidationRead,
  type CoverageShiftItem,
  type PlanningDispatchPreviewRead,
  type PlanningOutputDocumentRead,
  type ShiftReleaseValidationRead,
  type StaffingBoardShiftItem,
} from "@/api/planningStaffing";
import { planningStaffingMessages } from "@/i18n/planningStaffing.messages";
import {
  actorLabel,
  coverageTone,
  derivePlanningStaffingActionState,
  mapPlanningStaffingApiMessage,
  summarizeCoverage,
  summarizeValidations,
  validationTone,
} from "@/features/planning/planningStaffing.helpers";

const RULE_TEXT_MAP = {
  function_match: "ruleFunctionMatch",
  qualification_match: "ruleQualificationMatch",
  certificate_validity: "ruleCertificateValidity",
  mandatory_documents: "ruleMandatoryDocuments",
  customer_block: "ruleCustomerBlock",
  double_booking: "ruleDoubleBooking",
  rest_period: "ruleRestPeriod",
  max_hours: "ruleMaxHours",
  earnings_threshold: "ruleEarningsThreshold",
  minimum_staffing: "ruleMinimumStaffing",
} as const;

const currentLocale = ref<"de" | "en">("de");
const role = ref("dispatcher");
const tenantScopeInput = ref(globalThis.localStorage?.getItem("planning-staffing.tenant") ?? "");
const accessTokenInput = ref(globalThis.localStorage?.getItem("planning-staffing.token") ?? "");
const tenantScopeId = ref(tenantScopeInput.value.trim());
const accessToken = ref(accessTokenInput.value.trim());
const coverageRows = ref<CoverageShiftItem[]>([]);
const boardRows = ref<StaffingBoardShiftItem[]>([]);
const selectedShiftId = ref("");
const selectedAssignmentId = ref("");
const shiftValidations = ref<ShiftReleaseValidationRead | null>(null);
const assignmentValidations = ref<AssignmentValidationRead | null>(null);
const assignmentOverrides = ref<any[]>([]);
const shiftOutputs = ref<PlanningOutputDocumentRead[]>([]);
const dispatchPreview = ref<PlanningDispatchPreviewRead | null>(null);
const dispatchAudienceEmployees = ref(true);
const dispatchAudienceSubcontractors = ref(false);
const overrideRuleCode = ref("");
const overrideReason = ref("");
const loading = ref(false);
const savingOverride = ref(false);
const feedback = reactive({ message: "", title: "", tone: "error" });
const filters = reactive({
  date_from: "2026-04-05T00:00",
  date_to: "2026-04-06T00:00",
  planning_record_id: "",
  planning_mode_code: "",
  workforce_scope_code: "",
  confirmation_state: "",
});

function tp(key: keyof typeof planningStaffingMessages.de) {
  return planningStaffingMessages[currentLocale.value][key] ?? planningStaffingMessages.de[key] ?? key;
}

const selectedShift = computed(() => coverageRows.value.find((row) => row.shift_id === selectedShiftId.value) ?? null);
const selectedBoardShift = computed(() => boardRows.value.find((row) => row.id === selectedShiftId.value) ?? null);
const selectedIssue = computed(() => assignmentValidations.value?.issues.find((issue) => issue.rule_code === overrideRuleCode.value) ?? null);
const actionState = computed(() =>
  derivePlanningStaffingActionState(role.value, selectedShift.value, selectedAssignmentId.value ? { id: selectedAssignmentId.value } : null, selectedIssue.value),
);
const summary = computed(() => summarizeCoverage(coverageRows.value));
const shiftValidationSummary = computed(() => summarizeValidations(shiftValidations.value));
const assignmentValidationSummary = computed(() => summarizeValidations(assignmentValidations.value));

function clearFeedback() {
  feedback.message = "";
  feedback.title = "";
  feedback.tone = "error";
}

function setFeedback(tone: string, title: string, message: string) {
  feedback.tone = tone;
  feedback.title = title;
  feedback.message = message;
}

function rememberScopeAndToken() {
  tenantScopeId.value = tenantScopeInput.value.trim();
  accessToken.value = accessTokenInput.value.trim();
  globalThis.localStorage?.setItem("planning-staffing.tenant", tenantScopeId.value);
  globalThis.localStorage?.setItem("planning-staffing.token", accessToken.value);
}

function statusKey(state: string) {
  if (state === "green") {
    return "statusGreen";
  }
  if (state === "yellow") {
    return "statusYellow";
  }
  return "statusRed";
}

function ruleText(ruleCode: string) {
  const key = RULE_TEXT_MAP[ruleCode as keyof typeof RULE_TEXT_MAP];
  return key ? tp(key) : ruleCode;
}

function queryFilters() {
  return { ...filters };
}

async function refreshAll() {
  clearFeedback();
  if (!tenantScopeId.value || !accessToken.value) {
    return;
  }
  loading.value = true;
  try {
    const [coverage, board] = await Promise.all([
      listStaffingCoverage(tenantScopeId.value, accessToken.value, queryFilters()),
      listStaffingBoard(tenantScopeId.value, accessToken.value, queryFilters()),
    ]);
    coverageRows.value = coverage;
    boardRows.value = board;
    if (!coverageRows.value.find((row) => row.shift_id === selectedShiftId.value)) {
      selectedShiftId.value = coverageRows.value[0]?.shift_id ?? "";
    }
    if (!selectedShiftId.value) {
      shiftValidations.value = null;
      assignmentValidations.value = null;
      assignmentOverrides.value = [];
      shiftOutputs.value = [];
      dispatchPreview.value = null;
      selectedAssignmentId.value = "";
      return;
    }
    await loadSelectedShiftDetails();
  } catch (error) {
    handleApiError(error);
  } finally {
    loading.value = false;
  }
}

async function loadSelectedShiftDetails() {
  if (!tenantScopeId.value || !accessToken.value || !selectedShiftId.value) {
    return;
  }
  shiftValidations.value = await getShiftReleaseValidations(tenantScopeId.value, accessToken.value, selectedShiftId.value);
  shiftOutputs.value = await listShiftOutputs(tenantScopeId.value, accessToken.value, selectedShiftId.value);
  const boardShift = selectedBoardShift.value;
  if (!boardShift?.assignments?.length) {
    selectedAssignmentId.value = "";
    assignmentValidations.value = null;
    assignmentOverrides.value = [];
    return;
  }
  if (!boardShift.assignments.some((row) => row.id === selectedAssignmentId.value)) {
    selectedAssignmentId.value = boardShift.assignments[0].id;
  }
  await loadSelectedAssignmentDetails();
}

function dispatchAudienceCodes() {
  const codes = [];
  if (dispatchAudienceEmployees.value) {
    codes.push("assigned_employees");
  }
  if (dispatchAudienceSubcontractors.value) {
    codes.push("subcontractor_release");
  }
  return codes;
}

async function loadDispatchPreview() {
  if (!tenantScopeId.value || !accessToken.value || !selectedShiftId.value) {
    return;
  }
  dispatchPreview.value = await previewShiftDispatchMessage(tenantScopeId.value, accessToken.value, selectedShiftId.value, {
    tenant_id: tenantScopeId.value,
    shift_id: selectedShiftId.value,
    audience_codes: dispatchAudienceCodes(),
  });
}

async function queueDispatch() {
  if (!tenantScopeId.value || !accessToken.value || !selectedShiftId.value) {
    return;
  }
  await queueShiftDispatchMessage(tenantScopeId.value, accessToken.value, selectedShiftId.value, {
    tenant_id: tenantScopeId.value,
    shift_id: selectedShiftId.value,
    audience_codes: dispatchAudienceCodes(),
  });
  setFeedback("good", tp("dispatchTitle"), tp("dispatchQueuedSuccess"));
}

async function generateOutput(audienceCode: "customer" | "internal") {
  if (!tenantScopeId.value || !accessToken.value || !selectedShiftId.value) {
    return;
  }
  await generateShiftOutput(tenantScopeId.value, accessToken.value, selectedShiftId.value, {
    tenant_id: tenantScopeId.value,
    variant_code: "deployment_plan",
    audience_code: audienceCode,
  });
  shiftOutputs.value = await listShiftOutputs(tenantScopeId.value, accessToken.value, selectedShiftId.value);
}

async function loadSelectedAssignmentDetails() {
  if (!tenantScopeId.value || !accessToken.value || !selectedAssignmentId.value) {
    assignmentValidations.value = null;
    assignmentOverrides.value = [];
    return;
  }
  const [validations, overrides] = await Promise.all([
    getAssignmentValidations(tenantScopeId.value, accessToken.value, selectedAssignmentId.value),
    listAssignmentValidationOverrides(tenantScopeId.value, accessToken.value, selectedAssignmentId.value),
  ]);
  assignmentValidations.value = validations;
  assignmentOverrides.value = overrides;
  if (overrideRuleCode.value && !validations.issues.some((issue) => issue.rule_code === overrideRuleCode.value && issue.override_allowed)) {
    cancelOverride();
  }
}

function startOverride(ruleCode: string) {
  overrideRuleCode.value = ruleCode;
  overrideReason.value = "";
}

function cancelOverride() {
  overrideRuleCode.value = "";
  overrideReason.value = "";
}

async function submitOverride() {
  if (!tenantScopeId.value || !accessToken.value || !selectedAssignmentId.value || !overrideRuleCode.value) {
    return;
  }
  savingOverride.value = true;
  clearFeedback();
  try {
    await createAssignmentValidationOverride(tenantScopeId.value, accessToken.value, selectedAssignmentId.value, {
      tenant_id: tenantScopeId.value,
      rule_code: overrideRuleCode.value,
      reason_text: overrideReason.value.trim(),
    });
    setFeedback("good", tp("overrideTitle"), tp("saveSuccess"));
    cancelOverride();
    await loadSelectedAssignmentDetails();
    await loadSelectedShiftDetails();
  } catch (error) {
    handleApiError(error);
  } finally {
    savingOverride.value = false;
  }
}

function handleApiError(error: unknown) {
  if (error instanceof PlanningStaffingApiError) {
    const key = mapPlanningStaffingApiMessage(error.messageKey);
    setFeedback("error", tp("title"), tp(key));
    return;
  }
  setFeedback("error", tp("title"), tp("error"));
}

watch(selectedShiftId, async () => {
  if (!loading.value) {
    try {
      await loadSelectedShiftDetails();
    } catch (error) {
      handleApiError(error);
    }
  }
});

watch(selectedAssignmentId, async () => {
  if (!loading.value) {
    try {
      await loadSelectedAssignmentDetails();
    } catch (error) {
      handleApiError(error);
    }
  }
});
</script>

<style scoped>
.planning-staffing-page,
.planning-staffing-grid,
.planning-staffing-filter-grid,
.planning-staffing-summary,
.planning-staffing-detail,
.planning-staffing-metrics,
.planning-staffing-issues {
  display: grid;
  gap: 1rem;
}

.planning-staffing-grid {
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
}

.planning-staffing-hero {
  display: grid;
  gap: 1rem;
  grid-template-columns: minmax(0, 1.8fr) minmax(0, 1fr);
}

.planning-staffing-meta,
.planning-staffing-metrics,
.planning-staffing-panel__header,
.planning-staffing-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  justify-content: space-between;
  align-items: center;
}

.planning-staffing-meta__pill,
.planning-staffing-state,
.planning-staffing-summary__card,
.planning-staffing-issue {
  border: 1px solid rgba(40, 170, 170, 0.18);
  border-radius: 16px;
  padding: 0.75rem 0.9rem;
  background: rgba(40, 170, 170, 0.06);
}

.planning-staffing-row,
.planning-staffing-subpanel {
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 18px;
  padding: 1rem;
  background: #fff;
}

.planning-staffing-row {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  text-align: left;
}

.planning-staffing-row.selected {
  border-color: rgb(40, 170, 170);
  box-shadow: 0 0 0 1px rgba(40, 170, 170, 0.2);
}

.planning-staffing-issue {
  display: grid;
  gap: 0.35rem;
}

.planning-staffing-issue[data-tone="good"],
.planning-staffing-state[data-tone="good"],
.planning-staffing-summary__card[data-tone="good"] {
  background: rgba(24, 160, 88, 0.12);
  border-color: rgba(24, 160, 88, 0.24);
}

.planning-staffing-issue[data-tone="warn"],
.planning-staffing-state[data-tone="warn"],
.planning-staffing-summary__card[data-tone="warn"] {
  background: rgba(214, 158, 46, 0.12);
  border-color: rgba(214, 158, 46, 0.28);
}

.planning-staffing-issue[data-tone="bad"],
.planning-staffing-state[data-tone="bad"],
.planning-staffing-summary__card[data-tone="bad"] {
  background: rgba(220, 38, 38, 0.12);
  border-color: rgba(220, 38, 38, 0.24);
}

.planning-staffing-issue[data-tone="neutral"] {
  background: rgba(15, 23, 42, 0.04);
  border-color: rgba(15, 23, 42, 0.12);
}

@media (max-width: 900px) {
  .planning-staffing-hero {
    grid-template-columns: 1fr;
  }
}
</style>
