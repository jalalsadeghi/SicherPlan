<template>
  <section class="planning-shifts-page">
    <section v-if="!props.embedded" class="module-card planning-shifts-hero">
      <div>
        <p class="eyebrow">{{ tp("eyebrow") }}</p>
        <h2>{{ tp("title") }}</h2>
        <p class="planning-shifts-lead">{{ tp("lead") }}</p>
      </div>
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
          <div class="cta-row">
            <button class="cta-button cta-secondary" type="button" @click="refreshTemplates">{{ tp("actionsRefresh") }}</button>
            <button
              class="cta-button cta-secondary"
              data-testid="planning-shifts-create-template"
              type="button"
              :disabled="!actionState.canCreateTemplate"
              @click="startCreateTemplate"
            >
              {{ tp("actionsCreateTemplate") }}
            </button>
          </div>
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
          <label class="field-stack">
            <span>{{ tp("filtersPlanningRecord") }}</span>
            <select v-model="planFilters.planning_record_id">
              <option value="">{{ tp("planningRecordPlaceholder") }}</option>
              <option v-for="record in planningRecordOptions" :key="record.id" :value="record.id">
                {{ record.label }}
              </option>
            </select>
          </label>
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
            <label class="field-stack">
              <span>{{ tp("fieldsPlanningRecordId") }}</span>
              <select v-model="shiftPlanDraft.planning_record_id" required>
                <option value="" disabled>{{ tp("planningRecordPlaceholder") }}</option>
                <option v-for="record in planningRecordOptions" :key="record.id" :value="record.id">
                  {{ record.label }}
                </option>
              </select>
            </label>
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
        <div
          class="planning-shifts-series-context"
          :class="{ 'planning-shifts-series-context--warning': !selectedShiftPlanRow }"
          data-testid="planning-shifts-series-context"
        >
          <label class="field-stack field-stack--wide">
            <span>{{ tp("fieldsShiftPlan") }}</span>
            <select
              v-model="selectedShiftPlanId"
              data-testid="planning-shifts-series-plan-select"
              :disabled="!shiftPlans.length"
              @change="changeSeriesShiftPlan"
            >
              <option value="">{{ shiftPlans.length ? tp("seriesSelectPlanFirst") : tp("seriesNoPlansAvailable") }}</option>
              <option v-for="plan in shiftPlans" :key="plan.id" :value="plan.id">
                {{ plan.name }} · {{ plan.planning_from }} - {{ plan.planning_to }}
              </option>
            </select>
          </label>
          <div v-if="selectedShiftPlanRow">
            <strong>{{ tp("seriesSelectedPlanLabel") }}</strong>
            <p>{{ selectedShiftPlanRow.name }}</p>
            <p class="field-help">
              {{ tp("seriesSelectedPlanWindow") }}: {{ selectedShiftPlanRow.planning_from }} - {{ selectedShiftPlanRow.planning_to }}
              · {{ tp("seriesSelectedPlanWorkforce") }}: {{ workforceLabel(selectedShiftPlanRow.workforce_scope_code) }}
            </p>
          </div>
          <p v-else class="field-help">{{ shiftPlans.length ? tp("seriesSelectPlanFirst") : tp("seriesNoPlansAvailable") }}</p>
          <button class="cta-button cta-secondary" type="button" @click="activeWorkspaceTab = 'plans'">{{ tp("actionsOpenPlansTab") }}</button>
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
            <label class="field-stack">
              <span>{{ tp("fieldsShiftTemplateId") }}</span>
              <select v-model="seriesDraft.shift_template_id" required>
                <option value="" disabled>{{ tp("shiftTemplatePlaceholder") }}</option>
                <option v-for="template in shiftTemplateOptions" :key="template.id" :value="template.id">
                  {{ template.label }}
                </option>
              </select>
            </label>
            <label class="field-stack"><span>{{ tp("fieldsLabel") }}</span><input v-model="seriesDraft.label" required /></label>
            <label class="field-stack">
              <span>{{ tp("fieldsRecurrence") }}</span>
              <select v-model="seriesDraft.recurrence_code">
                <option value="daily">{{ tp("recurrenceDaily") }}</option>
                <option value="weekly">{{ tp("recurrenceWeekly") }}</option>
              </select>
            </label>
            <label class="field-stack"><span>{{ tp("fieldsInterval") }}</span><input v-model.number="seriesDraft.interval_count" type="number" min="1" /></label>
            <div v-if="seriesUsesWeeklyRecurrence" class="field-stack field-stack--wide">
              <span>{{ tp("fieldsWeekdayMask") }}</span>
              <div class="planning-shifts-weekday-picker" data-testid="planning-shifts-weekday-picker">
                <button
                  v-for="day in weekdayOptions"
                  :key="day.index"
                  type="button"
                  class="planning-shifts-weekday-chip"
                  :class="{ active: isWeekdaySelected(day.index) }"
                  @click="toggleWeekday(day.index)"
                >
                  {{ day.label }}
                </button>
              </div>
            </div>
            <label class="field-stack">
              <span>{{ tp("fieldsTimezone") }}</span>
              <input v-model="seriesDraft.timezone" list="planning-shifts-timezones" required />
            </label>
            <label class="field-stack"><span>{{ tp("fieldsPlanningFrom") }}</span><input v-model="seriesDraft.date_from" type="date" required /></label>
            <label class="field-stack"><span>{{ tp("fieldsPlanningTo") }}</span><input v-model="seriesDraft.date_to" type="date" required /></label>
            <label class="field-stack"><span>{{ tp("fieldsReleaseState") }}</span>
              <select v-model="seriesDraft.release_state">
                <option value="draft">{{ tp("statusDraft") }}</option>
                <option value="release_ready">{{ tp("statusReleaseReady") }}</option>
                <option value="released">{{ tp("statusReleased") }}</option>
              </select>
            </label>
            <label class="field-stack">
              <span>{{ tp("fieldsShiftType") }}</span>
              <select v-model="seriesDraft.shift_type_code" :disabled="loadingShiftTypeOptions || !seriesShiftTypeOptions.length">
                <option value="">{{ tp("shiftTypeOptionalPlaceholder") }}</option>
                <option v-for="option in seriesShiftTypeOptions" :key="option.code" :value="option.code">
                  {{ option.label }}
                </option>
              </select>
              <span v-if="shiftTypeHelpLabel" class="field-help">{{ shiftTypeHelpLabel }}</span>
            </label>
            <label class="field-stack"><span>{{ tp("fieldsMeetingPoint") }}</span><input v-model="seriesDraft.meeting_point" /></label>
            <label class="field-stack"><span>{{ tp("fieldsLocationText") }}</span><input v-model="seriesDraft.location_text" /></label>
            <label class="field-stack"><span>{{ tp("fieldsBreakMinutes") }}</span><input v-model.number="seriesDraft.default_break_minutes" type="number" min="0" /></label>
            <label class="field-stack field-stack--wide"><span>{{ tp("fieldsNotes") }}</span><textarea v-model="seriesDraft.notes" rows="2" /></label>
            <label class="planning-orders-checkbox"><input v-model="seriesDraft.customer_visible_flag" type="checkbox" /><span>{{ tp("fieldsVisibilityCustomer") }}</span></label>
            <label class="planning-orders-checkbox"><input v-model="seriesDraft.subcontractor_visible_flag" type="checkbox" /><span>{{ tp("fieldsVisibilitySubcontractor") }}</span></label>
            <label class="planning-orders-checkbox"><input v-model="seriesDraft.stealth_mode_flag" type="checkbox" /><span>{{ tp("fieldsVisibilityStealth") }}</span></label>
          </div>
          <div class="cta-row">
            <button class="cta-button" type="submit" :disabled="!actionState.canCreateSeries">{{ tp("actionsSave") }}</button>
            <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canGenerateSeries" @click="generateSelectedSeries">{{ tp("actionsGenerate") }}</button>
          </div>
          <p v-if="!selectedShiftPlanRow" class="field-help">{{ shiftPlans.length ? tp("seriesSelectPlanFirst") : tp("seriesNoPlansAvailable") }}</p>
        </form>
        <form v-if="selectedSeriesId" class="planning-orders-form" @submit.prevent="submitException">
          <div class="planning-orders-panel__header">
            <div>
              <p class="eyebrow">{{ tp("exceptionsTitle") }}</p>
              <h4>{{ tp("exceptionsTitle") }}</h4>
            </div>
            <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canManageExceptions" @click="startCreateException">{{ tp("actionsNewException") }}</button>
          </div>
          <div v-if="seriesExceptions.length" class="planning-orders-list">
            <button
              v-for="exception in seriesExceptions"
              :key="exception.id"
              type="button"
              class="planning-orders-row"
              :class="{ selected: exception.id === selectedExceptionId }"
              @click="selectException(exception.id)"
            >
              <div>
                <strong>{{ exception.exception_date }}</strong>
                <span>{{ exception.action_code === 'override' ? tp('exceptionOverride') : tp('exceptionSkip') }}</span>
              </div>
            </button>
          </div>
          <p v-else class="planning-orders-list-empty">{{ tp("exceptionsEmpty") }}</p>
          <div class="planning-orders-form-grid">
            <label class="field-stack"><span>{{ tp("fieldsOccurrenceDate") }}</span><input v-model="exceptionDraft.exception_date" type="date" required /></label>
            <label class="field-stack">
              <span>{{ tp("fieldsActionCode") }}</span>
              <select v-model="exceptionDraft.action_code">
                <option value="skip">{{ tp("exceptionSkip") }}</option>
                <option value="override">{{ tp("exceptionOverride") }}</option>
              </select>
            </label>
            <label v-if="exceptionRequiresOverrideTimes" class="field-stack"><span>{{ tp("fieldsOverrideStart") }}</span><input v-model="exceptionDraft.override_local_start_time" type="time" required /></label>
            <label v-if="exceptionRequiresOverrideTimes" class="field-stack"><span>{{ tp("fieldsOverrideEnd") }}</span><input v-model="exceptionDraft.override_local_end_time" type="time" required /></label>
            <label class="field-stack field-stack--wide"><span>{{ tp("fieldsNotes") }}</span><textarea v-model="exceptionDraft.notes" rows="2" /></label>
          </div>
          <div class="cta-row">
            <button class="cta-button cta-secondary" type="submit" :disabled="!actionState.canManageExceptions">
              {{ selectedExceptionId ? tp("actionsUpdateException") : tp("actionsCreateException") }}
            </button>
            <button class="cta-button cta-secondary" type="button" @click="resetExceptionDraft">{{ tp("actionsReset") }}</button>
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
        <div
          class="planning-shifts-series-context"
          :class="{ 'planning-shifts-series-context--warning': !selectedShiftPlanRow }"
          data-testid="planning-shifts-shifts-context"
        >
          <label class="field-stack field-stack--wide">
            <span>{{ tp("fieldsShiftPlan") }}</span>
            <select
              v-model="selectedShiftPlanId"
              data-testid="planning-shifts-shifts-plan-select"
              :disabled="!shiftPlans.length"
              @change="changeShiftTabPlan"
            >
              <option value="">{{ shiftPlans.length ? tp("seriesSelectPlanFirst") : tp("seriesNoPlansAvailable") }}</option>
              <option v-for="plan in shiftPlans" :key="plan.id" :value="plan.id">
                {{ plan.name }} · {{ plan.planning_from }} - {{ plan.planning_to }}
              </option>
            </select>
          </label>
          <div v-if="selectedShiftPlanRow">
            <strong>{{ tp("seriesSelectedPlanLabel") }}</strong>
            <p>{{ selectedShiftPlanRow.name }}</p>
            <p class="field-help">
              {{ tp("seriesSelectedPlanWindow") }}: {{ selectedShiftPlanRow.planning_from }} - {{ selectedShiftPlanRow.planning_to }}
              · {{ tp("seriesSelectedPlanWorkforce") }}: {{ workforceLabel(selectedShiftPlanRow.workforce_scope_code) }}
            </p>
          </div>
          <p v-else class="field-help">{{ shiftPlans.length ? tp("seriesSelectPlanFirst") : tp("seriesNoPlansAvailable") }}</p>
          <button class="cta-button cta-secondary" type="button" @click="activeWorkspaceTab = 'plans'">{{ tp("actionsOpenPlansTab") }}</button>
        </div>
        <div class="planning-orders-form-grid">
          <label class="field-stack"><span>{{ tp("filtersDateFrom") }}</span><input v-model="shiftFilters.date_from" type="date" /></label>
          <label class="field-stack"><span>{{ tp("filtersDateTo") }}</span><input v-model="shiftFilters.date_to" type="date" /></label>
          <label class="field-stack">
            <span>{{ tp("filtersVisibility") }}</span>
            <select v-model="shiftFilters.visibility_state">
              <option value="">{{ tp("visibilityPlaceholder") }}</option>
              <option v-for="option in visibilityStateOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </label>
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
            <label class="field-stack">
              <span>{{ tp("fieldsStartsAtLocal") }}</span>
              <input v-model="shiftDraft.starts_at" type="datetime-local" required />
              <span class="field-help">{{ tp("fieldsLocalDateTimeHelp") }}</span>
            </label>
            <label class="field-stack">
              <span>{{ tp("fieldsEndsAtLocal") }}</span>
              <input v-model="shiftDraft.ends_at" type="datetime-local" required />
              <span class="field-help">{{ tp("fieldsLocalDateTimeHelp") }}</span>
            </label>
            <label class="field-stack"><span>{{ tp("fieldsBreakMinutes") }}</span><input v-model.number="shiftDraft.break_minutes" type="number" min="0" /></label>
            <label class="field-stack">
              <span>{{ tp("fieldsShiftType") }}</span>
              <select v-model="shiftDraft.shift_type_code" required :disabled="loadingShiftTypeOptions || !shiftShiftTypeOptions.length">
                <option value="" disabled>{{ shiftTypePlaceholderLabel }}</option>
                <option v-for="option in shiftShiftTypeOptions" :key="option.code" :value="option.code">
                  {{ option.label }}
                </option>
              </select>
              <span v-if="shiftTypeHelpLabel" class="field-help">{{ shiftTypeHelpLabel }}</span>
            </label>
            <label class="field-stack"><span>{{ tp("fieldsMeetingPoint") }}</span><input v-model="shiftDraft.meeting_point" /></label>
            <label class="field-stack"><span>{{ tp("fieldsLocationText") }}</span><input v-model="shiftDraft.location_text" /></label>
            <label class="field-stack"><span>{{ tp("fieldsReleaseState") }}</span>
              <select v-model="shiftDraft.release_state" :disabled="Boolean(selectedShiftId)">
                <option value="draft">{{ tp("statusDraft") }}</option>
                <option value="release_ready">{{ tp("statusReleaseReady") }}</option>
                <option value="released">{{ tp("statusReleased") }}</option>
              </select>
            </label>
            <label class="field-stack field-stack--wide"><span>{{ tp("fieldsNotes") }}</span><textarea v-model="shiftDraft.notes" rows="2" /></label>
            <label class="planning-orders-checkbox"><input v-model="shiftDraft.customer_visible_flag" type="checkbox" :disabled="Boolean(selectedShiftId)" /><span>{{ tp("fieldsVisibilityCustomer") }}</span></label>
            <label class="planning-orders-checkbox"><input v-model="shiftDraft.subcontractor_visible_flag" type="checkbox" :disabled="Boolean(selectedShiftId)" /><span>{{ tp("fieldsVisibilitySubcontractor") }}</span></label>
            <label class="planning-orders-checkbox"><input v-model="shiftDraft.stealth_mode_flag" type="checkbox" /><span>{{ tp("fieldsVisibilityStealth") }}</span></label>
          </div>
          <div class="cta-row">
            <button class="cta-button" type="submit" :disabled="!actionState.canCreateShift">{{ tp("actionsSave") }}</button>
            <button class="cta-button cta-secondary" type="button" @click="resetShiftDraft">{{ tp("actionsReset") }}</button>
          </div>
        </form>
        <section v-if="selectedShiftId && selectedShiftDiagnostics" class="planning-orders-form planning-shifts-release-panel" data-testid="planning-shifts-release-panel">
          <div class="planning-orders-panel__header">
            <div>
              <p class="eyebrow">{{ tp("releaseSectionTitle") }}</p>
              <h4>{{ tp("releaseSectionTitle") }}</h4>
            </div>
            <button class="cta-button cta-secondary" type="button" @click="refreshSelectedShift">{{ tp("actionsRefresh") }}</button>
          </div>
          <div class="planning-shifts-release-grid">
            <div class="planning-shifts-release-stat">
              <strong>{{ tp("fieldsReleaseState") }}</strong>
              <span>{{ releaseStateLabel(selectedShiftDiagnostics.release_state) }}</span>
            </div>
            <div class="planning-shifts-release-stat">
              <strong>{{ tp("releaseBlockingCount") }}</strong>
              <span>{{ selectedShiftDiagnostics.blocking_count }}</span>
            </div>
            <div class="planning-shifts-release-stat">
              <strong>{{ tp("releaseWarningCount") }}</strong>
              <span>{{ selectedShiftDiagnostics.warning_count }}</span>
            </div>
          </div>
          <div class="planning-shifts-release-actions">
            <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canEditShift" @click="changeShiftReleaseState('draft')">{{ tp("actionsSetDraft") }}</button>
            <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canEditShift" @click="changeShiftReleaseState('release_ready')">{{ tp("actionsSetReleaseReady") }}</button>
            <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canEditShift" @click="changeShiftReleaseState('released')">{{ tp("actionsSetReleased") }}</button>
          </div>
          <div class="planning-shifts-release-actions">
            <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canEditShift" @click="updateSelectedShiftVisibility(true, selectedShiftDiagnostics.subcontractor_visible_flag)">{{ tp("actionsShowCustomer") }}</button>
            <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canEditShift" @click="updateSelectedShiftVisibility(selectedShiftDiagnostics.customer_visible_flag, true)">{{ tp("actionsShowSubcontractor") }}</button>
            <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canEditShift" @click="updateSelectedShiftVisibility(false, false)">{{ tp("actionsHideExternal") }}</button>
          </div>
          <p class="field-help">{{ tp("releaseVisibilityHelp") }}</p>
          <div v-if="selectedShiftDiagnostics.issues.length" class="planning-shifts-release-issues">
            <strong>{{ tp("releaseDiagnosticsTitle") }}</strong>
            <ul>
              <li v-for="issue in selectedShiftDiagnostics.issues" :key="`${issue.scope}-${issue.code}-${issue.message}`">
                {{ issue.message || issue.code }}
              </li>
            </ul>
          </div>
          <p v-else class="field-help">{{ tp("releaseDiagnosticsEmpty") }}</p>
        </section>
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
          <label class="field-stack">
            <span>{{ tp("filtersReleaseState") }}</span>
            <select v-model="boardFilters.release_state">
              <option value="">{{ tp("releaseStatePlaceholder") }}</option>
              <option v-for="option in releaseStateOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </label>
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
      <datalist id="planning-shifts-timezones">
        <option v-for="timezone in timezoneSuggestions" :key="timezone" :value="timezone" />
      </datalist>
    </div>

    <Modal
      v-model:open="templateModalOpen"
      :title="selectedTemplateId ? tp('templateModalEditTitle') : tp('templateModalCreateTitle')"
      :footer="null"
      @cancel="closeTemplateModal"
    >
      <form class="planning-orders-form planning-shifts-template-modal" data-testid="planning-shifts-template-modal" @submit.prevent="submitTemplate">
        <div class="planning-orders-form-grid">
          <label class="field-stack"><span>{{ tp("fieldsCode") }}</span><input v-model="templateDraft.code" required /></label>
          <label class="field-stack"><span>{{ tp("fieldsLabel") }}</span><input v-model="templateDraft.label" required /></label>
          <label class="field-stack"><span>{{ tp("fieldsStartTime") }}</span><input v-model="templateDraft.local_start_time" type="time" required /></label>
          <label class="field-stack"><span>{{ tp("fieldsEndTime") }}</span><input v-model="templateDraft.local_end_time" type="time" required /></label>
          <label class="field-stack"><span>{{ tp("fieldsBreakMinutes") }}</span><input v-model.number="templateDraft.default_break_minutes" type="number" min="0" /></label>
          <label class="field-stack">
            <span>{{ tp("fieldsShiftType") }}</span>
            <select v-model="templateDraft.shift_type_code" required :disabled="loadingShiftTypeOptions || !templateShiftTypeOptions.length">
              <option value="" disabled>{{ shiftTypePlaceholderLabel }}</option>
              <option v-for="option in templateShiftTypeOptions" :key="option.code" :value="option.code">
                {{ option.label }}
              </option>
            </select>
            <span v-if="shiftTypeHelpLabel" class="field-help">{{ shiftTypeHelpLabel }}</span>
          </label>
          <label class="field-stack"><span>{{ tp("fieldsMeetingPoint") }}</span><input v-model="templateDraft.meeting_point" /></label>
          <label class="field-stack"><span>{{ tp("fieldsLocationText") }}</span><input v-model="templateDraft.location_text" /></label>
          <label class="field-stack field-stack--wide"><span>{{ tp("fieldsNotes") }}</span><textarea v-model="templateDraft.notes" rows="2" /></label>
        </div>
        <div class="cta-row">
          <button class="cta-button" data-testid="planning-shifts-template-modal-save" type="submit" :disabled="!actionState.canCreateTemplate">{{ tp("actionsSave") }}</button>
          <button class="cta-button cta-secondary" type="button" @click="resetTemplateDraft">{{ tp("actionsReset") }}</button>
          <button class="cta-button cta-secondary" data-testid="planning-shifts-template-modal-cancel" type="button" @click="closeTemplateModal">{{ tp("actionsCancel") }}</button>
        </div>
      </form>
    </Modal>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import { Modal } from "ant-design-vue";

import { useAuthStore as usePrimaryAuthStore } from "#/store";
import { useSicherPlanFeedback } from "@/composables/useSicherPlanFeedback";
import { listPlanningRecords, type PlanningRecordListItem } from "@/api/planningOrders";
import {
  createShift,
  createShiftPlan,
  createShiftSeries,
  createShiftSeriesException,
  createShiftTemplate,
  generateShiftSeries,
  getShift,
  getShiftPlan,
  getShiftReleaseDiagnostics,
  getShiftSeries,
  getShiftTemplate,
  listShiftTypeOptions,
  listBoardShifts,
  listShiftPlans,
  listShiftSeriesExceptions,
  listShiftSeries,
  listShiftTemplates,
  listShifts,
  setShiftReleaseState,
  updateShift,
  updateShiftPlan,
  updateShiftSeries,
  updateShiftSeriesException,
  updateShiftTemplate,
  updateShiftVisibility,
  copyShiftSlice,
  type PlanningBoardShiftListItem,
  type ShiftListItem,
  type ShiftRead,
  type ShiftReleaseDiagnosticsRead,
  type ShiftPlanListItem,
  type ShiftSeriesExceptionRead,
  type ShiftSeriesListItem,
  type ShiftSeriesRead,
  type ShiftTypeOption,
  type ShiftTemplateListItem,
  type ShiftTemplateRead,
  PlanningShiftsApiError,
} from "@/api/planningShifts";
import { planningShiftsMessages } from "@/i18n/planningShifts.messages";
import { useAuthStore } from "@/stores/auth";
import { useLocaleStore } from "@/stores/locale";
import {
  buildShiftTypeOptions,
  buildShiftCopyPayload,
  DEFAULT_SHIFT_TYPE_OPTIONS,
  derivePlanningShiftActionState,
  mapPlanningShiftApiMessage,
  recurrenceLabel,
  resolveSelectedShiftPlanId,
} from "@/features/planning/planningShifts.helpers";

const props = withDefaults(defineProps<{ embedded?: boolean }>(), {
  embedded: false,
});

const primaryAuthStore = usePrimaryAuthStore();
const authStore = useAuthStore();
const localeStore = useLocaleStore();
const { showFeedbackToast } = useSicherPlanFeedback();
const currentLocale = computed(() => (localeStore.locale === "en" ? "en" : "de"));
const role = computed(() => authStore.effectiveRole || "tenant_admin");
const tenantScopeId = computed(() => authStore.effectiveTenantScopeId || authStore.tenantScopeId || "");
const accessToken = computed(() => authStore.effectiveAccessToken || authStore.accessToken || "");

const templates = ref<ShiftTemplateListItem[]>([]);
const planningRecords = ref<PlanningRecordListItem[]>([]);
const shiftPlans = ref<ShiftPlanListItem[]>([]);
const seriesRows = ref<ShiftSeriesListItem[]>([]);
const shifts = ref<ShiftListItem[]>([]);
const boardRows = ref<PlanningBoardShiftListItem[]>([]);
const seriesExceptions = ref<ShiftSeriesExceptionRead[]>([]);
const selectedShiftDiagnostics = ref<ShiftReleaseDiagnosticsRead | null>(null);
const shiftTypeOptions = ref<ShiftTypeOption[]>([]);
const loadingShiftTypeOptions = ref(false);
const templateModalOpen = ref(false);

const selectedTemplateId = ref("");
const selectedShiftPlanId = ref("");
const selectedSeriesId = ref("");
const selectedExceptionId = ref("");
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
const activeWorkspaceTab = ref("templates");
const workspaceTabs = computed(() => [
  { id: "templates", label: tp("templatesTitle") },
  { id: "plans", label: tp("plansTitle") },
  { id: "series", label: tp("seriesTitle") },
  { id: "shifts", label: tp("shiftsTitle") },
  { id: "board", label: tp("boardTitle") },
]);
const shiftTemplateOptions = computed(() => templates.value);
const selectedShiftPlanRow = computed(() => shiftPlans.value.find((plan) => plan.id === selectedShiftPlanId.value) || null);
const planningRecordOptions = computed(() =>
  planningRecords.value.map((record) => ({
    id: record.id,
    label: `${record.name} · ${record.planning_from} - ${record.planning_to}`,
  })),
);
const templateShiftTypeOptions = computed(() =>
  buildShiftTypeOptions(shiftTypeOptions.value, templateDraft.shift_type_code, tp("shiftTypeLegacySuffix")),
);
const seriesShiftTypeOptions = computed(() =>
  buildShiftTypeOptions(shiftTypeOptions.value, seriesDraft.shift_type_code, tp("shiftTypeLegacySuffix")),
);
const shiftShiftTypeOptions = computed(() =>
  buildShiftTypeOptions(shiftTypeOptions.value, shiftDraft.shift_type_code, tp("shiftTypeLegacySuffix")),
);
const shiftTypePlaceholderLabel = computed(() =>
  loadingShiftTypeOptions.value ? tp("shiftTypeLoading") : tp("shiftTypePlaceholder"),
);
const shiftTypeHelpLabel = computed(() =>
  loadingShiftTypeOptions.value ? tp("shiftTypeLoading") : shiftTypeOptions.value.length ? "" : tp("shiftTypeUnavailable"),
);
const weekdayOptions = computed(() => [
  { index: 0, label: tp("weekdayMon") },
  { index: 1, label: tp("weekdayTue") },
  { index: 2, label: tp("weekdayWed") },
  { index: 3, label: tp("weekdayThu") },
  { index: 4, label: tp("weekdayFri") },
  { index: 5, label: tp("weekdaySat") },
  { index: 6, label: tp("weekdaySun") },
]);
const visibilityStateOptions = computed(() => [
  { value: "customer", label: tp("visibilityCustomer") },
  { value: "subcontractor", label: tp("visibilitySubcontractor") },
  { value: "stealth", label: tp("visibilityStealth") },
]);
const releaseStateOptions = computed(() => [
  { value: "draft", label: tp("statusDraft") },
  { value: "release_ready", label: tp("statusReleaseReady") },
  { value: "released", label: tp("statusReleased") },
]);
const timezoneSuggestions = ["Europe/Berlin", "Europe/Vienna", "Europe/Zurich", "UTC"];
const seriesUsesWeeklyRecurrence = computed(() => seriesDraft.recurrence_code === "weekly");
const exceptionRequiresOverrideTimes = computed(() => exceptionDraft.action_code === "override");

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

function setFeedback(tone: string, title: string, message: string) {
  showFeedbackToast({
    key: "planning-shifts-feedback",
    message,
    title,
    tone: tone as "error" | "info" | "neutral" | "success" | "warning",
  });
}

function createEmptyTemplateDraft() {
  return {
    tenant_id: tenantScopeId.value || "",
    code: "",
    label: "",
    local_start_time: "08:00",
    local_end_time: "16:00",
    default_break_minutes: 30,
    shift_type_code: DEFAULT_SHIFT_TYPE_OPTIONS[0]?.code || "",
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
    notes: "",
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
    notes: "",
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
    shift_type_code: DEFAULT_SHIFT_TYPE_OPTIONS[0]?.code || "",
    location_text: "",
    meeting_point: "",
    notes: "",
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

function resetExceptionDraft() {
  Object.assign(exceptionDraft, createEmptyExceptionDraft());
}

function resetShiftDraft() {
  Object.assign(shiftDraft, createEmptyShiftDraft());
}

async function selectTemplate(templateId: string) {
  selectedTemplateId.value = templateId;
  const row = await getShiftTemplate(tenantScopeId.value, templateId, accessToken.value);
  assignTemplateDraft(row);
  templateModalOpen.value = true;
}

async function selectShiftPlan(shiftPlanId: string) {
  selectedShiftPlanId.value = shiftPlanId;
  await refreshPlanDetails();
}

async function changeSeriesShiftPlan() {
  if (!selectedShiftPlanId.value) {
    clearPlanSelectionContext();
    return;
  }
  await refreshPlanDetails();
  startCreateSeries();
}

async function changeShiftTabPlan() {
  if (!selectedShiftPlanId.value) {
    clearPlanSelectionContext();
    return;
  }
  await refreshPlanDetails();
  startCreateShift();
}

async function selectSeries(seriesId: string) {
  selectedSeriesId.value = seriesId;
  await refreshSeriesDetails();
}

function selectException(exceptionId: string) {
  selectedExceptionId.value = exceptionId;
  const row = seriesExceptions.value.find((entry) => entry.id === exceptionId);
  if (row) {
    Object.assign(exceptionDraft, {
      ...row,
      tenant_id: tenantScopeId.value,
      override_local_start_time: row.override_local_start_time || "",
      override_local_end_time: row.override_local_end_time || "",
      notes: row.notes || "",
    });
  }
}

async function selectShift(shiftId: string) {
  selectedShiftId.value = shiftId;
  await refreshSelectedShift();
}

function startCreateTemplate() {
  resetTemplateDraft();
  selectedTemplateId.value = "";
  templateModalOpen.value = true;
}
function startCreatePlan() {
  resetShiftPlanDraft();
  clearPlanSelectionContext();
}
function startCreateSeries() {
  resetSeriesDraft();
  resetExceptionDraft();
  selectedSeriesId.value = "";
  selectedExceptionId.value = "";
  seriesExceptions.value = [];
}
function startCreateException() {
  resetExceptionDraft();
  selectedExceptionId.value = "";
}
function startCreateShift() {
  resetShiftDraft();
  selectedShiftId.value = "";
  selectedShiftDiagnostics.value = null;
}

async function refreshTemplates() {
  templates.value = await listShiftTemplates(tenantScopeId.value, accessToken.value, {});
}

async function refreshShiftTypeOptions() {
  loadingShiftTypeOptions.value = true;
  try {
    const options = await listShiftTypeOptions(tenantScopeId.value, accessToken.value);
    shiftTypeOptions.value = options.length ? options : DEFAULT_SHIFT_TYPE_OPTIONS;
  } finally {
    loadingShiftTypeOptions.value = false;
  }
}

async function refreshPlanningRecords() {
  planningRecords.value = await listPlanningRecords(tenantScopeId.value, accessToken.value, {});
}

async function refreshPlans() {
  const [records, plans] = await Promise.all([
    listPlanningRecords(tenantScopeId.value, accessToken.value, {}),
    listShiftPlans(tenantScopeId.value, accessToken.value, planFilters),
  ]);
  planningRecords.value = records;
  shiftPlans.value = plans;
  const nextShiftPlanId = resolveSelectedShiftPlanId(selectedShiftPlanId.value, plans);
  if (!nextShiftPlanId) {
    clearPlanSelectionContext();
    return;
  }
  selectedShiftPlanId.value = nextShiftPlanId;
}

async function refreshPlanDetails() {
  if (!selectedShiftPlanId.value) return;
  const plan = await getShiftPlan(tenantScopeId.value, selectedShiftPlanId.value, accessToken.value);
  seriesRows.value = await listShiftSeries(tenantScopeId.value, selectedShiftPlanId.value, accessToken.value);
  shifts.value = await listShifts(tenantScopeId.value, accessToken.value, { ...shiftFilters, shift_plan_id: selectedShiftPlanId.value });
  Object.assign(shiftPlanDraft, { ...plan, tenant_id: tenantScopeId.value });
  if (selectedSeriesId.value && !seriesRows.value.some((entry) => entry.id === selectedSeriesId.value)) {
    selectedSeriesId.value = "";
    selectedExceptionId.value = "";
    seriesExceptions.value = [];
  }
  if (selectedShiftId.value && !shifts.value.some((entry) => entry.id === selectedShiftId.value)) {
    selectedShiftId.value = "";
    selectedShiftDiagnostics.value = null;
  }
}

async function refreshSeriesDetails() {
  if (!selectedSeriesId.value) return;
  const [series, exceptions] = await Promise.all([
    getShiftSeries(tenantScopeId.value, selectedSeriesId.value, accessToken.value),
    listShiftSeriesExceptions(tenantScopeId.value, selectedSeriesId.value, accessToken.value),
  ]);
  assignSeriesDraft(series);
  seriesExceptions.value = exceptions;
  if (selectedExceptionId.value && !exceptions.some((entry) => entry.id === selectedExceptionId.value)) {
    selectedExceptionId.value = "";
    resetExceptionDraft();
  }
}

async function refreshSelectedShift() {
  if (!selectedShiftId.value) return;
  const [shift, diagnostics] = await Promise.all([
    getShift(tenantScopeId.value, selectedShiftId.value, accessToken.value),
    getShiftReleaseDiagnostics(tenantScopeId.value, selectedShiftId.value, accessToken.value),
  ]);
  assignShiftDraft(shift);
  selectedShiftDiagnostics.value = diagnostics;
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
    const payload = {
      ...templateDraft,
      tenant_id: tenantScopeId.value,
    };
    if (selectedTemplateId.value) {
      await updateShiftTemplate(tenantScopeId.value, selectedTemplateId.value, accessToken.value, payload);
    } else {
      const created = await createShiftTemplate(tenantScopeId.value, accessToken.value, payload);
      selectedTemplateId.value = created.id;
    }
    await refreshTemplates();
    if (selectedTemplateId.value) {
      await selectTemplate(selectedTemplateId.value);
    }
    templateModalOpen.value = false;
    setFeedback("success", tp("successTitle"), tp("saved"));
  } catch (error) {
    handleApiError(error);
  }
}

function closeTemplateModal() {
  templateModalOpen.value = false;
}

async function submitShiftPlan() {
  try {
    const payload = {
      ...shiftPlanDraft,
      tenant_id: tenantScopeId.value,
    };
    if (selectedShiftPlanId.value) {
      await updateShiftPlan(tenantScopeId.value, selectedShiftPlanId.value, accessToken.value, payload);
    } else {
      const created = await createShiftPlan(tenantScopeId.value, accessToken.value, payload);
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
  if (!selectedShiftPlanId.value) {
    setFeedback("error", tp("errorTitle"), tp("seriesMissingPlanSubmit"));
    return;
  }
  try {
    const payload = {
      ...seriesDraft,
      tenant_id: tenantScopeId.value,
      shift_plan_id: selectedShiftPlanId.value,
      shift_template_id: seriesDraft.shift_template_id || selectedTemplateId.value || "",
    };
    if (selectedSeriesId.value) {
      await updateShiftSeries(tenantScopeId.value, selectedSeriesId.value, accessToken.value, payload);
    } else {
      const created = await createShiftSeries(tenantScopeId.value, selectedShiftPlanId.value, accessToken.value, payload);
      selectedSeriesId.value = created.id;
    }
    seriesRows.value = await listShiftSeries(tenantScopeId.value, selectedShiftPlanId.value, accessToken.value);
    await refreshSeriesDetails();
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
    const payload = {
      ...exceptionDraft,
      tenant_id: tenantScopeId.value,
    };
    if (selectedExceptionId.value) {
      await updateShiftSeriesException(tenantScopeId.value, selectedExceptionId.value, accessToken.value, payload);
    } else {
      const created = await createShiftSeriesException(tenantScopeId.value, selectedSeriesId.value, accessToken.value, payload);
      selectedExceptionId.value = created.id;
    }
    await refreshSeriesDetails();
    setFeedback("success", tp("successTitle"), tp("saved"));
  } catch (error) {
    handleApiError(error);
  }
}

async function submitShift() {
  if (!selectedShiftPlanId.value) {
    setFeedback("error", tp("errorTitle"), tp("shiftsMissingPlanSubmit"));
    return;
  }
  try {
    const payload = {
      ...shiftDraft,
      tenant_id: tenantScopeId.value,
      shift_plan_id: selectedShiftPlanId.value,
      starts_at: fromDateTimeLocal(shiftDraft.starts_at),
      ends_at: fromDateTimeLocal(shiftDraft.ends_at),
    };
    if (selectedShiftId.value) {
      await updateShift(tenantScopeId.value, selectedShiftId.value, accessToken.value, payload);
    } else {
      const created = await createShift(tenantScopeId.value, accessToken.value, payload);
      selectedShiftId.value = created.id;
    }
    await refreshShifts();
    await refreshBoard();
    if (selectedShiftId.value) {
      await refreshSelectedShift();
    }
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
    await copyShiftSlice(
      tenantScopeId.value,
      selectedShiftPlanId.value,
      accessToken.value,
      buildShiftCopyPayload(shiftFilters.date_from, deltaDays),
    );
    await refreshShifts();
    await refreshBoard();
    setFeedback("success", tp("successTitle"), tp("copied"));
  } catch (error) {
    handleApiError(error);
  }
}

async function changeShiftReleaseState(releaseState: string) {
  if (!selectedShiftId.value) return;
  try {
    await setShiftReleaseState(tenantScopeId.value, selectedShiftId.value, accessToken.value, {
      release_state: releaseState,
      version_no: shiftDraft.version_no,
    });
    await refreshShifts();
    await refreshBoard();
    await refreshSelectedShift();
    setFeedback("success", tp("successTitle"), tp("saved"));
  } catch (error) {
    handleApiError(error);
  }
}

async function updateSelectedShiftVisibility(customerVisibleFlag: boolean, subcontractorVisibleFlag: boolean) {
  if (!selectedShiftId.value) return;
  try {
    await updateShiftVisibility(tenantScopeId.value, selectedShiftId.value, accessToken.value, {
      customer_visible_flag: customerVisibleFlag,
      subcontractor_visible_flag: subcontractorVisibleFlag,
      version_no: shiftDraft.version_no,
    });
    await refreshShifts();
    await refreshBoard();
    await refreshSelectedShift();
    setFeedback("success", tp("successTitle"), tp("saved"));
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

function releaseStateLabel(value: string) {
  if (value === "draft") return tp("statusDraft");
  if (value === "release_ready") return tp("statusReleaseReady");
  if (value === "released") return tp("statusReleased");
  return value;
}

function normalizeWeekdayMask(value: string | null | undefined) {
  const candidate = (value || "").trim();
  return /^[01]{7}$/.test(candidate) ? candidate : "1111100";
}

function isWeekdaySelected(index: number) {
  return normalizeWeekdayMask(seriesDraft.weekday_mask)[index] === "1";
}

function toggleWeekday(index: number) {
  const mask = normalizeWeekdayMask(seriesDraft.weekday_mask).split("");
  mask[index] = mask[index] === "1" ? "0" : "1";
  seriesDraft.weekday_mask = mask.join("");
}

function handleApiError(error: unknown) {
  const messageKey = error instanceof PlanningShiftsApiError ? error.messageKey : "error";
  if (messageKey === "errors.iam.auth.invalid_access_token" || messageKey === "errors.iam.auth.invalid_refresh_token") {
    void handleAuthExpired();
  }
  setFeedback("error", tp("errorTitle"), tp(mapPlanningShiftApiMessage(messageKey) as keyof typeof planningShiftsMessages.de));
}

async function handleAuthExpired() {
  authStore.clearSession();
  try {
    primaryAuthStore.clearSessionState();
    await primaryAuthStore.redirectToLogin("/admin/planning-shifts");
  } catch {
    // Keep the current page feedback visible even if redirect bootstrap is unavailable.
  }
}

async function ensureShiftSessionReady() {
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

async function refreshActiveWorkspaceData() {
  if (!tenantScopeId.value || !accessToken.value || !canRead.value) {
    return;
  }

  if (activeWorkspaceTab.value === "templates") {
    await refreshTemplates();
    return;
  }
  if (activeWorkspaceTab.value === "plans") {
    await refreshPlans();
    return;
  }
  if (activeWorkspaceTab.value === "series") {
    await refreshPlans();
    if (selectedShiftPlanId.value) {
      seriesRows.value = await listShiftSeries(tenantScopeId.value, selectedShiftPlanId.value, accessToken.value);
      if (selectedSeriesId.value) {
        seriesExceptions.value = await listShiftSeriesExceptions(tenantScopeId.value, selectedSeriesId.value, accessToken.value);
      }
    }
    return;
  }
  if (activeWorkspaceTab.value === "shifts") {
    await refreshPlans();
    if (selectedShiftPlanId.value) {
      await refreshShifts();
    }
    if (selectedShiftId.value) {
      selectedShiftDiagnostics.value = await getShiftReleaseDiagnostics(tenantScopeId.value, selectedShiftId.value, accessToken.value);
    }
    return;
  }
  await refreshBoard();
}

async function recoverSessionAndRefreshActiveTab() {
  if (document.visibilityState === "hidden") {
    return;
  }
  const ready = await ensureShiftSessionReady();
  if (!ready) {
    return;
  }
  try {
    await refreshActiveWorkspaceData();
  } catch (error) {
    handleApiError(error);
  }
}

function handleVisibilityChange() {
  if (document.visibilityState === "visible") {
    void recoverSessionAndRefreshActiveTab();
  }
}

function handleWindowFocus() {
  void recoverSessionAndRefreshActiveTab();
}

function clearPlanSelectionContext() {
  selectedShiftPlanId.value = "";
  selectedSeriesId.value = "";
  selectedExceptionId.value = "";
  selectedShiftId.value = "";
  seriesRows.value = [];
  seriesExceptions.value = [];
  shifts.value = [];
  selectedShiftDiagnostics.value = null;
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

function assignTemplateDraft(row: ShiftTemplateRead) {
  Object.assign(templateDraft, {
    ...row,
    tenant_id: tenantScopeId.value,
    meeting_point: row.meeting_point || "",
    location_text: row.location_text || "",
    notes: row.notes || "",
    shift_type_code: row.shift_type_code || "",
  });
}

function assignSeriesDraft(row: ShiftSeriesRead) {
  Object.assign(seriesDraft, {
    ...row,
    tenant_id: tenantScopeId.value,
    shift_template_id: row.shift_template_id || "",
    weekday_mask: normalizeWeekdayMask(row.weekday_mask),
    notes: row.notes || "",
    shift_type_code: row.shift_type_code || "",
    meeting_point: row.meeting_point || "",
    location_text: row.location_text || "",
  });
}

function assignShiftDraft(row: ShiftRead) {
  Object.assign(shiftDraft, {
    ...row,
    tenant_id: tenantScopeId.value,
    starts_at: normalizeDateTimeLocal(row.starts_at),
    ends_at: normalizeDateTimeLocal(row.ends_at),
    notes: row.notes || "",
    shift_type_code: row.shift_type_code || "",
    meeting_point: row.meeting_point || "",
    location_text: row.location_text || "",
  });
}

watch(
  () => seriesDraft.recurrence_code,
  (value) => {
    if (value === "weekly") {
      seriesDraft.weekday_mask = normalizeWeekdayMask(seriesDraft.weekday_mask);
      return;
    }
    seriesDraft.weekday_mask = "";
  },
  { immediate: true },
);

watch(
  () => exceptionDraft.action_code,
  (value) => {
    if (value !== "override") {
      exceptionDraft.override_local_start_time = "";
      exceptionDraft.override_local_end_time = "";
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
    void refreshActiveWorkspaceData();
  },
);

onMounted(async () => {
  authStore.syncFromPrimarySession();
  const sessionReady = await ensureShiftSessionReady();
  if (!sessionReady || !tenantScopeId.value || !accessToken.value || !canRead.value) {
    return;
  }
  document.addEventListener("visibilitychange", handleVisibilityChange);
  window.addEventListener("focus", handleWindowFocus);
  try {
    await Promise.all([refreshShiftTypeOptions(), refreshTemplates(), refreshPlanningRecords(), refreshPlans(), refreshBoard()]);
  } catch (error) {
    handleApiError(error);
  }
});

onBeforeUnmount(() => {
  document.removeEventListener("visibilitychange", handleVisibilityChange);
  window.removeEventListener("focus", handleWindowFocus);
});
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
.planning-shifts-panel,
.planning-orders-empty {
  border-radius: 18px;
  border: 1px solid var(--sp-color-border);
  background: color-mix(in srgb, var(--sp-color-surface-card) 94%, white);
  box-shadow: 0 18px 50px rgb(15 23 42 / 7%);
}

.planning-shifts-hero {
  display: grid;
  gap: 1rem;
}

.planning-shifts-weekday-picker {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.planning-shifts-series-context {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  padding: 1rem 1.1rem;
  border-radius: 14px;
  border: 1px solid color-mix(in srgb, var(--primary-color, rgb(40,170,170)) 18%, white);
  background: color-mix(in srgb, var(--primary-color, rgb(40,170,170)) 6%, white);
}

.planning-shifts-series-context p {
  margin: 0.25rem 0 0;
}

.planning-shifts-series-context--warning {
  border-color: color-mix(in srgb, #d97706 45%, white);
  background: color-mix(in srgb, #f59e0b 10%, white);
}

.planning-shifts-weekday-chip {
  border: 1px solid color-mix(in srgb, var(--primary-color, rgb(40,170,170)) 30%, white);
  background: white;
  color: #184949;
  border-radius: 999px;
  padding: 0.4rem 0.75rem;
  font-weight: 600;
}

.planning-shifts-weekday-chip.active {
  border-color: var(--primary-color, rgb(40,170,170));
  background: color-mix(in srgb, var(--primary-color, rgb(40,170,170)) 16%, white);
}

.planning-shifts-board {
  grid-column: 1 / -1;
}

.planning-shifts-lead {
  max-width: 70ch;
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

.planning-shifts-release-panel {
  gap: 1rem;
}

.planning-shifts-release-grid {
  display: grid;
  gap: 0.9rem;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.planning-shifts-release-stat {
  display: grid;
  gap: 0.35rem;
  padding: 0.85rem 1rem;
  border-radius: 14px;
  border: 1px solid var(--sp-color-border-soft);
  background: color-mix(in srgb, var(--sp-color-surface-card) 92%, white);
}

.planning-shifts-release-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.planning-shifts-release-issues {
  display: grid;
  gap: 0.55rem;
}

.planning-shifts-release-issues ul {
  margin: 0;
  padding-left: 1.1rem;
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
  .planning-orders-empty,
  .planning-shifts-series-context {
    flex-direction: column;
    align-items: stretch;
  }

  .planning-orders-form-grid,
  .planning-shifts-form-grid,
  .planning-shifts-form-grid--controls,
  .planning-shifts-release-grid {
    grid-template-columns: 1fr;
  }
}
</style>
