<template>
  <section class="employee-admin-page">
    <section v-if="!embedded" class="module-card employee-admin-hero">
      <div>
        <p class="eyebrow">{{ t("employeeAdmin.eyebrow") }}</p>
        <h2>{{ t("employeeAdmin.title") }}</h2>
        <p class="employee-admin-lead">{{ t("employeeAdmin.lead") }}</p>
        <div class="employee-admin-meta">
          <span class="employee-admin-meta__pill">{{ t("employeeAdmin.permission.read") }}: {{ canRead ? "on" : "off" }}</span>
          <span class="employee-admin-meta__pill">{{ t("employeeAdmin.permission.write") }}: {{ canWrite ? "on" : "off" }}</span>
          <span class="employee-admin-meta__pill">{{ t("employeeAdmin.permission.privateRead") }}: {{ canReadPrivate ? "on" : "off" }}</span>
        </div>
      </div>
    </section>

    <div v-if="!embedded && isPlatformAdmin" class="module-card employee-admin-scope" :class="{ 'employee-admin-scope--embedded': embedded }">
      <label class="field-stack">
        <span>{{ t("employeeAdmin.scope.label") }}</span>
        <input v-model="tenantScopeInput" :disabled="!isPlatformAdmin" :placeholder="t('employeeAdmin.scope.placeholder')" />
      </label>
      <p class="field-help">{{ t("employeeAdmin.scope.help") }}</p>
      <div class="cta-row">
        <button class="cta-button" type="button" @click="rememberScope">
          {{ t("employeeAdmin.actions.rememberScope") }}
        </button>
        <button class="cta-button cta-secondary" type="button" :disabled="!canRead" @click="refreshEmployees">
          {{ t("employeeAdmin.actions.refresh") }}
        </button>
      </div>
    </div>

    <section v-if="!resolvedTenantScopeId" class="module-card employee-admin-empty">
      <p class="eyebrow">{{ t("employeeAdmin.scope.missingTitle") }}</p>
      <h3>{{ t("employeeAdmin.scope.missingBody") }}</h3>
    </section>

    <section v-else-if="!canRead" class="module-card employee-admin-empty">
      <p class="eyebrow">{{ t("employeeAdmin.permission.missingTitle") }}</p>
      <h3>{{ t("employeeAdmin.permission.missingBody") }}</h3>
    </section>

    <SicherPlanLoadingOverlay
      v-else
      :aria-label="employeeWorkspaceLoadingText"
      :busy="employeeWorkspaceBusy"
      :text="employeeWorkspaceLoadingText"
      busy-testid="employee-workspace-loading-overlay"
    >
      <div class="employee-admin-grid" data-testid="employee-master-detail-layout">
      <section class="module-card employee-admin-panel employee-admin-list-panel" data-testid="employee-list-section">
        <div class="employee-admin-panel__header">
          <div>
            <p class="eyebrow">{{ t("employeeAdmin.list.eyebrow") }}</p>
            <h3>{{ t("employeeAdmin.list.title") }}</h3>
          </div>
          <StatusBadge :status="loading.list ? 'inactive' : 'active'" />
        </div>

        <nav class="employee-admin-tabs employee-admin-tabs--panel" data-testid="employee-list-tabs" aria-label="Employee list tools">
          <button
            type="button"
            class="employee-admin-tab"
            :class="{ active: listPanelTab === 'search' }"
            data-testid="employee-list-tab-search"
            @click="listPanelTab = 'search'"
          >
            {{ t("employeeAdmin.actions.search") }}
          </button>
          <button
            type="button"
            class="employee-admin-tab"
            :class="{ active: listPanelTab === 'import_export' }"
            data-testid="employee-list-tab-import-export"
            @click="listPanelTab = 'import_export'"
          >
            {{ t("employeeAdmin.import.eyebrow") }}
          </button>
        </nav>

        <section v-show="listPanelTab === 'search'" class="employee-admin-section employee-admin-tab-panel" data-testid="employee-list-tab-panel-search">
          <div class="employee-admin-form-grid">
            <label class="field-stack">
              <span>{{ t("employeeAdmin.filters.search") }}</span>
              <input v-model="filters.search" :placeholder="t('employeeAdmin.filters.searchPlaceholder')" />
            </label>
            <label class="field-stack">
              <span>{{ t("employeeAdmin.filters.status") }}</span>
              <select v-model="filters.status">
                <option value="">{{ t("employeeAdmin.filters.allStatuses") }}</option>
                <option value="active">{{ t("employeeAdmin.status.active") }}</option>
                <option value="inactive">{{ t("employeeAdmin.status.inactive") }}</option>
                <option value="archived">{{ t("employeeAdmin.status.archived") }}</option>
              </select>
            </label>
            <label class="field-stack">
              <span>{{ t("employeeAdmin.fields.defaultBranchId") }}</span>
              <select v-model="filters.default_branch_id">
                <option value="">{{ t("employeeAdmin.summary.none") }}</option>
                <option v-for="branch in branchOptions" :key="branch.id" :value="branch.id">
                  {{ formatStructureLabel(branch) }}
                </option>
              </select>
            </label>
            <label class="field-stack">
              <span>{{ t("employeeAdmin.fields.defaultMandateId") }}</span>
              <select v-model="filters.default_mandate_id">
                <option value="">{{ t("employeeAdmin.summary.none") }}</option>
                <option v-for="mandate in filterMandateOptions(filters.default_branch_id)" :key="mandate.id" :value="mandate.id">
                  {{ formatStructureLabel(mandate) }}
                </option>
              </select>
            </label>
          </div>

          <label class="employee-admin-checkbox">
            <input v-model="filters.include_archived" type="checkbox" />
            <span>{{ t("employeeAdmin.filters.includeArchived") }}</span>
          </label>

          <div class="cta-row">
            <button class="cta-button" type="button" @click="refreshEmployees">{{ t("employeeAdmin.actions.search") }}</button>
            <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canCreate" @click="startCreateEmployee">
              {{ t("employeeAdmin.actions.newEmployee") }}
            </button>
          </div>
        </section>

        <section v-show="listPanelTab === 'import_export'" class="employee-admin-section employee-admin-tab-panel" data-testid="employee-list-tab-panel-import-export">
          <div class="employee-admin-panel__header">
            <div>
              <p class="eyebrow">{{ t("employeeAdmin.import.eyebrow") }}</p>
              <h3>{{ t("employeeAdmin.import.title") }}</h3>
            </div>
          </div>
          <input type="file" accept=".csv,text/csv" :disabled="!actionState.canImport" @change="onImportSelected" />
          <div class="cta-row">
            <button class="cta-button cta-secondary" type="button" :disabled="!pendingImportFile || !actionState.canImport" @click="loadImportFile">
              {{ t("employeeAdmin.actions.loadImportFile") }}
            </button>
            <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canImport" @click="importDraft.csv_text = buildEmployeeImportTemplateRows()">
              {{ t("employeeAdmin.actions.resetImportTemplate") }}
            </button>
            <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canExport" @click="runExport">
              {{ t("employeeAdmin.actions.exportEmployees") }}
            </button>
          </div>
          <label class="field-stack">
            <span>{{ t("employeeAdmin.import.csvLabel") }}</span>
            <textarea v-model="importDraft.csv_text" :disabled="!actionState.canImport" rows="7" />
          </label>
          <label class="employee-admin-checkbox">
            <input v-model="importDraft.continue_on_error" type="checkbox" :disabled="!actionState.canImport" />
            <span>{{ t("employeeAdmin.import.continueOnError") }}</span>
          </label>
          <div class="cta-row">
            <button class="cta-button" type="button" :disabled="!actionState.canImport" @click="runImportDryRun">
              {{ t("employeeAdmin.actions.importDryRun") }}
            </button>
            <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canImport" @click="runImportExecute">
              {{ t("employeeAdmin.actions.importExecute") }}
            </button>
          </div>
          <p v-if="importDryRunResult" class="field-help">
            {{ t("employeeAdmin.import.dryRunSummary", { total: importDryRunResult.total_rows, invalid: importDryRunResult.invalid_rows }) }}
          </p>
          <p v-if="lastImportResult" class="field-help">
            {{ t("employeeAdmin.import.executeSummary", { total: lastImportResult.total_rows, created: lastImportResult.created_employees, updated: lastImportResult.updated_employees }) }}
          </p>
          <p v-if="lastExportResult" class="field-help">
            {{ t("employeeAdmin.import.exportSummary", { rows: lastExportResult.row_count, documentId: lastExportResult.document_id }) }}
          </p>
        </section>

        <div v-if="employees.length" class="employee-admin-list">
          <button
            v-for="employee in employees"
            :key="employee.id"
            type="button"
            class="employee-admin-row"
            :class="{ selected: employee.id === selectedEmployeeId }"
            @click="selectEmployee(employee.id)"
          >
            <div class="employee-admin-row__text">
              <strong class="employee-admin-row__title">{{ employee.personnel_no }} · {{ employee.first_name }} {{ employee.last_name }}</strong>
              <span class="employee-admin-row__meta">{{ employee.work_email || employee.mobile_phone || t("employeeAdmin.summary.none") }}</span>
            </div>
            <StatusBadge :status="employee.status" />
          </button>
        </div>
        <p v-else class="employee-admin-list-empty">{{ t("employeeAdmin.list.empty") }}</p>
      </section>

      <section class="module-card employee-admin-panel employee-admin-detail" data-testid="employee-detail-workspace">
        <div class="employee-admin-panel__header">
          <div>
            <p class="eyebrow">{{ t("employeeAdmin.detail.eyebrow") }}</p>
            <h3>{{ isCreatingEmployee ? t("employeeAdmin.detail.newTitle") : selectedEmployeeLabel }}</h3>
          </div>
          <StatusBadge v-if="selectedEmployee && !isCreatingEmployee" :status="selectedEmployee.status" />
        </div>

        <template v-if="isCreatingEmployee || selectedEmployee">
          <nav class="employee-admin-tabs" data-testid="employee-detail-tabs" aria-label="Employee detail sections">
            <button
              v-for="tab in employeeDetailTabs"
              :key="tab.id"
              type="button"
              class="employee-admin-tab"
              :class="{ active: tab.id === activeDetailTab }"
              :data-testid="`employee-tab-${tab.id}`"
              @click="activeDetailTab = tab.id"
            >
              {{ tab.label }}
            </button>
          </nav>

          <section
            v-if="activeDetailTab === 'overview'"
            class="employee-admin-section employee-admin-tab-panel"
            data-testid="employee-tab-panel-overview"
          >
          <div v-if="selectedEmployee && !isCreatingEmployee" class="employee-admin-summary">
            <article class="employee-admin-summary__card">
              <span>{{ t("employeeAdmin.summary.branch") }}</span>
              <strong>{{ selectedEmployeeBranchLabel || t("employeeAdmin.summary.none") }}</strong>
            </article>
            <article class="employee-admin-summary__card">
              <span>{{ t("employeeAdmin.summary.mandate") }}</span>
              <strong>{{ selectedEmployeeMandateLabel || t("employeeAdmin.summary.none") }}</strong>
            </article>
            <article class="employee-admin-summary__card">
              <span>{{ t("employeeAdmin.summary.currentAddress") }}</span>
              <strong>{{ currentAddressSummary || t("employeeAdmin.summary.none") }}</strong>
            </article>
            <article class="employee-admin-summary__card">
              <span>{{ t("employeeAdmin.summary.groups") }}</span>
              <strong>{{ selectedEmployee.group_memberships.length || 0 }}</strong>
            </article>
          </div>

          <form class="employee-admin-form employee-admin-form--structured" @submit.prevent="submitEmployee">
            <section class="employee-admin-editor-intro">
              <div>
                <p class="eyebrow">{{ t("employeeAdmin.form.eyebrow") }}</p>
                <h4>{{ t("employeeAdmin.form.title") }}</h4>
              </div>
              <p class="field-help">{{ t("employeeAdmin.form.lead") }}</p>
            </section>

            <section class="employee-admin-form-section">
              <div class="employee-admin-form-section__header">
                <p class="eyebrow">{{ t("employeeAdmin.form.identityEyebrow") }}</p>
                <h4>{{ t("employeeAdmin.form.identityTitle") }}</h4>
              </div>
              <div class="employee-admin-form-grid employee-admin-form-grid--editor">
                <label class="field-stack">
                  <span>{{ t("employeeAdmin.fields.personnelNo") }}</span>
                  <input v-model="employeeDraft.personnel_no" required />
                </label>
                <label class="field-stack">
                  <span>{{ t("employeeAdmin.fields.preferredName") }}</span>
                  <input v-model="employeeDraft.preferred_name" />
                </label>
                <label class="field-stack">
                  <span>{{ t("employeeAdmin.fields.firstName") }}</span>
                  <input v-model="employeeDraft.first_name" required />
                </label>
                <label class="field-stack">
                  <span>{{ t("employeeAdmin.fields.lastName") }}</span>
                  <input v-model="employeeDraft.last_name" required />
                </label>
              </div>
            </section>

            <section class="employee-admin-form-section">
              <div class="employee-admin-form-section__header">
                <p class="eyebrow">{{ t("employeeAdmin.form.contactEyebrow") }}</p>
                <h4>{{ t("employeeAdmin.form.contactTitle") }}</h4>
              </div>
              <div class="employee-admin-form-grid employee-admin-form-grid--editor">
                <label class="field-stack">
                  <span>{{ t("employeeAdmin.fields.workEmail") }}</span>
                  <input v-model="employeeDraft.work_email" type="email" />
                </label>
                <label class="field-stack">
                  <span>{{ t("employeeAdmin.fields.workPhone") }}</span>
                  <input v-model="employeeDraft.work_phone" />
                </label>
                <label class="field-stack">
                  <span>{{ t("employeeAdmin.fields.mobilePhone") }}</span>
                  <input v-model="employeeDraft.mobile_phone" />
                </label>
              </div>
            </section>

            <section class="employee-admin-form-section">
              <div class="employee-admin-form-section__header">
                <p class="eyebrow">{{ t("employeeAdmin.form.assignmentEyebrow") }}</p>
                <h4>{{ t("employeeAdmin.form.assignmentTitle") }}</h4>
              </div>
              <div class="employee-admin-form-grid employee-admin-form-grid--editor">
                <label class="field-stack">
                  <span>{{ t("employeeAdmin.fields.defaultBranchId") }}</span>
                  <select v-model="employeeDraft.default_branch_id">
                    <option value="">{{ t("employeeAdmin.summary.none") }}</option>
                    <option v-for="branch in branchOptions" :key="branch.id" :value="branch.id">
                      {{ formatStructureLabel(branch) }}
                    </option>
                  </select>
                </label>
                <label class="field-stack">
                  <span>{{ t("employeeAdmin.fields.defaultMandateId") }}</span>
                  <select v-model="employeeDraft.default_mandate_id">
                    <option value="">{{ t("employeeAdmin.summary.none") }}</option>
                    <option
                      v-for="mandate in filteredEmployeeMandates"
                      :key="mandate.id"
                      :value="mandate.id"
                    >
                      {{ formatStructureLabel(mandate) }}
                    </option>
                  </select>
                </label>
                <label class="field-stack">
                  <span>{{ t("employeeAdmin.fields.hireDate") }}</span>
                  <input v-model="employeeDraft.hire_date" type="date" />
                </label>
                <label class="field-stack">
                  <span>{{ t("employeeAdmin.fields.terminationDate") }}</span>
                  <input v-model="employeeDraft.termination_date" type="date" />
                </label>
                <label class="field-stack">
                  <span>{{ t("employeeAdmin.fields.status") }}</span>
                  <select v-model="employeeDraft.status">
                    <option value="active">{{ t("employeeAdmin.status.active") }}</option>
                    <option value="inactive">{{ t("employeeAdmin.status.inactive") }}</option>
                    <option value="archived">{{ t("employeeAdmin.status.archived") }}</option>
                  </select>
                </label>
                <label class="field-stack">
                  <span>{{ t("employeeAdmin.fields.employmentTypeCode") }}</span>
                  <select v-model="employeeDraft.employment_type_code">
                    <option value="">{{ t("employeeAdmin.summary.none") }}</option>
                    <option v-for="option in employmentTypeOptions" :key="option.value" :value="option.value">
                      {{ option.label }}
                    </option>
                  </select>
                </label>
                <label class="field-stack">
                  <span>{{ t("employeeAdmin.fields.targetWeeklyHours") }}</span>
                  <input v-model="employeeDraft.target_weekly_hours" min="0" step="0.25" type="number" />
                </label>
                <label class="field-stack">
                  <span>{{ t("employeeAdmin.fields.targetMonthlyHours") }}</span>
                  <input v-model="employeeDraft.target_monthly_hours" min="0" step="0.25" type="number" />
                </label>
              </div>
            </section>

            <section class="employee-admin-form-section">
              <div class="employee-admin-form-section__header">
                <p class="eyebrow">{{ t("employeeAdmin.form.accessEyebrow") }}</p>
                <h4>{{ t("employeeAdmin.form.accessTitle") }}</h4>
              </div>
              <p class="field-help">{{ t("employeeAdmin.form.accessLead") }}</p>
              <p v-if="!isCreatingEmployee && employeeDraft.user_id" class="field-help">
                {{ t("employeeAdmin.form.accessCurrent") }}: {{ employeeDraft.user_id }}
              </p>
            </section>

            <section class="employee-admin-form-section">
              <div class="employee-admin-form-section__header">
                <p class="eyebrow">{{ t("employeeAdmin.form.notesEyebrow") }}</p>
                <h4>{{ t("employeeAdmin.form.notesTitle") }}</h4>
              </div>
              <div class="employee-admin-form-grid employee-admin-form-grid--editor">
                <label class="field-stack field-stack--wide">
                  <span>{{ t("employeeAdmin.fields.notes") }}</span>
                  <textarea v-model="employeeDraft.notes" rows="4" />
                </label>
              </div>
            </section>

            <div class="employee-admin-form-actions">
              <div>
                <p class="eyebrow">{{ t("employeeAdmin.form.actionsEyebrow") }}</p>
                <strong>{{ t("employeeAdmin.form.actionsTitle") }}</strong>
              </div>
              <div class="cta-row">
                <button class="cta-button" type="submit" :disabled="!actionState.canEdit && !isCreatingEmployee">
                  {{ isCreatingEmployee ? t("employeeAdmin.actions.createEmployee") : t("employeeAdmin.actions.saveEmployee") }}
                </button>
                <button class="cta-button cta-secondary" type="button" @click="resetEmployeeDraft">
                  {{ t("employeeAdmin.actions.reset") }}
                </button>
              </div>
            </div>
          </form>
          </section>

          <section
            v-if="selectedEmployee && !isCreatingEmployee && activeDetailTab === 'app_access'"
            class="employee-admin-section employee-admin-tab-panel"
            data-testid="employee-tab-panel-app-access"
          >
            <div class="employee-admin-summary">
              <article class="employee-admin-summary__card">
                <span>{{ t("employeeAdmin.access.user") }}</span>
                <strong>{{ accessLink?.username || t("employeeAdmin.summary.none") }}</strong>
              </article>
              <article class="employee-admin-summary__card">
                <span>{{ t("employeeAdmin.access.email") }}</span>
                <strong>{{ accessLink?.email || t("employeeAdmin.summary.none") }}</strong>
              </article>
              <article class="employee-admin-summary__card">
                <span>{{ t("employeeAdmin.access.enabled") }}</span>
                <strong>{{ accessLink?.app_access_enabled ? t("employeeAdmin.access.enabledYes") : t("employeeAdmin.access.enabledNo") }}</strong>
              </article>
              <article class="employee-admin-summary__card">
                <span>{{ t("employeeAdmin.access.roleAssignment") }}</span>
                <strong>{{ accessLink?.role_assignment_active ? t("employeeAdmin.access.roleAssignmentYes") : t("employeeAdmin.access.roleAssignmentNo") }}</strong>
              </article>
              <article class="employee-admin-summary__card">
                <span>{{ t("employeeAdmin.access.manageFullName") }}</span>
                <strong>{{ accessLink?.full_name || t("employeeAdmin.summary.none") }}</strong>
              </article>
            </div>
            <div class="employee-admin-form employee-admin-form--structured">
              <section class="employee-admin-editor-intro">
                <div>
                  <p class="eyebrow">{{ t("employeeAdmin.access.eyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.access.title") }}</h4>
                </div>
                <p class="field-help">{{ t("employeeAdmin.access.lead") }}</p>
              </section>

              <section v-if="!hasLinkedAccess" class="employee-admin-form-section">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.access.stateCreateEyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.access.stateCreateTitle") }}</h4>
                  <p class="field-help">{{ t("employeeAdmin.access.stateCreateLead") }}</p>
                </div>
                <div class="employee-admin-form-section employee-admin-form-section--nested">
                  <div class="employee-admin-form-section__header">
                    <p class="eyebrow">{{ t("employeeAdmin.access.createEyebrow") }}</p>
                    <h4>{{ t("employeeAdmin.access.createTitle") }}</h4>
                    <p class="field-help">{{ t("employeeAdmin.access.createLead") }}</p>
                  </div>
                  <div class="employee-admin-form-grid employee-admin-form-grid--editor">
                    <label class="field-stack">
                      <span>{{ t("employeeAdmin.access.createUsername") }}</span>
                      <input v-model="accessCreateDraft.username" :disabled="!actionState.canManageAccess" />
                    </label>
                    <label class="field-stack">
                      <span>{{ t("employeeAdmin.access.createEmail") }}</span>
                      <input v-model="accessCreateDraft.email" :disabled="!actionState.canManageAccess" type="email" />
                    </label>
                    <label class="field-stack">
                      <span>{{ t("employeeAdmin.access.createPassword") }}</span>
                      <input v-model="accessCreateDraft.password" :disabled="!actionState.canManageAccess" type="password" />
                    </label>
                  </div>
                  <p class="field-help">{{ t("employeeAdmin.access.createHint") }}</p>
                  <div class="cta-row">
                    <button class="cta-button" type="button" :disabled="!actionState.canManageAccess" @click="createAccessUser">
                      {{ t("employeeAdmin.actions.createAccessUser") }}
                    </button>
                  </div>
                </div>
              </section>

              <section v-else class="employee-admin-form-section">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.access.stateLinkedEyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.access.stateLinkedTitle") }}</h4>
                  <p class="field-help">{{ t("employeeAdmin.access.stateLinkedLead") }}</p>
                </div>

                <div class="employee-admin-form-section employee-admin-form-section--nested">
                  <div class="employee-admin-form-section__header">
                    <p class="eyebrow">{{ t("employeeAdmin.access.manageEyebrow") }}</p>
                    <h4>{{ t("employeeAdmin.access.manageTitle") }}</h4>
                    <p class="field-help">{{ t("employeeAdmin.access.manageLead") }}</p>
                  </div>
                  <div class="employee-admin-form-grid employee-admin-form-grid--editor">
                    <label class="field-stack">
                      <span>{{ t("employeeAdmin.access.manageUsername") }}</span>
                      <input v-model="accessManageDraft.username" :disabled="!actionState.canManageAccess" />
                    </label>
                    <label class="field-stack">
                      <span>{{ t("employeeAdmin.access.manageEmail") }}</span>
                      <input v-model="accessManageDraft.email" :disabled="!actionState.canManageAccess" type="email" />
                    </label>
                    <label class="field-stack field-stack--wide">
                      <span>{{ t("employeeAdmin.access.manageFullName") }}</span>
                      <input v-model="accessManageDraft.full_name" :disabled="!actionState.canManageAccess" />
                    </label>
                  </div>
                  <div class="cta-row">
                    <button class="cta-button" type="button" :disabled="!actionState.canManageAccess" @click="updateAccessUser">
                      {{ t("employeeAdmin.actions.updateAccessUser") }}
                    </button>
                  </div>
                </div>

                <div class="employee-admin-form-section employee-admin-form-section--nested">
                  <div class="employee-admin-form-section__header">
                    <p class="eyebrow">{{ t("employeeAdmin.access.resetEyebrow") }}</p>
                    <h4>{{ t("employeeAdmin.access.resetTitle") }}</h4>
                    <p class="field-help">{{ t("employeeAdmin.access.resetLead") }}</p>
                  </div>
                  <div class="employee-admin-form-grid employee-admin-form-grid--editor">
                    <label class="field-stack">
                      <span>{{ t("employeeAdmin.access.resetPassword") }}</span>
                      <input v-model="accessResetDraft.password" :disabled="!actionState.canManageAccess" type="password" />
                    </label>
                  </div>
                  <div class="cta-row">
                    <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canManageAccess" @click="resetAccessPassword">
                      {{ t("employeeAdmin.actions.resetAccessPassword") }}
                    </button>
                  </div>
                </div>

                <div class="employee-admin-form-section employee-admin-form-section--nested">
                  <div class="employee-admin-form-section__header">
                    <p class="eyebrow">{{ t("employeeAdmin.access.detachEyebrow") }}</p>
                    <h4>{{ t("employeeAdmin.access.detachTitle") }}</h4>
                    <p class="field-help">{{ t("employeeAdmin.access.detachLead") }}</p>
                  </div>
                  <div class="cta-row">
                    <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canManageAccess || !accessLink?.user_id" @click="detachAccessUser">
                      {{ t("employeeAdmin.actions.detachAccessUser") }}
                    </button>
                  </div>
                </div>
              </section>

              <details class="employee-admin-advanced-access">
                <summary>
                  <span class="eyebrow">{{ t("employeeAdmin.access.advancedEyebrow") }}</span>
                  <strong>{{ t("employeeAdmin.access.advancedSummary") }}</strong>
                </summary>
                <p class="field-help">{{ t("employeeAdmin.access.advancedLead") }}</p>

                <section class="employee-admin-form-section employee-admin-form-section--nested">
                  <div class="employee-admin-form-section__header">
                    <p class="eyebrow">{{ t("employeeAdmin.access.attachEyebrow") }}</p>
                    <h4>{{ t("employeeAdmin.access.attachTitle") }}</h4>
                    <p class="field-help">{{ t("employeeAdmin.access.attachLead") }}</p>
                  </div>
                  <div class="employee-admin-form-grid employee-admin-form-grid--editor">
                    <label class="field-stack">
                      <span>{{ t("employeeAdmin.access.attachUserId") }}</span>
                      <input v-model="accessAttachDraft.user_id" :disabled="!actionState.canManageAccess" />
                    </label>
                    <label class="field-stack">
                      <span>{{ t("employeeAdmin.access.attachUsername") }}</span>
                      <input v-model="accessAttachDraft.username" :disabled="!actionState.canManageAccess" />
                    </label>
                    <label class="field-stack">
                      <span>{{ t("employeeAdmin.access.attachEmail") }}</span>
                      <input v-model="accessAttachDraft.email" :disabled="!actionState.canManageAccess" type="email" />
                    </label>
                  </div>
                  <div class="cta-row">
                    <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canManageAccess" @click="attachAccessUser">
                      {{ t("employeeAdmin.actions.attachAccessUser") }}
                    </button>
                  </div>
                </section>

                <section class="employee-admin-form-section employee-admin-form-section--nested">
                  <div class="employee-admin-form-section__header">
                    <p class="eyebrow">{{ t("employeeAdmin.access.reconcileEyebrow") }}</p>
                    <h4>{{ t("employeeAdmin.access.reconcileTitle") }}</h4>
                    <p class="field-help">{{ t("employeeAdmin.access.reconcileLead") }}</p>
                  </div>
                  <div class="cta-row">
                    <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canManageAccess || !accessLink?.user_id" @click="reconcileAccessUser">
                      {{ t("employeeAdmin.actions.reconcileAccessUser") }}
                    </button>
                  </div>
                </section>
              </details>
            </div>
          </section>

          <section
            v-if="selectedEmployee && !isCreatingEmployee && activeDetailTab === 'profile_photo'"
            class="employee-admin-section employee-admin-tab-panel"
            data-testid="employee-tab-panel-profile-photo"
          >
            <div class="employee-admin-form employee-admin-form--structured">
              <section class="employee-admin-editor-intro">
                <div>
                  <p class="eyebrow">{{ t("employeeAdmin.photo.eyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.photo.title") }}</h4>
                </div>
                <p class="field-help">{{ t("employeeAdmin.photo.help") }}</p>
              </section>

              <section class="employee-admin-form-section">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.photo.manageEyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.photo.manageTitle") }}</h4>
                  <p class="field-help">{{ currentPhoto?.file_name || t("employeeAdmin.photo.empty") }}</p>
                </div>

                <div class="employee-admin-photo">
                  <div class="employee-admin-photo__preview">
                    <img v-if="photoPreviewUrl" :src="photoPreviewUrl" :alt="t('employeeAdmin.photo.alt')" />
                    <span v-else>{{ t("employeeAdmin.photo.empty") }}</span>
                  </div>
                  <div class="employee-admin-photo__controls">
                    <label class="field-stack field-stack--wide">
                      <span>{{ t("employeeAdmin.photo.fileLabel") }}</span>
                      <input :disabled="!actionState.canManagePhoto" type="file" accept="image/*" @change="onPhotoSelected" />
                    </label>
                    <div class="cta-row">
                      <button class="cta-button" type="button" :disabled="!pendingPhotoFile || !actionState.canManagePhoto" @click="submitPhoto">
                        {{ t("employeeAdmin.actions.uploadPhoto") }}
                      </button>
                      <button class="cta-button cta-secondary" type="button" :disabled="!currentPhoto?.current_version_no" @click="downloadDocument(currentPhoto)">
                        {{ t("employeeAdmin.actions.downloadPhoto") }}
                      </button>
                    </div>
                  </div>
                </div>
              </section>
            </div>
          </section>

          <section
            v-if="selectedEmployee && !isCreatingEmployee && activeDetailTab === 'qualifications'"
            class="employee-admin-section employee-admin-tab-panel"
            data-testid="employee-tab-panel-qualifications"
          >
            <div class="employee-admin-form employee-admin-form--structured">
              <section class="employee-admin-editor-intro">
                <div>
                  <p class="eyebrow">{{ t("employeeAdmin.qualifications.eyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.qualifications.title") }}</h4>
                </div>
                <p class="field-help">{{ t("employeeAdmin.qualifications.lead") }}</p>
              </section>

              <section class="employee-admin-form-section">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.qualifications.registerEyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.qualifications.registerTitle") }}</h4>
                </div>
                <div v-if="employeeQualifications.length" class="employee-admin-record-list">
                  <button
                    v-for="qualification in employeeQualifications"
                    :key="qualification.id"
                    type="button"
                    class="employee-admin-record"
                    :class="{ selected: qualification.id === editingQualificationId }"
                    @click="editQualification(qualification)"
                  >
                    <div class="employee-admin-record__body">
                      <strong>
                        {{ qualification.qualification_type?.label || qualification.function_type?.label || qualification.certificate_no || t("employeeAdmin.summary.none") }}
                      </strong>
                      <span class="employee-admin-record__meta">
                        {{ qualification.record_kind === "function" ? t("employeeAdmin.readiness.recordKindFunction") : t("employeeAdmin.readiness.recordKindQualification") }}
                        ·
                        {{ qualification.issued_at || t("employeeAdmin.summary.none") }}
                        ·
                        {{ qualification.valid_until || t("employeeAdmin.summary.none") }}
                      </span>
                    </div>
                    <StatusBadge :status="qualification.status" />
                  </button>
                </div>
                <p v-else class="employee-admin-list-empty">{{ t("employeeAdmin.qualifications.empty") }}</p>
              </section>

              <form class="employee-admin-form-section employee-admin-inline-form" @submit.prevent="submitQualification">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.qualifications.editorEyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.qualifications.editorTitle") }}</h4>
                </div>
                <div class="employee-admin-form-grid employee-admin-form-grid--editor">
                  <label class="field-stack">
                    <span>{{ t("employeeAdmin.fields.recordKind") }}</span>
                    <select v-model="qualificationDraft.record_kind" :disabled="!actionState.canManageQualifications">
                      <option v-for="option in readinessRecordKindOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
                    </select>
                  </label>
                  <label v-if="qualificationDraft.record_kind === 'function'" class="field-stack">
                    <span>{{ t("employeeAdmin.fields.functionType") }}</span>
                    <select
                      v-model="qualificationDraft.function_type_id"
                      :disabled="!actionState.canManageQualifications || employeeFunctionTypeOptions.length === 0"
                    >
                      <option value="">{{ t("employeeAdmin.qualifications.functionTypePlaceholder") }}</option>
                      <option v-for="option in employeeFunctionTypeOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
                    </select>
                    <span v-if="employeeFunctionTypeOptions.length === 0" class="field-help">{{ t("employeeAdmin.qualifications.functionTypeEmptyHint") }}</span>
                  </label>
                  <label v-else class="field-stack">
                    <span>{{ t("employeeAdmin.fields.qualificationType") }}</span>
                    <select
                      v-model="qualificationDraft.qualification_type_id"
                      :disabled="!actionState.canManageQualifications || employeeQualificationTypeOptions.length === 0"
                    >
                      <option value="">{{ t("employeeAdmin.qualifications.qualificationTypePlaceholder") }}</option>
                      <option v-for="option in employeeQualificationTypeOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
                    </select>
                    <span v-if="employeeQualificationTypeOptions.length === 0" class="field-help">{{ t("employeeAdmin.qualifications.qualificationTypeEmptyHint") }}</span>
                  </label>
                  <label class="field-stack">
                    <span>{{ t("employeeAdmin.fields.certificateNo") }}</span>
                    <input v-model="qualificationDraft.certificate_no" :disabled="!actionState.canManageQualifications" />
                  </label>
                  <label class="field-stack">
                    <span>{{ t("employeeAdmin.fields.issuedAt") }}</span>
                    <input v-model="qualificationDraft.issued_at" :disabled="!actionState.canManageQualifications" type="date" />
                  </label>
                  <label class="field-stack">
                    <span>{{ t("employeeAdmin.fields.validUntil") }}</span>
                    <input v-model="qualificationDraft.valid_until" :disabled="!actionState.canManageQualifications" type="date" />
                  </label>
                  <label class="field-stack">
                    <span>{{ t("employeeAdmin.fields.issuingAuthority") }}</span>
                    <input v-model="qualificationDraft.issuing_authority" :disabled="!actionState.canManageQualifications" />
                  </label>
                  <label class="field-stack field-stack--wide">
                    <span>{{ t("employeeAdmin.fields.notes") }}</span>
                    <textarea v-model="qualificationDraft.notes" :disabled="!actionState.canManageQualifications" rows="3" />
                  </label>
                </div>
                <label class="employee-admin-checkbox">
                  <input v-model="qualificationDraft.granted_internally" :disabled="!actionState.canManageQualifications" type="checkbox" />
                  <span>{{ t("employeeAdmin.fields.grantedInternally") }}</span>
                </label>
                <div class="cta-row">
                  <button class="cta-button" type="submit" :disabled="!actionState.canManageQualifications">
                    {{ editingQualificationId ? t("employeeAdmin.actions.saveQualification") : t("employeeAdmin.actions.createQualification") }}
                  </button>
                  <button class="cta-button cta-secondary" type="button" @click="resetQualificationDraft">
                    {{ t("employeeAdmin.actions.resetQualification") }}
                  </button>
                </div>
              </form>

              <section class="employee-admin-form-section">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.qualifications.proofEyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.qualifications.proofTitle") }}</h4>
                </div>
                <p v-if="selectedQualification" class="field-help">
                  {{ t("employeeAdmin.qualifications.proofLead") }}: {{ selectedQualification.qualification_type?.label || selectedQualification.function_type?.label || selectedQualification.id }}
                </p>
                <p v-else class="employee-admin-list-empty">{{ t("employeeAdmin.qualifications.proofEmpty") }}</p>
                <div v-if="selectedQualificationProofs.length" class="employee-admin-record-list">
                  <article v-for="proof in selectedQualificationProofs" :key="`${proof.document_id}-${proof.current_version_no || 0}`" class="employee-admin-record employee-admin-record--static">
                    <div class="employee-admin-record__body">
                      <strong>{{ proof.title }}</strong>
                      <span class="employee-admin-record__meta">{{ proof.file_name || t("employeeAdmin.summary.none") }} · v{{ proof.current_version_no || 0 }}</span>
                    </div>
                    <div class="employee-admin-record__actions">
                      <button class="cta-button cta-secondary" type="button" :disabled="!proof.current_version_no" @click="downloadDocument(proof)">
                        {{ t("employeeAdmin.actions.downloadDocument") }}
                      </button>
                    </div>
                  </article>
                </div>
                <form v-if="selectedQualification" class="employee-admin-form" @submit.prevent="submitQualificationProof">
                  <div class="employee-admin-form-grid employee-admin-form-grid--editor">
                    <label class="field-stack">
                      <span>{{ t("employeeAdmin.fields.documentTitle") }}</span>
                      <input v-model="qualificationProofDraft.title" :disabled="!actionState.canManageQualifications" />
                    </label>
                    <label class="field-stack field-stack--wide">
                      <span>{{ t("employeeAdmin.fields.proofFile") }}</span>
                      <input :disabled="!actionState.canManageQualifications" type="file" @change="onQualificationProofSelected" />
                    </label>
                  </div>
                  <div class="cta-row">
                    <button class="cta-button cta-secondary" type="submit" :disabled="!actionState.canManageQualifications || !pendingQualificationProofFile">
                      {{ t("employeeAdmin.actions.uploadQualificationProof") }}
                    </button>
                  </div>
                </form>
              </section>
            </div>
          </section>

          <section
            v-if="selectedEmployee && !isCreatingEmployee && activeDetailTab === 'credentials'"
            class="employee-admin-section employee-admin-tab-panel"
            data-testid="employee-tab-panel-credentials"
          >
            <div class="employee-admin-form employee-admin-form--structured">
              <section class="employee-admin-editor-intro">
                <div>
                  <p class="eyebrow">{{ t("employeeAdmin.credentials.eyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.credentials.title") }}</h4>
                </div>
                <p class="field-help">{{ t("employeeAdmin.credentials.lead") }}</p>
              </section>

              <section class="employee-admin-form-section">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.credentials.registerEyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.credentials.registerTitle") }}</h4>
                </div>
                <div v-if="employeeCredentials.length" class="employee-admin-record-list">
                  <article
                    v-for="credential in employeeCredentials"
                    :key="credential.id"
                    class="employee-admin-record"
                    :class="{ selected: credential.id === editingCredentialId }"
                  >
                    <button type="button" class="employee-admin-record__body employee-admin-record__button" @click="editCredential(credential)">
                      <strong>{{ credential.credential_no }}</strong>
                      <span class="employee-admin-record__meta">{{ credential.credential_type }} · {{ credential.valid_from }} · {{ credential.valid_until || t("employeeAdmin.summary.none") }}</span>
                    </button>
                    <div class="employee-admin-record__actions">
                      <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canManageCredentials" @click="issueCredentialBadge(credential)">
                        {{ t("employeeAdmin.actions.issueCredentialBadge") }}
                      </button>
                      <StatusBadge :status="credential.status" />
                    </div>
                  </article>
                </div>
                <p v-else class="employee-admin-list-empty">{{ t("employeeAdmin.credentials.empty") }}</p>
              </section>

              <form class="employee-admin-form-section employee-admin-inline-form" @submit.prevent="submitCredential">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.credentials.editorEyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.credentials.editorTitle") }}</h4>
                </div>
                <div class="employee-admin-form-grid employee-admin-form-grid--editor">
                  <label class="field-stack">
                    <span>{{ t("employeeAdmin.fields.credentialNo") }}</span>
                    <input v-model="credentialDraft.credential_no" :disabled="!actionState.canManageCredentials || !!editingCredentialId" />
                  </label>
                  <label class="field-stack">
                    <span>{{ t("employeeAdmin.fields.credentialType") }}</span>
                    <select v-model="credentialDraft.credential_type" :disabled="!actionState.canManageCredentials || !!editingCredentialId">
                      <option value="">{{ t("employeeAdmin.credentials.credentialTypePlaceholder") }}</option>
                      <option v-for="option in employeeCredentialTypeOptions" :key="option.value" :value="option.value">
                        {{ option.label }}
                      </option>
                    </select>
                  </label>
                  <label class="field-stack">
                    <span>{{ t("employeeAdmin.fields.encodedValue") }}</span>
                    <input v-model="credentialDraft.encoded_value" :disabled="!actionState.canManageCredentials" />
                    <p class="field-help">{{ t("employeeAdmin.credentials.encodedValueHelp") }}</p>
                  </label>
                  <label class="field-stack">
                    <span>{{ t("employeeAdmin.fields.validFrom") }}</span>
                    <input v-model="credentialDraft.valid_from" :disabled="!actionState.canManageCredentials" type="date" />
                  </label>
                  <label class="field-stack">
                    <span>{{ t("employeeAdmin.fields.validUntil") }}</span>
                    <input v-model="credentialDraft.valid_until" :disabled="!actionState.canManageCredentials" type="date" />
                  </label>
                  <label class="field-stack field-stack--wide">
                    <span>{{ t("employeeAdmin.fields.notes") }}</span>
                    <textarea v-model="credentialDraft.notes" :disabled="!actionState.canManageCredentials" rows="3" />
                  </label>
                </div>
                <div class="cta-row">
                  <button class="cta-button" type="submit" :disabled="!actionState.canManageCredentials">
                    {{ editingCredentialId ? t("employeeAdmin.actions.saveCredential") : t("employeeAdmin.actions.createCredential") }}
                  </button>
                  <button class="cta-button cta-secondary" type="button" @click="resetCredentialDraft">
                    {{ t("employeeAdmin.actions.resetCredential") }}
                  </button>
                </div>
              </form>
            </div>
          </section>

          <section
            v-if="selectedEmployee && !isCreatingEmployee && activeDetailTab === 'availability'"
            class="employee-admin-section employee-admin-tab-panel"
            data-testid="employee-tab-panel-availability"
          >
            <div class="employee-admin-form employee-admin-form--structured">
              <section class="employee-admin-editor-intro">
                <div>
                  <p class="eyebrow">{{ t("employeeAdmin.availability.eyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.availability.title") }}</h4>
                </div>
                <p class="field-help">{{ t("employeeAdmin.availability.lead") }}</p>
              </section>

              <section class="employee-admin-form-section">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.availability.registerEyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.availability.registerTitle") }}</h4>
                </div>
                <div v-if="employeeAvailabilityRules.length" class="employee-admin-record-list">
                  <button
                    v-for="rule in employeeAvailabilityRules"
                    :key="rule.id"
                    type="button"
                    class="employee-admin-record"
                    :class="{ selected: rule.id === editingAvailabilityRuleId }"
                    @click="editAvailabilityRule(rule)"
                  >
                    <div class="employee-admin-record__body">
                      <strong>{{ rule.rule_kind }}</strong>
                      <span class="employee-admin-record__meta">{{ toLocalDateTimeInput(rule.starts_at) }} · {{ toLocalDateTimeInput(rule.ends_at) }}</span>
                    </div>
                    <StatusBadge :status="rule.status" />
                  </button>
                </div>
                <p v-else class="employee-admin-list-empty">{{ t("employeeAdmin.availability.empty") }}</p>
              </section>

              <form class="employee-admin-form-section employee-admin-inline-form" @submit.prevent="submitAvailabilityRule">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.availability.editorEyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.availability.editorTitle") }}</h4>
                </div>
                <div class="employee-admin-form-grid employee-admin-form-grid--editor">
                  <label class="field-stack">
                    <span>{{ t("employeeAdmin.fields.ruleKind") }}</span>
                    <select v-model="availabilityDraft.rule_kind" :disabled="!actionState.canManageAvailability">
                      <option value="">{{ t("employeeAdmin.availability.ruleKindPlaceholder") }}</option>
                      <option v-for="option in employeeAvailabilityRuleKindOptions" :key="option.value" :value="option.value">
                        {{ option.label }}
                      </option>
                    </select>
                  </label>
                  <label class="field-stack">
                    <span>{{ t("employeeAdmin.fields.startsAt") }}</span>
                    <input v-model="availabilityDraft.starts_at" :disabled="!actionState.canManageAvailability" type="datetime-local" />
                  </label>
                  <label class="field-stack">
                    <span>{{ t("employeeAdmin.fields.endsAt") }}</span>
                    <input v-model="availabilityDraft.ends_at" :disabled="!actionState.canManageAvailability" type="datetime-local" />
                  </label>
                  <label class="field-stack">
                    <span>{{ t("employeeAdmin.fields.recurrenceType") }}</span>
                    <select v-model="availabilityDraft.recurrence_type" :disabled="!actionState.canManageAvailability">
                      <option v-for="option in availabilityRecurrenceOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
                    </select>
                  </label>
                  <div v-if="availabilityDraft.recurrence_type === 'weekly'" class="field-stack field-stack--wide">
                    <span>{{ t("employeeAdmin.fields.weekdays") }}</span>
                    <div class="employee-admin-weekday-grid">
                      <label v-for="option in weekdayOptions" :key="option.value" class="employee-admin-checkbox">
                        <input
                          :checked="availabilityDraft.weekday_indexes.includes(option.value)"
                          :disabled="!actionState.canManageAvailability"
                          type="checkbox"
                          @change="toggleAvailabilityWeekday(option.value, ($event.target as HTMLInputElement).checked)"
                        />
                        <span>{{ option.label }}</span>
                      </label>
                    </div>
                    <p class="field-help">{{ buildWeekdayMask(availabilityDraft.weekday_indexes) }}</p>
                  </div>
                  <label class="field-stack field-stack--wide">
                    <span>{{ t("employeeAdmin.fields.notes") }}</span>
                    <textarea v-model="availabilityDraft.notes" :disabled="!actionState.canManageAvailability" rows="3" />
                  </label>
                </div>
                <div class="cta-row">
                  <button class="cta-button" type="submit" :disabled="!actionState.canManageAvailability">
                    {{ editingAvailabilityRuleId ? t("employeeAdmin.actions.saveAvailability") : t("employeeAdmin.actions.createAvailability") }}
                  </button>
                  <button class="cta-button cta-secondary" type="button" @click="resetAvailabilityDraft">
                    {{ t("employeeAdmin.actions.resetAvailability") }}
                  </button>
                </div>
              </form>
            </div>
          </section>

          <section
            v-if="selectedEmployee && !isCreatingEmployee && canReadPrivate && activeDetailTab === 'absences'"
            class="employee-admin-section employee-admin-tab-panel"
            data-testid="employee-tab-panel-absences"
          >
            <div class="employee-admin-form employee-admin-form--structured">
              <section class="employee-admin-editor-intro">
                <div>
                  <p class="eyebrow">{{ t("employeeAdmin.absences.eyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.absences.title") }}</h4>
                </div>
                <p class="field-help">{{ t("employeeAdmin.absences.lead") }}</p>
              </section>

              <section class="employee-admin-form-section">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.absences.registerEyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.absences.registerTitle") }}</h4>
                </div>
                <div v-if="employeeAbsences.length" class="employee-admin-record-list">
                  <button
                    v-for="absence in employeeAbsences"
                    :key="absence.id"
                    type="button"
                    class="employee-admin-record"
                    :class="{ selected: absence.id === editingAbsenceId }"
                    @click="editAbsence(absence)"
                  >
                    <div class="employee-admin-record__body">
                      <strong>{{ absence.absence_type }}</strong>
                      <span class="employee-admin-record__meta">{{ absence.starts_on }} · {{ absence.ends_on }} · {{ absence.quantity_days }}</span>
                    </div>
                    <StatusBadge :status="absence.status" />
                  </button>
                </div>
                <p v-else class="employee-admin-list-empty">{{ t("employeeAdmin.absences.empty") }}</p>
              </section>

              <form class="employee-admin-form-section employee-admin-inline-form" @submit.prevent="submitAbsence">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.absences.editorEyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.absences.editorTitle") }}</h4>
                </div>
                <div class="employee-admin-form-grid employee-admin-form-grid--editor">
                  <label class="field-stack">
                    <span>{{ t("employeeAdmin.fields.absenceType") }}</span>
                    <input v-model="absenceDraft.absence_type" :disabled="!actionState.canManageAbsences" />
                  </label>
                  <label class="field-stack">
                    <span>{{ t("employeeAdmin.fields.startsOn") }}</span>
                    <input v-model="absenceDraft.starts_on" :disabled="!actionState.canManageAbsences" type="date" />
                  </label>
                  <label class="field-stack">
                    <span>{{ t("employeeAdmin.fields.endsOn") }}</span>
                    <input v-model="absenceDraft.ends_on" :disabled="!actionState.canManageAbsences" type="date" />
                  </label>
                  <label v-if="editingAbsenceId" class="field-stack">
                    <span>{{ t("employeeAdmin.fields.decisionNote") }}</span>
                    <input v-model="absenceDraft.decision_note" :disabled="!actionState.canManageAbsences" />
                  </label>
                  <label class="field-stack field-stack--wide">
                    <span>{{ t("employeeAdmin.fields.notes") }}</span>
                    <textarea v-model="absenceDraft.notes" :disabled="!actionState.canManageAbsences" rows="3" />
                  </label>
                </div>
                <div class="cta-row">
                  <button class="cta-button" type="submit" :disabled="!actionState.canManageAbsences">
                    {{ editingAbsenceId ? t("employeeAdmin.actions.saveAbsence") : t("employeeAdmin.actions.createAbsence") }}
                  </button>
                  <button class="cta-button cta-secondary" type="button" @click="resetAbsenceDraft">
                    {{ t("employeeAdmin.actions.resetAbsence") }}
                  </button>
                </div>
              </form>
            </div>
          </section>

          <section
            v-if="selectedEmployee && !isCreatingEmployee && activeDetailTab === 'notes'"
            class="employee-admin-section employee-admin-tab-panel"
            data-testid="employee-tab-panel-notes"
          >
            <div class="employee-admin-form employee-admin-form--structured">
              <section class="employee-admin-editor-intro">
                <div>
                  <p class="eyebrow">{{ t("employeeAdmin.notes.eyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.notes.title") }}</h4>
                </div>
                <p class="field-help">{{ t("employeeAdmin.notes.lead") }}</p>
              </section>

              <section class="employee-admin-form-section">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.notes.registerEyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.notes.registerTitle") }}</h4>
                </div>

                <div v-if="employeeNotes.length" class="employee-admin-record-list">
                  <button
                    v-for="note in employeeNotes"
                    :key="note.id"
                    type="button"
                    class="employee-admin-record"
                    :class="{ selected: note.id === editingNoteId }"
                    @click="editNote(note)"
                  >
                    <div class="employee-admin-record__body">
                      <strong>{{ note.title }}</strong>
                      <span class="employee-admin-record__meta">{{ t(`employeeAdmin.noteType.${note.note_type}` as never) }} · {{ note.reminder_at || t("employeeAdmin.summary.none") }}</span>
                    </div>
                    <StatusBadge :status="note.completed_at ? 'active' : note.status" />
                  </button>
                </div>
                <p v-else class="employee-admin-list-empty">{{ t("employeeAdmin.notes.empty") }}</p>
              </section>

              <form class="employee-admin-form-section employee-admin-inline-form" @submit.prevent="submitNote">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.notes.editorEyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.notes.editorTitle") }}</h4>
                </div>
                <div class="employee-admin-form-grid employee-admin-form-grid--editor">
                  <label class="field-stack">
                    <span>{{ t("employeeAdmin.fields.noteType") }}</span>
                    <select v-model="noteDraft.note_type" :disabled="!actionState.canManageNotes">
                      <option value="operational_note">{{ t("employeeAdmin.noteType.operational_note") }}</option>
                      <option value="positive_activity">{{ t("employeeAdmin.noteType.positive_activity") }}</option>
                      <option value="reminder">{{ t("employeeAdmin.noteType.reminder") }}</option>
                    </select>
                  </label>
                  <label class="field-stack">
                    <span>{{ t("employeeAdmin.fields.noteTitle") }}</span>
                    <input v-model="noteDraft.title" :disabled="!actionState.canManageNotes" required />
                  </label>
                  <label class="field-stack">
                    <span>{{ t("employeeAdmin.fields.reminderAt") }}</span>
                    <input v-model="noteDraft.reminder_at" :disabled="!actionState.canManageNotes" type="date" />
                  </label>
                  <label class="field-stack">
                    <span>{{ t("employeeAdmin.fields.completedAt") }}</span>
                    <input v-model="noteDraft.completed_at" :disabled="!actionState.canManageNotes" type="date" />
                  </label>
                  <label class="field-stack field-stack--wide">
                    <span>{{ t("employeeAdmin.fields.noteBody") }}</span>
                    <textarea v-model="noteDraft.body" :disabled="!actionState.canManageNotes" rows="3" />
                  </label>
                </div>
                <div class="cta-row">
                  <button class="cta-button" type="submit" :disabled="!actionState.canManageNotes">
                    {{ editingNoteId ? t("employeeAdmin.actions.saveNote") : t("employeeAdmin.actions.createNote") }}
                  </button>
                  <button class="cta-button cta-secondary" type="button" @click="resetNoteDraft">
                    {{ t("employeeAdmin.actions.resetNote") }}
                  </button>
                </div>
              </form>
            </div>
          </section>

          <section
            v-if="selectedEmployee && !isCreatingEmployee && activeDetailTab === 'groups'"
            class="employee-admin-section employee-admin-tab-panel"
            data-testid="employee-tab-panel-groups"
          >
            <div class="employee-admin-form employee-admin-form--structured">
              <section class="employee-admin-editor-intro">
                <div>
                  <p class="eyebrow">{{ t("employeeAdmin.groups.eyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.groups.title") }}</h4>
                </div>
                <p class="field-help">{{ t("employeeAdmin.groups.lead") }}</p>
              </section>

              <section class="employee-admin-form-section">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.groups.catalogEyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.groups.catalogTitle") }}</h4>
                </div>
                <div class="employee-admin-form-grid employee-admin-form-grid--editor">
                  <label class="field-stack">
                    <span>{{ t("employeeAdmin.fields.groupCode") }}</span>
                    <input v-model="groupDraft.code" :disabled="!actionState.canManageGroups" />
                  </label>
                  <label class="field-stack">
                    <span>{{ t("employeeAdmin.fields.groupName") }}</span>
                    <input v-model="groupDraft.name" :disabled="!actionState.canManageGroups" />
                  </label>
                  <label class="field-stack field-stack--wide">
                    <span>{{ t("employeeAdmin.fields.groupDescription") }}</span>
                    <input v-model="groupDraft.description" :disabled="!actionState.canManageGroups" />
                  </label>
                </div>
                <div class="cta-row">
                  <button class="cta-button" type="button" :disabled="!actionState.canManageGroups" @click="submitGroup">
                    {{ editingGroupId ? t("employeeAdmin.actions.saveGroup") : t("employeeAdmin.actions.createGroup") }}
                  </button>
                  <button class="cta-button cta-secondary" type="button" @click="resetGroupDraft">
                    {{ t("employeeAdmin.actions.resetGroup") }}
                  </button>
                </div>
              </section>

              <section class="employee-admin-form-section">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.groups.assignEyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.groups.assignTitle") }}</h4>
                </div>
                <div class="employee-admin-form-grid employee-admin-form-grid--editor">
                  <label class="field-stack">
                    <span>{{ t("employeeAdmin.fields.assignGroup") }}</span>
                    <select v-model="membershipDraft.group_id" :disabled="!actionState.canManageGroups">
                      <option value="">{{ t("employeeAdmin.groups.selectPlaceholder") }}</option>
                      <option v-for="group in employeeGroups" :key="group.id" :value="group.id">{{ group.code }} · {{ group.name }}</option>
                    </select>
                  </label>
                  <label class="field-stack">
                    <span>{{ t("employeeAdmin.fields.validFrom") }}</span>
                    <input v-model="membershipDraft.valid_from" :disabled="!actionState.canManageGroups" type="date" />
                  </label>
                  <label class="field-stack">
                    <span>{{ t("employeeAdmin.fields.validUntil") }}</span>
                    <input v-model="membershipDraft.valid_until" :disabled="!actionState.canManageGroups" type="date" />
                  </label>
                  <label class="field-stack field-stack--wide">
                    <span>{{ t("employeeAdmin.fields.membershipNotes") }}</span>
                    <input v-model="membershipDraft.notes" :disabled="!actionState.canManageGroups" />
                  </label>
                </div>
                <div class="cta-row">
                  <button class="cta-button" type="button" :disabled="!actionState.canManageGroups || !membershipDraft.group_id" @click="submitMembership">
                    {{ editingMembershipId ? t("employeeAdmin.actions.saveMembership") : t("employeeAdmin.actions.assignGroup") }}
                  </button>
                  <button class="cta-button cta-secondary" type="button" @click="resetMembershipDraft">
                    {{ t("employeeAdmin.actions.resetMembership") }}
                  </button>
                </div>
              </section>

              <section class="employee-admin-form-section">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.groups.currentEyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.groups.currentTitle") }}</h4>
                </div>
                <div v-if="selectedEmployee?.group_memberships.length" class="employee-admin-record-list">
                  <button
                    v-for="membership in selectedEmployee.group_memberships"
                    :key="membership.id"
                    type="button"
                    class="employee-admin-record"
                    :class="{ selected: membership.id === editingMembershipId }"
                    @click="editMembership(membership)"
                  >
                    <div class="employee-admin-record__body">
                      <strong>{{ membership.group?.name || membership.group_id }}</strong>
                      <span class="employee-admin-record__meta">{{ membership.valid_from }} · {{ membership.valid_until || t("employeeAdmin.summary.none") }}</span>
                    </div>
                    <StatusBadge :status="membership.status" />
                  </button>
                </div>
                <p v-else class="employee-admin-list-empty">{{ t("employeeAdmin.groups.empty") }}</p>
              </section>
            </div>
          </section>

          <section
            v-if="selectedEmployee && !isCreatingEmployee && canReadPrivate && activeDetailTab === 'private_profile'"
            class="employee-admin-section employee-admin-tab-panel"
            data-testid="employee-tab-panel-private-profile"
          >
            <form class="employee-admin-form employee-admin-form--structured" @submit.prevent="submitPrivateProfile">
              <section class="employee-admin-editor-intro">
                <div>
                  <p class="eyebrow">{{ t("employeeAdmin.privateProfile.eyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.privateProfile.title") }}</h4>
                </div>
                <p class="field-help">{{ t("employeeAdmin.privateProfile.lead") }}</p>
              </section>

              <section class="employee-admin-form-section">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.privateProfile.identityEyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.privateProfile.identityTitle") }}</h4>
                </div>
                <div class="employee-admin-form-grid employee-admin-form-grid--editor">
                  <label class="field-stack">
                    <span>{{ t("employeeAdmin.fields.birthDate") }}</span>
                    <input v-model="privateProfileDraft.birth_date" :disabled="!actionState.canManagePrivateProfile" type="date" />
                  </label>
                  <label class="field-stack">
                    <span>{{ t("employeeAdmin.fields.placeOfBirth") }}</span>
                    <input v-model="privateProfileDraft.place_of_birth" :disabled="!actionState.canManagePrivateProfile" />
                  </label>
                  <label class="field-stack">
                    <span>{{ t("employeeAdmin.fields.nationalityCountryCode") }}</span>
                    <input
                      v-model="privateProfileDraft.nationality_country_code"
                      :disabled="!actionState.canManagePrivateProfile"
                      maxlength="2"
                    />
                  </label>
                </div>
              </section>

              <div class="employee-admin-form-actions">
                <div>
                  <p class="eyebrow">{{ t("employeeAdmin.privateProfile.actionsEyebrow") }}</p>
                  <strong>{{ t("employeeAdmin.privateProfile.actionsTitle") }}</strong>
                </div>
                <div class="cta-row">
                  <button class="cta-button" type="submit" :disabled="!actionState.canManagePrivateProfile">
                    {{ t("employeeAdmin.actions.savePrivateProfile") }}
                  </button>
                  <button class="cta-button cta-secondary" type="button" @click="resetPrivateProfileDraft">
                    {{ t("employeeAdmin.actions.resetPrivateProfile") }}
                  </button>
                </div>
              </div>
            </form>
          </section>

          <section
            v-if="selectedEmployee && !isCreatingEmployee && canReadPrivate && activeDetailTab === 'addresses'"
            class="employee-admin-section employee-admin-tab-panel"
            data-testid="employee-tab-panel-addresses"
          >
            <div class="employee-admin-form employee-admin-form--structured">
              <section class="employee-admin-editor-intro">
                <div>
                  <p class="eyebrow">{{ t("employeeAdmin.addresses.eyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.addresses.title") }}</h4>
                </div>
                <p class="field-help">{{ t("employeeAdmin.addresses.lead") }}</p>
              </section>

              <section class="employee-admin-form-section">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.addresses.currentEyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.addresses.currentTitle") }}</h4>
                </div>
                <div v-if="currentEmployeeAddress" class="employee-admin-record employee-admin-record--static">
                  <div class="employee-admin-record__body">
                    <strong>{{ currentAddressSummary || currentEmployeeAddress.address_id }}</strong>
                    <span class="employee-admin-record__meta">
                      {{ currentEmployeeAddress.valid_from }} · {{ currentEmployeeAddress.valid_to || t("employeeAdmin.summary.none") }}
                    </span>
                  </div>
                  <StatusBadge :status="currentEmployeeAddress.status" />
                </div>
                <p v-else class="employee-admin-list-empty">{{ t("employeeAdmin.addresses.currentEmpty") }}</p>
              </section>

              <form class="employee-admin-form-section" @submit.prevent="submitAddress">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.addresses.editorEyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.addresses.editorTitle") }}</h4>
                </div>
                <p class="field-help">{{ t("employeeAdmin.addresses.editorLead") }}</p>
                <div class="employee-admin-form-grid employee-admin-form-grid--editor">
                  <label class="field-stack field-stack--wide">
                    <span>{{ t("customerAdmin.fields.streetLine1") }}</span>
                    <input v-model="addressDraft.street_line_1" :disabled="!actionState.canManageAddresses" />
                  </label>
                  <label class="field-stack field-stack--wide">
                    <span>{{ t("customerAdmin.fields.streetLine2") }}</span>
                    <input v-model="addressDraft.street_line_2" :disabled="!actionState.canManageAddresses" />
                  </label>
                  <label class="field-stack">
                    <span>{{ t("customerAdmin.fields.postalCode") }}</span>
                    <input v-model="addressDraft.postal_code" :disabled="!actionState.canManageAddresses" />
                  </label>
                  <label class="field-stack">
                    <span>{{ t("customerAdmin.fields.city") }}</span>
                    <input v-model="addressDraft.city" :disabled="!actionState.canManageAddresses" />
                  </label>
                  <label class="field-stack">
                    <span>{{ t("customerAdmin.fields.state") }}</span>
                    <input v-model="addressDraft.state_region" :disabled="!actionState.canManageAddresses" />
                  </label>
                  <label class="field-stack">
                    <span>{{ t("customerAdmin.fields.countryCode") }}</span>
                    <input v-model="addressDraft.country_code" :disabled="!actionState.canManageAddresses" maxlength="2" />
                  </label>
                  <label class="field-stack">
                    <span>{{ t("customerAdmin.fields.addressType") }}</span>
                    <select v-model="addressDraft.address_type" :disabled="!actionState.canManageAddresses">
                      <option value="home">{{ t("employeeAdmin.addresses.typeHome") }}</option>
                      <option value="mailing">{{ t("employeeAdmin.addresses.typeMailing") }}</option>
                    </select>
                  </label>
                  <label class="field-stack">
                    <span>{{ t("employeeAdmin.fields.validFrom") }}</span>
                    <input v-model="addressDraft.valid_from" :disabled="!actionState.canManageAddresses" type="date" />
                  </label>
                  <label class="field-stack">
                    <span>{{ t("employeeAdmin.fields.validUntil") }}</span>
                    <input
                      v-model="addressDraft.valid_to"
                      :disabled="!actionState.canManageAddresses || addressDraft.is_current"
                      type="date"
                    />
                  </label>
                  <label class="field-stack field-stack--wide">
                    <span>{{ t("employeeAdmin.fields.notes") }}</span>
                    <textarea v-model="addressDraft.notes" :disabled="!actionState.canManageAddresses" rows="3" />
                  </label>
                </div>
                <div class="employee-admin-checkbox">
                  <input
                    v-model="addressDraft.is_current"
                    :disabled="!actionState.canManageAddresses"
                    type="checkbox"
                    @change="onAddressCurrentToggle"
                  />
                  <span>{{ t("employeeAdmin.addresses.currentBadge") }}</span>
                </div>
                <div class="employee-admin-checkbox">
                  <input v-model="addressDraft.is_primary" :disabled="!actionState.canManageAddresses" type="checkbox" />
                  <span>{{ t("employeeAdmin.summary.currentAddress") }}</span>
                </div>
                <div class="cta-row">
                  <button
                    v-if="editingAddressId"
                    class="cta-button cta-secondary"
                    type="button"
                    :disabled="!actionState.canManageAddresses"
                    @click="resetAddressDraft"
                  >
                    {{ t("employeeAdmin.actions.addAddress") }}
                  </button>
                  <button class="cta-button" type="submit" :disabled="!actionState.canManageAddresses">
                    {{ editingAddressId ? t("employeeAdmin.actions.saveAddress") : t("employeeAdmin.actions.addAddress") }}
                  </button>
                  <button class="cta-button cta-secondary" type="button" @click="resetAddressDraft">
                    {{ t("employeeAdmin.actions.resetAddress") }}
                  </button>
                </div>
              </form>

              <section class="employee-admin-form-section">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.addresses.historyEyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.addresses.historyTitle") }}</h4>
                </div>
                <div v-if="employeeAddressTimeline.length" class="employee-admin-record-list">
                  <article v-for="addressRow in employeeAddressTimeline" :key="addressRow.id" class="employee-admin-record employee-admin-record--static">
                    <div class="employee-admin-record__body">
                      <strong>{{ addressRow.address?.street_line_1 || addressRow.address_id }}</strong>
                      <span class="employee-admin-record__meta">{{ addressRow.valid_from }} · {{ addressRow.valid_to || t("employeeAdmin.summary.none") }}</span>
                      <span class="employee-admin-record__meta">
                        {{ addressRow.address_type === "home" ? t("employeeAdmin.addresses.typeHome") : t("employeeAdmin.addresses.typeMailing") }}
                        ·
                        {{ addressRow.valid_to ? t("employeeAdmin.addresses.closedBadge") : t("employeeAdmin.addresses.currentBadge") }}
                      </span>
                    </div>
                    <div class="employee-admin-record__actions">
                      <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canManageAddresses" @click="editAddress(addressRow)">
                        {{ t("employeeAdmin.actions.editAddress") }}
                      </button>
                      <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canManageAddresses" @click="prepareAddressAsCurrent(addressRow)">
                        {{ t("employeeAdmin.actions.markCurrentAddress") }}
                      </button>
                      <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canManageAddresses" @click="prepareAddressValidityClose(addressRow)">
                        {{ t("employeeAdmin.actions.closeAddressValidity") }}
                      </button>
                      <StatusBadge :status="addressRow.status" />
                    </div>
                  </article>
                </div>
                <p v-else class="employee-admin-list-empty">{{ t("employeeAdmin.addresses.empty") }}</p>
              </section>
            </div>
          </section>

          <section
            v-if="selectedEmployee && !isCreatingEmployee && activeDetailTab === 'documents'"
            class="employee-admin-section employee-admin-tab-panel"
            data-testid="employee-tab-panel-documents"
          >
            <div class="employee-admin-form employee-admin-form--structured">
              <section class="employee-admin-editor-intro">
                <div>
                  <p class="eyebrow">{{ t("employeeAdmin.documents.eyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.documents.title") }}</h4>
                </div>
                <p class="field-help">{{ t("employeeAdmin.documents.lead") }}</p>
              </section>

              <section class="employee-admin-form-section">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.documents.libraryEyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.documents.libraryTitle") }}</h4>
                </div>
                <div v-if="employeeDocuments.length" class="employee-admin-record-list">
                  <article
                    v-for="document in employeeDocuments"
                    :key="document.document_id"
                    class="employee-admin-record"
                  >
                    <div class="employee-admin-record__body">
                      <strong>{{ document.title }}</strong>
                      <span class="employee-admin-record__meta">{{ document.label || t("employeeAdmin.summary.none") }} · {{ resolveEmployeeDocumentRelationLabel(document.relation_type) }}</span>
                      <span class="employee-admin-record__meta">
                        {{ document.file_name || t("employeeAdmin.summary.none") }}
                        ·
                        {{ document.content_type || t("employeeAdmin.summary.none") }}
                        ·
                        v{{ document.current_version_no || 0 }}
                      </span>
                      <span class="employee-admin-record__meta">{{ document.linked_at || t("employeeAdmin.summary.none") }}</span>
                    </div>
                    <div class="employee-admin-record__actions">
                      <button class="cta-button cta-secondary" type="button" :disabled="!document.current_version_no" @click="downloadDocument(document)">
                        {{ t("employeeAdmin.actions.downloadDocument") }}
                      </button>
                      <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canEdit" @click="useEmployeeDocumentForVersion(document)">
                        {{ t("employeeAdmin.actions.useDocumentForVersion") }}
                      </button>
                      <StatusBadge :status="document.current_version_no ? 'active' : 'inactive'" />
                    </div>
                  </article>
                </div>
                <p v-else class="employee-admin-list-empty">{{ t("employeeAdmin.documents.empty") }}</p>
              </section>

              <section class="employee-admin-form-section">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.documents.uploadEyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.documents.uploadTitle") }}</h4>
                </div>
                <p class="field-help">{{ t("employeeAdmin.documents.uploadLead") }}</p>
                <form class="employee-admin-form" @submit.prevent="submitEmployeeDocumentUpload">
                  <div class="employee-admin-form-grid">
                    <label class="field-stack">
                      <span>{{ t("employeeAdmin.fields.documentTitle") }}</span>
                      <input v-model="documentUploadDraft.title" required />
                    </label>
                    <label class="field-stack">
                      <span>{{ t("employeeAdmin.fields.documentLabel") }}</span>
                      <input v-model="documentUploadDraft.label" />
                    </label>
                    <label class="field-stack">
                      <span>{{ t("employeeAdmin.fields.documentRelationType") }}</span>
                      <select v-model="documentUploadDraft.relation_type">
                        <option v-for="option in employeeDocumentRelationOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
                      </select>
                    </label>
                    <label class="field-stack">
                      <span>{{ t("employeeAdmin.fields.documentTypeKey") }}</span>
                      <select v-model="documentUploadDraft.document_type_key">
                        <option v-for="option in employeeDocumentTypeOptions" :key="option.value || 'none'" :value="option.value">
                          {{ option.label }}
                        </option>
                      </select>
                      <span class="field-help">{{ t("employeeAdmin.documents.documentTypeHelp") }}</span>
                    </label>
                    <label class="field-stack field-stack--wide">
                      <span>{{ t("employeeAdmin.fields.documentFile") }}</span>
                      <input type="file" @change="onEmployeeDocumentSelected" />
                    </label>
                  </div>
                  <div class="cta-row">
                    <button class="cta-button" type="submit" :disabled="!actionState.canEdit || !pendingEmployeeDocumentFile">
                      {{ t("employeeAdmin.actions.uploadDocument") }}
                    </button>
                  </div>
                </form>
              </section>

              <section class="employee-admin-form-section">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.documents.linkEyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.documents.linkTitle") }}</h4>
                </div>
                <p class="field-help">{{ t("employeeAdmin.documents.linkLead") }}</p>
                <form class="employee-admin-form" @submit.prevent="submitEmployeeDocumentLink">
                  <div class="employee-admin-form-grid">
                    <label class="field-stack">
                      <span>{{ t("employeeAdmin.fields.documentId") }}</span>
                      <input v-model="documentLinkDraft.document_id" required />
                    </label>
                    <label class="field-stack">
                      <span>{{ t("employeeAdmin.fields.documentLabel") }}</span>
                      <input v-model="documentLinkDraft.label" />
                    </label>
                    <label class="field-stack">
                      <span>{{ t("employeeAdmin.fields.documentRelationType") }}</span>
                      <select v-model="documentLinkDraft.relation_type">
                        <option v-for="option in employeeDocumentRelationOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
                      </select>
                    </label>
                  </div>
                  <div class="cta-row">
                    <button class="cta-button cta-secondary" type="submit" :disabled="!actionState.canEdit">
                      {{ t("employeeAdmin.actions.linkDocument") }}
                    </button>
                  </div>
                </form>
              </section>

              <section class="employee-admin-form-section">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.documents.versionEyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.documents.versionTitle") }}</h4>
                </div>
                <p class="field-help">{{ t("employeeAdmin.documents.versionLead") }}</p>
                <p v-if="selectedEmployeeDocument" class="field-help">
                  {{ t("employeeAdmin.documents.selectedVersionTarget") }}: {{ selectedEmployeeDocument.title }}
                </p>
                <p v-else class="employee-admin-list-empty">{{ t("employeeAdmin.documents.versionEmpty") }}</p>
                <form class="employee-admin-form" @submit.prevent="submitEmployeeDocumentVersion">
                  <div class="employee-admin-form-grid">
                    <label class="field-stack">
                      <span>{{ t("employeeAdmin.fields.documentVersionTarget") }}</span>
                      <select v-model="selectedEmployeeDocumentId">
                        <option value="">{{ t("employeeAdmin.summary.none") }}</option>
                        <option v-for="document in employeeDocuments" :key="document.document_id" :value="document.document_id">
                          {{ document.title }}
                        </option>
                      </select>
                    </label>
                    <label class="field-stack field-stack--wide">
                      <span>{{ t("employeeAdmin.fields.documentFile") }}</span>
                      <input type="file" @change="onEmployeeDocumentVersionSelected" />
                    </label>
                  </div>
                  <div class="cta-row">
                    <button class="cta-button" type="submit" :disabled="!actionState.canEdit || !selectedEmployeeDocumentId || !pendingEmployeeDocumentVersionFile">
                      {{ t("employeeAdmin.actions.addDocumentVersion") }}
                    </button>
                  </div>
                </form>
              </section>
            </div>
          </section>
        </template>

        <section v-else class="employee-admin-empty">
          <p class="eyebrow">{{ t("employeeAdmin.detail.emptyEyebrow") }}</p>
          <h3>{{ t("employeeAdmin.detail.emptyTitle") }}</h3>
          <p>{{ t("employeeAdmin.detail.emptyBody") }}</p>
        </section>
      </section>
      </div>
    </SicherPlanLoadingOverlay>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";

import { listBranches, listMandates, type BranchRead, type MandateRead } from "@/api/coreAdmin";
import {
  addEmployeeDocumentVersion,
  attachEmployeeAccessUser,
  createEmployeeAbsence,
  createEmployeeAccessUser,
  createEmployeeAddress,
  createEmployeeAvailabilityRule,
  createEmployeeCredential,
  createEmployee,
  createEmployeeGroup,
  createEmployeeGroupMembership,
  createEmployeeNote,
  createEmployeeQualification,
  detachEmployeeAccessUser,
  downloadEmployeeDocument,
  EmployeeAdminApiError,
  exportEmployees,
  getEmployee,
  getEmployeeAccessLink,
  getEmployeePrivateProfile,
  getEmployeePhoto,
  importEmployeesDryRun,
  importEmployeesExecute,
  issueEmployeeCredentialBadgeOutput,
  linkEmployeeDocument,
  listEmployeeAbsences,
  listEmployeeAddresses,
  listEmployeeAvailabilityRules,
  listEmployeeCredentials,
  listEmployeeDocuments,
  listEmployeeGroups,
  listEmployeeNotes,
  listEmployeeQualificationProofs,
  listEmployeeQualifications,
  listEmployees,
  listFunctionTypes,
  listQualificationTypes,
  type EmployeeAbsenceCreatePayload,
  type EmployeeAbsenceRead,
  type EmployeeAbsenceUpdatePayload,
  reconcileEmployeeAccessUser,
  resetEmployeeAccessUserPassword,
  type EmployeeAvailabilityRuleCreatePayload,
  type EmployeeAvailabilityRuleRead,
  type EmployeeAvailabilityRuleUpdatePayload,
  type EmployeeCredentialBadgeIssuePayload,
  type EmployeeCredentialCreatePayload,
  type EmployeeCredentialRead,
  type EmployeeCredentialUpdatePayload,
  type EmployeeQualificationCreatePayload,
  type EmployeeQualificationProofRead,
  type EmployeeQualificationProofUploadPayload,
  type EmployeeQualificationRead,
  type EmployeeQualificationUpdatePayload,
  type FunctionTypeRead,
  updateEmployee,
  updateEmployeeAddress,
  updateEmployeeAccessUser,
  updateEmployeeAbsence,
  updateEmployeeAvailabilityRule,
  updateEmployeeCredential,
  updateEmployeeGroup,
  updateEmployeeGroupMembership,
  updateEmployeeNote,
  updateEmployeeQualification,
  uploadEmployeePhoto,
  uploadEmployeeQualificationProof,
  type QualificationTypeRead,
  type EmployeeAccessLinkRead,
  type EmployeeAccessResetPasswordRequest,
  type EmployeeAccessUpdateUserRequest,
  type EmployeeAddressHistoryCreatePayload,
  type EmployeeAddressHistoryRead,
  type EmployeeAddressHistoryUpdatePayload,
  type EmployeeDocumentLinkPayload,
  type EmployeeDocumentListItemRead,
  type EmployeeDocumentUploadPayload,
  type EmployeeDocumentVersionPayload,
  type EmployeeExportResult,
  type EmployeeGroupMembershipRead,
  type EmployeeGroupRead,
  type EmployeeImportDryRunResult,
  type EmployeeImportExecuteResult,
  type EmployeeListItem,
  type EmployeeNoteRead,
  type EmployeeOperationalRead,
  type EmployeePrivateProfileRead,
  type EmployeePrivateProfileUpdatePayload,
  type EmployeePrivateProfileWritePayload,
  type EmployeePhotoRead,
  updateEmployeePrivateProfile,
  uploadEmployeeDocument,
  upsertEmployeePrivateProfile,
} from "@/api/employeeAdmin";
import SicherPlanLoadingOverlay from "@/components/SicherPlanLoadingOverlay.vue";
import StatusBadge from "@/components/StatusBadge.vue";
import { useSicherPlanFeedback } from "@/composables/useSicherPlanFeedback";
import { useI18n } from "@/i18n";
import {
  buildEmployeeImportTemplateRows,
  buildEmployeeAbsencePayload,
  buildEmployeeAvailabilityPayload,
  EMPLOYEE_AVAILABILITY_RULE_KIND_OPTIONS,
  buildEmployeeCredentialPayload,
  buildEmployeeDocumentUploadPayload,
  buildEmployeeOperationalPayload,
  buildEmployeePrivateProfilePayload,
  buildEmployeeQualificationPayload,
  buildWeekdayMask,
  deriveEmployeeActionState,
  EMPLOYEE_CREDENTIAL_TYPE_OPTIONS,
  EMPLOYEE_DOCUMENT_TYPE_OPTIONS,
  filterMandatesForBranch,
  formatEmployeeStructureLabel,
  mapEmployeeApiMessage,
  normalizeOptionalText,
  parseWeekdayMask,
  resolveEmployeeDetailTab,
  summarizeCurrentAddress,
  toLocalDateTimeInput,
  validateEmployeeAbsenceDraft,
  validateEmployeeAddressDraft,
  validateEmployeeAvailabilityDraft,
  validateEmployeeCredentialDraft,
  validateEmployeeQualificationDraft,
} from "@/features/employees/employeeAdmin.helpers.js";
import type { MessageKey } from "@/i18n/messages";
import { useAuthStore } from "@/stores/auth";

withDefaults(defineProps<{ embedded?: boolean }>(), {
  embedded: false,
});

const { t } = useI18n();
const authStore = useAuthStore();
const { showFeedbackToast } = useSicherPlanFeedback();

const loading = reactive({
  list: false,
  detail: false,
  action: false,
});

const filters = reactive({
  search: "",
  status: "",
  default_branch_id: "",
  default_mandate_id: "",
  include_archived: false,
});

const employeeDraft = reactive({
  tenant_id: "",
  personnel_no: "",
  first_name: "",
  last_name: "",
  preferred_name: "",
  work_email: "",
  work_phone: "",
  mobile_phone: "",
  default_branch_id: "",
  default_mandate_id: "",
  hire_date: "",
  termination_date: "",
  status: "active",
  employment_type_code: "",
  target_weekly_hours: "",
  target_monthly_hours: "",
  user_id: "",
  notes: "",
});

const privateProfileDraft = reactive({
  birth_date: "",
  place_of_birth: "",
  nationality_country_code: "",
});

const noteDraft = reactive({
  note_type: "operational_note",
  title: "",
  body: "",
  reminder_at: "",
  completed_at: "",
});

const groupDraft = reactive({
  code: "",
  name: "",
  description: "",
});

const membershipDraft = reactive({
  group_id: "",
  valid_from: "",
  valid_until: "",
  notes: "",
});

const addressDraft = reactive({
  street_line_1: "",
  street_line_2: "",
  postal_code: "",
  city: "",
  state_region: "",
  country_code: "DE",
  address_type: "home",
  valid_from: "",
  valid_to: "",
  is_current: true,
  is_primary: true,
  notes: "",
});

const qualificationDraft = reactive({
  record_kind: "qualification",
  function_type_id: "",
  qualification_type_id: "",
  certificate_no: "",
  issued_at: "",
  valid_until: "",
  issuing_authority: "",
  granted_internally: false,
  notes: "",
});

const qualificationProofDraft = reactive({
  title: "",
});

const credentialDraft = reactive({
  credential_no: "",
  credential_type: "",
  encoded_value: "",
  valid_from: "",
  valid_until: "",
  notes: "",
});

const availabilityDraft = reactive({
  rule_kind: "",
  starts_at: "",
  ends_at: "",
  recurrence_type: "none",
  weekday_indexes: [] as number[],
  notes: "",
});

const absenceDraft = reactive({
  absence_type: "",
  starts_on: "",
  ends_on: "",
  decision_note: "",
  notes: "",
});

const importDraft = reactive({
  csv_text: buildEmployeeImportTemplateRows(),
  continue_on_error: true,
});

const accessCreateDraft = reactive({
  username: "",
  email: "",
  password: "",
});

const accessManageDraft = reactive<EmployeeAccessUpdateUserRequest>({
  tenant_id: "",
  username: "",
  email: "",
  full_name: "",
});

const accessResetDraft = reactive<EmployeeAccessResetPasswordRequest>({
  tenant_id: "",
  password: "",
});

const accessAttachDraft = reactive({
  user_id: "",
  username: "",
  email: "",
});

const tenantScopeInput = ref(authStore.effectiveTenantScopeId || authStore.tenantScopeId || "");
const branches = ref<BranchRead[]>([]);
const mandates = ref<MandateRead[]>([]);
const employees = ref<EmployeeListItem[]>([]);
const selectedEmployeeId = ref("");
const selectedEmployee = ref<EmployeeOperationalRead | null>(null);
const selectedPrivateProfile = ref<EmployeePrivateProfileRead | null>(null);
const employeeAddresses = ref<EmployeeAddressHistoryRead[]>([]);
const employeeNotes = ref<EmployeeNoteRead[]>([]);
const employeeGroups = ref<EmployeeGroupRead[]>([]);
const employeeQualifications = ref<EmployeeQualificationRead[]>([]);
const employeeCredentials = ref<EmployeeCredentialRead[]>([]);
const employeeAvailabilityRules = ref<EmployeeAvailabilityRuleRead[]>([]);
const employeeAbsences = ref<EmployeeAbsenceRead[]>([]);
const employeeDocuments = ref<EmployeeDocumentListItemRead[]>([]);
const functionTypes = ref<FunctionTypeRead[]>([]);
const qualificationTypes = ref<QualificationTypeRead[]>([]);
const qualificationProofsById = reactive<Record<string, EmployeeQualificationProofRead[]>>({});
const currentPhoto = ref<EmployeePhotoRead | null>(null);
const accessLink = ref<EmployeeAccessLinkRead | null>(null);
const importDryRunResult = ref<EmployeeImportDryRunResult | null>(null);
const lastImportResult = ref<EmployeeImportExecuteResult | null>(null);
const lastExportResult = ref<EmployeeExportResult | null>(null);
const photoPreviewUrl = ref("");
const pendingPhotoFile = ref<File | null>(null);
const pendingEmployeeDocumentFile = ref<File | null>(null);
const pendingEmployeeDocumentVersionFile = ref<File | null>(null);
const pendingImportFile = ref<File | null>(null);
const isCreatingEmployee = ref(false);
const listPanelTab = ref<"import_export" | "search">("search");
const activeDetailTab = ref("overview");
const editingNoteId = ref("");
const editingGroupId = ref("");
const editingMembershipId = ref("");
const editingAddressId = ref("");
const editingQualificationId = ref("");
const editingCredentialId = ref("");
const editingAvailabilityRuleId = ref("");
const editingAbsenceId = ref("");
const selectedEmployeeDocumentId = ref("");
const pendingQualificationProofFile = ref<File | null>(null);

const documentUploadDraft = reactive({
  title: "",
  relation_type: "employee_document",
  label: "",
  document_type_key: "",
});

const documentLinkDraft = reactive<EmployeeDocumentLinkPayload>({
  document_id: "",
  relation_type: "employee_document",
  label: "",
});

const effectiveRole = computed(() => authStore.effectiveRole);
const isPlatformAdmin = computed(() => effectiveRole.value === "platform_admin");
const actionState = computed(() => deriveEmployeeActionState(effectiveRole.value, selectedEmployee.value));
const canRead = computed(() => actionState.value.canRead);
const canWrite = computed(() => actionState.value.canWrite);
const canReadPrivate = computed(() => actionState.value.canReadPrivate);
const employeeWorkspaceBusy = computed(() => loading.action);
const employeeWorkspaceLoadingText = computed(() => (employeeWorkspaceBusy.value ? t("workspace.loading.processing") : ""));
const resolvedTenantScopeId = computed(() => authStore.effectiveTenantScopeId);
const hasLinkedAccess = computed(() => !!accessLink.value?.user_id);
const selectedEmployeeLabel = computed(() =>
  selectedEmployee.value
    ? `${selectedEmployee.value.personnel_no} · ${selectedEmployee.value.first_name} ${selectedEmployee.value.last_name}`
    : t("employeeAdmin.detail.emptyTitle"),
);
const currentAddressSummary = computed(() => summarizeCurrentAddress(employeeAddresses.value));
const employeeAddressTimeline = computed(() =>
  [...employeeAddresses.value].sort((left, right) => {
    const startCompare = right.valid_from.localeCompare(left.valid_from);
    if (startCompare !== 0) {
      return startCompare;
    }
    return (right.valid_to || "9999-12-31").localeCompare(left.valid_to || "9999-12-31");
  }),
);
const currentEmployeeAddress = computed(
  () => [...employeeAddresses.value].filter((row) => !row.archived_at && !row.valid_to).sort((a, b) => a.valid_from.localeCompare(b.valid_from)).at(-1) ?? null,
);
const selectedEmployeeDocument = computed(
  () => employeeDocuments.value.find((document) => document.document_id === selectedEmployeeDocumentId.value) ?? null,
);
const selectedQualification = computed(
  () => employeeQualifications.value.find((qualification) => qualification.id === editingQualificationId.value) ?? null,
);
const selectedQualificationProofs = computed(() =>
  editingQualificationId.value ? (qualificationProofsById[editingQualificationId.value] ?? []) : [],
);
const employeeFunctionTypeOptions = computed(() =>
  functionTypes.value
    .filter((row) => row.archived_at == null && row.is_active)
    .map((row) => ({ value: row.id, label: `${row.code} · ${row.label}` })),
);
const employeeQualificationTypeOptions = computed(() =>
  qualificationTypes.value
    .filter((row) => row.archived_at == null && row.is_active)
    .map((row) => ({ value: row.id, label: `${row.code} · ${row.label}` })),
);
const employeeCredentialTypeOptions = computed(() =>
  EMPLOYEE_CREDENTIAL_TYPE_OPTIONS.map((option) => ({
    value: option.value,
    label: t(option.labelKey as never),
  })),
);
const employeeAvailabilityRuleKindOptions = computed(() =>
  EMPLOYEE_AVAILABILITY_RULE_KIND_OPTIONS.map((option) => ({
    value: option.value,
    label: t(option.labelKey as never),
  })),
);
const readinessRecordKindOptions = computed(() => [
  { value: "qualification", label: t("employeeAdmin.readiness.recordKindQualification") },
  { value: "function", label: t("employeeAdmin.readiness.recordKindFunction") },
]);
const availabilityRecurrenceOptions = computed(() => [
  { value: "none", label: t("employeeAdmin.readiness.recurrenceNone") },
  { value: "weekly", label: t("employeeAdmin.readiness.recurrenceWeekly") },
]);
const weekdayOptions = computed(() => [
  { value: 0, label: t("employeeAdmin.readiness.weekdayMon") },
  { value: 1, label: t("employeeAdmin.readiness.weekdayTue") },
  { value: 2, label: t("employeeAdmin.readiness.weekdayWed") },
  { value: 3, label: t("employeeAdmin.readiness.weekdayThu") },
  { value: 4, label: t("employeeAdmin.readiness.weekdayFri") },
  { value: 5, label: t("employeeAdmin.readiness.weekdaySat") },
  { value: 6, label: t("employeeAdmin.readiness.weekdaySun") },
]);
const employmentTypeOptions = computed(() => [
  { value: "full_time", label: t("employeeAdmin.employmentType.full_time") },
  { value: "part_time", label: t("employeeAdmin.employmentType.part_time") },
  { value: "mini_job", label: t("employeeAdmin.employmentType.mini_job") },
  { value: "temporary", label: t("employeeAdmin.employmentType.temporary") },
  { value: "working_student", label: t("employeeAdmin.employmentType.working_student") },
  { value: "freelance", label: t("employeeAdmin.employmentType.freelance") },
  { value: "other", label: t("employeeAdmin.employmentType.other") },
]);
const employeeDocumentRelationOptions = computed(() => [
  { value: "employee_document", label: t("employeeAdmin.documents.relation.employee_document") },
  { value: "id_proof", label: t("employeeAdmin.documents.relation.id_proof") },
  { value: "contract", label: t("employeeAdmin.documents.relation.contract") },
  { value: "certificate", label: t("employeeAdmin.documents.relation.certificate") },
  { value: "residence_permit", label: t("employeeAdmin.documents.relation.residence_permit") },
  { value: "misc", label: t("employeeAdmin.documents.relation.misc") },
]);
const employeeDocumentTypeOptions = computed(() => [
  { value: "", label: t("employeeAdmin.documents.documentTypePlaceholder") },
  ...EMPLOYEE_DOCUMENT_TYPE_OPTIONS.map((option) => ({
    value: option.value,
    label: t(option.labelKey as MessageKey),
  })),
]);
const branchOptions = computed(() => branches.value.filter((branch) => branch.archived_at == null));
const mandateOptions = computed(() => mandates.value.filter((mandate) => mandate.archived_at == null));
const filteredEmployeeMandates = computed(() => filterMandateOptions(employeeDraft.default_branch_id));
const branchLabelMap = computed(() => new Map(branchOptions.value.map((branch) => [branch.id, formatStructureLabel(branch)])));
const mandateLabelMap = computed(() => new Map(mandateOptions.value.map((mandate) => [mandate.id, formatStructureLabel(mandate)])));
const selectedEmployeeBranchLabel = computed(() => {
  const branchId = selectedEmployee.value?.default_branch_id;
  return branchId ? branchLabelMap.value.get(branchId) ?? branchId : "";
});
const selectedEmployeeMandateLabel = computed(() => {
  const mandateId = selectedEmployee.value?.default_mandate_id;
  return mandateId ? mandateLabelMap.value.get(mandateId) ?? mandateId : "";
});
const employeeDetailTabs = computed(() => {
  const tabs = [
    { id: "overview", label: t("employeeAdmin.tabs.overview") },
    { id: "app_access", label: t("employeeAdmin.tabs.appAccess") },
    { id: "profile_photo", label: t("employeeAdmin.tabs.profilePhoto") },
    { id: "qualifications", label: t("employeeAdmin.tabs.qualifications") },
    { id: "credentials", label: t("employeeAdmin.tabs.credentials") },
    { id: "availability", label: t("employeeAdmin.tabs.availability") },
    { id: "notes", label: t("employeeAdmin.tabs.notes") },
    { id: "groups", label: t("employeeAdmin.tabs.groups") },
    { id: "documents", label: t("employeeAdmin.tabs.documents") },
  ];

  if (canReadPrivate.value) {
    tabs.splice(6, 0, { id: "private_profile", label: t("employeeAdmin.tabs.privateProfile") });
    tabs.splice(7, 0, { id: "addresses", label: t("employeeAdmin.tabs.addresses") });
    tabs.splice(8, 0, { id: "absences", label: t("employeeAdmin.tabs.absences") });
  }

  return isCreatingEmployee.value ? tabs.filter((tab) => tab.id === "overview") : tabs;
});

type SelectEmployeeOptions = {
  fallbackTab?: string;
  preserveActiveTab?: boolean;
};

function formatStructureLabel(record: BranchRead | MandateRead) {
  return formatEmployeeStructureLabel(record);
}

function filterMandateOptions(branchId: string) {
  return filterMandatesForBranch(mandateOptions.value, branchId) as MandateRead[];
}

function resolveEmployeeDocumentRelationLabel(relationType: string) {
  const match = employeeDocumentRelationOptions.value.find((option) => option.value === relationType);
  return match?.label ?? relationType;
}

function setFeedback(tone: "error" | "neutral" | "success", title: string, message: string) {
  showFeedbackToast({
    key: "employee-admin-feedback",
    message,
    title,
    tone,
  });
}

function resolveEmployeeDocumentErrorMessage(error: unknown) {
  if (!(error instanceof EmployeeAdminApiError)) {
    return t("employeeAdmin.feedback.error");
  }

  const mappedKey = mapEmployeeApiMessage(error.messageKey);
  if (mappedKey !== "employeeAdmin.feedback.error") {
    return t(mappedKey as never);
  }

  if (import.meta.env.DEV) {
    return t("employeeAdmin.feedback.apiDiagnostic" as never, {
      statusCode: String(error.statusCode),
      code: error.code || "-",
      messageKey: error.messageKey || "-",
      requestId: error.requestId || "-",
    });
  }

  if (error.statusCode === 404) {
    return t("employeeAdmin.feedback.routeNotFound");
  }

  return t("employeeAdmin.feedback.error");
}

function normalizeAccessToken(value: string) {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9._-]+/g, ".");
}

function buildSuggestedAccessUsername(employee: EmployeeOperationalRead | null) {
  if (!employee) {
    return "";
  }
  const personnelNo = normalizeAccessToken(employee.personnel_no || "");
  if (personnelNo) {
    return personnelNo;
  }
  const firstName = normalizeAccessToken(employee.first_name || "");
  const lastName = normalizeAccessToken(employee.last_name || "");
  return [firstName, lastName].filter(Boolean).join(".").replace(/\.+/g, ".");
}

function syncAccessCreateDraft(force = false) {
  if (!selectedEmployee.value || hasLinkedAccess.value) {
    return;
  }
  const suggestedUsername = buildSuggestedAccessUsername(selectedEmployee.value);
  const suggestedEmail = selectedEmployee.value.work_email || "";
  if (force || !accessCreateDraft.username.trim()) {
    accessCreateDraft.username = suggestedUsername;
  }
  if (force || !accessCreateDraft.email.trim()) {
    accessCreateDraft.email = suggestedEmail;
  }
}

function syncAccessManageDraft() {
  accessManageDraft.tenant_id = resolvedTenantScopeId.value || "";
  accessResetDraft.tenant_id = resolvedTenantScopeId.value || "";
  accessResetDraft.password = "";
  if (!accessLink.value?.user_id) {
    accessManageDraft.username = "";
    accessManageDraft.email = "";
    accessManageDraft.full_name = "";
    return;
  }
  accessManageDraft.username = accessLink.value.username || "";
  accessManageDraft.email = accessLink.value.email || "";
  accessManageDraft.full_name = accessLink.value.full_name || "";
}

function setCatalogRefreshWarning() {
  setFeedback(
    "neutral",
    t("employeeAdmin.feedback.titleError"),
    t("employeeAdmin.feedback.catalogPartial"),
  );
}

function rememberScope() {
  authStore.setTenantScopeId(tenantScopeInput.value);
  void refreshEmployees();
}

async function loadTenantStructure() {
  if (!resolvedTenantScopeId.value || !authStore.accessToken || !canRead.value) {
    branches.value = [];
    mandates.value = [];
    return;
  }

  const actorTenantId = resolvedTenantScopeId.value;
  const [branchRecords, mandateRecords] = await Promise.all([
    listBranches(authStore.accessToken, resolvedTenantScopeId.value, effectiveRole.value, actorTenantId),
    listMandates(authStore.accessToken, resolvedTenantScopeId.value, effectiveRole.value, actorTenantId),
  ]);

  branches.value = branchRecords;
  mandates.value = mandateRecords;
}

function resetEmployeeDraft() {
  employeeDraft.tenant_id = resolvedTenantScopeId.value || "";
  employeeDraft.personnel_no = "";
  employeeDraft.first_name = "";
  employeeDraft.last_name = "";
  employeeDraft.preferred_name = "";
  employeeDraft.work_email = "";
  employeeDraft.work_phone = "";
  employeeDraft.mobile_phone = "";
  employeeDraft.default_branch_id = "";
  employeeDraft.default_mandate_id = "";
  employeeDraft.hire_date = "";
  employeeDraft.termination_date = "";
  employeeDraft.status = "active";
  employeeDraft.employment_type_code = "";
  employeeDraft.target_weekly_hours = "";
  employeeDraft.target_monthly_hours = "";
  employeeDraft.user_id = "";
  employeeDraft.notes = "";
}

function resetPrivateProfileDraft() {
  privateProfileDraft.birth_date = selectedPrivateProfile.value?.birth_date || "";
  privateProfileDraft.place_of_birth = selectedPrivateProfile.value?.place_of_birth || "";
  privateProfileDraft.nationality_country_code = selectedPrivateProfile.value?.nationality_country_code || "";
}

function syncEmployeeDraft(employee: EmployeeOperationalRead) {
  employeeDraft.tenant_id = employee.tenant_id;
  employeeDraft.personnel_no = employee.personnel_no;
  employeeDraft.first_name = employee.first_name;
  employeeDraft.last_name = employee.last_name;
  employeeDraft.preferred_name = employee.preferred_name || "";
  employeeDraft.work_email = employee.work_email || "";
  employeeDraft.work_phone = employee.work_phone || "";
  employeeDraft.mobile_phone = employee.mobile_phone || "";
  employeeDraft.default_branch_id = employee.default_branch_id || "";
  employeeDraft.default_mandate_id = employee.default_mandate_id || "";
  employeeDraft.hire_date = employee.hire_date || "";
  employeeDraft.termination_date = employee.termination_date || "";
  employeeDraft.status = employee.status || "active";
  employeeDraft.employment_type_code = employee.employment_type_code || "";
  employeeDraft.target_weekly_hours = employee.target_weekly_hours == null ? "" : String(employee.target_weekly_hours);
  employeeDraft.target_monthly_hours = employee.target_monthly_hours == null ? "" : String(employee.target_monthly_hours);
  employeeDraft.user_id = employee.user_id || "";
  employeeDraft.notes = employee.notes || "";
}

function syncPrivateProfileDraft(profile: EmployeePrivateProfileRead | null) {
  selectedPrivateProfile.value = profile;
  privateProfileDraft.birth_date = profile?.birth_date || "";
  privateProfileDraft.place_of_birth = profile?.place_of_birth || "";
  privateProfileDraft.nationality_country_code = profile?.nationality_country_code || "";
}

function resetNoteDraft() {
  noteDraft.note_type = "operational_note";
  noteDraft.title = "";
  noteDraft.body = "";
  noteDraft.reminder_at = "";
  noteDraft.completed_at = "";
  editingNoteId.value = "";
}

function editNote(note: EmployeeNoteRead) {
  editingNoteId.value = note.id;
  noteDraft.note_type = note.note_type;
  noteDraft.title = note.title;
  noteDraft.body = note.body || "";
  noteDraft.reminder_at = note.reminder_at || "";
  noteDraft.completed_at = note.completed_at || "";
}

function resetGroupDraft() {
  groupDraft.code = "";
  groupDraft.name = "";
  groupDraft.description = "";
  editingGroupId.value = "";
}

function resetMembershipDraft() {
  membershipDraft.group_id = "";
  membershipDraft.valid_from = "";
  membershipDraft.valid_until = "";
  membershipDraft.notes = "";
  editingMembershipId.value = "";
}

function resetAddressDraft() {
  addressDraft.street_line_1 = "";
  addressDraft.street_line_2 = "";
  addressDraft.postal_code = "";
  addressDraft.city = "";
  addressDraft.state_region = "";
  addressDraft.country_code = "DE";
  addressDraft.address_type = "home";
  addressDraft.valid_from = "";
  addressDraft.valid_to = "";
  addressDraft.is_current = true;
  addressDraft.is_primary = true;
  addressDraft.notes = "";
  editingAddressId.value = "";
}

function resetQualificationDraft() {
  qualificationDraft.record_kind = "qualification";
  qualificationDraft.function_type_id = "";
  qualificationDraft.qualification_type_id = "";
  qualificationDraft.certificate_no = "";
  qualificationDraft.issued_at = "";
  qualificationDraft.valid_until = "";
  qualificationDraft.issuing_authority = "";
  qualificationDraft.granted_internally = false;
  qualificationDraft.notes = "";
  qualificationProofDraft.title = "";
  editingQualificationId.value = "";
  pendingQualificationProofFile.value = null;
}

function resetCredentialDraft() {
  credentialDraft.credential_no = "";
  credentialDraft.credential_type = "";
  credentialDraft.encoded_value = "";
  credentialDraft.valid_from = "";
  credentialDraft.valid_until = "";
  credentialDraft.notes = "";
  editingCredentialId.value = "";
}

function resetAvailabilityDraft() {
  availabilityDraft.rule_kind = "";
  availabilityDraft.starts_at = "";
  availabilityDraft.ends_at = "";
  availabilityDraft.recurrence_type = "none";
  availabilityDraft.weekday_indexes = [];
  availabilityDraft.notes = "";
  editingAvailabilityRuleId.value = "";
}

function resetAbsenceDraft() {
  absenceDraft.absence_type = "";
  absenceDraft.starts_on = "";
  absenceDraft.ends_on = "";
  absenceDraft.decision_note = "";
  absenceDraft.notes = "";
  editingAbsenceId.value = "";
}

function resetEmployeeDocumentDrafts() {
  documentUploadDraft.title = "";
  documentUploadDraft.relation_type = "employee_document";
  documentUploadDraft.label = "";
  documentUploadDraft.document_type_key = "";
  documentLinkDraft.document_id = "";
  documentLinkDraft.relation_type = "employee_document";
  documentLinkDraft.label = "";
  selectedEmployeeDocumentId.value = "";
  pendingEmployeeDocumentFile.value = null;
  pendingEmployeeDocumentVersionFile.value = null;
}

function editQualification(qualification: EmployeeQualificationRead) {
  editingQualificationId.value = qualification.id;
  qualificationDraft.record_kind = qualification.record_kind || "qualification";
  qualificationDraft.function_type_id = qualification.function_type_id || "";
  qualificationDraft.qualification_type_id = qualification.qualification_type_id || "";
  qualificationDraft.certificate_no = qualification.certificate_no || "";
  qualificationDraft.issued_at = qualification.issued_at || "";
  qualificationDraft.valid_until = qualification.valid_until || "";
  qualificationDraft.issuing_authority = qualification.issuing_authority || "";
  qualificationDraft.granted_internally = qualification.granted_internally;
  qualificationDraft.notes = qualification.notes || "";
  qualificationProofDraft.title = "";
  void loadQualificationProofs(qualification.id);
}

function editCredential(credential: EmployeeCredentialRead) {
  editingCredentialId.value = credential.id;
  credentialDraft.credential_no = credential.credential_no;
  credentialDraft.credential_type = credential.credential_type;
  credentialDraft.encoded_value = credential.encoded_value;
  credentialDraft.valid_from = credential.valid_from;
  credentialDraft.valid_until = credential.valid_until || "";
  credentialDraft.notes = credential.notes || "";
}

function editAvailabilityRule(rule: EmployeeAvailabilityRuleRead) {
  editingAvailabilityRuleId.value = rule.id;
  availabilityDraft.rule_kind = rule.rule_kind;
  availabilityDraft.starts_at = toLocalDateTimeInput(rule.starts_at);
  availabilityDraft.ends_at = toLocalDateTimeInput(rule.ends_at);
  availabilityDraft.recurrence_type = rule.recurrence_type || "none";
  availabilityDraft.weekday_indexes = parseWeekdayMask(rule.weekday_mask);
  availabilityDraft.notes = rule.notes || "";
}

function editAbsence(absence: EmployeeAbsenceRead) {
  editingAbsenceId.value = absence.id;
  absenceDraft.absence_type = absence.absence_type;
  absenceDraft.starts_on = absence.starts_on;
  absenceDraft.ends_on = absence.ends_on;
  absenceDraft.decision_note = absence.decision_note || "";
  absenceDraft.notes = absence.notes || "";
}

function useEmployeeDocumentForVersion(document: EmployeeDocumentListItemRead) {
  selectedEmployeeDocumentId.value = document.document_id;
}

function editAddress(row: EmployeeAddressHistoryRead) {
  editingAddressId.value = row.id;
  addressDraft.street_line_1 = row.address?.street_line_1 || "";
  addressDraft.street_line_2 = row.address?.street_line_2 || "";
  addressDraft.postal_code = row.address?.postal_code || "";
  addressDraft.city = row.address?.city || "";
  addressDraft.state_region = row.address?.state_region || "";
  addressDraft.country_code = row.address?.country_code || "DE";
  addressDraft.address_type = row.address_type;
  addressDraft.valid_from = row.valid_from;
  addressDraft.valid_to = row.valid_to || "";
  addressDraft.is_current = !row.valid_to;
  addressDraft.is_primary = row.is_primary;
  addressDraft.notes = row.notes || "";
}

function prepareAddressAsCurrent(row: EmployeeAddressHistoryRead) {
  editAddress(row);
  addressDraft.is_current = true;
  addressDraft.valid_to = "";
}

function prepareAddressValidityClose(row: EmployeeAddressHistoryRead) {
  editAddress(row);
  addressDraft.is_current = false;
  addressDraft.valid_to = row.valid_to || new Date().toISOString().slice(0, 10);
}

function onAddressCurrentToggle() {
  if (addressDraft.is_current) {
    addressDraft.valid_to = "";
  }
}

function resetAccessDrafts() {
  accessCreateDraft.username = "";
  accessCreateDraft.email = "";
  accessCreateDraft.password = "";
  accessManageDraft.tenant_id = resolvedTenantScopeId.value || "";
  accessManageDraft.username = "";
  accessManageDraft.email = "";
  accessManageDraft.full_name = "";
  accessResetDraft.tenant_id = resolvedTenantScopeId.value || "";
  accessResetDraft.password = "";
  accessAttachDraft.user_id = "";
  accessAttachDraft.username = "";
  accessAttachDraft.email = "";
  syncAccessCreateDraft(true);
  syncAccessManageDraft();
}

function editMembership(membership: EmployeeGroupMembershipRead) {
  editingMembershipId.value = membership.id;
  membershipDraft.group_id = membership.group_id;
  membershipDraft.valid_from = membership.valid_from;
  membershipDraft.valid_until = membership.valid_until || "";
  membershipDraft.notes = membership.notes || "";
}

function startCreateEmployee() {
  isCreatingEmployee.value = true;
  activeDetailTab.value = "overview";
  selectedEmployeeId.value = "";
  selectedEmployee.value = null;
  selectedPrivateProfile.value = null;
  employeeAddresses.value = [];
  employeeNotes.value = [];
  employeeQualifications.value = [];
  employeeCredentials.value = [];
  employeeAvailabilityRules.value = [];
  employeeAbsences.value = [];
  employeeDocuments.value = [];
  currentPhoto.value = null;
  accessLink.value = null;
  syncPrivateProfileDraft(null);
  clearPhotoPreview();
  resetEmployeeDocumentDrafts();
  resetEmployeeDraft();
  resetNoteDraft();
  resetMembershipDraft();
  resetAddressDraft();
  resetQualificationDraft();
  resetCredentialDraft();
  resetAvailabilityDraft();
  resetAbsenceDraft();
  resetAccessDrafts();
}

function clearPhotoPreview() {
  if (photoPreviewUrl.value) {
    URL.revokeObjectURL(photoPreviewUrl.value);
  }
  photoPreviewUrl.value = "";
}

async function refreshEmployees() {
  if (!resolvedTenantScopeId.value || !authStore.accessToken || !canRead.value) {
    branches.value = [];
    mandates.value = [];
    employees.value = [];
    selectedEmployee.value = null;
    return;
  }

  loading.list = true;
  try {
    employees.value = await listEmployees(resolvedTenantScopeId.value, authStore.accessToken, filters);
    if (selectedEmployeeId.value) {
      const stillSelected = employees.value.some((row) => row.id === selectedEmployeeId.value);
      if (stillSelected) {
        await selectEmployee(selectedEmployeeId.value);
      } else {
        selectedEmployeeId.value = "";
        selectedEmployee.value = null;
      }
    } else if (employees.value.length && !isCreatingEmployee.value) {
      const [firstEmployee] = employees.value;
      if (firstEmployee) {
        await selectEmployee(firstEmployee.id);
      }
    }
  } catch (error) {
    const key = error instanceof EmployeeAdminApiError ? mapEmployeeApiMessage(error.messageKey) : "employeeAdmin.feedback.error";
    setFeedback("error", t("employeeAdmin.feedback.titleError"), t(key as never));
    loading.list = false;
    return;
  }

  let catalogRefreshFailed = false;
  try {
    await loadTenantStructure();
  } catch {
    branches.value = [];
    mandates.value = [];
    catalogRefreshFailed = true;
  }

  try {
    await listSupplementalGroups();
  } catch {
    employeeGroups.value = [];
    catalogRefreshFailed = true;
  }

  try {
    await loadEmployeeReadinessCatalogs();
  } catch {
    functionTypes.value = [];
    qualificationTypes.value = [];
    catalogRefreshFailed = true;
  } finally {
    loading.list = false;
  }

  if (catalogRefreshFailed) {
    setCatalogRefreshWarning();
  }
}

async function listSupplementalGroups() {
  if (!resolvedTenantScopeId.value || !authStore.accessToken || !canRead.value) {
    employeeGroups.value = [];
    return;
  }
  employeeGroups.value = await listEmployeeGroups(resolvedTenantScopeId.value, authStore.accessToken);
}

async function loadEmployeeReadinessCatalogs() {
  if (!resolvedTenantScopeId.value || !authStore.accessToken || !canRead.value) {
    functionTypes.value = [];
    qualificationTypes.value = [];
    return;
  }
  const [functionTypeRows, qualificationTypeRows] = await Promise.all([
    listFunctionTypes(resolvedTenantScopeId.value, authStore.accessToken),
    listQualificationTypes(resolvedTenantScopeId.value, authStore.accessToken),
  ]);
  functionTypes.value = functionTypeRows;
  qualificationTypes.value = qualificationTypeRows;
}

async function loadQualificationProofs(qualificationId: string) {
  if (!qualificationId || !resolvedTenantScopeId.value || !authStore.accessToken) {
    return;
  }
  qualificationProofsById[qualificationId] = await listEmployeeQualificationProofs(
    resolvedTenantScopeId.value,
    qualificationId,
    authStore.accessToken,
  );
}

async function selectEmployee(employeeId: string, options: SelectEmployeeOptions = {}) {
  if (!resolvedTenantScopeId.value || !authStore.accessToken) {
    return;
  }
  const { preserveActiveTab = false, fallbackTab = "overview" } = options;
  const desiredTab = preserveActiveTab ? activeDetailTab.value : fallbackTab;
  isCreatingEmployee.value = false;
  selectedEmployeeId.value = employeeId;
  loading.detail = true;
  try {
    const [
      employee,
      notes,
      documents,
      photo,
      qualifications,
      credentials,
      availabilityRules,
      absencesOrNull,
    ] = await Promise.all([
      getEmployee(resolvedTenantScopeId.value, employeeId, authStore.accessToken),
      listEmployeeNotes(resolvedTenantScopeId.value, employeeId, authStore.accessToken),
      listEmployeeDocuments(resolvedTenantScopeId.value, employeeId, authStore.accessToken),
      getEmployeePhoto(resolvedTenantScopeId.value, employeeId, authStore.accessToken),
      listEmployeeQualifications(resolvedTenantScopeId.value, employeeId, authStore.accessToken),
      listEmployeeCredentials(resolvedTenantScopeId.value, employeeId, authStore.accessToken),
      listEmployeeAvailabilityRules(resolvedTenantScopeId.value, employeeId, authStore.accessToken),
      canReadPrivate.value
        ? listEmployeeAbsences(resolvedTenantScopeId.value, employeeId, authStore.accessToken)
        : Promise.resolve(null),
    ]);
    selectedEmployee.value = employee;
    employeeNotes.value = notes;
    employeeDocuments.value = documents;
    employeeQualifications.value = qualifications;
    employeeCredentials.value = credentials;
    employeeAvailabilityRules.value = availabilityRules;
    employeeAbsences.value = absencesOrNull ?? [];
    currentPhoto.value = photo;
    accessLink.value = actionState.value.canManageAccess
      ? await getEmployeeAccessLink(resolvedTenantScopeId.value, employeeId, authStore.accessToken)
      : null;
    syncEmployeeDraft(employee);
    resetNoteDraft();
    resetMembershipDraft();
    resetAddressDraft();
    resetQualificationDraft();
    resetCredentialDraft();
    resetAvailabilityDraft();
    resetAbsenceDraft();
    resetEmployeeDocumentDrafts();
    syncPrivateProfileDraft(null);
    resetAccessDrafts();
    if (canReadPrivate.value) {
      const [addresses, privateProfile] = await Promise.all([
        listEmployeeAddresses(resolvedTenantScopeId.value, employeeId, authStore.accessToken),
        getEmployeePrivateProfile(resolvedTenantScopeId.value, employeeId, authStore.accessToken).catch((error) => {
          if (error instanceof EmployeeAdminApiError && error.statusCode === 404) {
            return null;
          }
          throw error;
        }),
      ]);
      employeeAddresses.value = addresses;
      syncPrivateProfileDraft(privateProfile);
    } else {
      employeeAddresses.value = [];
      syncPrivateProfileDraft(null);
    }
    Object.keys(qualificationProofsById).forEach((key) => delete qualificationProofsById[key]);
    const [firstQualification] = qualifications;
    if (firstQualification) {
      await loadQualificationProofs(firstQualification.id);
    }
    activeDetailTab.value = resolveEmployeeDetailTab(
      desiredTab,
      employeeDetailTabs.value.map((tab) => tab.id),
      fallbackTab,
    );
    await refreshPhotoPreview();
  } catch (error) {
    const key = error instanceof EmployeeAdminApiError ? mapEmployeeApiMessage(error.messageKey) : "employeeAdmin.feedback.error";
    setFeedback("error", t("employeeAdmin.feedback.titleError"), t(key as never));
  } finally {
    loading.detail = false;
  }
}

async function refreshPhotoPreview() {
  clearPhotoPreview();
  if (!currentPhoto.value?.current_version_no || !authStore.accessToken || !resolvedTenantScopeId.value) {
    return;
  }
  try {
    const file = await downloadEmployeeDocument(
      resolvedTenantScopeId.value,
      currentPhoto.value.document_id,
      currentPhoto.value.current_version_no,
      authStore.accessToken,
    );
    photoPreviewUrl.value = URL.createObjectURL(file.blob);
  } catch {
    photoPreviewUrl.value = "";
  }
}

async function submitEmployee() {
  if (!resolvedTenantScopeId.value || !authStore.accessToken) {
    return;
  }

  loading.action = true;
  try {
    const payload = buildEmployeeOperationalPayload(
      {
        tenant_id: resolvedTenantScopeId.value,
        personnel_no: employeeDraft.personnel_no,
        first_name: employeeDraft.first_name,
        last_name: employeeDraft.last_name,
        preferred_name: employeeDraft.preferred_name,
        work_email: employeeDraft.work_email,
        work_phone: employeeDraft.work_phone,
        mobile_phone: employeeDraft.mobile_phone,
        default_branch_id: employeeDraft.default_branch_id,
        default_mandate_id: employeeDraft.default_mandate_id,
        hire_date: employeeDraft.hire_date,
        termination_date: employeeDraft.termination_date,
        status: employeeDraft.status,
        employment_type_code: employeeDraft.employment_type_code,
        target_weekly_hours: employeeDraft.target_weekly_hours,
        target_monthly_hours: employeeDraft.target_monthly_hours,
        user_id: employeeDraft.user_id,
        notes: employeeDraft.notes,
      },
      {
        deferUserLink: isCreatingEmployee.value,
        allowedBranchIds: branchOptions.value.map((branch) => branch.id),
        allowedMandateIds: filteredEmployeeMandates.value.map((mandate) => mandate.id),
      } as any,
    );
    const employee = isCreatingEmployee.value
      ? await createEmployee(resolvedTenantScopeId.value, authStore.accessToken, payload)
      : await updateEmployee(resolvedTenantScopeId.value, selectedEmployeeId.value, authStore.accessToken, {
          ...payload,
          user_id: emptyToNull(employeeDraft.user_id),
          version_no: selectedEmployee.value?.version_no,
        });
    setFeedback("success", t("employeeAdmin.feedback.titleSuccess"), t("employeeAdmin.feedback.employeeSaved"));
    await refreshEmployees();
    await selectEmployee(employee.id, { preserveActiveTab: true });
  } catch (error) {
    const key = error instanceof EmployeeAdminApiError ? mapEmployeeApiMessage(error.messageKey) : "employeeAdmin.feedback.error";
    setFeedback("error", t("employeeAdmin.feedback.titleError"), t(key as never));
  } finally {
    loading.action = false;
  }
}

async function submitPrivateProfile() {
  if (!selectedEmployeeId.value || !resolvedTenantScopeId.value || !authStore.accessToken) {
    return;
  }

  loading.action = true;
  try {
    const payload = buildEmployeePrivateProfilePayload(privateProfileDraft, {
      tenantId: resolvedTenantScopeId.value,
      employeeId: selectedEmployeeId.value,
    });
    const saved = selectedPrivateProfile.value
      ? await updateEmployeePrivateProfile(
          resolvedTenantScopeId.value,
          selectedEmployeeId.value,
          authStore.accessToken,
          {
            ...payload,
            version_no: selectedPrivateProfile.value.version_no,
          } as EmployeePrivateProfileUpdatePayload,
        )
      : await upsertEmployeePrivateProfile(
          resolvedTenantScopeId.value,
          selectedEmployeeId.value,
          authStore.accessToken,
          payload as EmployeePrivateProfileWritePayload,
        );
    syncPrivateProfileDraft(saved);
    setFeedback("success", t("employeeAdmin.feedback.titleSuccess"), t("employeeAdmin.feedback.privateProfileSaved"));
  } catch (error) {
    const key = error instanceof EmployeeAdminApiError ? mapEmployeeApiMessage(error.messageKey) : "employeeAdmin.feedback.error";
    setFeedback("error", t("employeeAdmin.feedback.titleError"), t(key as never));
  } finally {
    loading.action = false;
  }
}

async function submitNote() {
  if (!selectedEmployeeId.value || !resolvedTenantScopeId.value || !authStore.accessToken) {
    return;
  }

  loading.action = true;
  try {
    if (editingNoteId.value) {
      const existing = employeeNotes.value.find((row) => row.id === editingNoteId.value);
      await updateEmployeeNote(resolvedTenantScopeId.value, selectedEmployeeId.value, editingNoteId.value, authStore.accessToken, {
        title: noteDraft.title.trim(),
        body: emptyToNull(noteDraft.body),
        reminder_at: emptyToNull(noteDraft.reminder_at),
        completed_at: emptyToNull(noteDraft.completed_at),
        version_no: existing?.version_no ?? 1,
      });
    } else {
      await createEmployeeNote(resolvedTenantScopeId.value, selectedEmployeeId.value, authStore.accessToken, {
        tenant_id: resolvedTenantScopeId.value,
        employee_id: selectedEmployeeId.value,
        note_type: noteDraft.note_type,
        title: noteDraft.title.trim(),
        body: emptyToNull(noteDraft.body),
        reminder_at: emptyToNull(noteDraft.reminder_at),
      });
    }
    resetNoteDraft();
    await selectEmployee(selectedEmployeeId.value, { preserveActiveTab: true });
    setFeedback("success", t("employeeAdmin.feedback.titleSuccess"), t("employeeAdmin.feedback.noteSaved"));
  } catch (error) {
    const key = error instanceof EmployeeAdminApiError ? mapEmployeeApiMessage(error.messageKey) : "employeeAdmin.feedback.error";
    setFeedback("error", t("employeeAdmin.feedback.titleError"), t(key as never));
  } finally {
    loading.action = false;
  }
}

async function submitGroup() {
  if (!resolvedTenantScopeId.value || !authStore.accessToken) {
    return;
  }
  loading.action = true;
  try {
    if (editingGroupId.value) {
      const existing = employeeGroups.value.find((row) => row.id === editingGroupId.value);
      await updateEmployeeGroup(resolvedTenantScopeId.value, editingGroupId.value, authStore.accessToken, {
        code: groupDraft.code.trim(),
        name: groupDraft.name.trim(),
        description: emptyToNull(groupDraft.description),
        version_no: existing?.version_no ?? 1,
      });
    } else {
      await createEmployeeGroup(resolvedTenantScopeId.value, authStore.accessToken, {
        tenant_id: resolvedTenantScopeId.value,
        code: groupDraft.code.trim(),
        name: groupDraft.name.trim(),
        description: emptyToNull(groupDraft.description),
      });
    }
    resetGroupDraft();
    await listSupplementalGroups();
    setFeedback("success", t("employeeAdmin.feedback.titleSuccess"), t("employeeAdmin.feedback.groupSaved"));
  } catch (error) {
    const key = error instanceof EmployeeAdminApiError ? mapEmployeeApiMessage(error.messageKey) : "employeeAdmin.feedback.error";
    setFeedback("error", t("employeeAdmin.feedback.titleError"), t(key as never));
  } finally {
    loading.action = false;
  }
}

async function submitMembership() {
  if (!resolvedTenantScopeId.value || !authStore.accessToken || !selectedEmployeeId.value) {
    return;
  }
  loading.action = true;
  try {
    if (editingMembershipId.value) {
      const existing = selectedEmployee.value?.group_memberships.find((row) => row.id === editingMembershipId.value);
      await updateEmployeeGroupMembership(resolvedTenantScopeId.value, editingMembershipId.value, authStore.accessToken, {
        valid_from: membershipDraft.valid_from,
        valid_until: emptyToNull(membershipDraft.valid_until),
        notes: emptyToNull(membershipDraft.notes),
        version_no: existing?.version_no ?? 1,
      });
    } else {
      await createEmployeeGroupMembership(resolvedTenantScopeId.value, authStore.accessToken, {
        tenant_id: resolvedTenantScopeId.value,
        employee_id: selectedEmployeeId.value,
        group_id: membershipDraft.group_id,
        valid_from: membershipDraft.valid_from,
        valid_until: emptyToNull(membershipDraft.valid_until),
        notes: emptyToNull(membershipDraft.notes),
      });
    }
    resetMembershipDraft();
    await selectEmployee(selectedEmployeeId.value, { preserveActiveTab: true });
    setFeedback("success", t("employeeAdmin.feedback.titleSuccess"), t("employeeAdmin.feedback.membershipSaved"));
  } catch (error) {
    const key = error instanceof EmployeeAdminApiError ? mapEmployeeApiMessage(error.messageKey) : "employeeAdmin.feedback.error";
    setFeedback("error", t("employeeAdmin.feedback.titleError"), t(key as never));
  } finally {
    loading.action = false;
  }
}

function buildEmployeeAddressPayload(): EmployeeAddressHistoryCreatePayload | EmployeeAddressHistoryUpdatePayload {
  return {
    ...(editingAddressId.value ? {} : { tenant_id: resolvedTenantScopeId.value, employee_id: selectedEmployeeId.value }),
    address: {
      street_line_1: addressDraft.street_line_1.trim(),
      street_line_2: addressDraft.street_line_2.trim() || null,
      postal_code: addressDraft.postal_code.trim(),
      city: addressDraft.city.trim(),
      state_region: addressDraft.state_region.trim() || null,
      country_code: addressDraft.country_code.trim().toUpperCase(),
    },
    address_type: addressDraft.address_type,
    valid_from: addressDraft.valid_from,
    valid_to: addressDraft.is_current ? null : (addressDraft.valid_to.trim() || null),
    is_primary: addressDraft.is_primary,
    notes: addressDraft.notes.trim() || null,
  };
}

async function submitAddress() {
  if (!resolvedTenantScopeId.value || !authStore.accessToken || !selectedEmployeeId.value) {
    return;
  }

  const validationKey = validateEmployeeAddressDraft(addressDraft, employeeAddresses.value, editingAddressId.value);
  if (validationKey) {
    setFeedback("error", t("employeeAdmin.feedback.titleError"), t(validationKey as never));
    return;
  }

  loading.action = true;
  try {
    if (editingAddressId.value) {
      const existing = employeeAddresses.value.find((row) => row.id === editingAddressId.value);
      await updateEmployeeAddress(
        resolvedTenantScopeId.value,
        selectedEmployeeId.value,
        editingAddressId.value,
        authStore.accessToken,
        {
          ...buildEmployeeAddressPayload(),
          version_no: existing?.version_no ?? 1,
        },
      );
    } else {
      await createEmployeeAddress(
        resolvedTenantScopeId.value,
        selectedEmployeeId.value,
        authStore.accessToken,
        buildEmployeeAddressPayload() as EmployeeAddressHistoryCreatePayload,
      );
    }
    employeeAddresses.value = await listEmployeeAddresses(
      resolvedTenantScopeId.value,
      selectedEmployeeId.value,
      authStore.accessToken,
    );
    resetAddressDraft();
    setFeedback("success", t("employeeAdmin.feedback.titleSuccess"), t("employeeAdmin.feedback.addressSaved"));
  } catch (error) {
    const key = error instanceof EmployeeAdminApiError ? mapEmployeeApiMessage(error.messageKey) : "employeeAdmin.feedback.error";
    setFeedback("error", t("employeeAdmin.feedback.titleError"), t(key as never));
  } finally {
    loading.action = false;
  }
}

async function submitQualification() {
  if (!resolvedTenantScopeId.value || !authStore.accessToken || !selectedEmployeeId.value) {
    return;
  }

  const validationKey = validateEmployeeQualificationDraft(qualificationDraft);
  if (validationKey) {
    setFeedback("error", t("employeeAdmin.feedback.titleError"), t(validationKey as never));
    return;
  }

  loading.action = true;
  try {
    const payload = buildEmployeeQualificationPayload(qualificationDraft, {
      tenantId: resolvedTenantScopeId.value,
      employeeId: selectedEmployeeId.value,
    }) as EmployeeQualificationCreatePayload;
    if (editingQualificationId.value) {
      const existing = employeeQualifications.value.find((row) => row.id === editingQualificationId.value);
      await updateEmployeeQualification(resolvedTenantScopeId.value, editingQualificationId.value, authStore.accessToken, {
        function_type_id: payload.function_type_id,
        qualification_type_id: payload.qualification_type_id,
        certificate_no: payload.certificate_no,
        issued_at: payload.issued_at,
        valid_until: payload.valid_until,
        issuing_authority: payload.issuing_authority,
        granted_internally: payload.granted_internally,
        notes: payload.notes,
        version_no: existing?.version_no ?? 1,
      } as EmployeeQualificationUpdatePayload);
    } else {
      await createEmployeeQualification(resolvedTenantScopeId.value, authStore.accessToken, payload);
    }
    await selectEmployee(selectedEmployeeId.value, { preserveActiveTab: true });
    setFeedback("success", t("employeeAdmin.feedback.titleSuccess"), t("employeeAdmin.feedback.qualificationSaved"));
  } catch (error) {
    const key = error instanceof EmployeeAdminApiError ? mapEmployeeApiMessage(error.messageKey) : "employeeAdmin.feedback.error";
    setFeedback("error", t("employeeAdmin.feedback.titleError"), t(key as never));
  } finally {
    loading.action = false;
  }
}

async function submitQualificationProof() {
  if (!editingQualificationId.value || !pendingQualificationProofFile.value || !resolvedTenantScopeId.value || !authStore.accessToken) {
    return;
  }

  loading.action = true;
  try {
    const payload: EmployeeQualificationProofUploadPayload = {
      title: normalizeOptionalText(qualificationProofDraft.title),
      file_name: pendingQualificationProofFile.value.name,
      content_type: pendingQualificationProofFile.value.type || "application/octet-stream",
      content_base64: await fileToBase64(pendingQualificationProofFile.value),
    };
    await uploadEmployeeQualificationProof(
      resolvedTenantScopeId.value,
      editingQualificationId.value,
      authStore.accessToken,
      payload,
    );
    pendingQualificationProofFile.value = null;
    qualificationProofDraft.title = "";
    await loadQualificationProofs(editingQualificationId.value);
    setFeedback("success", t("employeeAdmin.feedback.titleSuccess"), t("employeeAdmin.feedback.qualificationProofSaved"));
  } catch (error) {
    const key = error instanceof EmployeeAdminApiError ? mapEmployeeApiMessage(error.messageKey) : "employeeAdmin.feedback.error";
    setFeedback("error", t("employeeAdmin.feedback.titleError"), t(key as never));
  } finally {
    loading.action = false;
  }
}

async function submitCredential() {
  if (!resolvedTenantScopeId.value || !authStore.accessToken || !selectedEmployeeId.value) {
    return;
  }

  const validationKey = validateEmployeeCredentialDraft(credentialDraft);
  if (validationKey) {
    setFeedback("error", t("employeeAdmin.feedback.titleError"), t(validationKey as never));
    return;
  }

  loading.action = true;
  try {
    const payload = buildEmployeeCredentialPayload(credentialDraft, {
      tenantId: resolvedTenantScopeId.value,
      employeeId: selectedEmployeeId.value,
    }) as EmployeeCredentialCreatePayload;
    if (editingCredentialId.value) {
      const existing = employeeCredentials.value.find((row) => row.id === editingCredentialId.value);
      await updateEmployeeCredential(resolvedTenantScopeId.value, editingCredentialId.value, authStore.accessToken, {
        encoded_value: payload.encoded_value,
        valid_from: payload.valid_from,
        valid_until: payload.valid_until,
        notes: payload.notes,
        version_no: existing?.version_no ?? 1,
      } as EmployeeCredentialUpdatePayload);
    } else {
      await createEmployeeCredential(resolvedTenantScopeId.value, authStore.accessToken, payload);
    }
    await selectEmployee(selectedEmployeeId.value, { preserveActiveTab: true });
    setFeedback("success", t("employeeAdmin.feedback.titleSuccess"), t("employeeAdmin.feedback.credentialSaved"));
  } catch (error) {
    const key = error instanceof EmployeeAdminApiError ? mapEmployeeApiMessage(error.messageKey) : "employeeAdmin.feedback.error";
    setFeedback("error", t("employeeAdmin.feedback.titleError"), t(key as never));
  } finally {
    loading.action = false;
  }
}

async function issueCredentialBadge(credential: EmployeeCredentialRead) {
  if (!resolvedTenantScopeId.value || !authStore.accessToken) {
    return;
  }
  loading.action = true;
  try {
    await issueEmployeeCredentialBadgeOutput(
      resolvedTenantScopeId.value,
      credential.id,
      authStore.accessToken,
      { title: `${credential.credential_no}-badge` } as EmployeeCredentialBadgeIssuePayload,
    );
    setFeedback("success", t("employeeAdmin.feedback.titleSuccess"), t("employeeAdmin.feedback.credentialBadgeIssued"));
  } catch (error) {
    const key = error instanceof EmployeeAdminApiError ? mapEmployeeApiMessage(error.messageKey) : "employeeAdmin.feedback.error";
    setFeedback("error", t("employeeAdmin.feedback.titleError"), t(key as never));
  } finally {
    loading.action = false;
  }
}

async function submitAvailabilityRule() {
  if (!resolvedTenantScopeId.value || !authStore.accessToken || !selectedEmployeeId.value) {
    return;
  }

  const validationKey = validateEmployeeAvailabilityDraft(availabilityDraft);
  if (validationKey) {
    setFeedback("error", t("employeeAdmin.feedback.titleError"), t(validationKey as never));
    return;
  }

  loading.action = true;
  try {
    const payload = buildEmployeeAvailabilityPayload(availabilityDraft, {
      tenantId: resolvedTenantScopeId.value,
      employeeId: selectedEmployeeId.value,
    }) as EmployeeAvailabilityRuleCreatePayload;
    if (editingAvailabilityRuleId.value) {
      const existing = employeeAvailabilityRules.value.find((row) => row.id === editingAvailabilityRuleId.value);
      await updateEmployeeAvailabilityRule(
        resolvedTenantScopeId.value,
        editingAvailabilityRuleId.value,
        authStore.accessToken,
        {
          rule_kind: payload.rule_kind,
          starts_at: payload.starts_at,
          ends_at: payload.ends_at,
          recurrence_type: payload.recurrence_type,
          weekday_mask: payload.weekday_mask,
          notes: payload.notes,
          version_no: existing?.version_no ?? 1,
        } as EmployeeAvailabilityRuleUpdatePayload,
      );
    } else {
      await createEmployeeAvailabilityRule(resolvedTenantScopeId.value, authStore.accessToken, payload);
    }
    await selectEmployee(selectedEmployeeId.value, { preserveActiveTab: true });
    setFeedback("success", t("employeeAdmin.feedback.titleSuccess"), t("employeeAdmin.feedback.availabilitySaved"));
  } catch (error) {
    const key = error instanceof EmployeeAdminApiError ? mapEmployeeApiMessage(error.messageKey) : "employeeAdmin.feedback.error";
    setFeedback("error", t("employeeAdmin.feedback.titleError"), t(key as never));
  } finally {
    loading.action = false;
  }
}

async function submitAbsence() {
  if (!resolvedTenantScopeId.value || !authStore.accessToken || !selectedEmployeeId.value) {
    return;
  }

  const validationKey = validateEmployeeAbsenceDraft(absenceDraft);
  if (validationKey) {
    setFeedback("error", t("employeeAdmin.feedback.titleError"), t(validationKey as never));
    return;
  }

  loading.action = true;
  try {
    const payload = buildEmployeeAbsencePayload(absenceDraft, {
      tenantId: resolvedTenantScopeId.value,
      employeeId: selectedEmployeeId.value,
    }) as EmployeeAbsenceCreatePayload;
    if (editingAbsenceId.value) {
      const existing = employeeAbsences.value.find((row) => row.id === editingAbsenceId.value);
      await updateEmployeeAbsence(resolvedTenantScopeId.value, editingAbsenceId.value, authStore.accessToken, {
        absence_type: payload.absence_type,
        starts_on: payload.starts_on,
        ends_on: payload.ends_on,
        decision_note: normalizeOptionalText(absenceDraft.decision_note),
        notes: payload.notes,
        version_no: existing?.version_no ?? 1,
      } as EmployeeAbsenceUpdatePayload);
    } else {
      await createEmployeeAbsence(resolvedTenantScopeId.value, authStore.accessToken, payload);
    }
    await selectEmployee(selectedEmployeeId.value, { preserveActiveTab: true });
    setFeedback("success", t("employeeAdmin.feedback.titleSuccess"), t("employeeAdmin.feedback.absenceSaved"));
  } catch (error) {
    const key = error instanceof EmployeeAdminApiError ? mapEmployeeApiMessage(error.messageKey) : "employeeAdmin.feedback.error";
    setFeedback("error", t("employeeAdmin.feedback.titleError"), t(key as never));
  } finally {
    loading.action = false;
  }
}

function onPhotoSelected(event: Event) {
  const target = event.target as HTMLInputElement;
  pendingPhotoFile.value = target.files?.[0] ?? null;
}

function onQualificationProofSelected(event: Event) {
  const target = event.target as HTMLInputElement;
  pendingQualificationProofFile.value = target.files?.[0] ?? null;
}

function toggleAvailabilityWeekday(dayValue: number, checked: boolean) {
  if (checked) {
    availabilityDraft.weekday_indexes = Array.from(new Set([...availabilityDraft.weekday_indexes, dayValue])).sort((left, right) => left - right);
    return;
  }
  availabilityDraft.weekday_indexes = availabilityDraft.weekday_indexes.filter((value) => value !== dayValue);
}

function onEmployeeDocumentSelected(event: Event) {
  const target = event.target as HTMLInputElement;
  pendingEmployeeDocumentFile.value = target.files?.[0] ?? null;
}

function onEmployeeDocumentVersionSelected(event: Event) {
  const target = event.target as HTMLInputElement;
  pendingEmployeeDocumentVersionFile.value = target.files?.[0] ?? null;
}

function onImportSelected(event: Event) {
  const target = event.target as HTMLInputElement;
  pendingImportFile.value = target.files?.[0] ?? null;
}

async function submitEmployeeDocumentUpload() {
  if (!pendingEmployeeDocumentFile.value || !selectedEmployeeId.value || !resolvedTenantScopeId.value || !authStore.accessToken) {
    return;
  }

  loading.action = true;
  try {
    const payload: EmployeeDocumentUploadPayload = await buildEmployeeDocumentUploadPayload(
      documentUploadDraft,
      pendingEmployeeDocumentFile.value,
      fileToBase64,
    );
    await uploadEmployeeDocument(resolvedTenantScopeId.value, selectedEmployeeId.value, authStore.accessToken, payload);
    await selectEmployee(selectedEmployeeId.value, { preserveActiveTab: true });
    setFeedback("success", t("employeeAdmin.feedback.titleSuccess"), t("employeeAdmin.feedback.documentUploaded"));
  } catch (error) {
    setFeedback("error", t("employeeAdmin.feedback.titleError"), resolveEmployeeDocumentErrorMessage(error));
  } finally {
    loading.action = false;
  }
}

async function submitEmployeeDocumentLink() {
  if (!selectedEmployeeId.value || !resolvedTenantScopeId.value || !authStore.accessToken) {
    return;
  }

  loading.action = true;
  try {
    await linkEmployeeDocument(
      resolvedTenantScopeId.value,
      selectedEmployeeId.value,
      authStore.accessToken,
      {
        document_id: documentLinkDraft.document_id.trim(),
        relation_type: documentLinkDraft.relation_type || "employee_document",
        label: emptyToNull(documentLinkDraft.label || ""),
      },
    );
    await selectEmployee(selectedEmployeeId.value, { preserveActiveTab: true });
    setFeedback("success", t("employeeAdmin.feedback.titleSuccess"), t("employeeAdmin.feedback.documentLinked"));
  } catch (error) {
    setFeedback("error", t("employeeAdmin.feedback.titleError"), resolveEmployeeDocumentErrorMessage(error));
  } finally {
    loading.action = false;
  }
}

async function submitEmployeeDocumentVersion() {
  if (
    !pendingEmployeeDocumentVersionFile.value
    || !selectedEmployeeDocumentId.value
    || !selectedEmployeeId.value
    || !resolvedTenantScopeId.value
    || !authStore.accessToken
  ) {
    return;
  }

  loading.action = true;
  try {
    const payload: EmployeeDocumentVersionPayload = {
      file_name: pendingEmployeeDocumentVersionFile.value.name,
      content_type: pendingEmployeeDocumentVersionFile.value.type || "application/octet-stream",
      content_base64: await fileToBase64(pendingEmployeeDocumentVersionFile.value),
    };
    await addEmployeeDocumentVersion(
      resolvedTenantScopeId.value,
      selectedEmployeeId.value,
      selectedEmployeeDocumentId.value,
      authStore.accessToken,
      payload,
    );
    await selectEmployee(selectedEmployeeId.value, { preserveActiveTab: true });
    setFeedback("success", t("employeeAdmin.feedback.titleSuccess"), t("employeeAdmin.feedback.documentVersionSaved"));
  } catch (error) {
    setFeedback("error", t("employeeAdmin.feedback.titleError"), resolveEmployeeDocumentErrorMessage(error));
  } finally {
    loading.action = false;
  }
}

async function submitPhoto() {
  if (!pendingPhotoFile.value || !selectedEmployeeId.value || !resolvedTenantScopeId.value || !authStore.accessToken) {
    return;
  }
  loading.action = true;
  try {
    const contentBase64 = await fileToBase64(pendingPhotoFile.value);
    await uploadEmployeePhoto(resolvedTenantScopeId.value, selectedEmployeeId.value, authStore.accessToken, {
      title: pendingPhotoFile.value.name,
      file_name: pendingPhotoFile.value.name,
      content_type: pendingPhotoFile.value.type || "application/octet-stream",
      content_base64: contentBase64,
    });
    pendingPhotoFile.value = null;
    await selectEmployee(selectedEmployeeId.value, { preserveActiveTab: true });
    setFeedback("success", t("employeeAdmin.feedback.titleSuccess"), t("employeeAdmin.feedback.photoSaved"));
  } catch (error) {
    const key = error instanceof EmployeeAdminApiError ? mapEmployeeApiMessage(error.messageKey) : "employeeAdmin.feedback.error";
    setFeedback("error", t("employeeAdmin.feedback.titleError"), t(key as never));
  } finally {
    loading.action = false;
  }
}

async function loadImportFile() {
  if (!pendingImportFile.value) {
    return;
  }
  importDraft.csv_text = await pendingImportFile.value.text();
}

async function runImportDryRun() {
  if (!resolvedTenantScopeId.value || !authStore.accessToken) {
    return;
  }
  loading.action = true;
  try {
    importDryRunResult.value = await importEmployeesDryRun(resolvedTenantScopeId.value, authStore.accessToken, {
      tenant_id: resolvedTenantScopeId.value,
      csv_content_base64: btoa(unescape(encodeURIComponent(importDraft.csv_text))),
    });
    setFeedback("success", t("employeeAdmin.feedback.titleSuccess"), t("employeeAdmin.feedback.importDryRunReady"));
  } catch (error) {
    const key = error instanceof EmployeeAdminApiError ? mapEmployeeApiMessage(error.messageKey) : "employeeAdmin.feedback.error";
    setFeedback("error", t("employeeAdmin.feedback.titleError"), t(key as never));
  } finally {
    loading.action = false;
  }
}

async function runImportExecute() {
  if (!resolvedTenantScopeId.value || !authStore.accessToken) {
    return;
  }
  loading.action = true;
  try {
    lastImportResult.value = await importEmployeesExecute(resolvedTenantScopeId.value, authStore.accessToken, {
      tenant_id: resolvedTenantScopeId.value,
      csv_content_base64: btoa(unescape(encodeURIComponent(importDraft.csv_text))),
      continue_on_error: importDraft.continue_on_error,
    });
    await refreshEmployees();
    setFeedback("success", t("employeeAdmin.feedback.titleSuccess"), t("employeeAdmin.feedback.importExecuted"));
  } catch (error) {
    const key = error instanceof EmployeeAdminApiError ? mapEmployeeApiMessage(error.messageKey) : "employeeAdmin.feedback.error";
    setFeedback("error", t("employeeAdmin.feedback.titleError"), t(key as never));
  } finally {
    loading.action = false;
  }
}

async function runExport() {
  if (!resolvedTenantScopeId.value || !authStore.accessToken) {
    return;
  }
  loading.action = true;
  try {
    lastExportResult.value = await exportEmployees(resolvedTenantScopeId.value, authStore.accessToken, {
      tenant_id: resolvedTenantScopeId.value,
      search: emptyToNull(filters.search),
      include_archived: filters.include_archived,
    });
    setFeedback("success", t("employeeAdmin.feedback.titleSuccess"), t("employeeAdmin.feedback.exportReady"));
  } catch (error) {
    const key = error instanceof EmployeeAdminApiError ? mapEmployeeApiMessage(error.messageKey) : "employeeAdmin.feedback.error";
    setFeedback("error", t("employeeAdmin.feedback.titleError"), t(key as never));
  } finally {
    loading.action = false;
  }
}

async function createAccessUser() {
  if (!resolvedTenantScopeId.value || !authStore.accessToken || !selectedEmployeeId.value) {
    return;
  }
  loading.action = true;
  try {
    accessLink.value = await createEmployeeAccessUser(
      resolvedTenantScopeId.value,
      selectedEmployeeId.value,
      authStore.accessToken,
      {
        tenant_id: resolvedTenantScopeId.value,
        username: accessCreateDraft.username.trim(),
        email: accessCreateDraft.email.trim(),
        password: accessCreateDraft.password,
      },
    );
    await selectEmployee(selectedEmployeeId.value, { preserveActiveTab: true });
    setFeedback("success", t("employeeAdmin.feedback.titleSuccess"), t("employeeAdmin.feedback.accessLinked"));
  } catch (error) {
    const key = error instanceof EmployeeAdminApiError ? mapEmployeeApiMessage(error.messageKey) : "employeeAdmin.feedback.error";
    setFeedback("error", t("employeeAdmin.feedback.titleError"), t(key as never));
  } finally {
    loading.action = false;
  }
}

async function updateAccessUser() {
  if (!resolvedTenantScopeId.value || !authStore.accessToken || !selectedEmployeeId.value || !hasLinkedAccess.value) {
    return;
  }
  loading.action = true;
  try {
    accessLink.value = await updateEmployeeAccessUser(
      resolvedTenantScopeId.value,
      selectedEmployeeId.value,
      authStore.accessToken,
      {
        tenant_id: resolvedTenantScopeId.value,
        username: accessManageDraft.username.trim(),
        email: accessManageDraft.email.trim(),
        full_name: accessManageDraft.full_name.trim(),
      },
    );
    await selectEmployee(selectedEmployeeId.value, { preserveActiveTab: true });
    setFeedback("success", t("employeeAdmin.feedback.titleSuccess"), t("employeeAdmin.feedback.accessUpdated"));
  } catch (error) {
    const key = error instanceof EmployeeAdminApiError ? mapEmployeeApiMessage(error.messageKey) : "employeeAdmin.feedback.error";
    setFeedback("error", t("employeeAdmin.feedback.titleError"), t(key as never));
  } finally {
    loading.action = false;
  }
}

async function resetAccessPassword() {
  if (!resolvedTenantScopeId.value || !authStore.accessToken || !selectedEmployeeId.value || !hasLinkedAccess.value) {
    return;
  }
  loading.action = true;
  try {
    accessLink.value = await resetEmployeeAccessUserPassword(
      resolvedTenantScopeId.value,
      selectedEmployeeId.value,
      authStore.accessToken,
      {
        tenant_id: resolvedTenantScopeId.value,
        password: accessResetDraft.password,
      },
    );
    await selectEmployee(selectedEmployeeId.value, { preserveActiveTab: true });
    setFeedback("success", t("employeeAdmin.feedback.titleSuccess"), t("employeeAdmin.feedback.accessPasswordReset"));
  } catch (error) {
    const key = error instanceof EmployeeAdminApiError ? mapEmployeeApiMessage(error.messageKey) : "employeeAdmin.feedback.error";
    setFeedback("error", t("employeeAdmin.feedback.titleError"), t(key as never));
  } finally {
    loading.action = false;
  }
}

async function attachAccessUser() {
  if (!resolvedTenantScopeId.value || !authStore.accessToken || !selectedEmployeeId.value) {
    return;
  }
  loading.action = true;
  try {
    accessLink.value = await attachEmployeeAccessUser(
      resolvedTenantScopeId.value,
      selectedEmployeeId.value,
      authStore.accessToken,
      {
        tenant_id: resolvedTenantScopeId.value,
        user_id: emptyToNull(accessAttachDraft.user_id),
        username: emptyToNull(accessAttachDraft.username),
        email: emptyToNull(accessAttachDraft.email),
      },
    );
    await selectEmployee(selectedEmployeeId.value, { preserveActiveTab: true });
    setFeedback("success", t("employeeAdmin.feedback.titleSuccess"), t("employeeAdmin.feedback.accessLinked"));
  } catch (error) {
    const key = error instanceof EmployeeAdminApiError ? mapEmployeeApiMessage(error.messageKey) : "employeeAdmin.feedback.error";
    setFeedback("error", t("employeeAdmin.feedback.titleError"), t(key as never));
  } finally {
    loading.action = false;
  }
}

async function detachAccessUser() {
  if (!resolvedTenantScopeId.value || !authStore.accessToken || !selectedEmployeeId.value) {
    return;
  }
  loading.action = true;
  try {
    accessLink.value = await detachEmployeeAccessUser(
      resolvedTenantScopeId.value,
      selectedEmployeeId.value,
      authStore.accessToken,
      { tenant_id: resolvedTenantScopeId.value },
    );
    await selectEmployee(selectedEmployeeId.value, { preserveActiveTab: true });
    setFeedback("success", t("employeeAdmin.feedback.titleSuccess"), t("employeeAdmin.feedback.accessDetached"));
  } catch (error) {
    const key = error instanceof EmployeeAdminApiError ? mapEmployeeApiMessage(error.messageKey) : "employeeAdmin.feedback.error";
    setFeedback("error", t("employeeAdmin.feedback.titleError"), t(key as never));
  } finally {
    loading.action = false;
  }
}

async function reconcileAccessUser() {
  if (!resolvedTenantScopeId.value || !authStore.accessToken || !selectedEmployeeId.value) {
    return;
  }
  loading.action = true;
  try {
    accessLink.value = await reconcileEmployeeAccessUser(
      resolvedTenantScopeId.value,
      selectedEmployeeId.value,
      authStore.accessToken,
    );
    await selectEmployee(selectedEmployeeId.value, { preserveActiveTab: true });
    setFeedback("success", t("employeeAdmin.feedback.titleSuccess"), t("employeeAdmin.feedback.accessReconciled"));
  } catch (error) {
    const key = error instanceof EmployeeAdminApiError ? mapEmployeeApiMessage(error.messageKey) : "employeeAdmin.feedback.error";
    setFeedback("error", t("employeeAdmin.feedback.titleError"), t(key as never));
  } finally {
    loading.action = false;
  }
}

async function downloadDocument(document: EmployeeDocumentListItemRead | EmployeePhotoRead | null) {
  if (!document?.current_version_no || !resolvedTenantScopeId.value || !authStore.accessToken) {
    return;
  }
  try {
    const file = await downloadEmployeeDocument(
      resolvedTenantScopeId.value,
      document.document_id,
      document.current_version_no,
      authStore.accessToken,
    );
    const url = URL.createObjectURL(file.blob);
    const anchor = window.document.createElement("a");
    anchor.href = url;
    anchor.download = file.fileName;
    anchor.click();
    URL.revokeObjectURL(url);
  } catch (error) {
    const key = error instanceof EmployeeAdminApiError ? mapEmployeeApiMessage(error.messageKey) : "employeeAdmin.feedback.error";
    setFeedback("error", t("employeeAdmin.feedback.titleError"), t(key as never));
  }
}

function emptyToNull(value: string) {
  const trimmed = value.trim();
  return trimmed || null;
}

watch(
  () => [isCreatingEmployee.value, !!selectedEmployee.value, canReadPrivate.value],
  () => {
    const allowedTabs = employeeDetailTabs.value.map((tab) => tab.id);
    if (!allowedTabs.includes(activeDetailTab.value)) {
      activeDetailTab.value = resolveEmployeeDetailTab(activeDetailTab.value, allowedTabs);
    }
  },
  { immediate: true },
);

watch(
  () => qualificationDraft.record_kind,
  (recordKind) => {
    if (recordKind === "function") {
      qualificationDraft.qualification_type_id = "";
    } else {
      qualificationDraft.function_type_id = "";
    }
  },
);

watch(
  () => availabilityDraft.recurrence_type,
  (recurrenceType) => {
    if (recurrenceType !== "weekly") {
      availabilityDraft.weekday_indexes = [];
    }
  },
);

watch(
  () => [
    selectedEmployee.value?.id,
    selectedEmployee.value?.personnel_no,
    selectedEmployee.value?.first_name,
    selectedEmployee.value?.last_name,
    selectedEmployee.value?.work_email,
    accessLink.value?.user_id,
    accessLink.value?.username,
    accessLink.value?.email,
    accessLink.value?.full_name,
    resolvedTenantScopeId.value,
  ],
  () => {
    syncAccessCreateDraft();
    syncAccessManageDraft();
  },
  { immediate: true },
);

watch(
  () => employeeDraft.default_branch_id,
  (branchId) => {
    if (!employeeDraft.default_mandate_id) {
      return;
    }
    const mandateStillValid = filterMandateOptions(branchId).some((mandate) => mandate.id === employeeDraft.default_mandate_id);
    if (!mandateStillValid) {
      employeeDraft.default_mandate_id = "";
    }
  },
);

watch(
  () => filters.default_branch_id,
  (branchId) => {
    if (!filters.default_mandate_id) {
      return;
    }
    const mandateStillValid = filterMandateOptions(branchId).some((mandate) => mandate.id === filters.default_mandate_id);
    if (!mandateStillValid) {
      filters.default_mandate_id = "";
    }
  },
);

watch(
  () => [authStore.effectiveRole, authStore.effectiveTenantScopeId] as const,
  () => {
    if (!isPlatformAdmin.value) {
      tenantScopeInput.value = authStore.effectiveTenantScopeId || authStore.tenantScopeId;
    }
  },
  { immediate: true },
);

function fileToBase64(file: File) {
  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = typeof reader.result === "string" ? reader.result : "";
      resolve(result.split(",")[1] || "");
    };
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}

onMounted(async () => {
  authStore.syncFromPrimarySession();
  try {
    await authStore.ensureSessionReady();
  } catch {
    // handled by store
  }
  tenantScopeInput.value = authStore.effectiveTenantScopeId || authStore.tenantScopeId;
  resetEmployeeDraft();
  await refreshEmployees();
});

onBeforeUnmount(() => {
  clearPhotoPreview();
});
</script>

<style scoped>
.employee-admin-page,
.employee-admin-list,
.employee-admin-form-grid,
.employee-admin-record-list {
  display: grid;
  gap: 1rem;
  min-width: 0;
}

.employee-admin-grid {
  display: grid;
  gap: var(--sp-page-gap, 1.25rem);
  grid-template-columns: minmax(320px, 420px) minmax(0, 1fr);
  align-items: start;
}

.employee-admin-list-panel {
  position: sticky;
  top: 0;
}

.employee-admin-hero {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 1rem;
  align-items: start;
  min-width: 0;
}

.employee-admin-panel,
.employee-admin-section,
.employee-admin-tab-panel,
.employee-admin-empty,
.employee-admin-scope {
  display: grid;
  gap: 1rem;
  min-width: 0;
}

.employee-admin-scope--embedded {
  margin-bottom: 0.25rem;
}

.employee-admin-meta,
.employee-admin-summary,
.employee-admin-photo__controls {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  min-width: 0;
}

.employee-admin-photo {
  display: grid;
  gap: 1rem;
  grid-template-columns: minmax(180px, 240px) minmax(0, 1fr);
  align-items: start;
  min-width: 0;
}

.employee-admin-meta__pill,
.employee-admin-summary__card,
.employee-admin-record,
.employee-admin-photo__preview {
  padding: 0.75rem 1rem;
  border-radius: 16px;
  background: var(--sp-color-surface-page);
}

.employee-admin-row,
.employee-admin-record {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 1rem;
  align-items: center;
  min-width: 0;
  padding: 1rem;
  border-radius: 18px;
  border: 1px solid var(--sp-color-border-soft);
  background: var(--sp-color-surface-page);
  text-align: left;
  cursor: pointer;
}

.employee-admin-summary__card {
  display: grid;
  gap: 0.35rem;
  min-width: min(100%, 180px);
  flex: 1 1 180px;
}

.employee-admin-summary__card span,
.employee-admin-record__meta,
.employee-admin-list-empty {
  color: var(--sp-color-text-secondary);
}

.employee-admin-summary__card strong,
.employee-admin-record__body strong {
  color: var(--sp-color-text-primary);
}

.employee-admin-row {
  appearance: none;
}

.employee-admin-row > *,
.employee-admin-record > * {
  min-width: 0;
}

.employee-admin-row__text {
  display: grid;
  gap: 0.35rem;
  min-width: 0;
  flex: 1 1 auto;
}

.employee-admin-row__title,
.employee-admin-row__meta {
  display: block;
}

.employee-admin-row__title {
  color: var(--sp-color-text-primary);
}

.employee-admin-row__meta {
  color: var(--sp-color-text-secondary);
}

.employee-admin-row.selected,
.employee-admin-record.selected {
  border-color: var(--sp-color-primary);
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--sp-color-primary) 40%, transparent);
}

.employee-admin-record--static {
  cursor: default;
}

.employee-admin-record__body {
  display: grid;
  gap: 0.35rem;
  min-width: 0;
  flex: 1 1 auto;
}

.employee-admin-record__button {
  appearance: none;
  border: 0;
  background: transparent;
  padding: 0;
  text-align: left;
  cursor: pointer;
}

.employee-admin-record__meta {
  margin: 0;
}

.employee-admin-record__actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 0.65rem;
  align-items: center;
}

.employee-admin-panel__header {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 1rem;
  align-items: start;
  min-width: 0;
}

.employee-admin-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.employee-admin-tabs--panel {
  margin-top: -0.1rem;
}

.employee-admin-tab {
  border: 1px solid var(--sp-color-border-soft);
  background: var(--sp-color-surface-page);
  color: var(--sp-color-text-secondary);
  border-radius: 999px;
  padding: 0.6rem 1rem;
  font: inherit;
  cursor: pointer;
  transition:
    border-color 0.18s ease,
    color 0.18s ease,
    background-color 0.18s ease,
    box-shadow 0.18s ease;
}

.employee-admin-tab.active {
  border-color: var(--sp-color-primary);
  color: var(--sp-color-primary-strong);
  background: color-mix(in srgb, var(--sp-color-primary-muted) 70%, white);
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--sp-color-primary) 28%, transparent);
}

.employee-admin-detail,
.employee-admin-form,
.employee-admin-inline-form {
  display: grid;
  gap: 1rem;
  min-width: 0;
}

.employee-admin-form--structured {
  gap: 1.1rem;
}

.employee-admin-editor-intro,
.employee-admin-form-section,
.employee-admin-form-actions {
  display: grid;
  gap: 0.85rem;
  padding: 1rem 1.1rem;
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 18px;
  background: color-mix(in srgb, var(--sp-color-surface-page) 76%, white 24%);
  min-width: 0;
}

.employee-admin-editor-intro h4,
.employee-admin-form-section__header h4,
.employee-admin-form-actions strong {
  margin: 0;
  color: var(--sp-color-text-primary);
}

.employee-admin-editor-intro .field-help {
  margin: 0;
}

.employee-admin-form-section__header {
  display: grid;
  gap: 0.25rem;
}

.employee-admin-form-section--nested {
  padding: 0.9rem 1rem;
  background: var(--sp-color-surface-card);
}

.employee-admin-advanced-access {
  display: grid;
  gap: 0.85rem;
  padding: 1rem 1.1rem;
  border: 1px dashed var(--sp-color-border-soft);
  border-radius: 18px;
  background: color-mix(in srgb, var(--sp-color-surface-page) 84%, white 16%);
}

.employee-admin-advanced-access summary {
  display: grid;
  gap: 0.2rem;
  cursor: pointer;
  list-style: none;
}

.employee-admin-advanced-access summary::-webkit-details-marker {
  display: none;
}

.employee-admin-form-grid--editor {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.85rem 1rem;
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

.field-help {
  margin: 0;
  font-size: 0.85rem;
}

.employee-admin-checkbox {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  min-width: 0;
  color: var(--sp-color-text-secondary);
}

.employee-admin-checkbox input[type='checkbox'] {
  width: 1rem;
  height: 1rem;
  margin: 0;
  accent-color: var(--sp-color-primary);
}

.employee-admin-weekday-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem 1rem;
}

.employee-admin-form-actions {
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
}

.employee-admin-photo__preview {
  max-width: 100%;
  min-width: 160px;
  min-height: 160px;
  display: grid;
  place-items: center;
}

.employee-admin-form-grid > *,
.employee-admin-record-list > *,
.employee-admin-list > * {
  min-width: 0;
}

.employee-admin-photo__preview img {
  max-width: 160px;
  max-height: 160px;
  border-radius: 16px;
  object-fit: cover;
}

@media (max-width: 1080px) {
  .employee-admin-grid,
  .employee-admin-hero,
  .employee-admin-photo {
    grid-template-columns: 1fr;
    display: grid;
  }

  .employee-admin-list-panel {
    position: static;
  }
}

@media (max-width: 820px) {
  .employee-admin-form-grid--editor,
  .employee-admin-form-actions {
    grid-template-columns: 1fr;
  }

  .employee-admin-record__actions {
    justify-content: flex-start;
  }
}
</style>
