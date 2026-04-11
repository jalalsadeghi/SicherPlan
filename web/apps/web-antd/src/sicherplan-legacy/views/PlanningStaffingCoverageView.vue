<template>
  <section class="planning-staffing-page">
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

    <div v-else class="planning-staffing-grid" data-testid="planning-staffing-workspace">
      <section class="module-card planning-staffing-panel">
        <div class="planning-staffing-panel__header planning-staffing-panel__header--filters">
          <div>
            <p class="eyebrow">{{ tp("filtersTitle") }}</p>
            <h3>{{ tp("filtersTitle") }}</h3>
            <p class="planning-staffing-panel__lead">
              {{ tp("roleLabel") }}: {{ role }} · {{ tp("tenantScopeLabel") }}: {{ tenantScopeId || tp("scopeUnavailable") }}
            </p>
          </div>
          <div class="cta-row planning-staffing-panel__actions">
            <button
              class="cta-button cta-secondary"
              type="button"
              data-testid="planning-staffing-refresh"
              :disabled="loading"
              @click="refreshAll"
            >
              {{ tp("refresh") }}
            </button>
            <a class="cta-button cta-secondary" href="/admin/employees">{{ tp("openEmployeesAdmin") }}</a>
            <a class="cta-button cta-secondary" href="/admin/subcontractors">{{ tp("openSubcontractorsAdmin") }}</a>
          </div>
        </div>
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
            <Select
              :value="filters.planning_record_id || undefined"
              show-search
              allow-clear
              class="planning-staffing-select"
              popup-class-name="planning-staffing-select-dropdown"
              :loading="planningRecordLookupLoading"
              :filter-option="false"
              :options="planningRecordSelectOptions"
              :placeholder="tp('filtersPlanningRecordPlaceholder')"
              data-testid="planning-staffing-planning-record-select"
              @search="handlePlanningRecordSearch"
              @change="handlePlanningRecordSelection"
              @clear="clearPlanningRecordSelection"
            />
            <p v-if="planningRecordLookupLoading" class="field-help">{{ tp("filtersPlanningRecordLoading") }}</p>
            <p v-else-if="planningRecordLookupError" class="field-help">{{ planningRecordLookupError }}</p>
            <p v-else-if="!planningRecordOptions.length" class="field-help">{{ tp("filtersPlanningRecordEmpty") }}</p>
            <p
              v-else-if="filters.planning_record_id && !selectedPlanningRecordOptionLabel"
              class="field-help"
            >
              {{ tp("filtersPlanningRecordNoMatch") }}
            </p>
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

        <div class="planning-staffing-meta">
          <span class="planning-staffing-meta__pill">{{ tp("permissionRead") }}: {{ actionState.canReadCoverage ? "on" : "off" }}</span>
          <span class="planning-staffing-meta__pill">{{ tp("permissionWrite") }}: {{ actionState.canWriteStaffing ? "on" : "off" }}</span>
          <span class="planning-staffing-meta__pill">{{ tp("permissionOverride") }}: {{ actionState.canOverrideValidation ? "on" : "off" }}</span>
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
                <p class="eyebrow">{{ tp("demandGroupsTitle") }}</p>
                <h4>{{ tp("demandGroupsTitle") }}</h4>
              </div>
            </div>
            <div v-if="selectedBoardShift?.demand_groups?.length" class="planning-staffing-demand-groups" data-testid="planning-staffing-demand-group-list">
              <button
                v-for="group in selectedBoardShift.demand_groups"
                :key="group.id"
                type="button"
                class="planning-staffing-demand-group"
                :class="{ selected: group.id === selectedDemandGroupId }"
                @click="selectedDemandGroupId = group.id"
              >
                <strong>{{ formatDemandGroup(group) }}</strong>
                <span>{{ tp("columnMin") }} {{ group.min_qty }} · {{ tp("columnTarget") }} {{ group.target_qty }}</span>
                <span>{{ tp("columnAssigned") }} {{ group.assigned_count }} · {{ tp("columnConfirmed") }} {{ group.confirmed_count }}</span>
              </button>
            </div>
            <p v-else class="planning-staffing-list-empty">{{ tp("demandGroupsEmpty") }}</p>
          </section>

          <section class="module-card planning-staffing-subpanel">
            <div class="planning-staffing-panel__header">
              <div>
                <p class="eyebrow">{{ tp("staffingActionsTitle") }}</p>
                <h4>{{ tp("staffingActionsTitle") }}</h4>
              </div>
              <span class="field-help">{{ tp("staffingActionsHint") }}</span>
            </div>
            <div class="planning-staffing-filter-grid">
              <label class="field-stack">
                <span>{{ tp("fieldsDemandGroup") }}</span>
                <select v-model="selectedDemandGroupId">
                  <option value="">{{ tp("demandGroupPlaceholder") }}</option>
                  <option v-for="group in selectedBoardShift?.demand_groups ?? []" :key="group.id" :value="group.id">
                    {{ formatDemandGroup(group) }}
                  </option>
                </select>
              </label>
              <label class="field-stack">
                <span>{{ tp("fieldsActorKind") }}</span>
                <select v-model="staffingDraft.actor_kind">
                  <option value="team">{{ tp("actorKindTeam") }}</option>
                  <option value="employee">{{ tp("actorKindEmployee") }}</option>
                  <option value="subcontractor_worker">{{ tp("actorKindSubcontractorWorker") }}</option>
                </select>
              </label>
              <label class="field-stack">
                <span>{{ tp("fieldsTeam") }}</span>
                <select v-model="staffingDraft.team_id" data-testid="planning-staffing-team-select">
                  <option value="">{{ tp("teamPlaceholder") }}</option>
                  <option v-for="team in shiftTeams" :key="team.id" :value="team.id">
                    {{ team.name }}
                  </option>
                </select>
              </label>
              <label v-if="staffingDraft.actor_kind !== 'team'" class="field-stack">
                <span>{{ staffingDraft.actor_kind === 'employee' ? tp("fieldsEmployee") : tp("fieldsSubcontractorWorker") }}</span>
                <select v-model="staffingDraft.member_ref">
                  <option value="">{{ tp("memberPlaceholder") }}</option>
                  <option v-for="member in selectableTeamMembers" :key="member.id" :value="member.id">
                    {{ formatMember(member) }}
                  </option>
                </select>
              </label>
              <label class="field-stack">
                <span>{{ tp("fieldsAssignmentSource") }}</span>
                <select v-model="staffingDraft.assignment_source_code">
                  <option value="dispatcher">dispatcher</option>
                  <option value="manual">manual</option>
                  <option value="subcontractor_release">subcontractor_release</option>
                </select>
              </label>
              <label class="field-stack">
                <span>{{ tp("fieldsConfirmNow") }}</span>
                <input v-model="staffingDraft.confirm_now" type="checkbox" />
              </label>
              <label class="field-stack field-stack--wide">
                <span>{{ tp("fieldsRemarks") }}</span>
                <textarea v-model="staffingDraft.remarks" rows="2" />
              </label>
            </div>
            <div class="cta-row">
              <button
                class="cta-button"
                data-testid="planning-staffing-assign-action"
                type="button"
                :disabled="!canSubmitAssign || loading"
                @click="submitAssign"
              >
                {{ tp("assignAction") }}
              </button>
              <button
                class="cta-button cta-secondary"
                data-testid="planning-staffing-substitute-action"
                type="button"
                :disabled="!canSubmitSubstitute || loading"
                @click="submitSubstitute"
              >
                {{ tp("substituteAction") }}
              </button>
              <button
                class="cta-button cta-secondary"
                data-testid="planning-staffing-unassign-action"
                type="button"
                :disabled="!selectedAssignment || !actionState.canUnassign || loading"
                @click="submitUnassign"
              >
                {{ tp("unassignAction") }}
              </button>
            </div>
          </section>

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
            <div v-if="selectedAssignment" class="planning-staffing-metrics">
              <span>{{ tp("fieldsDemandGroup") }}: {{ selectedAssignment.demand_group_id }}</span>
              <span>{{ tp("fieldsVersion") }}: {{ selectedAssignment.version_no }}</span>
              <span>{{ tp("fieldsTeam") }}: {{ selectedAssignment.team_id || tp("unassignedLabel") }}</span>
            </div>
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
                <p class="eyebrow">{{ tp("teamReleaseTitle") }}</p>
                <h4>{{ tp("teamReleaseTitle") }}</h4>
              </div>
            </div>
            <div class="planning-staffing-support-grid">
              <article class="planning-staffing-support-card">
                <strong>{{ tp("teamsTitle") }}</strong>
                <p v-if="shiftTeams.length" class="planning-staffing-support-list">
                  <span v-for="team in shiftTeams" :key="team.id">{{ team.name }} · {{ team.members.length }}</span>
                </p>
                <p v-else class="planning-staffing-list-empty">{{ tp("teamsEmpty") }}</p>
              </article>
              <article class="planning-staffing-support-card">
                <strong>{{ tp("subcontractorReleasesTitle") }}</strong>
                <p v-if="subcontractorReleases.length" class="planning-staffing-support-list">
                  <span v-for="release in subcontractorReleases" :key="release.id">{{ release.subcontractor_id }} · {{ release.released_qty }}</span>
                </p>
                <p v-else class="planning-staffing-list-empty">{{ tp("subcontractorReleasesEmpty") }}</p>
              </article>
            </div>
            <div class="cta-row">
              <a class="cta-button cta-secondary" href="/admin/employees">{{ tp("openEmployeesAdmin") }}</a>
              <a class="cta-button cta-secondary" href="/admin/subcontractors">{{ tp("openSubcontractorsAdmin") }}</a>
            </div>
          </section>

          <section class="module-card planning-staffing-subpanel">
            <div class="planning-staffing-panel__header">
              <div>
                <p class="eyebrow">{{ tp("outputsTitle") }}</p>
                <h4>{{ tp("outputsTitle") }}</h4>
              </div>
              <div class="cta-row">
                <button class="cta-button cta-secondary" type="button" :disabled="!selectedShiftId || loading || !actionState.canManageRelease" @click="generateOutput('internal')">
                  {{ tp("generateInternalOutput") }}
                </button>
                <button class="cta-button cta-secondary" type="button" :disabled="!selectedShiftId || loading || !actionState.canManageRelease" @click="generateOutput('customer')">
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
              <button class="cta-button cta-secondary" type="button" :disabled="!selectedShiftId || loading || !actionState.canDispatch" @click="loadDispatchPreview">
                {{ tp("dispatchPreviewAction") }}
              </button>
              <button class="cta-button" type="button" :disabled="!selectedShiftId || loading || !actionState.canDispatch" @click="queueDispatch">
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
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import { Select } from "ant-design-vue";

import { useAuthStore as usePrimaryAuthStore } from "#/store";
import { listPlanningRecords, type PlanningRecordListItem } from "@/api/planningOrders";
import {
  assignStaffing,
  createAssignmentValidationOverride,
  generateShiftOutput,
  getAssignmentValidations,
  getShiftReleaseValidations,
  listAssignmentValidationOverrides,
  listShiftOutputs,
  listStaffingBoard,
  listStaffingCoverage,
  listSubcontractorReleases,
  listTeamMembers,
  listTeams,
  previewShiftDispatchMessage,
  queueShiftDispatchMessage,
  substituteStaffing,
  unassignStaffing,
  PlanningStaffingApiError,
  type AssignmentValidationRead,
  type CoverageShiftItem,
  type PlanningDispatchPreviewRead,
  type PlanningOutputDocumentRead,
  type ShiftReleaseValidationRead,
  type StaffingBoardAssignmentItem,
  type StaffingBoardDemandGroupItem,
  type StaffingBoardShiftItem,
  type SubcontractorReleaseRead,
  type TeamMemberRead,
  type TeamRead,
} from "@/api/planningStaffing";
import { planningStaffingMessages } from "@/i18n/planningStaffing.messages";
import { useAuthStore } from "@/stores/auth";
import { useLocaleStore } from "@/stores/locale";
import {
  actorLabel,
  buildPlanningStaffingPlanningRecordLookupFilters,
  formatPlanningStaffingPlanningRecordOption,
  buildStaffingMemberOptions,
  coverageTone,
  derivePlanningStaffingActionState,
  mapPlanningStaffingApiMessage,
  normalizePlanningStaffingLookupDate,
  resolveSelectedDemandGroupId,
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

const primaryAuthStore = usePrimaryAuthStore();
const authStore = useAuthStore();
const localeStore = useLocaleStore();

const currentLocale = computed<"de" | "en">(() => (localeStore.locale === "en" ? "en" : "de"));
const role = computed(() => authStore.effectiveRole || "tenant_admin");
const tenantScopeId = computed(() => authStore.effectiveTenantScopeId || authStore.tenantScopeId || "");
const accessToken = computed(() => authStore.effectiveAccessToken || authStore.accessToken || "");

const coverageRows = ref<CoverageShiftItem[]>([]);
const boardRows = ref<StaffingBoardShiftItem[]>([]);
const shiftTeams = ref<TeamRead[]>([]);
const teamMembers = ref<TeamMemberRead[]>([]);
const subcontractorReleases = ref<SubcontractorReleaseRead[]>([]);
const selectedShiftId = ref("");
const selectedDemandGroupId = ref("");
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
const planningRecordOptions = ref<PlanningRecordListItem[]>([]);
const planningRecordLookupLoading = ref(false);
const planningRecordLookupError = ref("");
const planningRecordLookupSearch = ref("");
const feedback = reactive({ message: "", title: "", tone: "error" });
const filters = reactive({
  date_from: "2026-04-05T00:00",
  date_to: "2026-04-06T00:00",
  planning_record_id: "",
  planning_mode_code: "",
  workforce_scope_code: "",
  confirmation_state: "",
});
const staffingDraft = reactive({
  actor_kind: "team",
  team_id: "",
  member_ref: "",
  assignment_source_code: "dispatcher",
  confirm_now: false,
  remarks: "",
});

function tp(key: keyof typeof planningStaffingMessages.de) {
  return planningStaffingMessages[currentLocale.value][key] ?? planningStaffingMessages.de[key] ?? key;
}

const selectedShift = computed(() => coverageRows.value.find((row) => row.shift_id === selectedShiftId.value) ?? null);
const selectedBoardShift = computed(() => boardRows.value.find((row) => row.id === selectedShiftId.value) ?? null);
const selectedAssignment = computed<StaffingBoardAssignmentItem | null>(
  () => selectedBoardShift.value?.assignments.find((row) => row.id === selectedAssignmentId.value) ?? null,
);
const selectedDemandGroup = computed<StaffingBoardDemandGroupItem | null>(
  () => selectedBoardShift.value?.demand_groups.find((row) => row.id === selectedDemandGroupId.value) ?? null,
);
const selectedIssue = computed(() => assignmentValidations.value?.issues.find((issue) => issue.rule_code === overrideRuleCode.value) ?? null);
const actionState = computed(() =>
  derivePlanningStaffingActionState(role.value, selectedShift.value, selectedAssignment.value, selectedIssue.value),
);
const summary = computed(() => summarizeCoverage(coverageRows.value));
const shiftValidationSummary = computed(() => summarizeValidations(shiftValidations.value));
const assignmentValidationSummary = computed(() => summarizeValidations(assignmentValidations.value));
const planningRecordSelectOptions = computed(() =>
  planningRecordOptions.value.map((record) => ({
    label: formatPlanningStaffingPlanningRecordOption(record),
    value: record.id,
  })),
);
const selectedPlanningRecordOptionLabel = computed(
  () => planningRecordSelectOptions.value.find((option) => option.value === filters.planning_record_id)?.label ?? "",
);
const selectableTeamMembers = computed(() => buildStaffingMemberOptions(teamMembers.value, staffingDraft.team_id));
const selectedMember = computed(() => selectableTeamMembers.value.find((member) => member.id === staffingDraft.member_ref) ?? null);
const canSubmitAssign = computed(() => {
  if (!actionState.value.canAssign || !selectedShiftId.value || !selectedDemandGroupId.value) {
    return false;
  }
  if (staffingDraft.actor_kind === "team") {
    return Boolean(staffingDraft.team_id);
  }
  return Boolean(staffingDraft.team_id && staffingDraft.member_ref && selectedMember.value);
});
const canSubmitSubstitute = computed(() => canSubmitAssign.value && actionState.value.canSubstitute && !!selectedAssignment.value);

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

const planningRecordLookupCache = new Map<string, PlanningRecordListItem[]>();
let planningRecordLookupRequestId = 0;
let planningRecordLookupTimer: ReturnType<typeof setTimeout> | null = null;

function staffingFilters() {
  return {
    shift_id: selectedShiftId.value,
    planning_record_id: filters.planning_record_id,
  };
}

function resetStaffingDraft() {
  staffingDraft.actor_kind = "team";
  staffingDraft.team_id = "";
  staffingDraft.member_ref = "";
  staffingDraft.assignment_source_code = "dispatcher";
  staffingDraft.confirm_now = false;
  staffingDraft.remarks = "";
}

function formatDemandGroup(group: StaffingBoardDemandGroupItem | null) {
  if (!group) {
    return "";
  }
  return [group.function_type_id, group.qualification_type_id].filter(Boolean).join(" · ");
}

function formatMember(member: TeamMemberRead) {
  if (member.employee_id) {
    return `employee:${member.employee_id}`;
  }
  if (member.subcontractor_worker_id) {
    return `worker:${member.subcontractor_worker_id}`;
  }
  return member.id;
}

function buildPlanningRecordLookupCacheKey(search = "") {
  return JSON.stringify({
    tenantId: tenantScopeId.value,
    planningModeCode: filters.planning_mode_code || "",
    planningFrom: normalizePlanningStaffingLookupDate(filters.date_from) || "",
    planningTo: normalizePlanningStaffingLookupDate(filters.date_to) || "",
    search: search.trim(),
  });
}

async function loadPlanningRecordOptions(search = "") {
  if (!tenantScopeId.value || !accessToken.value) {
    planningRecordOptions.value = [];
    planningRecordLookupError.value = "";
    return;
  }
  const cacheKey = buildPlanningRecordLookupCacheKey(search);
  const cached = planningRecordLookupCache.get(cacheKey);
  if (cached) {
    planningRecordOptions.value = cached;
    planningRecordLookupError.value = "";
    return;
  }
  planningRecordLookupLoading.value = true;
  planningRecordLookupError.value = "";
  const requestId = ++planningRecordLookupRequestId;
  try {
    const rows = await listPlanningRecords(
      tenantScopeId.value,
      accessToken.value,
      buildPlanningStaffingPlanningRecordLookupFilters(filters, search),
    );
    if (requestId !== planningRecordLookupRequestId) {
      return;
    }
    planningRecordLookupCache.set(cacheKey, rows);
    planningRecordOptions.value = rows;
  } catch {
    if (requestId !== planningRecordLookupRequestId) {
      return;
    }
    planningRecordOptions.value = [];
    planningRecordLookupError.value = tp("filtersPlanningRecordLookupError");
  } finally {
    if (requestId === planningRecordLookupRequestId) {
      planningRecordLookupLoading.value = false;
    }
  }
}

function schedulePlanningRecordLookup(search = planningRecordLookupSearch.value) {
  if (planningRecordLookupTimer) {
    clearTimeout(planningRecordLookupTimer);
  }
  planningRecordLookupTimer = setTimeout(() => {
    void loadPlanningRecordOptions(search);
  }, 250);
}

function handlePlanningRecordSearch(value: string) {
  planningRecordLookupSearch.value = value;
  schedulePlanningRecordLookup(value);
}

function handlePlanningRecordSelection(value: string | undefined) {
  filters.planning_record_id = typeof value === "string" ? value : "";
}

function clearPlanningRecordSelection() {
  filters.planning_record_id = "";
}

async function handleAuthExpired() {
  authStore.clearSession();
  try {
    primaryAuthStore.clearSessionState();
    await primaryAuthStore.redirectToLogin("/admin/planning-staffing");
  } catch {
    // Keep inline feedback visible if redirect bootstrap is unavailable.
  }
}

function handleApiError(error: unknown) {
  if (error instanceof PlanningStaffingApiError) {
    const key = mapPlanningStaffingApiMessage(error.messageKey);
    if (key === "authRequired") {
      void handleAuthExpired();
    }
    setFeedback("error", tp("title"), tp(key as keyof typeof planningStaffingMessages.de));
    return;
  }
  setFeedback("error", tp("title"), tp("error"));
}

async function ensureStaffingSessionReady() {
  authStore.syncFromPrimarySession();
  if (!authStore.effectiveAccessToken && !authStore.refreshToken) {
    return false;
  }
  try {
    await authStore.ensureSessionReady();
    return Boolean(authStore.effectiveAccessToken);
  } catch {
    await handleAuthExpired();
    return false;
  }
}

function dispatchAudienceCodes() {
  const codes: string[] = [];
  if (dispatchAudienceEmployees.value) {
    codes.push("assigned_employees");
  }
  if (dispatchAudienceSubcontractors.value) {
    codes.push("subcontractor_release");
  }
  return codes;
}

async function refreshSupportingData() {
  if (!tenantScopeId.value || !accessToken.value || !selectedShiftId.value) {
    shiftTeams.value = [];
    teamMembers.value = [];
    subcontractorReleases.value = [];
    return;
  }
  const [teams, members, releases] = await Promise.all([
    listTeams(tenantScopeId.value, accessToken.value, staffingFilters()),
    listTeamMembers(tenantScopeId.value, accessToken.value, staffingFilters()),
    listSubcontractorReleases(tenantScopeId.value, accessToken.value, staffingFilters()),
  ]);
  shiftTeams.value = teams;
  teamMembers.value = members;
  subcontractorReleases.value = releases;
  if (!shiftTeams.value.some((team) => team.id === staffingDraft.team_id)) {
    staffingDraft.team_id = "";
    staffingDraft.member_ref = "";
  }
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
      selectedDemandGroupId.value = "";
      selectedAssignmentId.value = "";
      shiftValidations.value = null;
      assignmentValidations.value = null;
      assignmentOverrides.value = [];
      shiftOutputs.value = [];
      dispatchPreview.value = null;
      shiftTeams.value = [];
      teamMembers.value = [];
      subcontractorReleases.value = [];
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
  const [validations, outputs] = await Promise.all([
    getShiftReleaseValidations(tenantScopeId.value, accessToken.value, selectedShiftId.value),
    listShiftOutputs(tenantScopeId.value, accessToken.value, selectedShiftId.value),
    refreshSupportingData(),
  ]);
  shiftValidations.value = validations;
  shiftOutputs.value = outputs;
  selectedDemandGroupId.value = resolveSelectedDemandGroupId(selectedBoardShift.value, selectedDemandGroupId.value);
  const boardShift = selectedBoardShift.value;
  if (!boardShift?.assignments?.length) {
    selectedAssignmentId.value = "";
    assignmentValidations.value = null;
    assignmentOverrides.value = [];
    return;
  }
  if (!boardShift.assignments.some((row) => row.id === selectedAssignmentId.value)) {
    selectedAssignmentId.value = boardShift.assignments[0]!.id;
  }
  await loadSelectedAssignmentDetails();
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

function buildAssignPayload() {
  return {
    tenant_id: tenantScopeId.value,
    shift_id: selectedShiftId.value,
    demand_group_id: selectedDemandGroupId.value,
    team_id: staffingDraft.team_id || null,
    employee_id:
      staffingDraft.actor_kind === "employee"
        ? (selectedMember.value?.employee_id ?? null)
        : null,
    subcontractor_worker_id:
      staffingDraft.actor_kind === "subcontractor_worker"
        ? (selectedMember.value?.subcontractor_worker_id ?? null)
        : null,
    assignment_source_code: staffingDraft.assignment_source_code,
    confirmed_at: staffingDraft.confirm_now ? new Date().toISOString() : null,
    remarks: staffingDraft.remarks.trim() || null,
  };
}

async function submitAssign() {
  if (!tenantScopeId.value || !accessToken.value || !canSubmitAssign.value) {
    return;
  }
  clearFeedback();
  try {
    const result = await assignStaffing(tenantScopeId.value, accessToken.value, buildAssignPayload());
    if (result.outcome_code === "blocked") {
      setFeedback("error", tp("staffingActionsTitle"), tp("assignmentBlocked"));
      await loadSelectedShiftDetails();
      return;
    }
    selectedAssignmentId.value = result.assignment_id ?? "";
    resetStaffingDraft();
    await refreshAll();
  } catch (error) {
    handleApiError(error);
  }
}

async function submitUnassign() {
  if (!tenantScopeId.value || !accessToken.value || !selectedAssignment.value) {
    return;
  }
  clearFeedback();
  try {
    await unassignStaffing(tenantScopeId.value, accessToken.value, {
      tenant_id: tenantScopeId.value,
      assignment_id: selectedAssignment.value.id,
      version_no: selectedAssignment.value.version_no,
      remarks: staffingDraft.remarks.trim() || null,
    });
    selectedAssignmentId.value = "";
    await refreshAll();
  } catch (error) {
    handleApiError(error);
  }
}

async function submitSubstitute() {
  if (!tenantScopeId.value || !accessToken.value || !selectedAssignment.value || !canSubmitSubstitute.value) {
    return;
  }
  clearFeedback();
  try {
    const result = await substituteStaffing(tenantScopeId.value, accessToken.value, {
      tenant_id: tenantScopeId.value,
      assignment_id: selectedAssignment.value.id,
      version_no: selectedAssignment.value.version_no,
      replacement_team_id: staffingDraft.team_id || null,
      replacement_employee_id:
        staffingDraft.actor_kind === "employee"
          ? (selectedMember.value?.employee_id ?? null)
          : null,
      replacement_subcontractor_worker_id:
        staffingDraft.actor_kind === "subcontractor_worker"
          ? (selectedMember.value?.subcontractor_worker_id ?? null)
          : null,
      assignment_source_code: staffingDraft.assignment_source_code,
      remarks: staffingDraft.remarks.trim() || null,
    });
    if (result.outcome_code === "blocked") {
      setFeedback("error", tp("staffingActionsTitle"), tp("assignmentBlocked"));
      await loadSelectedShiftDetails();
      return;
    }
    selectedAssignmentId.value = result.assignment_id ?? "";
    resetStaffingDraft();
    await refreshAll();
  } catch (error) {
    handleApiError(error);
  }
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

async function recoverSessionAndRefresh() {
  if (document.visibilityState === "hidden") {
    return;
  }
  const ready = await ensureStaffingSessionReady();
  if (!ready || !actionState.value.canReadCoverage) {
    return;
  }
  await loadPlanningRecordOptions();
  await refreshAll();
}

function handleVisibilityChange() {
  if (document.visibilityState === "visible") {
    void recoverSessionAndRefresh();
  }
}

function handleWindowFocus() {
  void recoverSessionAndRefresh();
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

watch(
  selectedBoardShift,
  (shift) => {
    selectedDemandGroupId.value = resolveSelectedDemandGroupId(shift, selectedDemandGroupId.value);
  },
  { immediate: true },
);

watch(
  () => staffingDraft.team_id,
  () => {
    if (!selectableTeamMembers.value.some((member) => member.id === staffingDraft.member_ref)) {
      staffingDraft.member_ref = "";
    }
  },
);

watch(
  () => [authStore.effectiveRole, authStore.effectiveTenantScopeId, authStore.effectiveAccessToken, authStore.sessionUser?.id ?? ""],
  ([nextRole, nextTenantScopeId, nextAccessToken], [prevRole, prevTenantScopeId, prevAccessToken]) => {
    if (!nextRole || !nextTenantScopeId || !nextAccessToken) {
      return;
    }
    if (
      nextRole === prevRole
      && nextTenantScopeId === prevTenantScopeId
      && nextAccessToken === prevAccessToken
    ) {
      return;
    }
    void refreshAll();
  },
);

watch(
  () => [tenantScopeId.value, accessToken.value, filters.planning_mode_code, filters.date_from, filters.date_to],
  ([nextTenantScopeId, nextAccessToken]) => {
    if (!nextTenantScopeId || !nextAccessToken) {
      planningRecordOptions.value = [];
      planningRecordLookupError.value = "";
      return;
    }
    schedulePlanningRecordLookup();
  },
);

onMounted(async () => {
  authStore.syncFromPrimarySession();
  const sessionReady = await ensureStaffingSessionReady();
  if (!sessionReady || !tenantScopeId.value || !accessToken.value || !actionState.value.canReadCoverage) {
    return;
  }
  document.addEventListener("visibilitychange", handleVisibilityChange);
  window.addEventListener("focus", handleWindowFocus);
  await refreshAll();
});

onBeforeUnmount(() => {
  if (planningRecordLookupTimer) {
    clearTimeout(planningRecordLookupTimer);
  }
  document.removeEventListener("visibilitychange", handleVisibilityChange);
  window.removeEventListener("focus", handleWindowFocus);
});
</script>

<style scoped>
.planning-staffing-page,
.planning-staffing-grid,
.planning-staffing-filter-grid,
.planning-staffing-summary,
.planning-staffing-detail,
.planning-staffing-metrics,
.planning-staffing-issues,
.planning-staffing-demand-groups,
.planning-staffing-support-grid {
  display: grid;
  gap: 1rem;
}

.planning-staffing-grid {
  align-items: start;
  grid-template-columns: minmax(300px, 0.95fr) minmax(320px, 1fr) minmax(420px, 1.35fr);
}

.planning-staffing-meta,
.planning-staffing-metrics,
.planning-staffing-panel__header,
.planning-staffing-summary,
.planning-staffing-support-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  justify-content: space-between;
  align-items: center;
}

.planning-staffing-meta__pill,
.planning-staffing-state,
.planning-staffing-summary__card,
.planning-staffing-issue,
.planning-staffing-support-card,
.planning-staffing-demand-group {
  border: 1px solid rgba(40, 170, 170, 0.18);
  border-radius: 16px;
  padding: 0.75rem 0.9rem;
  background: rgba(40, 170, 170, 0.06);
}

.planning-staffing-row,
.planning-staffing-subpanel,
.planning-staffing-feedback {
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 18px;
  padding: 1rem;
  background: #fff;
}

.planning-staffing-panel {
  align-content: start;
  gap: 1.25rem;
  padding: 1.25rem;
  box-shadow: 0 20px 44px rgba(15, 23, 42, 0.05);
}

.planning-staffing-panel__header {
  align-items: flex-start;
  gap: 1rem;
}

.planning-staffing-panel__lead {
  color: rgba(15, 23, 42, 0.72);
  font-size: 0.95rem;
  line-height: 1.45;
  margin: 0.35rem 0 0;
}

.planning-staffing-panel__header--filters {
  display: grid;
  gap: 1rem;
  grid-template-columns: minmax(0, 1fr) auto;
}

.planning-staffing-panel__header--filters > div,
.planning-staffing-panel__actions,
.planning-staffing-filter-grid > *,
.planning-staffing-filter-grid .field-stack,
.planning-staffing-select {
  min-width: 0;
}

.planning-staffing-panel__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  justify-content: flex-end;
}

.planning-staffing-filter-grid {
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}

.planning-staffing-filter-grid :deep(.field-stack),
.planning-staffing-filter-grid .field-stack,
.planning-staffing-subpanel .field-stack {
  display: grid;
  gap: 0.45rem;
}

.planning-staffing-filter-grid :deep(.field-stack > span),
.planning-staffing-filter-grid .field-stack > span,
.planning-staffing-subpanel .field-stack > span {
  color: rgba(15, 23, 42, 0.72);
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  text-transform: uppercase;
}

.planning-staffing-filter-grid input,
.planning-staffing-filter-grid select,
.planning-staffing-filter-grid textarea,
.planning-staffing-subpanel input,
.planning-staffing-subpanel select,
.planning-staffing-subpanel textarea {
  appearance: none;
  background: rgba(248, 250, 252, 0.96);
  border: 1px solid rgba(148, 163, 184, 0.35);
  border-radius: 14px;
  color: rgb(15, 23, 42);
  font: inherit;
  min-height: 2.85rem;
  padding: 0.75rem 0.9rem;
  transition: border-color 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;
  width: 100%;
}

.planning-staffing-filter-grid :deep(.ant-select),
.planning-staffing-filter-grid :deep(.ant-select-selector),
.planning-staffing-filter-grid :deep(.ant-select-selection-search),
.planning-staffing-filter-grid :deep(.ant-select-selection-search-input) {
  min-width: 0;
  width: 100%;
}

.planning-staffing-filter-grid :deep(.ant-select-selector) {
  align-items: center;
  min-height: 2.85rem;
}

.planning-staffing-filter-grid textarea,
.planning-staffing-subpanel textarea {
  min-height: 6rem;
  resize: vertical;
}

.planning-staffing-filter-grid input[type="checkbox"],
.planning-staffing-subpanel input[type="checkbox"] {
  accent-color: rgb(40, 170, 170);
  min-height: auto;
  min-width: 1.1rem;
  padding: 0;
  width: 1.1rem;
}

.planning-staffing-filter-grid input:focus,
.planning-staffing-filter-grid select:focus,
.planning-staffing-filter-grid textarea:focus,
.planning-staffing-subpanel input:focus,
.planning-staffing-subpanel select:focus,
.planning-staffing-subpanel textarea:focus {
  background: #fff;
  border-color: rgba(40, 170, 170, 0.9);
  box-shadow: 0 0 0 4px rgba(40, 170, 170, 0.14);
  outline: none;
}

.planning-staffing-row,
.planning-staffing-demand-group {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  text-align: left;
  transition: border-color 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease;
}

.planning-staffing-row.selected,
.planning-staffing-demand-group.selected {
  border-color: rgb(40, 170, 170);
  box-shadow: 0 0 0 1px rgba(40, 170, 170, 0.2);
}

.planning-staffing-row:hover,
.planning-staffing-demand-group:hover {
  border-color: rgba(40, 170, 170, 0.45);
  transform: translateY(-1px);
}

.planning-staffing-demand-group,
.planning-staffing-support-card,
.planning-staffing-issue {
  display: grid;
  gap: 0.35rem;
}

.planning-staffing-empty {
  display: grid;
  gap: 0.75rem;
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
.planning-staffing-summary__card[data-tone="bad"],
.planning-staffing-feedback[data-tone="error"] {
  background: rgba(220, 38, 38, 0.12);
  border-color: rgba(220, 38, 38, 0.24);
}

.planning-staffing-issue[data-tone="neutral"],
.planning-staffing-feedback[data-tone="good"] {
  background: rgba(15, 23, 42, 0.04);
  border-color: rgba(15, 23, 42, 0.12);
}

.field-stack--wide {
  grid-column: 1 / -1;
}

@media (max-width: 1180px) {
  .planning-staffing-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .planning-staffing-panel__header--filters {
    grid-template-columns: 1fr;
  }

  .planning-staffing-filter-grid {
    grid-template-columns: 1fr;
  }

  .planning-staffing-panel__actions {
    justify-content: flex-start;
  }
}
</style>
