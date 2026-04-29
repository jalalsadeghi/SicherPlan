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

    <SicherPlanLoadingOverlay
      v-else
      :aria-label="planningStaffingWorkspaceLoadingText"
      :busy="planningStaffingWorkspaceBusy"
      :text="planningStaffingWorkspaceLoadingText"
      busy-testid="planning-staffing-workspace-loading-overlay"
    >
      <div class="planning-staffing-workspace" data-testid="planning-staffing-workspace">
      <section class="module-card planning-staffing-panel planning-staffing-filter-panel" data-testid="planning-staffing-filter-panel">
        <div class="planning-staffing-panel__header planning-staffing-panel__header--filters">
          <div>
            <p class="eyebrow">{{ tp("filtersTitle") }}</p>
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
            <span class="planning-staffing-field-label">
              <span>{{ tp("filtersPlanningRecord") }}</span>
              <small
                v-if="planningRecordFieldStatusShort"
                class="planning-staffing-field-status"
                :title="planningRecordFieldStatusTitle"
                :aria-label="planningRecordFieldStatusTitle"
                data-testid="planning-staffing-planning-record-status"
              >
                {{ planningRecordFieldStatusShort }}
              </small>
            </span>
            <Select
              :value="filters.planning_record_id || undefined"
              show-search
              allow-clear
              class="planning-staffing-select"
              popup-class-name="planning-staffing-select-dropdown"
              :loading="planningRecordLookupLoading"
              :filter-option="false"
              :options="planningRecordSelectOptions"
              :not-found-content="planningRecordDropdownEmptyContent"
              :placeholder="tp('filtersPlanningRecordPlaceholder')"
              data-testid="planning-staffing-planning-record-select"
              @search="handlePlanningRecordSearch"
              @change="handlePlanningRecordSelection"
              @clear="clearPlanningRecordSelection"
            />
          </label>
          <label class="field-stack">
            <span>{{ tp("filtersPlanningMode") }}</span>
            <select v-model="filters.planning_mode_code">
              <option value="">{{ tp("filtersPlanningModePlaceholder") }}</option>
              <option value="event">event</option>
              <option value="site">site</option>
              <option value="trade_fair">trade_fair</option>
              <option value="patrol">patrol</option>
            </select>
          </label>
          <label class="field-stack">
            <span>{{ tp("filtersWorkforceScope") }}</span>
            <select v-model="filters.workforce_scope_code">
              <option value="">{{ tp("filtersWorkforceScopePlaceholder") }}</option>
              <option value="internal">internal</option>
              <option value="subcontractor">subcontractor</option>
              <option value="mixed">mixed</option>
            </select>
          </label>
          <label class="field-stack">
            <span>{{ tp("filtersConfirmation") }}</span>
            <select v-model="filters.confirmation_state">
              <option value="">{{ tp("filtersConfirmationPlaceholder") }}</option>
              <option value="confirmed_only">confirmed_only</option>
            </select>
          </label>
          <div class="planning-staffing-filter-actions field-stack--wide">
            <button
              class="cta-button cta-secondary"
              type="button"
              data-testid="planning-staffing-refresh"
              :disabled="loading"
              @click="refreshAll"
            >
              {{ tp("refresh") }}
            </button>
          </div>
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

      <div class="planning-staffing-main-grid" data-testid="planning-staffing-main-grid">
      <section
        class="module-card planning-staffing-panel planning-staffing-coverage-panel"
        data-testid="planning-staffing-shift-coverage-panel"
      >
        <div class="planning-staffing-panel__header">
          <div>
            <p class="eyebrow">{{ tp("listTitle") }}</p>
          </div>
        </div>
        <div
          v-if="coverageRows.length"
          class="planning-staffing-list planning-staffing-list--scroll"
          data-testid="planning-staffing-shift-coverage-scroll"
        >
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
              <span v-if="rowCoverageState(row) === 'setup_required'" class="field-help">{{ tp("coverageSetupRequiredHint") }}</span>
            </div>
            <span class="planning-staffing-state" :data-tone="coverageTone(rowCoverageState(row))">
              {{ tp(statusKey(rowCoverageState(row))) }}
            </span>
          </button>
        </div>
        <p v-else class="planning-staffing-list-empty">{{ tp("listEmpty") }}</p>
      </section>

      <section class="module-card planning-staffing-panel planning-staffing-detail">
        <div class="planning-staffing-panel__header">
          <div>
            <p class="eyebrow">{{ tp("detailTitle") }}</p>
            <p
              v-if="selectedShiftContextMeta"
              class="planning-staffing-panel__lead planning-staffing-panel__lead--context"
              data-testid="planning-staffing-selected-shift-context"
            >
              {{ selectedShiftContextMeta }}
            </p>
          </div>
          <span v-if="selectedShift" class="planning-staffing-state" :data-tone="coverageTone(rowCoverageState(selectedShift))">
            {{ tp(statusKey(rowCoverageState(selectedShift))) }}
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
          <nav
            class="planning-staffing-tabs"
            role="tablist"
            :aria-label="tp('detailTabsAriaLabel')"
            data-testid="planning-staffing-detail-tabs"
          >
            <button
              v-for="tab in shiftDetailTabs"
              :id="`planning-staffing-tab-${tab.id}`"
              :key="tab.id"
              type="button"
              class="planning-staffing-tab"
              :class="{ active: tab.id === activeShiftDetailTab }"
              role="tab"
              :aria-selected="tab.id === activeShiftDetailTab"
              :aria-controls="`planning-staffing-panel-${tab.id}`"
              @click="activeShiftDetailTab = tab.id"
            >
              {{ tp(tab.labelKey) }}
            </button>
          </nav>

          <section
            v-if="activeShiftDetailTab === 'demand_staffing'"
            class="planning-staffing-tab-panel"
            :id="'planning-staffing-panel-demand_staffing'"
            role="tabpanel"
            :aria-labelledby="'planning-staffing-tab-demand_staffing'"
            data-testid="planning-staffing-tab-panel-demand-staffing"
          >
            <section class="module-card planning-staffing-subpanel">
              <div class="planning-staffing-panel__header">
                <div>
                  <p class="eyebrow">{{ tp("demandGroupsTitle") }}</p>
                  <h4>{{ tp("demandGroupsTitle") }}</h4>
                </div>
                <div v-if="selectedShift && actionState.canWriteStaffing" class="planning-staffing-panel__actions">
                  <button
                    class="cta-button cta-secondary"
                    type="button"
                    data-testid="planning-staffing-demand-group-start-create"
                    :disabled="loading || savingDemandGroup"
                    @click="startCreateDemandGroup"
                  >
                    {{ tp("demandGroupCreateAction") }}
                  </button>
                </div>
              </div>
              <div v-if="selectedBoardShift?.demand_groups?.length" class="planning-staffing-demand-groups" data-testid="planning-staffing-demand-group-list">
                <button
                  v-for="group in selectedBoardShift.demand_groups"
                  :key="group.id"
                  type="button"
                  class="planning-staffing-demand-group"
                  :class="{ selected: group.id === selectedDemandGroupId }"
                  @click="startEditDemandGroup(group.id)"
                >
                  <strong>{{ formatDemandGroup(group) }}</strong>
                  <span>{{ tp("columnMin") }} {{ group.min_qty }} · {{ tp("columnTarget") }} {{ group.target_qty }}</span>
                  <span>{{ tp("columnAssigned") }} {{ group.assigned_count }} · {{ tp("columnConfirmed") }} {{ group.confirmed_count }}</span>
                </button>
              </div>
              <div v-else class="planning-staffing-empty">
                <p class="planning-staffing-list-empty">{{ tp("demandGroupsEmpty") }}</p>
                <p class="field-help">{{ tp("demandGroupsSetupRequired") }}</p>
              </div>
              <p v-if="showDemandGroupSetupLead" class="field-help">{{ tp("demandGroupSetupLead") }}</p>
            </section>

            <section class="module-card planning-staffing-subpanel">
              <div class="planning-staffing-panel__header">
                <div>
                  <p class="eyebrow">{{ tp("staffingActionsTitle") }}</p>
                  <h4>{{ tp("staffingActionsTitle") }}</h4>
                </div>
                <span class="field-help">{{ tp("staffingActionsHint") }}</span>
              </div>
              <p v-if="!hasSelectedDemandGroups" class="planning-staffing-list-empty">{{ tp("staffingActionsDemandGroupRequired") }}</p>
              <fieldset class="planning-staffing-fieldset" :disabled="!hasSelectedDemandGroups">
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
                    <select v-model="staffingDraft.actor_kind" data-testid="planning-staffing-actor-kind-select">
                      <option value="employee">{{ tp("actorKindEmployee") }}</option>
                      <option value="subcontractor_worker">{{ tp("actorKindSubcontractorWorker") }}</option>
                    </select>
                  </label>
                  <label class="field-stack">
                    <span>{{ tp("fieldsTeam") }}</span>
                    <select v-model="staffingDraft.team_id" data-testid="planning-staffing-team-select">
                      <option value="">{{ tp("teamContextPlaceholder") }}</option>
                      <option v-for="team in availableTeams" :key="team.id" :value="team.id">
                        {{ formatTeam(team) }}
                      </option>
                    </select>
                    <p class="field-help">{{ tp("fieldsTeamContextHint") }}</p>
                  </label>
                  <label class="field-stack">
                    <span>{{ staffingDraft.actor_kind === 'employee' ? tp("fieldsEmployee") : tp("fieldsSubcontractorWorker") }}</span>
                    <select v-model="staffingDraft.member_ref" data-testid="planning-staffing-member-select">
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
                  <label class="field-stack field-stack--wide">
                    <span>{{ tp("fieldsRemarks") }}</span>
                    <textarea v-model="staffingDraft.remarks" rows="2" />
                  </label>
                  <div v-if="showImmediateConfirmationControl" class="planning-staffing-confirm-row field-stack--wide">
                    <label class="planning-staffing-checkbox-row">
                      <input v-model="staffingDraft.confirm_now" type="checkbox" data-testid="planning-staffing-confirm-now" />
                      <span>{{ tp("fieldsConfirmAtCreation") }}</span>
                    </label>
                    <p class="field-help">{{ tp("fieldsConfirmAtCreationHint") }}</p>
                  </div>
                </div>
              </fieldset>
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
          </section>

          <section
            v-if="activeShiftDetailTab === 'validations'"
            class="planning-staffing-tab-panel"
            :id="'planning-staffing-panel-validations'"
            role="tabpanel"
            :aria-labelledby="'planning-staffing-tab-validations'"
            data-testid="planning-staffing-tab-panel-validations"
          >
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
          </section>

          <section
            v-if="activeShiftDetailTab === 'assignments'"
            class="planning-staffing-tab-panel"
            :id="'planning-staffing-panel-assignments'"
            role="tabpanel"
            :aria-labelledby="'planning-staffing-tab-assignments'"
            data-testid="planning-staffing-tab-panel-assignments"
          >
            <section class="module-card planning-staffing-subpanel">
              <div class="planning-staffing-panel__header">
                <div>
                  <p class="eyebrow">{{ tp("assignmentsTitle") }}</p>
                  <h4>{{ tp("assignmentsTitle") }}</h4>
                </div>
                <div class="planning-staffing-panel__actions">
                  <button
                    class="cta-button cta-secondary"
                    type="button"
                    data-testid="planning-staffing-start-assignment-create"
                    :disabled="!selectedShiftId || !actionState.canWriteStaffing || assignmentEditorLoading || assignmentEditorSaving"
                    @click="startCreateAssignment"
                  >
                    {{ tp("assignmentCreateAction") }}
                  </button>
                </div>
              </div>
              <div v-if="selectedBoardShift?.assignments?.length" class="planning-staffing-list">
                <button
                  v-for="assignment in selectedBoardShift.assignments"
                  :key="assignment.id"
                  type="button"
                  class="planning-staffing-row planning-staffing-row--assignment"
                  :data-testid="`planning-staffing-assignment-row-${assignment.id}`"
                  :class="{ selected: assignment.id === selectedAssignmentId }"
                  :disabled="assignmentEditorLoading || assignmentEditorSaving"
                  @click="startEditAssignment(assignment.id)"
                >
                  <div class="planning-staffing-assignment-row__body">
                    <strong class="planning-staffing-assignment-row__title">{{ formatAssignmentActor(assignment) }}</strong>
                    <span class="planning-staffing-assignment-row__detail">{{ formatDemandGroupById(assignment.demand_group_id) }}</span>
                    <span class="planning-staffing-assignment-row__meta">{{ assignment.assignment_status_code }} · {{ assignment.assignment_source_code }}</span>
                  </div>
                  <span class="planning-staffing-assignment-row__marker" aria-hidden="true"></span>
                </button>
              </div>
              <div v-else class="planning-staffing-empty">
                <p class="planning-staffing-list-empty">{{ tp("assignmentsEmpty") }}</p>
                <p class="field-help">{{ tp("assignmentsEmptyLead") }}</p>
                <div class="cta-row">
                  <button
                    class="cta-button cta-secondary"
                    type="button"
                    data-testid="planning-staffing-empty-create-assignment"
                    :disabled="!selectedShiftId || !actionState.canWriteStaffing || !selectedBoardShift?.demand_groups?.length"
                    @click="startCreateAssignment"
                  >
                    {{ tp("assignmentCreateAction") }}
                  </button>
                </div>
              </div>
              <div v-if="selectedAssignment" class="planning-staffing-metrics">
                <span>{{ tp("fieldsDemandGroup") }}: {{ formatDemandGroupById(selectedAssignment.demand_group_id) }}</span>
                <span>{{ tp("fieldsVersion") }}: {{ selectedAssignmentDetails?.version_no ?? selectedAssignment.version_no }}</span>
                <span>{{ tp("fieldsTeam") }}: {{ assignmentTeamLabel(selectedAssignment.team_id) }}</span>
              </div>
              <div v-if="selectedAssignment" class="planning-staffing-assignment-validation-summary">
                <span>{{ tp("validationBlock") }}: {{ assignmentValidationSummary.blocking }}</span>
                <span>{{ tp("validationWarn") }}: {{ assignmentValidationSummary.warnings }}</span>
                <span>{{ tp("validationInfo") }}: {{ assignmentValidationSummary.infos }}</span>
                <button
                  class="cta-button cta-secondary"
                  type="button"
                  data-testid="planning-staffing-open-assignment-validations"
                  :disabled="!selectedAssignmentId"
                  @click="activeShiftDetailTab = 'validations'"
                >
                  {{ tp("assignmentOpenValidationsAction") }}
                </button>
              </div>
            </section>
          </section>

          <section
            v-if="activeShiftDetailTab === 'teams_releases'"
            class="planning-staffing-tab-panel"
            :id="'planning-staffing-panel-teams_releases'"
            role="tabpanel"
            :aria-labelledby="'planning-staffing-tab-teams_releases'"
            data-testid="planning-staffing-tab-panel-teams-releases"
          >
            <section class="module-card planning-staffing-subpanel">
              <div class="planning-staffing-panel__header">
                <div>
                  <p class="eyebrow">{{ tp("teamReleaseTitle") }}</p>
                  <h4>{{ tp("teamReleaseTitle") }}</h4>
                </div>
                <div v-if="actionState.canWriteStaffing" class="planning-staffing-panel__actions">
                  <button
                    class="cta-button cta-secondary"
                    type="button"
                    data-testid="planning-staffing-create-planning-team"
                    :disabled="!relevantPlanningRecordId || savingTeam"
                    @click="startCreateTeam('planning')"
                  >
                    {{ tp("createPlanningTeamAction") }}
                  </button>
                  <button
                    class="cta-button cta-secondary"
                    type="button"
                    data-testid="planning-staffing-create-shift-team"
                    :disabled="!selectedShiftId || savingTeam"
                    @click="startCreateTeam('shift')"
                  >
                    {{ tp("createShiftTeamAction") }}
                  </button>
                  <button
                    class="cta-button cta-secondary"
                    type="button"
                    data-testid="planning-staffing-edit-team"
                    :disabled="!selectedTeamId || savingTeam"
                    @click="startEditTeam()"
                  >
                    {{ tp("editTeamAction") }}
                  </button>
                  <button
                    class="cta-button cta-secondary"
                    type="button"
                    data-testid="planning-staffing-create-team-member"
                    :disabled="!selectedTeamId || savingTeamMember"
                    @click="startCreateTeamMember()"
                  >
                    {{ tp("createTeamMemberAction") }}
                  </button>
                </div>
              </div>
              <div class="planning-staffing-support-grid">
                <article class="planning-staffing-support-card">
                  <strong>{{ tp("teamsTitle") }}</strong>
                  <div v-if="availableTeams.length" class="planning-staffing-list">
                    <button
                      v-for="team in availableTeams"
                      :key="team.id"
                      type="button"
                      class="planning-staffing-row"
                      :class="{ selected: team.id === selectedTeamId }"
                      @click="selectedTeamId = team.id"
                    >
                      <div>
                        <strong>{{ team.name }}</strong>
                        <span>{{ tp(team.shift_id ? "teamScopeShift" : "teamScopePlanning") }}</span>
                        <span>{{ tp("teamMemberCount") }}: {{ team.members.length }}</span>
                      </div>
                    </button>
                  </div>
                  <p v-else class="planning-staffing-list-empty">{{ tp("teamsEmpty") }}</p>
                  <div v-if="selectedTeam" class="planning-staffing-issues">
                    <article class="planning-staffing-issue" data-tone="neutral">
                      <strong>{{ selectedTeam.name }}</strong>
                      <span>{{ tp(selectedTeam.shift_id ? "teamScopeShift" : "teamScopePlanning") }}</span>
                      <span v-if="selectedTeam.role_label">{{ selectedTeam.role_label }}</span>
                      <span v-if="selectedTeam.notes">{{ selectedTeam.notes }}</span>
                    </article>
                    <article
                      v-for="member in selectedTeamMembers"
                      :key="member.id"
                      class="planning-staffing-issue"
                      data-tone="neutral"
                    >
                      <div class="planning-staffing-panel__header">
                        <div>
                          <strong>{{ formatMember(member) }}</strong>
                          <span>{{ member.role_label || tp("teamMemberRolePlaceholder") }}</span>
                          <span v-if="member.is_team_lead">{{ tp("teamLeadBadge") }}</span>
                        </div>
                        <button
                          v-if="actionState.canWriteStaffing"
                          class="cta-button cta-secondary"
                          type="button"
                          :data-testid="`planning-staffing-edit-team-member-${member.id}`"
                          @click="startEditTeamMember(member.id)"
                        >
                          {{ tp("editTeamMemberAction") }}
                        </button>
                      </div>
                    </article>
                  </div>
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
          </section>

          <section
            v-if="activeShiftDetailTab === 'outputs_dispatch'"
            class="planning-staffing-tab-panel"
            :id="'planning-staffing-panel-outputs_dispatch'"
            role="tabpanel"
            :aria-labelledby="'planning-staffing-tab-outputs_dispatch'"
            data-testid="planning-staffing-tab-panel-outputs-dispatch"
          >
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
          </section>
        </template>

        <section v-else-if="relevantPlanningRecordId" class="planning-staffing-tab-panel" data-testid="planning-staffing-planning-context-panel">
          <section class="module-card planning-staffing-subpanel">
            <div class="planning-staffing-panel__header">
              <div>
                <p class="eyebrow">{{ tp("teamReleaseTitle") }}</p>
                <h4>{{ tp("planningContextTitle") }}</h4>
                <p class="field-help">{{ tp("planningContextLead") }}</p>
              </div>
              <div v-if="actionState.canWriteStaffing" class="planning-staffing-panel__actions">
                <button
                  class="cta-button cta-secondary"
                  type="button"
                  data-testid="planning-staffing-create-planning-team-context"
                  :disabled="!relevantPlanningRecordId || savingTeam"
                  @click="startCreateTeam('planning')"
                >
                  {{ tp("createPlanningTeamAction") }}
                </button>
              </div>
            </div>
            <article class="planning-staffing-issue" data-tone="neutral">
              <strong>{{ tp("filtersPlanningRecord") }}</strong>
              <span>{{ selectedPlanningRecordOptionLabel || relevantPlanningRecordId }}</span>
            </article>
            <div v-if="availableTeams.length" class="planning-staffing-list">
              <button
                v-for="team in availableTeams"
                :key="team.id"
                type="button"
                class="planning-staffing-row"
                :class="{ selected: team.id === selectedTeamId }"
                @click="selectedTeamId = team.id"
              >
                <div>
                  <strong>{{ team.name }}</strong>
                  <span>{{ tp(team.shift_id ? "teamScopeShift" : "teamScopePlanning") }}</span>
                  <span>{{ tp("teamMemberCount") }}: {{ team.members.length }}</span>
                </div>
              </button>
            </div>
            <p v-else class="planning-staffing-list-empty">{{ tp("teamsEmptyPlanningContext") }}</p>
          </section>
        </section>

        <p v-else class="planning-staffing-list-empty">{{ tp("noSelection") }}</p>
      </section>
      </div>
      </div>
    </SicherPlanLoadingOverlay>

    <Modal
      v-model:open="assignmentDialogOpen"
      :title="tp(assignmentEditorMode === 'edit' ? 'assignmentEditTitle' : 'assignmentCreateTitle')"
      :footer="null"
      @cancel="closeAssignmentDialog"
    >
      <div
        v-if="assignmentEditorLoading"
        class="planning-staffing-loading-state"
        data-testid="planning-staffing-assignment-modal-loading"
      >
        <p class="eyebrow">{{ tp("assignmentEditTitle") }}</p>
        <h4>{{ tp("workspaceLoadingAssignmentOpen") }}</h4>
      </div>
      <form
        v-else-if="selectedShift && actionState.canWriteStaffing"
        class="planning-staffing-demand-group-editor"
        data-testid="planning-staffing-assignment-modal"
        @submit.prevent="submitAssignmentEditor"
      >
        <div class="planning-staffing-metrics">
          <span>{{ tp("assignmentShiftLabel") }}: {{ selectedShift?.order_no || selectedShiftId }}</span>
          <span>{{ tp("fieldsVersion") }}: {{ assignmentDraft.version_no ?? 0 }}</span>
          <span>{{ tp("fieldsTeam") }}: {{ assignmentTeamLabel(assignmentDraft.team_id || null) }}</span>
        </div>
        <div class="planning-staffing-filter-grid">
          <label class="field-stack">
            <span>{{ tp("fieldsDemandGroup") }}</span>
            <select
              v-model="assignmentDraft.demand_group_id"
              data-testid="planning-staffing-assignment-demand-group"
              :disabled="assignmentEditorMode === 'edit'"
            >
              <option value="">{{ tp("demandGroupPlaceholder") }}</option>
              <option v-for="group in selectedBoardShift?.demand_groups ?? []" :key="group.id" :value="group.id">
                {{ formatDemandGroup(group) }}
              </option>
            </select>
            <p v-if="assignmentEditorMode === 'edit'" class="field-help">{{ tp("assignmentDemandGroupLockedHint") }}</p>
          </label>
          <label class="field-stack">
            <span>{{ tp("fieldsActorKind") }}</span>
            <select v-model="assignmentDraft.actor_kind" data-testid="planning-staffing-assignment-actor-kind">
              <option value="employee">{{ tp("actorKindEmployee") }}</option>
              <option value="subcontractor_worker">{{ tp("actorKindSubcontractorWorker") }}</option>
            </select>
          </label>
          <label class="field-stack field-stack--wide">
            <span>{{ tp("assignmentTeamLinkLabel") }}</span>
            <select v-model="assignmentDraft.team_id" data-testid="planning-staffing-assignment-team-select">
              <option value="">{{ tp("assignmentTeamLinkPlaceholder") }}</option>
              <option v-for="team in availableTeams" :key="team.id" :value="team.id">
                {{ formatTeam(team) }}
              </option>
            </select>
            <p class="field-help">{{ tp("assignmentTeamLinkHint") }}</p>
          </label>
          <label class="field-stack">
            <span>{{ assignmentDraft.actor_kind === 'employee' ? tp("fieldsEmployee") : tp("fieldsSubcontractorWorker") }}</span>
            <select v-model="assignmentDraft.member_ref" data-testid="planning-staffing-assignment-member-select">
              <option value="">{{ tp("memberPlaceholder") }}</option>
              <option v-for="option in assignmentActorOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </label>
          <label class="field-stack">
            <span>{{ tp("assignmentStatusLabel") }}</span>
            <select v-model="assignmentDraft.assignment_status_code" data-testid="planning-staffing-assignment-status">
              <option v-for="option in assignmentStatusOptions" :key="option.value" :value="option.value">
                {{ tp(option.labelKey) }}
              </option>
            </select>
          </label>
          <label class="field-stack">
            <span>{{ tp("fieldsAssignmentSource") }}</span>
            <select v-model="assignmentDraft.assignment_source_code" data-testid="planning-staffing-assignment-source">
              <option v-for="option in assignmentSourceOptions" :key="option.value" :value="option.value">
                {{ tp(option.labelKey) }}
              </option>
            </select>
          </label>
          <label class="field-stack">
            <span>{{ tp("assignmentOfferedAtLabel") }}</span>
            <input v-model="assignmentDraft.offered_at" type="datetime-local" data-testid="planning-staffing-assignment-offered-at" />
          </label>
          <label class="field-stack">
            <span>{{ tp("assignmentConfirmedAtLabel") }}</span>
            <input v-model="assignmentDraft.confirmed_at" type="datetime-local" data-testid="planning-staffing-assignment-confirmed-at" />
          </label>
          <label class="field-stack field-stack--wide">
            <span>{{ tp("fieldsRemarks") }}</span>
            <textarea v-model="assignmentDraft.remarks" rows="3" data-testid="planning-staffing-assignment-remarks" />
          </label>
        </div>
        <div v-if="selectedAssignmentId" class="planning-staffing-assignment-validation-summary">
          <span>{{ tp("validationBlock") }}: {{ assignmentValidationSummary.blocking }}</span>
          <span>{{ tp("validationWarn") }}: {{ assignmentValidationSummary.warnings }}</span>
          <span>{{ tp("validationInfo") }}: {{ assignmentValidationSummary.infos }}</span>
          <button
            class="cta-button cta-secondary"
            type="button"
            data-testid="planning-staffing-open-assignment-validations"
            :disabled="!selectedAssignmentId"
            @click="activeShiftDetailTab = 'validations'"
          >
            {{ tp("assignmentOpenValidationsAction") }}
          </button>
        </div>
        <div class="cta-row">
          <button
            class="cta-button"
            type="submit"
            data-testid="planning-staffing-assignment-modal-save"
            :disabled="!canSubmitAssignmentEditor || assignmentEditorSaving"
          >
            {{ tp(assignmentEditorMode === 'edit' ? 'assignmentUpdateAction' : 'assignmentCreateAction') }}
          </button>
          <button
            class="cta-button cta-secondary"
            type="button"
            data-testid="planning-staffing-assignment-modal-reset"
            :disabled="assignmentEditorSaving"
            @click="resetAssignmentEditor"
          >
            {{ tp("assignmentResetAction") }}
          </button>
          <button
            v-if="selectedAssignmentId"
            class="cta-button cta-secondary"
            type="button"
            data-testid="planning-staffing-assignment-modal-remove"
            :disabled="!actionState.canUnassign || assignmentEditorSaving"
            @click="submitUnassign"
          >
            {{ tp("unassignAction") }}
          </button>
          <button
            class="cta-button cta-secondary"
            type="button"
            data-testid="planning-staffing-assignment-modal-cancel"
            :disabled="assignmentEditorSaving"
            @click="closeAssignmentDialog"
          >
            {{ tp("assignmentCancelAction") }}
          </button>
        </div>
      </form>
    </Modal>

    <Modal
      v-model:open="demandGroupDialogOpen"
      :title="editingDemandGroup ? tp('demandGroupEditTitle') : tp('demandGroupCreateTitle')"
      :footer="null"
      @cancel="closeDemandGroupDialog"
    >
      <form
        v-if="selectedShift && actionState.canWriteStaffing"
        class="planning-staffing-demand-group-editor"
        data-testid="planning-staffing-demand-group-editor"
        @submit.prevent="submitDemandGroup"
      >
        <div class="planning-staffing-filter-grid">
          <label class="field-stack">
            <span>{{ tp("demandGroupFunctionType") }}</span>
            <select v-model="demandGroupDraft.function_type_id" data-testid="planning-staffing-demand-group-function-type">
              <option value="">{{ tp("demandGroupFunctionTypePlaceholder") }}</option>
              <option v-for="option in functionTypeOptions" :key="option.id" :value="option.id">
                {{ option.label || option.code }}
              </option>
            </select>
          </label>
          <label class="field-stack">
            <span>{{ tp("demandGroupQualificationType") }}</span>
            <select v-model="demandGroupDraft.qualification_type_id" data-testid="planning-staffing-demand-group-qualification-type">
              <option value="">{{ tp("demandGroupQualificationTypePlaceholder") }}</option>
              <option v-for="option in qualificationTypeOptions" :key="option.id" :value="option.id">
                {{ option.label || option.code }}
              </option>
            </select>
          </label>
          <label class="field-stack">
            <span>{{ tp("demandGroupMinQty") }}</span>
            <input v-model.number="demandGroupDraft.min_qty" type="number" min="0" step="1" />
          </label>
          <label class="field-stack">
            <span>{{ tp("demandGroupTargetQty") }}</span>
            <input v-model.number="demandGroupDraft.target_qty" type="number" min="0" step="1" />
          </label>
          <label class="field-stack">
            <span>{{ tp("demandGroupSortOrder") }}</span>
            <input
              v-model.number="demandGroupDraft.sort_order"
              type="number"
              min="0"
              step="1"
              data-testid="planning-staffing-demand-group-sort-order"
            />
            <p class="field-help">{{ tp("demandGroupSortOrderHint") }}</p>
          </label>
          <div class="planning-staffing-confirm-row field-stack--wide">
            <label class="planning-staffing-checkbox-row">
              <input v-model="demandGroupDraft.mandatory_flag" type="checkbox" />
              <span>{{ tp("demandGroupMandatoryFlag") }}</span>
            </label>
            <p class="field-help">{{ tp("demandGroupMandatoryHint") }}</p>
          </div>
          <label class="field-stack field-stack--wide">
            <span>{{ tp("demandGroupRemark") }}</span>
            <textarea v-model="demandGroupDraft.remark" rows="2" />
          </label>
        </div>
        <div class="cta-row">
          <button
            class="cta-button"
            type="submit"
            data-testid="planning-staffing-demand-group-save"
            :disabled="!canSubmitDemandGroup || savingDemandGroup"
          >
            {{ editingDemandGroup ? tp("demandGroupUpdateAction") : tp("demandGroupSaveAction") }}
          </button>
          <button
            class="cta-button cta-secondary"
            type="button"
            :disabled="savingDemandGroup"
            @click="resetDemandGroupDraft"
          >
            {{ tp("demandGroupResetAction") }}
          </button>
          <button
            class="cta-button cta-secondary"
            type="button"
            data-testid="planning-staffing-demand-group-modal-cancel"
            :disabled="savingDemandGroup"
            @click="closeDemandGroupDialog"
          >
            {{ tp("demandGroupCancelAction") }}
          </button>
        </div>
      </form>
    </Modal>

    <Modal
      v-model:open="teamDialogOpen"
      :title="editingTeam ? tp('teamEditTitle') : tp('teamCreateTitle')"
      :footer="null"
      @cancel="closeTeamDialog"
    >
      <form
        v-if="actionState.canWriteStaffing"
        class="planning-staffing-demand-group-editor"
        data-testid="planning-staffing-team-editor"
        @submit.prevent="submitTeam"
      >
        <div class="planning-staffing-filter-grid">
          <label v-if="teamDraft.scope_kind === 'planning'" class="field-stack field-stack--wide">
            <span>{{ tp("filtersPlanningRecord") }}</span>
            <input :value="planningRecordDisplayName || tp('scopeUnavailable')" type="text" disabled data-testid="planning-staffing-team-planning-record" />
            <p class="field-help">
              {{ tp("teamPlanningRecordHint") }}
              <span v-if="relevantPlanningRecordId"> {{ tp("teamPlanningRecordIdHint") }} {{ relevantPlanningRecordId }}</span>
            </p>
          </label>
          <label class="field-stack">
            <span>{{ tp("teamNameLabel") }}</span>
            <input v-model="teamDraft.name" type="text" data-testid="planning-staffing-team-name" />
          </label>
          <label class="field-stack">
            <span>{{ tp("teamScopeLabel") }}</span>
            <select v-model="teamDraft.scope_kind" data-testid="planning-staffing-team-scope">
              <option value="planning">{{ tp("teamScopePlanning") }}</option>
              <option value="shift" :disabled="!selectedShiftId">{{ tp("teamScopeShift") }}</option>
            </select>
          </label>
          <label class="field-stack">
            <span>{{ tp("teamRoleLabel") }}</span>
            <input v-model="teamDraft.role_label" type="text" />
          </label>
          <label class="field-stack field-stack--wide">
            <span>{{ tp("teamNotesLabel") }}</span>
            <textarea v-model="teamDraft.notes" rows="2" />
          </label>
          <label v-if="!editingTeam" class="field-stack">
            <span>{{ tp("teamLeadActorLabel") }}</span>
            <select v-model="teamDraft.lead_actor_kind" data-testid="planning-staffing-team-lead-actor-kind">
              <option value="employee">{{ tp("actorKindEmployee") }}</option>
              <option value="subcontractor_worker">{{ tp("actorKindSubcontractorWorker") }}</option>
            </select>
          </label>
          <label v-if="!editingTeam" class="field-stack">
            <span>{{ tp("teamLeadMemberLabel") }}</span>
            <select v-model="teamDraft.lead_member_ref" data-testid="planning-staffing-team-lead-member">
              <option value="">{{ tp("teamLeadMemberPlaceholder") }}</option>
              <option v-for="option in teamLeadOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </label>
        </div>
        <div class="cta-row">
          <button
            class="cta-button"
            type="submit"
            data-testid="planning-staffing-team-save"
            :disabled="!canSubmitTeam || savingTeam"
          >
            {{ editingTeam ? tp("teamUpdateAction") : tp("teamSaveAction") }}
          </button>
          <button class="cta-button cta-secondary" type="button" :disabled="savingTeam" @click="closeTeamDialog">
            {{ tp("demandGroupCancelAction") }}
          </button>
        </div>
      </form>
    </Modal>

    <Modal
      v-model:open="teamMemberDialogOpen"
      :title="editingTeamMember ? tp('teamMemberEditTitle') : tp('teamMemberCreateTitle')"
      :footer="null"
      @cancel="closeTeamMemberDialog"
    >
      <form
        v-if="actionState.canWriteStaffing"
        class="planning-staffing-demand-group-editor"
        data-testid="planning-staffing-team-member-editor"
        @submit.prevent="submitTeamMember"
      >
        <div class="planning-staffing-filter-grid">
          <label class="field-stack">
            <span>{{ tp("fieldsTeam") }}</span>
            <select v-model="teamMemberDraft.team_id" data-testid="planning-staffing-team-member-team">
              <option value="">{{ tp("teamPlaceholder") }}</option>
              <option v-for="team in availableTeams" :key="team.id" :value="team.id">
                {{ formatTeam(team) }}
              </option>
            </select>
          </label>
          <label class="field-stack">
            <span>{{ tp("fieldsActorKind") }}</span>
            <select v-model="teamMemberDraft.actor_kind" data-testid="planning-staffing-team-member-actor-kind">
              <option value="employee">{{ tp("actorKindEmployee") }}</option>
              <option value="subcontractor_worker">{{ tp("actorKindSubcontractorWorker") }}</option>
            </select>
          </label>
          <label class="field-stack">
            <span>{{ tp("teamMemberActorLabel") }}</span>
            <select v-model="teamMemberDraft.member_ref" data-testid="planning-staffing-team-member-member">
              <option value="">{{ tp("teamMemberActorPlaceholder") }}</option>
              <option v-for="option in teamMemberActorOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </label>
          <label class="field-stack">
            <span>{{ tp("teamMemberRoleLabel") }}</span>
            <input v-model="teamMemberDraft.role_label" type="text" data-testid="planning-staffing-team-member-role-label" />
          </label>
          <label class="field-stack">
            <span>{{ tp("teamMemberValidFromLabel") }}</span>
            <input v-model="teamMemberDraft.valid_from" type="datetime-local" />
          </label>
          <label class="field-stack">
            <span>{{ tp("teamMemberValidToLabel") }}</span>
            <input v-model="teamMemberDraft.valid_to" type="datetime-local" />
          </label>
          <div class="planning-staffing-confirm-row field-stack--wide">
            <label class="planning-staffing-checkbox-row">
              <input v-model="teamMemberDraft.is_team_lead" type="checkbox" />
              <span>{{ tp("teamMemberLeadLabel") }}</span>
            </label>
          </div>
          <label class="field-stack field-stack--wide">
            <span>{{ tp("teamMemberNotesLabel") }}</span>
            <textarea v-model="teamMemberDraft.notes" rows="2" />
          </label>
        </div>
        <div class="cta-row">
          <button
            class="cta-button"
            type="submit"
            data-testid="planning-staffing-team-member-save"
            :disabled="!canSubmitTeamMember || savingTeamMember"
          >
            {{ editingTeamMember ? tp("teamMemberUpdateAction") : tp("teamMemberSaveAction") }}
          </button>
          <button class="cta-button cta-secondary" type="button" :disabled="savingTeamMember" @click="closeTeamMemberDialog">
            {{ tp("demandGroupCancelAction") }}
          </button>
        </div>
      </form>
    </Modal>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { Modal, Select } from "ant-design-vue";

import { useAuthStore as usePrimaryAuthStore } from "#/store";
import {
  listEmployees,
  listFunctionTypes,
  listQualificationTypes,
  type EmployeeListItem,
  type FunctionTypeRead,
  type QualificationTypeRead,
} from "@/api/employeeAdmin";
import {
  getPlanningRecord,
  listPlanningRecords,
  type PlanningRecordListItem,
  type PlanningRecordRead,
} from "@/api/planningOrders";
import { getShift } from "@/api/planningShifts";
import {
  assignStaffing,
  createAssignment,
  createTeam,
  createTeamMember,
  createDemandGroup,
  createAssignmentValidationOverride,
  getAssignment,
  getTeam,
  listDemandGroups,
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
  updateAssignment,
  updateDemandGroup,
  updateTeam,
  updateTeamMember,
  type AssignmentCreate,
  type AssignmentRead,
  PlanningStaffingApiError,
  type AssignmentUpdate,
  type AssignmentValidationRead,
  type CoverageFilterParams,
  type CoverageShiftItem,
  type DemandGroupRead,
  type PlanningDispatchPreviewRead,
  type PlanningOutputDocumentRead,
  type ShiftReleaseValidationRead,
  type StaffingBoardAssignmentItem,
  type StaffingBoardDemandGroupItem,
  type StaffingBoardShiftItem,
  type SubcontractorReleaseRead,
  type TeamCreate,
  type TeamMemberCreate,
  type TeamMemberRead,
  type TeamRead,
} from "@/api/planningStaffing";
import SicherPlanLoadingOverlay from "@/components/SicherPlanLoadingOverlay.vue";
import { planningStaffingMessages } from "@/i18n/planningStaffing.messages";
import { useIsRouteCachePaneActive } from "@vben/layouts";
import {
  listSubcontractorWorkers,
  type SubcontractorWorkerListItem,
} from "@/api/subcontractors";
import { useAuthStore } from "@/stores/auth";
import { useLocaleStore } from "@/stores/locale";
import {
  actorLabel,
  buildPlanningStaffingPlanningRecordLookupFilters,
  buildStaffingMemberOptions,
  coverageTone,
  derivePlanningStaffingActionState,
  formatPlanningStaffingDemandGroupLabel,
  formatPlanningStaffingPlanningRecordOption,
  mapPlanningStaffingApiMessage,
  normalizePlanningStaffingLookupDate,
  resolvePlanningStaffingCoverageState,
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
const isRouteCachePaneActive = useIsRouteCachePaneActive();
const localeStore = useLocaleStore();
const route = useRoute();

const currentLocale = computed<"de" | "en">(() => (localeStore.locale === "en" ? "en" : "de"));
const role = computed(() => authStore.effectiveRole || "tenant_admin");
const tenantScopeId = computed(() => authStore.effectiveTenantScopeId || authStore.tenantScopeId || "");
const accessToken = computed(() => authStore.effectiveAccessToken || authStore.accessToken || "");

const coverageRows = ref<CoverageShiftItem[]>([]);
const boardRows = ref<StaffingBoardShiftItem[]>([]);
const demandGroupRows = ref<DemandGroupRead[]>([]);
const functionTypeOptions = ref<FunctionTypeRead[]>([]);
const qualificationTypeOptions = ref<QualificationTypeRead[]>([]);
const planningTeams = ref<TeamRead[]>([]);
const teamMembers = ref<TeamMemberRead[]>([]);
const employeeOptions = ref<EmployeeListItem[]>([]);
const subcontractorWorkerOptions = ref<SubcontractorWorkerListItem[]>([]);
const subcontractorReleases = ref<SubcontractorReleaseRead[]>([]);
const selectedShiftId = ref("");
const selectedDemandGroupId = ref("");
const selectedAssignmentId = ref("");
const selectedTeamId = ref("");
const demandGroupDialogOpen = ref(false);
const assignmentDialogOpen = ref(false);
const assignmentDialogMode = ref<"create" | "edit">("create");
const teamDialogOpen = ref(false);
const teamMemberDialogOpen = ref(false);
const activeShiftDetailTab = ref<"demand_staffing" | "validations" | "assignments" | "teams_releases" | "outputs_dispatch">("demand_staffing");
const shiftValidations = ref<ShiftReleaseValidationRead | null>(null);
const assignmentValidations = ref<AssignmentValidationRead | null>(null);
const assignmentOverrides = ref<any[]>([]);
const selectedAssignmentDetails = ref<AssignmentRead | null>(null);
const shiftOutputs = ref<PlanningOutputDocumentRead[]>([]);
const dispatchPreview = ref<PlanningDispatchPreviewRead | null>(null);
const dispatchAudienceEmployees = ref(true);
const dispatchAudienceSubcontractors = ref(false);
const overrideRuleCode = ref("");
const overrideReason = ref("");
const loading = ref(false);
const savingOverride = ref(false);
const savingDemandGroup = ref(false);
const savingTeam = ref(false);
const savingTeamMember = ref(false);
const assignmentEditorLoading = ref(false);
const assignmentEditorSaving = ref(false);
const planningRecordOptions = ref<PlanningRecordListItem[]>([]);
const resolvedPlanningRecord = ref<null | PlanningRecordRead>(null);
const planningRecordLookupLoading = ref(false);
const planningRecordLookupError = ref("");
const planningRecordLookupSearch = ref("");
const routeHydrationShiftId = ref("");
const routeHydrationInFlight = ref(false);
const feedback = reactive({ message: "", title: "", tone: "error" });
const filters = reactive<CoverageFilterParams>({
  customer_id: "",
  date_from: "2026-04-05T00:00",
  date_to: "2026-04-06T00:00",
  planning_record_id: "",
  shift_plan_id: "",
  order_id: "",
  planning_mode_code: "",
  workforce_scope_code: "",
  function_type_id: "",
  qualification_type_id: "",
  release_state: "",
  visibility_state: "",
  confirmation_state: "",
});
const staffingDraft = reactive({
  actor_kind: "employee",
  team_id: "",
  member_ref: "",
  assignment_source_code: "dispatcher",
  confirm_now: false,
  remarks: "",
});
const assignmentDraft = reactive({
  id: "",
  demand_group_id: "",
  actor_kind: "employee",
  team_id: "",
  member_ref: "",
  assignment_status_code: "assigned",
  assignment_source_code: "dispatcher",
  offered_at: "",
  confirmed_at: "",
  remarks: "",
  version_no: null as null | number,
});
const demandGroupDraft = reactive({
  id: "",
  function_type_id: "",
  qualification_type_id: "",
  min_qty: 1,
  target_qty: 1,
  mandatory_flag: true,
  sort_order: 100,
  remark: "",
  version_no: null as null | number,
});
const teamDraft = reactive({
  id: "",
  name: "",
  scope_kind: "planning",
  role_label: "",
  notes: "",
  lead_actor_kind: "employee",
  lead_member_ref: "",
  version_no: null as null | number,
});
const teamMemberDraft = reactive({
  id: "",
  team_id: "",
  actor_kind: "employee",
  member_ref: "",
  role_label: "",
  is_team_lead: false,
  valid_from: "",
  valid_to: "",
  notes: "",
  version_no: null as null | number,
});

function tp(key: keyof typeof planningStaffingMessages.de) {
  return planningStaffingMessages[currentLocale.value][key] ?? planningStaffingMessages.de[key] ?? key;
}

function routeQueryValue(value: unknown) {
  if (Array.isArray(value)) {
    return typeof value[0] === "string" ? value[0] : "";
  }
  return typeof value === "string" ? value : "";
}

function formatLocalDateTimeValue(value: Date) {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  const hours = String(value.getHours()).padStart(2, "0");
  const minutes = String(value.getMinutes()).padStart(2, "0");
  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

function formatShiftContextDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat(currentLocale.value === "en" ? "en-GB" : "de-DE", {
    dateStyle: "medium",
  }).format(date);
}

function formatShiftContextTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat(currentLocale.value === "en" ? "en-GB" : "de-DE", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function formatShiftContextTimeRange(startsAt: string, endsAt: string) {
  return `${formatShiftContextTime(startsAt)}–${formatShiftContextTime(endsAt)}`;
}

function canonicalStaffingWindow(startsAt: string, endsAt: string) {
  const start = new Date(startsAt);
  const end = new Date(endsAt);
  const dateFrom = new Date(start.getFullYear(), start.getMonth(), start.getDate(), 0, 0, 0, 0);
  const dateTo = new Date(end.getFullYear(), end.getMonth(), end.getDate() + 1, 0, 0, 0, 0);
  return {
    date_from: formatLocalDateTimeValue(dateFrom),
    date_to: formatLocalDateTimeValue(dateTo),
  };
}

function applyRouteQueryContext(query = route.query) {
  let changed = false;
  const nextDateFrom = routeQueryValue(query.date_from);
  const nextDateTo = routeQueryValue(query.date_to);
  const nextPlanningRecordId = routeQueryValue(query.planning_record_id);
  const nextShiftId = routeQueryValue(query.shift_id);

  if (nextDateFrom && filters.date_from !== nextDateFrom) {
    filters.date_from = nextDateFrom;
    changed = true;
  }
  if (nextDateTo && filters.date_to !== nextDateTo) {
    filters.date_to = nextDateTo;
    changed = true;
  }
  if (nextPlanningRecordId && filters.planning_record_id !== nextPlanningRecordId) {
    filters.planning_record_id = nextPlanningRecordId;
    changed = true;
  }
  if (nextShiftId && selectedShiftId.value !== nextShiftId) {
    selectedShiftId.value = nextShiftId;
    changed = true;
  }
  routeHydrationShiftId.value = nextShiftId || "";

  return changed;
}

const shiftDetailTabs = [
  { id: "demand_staffing", labelKey: "detailTabDemandStaffing" },
  { id: "validations", labelKey: "detailTabValidations" },
  { id: "assignments", labelKey: "detailTabAssignments" },
  { id: "teams_releases", labelKey: "detailTabTeamsReleases" },
  { id: "outputs_dispatch", labelKey: "detailTabOutputsDispatch" },
] as const;

const selectedShift = computed(() => coverageRows.value.find((row) => row.shift_id === selectedShiftId.value) ?? null);
const selectedBoardShift = computed(() => boardRows.value.find((row) => row.id === selectedShiftId.value) ?? null);
const relevantPlanningRecordId = computed(() => selectedShift.value?.planning_record_id || filters.planning_record_id || "");
const availableTeams = computed(() =>
  planningTeams.value.filter(
    (team) =>
      team.planning_record_id === relevantPlanningRecordId.value
      && (team.shift_id == null || team.shift_id === selectedShiftId.value),
  ),
);
const shiftTeams = computed(() => availableTeams.value.filter((team) => team.shift_id === selectedShiftId.value));
const selectedTeam = computed(() => availableTeams.value.find((team) => team.id === selectedTeamId.value) ?? null);
const selectedAssignment = computed<StaffingBoardAssignmentItem | null>(
  () => selectedBoardShift.value?.assignments.find((row) => row.id === selectedAssignmentId.value) ?? null,
);
const selectedDemandGroupDetails = computed<DemandGroupRead | null>(
  () => demandGroupRows.value.find((row) => row.id === selectedDemandGroupId.value) ?? null,
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
const selectedPlanningRecordOption = computed(
  () => planningRecordOptions.value.find((record) => record.id === relevantPlanningRecordId.value) ?? null,
);
const planningRecordFieldStatusShort = computed(() => {
  if (planningRecordLookupLoading.value) {
    return tp("filtersPlanningRecordLoadingShort");
  }
  if (planningRecordLookupError.value) {
    return tp("filtersPlanningRecordLookupErrorShort");
  }
  if (!planningRecordOptions.value.length) {
    return tp("filtersPlanningRecordEmptyShort");
  }
  if (filters.planning_record_id && !selectedPlanningRecordOptionLabel.value) {
    return tp("filtersPlanningRecordNoMatchShort");
  }
  return "";
});
const planningRecordFieldStatusTitle = computed(() => {
  if (planningRecordLookupLoading.value) {
    return tp("filtersPlanningRecordLoading");
  }
  if (planningRecordLookupError.value) {
    return planningRecordLookupError.value;
  }
  if (!planningRecordOptions.value.length) {
    return tp("filtersPlanningRecordEmpty");
  }
  if (filters.planning_record_id && !selectedPlanningRecordOptionLabel.value) {
    return tp("filtersPlanningRecordNoMatch");
  }
  return "";
});
const planningRecordDropdownEmptyContent = computed(() => {
  if (planningRecordLookupLoading.value) {
    return tp("filtersPlanningRecordLoading");
  }
  if (planningRecordLookupError.value) {
    return planningRecordLookupError.value;
  }
  return tp("filtersPlanningRecordEmpty");
});
const planningRecordDisplayName = computed(() => {
  if (selectedShift.value?.planning_record_name) {
    return selectedShift.value.planning_record_name;
  }
  if (selectedPlanningRecordOption.value?.name) {
    return selectedPlanningRecordOption.value.name;
  }
  if (resolvedPlanningRecord.value?.name) {
    return resolvedPlanningRecord.value.name;
  }
  return relevantPlanningRecordId.value || "";
});
const selectedShiftContextTitle = computed(() => planningRecordDisplayName.value || tp("detailTitle"));
const selectedShiftContextMeta = computed(() => {
  if (!selectedShift.value) {
    return "";
  }
  const dateLabel = formatShiftContextDate(selectedShift.value.starts_at);
  const timeLabel = formatShiftContextTimeRange(selectedShift.value.starts_at, selectedShift.value.ends_at);
  return [dateLabel, timeLabel, selectedShift.value.order_no, selectedShift.value.shift_type_code]
    .filter(Boolean)
    .join(" · ");
});
const hasPlanningContext = computed(() => Boolean(relevantPlanningRecordId.value));
const selectableTeamMembers = computed(() => buildStaffingMemberOptions(teamMembers.value, staffingDraft.team_id));
const selectedMember = computed(() => selectableTeamMembers.value.find((member) => member.id === staffingDraft.member_ref) ?? null);
const selectedTeamMembers = computed(() => {
  if (selectedTeam.value?.members?.length) {
    return selectedTeam.value.members;
  }
  return teamMembers.value.filter((member) => member.team_id === selectedTeamId.value);
});
const employeeMemberOptions = computed(() =>
  employeeOptions.value.map((employee) => ({
    label: formatEmployee(employee),
    value: employee.id,
  })),
);
const subcontractorWorkerMemberOptions = computed(() =>
  subcontractorWorkerOptions.value.map((worker) => ({
    label: formatSubcontractorWorker(worker),
    value: worker.id,
  })),
);
const teamLeadOptions = computed(() =>
  teamDraft.lead_actor_kind === "subcontractor_worker" ? subcontractorWorkerMemberOptions.value : employeeMemberOptions.value,
);
const teamMemberActorOptions = computed(() =>
  teamMemberDraft.actor_kind === "subcontractor_worker" ? subcontractorWorkerMemberOptions.value : employeeMemberOptions.value,
);
const assignmentActorOptions = computed(() =>
  assignmentDraft.actor_kind === "subcontractor_worker" ? subcontractorWorkerMemberOptions.value : employeeMemberOptions.value,
);
const hasSelectedDemandGroups = computed(() => Boolean(selectedBoardShift.value?.demand_groups?.length));
const editingDemandGroup = computed(() => Boolean(demandGroupDraft.id));
const editingTeam = computed(() => Boolean(teamDraft.id));
const editingTeamMember = computed(() => Boolean(teamMemberDraft.id));
const showDemandGroupSetupLead = computed(() => Boolean(selectedShiftId.value && !hasSelectedDemandGroups.value));
const showImmediateConfirmationControl = computed(() => actionState.value.canAssign && !selectedAssignment.value && hasSelectedDemandGroups.value);
const canSubmitDemandGroup = computed(() => {
  if (!actionState.value.canWriteStaffing || !selectedShiftId.value || !demandGroupDraft.function_type_id) {
    return false;
  }
  const minQty = Number(demandGroupDraft.min_qty);
  const targetQty = Number(demandGroupDraft.target_qty);
  const sortOrder = Number(demandGroupDraft.sort_order);
  if (!Number.isInteger(minQty) || !Number.isInteger(targetQty) || !Number.isInteger(sortOrder) || minQty < 0 || targetQty < minQty || sortOrder < 0) {
    return false;
  }
  return true;
});
const canSubmitAssign = computed(() => {
  if (!actionState.value.canAssign || !selectedShiftId.value || !selectedDemandGroupId.value || !hasSelectedDemandGroups.value) {
    return false;
  }
  return Boolean(staffingDraft.member_ref && selectedMember.value);
});
const canSubmitSubstitute = computed(() => canSubmitAssign.value && actionState.value.canSubstitute && !!selectedAssignment.value);
const canSubmitTeam = computed(() => {
  if (!hasPlanningContext.value) {
    return false;
  }
  if (!actionState.value.canWriteStaffing) {
    return false;
  }
  return Boolean(teamDraft.name.trim());
});
const canSubmitTeamMember = computed(() => {
  if (!actionState.value.canWriteStaffing || !teamMemberDraft.team_id || !teamMemberDraft.member_ref || !teamMemberDraft.valid_from) {
    return false;
  }
  return true;
});
const assignmentEditorMode = computed(() => assignmentDialogMode.value);
const assignmentCreateDialogActive = computed(
  () => assignmentDialogOpen.value && assignmentDialogMode.value === "create",
);
const planningStaffingWorkspaceBusy = computed(
  () =>
    loading.value
    || savingOverride.value
    || savingDemandGroup.value
    || savingTeam.value
    || savingTeamMember.value
    || assignmentEditorLoading.value
    || assignmentEditorSaving.value,
);
const planningStaffingWorkspaceLoadingText = computed(() => {
  if (assignmentEditorLoading.value) {
    return tp("workspaceLoadingAssignmentOpen");
  }
  if (assignmentEditorSaving.value) {
    return tp("workspaceLoadingAssignment");
  }
  if (savingDemandGroup.value) {
    return tp("workspaceLoadingDemandGroup");
  }
  if (savingTeam.value) {
    return tp("workspaceLoadingTeam");
  }
  if (savingTeamMember.value) {
    return tp("workspaceLoadingTeamMember");
  }
  if (savingOverride.value) {
    return tp("workspaceLoadingOverride");
  }
  if (loading.value) {
    return tp("workspaceLoading");
  }
  return "";
});
const canSubmitAssignmentEditor = computed(() => {
  if (!actionState.value.canWriteStaffing || !selectedShiftId.value || !assignmentDraft.demand_group_id || !assignmentDraft.member_ref) {
    return false;
  }
  if (assignmentEditorMode.value === "edit" && !assignmentDraft.id) {
    return false;
  }
  return true;
});
const assignmentStatusOptions = [
  { value: "offered", labelKey: "assignmentStatusOffered" },
  { value: "assigned", labelKey: "assignmentStatusAssigned" },
  { value: "confirmed", labelKey: "assignmentStatusConfirmed" },
  { value: "removed", labelKey: "assignmentStatusRemoved" },
] as const;
const assignmentSourceOptions = [
  { value: "dispatcher", labelKey: "assignmentSourceDispatcher" },
  { value: "manual", labelKey: "assignmentSourceManual" },
  { value: "subcontractor_release", labelKey: "assignmentSourceSubcontractorRelease" },
  { value: "portal_allocation", labelKey: "assignmentSourcePortalAllocation" },
] as const;

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
  if (state === "setup_required") {
    return "statusSetupRequired";
  }
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

function queryFilters(): CoverageFilterParams {
  return {
    customer_id: filters.customer_id || undefined,
    planning_record_id: filters.planning_record_id || undefined,
    shift_plan_id: filters.shift_plan_id || undefined,
    order_id: filters.order_id || undefined,
    date_from: filters.date_from,
    date_to: filters.date_to,
    planning_mode_code: filters.planning_mode_code || undefined,
    workforce_scope_code: filters.workforce_scope_code || undefined,
    function_type_id: filters.function_type_id || undefined,
    qualification_type_id: filters.qualification_type_id || undefined,
    release_state: filters.release_state || undefined,
    visibility_state: filters.visibility_state || undefined,
    confirmation_state: filters.confirmation_state || undefined,
  };
}

function exactShiftBoardFilters(shiftId: string) {
  return {
    date_from: filters.date_from,
    date_to: filters.date_to,
    planning_record_id: filters.planning_record_id || undefined,
    shift_id: shiftId,
  };
}

async function normalizeRouteHydrationWindow() {
  if (!routeHydrationShiftId.value || !tenantScopeId.value || !accessToken.value) {
    return;
  }
  try {
    const shift = await getShift(tenantScopeId.value, routeHydrationShiftId.value, accessToken.value);
    const canonicalWindow = canonicalStaffingWindow(shift.starts_at, shift.ends_at);
    filters.date_from = canonicalWindow.date_from;
    filters.date_to = canonicalWindow.date_to;
  } catch {
    // Leave the original route window in place if the exact shift cannot be read.
  }
}

function rowCoverageState(row: CoverageShiftItem | null) {
  if (!row) {
    return "red";
  }
  return resolvePlanningStaffingCoverageState(row.coverage_state, row.demand_groups);
}

const planningRecordLookupCache = new Map<string, PlanningRecordListItem[]>();
const assignmentDetailCache = new Map<string, AssignmentRead>();
const assignmentValidationCache = new Map<string, AssignmentValidationRead>();
const assignmentOverrideCache = new Map<string, any[]>();
const assignmentInspectionRequests = new Map<string, Promise<void>>();
let planningRecordLookupRequestId = 0;
let planningRecordLookupTimer: ReturnType<typeof setTimeout> | null = null;

function staffingFilters() {
  return {
    shift_id: selectedShiftId.value,
    planning_record_id: filters.planning_record_id,
  };
}

function coverageStateForCounts(
  minQty: number,
  targetQty: number,
  assignedCount: number,
  confirmedCount: number,
  releasedPartnerQty: number,
) {
  if (targetQty > 0 && assignedCount >= targetQty && confirmedCount >= Math.min(targetQty, assignedCount)) {
    return "green";
  }
  if (assignedCount + releasedPartnerQty >= minQty) {
    return "yellow";
  }
  return "red";
}

function deriveCoverageRowFromBoardShift(boardShift: StaffingBoardShiftItem): CoverageShiftItem {
  const demandGroups = boardShift.demand_groups.map((group) => ({
    demand_group_id: group.id,
    function_type_id: group.function_type_id,
    qualification_type_id: group.qualification_type_id,
    min_qty: group.min_qty,
    target_qty: group.target_qty,
    assigned_count: group.assigned_count,
    confirmed_count: group.confirmed_count,
    released_partner_qty: group.released_partner_qty,
    coverage_state: coverageStateForCounts(
      group.min_qty,
      group.target_qty,
      group.assigned_count,
      group.confirmed_count,
      group.released_partner_qty,
    ),
  }));
  const assignedCount = filters.confirmation_state === "confirmed_only"
    ? demandGroups.reduce((sum, group) => sum + group.confirmed_count, 0)
    : demandGroups.reduce((sum, group) => sum + group.assigned_count, 0);
  const confirmedCount = demandGroups.reduce((sum, group) => sum + group.confirmed_count, 0);
  const minRequiredQty = demandGroups.reduce((sum, group) => sum + group.min_qty, 0);
  const targetRequiredQty = demandGroups.reduce((sum, group) => sum + group.target_qty, 0);
  const releasedPartnerQty = demandGroups.reduce((sum, group) => sum + group.released_partner_qty, 0);
  return {
    shift_id: boardShift.id,
    planning_record_id: boardShift.planning_record_id,
    shift_plan_id: boardShift.shift_plan_id,
    order_id: boardShift.order_id,
    order_no: boardShift.order_no,
    planning_record_name: boardShift.planning_record_name,
    planning_mode_code: boardShift.planning_mode_code,
    workforce_scope_code: boardShift.workforce_scope_code,
    starts_at: boardShift.starts_at,
    ends_at: boardShift.ends_at,
    shift_type_code: boardShift.shift_type_code,
    location_text: boardShift.location_text,
    meeting_point: boardShift.meeting_point,
    min_required_qty: minRequiredQty,
    target_required_qty: targetRequiredQty,
    assigned_count: assignedCount,
    confirmed_count: confirmedCount,
    released_partner_qty: releasedPartnerQty,
    coverage_state: coverageStateForCounts(
      minRequiredQty,
      targetRequiredQty,
      assignedCount,
      confirmedCount,
      releasedPartnerQty,
    ),
    demand_groups: demandGroups,
  };
}

function assignmentIsConfirmed(assignment: Pick<StaffingBoardAssignmentItem, "assignment_status_code" | "confirmed_at">) {
  return Boolean(assignment.confirmed_at) || assignment.assignment_status_code === "confirmed";
}

function toBoardAssignmentItem(
  assignment: AssignmentRead | StaffingBoardAssignmentItem,
): StaffingBoardAssignmentItem {
  return {
    id: assignment.id,
    shift_id: assignment.shift_id,
    demand_group_id: assignment.demand_group_id,
    team_id: assignment.team_id ?? null,
    employee_id: assignment.employee_id ?? null,
    subcontractor_worker_id: assignment.subcontractor_worker_id ?? null,
    assignment_status_code: assignment.assignment_status_code,
    assignment_source_code: assignment.assignment_source_code,
    confirmed_at: assignment.confirmed_at ?? null,
    version_no: assignment.version_no,
  };
}

function patchShiftAssignments(
  shiftId: string,
  mutateAssignments: (rows: StaffingBoardAssignmentItem[]) => StaffingBoardAssignmentItem[],
) {
  let nextBoardShift: StaffingBoardShiftItem | null = null;
  boardRows.value = boardRows.value.map((row) => {
    if (row.id !== shiftId) {
      return row;
    }
    const nextAssignments = mutateAssignments([...row.assignments]);
    const nextDemandGroups = row.demand_groups.map((group) => {
      const groupAssignments = nextAssignments.filter((assignment) => assignment.demand_group_id === group.id);
      const assignedCount = groupAssignments.length;
      const confirmedCount = groupAssignments.filter(assignmentIsConfirmed).length;
      return {
        ...group,
        assigned_count: assignedCount,
        confirmed_count: confirmedCount,
      };
    });
    nextBoardShift = {
      ...row,
      assignments: nextAssignments,
      demand_groups: nextDemandGroups,
    };
    return nextBoardShift;
  });

  if (!nextBoardShift) {
    return;
  }

  coverageRows.value = coverageRows.value.map((row) => {
    if (row.shift_id !== shiftId) {
      return row;
    }
    const nextCoverageDemandGroups = nextBoardShift!.demand_groups.map((group) => ({
      demand_group_id: group.id,
      function_type_id: group.function_type_id,
      qualification_type_id: group.qualification_type_id,
      min_qty: group.min_qty,
      target_qty: group.target_qty,
      assigned_count: group.assigned_count,
      confirmed_count: group.confirmed_count,
      released_partner_qty: group.released_partner_qty,
      coverage_state: coverageStateForCounts(
        group.min_qty,
        group.target_qty,
        group.assigned_count,
        group.confirmed_count,
        group.released_partner_qty,
      ),
    }));
    const assignedCount = filters.confirmation_state === "confirmed_only"
      ? nextCoverageDemandGroups.reduce((sum, group) => sum + group.confirmed_count, 0)
      : nextCoverageDemandGroups.reduce((sum, group) => sum + group.assigned_count, 0);
    const confirmedCount = nextCoverageDemandGroups.reduce((sum, group) => sum + group.confirmed_count, 0);
    const minRequiredQty = nextCoverageDemandGroups.reduce((sum, group) => sum + group.min_qty, 0);
    const targetRequiredQty = nextCoverageDemandGroups.reduce((sum, group) => sum + group.target_qty, 0);
    const releasedPartnerQty = nextCoverageDemandGroups.reduce((sum, group) => sum + group.released_partner_qty, 0);
    return {
      ...row,
      min_required_qty: minRequiredQty,
      target_required_qty: targetRequiredQty,
      assigned_count: assignedCount,
      confirmed_count: confirmedCount,
      released_partner_qty: releasedPartnerQty,
      coverage_state: coverageStateForCounts(
        minRequiredQty,
        targetRequiredQty,
        assignedCount,
        confirmedCount,
        releasedPartnerQty,
      ),
      demand_groups: nextCoverageDemandGroups,
    };
  });

  selectedDemandGroupId.value = resolveSelectedDemandGroupId(nextBoardShift, selectedDemandGroupId.value);
}

function upsertShiftAssignment(assignment: AssignmentRead | StaffingBoardAssignmentItem) {
  const boardAssignment = toBoardAssignmentItem(assignment);
  patchShiftAssignments(boardAssignment.shift_id, (rows) => {
    const nextRows = rows.filter((row) => row.id !== boardAssignment.id);
    nextRows.push(boardAssignment);
    return nextRows;
  });
}

function removeShiftAssignment(shiftId: string, assignmentId: string) {
  patchShiftAssignments(shiftId, (rows) => rows.filter((row) => row.id !== assignmentId));
}

function cacheAssignmentDetail(assignment: AssignmentRead) {
  assignmentDetailCache.set(assignment.id, assignment);
}

function invalidateAssignmentInspection(assignmentId: string) {
  if (!assignmentId) {
    return;
  }
  assignmentDetailCache.delete(assignmentId);
  assignmentValidationCache.delete(assignmentId);
  assignmentOverrideCache.delete(assignmentId);
}

function applyCachedAssignmentInspection(assignmentId: string) {
  const cachedAssignment = assignmentDetailCache.get(assignmentId) ?? null;
  const cachedValidations = assignmentValidationCache.get(assignmentId) ?? null;
  const cachedOverrides = assignmentOverrideCache.get(assignmentId) ?? [];
  selectedAssignmentDetails.value = cachedAssignment;
  assignmentValidations.value = cachedValidations;
  assignmentOverrides.value = cachedOverrides;
  if (cachedAssignment) {
    populateAssignmentDraft(cachedAssignment);
  } else if (!assignmentCreateDialogActive.value) {
    resetAssignmentDraft();
  }
  return Boolean(cachedAssignment);
}

async function loadSelectedAssignmentMeta() {
  if (!tenantScopeId.value || !accessToken.value || !selectedAssignmentId.value) {
    assignmentValidations.value = null;
    assignmentOverrides.value = [];
    return;
  }
  const assignmentId = selectedAssignmentId.value;
  const [validations, overrides] = await Promise.all([
    getAssignmentValidations(tenantScopeId.value, accessToken.value, assignmentId),
    listAssignmentValidationOverrides(tenantScopeId.value, accessToken.value, assignmentId),
  ]);
  if (selectedAssignmentId.value !== assignmentId) {
    return;
  }
  assignmentValidationCache.set(assignmentId, validations);
  assignmentOverrideCache.set(assignmentId, overrides);
  assignmentValidations.value = validations;
  assignmentOverrides.value = overrides;
}

async function refreshVisibleAssignmentDiagnostics() {
  if (
    !selectedAssignmentId.value
    || (activeShiftDetailTab.value !== "assignments" && activeShiftDetailTab.value !== "validations" && !assignmentDialogOpen.value)
  ) {
    return;
  }
  try {
    await loadSelectedAssignmentMeta();
  } catch {
    // Keep the optimistic assignment update and avoid blocking the primary mutation path on side data.
  }
}

async function refreshVisibleShiftValidations() {
  if (!tenantScopeId.value || !accessToken.value || !selectedShiftId.value || activeShiftDetailTab.value !== "validations") {
    return;
  }
  try {
    shiftValidations.value = await getShiftReleaseValidations(tenantScopeId.value, accessToken.value, selectedShiftId.value);
  } catch {
    // Keep the visible shift state stable if validation refresh fails in the background.
  }
}

function resetStaffingDraft() {
  staffingDraft.actor_kind = "employee";
  staffingDraft.team_id = "";
  staffingDraft.member_ref = "";
  staffingDraft.assignment_source_code = "dispatcher";
  staffingDraft.confirm_now = false;
  staffingDraft.remarks = "";
}

function resetAssignmentDraft() {
  assignmentDraft.id = "";
  assignmentDraft.demand_group_id = selectedDemandGroupId.value || selectedBoardShift.value?.demand_groups?.[0]?.id || "";
  assignmentDraft.actor_kind = "employee";
  assignmentDraft.team_id = "";
  assignmentDraft.member_ref = "";
  assignmentDraft.assignment_status_code = "assigned";
  assignmentDraft.assignment_source_code = "dispatcher";
  assignmentDraft.offered_at = "";
  assignmentDraft.confirmed_at = "";
  assignmentDraft.remarks = "";
  assignmentDraft.version_no = null;
}

function populateAssignmentDraft(assignment: AssignmentRead) {
  assignmentDraft.id = assignment.id;
  assignmentDraft.demand_group_id = assignment.demand_group_id;
  assignmentDraft.actor_kind = assignment.subcontractor_worker_id ? "subcontractor_worker" : "employee";
  assignmentDraft.team_id = assignment.team_id || "";
  assignmentDraft.member_ref = assignment.subcontractor_worker_id || assignment.employee_id || "";
  assignmentDraft.assignment_status_code = assignment.assignment_status_code;
  assignmentDraft.assignment_source_code = assignment.assignment_source_code;
  assignmentDraft.offered_at = normalizeDateTimeLocal(assignment.offered_at);
  assignmentDraft.confirmed_at = normalizeDateTimeLocal(assignment.confirmed_at);
  assignmentDraft.remarks = assignment.remarks || "";
  assignmentDraft.version_no = assignment.version_no;
}

function startCreateAssignment() {
  assignmentDialogMode.value = "create";
  selectedAssignmentId.value = "";
  selectedAssignmentDetails.value = null;
  resetAssignmentDraft();
  assignmentDialogOpen.value = true;
}

async function startEditAssignment(assignmentId = selectedAssignmentId.value) {
  if (!assignmentId || assignmentEditorLoading.value || assignmentEditorSaving.value) {
    return;
  }
  assignmentDialogMode.value = "edit";
  assignmentDialogOpen.value = true;
  assignmentEditorLoading.value = true;
  selectedAssignmentId.value = assignmentId;
  const hasCachedAssignment = applyCachedAssignmentInspection(assignmentId);
  if (!hasCachedAssignment) {
    selectedAssignmentDetails.value = null;
    assignmentValidations.value = null;
    assignmentOverrides.value = [];
  }
  try {
    const loadPromise = loadSelectedAssignmentDetails();
    if (hasCachedAssignment) {
      assignmentEditorLoading.value = false;
      void loadPromise;
      return;
    }
    await loadPromise;
  } finally {
    assignmentEditorLoading.value = false;
  }
}

function resetAssignmentEditor() {
  if (assignmentEditorMode.value === "create") {
    resetAssignmentDraft();
    return;
  }
  if (selectedAssignmentDetails.value) {
    populateAssignmentDraft(selectedAssignmentDetails.value);
    return;
  }
  resetAssignmentDraft();
}

function closeAssignmentDialog() {
  assignmentDialogOpen.value = false;
  resetAssignmentEditor();
}

function resetTeamDraft() {
  teamDraft.id = "";
  teamDraft.name = "";
  teamDraft.scope_kind = selectedShiftId.value ? "shift" : "planning";
  teamDraft.role_label = "";
  teamDraft.notes = "";
  teamDraft.lead_actor_kind = "employee";
  teamDraft.lead_member_ref = "";
  teamDraft.version_no = null;
}

function resetTeamMemberDraft() {
  teamMemberDraft.id = "";
  teamMemberDraft.team_id = selectedTeamId.value || "";
  teamMemberDraft.actor_kind = "employee";
  teamMemberDraft.member_ref = "";
  teamMemberDraft.role_label = "";
  teamMemberDraft.is_team_lead = false;
  teamMemberDraft.valid_from = normalizeDateTimeLocal(selectedShift.value?.starts_at) || filters.date_from;
  teamMemberDraft.valid_to = "";
  teamMemberDraft.notes = "";
  teamMemberDraft.version_no = null;
}

function resetDemandGroupDraft() {
  demandGroupDraft.id = "";
  demandGroupDraft.function_type_id = "";
  demandGroupDraft.qualification_type_id = "";
  demandGroupDraft.min_qty = 1;
  demandGroupDraft.target_qty = 1;
  demandGroupDraft.mandatory_flag = true;
  demandGroupDraft.sort_order = 100;
  demandGroupDraft.remark = "";
  demandGroupDraft.version_no = null;
}

function startCreateDemandGroup() {
  resetDemandGroupDraft();
  demandGroupDialogOpen.value = true;
}

function startEditDemandGroup(demandGroupId = selectedDemandGroupId.value) {
  const demandGroup = demandGroupRows.value.find((row) => row.id === demandGroupId) ?? null;
  if (!demandGroup) {
    return;
  }
  selectedDemandGroupId.value = demandGroup.id;
  demandGroupDraft.id = demandGroup.id;
  demandGroupDraft.function_type_id = demandGroup.function_type_id || "";
  demandGroupDraft.qualification_type_id = demandGroup.qualification_type_id || "";
  demandGroupDraft.min_qty = demandGroup.min_qty;
  demandGroupDraft.target_qty = demandGroup.target_qty;
  demandGroupDraft.mandatory_flag = demandGroup.mandatory_flag;
  demandGroupDraft.sort_order = demandGroup.sort_order;
  demandGroupDraft.remark = demandGroup.remark || "";
  demandGroupDraft.version_no = demandGroup.version_no;
  demandGroupDialogOpen.value = true;
}

function closeDemandGroupDialog() {
  demandGroupDialogOpen.value = false;
  resetDemandGroupDraft();
}

function formatDemandGroup(group: StaffingBoardDemandGroupItem | null) {
  return formatPlanningStaffingDemandGroupLabel(group, functionTypeOptions.value, qualificationTypeOptions.value);
}

function formatMember(member: TeamMemberRead) {
  if (member.employee_id) {
    return formatEmployee(employeeOptions.value.find((row) => row.id === member.employee_id)) || `employee:${member.employee_id}`;
  }
  if (member.subcontractor_worker_id) {
    return formatSubcontractorWorker(subcontractorWorkerOptions.value.find((row) => row.id === member.subcontractor_worker_id))
      || `worker:${member.subcontractor_worker_id}`;
  }
  return member.id;
}

function formatAssignmentActor(assignment: StaffingBoardAssignmentItem | null) {
  if (!assignment) {
    return "";
  }
  if (assignment.employee_id) {
    return formatEmployee(employeeOptions.value.find((row) => row.id === assignment.employee_id)) || `employee:${assignment.employee_id}`;
  }
  if (assignment.subcontractor_worker_id) {
    return formatSubcontractorWorker(subcontractorWorkerOptions.value.find((row) => row.id === assignment.subcontractor_worker_id))
      || `worker:${assignment.subcontractor_worker_id}`;
  }
  return actorLabel(assignment);
}

function formatEmployee(employee?: EmployeeListItem | null) {
  if (!employee) {
    return "";
  }
  return [employee.personnel_no, `${employee.first_name} ${employee.last_name}`.trim()].filter(Boolean).join(" · ");
}

function formatSubcontractorWorker(worker?: SubcontractorWorkerListItem | null) {
  if (!worker) {
    return "";
  }
  return [worker.worker_no, `${worker.first_name} ${worker.last_name}`.trim()].filter(Boolean).join(" · ");
}

function formatTeam(team: TeamRead | null) {
  if (!team) {
    return "";
  }
  return `${team.name} · ${tp(team.shift_id ? "teamScopeShift" : "teamScopePlanning")}`;
}

function assignmentTeamLabel(teamId: null | string) {
  if (!teamId) {
    return tp("unassignedLabel");
  }
  return formatTeam(availableTeams.value.find((team) => team.id === teamId) ?? planningTeams.value.find((team) => team.id === teamId) ?? null) || teamId;
}

function formatDemandGroupById(demandGroupId: string) {
  const boardGroup = selectedBoardShift.value?.demand_groups.find((row) => row.id === demandGroupId) ?? null;
  if (boardGroup) {
    return formatDemandGroup(boardGroup);
  }
  const detailGroup = demandGroupRows.value.find((row) => row.id === demandGroupId) ?? null;
  return detailGroup ? formatPlanningStaffingDemandGroupLabel(detailGroup, functionTypeOptions.value, qualificationTypeOptions.value) : demandGroupId;
}

function normalizeDateTimeLocal(value?: null | string) {
  if (!value) {
    return "";
  }
  return value.slice(0, 16);
}

function toIsoDateTime(value: string) {
  return value ? new Date(value).toISOString() : null;
}

function teamScopePayload() {
  return {
    planning_record_id: relevantPlanningRecordId.value || null,
    shift_id: teamDraft.scope_kind === "shift" ? (selectedShiftId.value || null) : null,
  };
}

function selectedActorPayload(actorKind: string, memberRef: string) {
  return {
    employee_id: actorKind === "employee" ? (memberRef || null) : null,
    subcontractor_worker_id: actorKind === "subcontractor_worker" ? (memberRef || null) : null,
  };
}

function startCreateTeam(scopeKind: "planning" | "shift" = "planning") {
  resetTeamDraft();
  teamDraft.scope_kind = scopeKind;
  teamDialogOpen.value = true;
}

async function startEditTeam(teamId = selectedTeamId.value) {
  if (!tenantScopeId.value || !accessToken.value || !teamId) {
    return;
  }
  const team = await getTeam(tenantScopeId.value, accessToken.value, teamId);
  selectedTeamId.value = team.id;
  teamDraft.id = team.id;
  teamDraft.name = team.name;
  teamDraft.scope_kind = team.shift_id ? "shift" : "planning";
  teamDraft.role_label = team.role_label || "";
  teamDraft.notes = team.notes || "";
  teamDraft.lead_actor_kind = "employee";
  teamDraft.lead_member_ref = "";
  teamDraft.version_no = team.version_no;
  teamDialogOpen.value = true;
}

function closeTeamDialog() {
  teamDialogOpen.value = false;
  resetTeamDraft();
}

function startCreateTeamMember(teamId = selectedTeamId.value) {
  if (!teamId) {
    return;
  }
  resetTeamMemberDraft();
  teamMemberDraft.team_id = teamId;
  teamMemberDialogOpen.value = true;
}

function startEditTeamMember(memberId: string) {
  const member = teamMembers.value.find((row) => row.id === memberId) ?? selectedTeamMembers.value.find((row) => row.id === memberId);
  if (!member) {
    return;
  }
  teamMemberDraft.id = member.id;
  teamMemberDraft.team_id = member.team_id;
  teamMemberDraft.actor_kind = member.subcontractor_worker_id ? "subcontractor_worker" : "employee";
  teamMemberDraft.member_ref = member.employee_id || member.subcontractor_worker_id || "";
  teamMemberDraft.role_label = member.role_label || "";
  teamMemberDraft.is_team_lead = member.is_team_lead;
  teamMemberDraft.valid_from = normalizeDateTimeLocal(member.valid_from);
  teamMemberDraft.valid_to = normalizeDateTimeLocal(member.valid_to);
  teamMemberDraft.notes = member.notes || "";
  teamMemberDraft.version_no = member.version_no;
  teamMemberDialogOpen.value = true;
}

function closeTeamMemberDialog() {
  teamMemberDialogOpen.value = false;
  resetTeamMemberDraft();
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

async function ensurePlanningRecordResolved() {
  if (!tenantScopeId.value || !accessToken.value || !relevantPlanningRecordId.value) {
    resolvedPlanningRecord.value = null;
    return;
  }
  if (selectedShift.value?.planning_record_name || selectedPlanningRecordOption.value?.name) {
    resolvedPlanningRecord.value = null;
    return;
  }
  if (resolvedPlanningRecord.value?.id === relevantPlanningRecordId.value && resolvedPlanningRecord.value.name) {
    return;
  }
  try {
    resolvedPlanningRecord.value = await getPlanningRecord(tenantScopeId.value, relevantPlanningRecordId.value, accessToken.value);
  } catch {
    resolvedPlanningRecord.value = null;
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
  if (!tenantScopeId.value || !accessToken.value || !relevantPlanningRecordId.value) {
    demandGroupRows.value = [];
    planningTeams.value = [];
    teamMembers.value = [];
    employeeOptions.value = [];
    subcontractorWorkerOptions.value = [];
    subcontractorReleases.value = [];
    return;
  }
  const [demandGroups, teams, members, releases, employees] = await Promise.all([
    selectedShiftId.value
      ? listDemandGroups(tenantScopeId.value, accessToken.value, staffingFilters())
      : Promise.resolve([]),
    listTeams(tenantScopeId.value, accessToken.value, { planning_record_id: relevantPlanningRecordId.value }),
    listTeamMembers(tenantScopeId.value, accessToken.value, {}),
    selectedShiftId.value
      ? listSubcontractorReleases(tenantScopeId.value, accessToken.value, staffingFilters())
      : Promise.resolve([]),
    listEmployees(tenantScopeId.value, accessToken.value, { status: "active" }),
  ]);
  const workerRows = releases.length
    ? (
        await Promise.all(
          [...new Set(releases.map((row) => row.subcontractor_id).filter(Boolean))].map((subcontractorId) =>
            listSubcontractorWorkers(tenantScopeId.value, subcontractorId, accessToken.value, { status: "active" }),
          ),
        )
      ).flat()
    : [];
  demandGroupRows.value = demandGroups;
  planningTeams.value = teams;
  teamMembers.value = members;
  employeeOptions.value = employees.filter((row) => row.archived_at == null && row.status === "active");
  subcontractorWorkerOptions.value = workerRows.filter((row) => row.archived_at == null && row.status === "active");
  subcontractorReleases.value = releases;
  if (!availableTeams.value.some((team) => team.id === staffingDraft.team_id)) {
    staffingDraft.team_id = "";
    staffingDraft.member_ref = "";
  }
  if (!availableTeams.value.some((team) => team.id === selectedTeamId.value)) {
    selectedTeamId.value = availableTeams.value[0]?.id ?? "";
  }
}

async function loadDemandGroupCatalogOptions() {
  if (!tenantScopeId.value || !accessToken.value) {
    functionTypeOptions.value = [];
    qualificationTypeOptions.value = [];
    return;
  }
  const [functionTypes, qualificationTypes] = await Promise.all([
    listFunctionTypes(tenantScopeId.value, accessToken.value),
    listQualificationTypes(tenantScopeId.value, accessToken.value),
  ]);
  functionTypeOptions.value = functionTypes.filter((row) => row.status === "active" && row.archived_at == null);
  qualificationTypeOptions.value = qualificationTypes.filter((row) => row.status === "active" && row.archived_at == null);
}

async function refreshAll() {
  clearFeedback();
  if (!tenantScopeId.value || !accessToken.value) {
    return;
  }
  loading.value = true;
  try {
    if (routeHydrationShiftId.value) {
      await normalizeRouteHydrationWindow();
    }
    const requestedShiftId = routeHydrationShiftId.value || "";
    const [coverage, board] = await Promise.all([
      listStaffingCoverage(tenantScopeId.value, accessToken.value, queryFilters()),
      listStaffingBoard(tenantScopeId.value, accessToken.value, queryFilters()),
    ]);
    let hydratedBoard = board;
    let exactShiftBoard = requestedShiftId
      ? hydratedBoard.find((row) => row.id === requestedShiftId) ?? null
      : null;

    if (requestedShiftId && !exactShiftBoard) {
      const exactBoardRows = await listStaffingBoard(
        tenantScopeId.value,
        accessToken.value,
        exactShiftBoardFilters(requestedShiftId),
      );
      exactShiftBoard = exactBoardRows.find((row) => row.id === requestedShiftId) ?? null;
      if (exactShiftBoard && !hydratedBoard.some((row) => row.id === exactShiftBoard?.id)) {
        hydratedBoard = [exactShiftBoard, ...hydratedBoard];
      }
    }

    let hydratedCoverage = coverage;
    if (exactShiftBoard && !hydratedCoverage.some((row) => row.shift_id === exactShiftBoard?.id)) {
      hydratedCoverage = [deriveCoverageRowFromBoardShift(exactShiftBoard), ...hydratedCoverage];
    }

    coverageRows.value = hydratedCoverage;
    boardRows.value = hydratedBoard;
    if (requestedShiftId && exactShiftBoard) {
      selectedShiftId.value = requestedShiftId;
      routeHydrationShiftId.value = "";
    } else if (!coverageRows.value.find((row) => row.shift_id === selectedShiftId.value)) {
      selectedShiftId.value = coverageRows.value[0]?.shift_id ?? "";
      routeHydrationShiftId.value = "";
    }
    if (!selectedShiftId.value) {
      selectedDemandGroupId.value = "";
      selectedAssignmentId.value = "";
      shiftValidations.value = null;
      assignmentValidations.value = null;
      assignmentOverrides.value = [];
      shiftOutputs.value = [];
      dispatchPreview.value = null;
      await refreshSupportingData();
      return;
    }
    await loadSelectedShiftDetails();
  } catch (error) {
    handleApiError(error);
  } finally {
    routeHydrationInFlight.value = false;
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
    selectedAssignmentDetails.value = null;
    if (!assignmentCreateDialogActive.value) {
      resetAssignmentDraft();
    }
    assignmentValidations.value = null;
    assignmentOverrides.value = [];
    return;
  }
  if (!boardShift.assignments.some((row) => row.id === selectedAssignmentId.value)) {
    selectedAssignmentId.value = "";
  }
  await loadSelectedAssignmentDetails();
}

async function loadSelectedAssignmentDetails() {
  if (!tenantScopeId.value || !accessToken.value || !selectedAssignmentId.value) {
    selectedAssignmentDetails.value = null;
    assignmentValidations.value = null;
    assignmentOverrides.value = [];
    if (!assignmentCreateDialogActive.value) {
      resetAssignmentDraft();
    }
    return;
  }
  const assignmentId = selectedAssignmentId.value;
  const cachedAssignment = assignmentDetailCache.get(assignmentId) ?? null;
  const cachedValidations = assignmentValidationCache.get(assignmentId) ?? null;
  const cachedOverrides = assignmentOverrideCache.get(assignmentId) ?? null;
  if (cachedAssignment) {
    selectedAssignmentDetails.value = cachedAssignment;
    populateAssignmentDraft(cachedAssignment);
  }
  if (cachedValidations) {
    assignmentValidations.value = cachedValidations;
  }
  if (cachedOverrides) {
    assignmentOverrides.value = cachedOverrides;
  }
  if (cachedAssignment && cachedValidations && cachedOverrides) {
    return;
  }
  let request = assignmentInspectionRequests.get(assignmentId);
  if (!request) {
    request = Promise.all([
      getAssignment(tenantScopeId.value, accessToken.value, assignmentId),
      getAssignmentValidations(tenantScopeId.value, accessToken.value, assignmentId),
      listAssignmentValidationOverrides(tenantScopeId.value, accessToken.value, assignmentId),
    ])
      .then(([assignment, validations, overrides]) => {
        assignmentDetailCache.set(assignmentId, assignment);
        assignmentValidationCache.set(assignmentId, validations);
        assignmentOverrideCache.set(assignmentId, overrides);
      })
      .finally(() => {
        assignmentInspectionRequests.delete(assignmentId);
      });
    assignmentInspectionRequests.set(assignmentId, request);
  }
  await request;
  if (selectedAssignmentId.value !== assignmentId) {
    return;
  }
  const assignment = assignmentDetailCache.get(assignmentId) ?? null;
  const validations = assignmentValidationCache.get(assignmentId) ?? null;
  const overrides = assignmentOverrideCache.get(assignmentId) ?? [];
  if (!assignment || !validations) {
    return;
  }
  selectedAssignmentDetails.value = assignment;
  populateAssignmentDraft(assignment);
  assignmentValidations.value = validations;
  assignmentOverrides.value = overrides;
  if (overrideRuleCode.value && !validations.issues.some((issue) => issue.rule_code === overrideRuleCode.value && issue.override_allowed)) {
    cancelOverride();
  }
}

function assignmentEditorPayload() {
  return {
    team_id: assignmentDraft.team_id || null,
    employee_id: assignmentDraft.actor_kind === "employee" ? (assignmentDraft.member_ref || null) : null,
    subcontractor_worker_id: assignmentDraft.actor_kind === "subcontractor_worker" ? (assignmentDraft.member_ref || null) : null,
    assignment_status_code: assignmentDraft.assignment_status_code,
    assignment_source_code: assignmentDraft.assignment_source_code,
    offered_at: toIsoDateTime(assignmentDraft.offered_at),
    confirmed_at: toIsoDateTime(assignmentDraft.confirmed_at),
    remarks: assignmentDraft.remarks.trim() || null,
  };
}

async function submitAssignmentEditor() {
  if (!tenantScopeId.value || !accessToken.value || !selectedShiftId.value || !canSubmitAssignmentEditor.value) {
    return;
  }
  clearFeedback();
  assignmentEditorSaving.value = true;
  try {
    let assignment: AssignmentRead;
    if (assignmentEditorMode.value === "edit" && assignmentDraft.id) {
      const payload: AssignmentUpdate = {
        ...assignmentEditorPayload(),
        version_no: assignmentDraft.version_no,
      };
      assignment = await updateAssignment(tenantScopeId.value, accessToken.value, assignmentDraft.id, payload);
    } else {
      const payload: AssignmentCreate = {
        tenant_id: tenantScopeId.value,
        shift_id: selectedShiftId.value,
        demand_group_id: assignmentDraft.demand_group_id,
        ...assignmentEditorPayload(),
      };
      assignment = await createAssignment(tenantScopeId.value, accessToken.value, payload);
    }
    cacheAssignmentDetail(assignment);
    assignmentValidationCache.delete(assignment.id);
    assignmentOverrideCache.delete(assignment.id);
    upsertShiftAssignment(assignment);
    selectedAssignmentId.value = assignment.id;
    selectedAssignmentDetails.value = assignment;
    assignmentValidations.value = null;
    assignmentOverrides.value = [];
    assignmentDialogOpen.value = false;
    void refreshVisibleAssignmentDiagnostics();
    void refreshVisibleShiftValidations();
  } catch (error) {
    handleApiError(error);
  } finally {
    assignmentEditorSaving.value = false;
  }
}

async function submitDemandGroup() {
  if (!tenantScopeId.value || !accessToken.value || !selectedShiftId.value || !canSubmitDemandGroup.value) {
    return;
  }
  clearFeedback();
  savingDemandGroup.value = true;
  try {
    const payload = {
      tenant_id: tenantScopeId.value,
      shift_id: selectedShiftId.value,
      function_type_id: demandGroupDraft.function_type_id,
      qualification_type_id: demandGroupDraft.qualification_type_id || null,
      min_qty: Number(demandGroupDraft.min_qty),
      target_qty: Number(demandGroupDraft.target_qty),
      mandatory_flag: demandGroupDraft.mandatory_flag,
      sort_order: Number(demandGroupDraft.sort_order),
      remark: demandGroupDraft.remark.trim() || null,
    };
    const result = demandGroupDraft.id
      ? await updateDemandGroup(tenantScopeId.value, accessToken.value, demandGroupDraft.id, {
          function_type_id: payload.function_type_id,
          qualification_type_id: payload.qualification_type_id,
          min_qty: payload.min_qty,
          target_qty: payload.target_qty,
          mandatory_flag: payload.mandatory_flag,
          sort_order: payload.sort_order,
          remark: payload.remark,
          version_no: demandGroupDraft.version_no,
        })
      : await createDemandGroup(tenantScopeId.value, accessToken.value, payload);
    selectedDemandGroupId.value = result.id;
    await refreshAll();
    closeDemandGroupDialog();
  } catch (error) {
    handleApiError(error);
  } finally {
    savingDemandGroup.value = false;
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
  loading.value = true;
  try {
    const result = await assignStaffing(tenantScopeId.value, accessToken.value, buildAssignPayload());
    if (result.outcome_code === "blocked") {
      setFeedback("error", tp("staffingActionsTitle"), tp("assignmentBlocked"));
      void refreshVisibleShiftValidations();
      return;
    }
    if (result.assignment) {
      invalidateAssignmentInspection(result.assignment.id);
      upsertShiftAssignment(result.assignment);
    }
    selectedAssignmentId.value = result.assignment_id ?? "";
    selectedAssignmentDetails.value = null;
    assignmentValidations.value = null;
    assignmentOverrides.value = [];
    resetStaffingDraft();
    void refreshVisibleAssignmentDiagnostics();
    void refreshVisibleShiftValidations();
  } catch (error) {
    handleApiError(error);
  } finally {
    loading.value = false;
  }
}

async function submitUnassign() {
  if (!tenantScopeId.value || !accessToken.value || !selectedAssignment.value) {
    return;
  }
  clearFeedback();
  loading.value = true;
  try {
    const assignmentId = selectedAssignment.value.id;
    const shiftId = selectedAssignment.value.shift_id;
    await unassignStaffing(tenantScopeId.value, accessToken.value, {
      tenant_id: tenantScopeId.value,
      assignment_id: assignmentId,
      version_no: selectedAssignment.value.version_no,
      remarks: staffingDraft.remarks.trim() || null,
    });
    invalidateAssignmentInspection(assignmentId);
    removeShiftAssignment(shiftId, assignmentId);
    selectedAssignmentId.value = "";
    selectedAssignmentDetails.value = null;
    assignmentValidations.value = null;
    assignmentOverrides.value = [];
    assignmentDialogOpen.value = false;
    void refreshVisibleShiftValidations();
  } catch (error) {
    handleApiError(error);
  } finally {
    loading.value = false;
  }
}

async function submitSubstitute() {
  if (!tenantScopeId.value || !accessToken.value || !selectedAssignment.value || !canSubmitSubstitute.value) {
    return;
  }
  clearFeedback();
  loading.value = true;
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
      void refreshVisibleShiftValidations();
      return;
    }
    if (selectedAssignment.value) {
      invalidateAssignmentInspection(selectedAssignment.value.id);
      removeShiftAssignment(selectedAssignment.value.shift_id, selectedAssignment.value.id);
    }
    if (result.assignment) {
      invalidateAssignmentInspection(result.assignment.id);
      upsertShiftAssignment(result.assignment);
    }
    selectedAssignmentId.value = result.assignment_id ?? "";
    selectedAssignmentDetails.value = null;
    assignmentValidations.value = null;
    assignmentOverrides.value = [];
    resetStaffingDraft();
    void refreshVisibleAssignmentDiagnostics();
    void refreshVisibleShiftValidations();
  } catch (error) {
    handleApiError(error);
  } finally {
    loading.value = false;
  }
}

async function submitTeam() {
  if (!tenantScopeId.value || !accessToken.value || !canSubmitTeam.value) {
    return;
  }
  clearFeedback();
  savingTeam.value = true;
  try {
    const payload: TeamCreate = {
      tenant_id: tenantScopeId.value,
      name: teamDraft.name.trim(),
      role_label: teamDraft.role_label.trim() || null,
      notes: teamDraft.notes.trim() || null,
      ...teamScopePayload(),
    };
    const team = teamDraft.id
      ? await updateTeam(tenantScopeId.value, accessToken.value, teamDraft.id, {
          ...teamScopePayload(),
          name: payload.name,
          role_label: payload.role_label,
          notes: payload.notes,
          version_no: teamDraft.version_no,
        })
      : await createTeam(tenantScopeId.value, accessToken.value, payload);
    if (!teamDraft.id && teamDraft.lead_member_ref) {
      const actorPayload = selectedActorPayload(teamDraft.lead_actor_kind, teamDraft.lead_member_ref);
      await createTeamMember(tenantScopeId.value, accessToken.value, {
        tenant_id: tenantScopeId.value,
        team_id: team.id,
        ...actorPayload,
        role_label: tp("teamLeadDefaultRole"),
        is_team_lead: true,
        valid_from: toIsoDateTime(normalizeDateTimeLocal(selectedShift.value?.starts_at) || filters.date_from) || new Date().toISOString(),
        valid_to: null,
        notes: null,
      });
    }
    selectedTeamId.value = team.id;
    staffingDraft.team_id = team.id;
    await refreshSupportingData();
    closeTeamDialog();
  } catch (error) {
    handleApiError(error);
  } finally {
    savingTeam.value = false;
  }
}

async function submitTeamMember() {
  if (!tenantScopeId.value || !accessToken.value || !canSubmitTeamMember.value) {
    return;
  }
  clearFeedback();
  savingTeamMember.value = true;
  try {
    const actorPayload = selectedActorPayload(teamMemberDraft.actor_kind, teamMemberDraft.member_ref);
    const payload: TeamMemberCreate = {
      tenant_id: tenantScopeId.value,
      team_id: teamMemberDraft.team_id,
      ...actorPayload,
      role_label: teamMemberDraft.role_label.trim() || null,
      is_team_lead: teamMemberDraft.is_team_lead,
      valid_from: toIsoDateTime(teamMemberDraft.valid_from) || new Date().toISOString(),
      valid_to: toIsoDateTime(teamMemberDraft.valid_to),
      notes: teamMemberDraft.notes.trim() || null,
    };
    if (teamMemberDraft.id) {
      await updateTeamMember(tenantScopeId.value, accessToken.value, teamMemberDraft.id, {
        ...actorPayload,
        role_label: payload.role_label,
        is_team_lead: payload.is_team_lead,
        valid_from: payload.valid_from,
        valid_to: payload.valid_to,
        notes: payload.notes,
        version_no: teamMemberDraft.version_no,
      });
    } else {
      await createTeamMember(tenantScopeId.value, accessToken.value, payload);
    }
    selectedTeamId.value = teamMemberDraft.team_id;
    await refreshSupportingData();
    closeTeamMemberDialog();
  } catch (error) {
    handleApiError(error);
  } finally {
    savingTeamMember.value = false;
  }
}

async function loadDispatchPreview() {
  if (!tenantScopeId.value || !accessToken.value || !selectedShiftId.value) {
    return;
  }
  loading.value = true;
  try {
    dispatchPreview.value = await previewShiftDispatchMessage(tenantScopeId.value, accessToken.value, selectedShiftId.value, {
      tenant_id: tenantScopeId.value,
      shift_id: selectedShiftId.value,
      audience_codes: dispatchAudienceCodes(),
    });
  } finally {
    loading.value = false;
  }
}

async function queueDispatch() {
  if (!tenantScopeId.value || !accessToken.value || !selectedShiftId.value) {
    return;
  }
  loading.value = true;
  try {
    await queueShiftDispatchMessage(tenantScopeId.value, accessToken.value, selectedShiftId.value, {
      tenant_id: tenantScopeId.value,
      shift_id: selectedShiftId.value,
      audience_codes: dispatchAudienceCodes(),
    });
    setFeedback("good", tp("dispatchTitle"), tp("dispatchQueuedSuccess"));
  } finally {
    loading.value = false;
  }
}

async function generateOutput(audienceCode: "customer" | "internal") {
  if (!tenantScopeId.value || !accessToken.value || !selectedShiftId.value) {
    return;
  }
  loading.value = true;
  try {
    await generateShiftOutput(tenantScopeId.value, accessToken.value, selectedShiftId.value, {
      tenant_id: tenantScopeId.value,
      variant_code: "deployment_plan",
      audience_code: audienceCode,
    });
    shiftOutputs.value = await listShiftOutputs(tenantScopeId.value, accessToken.value, selectedShiftId.value);
  } finally {
    loading.value = false;
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
  if (!isRouteCachePaneActive.value) {
    return;
  }
  if (document.visibilityState === "visible") {
    void recoverSessionAndRefresh();
  }
}

function handleWindowFocus() {
  if (!isRouteCachePaneActive.value) {
    return;
  }
  void recoverSessionAndRefresh();
}

watch(selectedShiftId, async () => {
  activeShiftDetailTab.value = "demand_staffing";
  if (demandGroupDialogOpen.value) {
    closeDemandGroupDialog();
  }
  if (!loading.value && !routeHydrationInFlight.value) {
    try {
      await loadSelectedShiftDetails();
    } catch (error) {
      handleApiError(error);
    }
  }
});

watch(selectedAssignmentId, async () => {
  if (!loading.value && !assignmentEditorLoading.value && !assignmentEditorSaving.value) {
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
    if (!selectedAssignmentId.value && !assignmentCreateDialogActive.value) {
      resetAssignmentDraft();
    }
    if (!shift?.demand_groups?.length) {
      resetDemandGroupDraft();
    }
  },
  { immediate: true },
);

watch(
  selectedDemandGroupDetails,
  (group) => {
    if (group && demandGroupDraft.id === group.id) {
      startEditDemandGroup();
    }
  },
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
  availableTeams,
  (teams) => {
    if (!teams.some((team) => team.id === selectedTeamId.value)) {
      selectedTeamId.value = teams[0]?.id ?? "";
    }
  },
  { immediate: true },
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
      functionTypeOptions.value = [];
      qualificationTypeOptions.value = [];
      return;
    }
    void loadDemandGroupCatalogOptions();
    schedulePlanningRecordLookup();
  },
);

watch(
  () => [tenantScopeId.value, accessToken.value, relevantPlanningRecordId.value, selectedShift.value?.planning_record_name || selectedPlanningRecordOption.value?.name || ""],
  ([nextTenantScopeId, nextAccessToken, nextPlanningRecordId]) => {
    if (!nextTenantScopeId || !nextAccessToken || !nextPlanningRecordId) {
      resolvedPlanningRecord.value = null;
      return;
    }
    void ensurePlanningRecordResolved();
  },
  { immediate: true },
);

onMounted(async () => {
  routeHydrationInFlight.value = true;
  applyRouteQueryContext();
  authStore.syncFromPrimarySession();
  const sessionReady = await ensureStaffingSessionReady();
  if (!sessionReady || !tenantScopeId.value || !accessToken.value || !actionState.value.canReadCoverage) {
    routeHydrationInFlight.value = false;
    return;
  }
  document.addEventListener("visibilitychange", handleVisibilityChange);
  window.addEventListener("focus", handleWindowFocus);
  await loadDemandGroupCatalogOptions();
  await refreshAll();
});

watch(
  () => route.fullPath,
  () => {
    routeHydrationInFlight.value = true;
    const changed = applyRouteQueryContext();
    if (!changed || !tenantScopeId.value || !accessToken.value || !actionState.value.canReadCoverage) {
      routeHydrationInFlight.value = false;
      return;
    }
    void refreshAll();
  },
);

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
.planning-staffing-workspace,
.planning-staffing-main-grid,
.planning-staffing-filter-grid,
.planning-staffing-summary,
.planning-staffing-detail,
.planning-staffing-metrics,
.planning-staffing-issues,
.planning-staffing-demand-groups,
.planning-staffing-demand-group-editor,
.planning-staffing-support-grid {
  display: grid;
  gap: 1rem;
}

.planning-staffing-workspace {
  gap: var(--sp-page-gap, 1.25rem);
}

.planning-staffing-main-grid {
  align-items: start;
  gap: var(--sp-page-gap, 1.25rem);
  grid-template-columns: minmax(320px, 420px) minmax(360px, 1fr);
}

.planning-staffing-meta,
.planning-staffing-metrics,
.planning-staffing-summary,
.planning-staffing-support-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  justify-content: flex-start;
  align-items: center;
}

.planning-staffing-panel__header {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
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
.planning-staffing-loading-state,
.planning-staffing-feedback {
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 18px;
  padding: 1rem;
  background: #fff;
}

.planning-staffing-panel {
  align-content: start;
  gap: 1.25rem;
  min-width: 0;
  padding: 1.25rem;
  box-shadow: 0 20px 44px rgba(15, 23, 42, 0.05);
}

.planning-staffing-filter-panel {
  width: 100%;
}

.planning-staffing-coverage-panel {
  width: 100%;
  max-width: 420px;
}

.planning-staffing-detail {
  min-width: 0;
}

.planning-staffing-panel__header {
  min-width: 0;
}

.planning-staffing-panel__lead {
  color: rgba(15, 23, 42, 0.72);
  font-size: 0.95rem;
  line-height: 1.45;
  margin: 0.35rem 0 0;
}

.planning-staffing-panel__lead--context {
  font-weight: 600;
}

.planning-staffing-panel__header--filters {
  display: grid;
  gap: 1rem;
  grid-template-columns: minmax(0, 1fr);
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
  align-items: center;
}

.planning-staffing-filter-grid {
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}

.planning-staffing-panel__header--filters + .planning-staffing-filter-grid {
  margin-top: 0.2rem;
}

.planning-staffing-filter-grid + .planning-staffing-summary {
  margin-top: 0.35rem;
}

.planning-staffing-filter-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  justify-content: flex-start;
  align-items: center;
}

.planning-staffing-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem;
}

.planning-staffing-tab {
  appearance: none;
  border: 1px solid rgba(40, 170, 170, 0.2);
  border-radius: 999px;
  background: rgba(40, 170, 170, 0.08);
  color: rgba(15, 23, 42, 0.82);
  cursor: pointer;
  font: inherit;
  font-weight: 700;
  line-height: 1.2;
  padding: 0.65rem 1rem;
  transition: background-color 120ms ease, border-color 120ms ease, color 120ms ease;
}

.planning-staffing-tab.active {
  background: rgba(40, 170, 170, 0.18);
  border-color: rgba(40, 170, 170, 0.45);
  color: rgb(17, 94, 89);
}

.planning-staffing-tab-panel {
  display: grid;
  gap: 1rem;
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

.planning-staffing-field-label {
  align-items: baseline;
  display: flex;
  gap: 0.5rem;
  justify-content: space-between;
  min-width: 0;
}

.planning-staffing-field-status {
  color: rgba(15, 23, 42, 0.52);
  display: inline-block;
  flex: 0 1 auto;
  font-size: 0.72rem;
  font-weight: 600;
  line-height: 1.25;
  max-width: 14rem;
  min-width: 0;
  overflow: hidden;
  text-align: right;
  text-overflow: ellipsis;
  text-transform: none;
  white-space: nowrap;
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

.planning-staffing-filter-grid select {
  background-image:
    linear-gradient(45deg, transparent 50%, rgba(15, 23, 42, 0.55) 50%),
    linear-gradient(135deg, rgba(15, 23, 42, 0.55) 50%, transparent 50%);
  background-position:
    calc(100% - 1.15rem) calc(50% - 0.16rem),
    calc(100% - 0.8rem) calc(50% - 0.16rem);
  background-repeat: no-repeat;
  background-size: 0.42rem 0.42rem, 0.42rem 0.42rem;
  cursor: pointer;
  padding-right: 2.4rem;
}

.planning-staffing-filter-grid select option[value=""] {
  color: rgba(15, 23, 42, 0.6);
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
  display: flex;
  min-height: 2.85rem;
}

.planning-staffing-filter-grid textarea,
.planning-staffing-subpanel textarea {
  min-height: 6rem;
  resize: vertical;
}

.planning-staffing-fieldset {
  border: 0;
  margin: 0;
  min-width: 0;
  padding: 0;
}

.planning-staffing-demand-groups {
  align-content: start;
  margin-block: 0.35rem 0.65rem;
}

.planning-staffing-confirm-row {
  display: grid;
  gap: 0.45rem;
}

.planning-staffing-checkbox-row {
  align-items: center;
  cursor: pointer;
  display: inline-flex;
  gap: 0.65rem;
  min-height: 2.85rem;
  min-width: 0;
  width: fit-content;
}

.planning-staffing-checkbox-row input[type="checkbox"] {
  appearance: auto;
  background: transparent;
  border: 0;
  border-radius: 0;
  box-shadow: none;
  flex: 0 0 1.1rem;
  height: 1.1rem;
  margin: 0;
  min-height: 1.1rem;
  min-width: 1.1rem;
  padding: 0;
  width: 1.1rem;
}

.planning-staffing-checkbox-row > span {
  color: rgb(15, 23, 42);
  font-size: 0.95rem;
  font-weight: 600;
  line-height: 1.35;
}

.planning-staffing-filter-grid input[type="checkbox"],
.planning-staffing-subpanel input[type="checkbox"] {
  accent-color: rgb(40, 170, 170);
  appearance: auto;
  min-height: auto;
  padding: 0;
  min-width: 1.1rem;
  vertical-align: middle;
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
  align-items: flex-start;
  text-align: left;
  transition: border-color 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease;
}

.planning-staffing-list {
  display: grid;
  gap: 0.85rem;
}

.planning-staffing-list--scroll {
  align-content: start;
  max-height: clamp(24rem, 58vh, 44rem);
  overflow-y: auto;
  padding-right: 0.25rem;
}

.planning-staffing-coverage-panel {
  display: flex;
  flex-direction: column;
}

.planning-staffing-row {
  padding-top: 1.15rem;
  padding-bottom: 1.15rem;
}

.planning-staffing-row--assignment {
  align-items: stretch;
  border-left: 4px solid transparent;
  border-radius: 18px;
  padding: 1rem 1rem 1rem 1.1rem;
}

.planning-staffing-row--assignment .planning-staffing-assignment-row__body {
  display: grid;
  gap: 0.24rem;
  min-width: 0;
}

.planning-staffing-row--assignment .planning-staffing-assignment-row__title {
  color: rgb(15, 23, 42);
  font-size: 0.97rem;
  font-weight: 700;
  line-height: 1.35;
  min-width: 0;
  overflow-wrap: anywhere;
}

.planning-staffing-row--assignment .planning-staffing-assignment-row__detail {
  color: rgba(15, 23, 42, 0.78);
  font-size: 0.88rem;
  line-height: 1.35;
  min-width: 0;
  overflow-wrap: anywhere;
}

.planning-staffing-row--assignment .planning-staffing-assignment-row__meta {
  color: rgba(15, 23, 42, 0.56);
  font-size: 0.8rem;
  font-weight: 600;
  letter-spacing: 0.01em;
  line-height: 1.35;
  min-width: 0;
  overflow-wrap: anywhere;
  text-transform: uppercase;
}

.planning-staffing-row--assignment .planning-staffing-assignment-row__marker {
  align-self: stretch;
  background: linear-gradient(180deg, rgba(40, 170, 170, 0.16), rgba(40, 170, 170, 0.04));
  border-radius: 999px;
  flex: 0 0 0.38rem;
  min-height: 100%;
}

.planning-staffing-row.selected,
.planning-staffing-demand-group.selected {
  border-color: rgb(40, 170, 170);
  box-shadow: 0 0 0 1px rgba(40, 170, 170, 0.2);
}

.planning-staffing-row--assignment.selected {
  background: linear-gradient(135deg, rgba(40, 170, 170, 0.12), rgba(255, 255, 255, 0.94));
  border-left-color: rgb(40, 170, 170);
  box-shadow:
    0 0 0 1px rgba(40, 170, 170, 0.24),
    0 10px 24px rgba(15, 23, 42, 0.08);
}

.planning-staffing-row--assignment.selected .planning-staffing-assignment-row__marker {
  background: linear-gradient(180deg, rgb(40, 170, 170), rgba(40, 170, 170, 0.42));
}

.planning-staffing-row:hover,
.planning-staffing-demand-group:hover {
  border-color: rgba(40, 170, 170, 0.45);
  transform: translateY(-1px);
}

.planning-staffing-row--assignment:hover {
  box-shadow: 0 10px 22px rgba(15, 23, 42, 0.08);
}

.planning-staffing-row--assignment:focus-visible {
  outline: none;
  box-shadow:
    0 0 0 3px rgba(40, 170, 170, 0.2),
    0 10px 22px rgba(15, 23, 42, 0.08);
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

.planning-staffing-meta__pill {
  flex: 0 1 auto;
  max-width: 100%;
}

.planning-staffing-summary__card {
  display: grid;
  flex: 1 1 150px;
  min-width: 0;
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
  .planning-staffing-main-grid {
    grid-template-columns: 1fr;
  }

  .planning-staffing-coverage-panel {
    max-width: none;
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
