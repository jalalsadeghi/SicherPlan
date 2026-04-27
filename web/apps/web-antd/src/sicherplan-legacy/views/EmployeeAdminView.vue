<template>
  <section class="employee-admin-page">
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
        <button class="cta-button cta-secondary" type="button" :disabled="!canRead" @click="() => refreshEmployees()">
          {{ t("employeeAdmin.actions.refresh") }}
        </button>
      </div>
    </div>

    <section v-if="isEmployeeSessionResolving && !resolvedTenantScopeId" class="module-card employee-admin-empty">
      <p class="eyebrow">{{ t("employeeAdmin.scope.reconcilingTitle") }}</p>
      <h3>{{ t("employeeAdmin.scope.reconcilingBody") }}</h3>
    </section>

    <section v-else-if="!resolvedTenantScopeId" class="module-card employee-admin-empty">
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
        <div v-if="employeeAdminListMode" class="employee-admin-mode-shell" data-testid="employee-list-only-mode">
          <section class="module-card employee-admin-panel employee-admin-list-panel" data-testid="employee-list-section">
            <div class="employee-admin-panel__header">
              <div>
                <p class="eyebrow">{{ t("employeeAdmin.list.eyebrow") }}</p>
                <h3>{{ t("employeeAdmin.list.title") }}</h3>
              </div>
              <div class="employee-admin-list-header-actions">
                <button
                  class="cta-button cta-secondary employee-admin-header-action"
                  data-testid="employee-list-header-import-export"
                  type="button"
                  @click="openImportExportDialog"
                >
                  {{ t("employeeAdmin.import.eyebrow") }}
                </button>
                <button
                  class="cta-button cta-secondary employee-admin-header-action"
                  data-assistant-action="employees.create.open"
                  data-assistant-page-id="E-01"
                  data-testid="employee-list-header-new-employee"
                  type="button"
                  :disabled="!actionState.canCreate"
                  @click="startCreateEmployee"
                >
                  {{ t("employeeAdmin.actions.newEmployee") }}
                </button>
                <StatusBadge :status="loading.list ? 'inactive' : 'active'" />
              </div>
            </div>

            <div class="employee-admin-filter-toolbar" data-testid="employee-list-filter-toolbar">
              <label class="field-stack employee-admin-search-field">
                <span>{{ t("employeeAdmin.filters.search") }}</span>
                <div class="employee-admin-search-select" data-testid="employee-search-select">
                  <input
                    v-model="filters.search"
                    :placeholder="t('employeeAdmin.filters.searchPlaceholder')"
                    data-testid="employee-search-select-input"
                  />
                </div>
              </label>
              <div class="employee-admin-filter-toolbar__actions">
                <button
                  class="cta-button cta-secondary"
                  data-testid="employee-advanced-filters-open"
                  type="button"
                  @click="openAdvancedFiltersDialog"
                >
                  {{ t("employeeAdmin.actions.advancedFilters") }}
                </button>
              </div>
            </div>

            <p
              v-if="!filteredEmployees.length"
              class="employee-admin-list-empty"
              data-testid="employee-list-empty-state"
            >
              {{ t("employeeAdmin.list.empty") }}
            </p>
            <div v-else class="employee-admin-record-list" data-testid="employee-list-rows">
            <button
              v-for="employee in filteredEmployees"
              :key="employee.id"
              type="button"
              class="employee-admin-record employee-admin-list-row employee-admin-employee-row"
              :class="{ selected: employee.id === selectedEmployeeId && employeeAdminDetailMode && !isCreatingEmployee }"
              data-testid="employee-list-row"
              :aria-label="`${employee.personnel_no} · ${employee.first_name} ${employee.last_name}`"
              @click="openEmployeeWorkspace(employee.id)"
            >
              <div class="employee-admin-employee-row__avatar" data-testid="employee-list-row-avatar" aria-hidden="true">
                <img
                  v-if="shouldShowEmployeeListPhoto(employee)"
                  :src="getEmployeeListPhotoUrl(employee)"
                  :alt="`${employee.first_name} ${employee.last_name}`"
                  class="employee-admin-employee-row__avatar-image"
                  data-testid="employee-list-row-avatar-image"
                  @error="markEmployeeListPhotoFailed(employee.id)"
                />
                <span v-else>{{ getEmployeeInitials(employee) }}</span>
              </div>
              <div class="employee-admin-record__body employee-admin-employee-row__body">
                <strong class="employee-admin-employee-row__line employee-admin-employee-row__line--primary">
                  {{ employee.personnel_no }} · {{ employee.first_name }} {{ employee.last_name }}
                </strong>
                <span class="employee-admin-record__meta employee-admin-employee-row__line employee-admin-employee-row__meta">
                  <template v-if="employee.preferred_name">{{ employee.preferred_name }} · </template>{{ resolveEmployeeSuggestionContact(employee) }}
                  <template v-if="formatEmployeeListContext(employee) !== t('employeeAdmin.summary.none')"> · {{ formatEmployeeListContext(employee) }}</template>
                </span>
              </div>
              <StatusBadge :status="employee.status" data-testid="employee-list-row-status" />
            </button>
            </div>
          </section>

          <div
            v-if="advancedFiltersModalOpen"
            class="employee-admin-modal-backdrop"
            data-testid="employee-advanced-filters-dialog-backdrop"
            @click.self="closeAdvancedFiltersDialog"
          >
            <section
              class="module-card employee-admin-modal"
              aria-labelledby="employee-advanced-filters-title"
              aria-modal="true"
              role="dialog"
              data-testid="employee-advanced-filters-dialog"
            >
              <form class="employee-admin-form-section" @submit.prevent="applyAdvancedFilters">
                <div class="employee-admin-form-section__header employee-admin-form-section__header--split">
                  <div>
                    <p class="eyebrow">{{ t("employeeAdmin.filters.additionalTitle") }}</p>
                    <h4 id="employee-advanced-filters-title">{{ t("employeeAdmin.filters.searchEmployees") }}</h4>
                  </div>
                  <button
                    class="cta-button cta-secondary"
                    type="button"
                    data-testid="employee-advanced-filters-cancel"
                    @click="closeAdvancedFiltersDialog"
                  >
                    {{ t("employeeAdmin.actions.closeFilters") }}
                  </button>
                </div>

                <div class="employee-admin-filter-grid employee-admin-filter-grid--dialog">
                  <label class="field-stack employee-admin-search-field">
                    <span>{{ t("employeeAdmin.filters.search") }}</span>
                    <div class="employee-admin-search-select">
                      <input
                        v-model="filters.search"
                        :placeholder="t('employeeAdmin.filters.searchPlaceholder')"
                        data-testid="employee-advanced-filters-search"
                      />
                    </div>
                  </label>
                  <label class="field-stack">
                    <span>{{ t("employeeAdmin.filters.status") }}</span>
                    <select v-model="advancedFilterDraft.status" data-testid="employee-advanced-filters-status">
                      <option value="">{{ t("employeeAdmin.filters.allStatuses") }}</option>
                      <option value="active">{{ t("employeeAdmin.status.active") }}</option>
                      <option value="inactive">{{ t("employeeAdmin.status.inactive") }}</option>
                      <option value="archived">{{ t("employeeAdmin.status.archived") }}</option>
                    </select>
                  </label>
                  <label class="field-stack">
                    <span>{{ t("employeeAdmin.fields.defaultBranchId") }}</span>
                    <select
                      v-model="advancedFilterDraft.default_branch_id"
                      data-testid="employee-advanced-filters-default-branch"
                    >
                      <option value="">{{ t("employeeAdmin.summary.none") }}</option>
                      <option v-for="branch in branchOptions" :key="branch.id" :value="branch.id">
                        {{ formatStructureLabel(branch) }}
                      </option>
                    </select>
                  </label>
                  <label class="field-stack">
                    <span>{{ t("employeeAdmin.fields.defaultMandateId") }}</span>
                    <select
                      v-model="advancedFilterDraft.default_mandate_id"
                      data-testid="employee-advanced-filters-default-mandate"
                    >
                      <option value="">{{ t("employeeAdmin.summary.none") }}</option>
                      <option
                        v-for="mandate in filterMandateOptions(advancedFilterDraft.default_branch_id)"
                        :key="mandate.id"
                        :value="mandate.id"
                      >
                        {{ formatStructureLabel(mandate) }}
                      </option>
                    </select>
                  </label>
                </div>

                <label class="employee-admin-checkbox">
                  <input
                    v-model="advancedFilterDraft.include_archived"
                    data-testid="employee-advanced-filters-include-archived"
                    type="checkbox"
                  />
                  <span>{{ t("employeeAdmin.filters.includeArchived") }}</span>
                </label>

                <div class="cta-row employee-admin-modal-actions">
                  <button class="cta-button" data-testid="employee-advanced-filters-apply" type="submit">
                    {{ t("employeeAdmin.actions.search") }}
                  </button>
                  <button class="cta-button cta-secondary" type="button" @click="closeAdvancedFiltersDialog">
                    {{ t("employeeAdmin.actions.closeFilters") }}
                  </button>
                </div>
              </form>
            </section>
          </div>

          <div
            v-if="importExportModalOpen"
            class="employee-admin-modal-backdrop"
            data-testid="employee-import-export-modal-backdrop"
            @click.self="closeImportExportDialog"
          >
            <section
              class="module-card employee-admin-modal"
              aria-labelledby="employee-import-export-title"
              aria-modal="true"
              role="dialog"
              data-testid="employee-import-export-modal"
            >
              <div class="employee-admin-form-section">
                <div class="employee-admin-form-section__header employee-admin-form-section__header--split">
                  <div>
                    <p class="eyebrow">{{ t("employeeAdmin.import.eyebrow") }}</p>
                    <h4 id="employee-import-export-title">{{ t("employeeAdmin.import.title") }}</h4>
                  </div>
                  <button
                    class="cta-button cta-secondary"
                    type="button"
                    data-testid="employee-import-export-close"
                    @click="closeImportExportDialog"
                  >
                    {{ t("employeeAdmin.actions.cancel") }}
                  </button>
                </div>
                <div data-testid="employee-import-export-panel">
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
                </div>
              </div>
            </section>
          </div>

        </div>

      <div v-else class="employee-admin-mode-shell" data-testid="employee-detail-only-mode">
      <section class="module-card employee-admin-panel employee-admin-detail" data-testid="employee-detail-workspace">
        <div class="employee-admin-panel__header">
          <div>
            <p class="eyebrow">{{ t("employeeAdmin.detail.eyebrow") }}</p>
            <h3>{{ detailWorkspaceTitle }}</h3>
          </div>
          <div class="employee-admin-detail-header-actions">
            <button
              class="cta-button cta-secondary employee-admin-back-button"
              type="button"
              data-testid="employee-detail-back-to-list"
              @click="returnToEmployeeList"
            >
              {{ t("employeeAdmin.actions.backToEmployeeList") }}
            </button>
            <StatusBadge v-if="selectedEmployee && !isCreatingEmployee" :status="selectedEmployee.status" />
          </div>
        </div>

        <nav class="employee-admin-tabs" data-testid="employee-detail-tabs" aria-label="Employee detail sections">
            <button
              v-for="tab in employeeDetailTabs"
              :key="tab.id"
              type="button"
              class="employee-admin-tab"
              :class="{ active: tab.id === activeDetailTab }"
              :data-testid="`employee-tab-${tab.id}`"
              :disabled="isEmployeeDetailTabDisabled(tab.id)"
              @click="selectEmployeeDetailTab(tab.id)"
            >
              {{ tab.label }}
            </button>
        </nav>

        <template v-if="isCreatingEmployee || selectedEmployee">
          <EmployeeDashboardTab
            v-if="selectedEmployee && !isCreatingEmployee && activeDetailTab === 'dashboard'"
            :access-token="authStore.accessToken"
            :can-manage-photo="actionState.canManagePhoto"
            :can-read-staffing="canReadStaffing"
            :employee="selectedEmployee"
            :photo-uploading="loading.photo"
            :photo-preview-url="photoPreviewUrl"
            :selected-employee-branch-label="selectedEmployeeBranchLabel"
            :selected-employee-mandate-label="selectedEmployeeMandateLabel"
            :tenant-id="resolvedTenantScopeId"
            data-testid="employee-tab-panel-dashboard"
            @photo-selected="submitDashboardPhoto"
          />

          <section
            v-if="activeDetailTab === 'overview'"
            class="employee-admin-tab-panel"
            data-testid="employee-tab-panel-overview"
          >
            <section ref="overviewOnePageRef" class="employee-admin-overview-onepage" data-testid="employee-overview-onepage">
            <aside
              v-if="visibleEmployeeOverviewSections.length > 1"
              class="employee-admin-overview-nav-shell"
              :class="{
                'employee-admin-overview-nav-shell--fixed': overviewNavFloatingMode === 'fixed',
                'employee-admin-overview-nav-shell--pinned': overviewNavFloatingMode === 'pinned',
              }"
              :style="overviewNavFloatingStyle"
              ref="overviewNavShellRef"
              data-testid="employee-overview-section-nav"
            >
              <nav
                :aria-label="t('employeeAdmin.tabs.overview')"
                class="employee-admin-overview-nav"
              >
                <button
                  v-for="section in visibleEmployeeOverviewSections"
                  :key="section.id"
                  type="button"
                  :aria-current="section.id === activeOverviewSection ? 'true' : undefined"
                  class="employee-admin-overview-nav__link"
                  :class="{ 'employee-admin-overview-nav__link--active': section.id === activeOverviewSection }"
                  :data-testid="section.testId"
                  @click="selectOverviewSection(section.id)"
                >
                  <IconifyIcon class="employee-admin-overview-nav__icon" :icon="section.icon" aria-hidden="true" />
                  <span>{{ section.label }}</span>
                </button>
              </nav>
            </aside>

            <div class="employee-admin-overview-content">
          <section
            id="employee-overview-section-file"
            class="employee-admin-overview-section-card"
            data-testid="employee-overview-section-file"
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
            <section class="employee-admin-overview-section-card__header">
              <div>
                <p class="eyebrow">{{ t("employeeAdmin.form.eyebrow") }}</p>
                <h4>{{ t("employeeAdmin.form.title") }}</h4>
              </div>
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
            v-if="isEmployeeOverviewSectionVisible('app_access')"
            id="employee-overview-section-app-access"
            class="employee-admin-overview-section-card"
            data-testid="employee-overview-section-app-access"
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
                <span>{{ t("employeeAdmin.access.linked") }}</span>
                <strong>{{ hasLinkedAccess ? t("employeeAdmin.access.linkedYes") : t("employeeAdmin.access.linkedNo") }}</strong>
              </article>
              <article class="employee-admin-summary__card">
                <span>{{ t("employeeAdmin.access.loginReady") }}</span>
                <strong>
                  {{
                    accessLink?.diagnostics.can_mobile_login
                      ? t("employeeAdmin.access.loginReadyYes")
                      : t("employeeAdmin.access.loginReadyNo")
                  }}
                </strong>
              </article>
              <article class="employee-admin-summary__card">
                <span>{{ t("employeeAdmin.access.manageFullName") }}</span>
                <strong>{{ accessLink?.full_name || t("employeeAdmin.summary.none") }}</strong>
              </article>
            </div>
            <div class="employee-admin-form employee-admin-form--structured">
              <section class="employee-admin-overview-section-card__header employee-admin-overview-section-card__header--split">
                <div>
                  <p class="eyebrow">{{ t("employeeAdmin.access.eyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.access.title") }}</h4>
                </div>
                <div class="employee-admin-overview-section-card__header-actions">
                  <button
                    v-if="accessLink"
                    class="cta-button cta-secondary employee-admin-header-action"
                    type="button"
                    data-testid="employee-access-diagnostics-open"
                    @click="openAccessDiagnosticsDialog"
                  >
                    {{ t("employeeAdmin.access.openDiagnostics") }}
                  </button>
                </div>
              </section>

              <section v-if="!hasLinkedAccess" class="employee-admin-form-section">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.access.stateCreateEyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.access.stateCreateTitle") }}</h4>
                </div>
                <div class="employee-admin-form-section employee-admin-form-section--nested">
                  <div class="employee-admin-form-section__header">
                    <p class="eyebrow">{{ t("employeeAdmin.access.createEyebrow") }}</p>
                    <h4>{{ t("employeeAdmin.access.createTitle") }}</h4>
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
                </div>

                <div class="employee-admin-form-section employee-admin-form-section--nested">
                  <div class="employee-admin-form-section__header">
                    <p class="eyebrow">{{ t("employeeAdmin.access.manageEyebrow") }}</p>
                    <h4>{{ t("employeeAdmin.access.manageTitle") }}</h4>
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
                    <button
                      class="cta-button cta-secondary"
                      type="button"
                      data-testid="employee-access-reset-password-open"
                      :disabled="!actionState.canManageAccess"
                      @click="openResetPasswordDialog"
                    >
                      {{ t("employeeAdmin.access.openResetPassword") }}
                    </button>
                    <button
                      class="cta-button cta-secondary"
                      type="button"
                      data-testid="employee-access-detach-button"
                      :disabled="!actionState.canManageAccess || !accessLink?.user_id"
                      @click="detachAccessUser"
                    >
                      {{ t("employeeAdmin.actions.detachAccessUser") }}
                    </button>
                  </div>
                </div>
              </section>

              <section v-if="accessLink" class="employee-admin-form-section" data-testid="employee-access-diagnostics-section">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.access.diagnosticsEyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.access.diagnosticsTitle") }}</h4>
                </div>
                <p class="field-help">
                  {{ t("employeeAdmin.access.diagnosticsSummary", { passed: employeeAccessDiagnosticsPassedCount, total: employeeAccessDiagnosticChecks.length }) }}
                </p>
              </section>

              <details class="employee-admin-advanced-access">
                <summary>
                  <span class="eyebrow">{{ t("employeeAdmin.access.advancedEyebrow") }}</span>
                  <strong>{{ t("employeeAdmin.access.advancedSummary") }}</strong>
                </summary>

                <section class="employee-admin-form-section employee-admin-form-section--nested">
                  <div class="employee-admin-form-section__header">
                    <p class="eyebrow">{{ t("employeeAdmin.access.attachEyebrow") }}</p>
                    <h4>{{ t("employeeAdmin.access.attachTitle") }}</h4>
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
            v-if="isEmployeeOverviewSectionVisible('qualifications')"
            id="employee-overview-section-qualifications"
            class="employee-admin-overview-section-card"
            data-testid="employee-overview-section-qualifications"
          >
            <div class="employee-admin-form employee-admin-form--structured">
              <section class="employee-admin-overview-section-card__header">
                <div>
                  <p class="eyebrow">{{ t("employeeAdmin.qualifications.eyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.qualifications.title") }}</h4>
                </div>
              </section>

              <section class="employee-admin-form-section">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.qualifications.registerEyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.qualifications.registerTitle") }}</h4>
                </div>
                <div class="cta-row">
                  <button class="cta-button" type="button" :disabled="!actionState.canManageQualifications" @click="openNewQualificationEditor">
                    {{ t("employeeAdmin.actions.createQualification") }}
                  </button>
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

              <section class="employee-admin-form-section">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.qualifications.proofEyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.qualifications.proofTitle") }}</h4>
                </div>
                <p v-if="selectedQualification" class="field-help">
                  {{ t("employeeAdmin.qualifications.proofLead") }}: {{ selectedQualification.qualification_type?.label || selectedQualification.function_type?.label || selectedQualification.id }}
                </p>
                <div v-if="selectedQualification" class="cta-row">
                  <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canManageQualifications" @click="openQualificationProofEditor">
                    {{ t("employeeAdmin.actions.uploadQualificationProof") }}
                  </button>
                </div>
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
              </section>
            </div>
          </section>

          <section
            v-if="isEmployeeOverviewSectionVisible('credentials')"
            id="employee-overview-section-credentials"
            class="employee-admin-overview-section-card"
            data-testid="employee-overview-section-credentials"
          >
            <div class="employee-admin-form employee-admin-form--structured">
              <section class="employee-admin-overview-section-card__header">
                <div>
                  <p class="eyebrow">{{ t("employeeAdmin.credentials.eyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.credentials.title") }}</h4>
                </div>
              </section>

              <section class="employee-admin-form-section">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.credentials.registerEyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.credentials.registerTitle") }}</h4>
                </div>
                <div class="cta-row">
                  <button class="cta-button" type="button" :disabled="!actionState.canManageCredentials" @click="openNewCredentialEditor">
                    {{ t("employeeAdmin.actions.createCredential") }}
                  </button>
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
                      <button
                        class="cta-button cta-secondary"
                        type="button"
                        data-testid="employee-credential-edit-open"
                        :disabled="!actionState.canManageCredentials"
                        @click.stop="editCredential(credential)"
                      >
                        {{ t("employeeAdmin.actions.editCredential") }}
                      </button>
                      <button
                        v-if="!credential.archived_at"
                        class="cta-button cta-secondary"
                        type="button"
                        data-testid="employee-credential-archive-open"
                        :disabled="!actionState.canManageCredentials"
                        @click.stop="openCredentialLifecycleDialog(credential)"
                      >
                        {{ credentialLifecycleActionLabel(credential) }}
                      </button>
                      <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canManageCredentials" @click="issueCredentialBadge(credential)">
                        {{ t("employeeAdmin.actions.issueCredentialBadge") }}
                      </button>
                      <StatusBadge :status="credential.status" />
                    </div>
                  </article>
                </div>
                <p v-else class="employee-admin-list-empty">{{ t("employeeAdmin.credentials.empty") }}</p>
              </section>
            </div>
          </section>

          <section
            v-if="isEmployeeOverviewSectionVisible('availability')"
            id="employee-overview-section-availability"
            class="employee-admin-overview-section-card"
            data-testid="employee-overview-section-availability"
          >
            <div class="employee-admin-form employee-admin-form--structured">
              <section class="employee-admin-overview-section-card__header">
                <div>
                  <p class="eyebrow">{{ t("employeeAdmin.availability.eyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.availability.title") }}</h4>
                </div>
              </section>

              <section class="employee-admin-form-section">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.availability.registerEyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.availability.registerTitle") }}</h4>
                </div>
                <div class="cta-row">
                  <button class="cta-button" type="button" :disabled="!actionState.canManageAvailability" @click="openNewAvailabilityEditor">
                    {{ t("employeeAdmin.actions.createAvailability") }}
                  </button>
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
            </div>
          </section>

          <section
            v-if="isEmployeeOverviewSectionVisible('private_profile')"
            id="employee-overview-section-private-profile"
            class="employee-admin-overview-section-card"
            data-testid="employee-overview-section-private-profile"
          >
            <form class="employee-admin-form employee-admin-form--structured" @submit.prevent="submitPrivateProfile">
              <section class="employee-admin-overview-section-card__header">
                <div>
                  <p class="eyebrow">{{ t("employeeAdmin.privateProfile.eyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.privateProfile.title") }}</h4>
                </div>
              </section>

              <section class="employee-admin-form-section">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.privateProfile.contactEyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.privateProfile.contactTitle") }}</h4>
                </div>
                <div class="employee-admin-form-grid employee-admin-form-grid--editor">
                  <label class="field-stack field-stack--half">
                    <span>{{ t("employeeAdmin.fields.privateEmail") }}</span>
                    <input v-model="privateProfileDraft.private_email" :disabled="!actionState.canManagePrivateProfile" type="email" />
                  </label>
                  <label class="field-stack field-stack--half">
                    <span>{{ t("employeeAdmin.fields.privatePhone") }}</span>
                    <input v-model="privateProfileDraft.private_phone" :disabled="!actionState.canManagePrivateProfile" inputmode="tel" />
                  </label>
                </div>
              </section>

              <section class="employee-admin-form-section">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.privateProfile.identityEyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.privateProfile.identityTitle") }}</h4>
                </div>
                <div class="employee-admin-form-grid employee-admin-form-grid--editor">
                  <label class="field-stack field-stack--half">
                    <span>{{ t("employeeAdmin.fields.birthDate") }}</span>
                    <input v-model="privateProfileDraft.birth_date" :disabled="!actionState.canManagePrivateProfile" type="date" />
                  </label>
                  <label class="field-stack field-stack--half">
                    <span>{{ t("employeeAdmin.fields.placeOfBirth") }}</span>
                    <input v-model="privateProfileDraft.place_of_birth" :disabled="!actionState.canManagePrivateProfile" />
                  </label>
                  <label class="field-stack field-stack--half">
                    <span>{{ t("employeeAdmin.fields.nationalityCountryCode") }}</span>
                    <input
                      v-model="privateProfileDraft.nationality_country_code"
                      :disabled="!actionState.canManagePrivateProfile"
                      maxlength="2"
                      autocapitalize="characters"
                    />
                  </label>
                  <label class="field-stack field-stack--half">
                    <span>{{ t("employeeAdmin.fields.maritalStatus") }}</span>
                    <select
                      v-model="privateProfileDraft.marital_status_code"
                      :disabled="!actionState.canManagePrivateProfile || maritalStatusOptionsLoading"
                      data-testid="employee-private-profile-marital-status-select"
                    >
                      <option value="">{{ t("employeeAdmin.privateProfile.maritalStatusPlaceholder") }}</option>
                      <option
                        v-for="option in privateProfileMaritalStatusOptions"
                        :key="option.code"
                        :value="option.code"
                      >
                        {{ option.label }}
                      </option>
                    </select>
                    <p v-if="maritalStatusOptionsLoading" class="field-help">
                      {{ t("employeeAdmin.privateProfile.maritalStatusLoading") }}
                    </p>
                    <p v-else-if="maritalStatusLookupError" class="field-help">
                      {{ maritalStatusLookupError }}
                    </p>
                    <p v-else-if="privateProfileMaritalStatusIsLegacy" class="field-help">
                      {{ t("employeeAdmin.privateProfile.maritalStatusLegacyHint") }}
                    </p>
                  </label>
                </div>
              </section>

              <section class="employee-admin-form-section">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.privateProfile.payrollEyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.privateProfile.payrollTitle") }}</h4>
                </div>
                <div class="employee-admin-form-grid employee-admin-form-grid--editor">
                  <label class="field-stack field-stack--half">
                    <span>{{ t("employeeAdmin.fields.taxId") }}</span>
                    <input v-model="privateProfileDraft.tax_id" :disabled="!actionState.canManagePrivateProfile" />
                  </label>
                  <label class="field-stack field-stack--half">
                    <span>{{ t("employeeAdmin.fields.socialSecurityNo") }}</span>
                    <input v-model="privateProfileDraft.social_security_no" :disabled="!actionState.canManagePrivateProfile" />
                  </label>
                </div>
              </section>

              <section class="employee-admin-form-section">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.privateProfile.bankingEyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.privateProfile.bankingTitle") }}</h4>
                </div>
                <div class="employee-admin-form-grid employee-admin-form-grid--editor">
                  <label class="field-stack field-stack--wide">
                    <span>{{ t("employeeAdmin.fields.bankAccountHolder") }}</span>
                    <input v-model="privateProfileDraft.bank_account_holder" :disabled="!actionState.canManagePrivateProfile" />
                  </label>
                  <label class="field-stack field-stack--half">
                    <span>{{ t("employeeAdmin.fields.bankIban") }}</span>
                    <input
                      v-model="privateProfileDraft.bank_iban"
                      :disabled="!actionState.canManagePrivateProfile"
                      autocapitalize="characters"
                    />
                  </label>
                  <label class="field-stack field-stack--half">
                    <span>{{ t("employeeAdmin.fields.bankBic") }}</span>
                    <input
                      v-model="privateProfileDraft.bank_bic"
                      :disabled="!actionState.canManagePrivateProfile"
                      autocapitalize="characters"
                    />
                  </label>
                </div>
              </section>

              <section class="employee-admin-form-section">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.privateProfile.emergencyEyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.privateProfile.emergencyTitle") }}</h4>
                </div>
                <div class="employee-admin-form-grid employee-admin-form-grid--editor">
                  <label class="field-stack field-stack--half">
                    <span>{{ t("employeeAdmin.fields.emergencyContactName") }}</span>
                    <input v-model="privateProfileDraft.emergency_contact_name" :disabled="!actionState.canManagePrivateProfile" />
                  </label>
                  <label class="field-stack field-stack--half">
                    <span>{{ t("employeeAdmin.fields.emergencyContactPhone") }}</span>
                    <input
                      v-model="privateProfileDraft.emergency_contact_phone"
                      :disabled="!actionState.canManagePrivateProfile"
                      inputmode="tel"
                    />
                  </label>
                </div>
              </section>

              <section class="employee-admin-form-section">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.privateProfile.notesEyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.privateProfile.notesTitle") }}</h4>
                </div>
                <div class="employee-admin-form-grid employee-admin-form-grid--editor">
                  <label class="field-stack field-stack--wide">
                    <span>{{ t("employeeAdmin.fields.notes") }}</span>
                    <textarea v-model="privateProfileDraft.notes" :disabled="!actionState.canManagePrivateProfile" rows="4" />
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
            v-if="isEmployeeOverviewSectionVisible('addresses')"
            id="employee-overview-section-addresses"
            class="employee-admin-overview-section-card"
            data-testid="employee-overview-section-addresses"
          >
            <div class="employee-admin-form employee-admin-form--structured">
              <section class="employee-admin-overview-section-card__header employee-admin-overview-section-card__header--split">
                <div>
                  <p class="eyebrow">{{ t("employeeAdmin.addresses.eyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.addresses.title") }}</h4>
                </div>
                <div class="employee-admin-overview-section-card__header-actions">
                  <button
                    class="cta-button cta-secondary employee-admin-header-action"
                    type="button"
                    data-testid="employee-address-history-open"
                    @click="openAddressHistoryDialog"
                  >
                    {{ t("employeeAdmin.addresses.showHistory") }}
                  </button>
                </div>
              </section>

              <section class="employee-admin-form-section">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.addresses.currentEyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.addresses.currentTitle") }}</h4>
                </div>
                <div class="cta-row">
                  <button class="cta-button" type="button" :disabled="!actionState.canManageAddresses" @click="openNewAddressEditor">
                    {{ t("employeeAdmin.actions.addAddress") }}
                  </button>
                </div>
                <div v-if="currentEmployeeAddress" class="employee-admin-record employee-admin-record--static">
                  <div class="employee-admin-record__body">
                    <strong>{{ currentAddressSummary || currentEmployeeAddress.address_id }}</strong>
                    <span class="employee-admin-record__meta">
                      {{ currentEmployeeAddress.valid_from }} · {{ currentEmployeeAddress.valid_to || t("employeeAdmin.summary.none") }}
                    </span>
                  </div>
                  <div class="employee-admin-record__actions">
                    <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canManageAddresses" @click="editAddress(currentEmployeeAddress)">
                      {{ t("employeeAdmin.actions.editAddress") }}
                    </button>
                    <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canManageAddresses" @click="prepareAddressValidityClose(currentEmployeeAddress)">
                      {{ t("employeeAdmin.actions.closeAddressValidity") }}
                    </button>
                    <StatusBadge :status="currentEmployeeAddress.status" />
                  </div>
                </div>
                <p v-else class="employee-admin-list-empty">{{ t("employeeAdmin.addresses.currentEmpty") }}</p>
              </section>

            </div>
          </section>
          <section
            v-if="isEmployeeOverviewSectionVisible('absences')"
            id="employee-overview-section-absences"
            class="employee-admin-overview-section-card"
            data-testid="employee-overview-section-absences"
          >
            <div class="employee-admin-form employee-admin-form--structured">
              <section class="employee-admin-overview-section-card__header">
                <div>
                  <p class="eyebrow">{{ t("employeeAdmin.absences.eyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.absences.title") }}</h4>
                </div>
              </section>

              <section class="employee-admin-form-section">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.absences.registerEyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.absences.registerTitle") }}</h4>
                </div>
                <div class="cta-row">
                  <button class="cta-button" type="button" :disabled="!actionState.canManageAbsences" @click="openNewAbsenceEditor">
                    {{ t("employeeAdmin.actions.createAbsence") }}
                  </button>
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
            </div>
          </section>

          <section
            v-if="isEmployeeOverviewSectionVisible('notes')"
            id="employee-overview-section-notes"
            class="employee-admin-overview-section-card"
            data-testid="employee-overview-section-notes"
          >
            <div class="employee-admin-form employee-admin-form--structured">
              <section class="employee-admin-overview-section-card__header">
                <div>
                  <p class="eyebrow">{{ t("employeeAdmin.notes.eyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.notes.title") }}</h4>
                </div>
              </section>

              <section class="employee-admin-form-section">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.notes.registerEyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.notes.registerTitle") }}</h4>
                </div>
                <div class="cta-row">
                  <button class="cta-button" type="button" :disabled="!actionState.canManageNotes" @click="openNewNoteEditor">
                    {{ t("employeeAdmin.actions.createNote") }}
                  </button>
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
            </div>
          </section>

          <section
            v-if="isEmployeeOverviewSectionVisible('groups')"
            id="employee-overview-section-groups"
            class="employee-admin-overview-section-card"
            data-testid="employee-overview-section-groups"
          >
            <div class="employee-admin-form employee-admin-form--structured">
              <section class="employee-admin-overview-section-card__header">
                <div>
                  <p class="eyebrow">{{ t("employeeAdmin.groups.eyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.groups.title") }}</h4>
                </div>
              </section>

              <section class="employee-admin-form-section">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.groups.catalogEyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.groups.catalogTitle") }}</h4>
                </div>
                <div class="cta-row">
                  <button class="cta-button" type="button" :disabled="!actionState.canManageGroups" @click="openGroupCatalogEditor">
                    {{ t("employeeAdmin.groups.catalogTitle") }}
                  </button>
                </div>
              </section>

              <section class="employee-admin-form-section">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.groups.assignEyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.groups.assignTitle") }}</h4>
                </div>
                <div class="cta-row">
                  <button class="cta-button" type="button" :disabled="!actionState.canManageGroups" @click="openGroupAssignmentEditor">
                    {{ t("employeeAdmin.actions.assignGroup") }}
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
            v-if="isEmployeeOverviewSectionVisible('documents')"
            id="employee-overview-section-documents"
            class="employee-admin-overview-section-card"
            data-testid="employee-overview-section-documents"
          >
            <div class="employee-admin-form employee-admin-form--structured">
              <section class="employee-admin-overview-section-card__header">
                <div>
                  <p class="eyebrow">{{ t("employeeAdmin.documents.eyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.documents.title") }}</h4>
                </div>
              </section>

              <section class="employee-admin-form-section">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.documents.libraryEyebrow") }}</p>
                  <h4>{{ t("employeeAdmin.documents.libraryTitle") }}</h4>
                </div>
                <div class="cta-row">
                  <button class="cta-button" type="button" :disabled="!actionState.canEdit" @click="openEmployeeOverviewEditor('document_upload')">
                    {{ t("employeeAdmin.actions.uploadDocument") }}
                  </button>
                  <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canEdit" @click="openEmployeeOverviewEditor('document_link')">
                    {{ t("employeeAdmin.actions.linkDocument") }}
                  </button>
                  <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canEdit" @click="openEmployeeOverviewEditor('document_version')">
                    {{ t("employeeAdmin.actions.addDocumentVersion") }}
                  </button>
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
            </div>
          </section>
            </div>
            </section>
          </section>
          <div
            v-if="credentialLifecycleDialogOpen"
            class="employee-admin-modal-backdrop"
            data-testid="employee-credential-archive-dialog"
            @click.self="closeCredentialLifecycleDialog"
          >
            <section
              class="module-card employee-admin-modal"
              aria-labelledby="employee-credential-lifecycle-title"
              aria-modal="true"
              role="dialog"
            >
              <div class="employee-admin-form-section">
                <div class="employee-admin-form-section__header">
                  <div>
                    <p class="eyebrow">{{ t("employeeAdmin.credentials.lifecycleEyebrow") }}</p>
                    <h4 id="employee-credential-lifecycle-title">{{ credentialLifecycleDialogTitle }}</h4>
                  </div>
                </div>
                <p class="field-help">{{ credentialLifecycleDialogBody }}</p>
                <div class="employee-admin-modal-actions">
                  <button
                    class="cta-button cta-secondary"
                    type="button"
                    data-testid="employee-credential-archive-cancel"
                    @click="closeCredentialLifecycleDialog"
                  >
                    {{ t("employeeAdmin.actions.cancel") }}
                  </button>
                  <button
                    class="cta-button"
                    type="button"
                    data-testid="employee-credential-archive-confirm"
                    :disabled="!actionState.canManageCredentials"
                    @click="confirmCredentialLifecycle"
                  >
                    {{ credentialLifecycleDialogActionLabel }}
                  </button>
                </div>
              </div>
            </section>
          </div>
          <div
            v-if="addressHistoryDialogOpen"
            class="employee-admin-modal-backdrop"
            data-testid="employee-address-history-dialog"
            @click.self="closeAddressHistoryDialog"
          >
            <section
              class="module-card employee-admin-modal"
              aria-labelledby="employee-address-history-title"
              aria-modal="true"
              role="dialog"
            >
              <div class="employee-admin-form-section">
                <div class="employee-admin-form-section__header">
                  <div>
                    <p class="eyebrow">{{ t("employeeAdmin.addresses.historyEyebrow") }}</p>
                    <h4 id="employee-address-history-title">{{ t("employeeAdmin.addresses.historyDialogTitle") }}</h4>
                  </div>
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
                      <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canManageAddresses" @click="editAddressFromHistoryDialog(addressRow)">
                        {{ t("employeeAdmin.actions.editAddress") }}
                      </button>
                      <button
                        v-if="!isEmployeeAddressCurrent(addressRow)"
                        class="cta-button cta-secondary"
                        type="button"
                        :disabled="!actionState.canManageAddresses"
                        @click="prepareAddressAsCurrentFromHistoryDialog(addressRow)"
                      >
                        {{ t("employeeAdmin.actions.markCurrentAddress") }}
                      </button>
                      <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canManageAddresses" @click="prepareAddressValidityCloseFromHistoryDialog(addressRow)">
                        {{ t("employeeAdmin.actions.closeAddressValidity") }}
                      </button>
                      <StatusBadge :status="addressRow.status" />
                    </div>
                  </article>
                </div>
                <p v-else class="employee-admin-list-empty">{{ t("employeeAdmin.addresses.historyEmpty") }}</p>
                <div class="employee-admin-modal-actions">
                  <button
                    class="cta-button cta-secondary"
                    type="button"
                    data-testid="employee-address-history-close"
                    @click="closeAddressHistoryDialog"
                  >
                    {{ t("employeeAdmin.actions.cancel") }}
                  </button>
                </div>
              </div>
            </section>
          </div>
          <div
            v-if="resetPasswordDialogOpen"
            class="employee-admin-modal-backdrop"
            data-testid="employee-access-reset-password-dialog"
            @click.self="closeResetPasswordDialog"
          >
            <section
              class="module-card employee-admin-modal"
              aria-labelledby="employee-access-reset-password-title"
              aria-modal="true"
              role="dialog"
            >
              <div class="employee-admin-form-section">
                <div class="employee-admin-form-section__header">
                  <div>
                    <p class="eyebrow">{{ t("employeeAdmin.access.resetEyebrow") }}</p>
                    <h4 id="employee-access-reset-password-title">{{ t("employeeAdmin.access.resetPasswordDialogTitle") }}</h4>
                  </div>
                </div>
                <div class="employee-admin-form-grid employee-admin-form-grid--editor">
                  <label class="field-stack">
                    <span>{{ t("employeeAdmin.access.resetPassword") }}</span>
                    <input v-model="accessResetDraft.password" :disabled="!actionState.canManageAccess" type="password" />
                  </label>
                </div>
                <div class="employee-admin-modal-actions">
                  <button class="cta-button cta-secondary" type="button" @click="closeResetPasswordDialog">
                    {{ t("employeeAdmin.actions.cancel") }}
                  </button>
                  <button
                    class="cta-button"
                    type="button"
                    data-testid="employee-access-reset-password-submit"
                    :disabled="!actionState.canManageAccess"
                    @click="resetAccessPassword"
                  >
                    {{ t("employeeAdmin.actions.resetAccessPassword") }}
                  </button>
                </div>
              </div>
            </section>
          </div>
          <div
            v-if="accessDiagnosticsDialogOpen"
            class="employee-admin-modal-backdrop"
            data-testid="employee-access-diagnostics-dialog"
            @click.self="closeAccessDiagnosticsDialog"
          >
            <section
              class="module-card employee-admin-modal"
              aria-labelledby="employee-access-diagnostics-title"
              aria-modal="true"
              role="dialog"
            >
              <div class="employee-admin-form-section">
                <div class="employee-admin-form-section__header">
                  <div>
                    <p class="eyebrow">{{ t("employeeAdmin.access.diagnosticsEyebrow") }}</p>
                    <h4 id="employee-access-diagnostics-title">{{ t("employeeAdmin.access.diagnosticsDialogTitle") }}</h4>
                  </div>
                </div>
                <div class="employee-admin-record-list employee-admin-access-diagnostics-list">
                  <article
                    v-for="check in employeeAccessDiagnosticChecks"
                    :key="check.label"
                    class="employee-admin-record employee-admin-access-diagnostic"
                    data-testid="employee-access-diagnostics-row"
                  >
                    <div class="employee-admin-record__body">
                      <strong>{{ check.label }}</strong>
                      <span class="employee-admin-record__meta">{{ check.value ? t("employeeAdmin.access.enabledYes") : t("employeeAdmin.access.enabledNo") }}</span>
                    </div>
                    <StatusBadge :status="check.value ? 'active' : 'inactive'" />
                  </article>
                </div>
                <div class="employee-admin-modal-actions">
                  <button
                    class="cta-button cta-secondary"
                    type="button"
                    data-testid="employee-access-diagnostics-close"
                    @click="closeAccessDiagnosticsDialog"
                  >
                    {{ t("employeeAdmin.actions.cancel") }}
                  </button>
                </div>
              </div>
            </section>
          </div>
          <div
            v-if="activeEmployeeOverviewEditor"
            class="employee-admin-modal-backdrop"
            @click.self="closeEmployeeOverviewEditor"
          >
            <section
              v-if="activeEmployeeOverviewEditor === 'qualification'"
              aria-labelledby="employee-overview-editor-qualification-title"
              aria-modal="true"
              class="module-card employee-admin-modal"
              data-testid="employee-overview-editor-qualification-modal"
              role="dialog"
            >
              <form class="employee-admin-form" @submit.prevent="submitQualification">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.qualifications.editorEyebrow") }}</p>
                  <h4 id="employee-overview-editor-qualification-title">{{ t("employeeAdmin.qualifications.editorTitle") }}</h4>
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
                    <select v-model="qualificationDraft.function_type_id" :disabled="!actionState.canManageQualifications || employeeFunctionTypeOptions.length === 0">
                      <option value="">{{ t("employeeAdmin.qualifications.functionTypePlaceholder") }}</option>
                      <option v-for="option in employeeFunctionTypeOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
                    </select>
                    <span v-if="employeeFunctionTypeOptions.length === 0" class="field-help">{{ t("employeeAdmin.qualifications.functionTypeEmptyHint") }}</span>
                  </label>
                  <label v-else class="field-stack">
                    <span>{{ t("employeeAdmin.fields.qualificationType") }}</span>
                    <select v-model="qualificationDraft.qualification_type_id" :disabled="!actionState.canManageQualifications || employeeQualificationTypeOptions.length === 0">
                      <option value="">{{ t("employeeAdmin.qualifications.qualificationTypePlaceholder") }}</option>
                      <option v-for="option in employeeQualificationTypeOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
                    </select>
                    <span v-if="employeeQualificationTypeOptions.length === 0" class="field-help">{{ t("employeeAdmin.qualifications.qualificationTypeEmptyHint") }}</span>
                    <span v-else-if="selectedQualificationType?.expiry_required && selectedQualificationType?.default_validity_days" class="field-help">
                      {{ t("employeeAdmin.qualifications.expiryAutofillHint", { days: selectedQualificationType.default_validity_days }) }}
                    </span>
                    <span v-else-if="selectedQualificationType?.expiry_required" class="field-help">{{ t("employeeAdmin.qualifications.expiryRequiredHint") }}</span>
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
                  <button class="cta-button cta-secondary" type="button" @click="resetQualificationDraft">{{ t("employeeAdmin.actions.resetQualification") }}</button>
                  <button class="cta-button cta-secondary" type="button" @click="closeEmployeeOverviewEditor">{{ t("employeeAdmin.actions.cancel") }}</button>
                </div>
              </form>
            </section>

            <section
              v-else-if="activeEmployeeOverviewEditor === 'qualification_proof'"
              aria-labelledby="employee-overview-editor-qualification-proof-title"
              aria-modal="true"
              class="module-card employee-admin-modal"
              data-testid="employee-overview-editor-qualification-proof-modal"
              role="dialog"
            >
              <form class="employee-admin-form" @submit.prevent="submitQualificationProof">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.qualifications.proofEyebrow") }}</p>
                  <h4 id="employee-overview-editor-qualification-proof-title">{{ t("employeeAdmin.qualifications.proofTitle") }}</h4>
                </div>
                <p v-if="selectedQualification" class="field-help">
                  {{ t("employeeAdmin.qualifications.proofLead") }}: {{ selectedQualification.qualification_type?.label || selectedQualification.function_type?.label || selectedQualification.id }}
                </p>
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
                  <button class="cta-button" type="submit" :disabled="!actionState.canManageQualifications || !pendingQualificationProofFile">
                    {{ t("employeeAdmin.actions.uploadQualificationProof") }}
                  </button>
                  <button class="cta-button cta-secondary" type="button" @click="closeEmployeeOverviewEditor">{{ t("employeeAdmin.actions.cancel") }}</button>
                </div>
              </form>
            </section>

            <section
              v-else-if="activeEmployeeOverviewEditor === 'credential'"
              aria-labelledby="employee-overview-editor-credential-title"
              aria-modal="true"
              class="module-card employee-admin-modal"
              data-testid="employee-overview-editor-credential-modal"
              role="dialog"
            >
              <form class="employee-admin-form" data-testid="employee-credential-edit-dialog" @submit.prevent="submitCredential">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.credentials.editorEyebrow") }}</p>
                  <h4 id="employee-overview-editor-credential-title">{{ t("employeeAdmin.credentials.editorTitle") }}</h4>
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
                      <option v-for="option in employeeCredentialTypeOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
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
                  <button class="cta-button" type="submit" data-testid="employee-credential-edit-save" :disabled="!actionState.canManageCredentials">
                    {{ editingCredentialId ? t("employeeAdmin.actions.saveCredential") : t("employeeAdmin.actions.createCredential") }}
                  </button>
                  <button class="cta-button cta-secondary" type="button" @click="resetCredentialDraft">{{ t("employeeAdmin.actions.resetCredential") }}</button>
                  <button
                    class="cta-button cta-secondary"
                    type="button"
                    data-testid="employee-credential-edit-cancel"
                    @click="closeEmployeeOverviewEditor"
                  >
                    {{ t("employeeAdmin.actions.cancel") }}
                  </button>
                </div>
              </form>
            </section>

            <section
              v-else-if="activeEmployeeOverviewEditor === 'availability'"
              aria-labelledby="employee-overview-editor-availability-title"
              aria-modal="true"
              class="module-card employee-admin-modal"
              data-testid="employee-overview-editor-availability-modal"
              role="dialog"
            >
              <form class="employee-admin-form" @submit.prevent="submitAvailabilityRule">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.availability.editorEyebrow") }}</p>
                  <h4 id="employee-overview-editor-availability-title">{{ t("employeeAdmin.availability.editorTitle") }}</h4>
                </div>
                <div class="employee-admin-form-grid employee-admin-form-grid--editor">
                  <label class="field-stack">
                    <span>{{ t("employeeAdmin.fields.ruleKind") }}</span>
                    <select v-model="availabilityDraft.rule_kind" :disabled="!actionState.canManageAvailability">
                      <option value="">{{ t("employeeAdmin.availability.ruleKindPlaceholder") }}</option>
                      <option v-for="option in employeeAvailabilityRuleKindOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
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
                        <input :checked="availabilityDraft.weekday_indexes.includes(option.value)" :disabled="!actionState.canManageAvailability" type="checkbox" @change="toggleAvailabilityWeekday(option.value, ($event.target as HTMLInputElement).checked)" />
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
                  <button class="cta-button cta-secondary" type="button" @click="resetAvailabilityDraft">{{ t("employeeAdmin.actions.resetAvailability") }}</button>
                  <button class="cta-button cta-secondary" type="button" @click="closeEmployeeOverviewEditor">{{ t("employeeAdmin.actions.cancel") }}</button>
                </div>
              </form>
            </section>

            <section
              v-else-if="activeEmployeeOverviewEditor === 'absence'"
              aria-labelledby="employee-overview-editor-absence-title"
              aria-modal="true"
              class="module-card employee-admin-modal"
              data-testid="employee-overview-editor-absence-modal"
              role="dialog"
            >
              <form class="employee-admin-form" @submit.prevent="submitAbsence">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.absences.editorEyebrow") }}</p>
                  <h4 id="employee-overview-editor-absence-title">{{ t("employeeAdmin.absences.editorTitle") }}</h4>
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
                  <button class="cta-button cta-secondary" type="button" @click="resetAbsenceDraft">{{ t("employeeAdmin.actions.resetAbsence") }}</button>
                  <button class="cta-button cta-secondary" type="button" @click="closeEmployeeOverviewEditor">{{ t("employeeAdmin.actions.cancel") }}</button>
                </div>
              </form>
            </section>

            <section
              v-else-if="activeEmployeeOverviewEditor === 'note'"
              aria-labelledby="employee-overview-editor-note-title"
              aria-modal="true"
              class="module-card employee-admin-modal"
              data-testid="employee-overview-editor-note-modal"
              role="dialog"
            >
              <form class="employee-admin-form" @submit.prevent="submitNote">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.notes.editorEyebrow") }}</p>
                  <h4 id="employee-overview-editor-note-title">{{ t("employeeAdmin.notes.editorTitle") }}</h4>
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
                  <button class="cta-button cta-secondary" type="button" @click="resetNoteDraft">{{ t("employeeAdmin.actions.resetNote") }}</button>
                  <button class="cta-button cta-secondary" type="button" @click="closeEmployeeOverviewEditor">{{ t("employeeAdmin.actions.cancel") }}</button>
                </div>
              </form>
            </section>

            <section
              v-else-if="activeEmployeeOverviewEditor === 'group_catalog'"
              aria-labelledby="employee-overview-editor-group-catalog-title"
              aria-modal="true"
              class="module-card employee-admin-modal"
              data-testid="employee-overview-editor-group-catalog-modal"
              role="dialog"
            >
              <form class="employee-admin-form" @submit.prevent="submitGroup">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.groups.catalogEyebrow") }}</p>
                  <h4 id="employee-overview-editor-group-catalog-title">{{ t("employeeAdmin.groups.catalogTitle") }}</h4>
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
                  <button class="cta-button" type="submit" :disabled="!actionState.canManageGroups">
                    {{ editingGroupId ? t("employeeAdmin.actions.saveGroup") : t("employeeAdmin.actions.createGroup") }}
                  </button>
                  <button class="cta-button cta-secondary" type="button" @click="resetGroupDraft">{{ t("employeeAdmin.actions.resetGroup") }}</button>
                  <button class="cta-button cta-secondary" type="button" @click="closeEmployeeOverviewEditor">{{ t("employeeAdmin.actions.cancel") }}</button>
                </div>
              </form>
            </section>

            <section
              v-else-if="activeEmployeeOverviewEditor === 'group_assignment'"
              aria-labelledby="employee-overview-editor-group-assignment-title"
              aria-modal="true"
              class="module-card employee-admin-modal"
              data-testid="employee-overview-editor-group-assignment-modal"
              role="dialog"
            >
              <form class="employee-admin-form" @submit.prevent="submitMembership">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.groups.assignEyebrow") }}</p>
                  <h4 id="employee-overview-editor-group-assignment-title">{{ t("employeeAdmin.groups.assignTitle") }}</h4>
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
                  <button class="cta-button" type="submit" :disabled="!actionState.canManageGroups || !membershipDraft.group_id">
                    {{ editingMembershipId ? t("employeeAdmin.actions.saveMembership") : t("employeeAdmin.actions.assignGroup") }}
                  </button>
                  <button class="cta-button cta-secondary" type="button" @click="resetMembershipDraft">{{ t("employeeAdmin.actions.resetMembership") }}</button>
                  <button class="cta-button cta-secondary" type="button" @click="closeEmployeeOverviewEditor">{{ t("employeeAdmin.actions.cancel") }}</button>
                </div>
              </form>
            </section>

            <section
              v-else-if="activeEmployeeOverviewEditor === 'address'"
              aria-labelledby="employee-overview-editor-address-title"
              aria-modal="true"
              class="module-card employee-admin-modal"
              data-testid="employee-overview-editor-address-modal"
              role="dialog"
            >
              <form class="employee-admin-form" @submit.prevent="submitAddress">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t(addressEditorEyebrowKey as never) }}</p>
                  <h4 id="employee-overview-editor-address-title">{{ t(addressEditorTitleKey as never) }}</h4>
                </div>
                <p class="field-help">{{ t(addressEditorLeadKey as never) }}</p>
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
                    <input v-model="addressDraft.valid_to" :disabled="!actionState.canManageAddresses" type="date" />
                  </label>
                  <label class="field-stack field-stack--wide">
                    <span>{{ t("employeeAdmin.fields.notes") }}</span>
                    <textarea v-model="addressDraft.notes" :disabled="!actionState.canManageAddresses" rows="3" />
                  </label>
                </div>
                <div class="employee-admin-checkbox">
                  <input v-model="addressDraft.is_primary" :disabled="!actionState.canManageAddresses" type="checkbox" />
                  <span>{{ t("employeeAdmin.addresses.primaryLabel") }}</span>
                </div>
                <div class="cta-row">
                  <button v-if="editingAddressId" class="cta-button cta-secondary" type="button" :disabled="!actionState.canManageAddresses" @click="resetAddressDraft">
                    {{ t("employeeAdmin.actions.addAddress") }}
                  </button>
                  <button class="cta-button" type="submit" :disabled="!actionState.canManageAddresses">
                    {{ editingAddressId ? t("employeeAdmin.actions.saveAddress") : t("employeeAdmin.actions.addAddress") }}
                  </button>
                  <button class="cta-button cta-secondary" type="button" @click="resetAddressDraft">{{ t("employeeAdmin.actions.resetAddress") }}</button>
                  <button class="cta-button cta-secondary" type="button" @click="closeEmployeeOverviewEditor">{{ t("employeeAdmin.actions.cancel") }}</button>
                </div>
              </form>
            </section>

            <section
              v-else-if="activeEmployeeOverviewEditor === 'document_upload'"
              aria-labelledby="employee-overview-editor-document-upload-title"
              aria-modal="true"
              class="module-card employee-admin-modal"
              data-testid="employee-overview-editor-document-upload-modal"
              role="dialog"
            >
              <form class="employee-admin-form" @submit.prevent="submitEmployeeDocumentUpload">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.documents.uploadEyebrow") }}</p>
                  <h4 id="employee-overview-editor-document-upload-title">{{ t("employeeAdmin.documents.uploadTitle") }}</h4>
                </div>
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
                      <option v-for="option in employeeDocumentTypeOptions" :key="option.value || 'none'" :value="option.value">{{ option.label }}</option>
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
                  <button class="cta-button cta-secondary" type="button" @click="closeEmployeeOverviewEditor">{{ t("employeeAdmin.actions.cancel") }}</button>
                </div>
              </form>
            </section>

            <section
              v-else-if="activeEmployeeOverviewEditor === 'document_link'"
              aria-labelledby="employee-overview-editor-document-link-title"
              aria-modal="true"
              class="module-card employee-admin-modal"
              data-testid="employee-overview-editor-document-link-modal"
              role="dialog"
            >
              <form class="employee-admin-form" @submit.prevent="submitEmployeeDocumentLink">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.documents.linkEyebrow") }}</p>
                  <h4 id="employee-overview-editor-document-link-title">{{ t("employeeAdmin.documents.linkTitle") }}</h4>
                </div>
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
                  <button class="cta-button" type="submit" :disabled="!actionState.canEdit">{{ t("employeeAdmin.actions.linkDocument") }}</button>
                  <button class="cta-button cta-secondary" type="button" @click="closeEmployeeOverviewEditor">{{ t("employeeAdmin.actions.cancel") }}</button>
                </div>
              </form>
            </section>

            <section
              v-else-if="activeEmployeeOverviewEditor === 'document_version'"
              aria-labelledby="employee-overview-editor-document-version-title"
              aria-modal="true"
              class="module-card employee-admin-modal"
              data-testid="employee-overview-editor-document-version-modal"
              role="dialog"
            >
              <form class="employee-admin-form" @submit.prevent="submitEmployeeDocumentVersion">
                <div class="employee-admin-form-section__header">
                  <p class="eyebrow">{{ t("employeeAdmin.documents.versionEyebrow") }}</p>
                  <h4 id="employee-overview-editor-document-version-title">{{ t("employeeAdmin.documents.versionTitle") }}</h4>
                </div>
                <p v-if="selectedEmployeeDocument" class="field-help">
                  {{ t("employeeAdmin.documents.selectedVersionTarget") }}: {{ selectedEmployeeDocument.title }}
                </p>
                <p v-else class="employee-admin-list-empty">{{ t("employeeAdmin.documents.versionEmpty") }}</p>
                <div class="employee-admin-form-grid">
                  <label class="field-stack">
                    <span>{{ t("employeeAdmin.fields.documentVersionTarget") }}</span>
                    <select v-model="selectedEmployeeDocumentId">
                      <option value="">{{ t("employeeAdmin.summary.none") }}</option>
                      <option v-for="document in employeeDocuments" :key="document.document_id" :value="document.document_id">{{ document.title }}</option>
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
                  <button class="cta-button cta-secondary" type="button" @click="closeEmployeeOverviewEditor">{{ t("employeeAdmin.actions.cancel") }}</button>
                </div>
              </form>
            </section>
          </div>
        </template>

        <section v-else class="employee-admin-empty">
          <p class="eyebrow">{{ t("employeeAdmin.detail.emptyEyebrow") }}</p>
          <h3>{{ t("employeeAdmin.detail.emptyTitle") }}</h3>
          <p>{{ t("employeeAdmin.detail.emptyBody") }}</p>
          <div class="cta-row">
            <button class="cta-button cta-secondary" type="button" data-testid="employee-open-catalogs" @click="openWorkforceCatalogs">
              {{ t("employeeAdmin.actions.manageCatalogs") }}
            </button>
          </div>
        </section>
      </section>
      </div>
      </div>
    </SicherPlanLoadingOverlay>
  </section>
</template>

<script setup lang="ts">
import { IconifyIcon } from "@vben/icons";
import type { CSSProperties } from "vue";
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";

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
  listEmployeePrivateProfileMaritalStatusOptions,
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
  type EmployeeListFilters,
  type EmployeeListItem,
  type EmployeeNoteRead,
  type EmployeeOperationalRead,
  type EmployeePrivateProfileRead,
  type EmployeePrivateProfileMaritalStatusOptionRead,
  type EmployeePrivateProfileUpdatePayload,
  type EmployeePrivateProfileWritePayload,
  type EmployeePhotoRead,
  updateEmployeePrivateProfile,
  uploadEmployeeDocument,
  upsertEmployeePrivateProfile,
} from "@/api/employeeAdmin";
import SicherPlanLoadingOverlay from "@/components/SicherPlanLoadingOverlay.vue";
import StatusBadge from "@/components/StatusBadge.vue";
import EmployeeDashboardTab from "@/components/employees/EmployeeDashboardTab.vue";
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
  isEmployeeAddressCurrent,
  summarizeCurrentAddress,
  toLocalDateTimeInput,
  validateEmployeeAbsenceDraft,
  validateEmployeeAddressDraft,
  validateEmployeeAvailabilityDraft,
  validateEmployeeCredentialDraft,
  validateEmployeePrivateProfileDraft,
  validateEmployeeQualificationDraft,
} from "@/features/employees/employeeAdmin.helpers.js";
import { ADMIN_MENU_RESELECT_EVENT, type AdminMenuReselectDetail } from "../layouts/navigationEvents";
import { hasPlanningStaffingPermission } from "@/features/planning/planningStaffing.helpers.js";
import type { MessageKey } from "@/i18n/messages";
import { useAuthStore } from "@/stores/auth";

withDefaults(defineProps<{ embedded?: boolean }>(), {
  embedded: false,
});

const { t } = useI18n();
const authStore = useAuthStore();
const router = useRouter();
const { showFeedbackToast } = useSicherPlanFeedback();

const loading = reactive({
  list: false,
  detail: false,
  action: false,
  photo: false,
  employeeSearch: false,
});

const filters = reactive({
  search: "",
  status: "",
  default_branch_id: "",
  default_mandate_id: "",
  include_archived: false,
});
const advancedFilterDraft = reactive({
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
  private_email: "",
  private_phone: "",
  birth_date: "",
  place_of_birth: "",
  nationality_country_code: "",
  marital_status_code: "",
  tax_id: "",
  social_security_no: "",
  bank_account_holder: "",
  bank_iban: "",
  bank_bic: "",
  emergency_contact_name: "",
  emergency_contact_phone: "",
  notes: "",
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

type AddressEditorMode = "close" | "create" | "edit" | "transition";
type EmployeeOverviewEditorDialog =
  | "qualification"
  | "qualification_proof"
  | "credential"
  | "availability"
  | "absence"
  | "note"
  | "group_catalog"
  | "group_assignment"
  | "address"
  | "document_upload"
  | "document_link"
  | "document_version"
  | null;

const tenantScopeInput = ref(authStore.effectiveTenantScopeId || authStore.tenantScopeId || "");
const branches = ref<BranchRead[]>([]);
const mandates = ref<MandateRead[]>([]);
const employees = ref<EmployeeListItem[]>([]);
const employeeSearchModalOpen = ref(false);
const employeeSearchResults = ref<EmployeeListItem[]>([]);
const employeeSearchSuggestions = ref<EmployeeListItem[]>([]);
const employeeSearchSuggestionsSuppressed = ref(false);
const employeeSearchError = ref("");
const advancedFiltersModalOpen = ref(false);
const importExportModalOpen = ref(false);
const credentialLifecycleDialogOpen = ref(false);
const addressHistoryDialogOpen = ref(false);
const resetPasswordDialogOpen = ref(false);
const accessDiagnosticsDialogOpen = ref(false);
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
const maritalStatusOptions = ref<EmployeePrivateProfileMaritalStatusOptionRead[]>([]);
const maritalStatusOptionsLoading = ref(false);
const maritalStatusLookupError = ref("");
const qualificationProofsById = reactive<Record<string, EmployeeQualificationProofRead[]>>({});
const currentPhoto = ref<EmployeePhotoRead | null>(null);
const accessLink = ref<EmployeeAccessLinkRead | null>(null);
const importDryRunResult = ref<EmployeeImportDryRunResult | null>(null);
const lastImportResult = ref<EmployeeImportExecuteResult | null>(null);
const lastExportResult = ref<EmployeeExportResult | null>(null);
const photoPreviewUrl = ref("");
const employeeListPhotoPreviewUrls = reactive<Record<string, string>>({});
const employeeListPhotoFailedIds = reactive<Record<string, boolean>>({});
const employeeListPhotoPendingIds = reactive<Record<string, boolean>>({});
const pendingEmployeeDocumentFile = ref<File | null>(null);
const pendingEmployeeDocumentVersionFile = ref<File | null>(null);
const pendingImportFile = ref<File | null>(null);
const isCreatingEmployee = ref(false);
const activeDetailTab = ref("overview");
const activeOverviewSection = ref<EmployeeOverviewSectionId>("employee_file");
const activeEmployeeOverviewEditor = ref<EmployeeOverviewEditorDialog>(null);
const overviewOnePageRef = ref<HTMLElement | null>(null);
const overviewNavShellRef = ref<HTMLElement | null>(null);
const overviewNavFloatingMode = ref<"fixed" | "pinned" | "static">("static");
const overviewNavFloatingStyle = ref<CSSProperties>({});
const editingNoteId = ref("");
const editingGroupId = ref("");
const editingMembershipId = ref("");
const editingAddressId = ref("");
const addressTransitionSourceId = ref("");
const addressEditorMode = ref<AddressEditorMode>("create");
const editingQualificationId = ref("");
const editingCredentialId = ref("");
const selectedCredentialLifecycleId = ref("");
const credentialLifecycleMode = ref<"archive" | "revoke" | null>(null);
const editingAvailabilityRuleId = ref("");
const editingAbsenceId = ref("");
const selectedEmployeeDocumentId = ref("");
const pendingQualificationProofFile = ref<File | null>(null);
let employeeSearchDebounceHandle: ReturnType<typeof setTimeout> | null = null;
let employeeSearchRequestSeq = 0;
let suppressNextEmployeeSearchWatch = false;
let employeeOverviewSectionObserver: IntersectionObserver | null = null;
let suppressOverviewScrollSpyUntil = 0;
let overviewNavScrollTargets: Array<HTMLElement | Window> = [];
let overviewNavFloatingRaf: number | null = null;
const employeeOverviewVisibleEntries = new Map<EmployeeOverviewSectionId, IntersectionObserverEntry>();
const EXTRA_SECTION_NAV_TOP_OFFSET = 25;
const OVERVIEW_NAV_FLOATING_MIN_WIDTH = 1081;
const EMPLOYEE_LIST_PHOTO_PRELOAD_CONCURRENCY = 4;

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
const canReadStaffing = computed(() => hasPlanningStaffingPermission(effectiveRole.value, "planning.staffing.read"));
const isEmployeeSessionResolving = computed(() => authStore.isSessionResolving);
const employeeWorkspaceBusy = computed(() => isEmployeeSessionResolving.value || loading.action);
const employeeWorkspaceLoadingText = computed(() =>
  employeeWorkspaceBusy.value
    ? t(isEmployeeSessionResolving.value ? "workspace.loading.reconcilingSession" : "workspace.loading.processing")
    : "",
);
const resolvedTenantScopeId = computed(() => authStore.effectiveTenantScopeId);
const hasLinkedAccess = computed(() => !!accessLink.value?.user_id);
const employeeAccessDiagnosticChecks = computed(() => {
  const diagnostics = accessLink.value?.diagnostics;
  if (!diagnostics) {
    return [];
  }
  return [
    { label: t("employeeAdmin.access.diagnosticUserExists"), value: diagnostics.user_exists },
    { label: t("employeeAdmin.access.diagnosticUserStatus"), value: diagnostics.user_status_active },
    { label: t("employeeAdmin.access.diagnosticUserArchived"), value: diagnostics.user_not_archived },
    { label: t("employeeAdmin.access.diagnosticPasswordLogin"), value: diagnostics.is_password_login_enabled },
    { label: t("employeeAdmin.access.diagnosticPasswordHash"), value: diagnostics.has_password_hash },
    { label: t("employeeAdmin.access.diagnosticEmployeeLinked"), value: diagnostics.employee_linked },
    { label: t("employeeAdmin.access.diagnosticEmployeeStatus"), value: diagnostics.employee_status_active },
    { label: t("employeeAdmin.access.diagnosticEmployeeArchived"), value: diagnostics.employee_not_archived },
    { label: t("employeeAdmin.access.diagnosticRoleAssignment"), value: diagnostics.employee_user_role_assignment_active },
    { label: t("employeeAdmin.access.diagnosticPermission"), value: diagnostics.portal_employee_access_granted },
  ];
});
const employeeAccessDiagnosticsPassedCount = computed(() => employeeAccessDiagnosticChecks.value.filter((check) => check.value).length);
const selectedEmployeeLabel = computed(() =>
  selectedEmployee.value
    ? `${selectedEmployee.value.personnel_no} · ${selectedEmployee.value.first_name} ${selectedEmployee.value.last_name}`
    : t("employeeAdmin.detail.emptyTitle"),
);
const detailWorkspaceTitle = computed(() => {
  if (isCreatingEmployee.value) {
    return t("employeeAdmin.detail.newTitle");
  }
  return selectedEmployeeLabel.value;
});
const hasEmployeeDetailWorkspace = computed(() => isCreatingEmployee.value || !!selectedEmployee.value);
const employeeAdminDetailMode = computed(() => hasEmployeeDetailWorkspace.value);
const employeeAdminListMode = computed(() => !employeeAdminDetailMode.value);
const currentAddressSummary = computed(() => summarizeCurrentAddress(employeeAddresses.value));
const employeeAddressTimeline = computed(() =>
  [...employeeAddresses.value].sort((left, right) => {
    const leftCurrent = isEmployeeAddressCurrent(left);
    const rightCurrent = isEmployeeAddressCurrent(right);
    if (leftCurrent !== rightCurrent) {
      return leftCurrent ? -1 : 1;
    }
    const startCompare = right.valid_from.localeCompare(left.valid_from);
    if (startCompare !== 0) {
      return startCompare;
    }
    return (right.valid_to || "9999-12-31").localeCompare(left.valid_to || "9999-12-31");
  }),
);
const currentEmployeeAddress = computed(
  () => [...employeeAddresses.value].filter((row) => isEmployeeAddressCurrent(row)).sort((a, b) => a.valid_from.localeCompare(b.valid_from)).at(-1) ?? null,
);
const selectedEmployeeDocument = computed(
  () => employeeDocuments.value.find((document) => document.document_id === selectedEmployeeDocumentId.value) ?? null,
);
const selectedQualification = computed(
  () => employeeQualifications.value.find((qualification) => qualification.id === editingQualificationId.value) ?? null,
);
const selectedCredentialLifecycle = computed(
  () => employeeCredentials.value.find((credential) => credential.id === selectedCredentialLifecycleId.value) ?? null,
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
const selectedQualificationType = computed(
  () => qualificationTypes.value.find((row) => row.id === qualificationDraft.qualification_type_id) ?? null,
);
const credentialLifecycleDialogTitle = computed(() =>
  credentialLifecycleMode.value === "revoke"
    ? t("employeeAdmin.credentials.revokeDialogTitle" as never)
    : t("employeeAdmin.credentials.archiveDialogTitle" as never),
);
const credentialLifecycleDialogBody = computed(() => {
  const credential = selectedCredentialLifecycle.value;
  if (!credential) {
    return "";
  }
  const key =
    credentialLifecycleMode.value === "revoke"
      ? "employeeAdmin.credentials.revokeConfirm"
      : "employeeAdmin.credentials.archiveConfirm";
  return t(key as never, { credentialNo: credential.credential_no });
});
const credentialLifecycleDialogActionLabel = computed(() =>
  credentialLifecycleMode.value === "revoke"
    ? t("employeeAdmin.actions.revokeCredential" as never)
    : t("employeeAdmin.actions.archiveCredential" as never),
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
const privateProfileMaritalStatusOptions = computed(() => {
  const options = maritalStatusOptions.value
    .filter((option) => option.archived_at == null && option.status === "active")
    .map((option) => ({
      code: option.code,
      label: option.label,
    }));
  const currentCode = typeof privateProfileDraft.marital_status_code === "string"
    ? privateProfileDraft.marital_status_code.trim()
    : "";
  if (currentCode && !options.some((option) => option.code === currentCode)) {
    options.push({
      code: currentCode,
      label: `${currentCode} (${t("employeeAdmin.privateProfile.maritalStatusLegacyValue")})`,
    });
  }
  return options;
});
const privateProfileMaritalStatusIsLegacy = computed(() => {
  const currentCode = typeof privateProfileDraft.marital_status_code === "string"
    ? privateProfileDraft.marital_status_code.trim()
    : "";
  if (!currentCode) {
    return false;
  }
  return !maritalStatusOptions.value.some((option) => option.code === currentCode && option.archived_at == null && option.status === "active");
});
const filteredEmployeeMandates = computed(() => filterMandateOptions(employeeDraft.default_branch_id));
const employeeSearchQuery = computed(() => `${filters.search ?? ""}`.trim());
const normalizedEmployeeListSearch = computed(() => normalizeEmployeeListSearchValue(filters.search));
const filteredEmployees = computed(() => {
  const search = normalizedEmployeeListSearch.value;
  if (!search) {
    return employees.value;
  }
  return employees.value.filter((employee) => employeeListSearchHaystack(employee).includes(search));
});
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

function formatEmployeeListContext(employee: EmployeeListItem) {
  const parts = [
    employee.default_branch_id ? branchLabelMap.value.get(employee.default_branch_id) ?? employee.default_branch_id : "",
    employee.default_mandate_id ? mandateLabelMap.value.get(employee.default_mandate_id) ?? employee.default_mandate_id : "",
  ].filter(Boolean);
  return parts.join(" · ") || t("employeeAdmin.summary.none");
}

function getEmployeeInitials(employee: EmployeeListItem) {
  return [employee.first_name, employee.last_name]
    .map((value) => `${value ?? ""}`.trim().charAt(0))
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

function getEmployeeListPhotoUrl(employee: EmployeeListItem) {
  return employeeListPhotoPreviewUrls[employee.id] ?? "";
}

function shouldShowEmployeeListPhoto(employee: EmployeeListItem) {
  return !!getEmployeeListPhotoUrl(employee) && employeeListPhotoFailedIds[employee.id] !== true;
}

function markEmployeeListPhotoFailed(employeeId: string) {
  employeeListPhotoFailedIds[employeeId] = true;
}

function normalizeEmployeeListSearchValue(value: string | null | undefined) {
  return `${value ?? ""}`.trim().toLocaleLowerCase();
}

function employeeListSearchHaystack(employee: EmployeeListItem) {
  return [
    employee.personnel_no,
    employee.first_name,
    employee.last_name,
    employee.preferred_name,
    employee.status,
    resolveEmployeeSuggestionContact(employee),
    formatEmployeeListContext(employee),
  ]
    .map((value) => normalizeEmployeeListSearchValue(value))
    .join(" ");
}
const addressEditorEyebrowKey = computed(() => {
  switch (addressEditorMode.value) {
    case "close":
      return "employeeAdmin.addresses.closeEyebrow";
    case "edit":
      return "employeeAdmin.addresses.editEyebrow";
    case "transition":
      return "employeeAdmin.addresses.transitionEyebrow";
    default:
      return "employeeAdmin.addresses.editorEyebrow";
  }
});
const addressEditorTitleKey = computed(() => {
  switch (addressEditorMode.value) {
    case "close":
      return "employeeAdmin.addresses.closeTitle";
    case "edit":
      return "employeeAdmin.addresses.editTitle";
    case "transition":
      return "employeeAdmin.addresses.transitionTitle";
    default:
      return "employeeAdmin.addresses.editorTitle";
  }
});
const addressEditorLeadKey = computed(() => {
  switch (addressEditorMode.value) {
    case "close":
      return "employeeAdmin.addresses.closeLead";
    case "edit":
      return "employeeAdmin.addresses.editLead";
    case "transition":
      return "employeeAdmin.addresses.transitionLead";
    default:
      return "employeeAdmin.addresses.editorLead";
  }
});
const employeeDetailTabs = computed(() => {
  if (isCreatingEmployee.value) {
    return [{ id: "overview", label: t("employeeAdmin.tabs.overview") }];
  }

  return [
    { id: "dashboard", label: t("employeeAdmin.tabs.dashboard") },
    { id: "overview", label: t("employeeAdmin.tabs.overview") },
  ];
});

const legacyEmployeeDetailTabIds = new Set([
  "app_access",
  "qualifications",
  "credentials",
  "availability",
  "private_profile",
  "addresses",
  "absences",
  "notes",
  "groups",
  "documents",
]);

type EmployeeOverviewSectionId =
  | "employee_file"
  | "app_access"
  | "qualifications"
  | "credentials"
  | "availability"
  | "private_profile"
  | "addresses"
  | "absences"
  | "notes"
  | "groups"
  | "documents";

type EmployeeOverviewSection = {
  id: EmployeeOverviewSectionId;
  icon: string;
  label: string;
  testId: string;
  visible: boolean;
};

const employeeOverviewSections = computed(() => {
  const existingEmployeeVisible = !isCreatingEmployee.value && !!selectedEmployee.value;
  const privateEmployeeVisible = existingEmployeeVisible && canReadPrivate.value;

  return [
    {
      id: "employee_file",
      icon: "lucide:id-card",
      label: t("employeeAdmin.overviewSections.employeeFile"),
      testId: "employee-overview-nav-file",
      visible: true,
    },
    {
      id: "app_access",
      icon: "lucide:key-round",
      label: t("employeeAdmin.overviewSections.appAccess"),
      testId: "employee-overview-nav-app_access",
      visible: existingEmployeeVisible,
    },
    {
      id: "qualifications",
      icon: "lucide:award",
      label: t("employeeAdmin.overviewSections.qualifications"),
      testId: "employee-overview-nav-qualifications",
      visible: existingEmployeeVisible,
    },
    {
      id: "credentials",
      icon: "lucide:badge-check",
      label: t("employeeAdmin.overviewSections.credentials"),
      testId: "employee-overview-nav-credentials",
      visible: existingEmployeeVisible,
    },
    {
      id: "availability",
      icon: "lucide:calendar-clock",
      label: t("employeeAdmin.overviewSections.availability"),
      testId: "employee-overview-nav-availability",
      visible: existingEmployeeVisible,
    },
    {
      id: "private_profile",
      icon: "lucide:user-lock",
      label: t("employeeAdmin.overviewSections.privateProfile"),
      testId: "employee-overview-nav-private_profile",
      visible: privateEmployeeVisible,
    },
    {
      id: "addresses",
      icon: "lucide:map-pin",
      label: t("employeeAdmin.overviewSections.addresses"),
      testId: "employee-overview-nav-addresses",
      visible: privateEmployeeVisible,
    },
    {
      id: "absences",
      icon: "lucide:calendar-x",
      label: t("employeeAdmin.overviewSections.absences"),
      testId: "employee-overview-nav-absences",
      visible: privateEmployeeVisible,
    },
    {
      id: "notes",
      icon: "lucide:sticky-note",
      label: t("employeeAdmin.overviewSections.notes"),
      testId: "employee-overview-nav-notes",
      visible: existingEmployeeVisible,
    },
    {
      id: "groups",
      icon: "lucide:users",
      label: t("employeeAdmin.overviewSections.groups"),
      testId: "employee-overview-nav-groups",
      visible: existingEmployeeVisible,
    },
    {
      id: "documents",
      icon: "lucide:file-text",
      label: t("employeeAdmin.overviewSections.documents"),
      testId: "employee-overview-nav-documents",
      visible: existingEmployeeVisible,
    },
  ] satisfies EmployeeOverviewSection[];
});

const visibleEmployeeOverviewSections = computed(() => employeeOverviewSections.value.filter((section) => section.visible));

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

function isEmployeeDetailTabDisabled(tabId: string) {
  void tabId;
  if (isCreatingEmployee.value) {
    return false;
  }
  if (selectedEmployee.value) {
    return false;
  }
  return true;
}

function selectEmployeeDetailTab(tabId: string) {
  activeDetailTab.value = tabId;
  if (tabId === "overview") {
    activeOverviewSection.value = "employee_file";
  }
}

function selectOverviewSection(sectionId: string) {
  activeOverviewSection.value = normalizeOverviewSectionId(sectionId);
  suppressOverviewScrollSpy();
  scrollToOverviewSection(activeOverviewSection.value);
}

function openEmployeeOverviewSection(sectionId: string) {
  activeDetailTab.value = "overview";
  activeOverviewSection.value = normalizeOverviewSectionId(sectionId);
  suppressOverviewScrollSpy();
  scrollToOverviewSection(activeOverviewSection.value);
}

function normalizeOverviewSectionId(sectionId: string): EmployeeOverviewSectionId {
  const normalizedSectionId = sectionId === "file" ? "employee_file" : sectionId;
  const matchingSection = employeeOverviewSections.value.find((section) => section.id === normalizedSectionId);
  if (matchingSection?.visible) {
    return matchingSection.id;
  }
  return "employee_file";
}

function scrollToOverviewSection(sectionId: EmployeeOverviewSectionId) {
  void nextTick(() => {
    document.getElementById(resolveOverviewSectionElementId(sectionId))?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  });
}

function suppressOverviewScrollSpy() {
  suppressOverviewScrollSpyUntil = window.performance.now() + 650;
}

function isEmployeeOverviewSectionVisible(sectionId: EmployeeOverviewSectionId) {
  return employeeOverviewSections.value.some((section) => section.id === sectionId && section.visible);
}

function resolveOverviewSectionElementId(sectionId: EmployeeOverviewSectionId) {
  return `employee-overview-section-${sectionId === "employee_file" ? "file" : sectionId.replaceAll("_", "-")}`;
}

function resolveOverviewSectionIdFromElement(element: Element): EmployeeOverviewSectionId | null {
  const sectionSuffix = element.id.replace(/^employee-overview-section-/, "");
  const sectionId = sectionSuffix === "file" ? "employee_file" : sectionSuffix.replaceAll("-", "_");
  const matchingSection = visibleEmployeeOverviewSections.value.find((section) => section.id === sectionId);
  return matchingSection?.id ?? null;
}

function disconnectEmployeeOverviewSectionObserver() {
  employeeOverviewSectionObserver?.disconnect();
  employeeOverviewSectionObserver = null;
  employeeOverviewVisibleEntries.clear();
}

function resolveOverviewStickyTop() {
  const navShell = overviewNavShellRef.value;
  if (navShell) {
    const top = Number.parseFloat(window.getComputedStyle(navShell).top);
    if (Number.isFinite(top)) {
      return top;
    }
  }

  const rootFontSize = Number.parseFloat(window.getComputedStyle(document.documentElement).fontSize);
  const baseTop = (Number.isFinite(rootFontSize) ? rootFontSize : 16) * 6.5;
  return baseTop + EXTRA_SECTION_NAV_TOP_OFFSET;
}

function isScrollableAncestor(element: HTMLElement) {
  const overflowY = window.getComputedStyle(element).overflowY;
  return /(auto|scroll|overlay)/.test(overflowY) && element.scrollHeight > element.clientHeight;
}

function findOverviewScrollContainers() {
  const containers: HTMLElement[] = [];
  let parent = overviewOnePageRef.value?.parentElement ?? null;

  while (parent && parent !== document.body) {
    if (isScrollableAncestor(parent)) {
      containers.push(parent);
    }
    parent = parent.parentElement;
  }

  return containers;
}

function resolveOverviewIntersectionRoot() {
  return findOverviewScrollContainers()[0] ?? null;
}

function resolveActiveEmployeeOverviewSection(sectionElements: HTMLElement[]) {
  const stickyTop = resolveOverviewStickyTop();
  const activeLineTolerance = 32;
  const visibleSections = sectionElements
    .map((element) => {
      const sectionId = resolveOverviewSectionIdFromElement(element);
      if (!sectionId || !employeeOverviewVisibleEntries.has(sectionId)) {
        return null;
      }
      const rect = element.getBoundingClientRect();
      return {
        distance: Math.abs(rect.top - stickyTop),
        isCurrentOrNear: rect.top <= stickyTop + activeLineTolerance,
        rectTop: rect.top,
        sectionId,
      };
    })
    .filter((entry): entry is Exclude<typeof entry, null> => !!entry);

  const currentSections = visibleSections.filter((section) => section.isCurrentOrNear);
  const [bestSection] = (currentSections.length ? currentSections : visibleSections).sort((left, right) => {
    if (left.distance !== right.distance) {
      return left.distance - right.distance;
    }
    return left.rectTop - right.rectTop;
  });

  return bestSection?.sectionId ?? null;
}

function resetOverviewNavFloating() {
  overviewNavFloatingMode.value = "static";
  overviewNavFloatingStyle.value = {};
}

function cancelOverviewNavFloatingFrame() {
  if (overviewNavFloatingRaf !== null) {
    window.cancelAnimationFrame(overviewNavFloatingRaf);
    overviewNavFloatingRaf = null;
  }
}

function updateOverviewNavFloating() {
  overviewNavFloatingRaf = null;

  const overviewElement = overviewOnePageRef.value;
  const navShell = overviewNavShellRef.value;
  if (
    activeDetailTab.value !== "overview" ||
    !overviewElement ||
    !navShell ||
    !window.matchMedia(`(min-width: ${OVERVIEW_NAV_FLOATING_MIN_WIDTH}px)`).matches
  ) {
    resetOverviewNavFloating();
    return;
  }

  const stickyTop = resolveOverviewStickyTop();
  const overviewRect = overviewElement.getBoundingClientRect();
  const navWidth = navShell.offsetWidth;
  const navHeight = navShell.offsetHeight;

  if (!navWidth || !navHeight || overviewRect.top > stickyTop || overviewRect.height <= navHeight) {
    resetOverviewNavFloating();
    return;
  }

  const maxHeight = `calc(100vh - ${Math.round(stickyTop)}px - 1rem)`;
  if (overviewRect.bottom <= stickyTop + navHeight) {
    overviewNavFloatingMode.value = "pinned";
    overviewNavFloatingStyle.value = {
      left: "0px",
      maxHeight,
      top: `${Math.max(0, overviewElement.offsetHeight - navHeight)}px`,
      width: `${navWidth}px`,
    };
    return;
  }

  overviewNavFloatingMode.value = "fixed";
  overviewNavFloatingStyle.value = {
    left: `${overviewRect.left}px`,
    maxHeight,
    top: `${stickyTop}px`,
    width: `${navWidth}px`,
  };
}

function scheduleOverviewNavFloatingUpdate() {
  if (overviewNavFloatingRaf !== null) {
    return;
  }
  overviewNavFloatingRaf = window.requestAnimationFrame(updateOverviewNavFloating);
}

function teardownOverviewNavFloating() {
  cancelOverviewNavFloatingFrame();
  overviewNavScrollTargets.forEach((target) => target.removeEventListener("scroll", scheduleOverviewNavFloatingUpdate));
  window.removeEventListener("resize", scheduleOverviewNavFloatingUpdate);
  overviewNavScrollTargets = [];
  resetOverviewNavFloating();
}

function setupOverviewNavFloating() {
  teardownOverviewNavFloating();

  if (activeDetailTab.value !== "overview" || !overviewOnePageRef.value || !overviewNavShellRef.value) {
    return;
  }

  overviewNavScrollTargets = [window, ...findOverviewScrollContainers()];
  overviewNavScrollTargets.forEach((target) =>
    target.addEventListener("scroll", scheduleOverviewNavFloatingUpdate, { passive: true }),
  );
  window.addEventListener("resize", scheduleOverviewNavFloatingUpdate, { passive: true });
  scheduleOverviewNavFloatingUpdate();
}

function setupEmployeeOverviewSectionObserver() {
  disconnectEmployeeOverviewSectionObserver();

  if (activeDetailTab.value !== "overview" || typeof window.IntersectionObserver === "undefined") {
    return;
  }

  const sectionElements = visibleEmployeeOverviewSections.value
    .map((section) => document.getElementById(resolveOverviewSectionElementId(section.id)))
    .filter((element): element is HTMLElement => !!element);

  if (!sectionElements.length) {
    return;
  }

  const stickyTop = resolveOverviewStickyTop();
  employeeOverviewSectionObserver = new IntersectionObserver(
    (entries) => {
      if (window.performance.now() < suppressOverviewScrollSpyUntil) {
        return;
      }

      entries.forEach((entry) => {
        const sectionId = resolveOverviewSectionIdFromElement(entry.target);
        if (!sectionId) {
          return;
        }
        if (entry.isIntersecting) {
          employeeOverviewVisibleEntries.set(sectionId, entry);
          return;
        }
        employeeOverviewVisibleEntries.delete(sectionId);
      });

      const sectionId = resolveActiveEmployeeOverviewSection(sectionElements);
      if (sectionId) {
        activeOverviewSection.value = sectionId;
      }
    },
    {
      root: resolveOverviewIntersectionRoot(),
      rootMargin: `-${Math.round(stickyTop)}px 0px -55% 0px`,
      threshold: [0, 0.1, 0.25, 0.5, 0.75, 1],
    },
  );

  sectionElements.forEach((element) => employeeOverviewSectionObserver?.observe(element));
}

function openWorkforceCatalogs() {
  void router.push("/admin/workforce-catalogs");
}

function openEmployeeOverviewEditor(dialog: Exclude<EmployeeOverviewEditorDialog, null>) {
  activeEmployeeOverviewEditor.value = dialog;
}

function closeEmployeeOverviewEditor() {
  activeEmployeeOverviewEditor.value = null;
}

function openNewQualificationEditor() {
  resetQualificationDraft();
  openEmployeeOverviewEditor("qualification");
}

function openQualificationProofEditor() {
  if (selectedQualification.value) {
    openEmployeeOverviewEditor("qualification_proof");
  }
}

function openNewCredentialEditor() {
  resetCredentialDraft();
  openEmployeeOverviewEditor("credential");
}

function openNewAvailabilityEditor() {
  resetAvailabilityDraft();
  openEmployeeOverviewEditor("availability");
}

function openNewAbsenceEditor() {
  resetAbsenceDraft();
  openEmployeeOverviewEditor("absence");
}

function openNewNoteEditor() {
  resetNoteDraft();
  openEmployeeOverviewEditor("note");
}

function openGroupCatalogEditor() {
  openEmployeeOverviewEditor("group_catalog");
}

function openGroupAssignmentEditor() {
  resetMembershipDraft();
  openEmployeeOverviewEditor("group_assignment");
}

function openNewAddressEditor() {
  resetAddressDraft();
  openEmployeeOverviewEditor("address");
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

function buildEmployeeSearchParams(searchOverride?: string): EmployeeListFilters {
  return {
    ...filters,
    search: searchOverride ?? filters.search,
  };
}

function syncAdvancedFilterDraftFromFilters() {
  advancedFilterDraft.status = filters.status ?? "";
  advancedFilterDraft.default_branch_id = filters.default_branch_id ?? "";
  advancedFilterDraft.default_mandate_id = filters.default_mandate_id ?? "";
  advancedFilterDraft.include_archived = !!filters.include_archived;
}

function openAdvancedFiltersDialog() {
  syncAdvancedFilterDraftFromFilters();
  advancedFiltersModalOpen.value = true;
}

function closeAdvancedFiltersDialog() {
  syncAdvancedFilterDraftFromFilters();
  advancedFiltersModalOpen.value = false;
}

async function applyAdvancedFilters() {
  filters.status = advancedFilterDraft.status;
  filters.default_branch_id = advancedFilterDraft.default_branch_id;
  filters.default_mandate_id = advancedFilterDraft.default_mandate_id;
  filters.include_archived = advancedFilterDraft.include_archived;
  await refreshEmployees({ autoSelectFirst: false });
  advancedFiltersModalOpen.value = false;
}

function openImportExportDialog() {
  importExportModalOpen.value = true;
}

function closeImportExportDialog() {
  importExportModalOpen.value = false;
}

function resolveCredentialLifecycleMode(credential: EmployeeCredentialRead): "archive" | "revoke" {
  return credential.status === "issued" ? "revoke" : "archive";
}

function credentialLifecycleActionLabel(credential: EmployeeCredentialRead) {
  return t(
    resolveCredentialLifecycleMode(credential) === "revoke"
      ? ("employeeAdmin.actions.revokeCredential" as never)
      : ("employeeAdmin.actions.archiveCredential" as never),
  );
}

function openCredentialLifecycleDialog(credential: EmployeeCredentialRead) {
  selectedCredentialLifecycleId.value = credential.id;
  credentialLifecycleMode.value = resolveCredentialLifecycleMode(credential);
  credentialLifecycleDialogOpen.value = true;
}

function closeCredentialLifecycleDialog() {
  credentialLifecycleDialogOpen.value = false;
  selectedCredentialLifecycleId.value = "";
  credentialLifecycleMode.value = null;
}

function openAddressHistoryDialog() {
  addressHistoryDialogOpen.value = true;
}

function closeAddressHistoryDialog() {
  addressHistoryDialogOpen.value = false;
}

function openResetPasswordDialog() {
  resetPasswordDialogOpen.value = true;
}

function closeResetPasswordDialog() {
  resetPasswordDialogOpen.value = false;
}

function openAccessDiagnosticsDialog() {
  accessDiagnosticsDialogOpen.value = true;
}

function closeAccessDiagnosticsDialog() {
  accessDiagnosticsDialogOpen.value = false;
}

function clearEmployeeSearchDebounce() {
  if (employeeSearchDebounceHandle) {
    clearTimeout(employeeSearchDebounceHandle);
    employeeSearchDebounceHandle = null;
  }
}

function resetEmployeeSearchState(options: { closeModal?: boolean } = {}) {
  clearEmployeeSearchDebounce();
  employeeSearchRequestSeq += 1;
  loading.employeeSearch = false;
  employeeSearchResults.value = [];
  employeeSearchSuggestions.value = [];
  employeeSearchSuggestionsSuppressed.value = false;
  employeeSearchError.value = "";
  if (options.closeModal) {
    employeeSearchModalOpen.value = false;
  }
}

function closeEmployeeSearchResultsModal() {
  employeeSearchModalOpen.value = false;
}

function closeEmployeeSearchSuggestions() {
  clearEmployeeSearchDebounce();
  employeeSearchRequestSeq += 1;
  employeeSearchSuggestions.value = [];
  employeeSearchSuggestionsSuppressed.value = true;
  loading.employeeSearch = false;
}

function resolveEmployeeSuggestionContact(employee: EmployeeListItem) {
  const contact = employee as EmployeeListItem & { work_phone?: null | string };
  return contact.work_email || contact.mobile_phone || contact.work_phone || t("employeeAdmin.summary.none");
}

function resolveEmployeeSearchErrorMessage(error: unknown) {
  if (error instanceof EmployeeAdminApiError) {
    return t(mapEmployeeApiMessage(error.messageKey) as never);
  }
  return t("employeeAdmin.feedback.error");
}

async function runEmployeeSearch(options: { openModal?: boolean; suppressFeedback?: boolean } = {}) {
  if (!resolvedTenantScopeId.value || !authStore.accessToken || !canRead.value) {
    resetEmployeeSearchState({ closeModal: true });
    return [];
  }

  const requestSeq = ++employeeSearchRequestSeq;
  loading.employeeSearch = true;
  employeeSearchError.value = "";
  try {
    const results = await listEmployees(
      resolvedTenantScopeId.value,
      authStore.accessToken,
      buildEmployeeSearchParams(employeeSearchQuery.value),
    );
    if (requestSeq !== employeeSearchRequestSeq) {
      return [];
    }
    employeeSearchResults.value = results;
    employeeSearchSuggestions.value = employeeSearchQuery.value ? results.slice(0, 6) : [];
    employeeSearchSuggestionsSuppressed.value = false;
    if (options.openModal) {
      employeeSearchModalOpen.value = true;
    }
    return results;
  } catch (error) {
    if (requestSeq !== employeeSearchRequestSeq) {
      return [];
    }
    employeeSearchResults.value = [];
    employeeSearchSuggestions.value = [];
    employeeSearchError.value = resolveEmployeeSearchErrorMessage(error);
    if (options.openModal) {
      employeeSearchModalOpen.value = true;
    }
    if (!options.suppressFeedback) {
      setFeedback("error", t("employeeAdmin.feedback.titleError"), employeeSearchError.value);
    }
    return [];
  } finally {
    if (requestSeq === employeeSearchRequestSeq) {
      loading.employeeSearch = false;
    }
  }
}

async function handleOpenEmployeeSearchResults() {
  clearEmployeeSearchDebounce();
  await runEmployeeSearch({ openModal: true });
}

async function openEmployeeWorkspace(employeeId: string, detailTab = "dashboard") {
  closeAdvancedFiltersDialog();
  closeImportExportDialog();
  await selectEmployee(employeeId, { fallbackTab: detailTab });
  if (!legacyEmployeeDetailTabIds.has(detailTab)) {
    activeDetailTab.value = detailTab;
  }
}

async function selectEmployeeFromSearchResult(employeeId: string) {
  employeeSearchModalOpen.value = false;
  employeeSearchSuggestions.value = [];
  employeeSearchSuggestionsSuppressed.value = true;
  employeeSearchError.value = "";
  await openEmployeeWorkspace(employeeId, "dashboard");
}

async function selectEmployeeFromSuggestion(employee: EmployeeListItem) {
  clearEmployeeSearchDebounce();
  employeeSearchRequestSeq += 1;
  employeeSearchModalOpen.value = false;
  employeeSearchSuggestions.value = [];
  employeeSearchSuggestionsSuppressed.value = true;
  employeeSearchError.value = "";
  suppressNextEmployeeSearchWatch = true;
  filters.search = `${employee.personnel_no} · ${employee.first_name} ${employee.last_name}`;
  await openEmployeeWorkspace(employee.id, "dashboard");
}

async function returnToEmployeeList() {
  isCreatingEmployee.value = false;
  resetSelectedEmployeeWorkspaceState();
  closeAdvancedFiltersDialog();
  closeImportExportDialog();
  await nextTick();
}

function handleAdminMenuReselect(event: Event) {
  const detail = (event as CustomEvent<AdminMenuReselectDetail>).detail;
  if (detail?.to !== "/admin/employees") {
    return;
  }
  if (!hasEmployeeDetailWorkspace.value) {
    return;
  }
  void returnToEmployeeList();
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
  privateProfileDraft.private_email = selectedPrivateProfile.value?.private_email || "";
  privateProfileDraft.private_phone = selectedPrivateProfile.value?.private_phone || "";
  privateProfileDraft.birth_date = selectedPrivateProfile.value?.birth_date || "";
  privateProfileDraft.place_of_birth = selectedPrivateProfile.value?.place_of_birth || "";
  privateProfileDraft.nationality_country_code = selectedPrivateProfile.value?.nationality_country_code || "";
  privateProfileDraft.marital_status_code = selectedPrivateProfile.value?.marital_status_code || "";
  privateProfileDraft.tax_id = selectedPrivateProfile.value?.tax_id || "";
  privateProfileDraft.social_security_no = selectedPrivateProfile.value?.social_security_no || "";
  privateProfileDraft.bank_account_holder = selectedPrivateProfile.value?.bank_account_holder || "";
  privateProfileDraft.bank_iban = selectedPrivateProfile.value?.bank_iban || "";
  privateProfileDraft.bank_bic = selectedPrivateProfile.value?.bank_bic || "";
  privateProfileDraft.emergency_contact_name = selectedPrivateProfile.value?.emergency_contact_name || "";
  privateProfileDraft.emergency_contact_phone = selectedPrivateProfile.value?.emergency_contact_phone || "";
  privateProfileDraft.notes = selectedPrivateProfile.value?.notes || "";
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
  privateProfileDraft.private_email = profile?.private_email || "";
  privateProfileDraft.private_phone = profile?.private_phone || "";
  privateProfileDraft.birth_date = profile?.birth_date || "";
  privateProfileDraft.place_of_birth = profile?.place_of_birth || "";
  privateProfileDraft.nationality_country_code = profile?.nationality_country_code || "";
  privateProfileDraft.marital_status_code = profile?.marital_status_code || "";
  privateProfileDraft.tax_id = profile?.tax_id || "";
  privateProfileDraft.social_security_no = profile?.social_security_no || "";
  privateProfileDraft.bank_account_holder = profile?.bank_account_holder || "";
  privateProfileDraft.bank_iban = profile?.bank_iban || "";
  privateProfileDraft.bank_bic = profile?.bank_bic || "";
  privateProfileDraft.emergency_contact_name = profile?.emergency_contact_name || "";
  privateProfileDraft.emergency_contact_phone = profile?.emergency_contact_phone || "";
  privateProfileDraft.notes = profile?.notes || "";
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
  openEmployeeOverviewEditor("note");
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
  addressDraft.is_primary = true;
  addressDraft.notes = "";
  editingAddressId.value = "";
  addressTransitionSourceId.value = "";
  addressEditorMode.value = "create";
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
  closeCredentialLifecycleDialog();
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
  openEmployeeOverviewEditor("qualification");
}

function editCredential(credential: EmployeeCredentialRead) {
  closeCredentialLifecycleDialog();
  editingCredentialId.value = credential.id;
  credentialDraft.credential_no = credential.credential_no;
  credentialDraft.credential_type = credential.credential_type;
  credentialDraft.encoded_value = credential.encoded_value;
  credentialDraft.valid_from = credential.valid_from;
  credentialDraft.valid_until = credential.valid_until || "";
  credentialDraft.notes = credential.notes || "";
  openEmployeeOverviewEditor("credential");
}

function editAvailabilityRule(rule: EmployeeAvailabilityRuleRead) {
  editingAvailabilityRuleId.value = rule.id;
  availabilityDraft.rule_kind = rule.rule_kind;
  availabilityDraft.starts_at = toLocalDateTimeInput(rule.starts_at);
  availabilityDraft.ends_at = toLocalDateTimeInput(rule.ends_at);
  availabilityDraft.recurrence_type = rule.recurrence_type || "none";
  availabilityDraft.weekday_indexes = parseWeekdayMask(rule.weekday_mask);
  availabilityDraft.notes = rule.notes || "";
  openEmployeeOverviewEditor("availability");
}

function editAbsence(absence: EmployeeAbsenceRead) {
  editingAbsenceId.value = absence.id;
  absenceDraft.absence_type = absence.absence_type;
  absenceDraft.starts_on = absence.starts_on;
  absenceDraft.ends_on = absence.ends_on;
  absenceDraft.decision_note = absence.decision_note || "";
  absenceDraft.notes = absence.notes || "";
  openEmployeeOverviewEditor("absence");
}

function useEmployeeDocumentForVersion(document: EmployeeDocumentListItemRead) {
  selectedEmployeeDocumentId.value = document.document_id;
  openEmployeeOverviewEditor("document_version");
}

function editAddress(row: EmployeeAddressHistoryRead) {
  addressEditorMode.value = "edit";
  editingAddressId.value = row.id;
  addressTransitionSourceId.value = "";
  addressDraft.street_line_1 = row.address?.street_line_1 || "";
  addressDraft.street_line_2 = row.address?.street_line_2 || "";
  addressDraft.postal_code = row.address?.postal_code || "";
  addressDraft.city = row.address?.city || "";
  addressDraft.state_region = row.address?.state_region || "";
  addressDraft.country_code = row.address?.country_code || "DE";
  addressDraft.address_type = row.address_type;
  addressDraft.valid_from = row.valid_from;
  addressDraft.valid_to = row.valid_to || "";
  addressDraft.is_primary = row.is_primary;
  addressDraft.notes = row.notes || "";
  openEmployeeOverviewEditor("address");
}

function prepareAddressAsCurrent(row: EmployeeAddressHistoryRead) {
  addressEditorMode.value = "transition";
  editingAddressId.value = "";
  addressTransitionSourceId.value = row.id;
  addressDraft.street_line_1 = row.address?.street_line_1 || "";
  addressDraft.street_line_2 = row.address?.street_line_2 || "";
  addressDraft.postal_code = row.address?.postal_code || "";
  addressDraft.city = row.address?.city || "";
  addressDraft.state_region = row.address?.state_region || "";
  addressDraft.country_code = row.address?.country_code || "DE";
  addressDraft.address_type = row.address_type;
  addressDraft.valid_from = new Date().toISOString().slice(0, 10);
  addressDraft.valid_to = "";
  addressDraft.is_primary = row.is_primary;
  addressDraft.notes = row.notes || "";
  openEmployeeOverviewEditor("address");
}

function prepareAddressValidityClose(row: EmployeeAddressHistoryRead) {
  editAddress(row);
  addressEditorMode.value = "close";
  addressDraft.valid_to = row.valid_to || new Date().toISOString().slice(0, 10);
}

function editAddressFromHistoryDialog(row: EmployeeAddressHistoryRead) {
  closeAddressHistoryDialog();
  editAddress(row);
}

function prepareAddressAsCurrentFromHistoryDialog(row: EmployeeAddressHistoryRead) {
  closeAddressHistoryDialog();
  prepareAddressAsCurrent(row);
}

function prepareAddressValidityCloseFromHistoryDialog(row: EmployeeAddressHistoryRead) {
  closeAddressHistoryDialog();
  prepareAddressValidityClose(row);
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
  resetPasswordDialogOpen.value = false;
  accessDiagnosticsDialogOpen.value = false;
  closeCredentialLifecycleDialog();
}

function editMembership(membership: EmployeeGroupMembershipRead) {
  editingMembershipId.value = membership.id;
  membershipDraft.group_id = membership.group_id;
  membershipDraft.valid_from = membership.valid_from;
  membershipDraft.valid_until = membership.valid_until || "";
  membershipDraft.notes = membership.notes || "";
  openEmployeeOverviewEditor("group_assignment");
}

function startCreateEmployee() {
  closeAdvancedFiltersDialog();
  closeImportExportDialog();
  closeCredentialLifecycleDialog();
  closeAddressHistoryDialog();
  closeResetPasswordDialog();
  closeAccessDiagnosticsDialog();
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

function resetSelectedEmployeeWorkspaceState() {
  closeAddressHistoryDialog();
  closeResetPasswordDialog();
  closeAccessDiagnosticsDialog();
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
  selectedEmployeeDocumentId.value = "";
  activeDetailTab.value = "overview";
  activeOverviewSection.value = "employee_file";
  activeEmployeeOverviewEditor.value = null;
  syncPrivateProfileDraft(null);
  clearPhotoPreview();
  resetEmployeeDocumentDrafts();
  resetAccessDrafts();
}

function clearPhotoPreview() {
  if (photoPreviewUrl.value && !Object.values(employeeListPhotoPreviewUrls).includes(photoPreviewUrl.value)) {
    URL.revokeObjectURL(photoPreviewUrl.value);
  }
  photoPreviewUrl.value = "";
}

function syncEmployeeListPhotoPreview(employeeId: string, previewUrl: string) {
  const previousUrl = employeeListPhotoPreviewUrls[employeeId];
  if (previousUrl && previousUrl !== previewUrl) {
    URL.revokeObjectURL(previousUrl);
  }
  employeeListPhotoPreviewUrls[employeeId] = previewUrl;
  employeeListPhotoFailedIds[employeeId] = false;
}

async function preloadEmployeeListPhotos(rows: EmployeeListItem[]) {
  if (!resolvedTenantScopeId.value || !authStore.accessToken) {
    return;
  }

  const queue = rows.filter(
    (employee) =>
      !!employee.photo_document_id
      && !!employee.photo_current_version_no
      && !employeeListPhotoPreviewUrls[employee.id]
      && employeeListPhotoPendingIds[employee.id] !== true,
  );
  if (!queue.length) {
    return;
  }

  const worker = async () => {
    while (queue.length) {
      const employee = queue.shift();
      if (!employee?.photo_document_id || !employee.photo_current_version_no) {
        continue;
      }
      employeeListPhotoPendingIds[employee.id] = true;
      try {
        const file = await downloadEmployeeDocument(
          resolvedTenantScopeId.value!,
          employee.photo_document_id,
          employee.photo_current_version_no,
          authStore.accessToken,
        );
        syncEmployeeListPhotoPreview(employee.id, URL.createObjectURL(file.blob));
      } catch {
        employeeListPhotoFailedIds[employee.id] = true;
      } finally {
        delete employeeListPhotoPendingIds[employee.id];
      }
    }
  };

  await Promise.all(
    Array.from(
      { length: Math.min(EMPLOYEE_LIST_PHOTO_PRELOAD_CONCURRENCY, queue.length) },
      () => worker(),
    ),
  );
}

async function refreshEmployees(options: { autoSelectFirst?: boolean } = {}) {
  if (!resolvedTenantScopeId.value || !authStore.accessToken || !canRead.value) {
    branches.value = [];
    mandates.value = [];
    maritalStatusOptions.value = [];
    maritalStatusLookupError.value = "";
    employees.value = [];
    resetEmployeeSearchState({ closeModal: true });
    selectedEmployee.value = null;
    return;
  }

  const { autoSelectFirst = false } = options;
  loading.list = true;
  try {
    employees.value = await listEmployees(resolvedTenantScopeId.value, authStore.accessToken, filters);
    void preloadEmployeeListPhotos(employees.value);
    if (selectedEmployeeId.value) {
      const stillSelected = employees.value.some((row) => row.id === selectedEmployeeId.value);
      if (stillSelected) {
        await selectEmployee(selectedEmployeeId.value);
      } else {
        selectedEmployeeId.value = "";
        selectedEmployee.value = null;
      }
    } else if (autoSelectFirst && employees.value.length && !isCreatingEmployee.value) {
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

  if (canReadPrivate.value) {
    try {
      await loadPrivateProfileMaritalStatusOptions();
    } catch {
      maritalStatusOptions.value = [];
      maritalStatusLookupError.value = t("employeeAdmin.privateProfile.maritalStatusLoadError");
      catalogRefreshFailed = true;
    }
  } else {
    maritalStatusOptions.value = [];
    maritalStatusLookupError.value = "";
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

async function loadPrivateProfileMaritalStatusOptions() {
  if (!resolvedTenantScopeId.value || !authStore.accessToken || !canReadPrivate.value) {
    maritalStatusOptions.value = [];
    maritalStatusLookupError.value = "";
    return;
  }
  maritalStatusOptionsLoading.value = true;
  maritalStatusLookupError.value = "";
  try {
    maritalStatusOptions.value = await listEmployeePrivateProfileMaritalStatusOptions(
      resolvedTenantScopeId.value,
      authStore.accessToken,
    );
  } catch {
    maritalStatusOptions.value = [];
    maritalStatusLookupError.value = t("employeeAdmin.privateProfile.maritalStatusLoadError");
  } finally {
    maritalStatusOptionsLoading.value = false;
  }
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
  const { preserveActiveTab = false, fallbackTab = "dashboard" } = options;
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
    if (legacyEmployeeDetailTabIds.has(desiredTab)) {
      openEmployeeOverviewSection(desiredTab);
    } else if (desiredTab === "profile_photo") {
      activeDetailTab.value = "dashboard";
    } else {
      activeDetailTab.value = resolveEmployeeDetailTab(
        desiredTab,
        employeeDetailTabs.value.map((tab) => tab.id),
        fallbackTab,
      );
    }
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
  if (selectedEmployeeId.value) {
    const listEmployee = employees.value.find((employee) => employee.id === selectedEmployeeId.value);
    const cachedUrl = employeeListPhotoPreviewUrls[selectedEmployeeId.value];
    if (
      cachedUrl
      && listEmployee?.photo_document_id === currentPhoto.value.document_id
      && listEmployee.photo_current_version_no === currentPhoto.value.current_version_no
      && employeeListPhotoFailedIds[selectedEmployeeId.value] !== true
    ) {
      photoPreviewUrl.value = cachedUrl;
      return;
    }
  }
  try {
    const file = await downloadEmployeeDocument(
      resolvedTenantScopeId.value,
      currentPhoto.value.document_id,
      currentPhoto.value.current_version_no,
      authStore.accessToken,
    );
    photoPreviewUrl.value = URL.createObjectURL(file.blob);
    if (selectedEmployeeId.value) {
      syncEmployeeListPhotoPreview(selectedEmployeeId.value, photoPreviewUrl.value);
    }
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

  const validationKey = validateEmployeePrivateProfileDraft(privateProfileDraft);
  if (validationKey) {
    setFeedback("error", t("employeeAdmin.feedback.titleError"), t(validationKey as never));
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
    closeEmployeeOverviewEditor();
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
    closeEmployeeOverviewEditor();
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
    closeEmployeeOverviewEditor();
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
    valid_to: addressDraft.valid_to.trim() || null,
    is_primary: addressDraft.is_primary,
    notes: addressDraft.notes.trim() || null,
  };
}

async function submitAddress() {
  if (!resolvedTenantScopeId.value || !authStore.accessToken || !selectedEmployeeId.value) {
    return;
  }

  const currentSameTypeAddress = employeeAddresses.value.find((row) =>
    row.id !== addressTransitionSourceId.value && row.address_type === addressDraft.address_type && isEmployeeAddressCurrent(row),
  );
  const validationKey = validateEmployeeAddressDraft(
    addressDraft,
    employeeAddresses.value,
    editingAddressId.value,
    addressEditorMode.value === "transition" && currentSameTypeAddress
      ? { ignoreRowIds: [currentSameTypeAddress.id] }
      : undefined,
  );
  if (validationKey) {
    setFeedback("error", t("employeeAdmin.feedback.titleError"), t(validationKey as never));
    return;
  }

  loading.action = true;
  try {
    if (addressEditorMode.value === "transition") {
      const effectiveFrom = addressDraft.valid_from.trim();
      if (currentSameTypeAddress) {
        const closeDate = new Date(`${effectiveFrom}T00:00:00Z`);
        closeDate.setUTCDate(closeDate.getUTCDate() - 1);
        const closeDateIso = closeDate.toISOString().slice(0, 10);
        if (closeDateIso < currentSameTypeAddress.valid_from) {
          setFeedback(
            "error",
            t("employeeAdmin.feedback.titleError"),
            t("employeeAdmin.feedback.addressTransitionEffectiveDate" as never),
          );
          return;
        }
        await updateEmployeeAddress(
          resolvedTenantScopeId.value,
          selectedEmployeeId.value,
          currentSameTypeAddress.id,
          authStore.accessToken,
          {
            valid_to: closeDateIso,
            version_no: currentSameTypeAddress.version_no,
          },
        );
      }
      await createEmployeeAddress(
        resolvedTenantScopeId.value,
        selectedEmployeeId.value,
        authStore.accessToken,
        buildEmployeeAddressPayload() as EmployeeAddressHistoryCreatePayload,
      );
    } else if (editingAddressId.value) {
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
    closeEmployeeOverviewEditor();
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

  const validationKey = validateEmployeeQualificationDraft(qualificationDraft, selectedQualificationType.value);
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
    closeEmployeeOverviewEditor();
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
    closeEmployeeOverviewEditor();
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
    closeEmployeeOverviewEditor();
    setFeedback("success", t("employeeAdmin.feedback.titleSuccess"), t("employeeAdmin.feedback.credentialSaved"));
  } catch (error) {
    const key = error instanceof EmployeeAdminApiError ? mapEmployeeApiMessage(error.messageKey) : "employeeAdmin.feedback.error";
    setFeedback("error", t("employeeAdmin.feedback.titleError"), t(key as never));
  } finally {
    loading.action = false;
  }
}

async function confirmCredentialLifecycle() {
  const credential = selectedCredentialLifecycle.value;
  const mode = credentialLifecycleMode.value;
  if (!resolvedTenantScopeId.value || !authStore.accessToken || !credential || !mode) {
    return;
  }

  loading.action = true;
  try {
    await updateEmployeeCredential(resolvedTenantScopeId.value, credential.id, authStore.accessToken, {
      status: mode === "revoke" ? "revoked" : undefined,
      archived_at: mode === "archive" ? new Date().toISOString() : undefined,
      version_no: credential.version_no,
    } as EmployeeCredentialUpdatePayload);
    await selectEmployee(selectedEmployeeId.value, { preserveActiveTab: true });
    closeCredentialLifecycleDialog();
    setFeedback(
      "success",
      t("employeeAdmin.feedback.titleSuccess"),
      t((mode === "revoke" ? "employeeAdmin.feedback.credentialRevoked" : "employeeAdmin.feedback.credentialArchived") as never),
    );
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
    closeEmployeeOverviewEditor();
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
    closeEmployeeOverviewEditor();
    setFeedback("success", t("employeeAdmin.feedback.titleSuccess"), t("employeeAdmin.feedback.absenceSaved"));
  } catch (error) {
    const key = error instanceof EmployeeAdminApiError ? mapEmployeeApiMessage(error.messageKey) : "employeeAdmin.feedback.error";
    setFeedback("error", t("employeeAdmin.feedback.titleError"), t(key as never));
  } finally {
    loading.action = false;
  }
}

async function submitDashboardPhoto(file: File) {
  await submitPhotoFile(file);
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
    closeEmployeeOverviewEditor();
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
    closeEmployeeOverviewEditor();
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
    closeEmployeeOverviewEditor();
    setFeedback("success", t("employeeAdmin.feedback.titleSuccess"), t("employeeAdmin.feedback.documentVersionSaved"));
  } catch (error) {
    setFeedback("error", t("employeeAdmin.feedback.titleError"), resolveEmployeeDocumentErrorMessage(error));
  } finally {
    loading.action = false;
  }
}

async function submitPhotoFile(file: File) {
  if (!file || !selectedEmployeeId.value || !resolvedTenantScopeId.value || !authStore.accessToken || !actionState.value.canManagePhoto) {
    return;
  }
  loading.photo = true;
  try {
    const contentBase64 = await fileToBase64(file);
    await uploadEmployeePhoto(resolvedTenantScopeId.value, selectedEmployeeId.value, authStore.accessToken, {
      title: file.name,
      file_name: file.name,
      content_type: file.type || "application/octet-stream",
      content_base64: contentBase64,
    });
    await selectEmployee(selectedEmployeeId.value, { preserveActiveTab: true });
    setFeedback("success", t("employeeAdmin.feedback.titleSuccess"), t("employeeAdmin.feedback.photoSaved"));
  } catch (error) {
    const key = error instanceof EmployeeAdminApiError ? mapEmployeeApiMessage(error.messageKey) : "employeeAdmin.feedback.error";
    setFeedback("error", t("employeeAdmin.feedback.titleError"), t(key as never));
  } finally {
    loading.photo = false;
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
    accessResetDraft.password = "";
    closeResetPasswordDialog();
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
  () => [isCreatingEmployee.value, !!selectedEmployee.value, canReadPrivate.value, activeDetailTab.value],
  () => {
    if (legacyEmployeeDetailTabIds.has(activeDetailTab.value)) {
      openEmployeeOverviewSection(activeDetailTab.value);
      return;
    }
    if (activeDetailTab.value === "profile_photo") {
      activeDetailTab.value = isCreatingEmployee.value ? "overview" : "dashboard";
      return;
    }
    const allowedTabs = employeeDetailTabs.value.map((tab) => tab.id);
    if (!allowedTabs.includes(activeDetailTab.value)) {
      activeDetailTab.value = resolveEmployeeDetailTab(activeDetailTab.value, allowedTabs);
    }
    activeOverviewSection.value = normalizeOverviewSectionId(activeOverviewSection.value);
  },
  { immediate: true },
);

watch(
  () => [
    activeDetailTab.value,
    selectedEmployee.value?.id,
    canReadPrivate.value,
    visibleEmployeeOverviewSections.value.map((section) => section.id).join("|"),
  ] as const,
  () => {
    disconnectEmployeeOverviewSectionObserver();
    teardownOverviewNavFloating();
    if (activeDetailTab.value === "overview") {
      void nextTick(() => {
        setupEmployeeOverviewSectionObserver();
        setupOverviewNavFloating();
      });
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
  () => advancedFilterDraft.default_branch_id,
  (branchId) => {
    if (!advancedFilterDraft.default_mandate_id) {
      return;
    }
    const mandateStillValid = filterMandateOptions(branchId).some((mandate) => mandate.id === advancedFilterDraft.default_mandate_id);
    if (!mandateStillValid) {
      advancedFilterDraft.default_mandate_id = "";
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
  window.addEventListener(ADMIN_MENU_RESELECT_EVENT, handleAdminMenuReselect as EventListener);
  authStore.syncFromPrimarySession();
  try {
    await authStore.ensureSessionReady();
  } catch {
    // handled by store
  }
  tenantScopeInput.value = authStore.effectiveTenantScopeId || authStore.tenantScopeId;
  resetEmployeeDraft();
  await refreshEmployees({ autoSelectFirst: false });
});

onBeforeUnmount(() => {
  window.removeEventListener(ADMIN_MENU_RESELECT_EVENT, handleAdminMenuReselect as EventListener);
  clearEmployeeSearchDebounce();
  const previewUrls = new Set<string>([
    photoPreviewUrl.value,
    ...Object.values(employeeListPhotoPreviewUrls),
  ].filter(Boolean));
  previewUrls.forEach((url) => URL.revokeObjectURL(url));
  photoPreviewUrl.value = "";
  disconnectEmployeeOverviewSectionObserver();
  teardownOverviewNavFloating();
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
  grid-template-columns: minmax(0, 1fr);
  align-items: start;
}

.employee-admin-mode-shell {
  display: grid;
  gap: var(--sp-page-gap, 1.25rem);
  min-width: 0;
}

.employee-admin-list-panel {
  position: static;
  top: auto;
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
.employee-admin-photo__controls,
.employee-admin-detail-header-actions,
.employee-admin-list-header-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  min-width: 0;
}

.employee-admin-list-header-actions {
  align-items: center;
  justify-content: flex-end;
  gap: 0.5rem;
}

.employee-admin-detail-header-actions {
  align-items: center;
  justify-content: flex-end;
  gap: 0.5rem;
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

.employee-admin-employee-row {
  flex-wrap: nowrap;
  align-items: center;
  gap: 0.8rem;
  padding: 0.4rem 0.4rem;
}

.employee-admin-employee-row__avatar {
  width: 3.5rem;
  height: 3.5rem;
  flex: 0 0 3.5rem;
  display: grid;
  place-items: center;
  overflow: hidden;
  border-radius: 999px;
  background: color-mix(in srgb, var(--sp-color-primary-muted) 65%, white);
  color: var(--sp-color-primary-strong);
  font-size: 0.86rem;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.employee-admin-employee-row__avatar-image {
  width: 100%;
  height: 100%;
  display: block;
  border-radius: inherit;
  object-fit: cover;
  object-position: center;
}

.employee-admin-employee-row__body {
  gap: 0.18rem;
  min-width: 0;
}

.employee-admin-employee-row__line {
  display: block;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.employee-admin-employee-row__line--primary {
  font-size: 0.95rem;
}

.employee-admin-employee-row__meta {
  font-size: 0.84rem;
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

.employee-admin-search-field {
  position: relative;
}

.employee-admin-search-select {
  position: relative;
  display: grid;
}

.employee-admin-search-select input {
  width: 100%;
}

.employee-admin-filter-toolbar {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 1rem;
  align-items: end;
}

.employee-admin-filter-toolbar__actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  min-width: 0;
}

.employee-admin-header-action {
  min-height: 2.15rem;
  padding: 0.42rem 0.75rem;
  border-radius: 999px;
  font-size: 0.84rem;
}

.employee-admin-back-button {
  min-height: 2rem;
  padding: 0.32rem 0.68rem;
  border-radius: 999px;
  font-size: 0.82rem;
  font-weight: 650;
}

.employee-admin-search-suggestions {
  position: absolute;
  z-index: 4;
  inset: calc(100% + 0.4rem) 0 auto;
  display: grid;
  gap: 0.35rem;
  padding: 0.45rem;
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 16px;
  background: var(--sp-color-surface-page);
  box-shadow: 0 20px 50px rgb(15 23 42 / 0.12);
}

.employee-admin-search-suggestion,
.employee-admin-search-result {
  text-align: left;
  cursor: pointer;
  color: inherit;
  font: inherit;
}

.employee-admin-search-suggestion {
  display: grid;
  gap: 0.2rem;
  width: 100%;
  padding: 0.8rem 0.9rem;
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 12px;
  background: var(--sp-color-surface-page);
}

.employee-admin-search-suggestion__title {
  font-weight: 600;
  color: var(--sp-color-text-primary);
}

.employee-admin-search-suggestion__meta,
.employee-admin-search-suggestion__status,
.employee-admin-search-suggestion-empty {
  color: var(--sp-color-text-secondary);
}

.employee-admin-search-suggestion__status {
  font-size: 0.8rem;
  text-transform: uppercase;
}

.employee-admin-search-suggestion-empty {
  margin: 0;
  padding: 0.8rem 0.9rem;
}

.employee-admin-modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 40;
  display: grid;
  place-items: center;
  padding: 1.5rem;
  background: rgb(15 23 42 / 42%);
}

.employee-admin-modal {
  width: min(760px, 100%);
  max-height: min(720px, calc(100vh - 3rem));
  overflow: auto;
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

.employee-admin-overview-onepage {
  --employee-overview-sticky-top: calc(var(--sp-sticky-offset, 6.5rem) + 25px);
  position: relative;
  display: grid;
  grid-template-columns: minmax(190px, 240px) minmax(0, 1fr);
  gap: 1.25rem;
  align-items: start;
  min-width: 0;
}

.employee-admin-overview-content {
  grid-column: 2;
  display: grid;
  gap: 1.25rem;
  min-width: 0;
}

.employee-admin-overview-section-card {
  display: grid;
  gap: 1rem;
  padding: 1.1rem;
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 1.25rem;
  background: var(--sp-color-surface-card);
  min-width: 0;
  scroll-margin-top: var(--employee-overview-sticky-top, 6.5rem);
}

.employee-admin-overview-section-card__header,
.employee-admin-overview-section-card .employee-admin-editor-intro {
  display: grid;
  gap: 0.35rem;
  padding: 0;
  border: 0;
  border-radius: 0;
  background: transparent;
}

.employee-admin-overview-section-card__header--split {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.employee-admin-overview-section-card__header-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 0.5rem;
  min-width: 0;
}

.employee-admin-overview-section-card__header h4,
.employee-admin-overview-section-card .employee-admin-editor-intro h4 {
  margin: 0;
  color: var(--sp-color-text-primary);
}

.employee-admin-overview-subsection,
.employee-admin-overview-section-card .employee-admin-form-section,
.employee-admin-overview-section-card .employee-admin-form-actions {
  display: grid;
  gap: 0.85rem;
  padding: 0;
  border: 0;
  border-radius: 0;
  background: transparent;
}

.employee-admin-overview-subsection__header,
.employee-admin-overview-section-card .employee-admin-form-section__header {
  display: grid;
  gap: 0.25rem;
}

.employee-admin-overview-subsection + .employee-admin-overview-subsection,
.employee-admin-overview-section-card .employee-admin-overview-section-card__header + .employee-admin-form-section,
.employee-admin-overview-section-card .employee-admin-editor-intro + .employee-admin-form-section,
.employee-admin-overview-section-card .employee-admin-form-section + .employee-admin-form-section,
.employee-admin-overview-section-card .employee-admin-form-section + .employee-admin-form-actions,
.employee-admin-overview-section-card .employee-admin-form-section + .employee-admin-advanced-access {
  border-top: 1px solid var(--sp-color-border-soft);
  padding-top: 1rem;
}

.employee-admin-overview-nav-shell {
  grid-column: 1;
  position: sticky;
  top: var(--employee-overview-sticky-top, 6.5rem);
  align-self: start;
  z-index: 2;
  min-width: 0;
  max-height: calc(100vh - var(--employee-overview-sticky-top, 6.5rem) - 1rem);
  overflow-y: auto;
  overscroll-behavior: contain;
}

.employee-admin-overview-nav-shell--fixed {
  position: fixed;
}

.employee-admin-overview-nav-shell--pinned {
  position: absolute;
}

.employee-admin-overview-nav {
  display: grid;
  gap: 0.25rem;
  padding: 0.25rem 0;
  border: 0;
  background: transparent;
}

.employee-admin-overview-nav__link {
  display: grid;
  grid-template-columns: 1.25rem minmax(0, 1fr);
  align-items: center;
  gap: 0.55rem;
  width: 100%;
  padding: 0.55rem 0.35rem 0.55rem 0.75rem;
  border: 0;
  border-left: 2px solid transparent;
  border-radius: 0.35rem;
  background: transparent;
  color: var(--sp-color-text-secondary);
  font: inherit;
  text-align: left;
  cursor: pointer;
}

.employee-admin-overview-nav__link:hover,
.employee-admin-overview-nav__link:focus-visible {
  color: var(--sp-color-primary-strong);
  background: color-mix(in srgb, var(--sp-color-primary-muted) 36%, transparent);
  outline: none;
}

.employee-admin-overview-nav__link:focus-visible {
  outline: 3px solid color-mix(in srgb, var(--sp-color-primary) 38%, transparent);
  outline-offset: 2px;
}

.employee-admin-overview-nav__link--active {
  border-left-color: var(--sp-color-primary);
  color: var(--sp-color-primary-strong);
  font-weight: 700;
}

.employee-admin-overview-nav__icon {
  width: 1.08rem;
  height: 1.08rem;
  color: currentColor;
}

.employee-admin-overview-section-card .employee-admin-advanced-access {
  display: grid;
  gap: 0.85rem;
  padding: 1rem 0 0;
  border: 0;
  border-top: 1px solid var(--sp-color-border-soft);
  border-radius: 0;
  background: transparent;
}

.employee-admin-overview-section-card .employee-admin-advanced-access[open] {
  padding-bottom: 0;
}

.employee-admin-detail,
.employee-admin-form {
  display: grid;
  gap: 1rem;
  min-width: 0;
}

.employee-admin-form--structured {
  gap: 1.1rem;
}

.employee-admin-filter-grid {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  align-items: start;
}

.employee-admin-filter-grid--dialog {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.employee-admin-filter-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.employee-admin-filter-actions__buttons {
  justify-content: flex-end;
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

.employee-admin-access-diagnostics-list {
  gap: 0.7rem;
}

.employee-admin-access-diagnostic {
  align-items: center;
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
  .employee-admin-photo,
  .employee-admin-overview-onepage {
    grid-template-columns: 1fr;
    display: grid;
  }

  .employee-admin-list-panel {
    position: static;
  }

  .employee-admin-overview-nav-shell {
    grid-column: 1;
    position: static;
    max-height: none;
    overflow: visible;
  }

  .employee-admin-overview-nav-shell--fixed,
  .employee-admin-overview-nav-shell--pinned {
    position: static;
  }

  .employee-admin-overview-content {
    grid-column: 1;
  }

  .employee-admin-overview-nav {
    display: flex;
    overflow-x: auto;
    padding: 0.25rem 0 0.5rem;
  }

  .employee-admin-overview-nav__link {
    min-width: max-content;
    border-left: 0;
    border-bottom: 2px solid transparent;
    padding: 0.55rem 0.75rem;
  }

  .employee-admin-overview-nav__link--active {
    border-bottom-color: var(--sp-color-primary);
  }
}

@media (max-width: 1280px) {
  .employee-admin-filter-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
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

@media (max-width: 720px) {
  .employee-admin-filter-toolbar {
    grid-template-columns: 1fr;
  }

  .employee-admin-filter-toolbar__actions,
  .employee-admin-list-header-actions {
    justify-content: flex-start;
  }

  .employee-admin-filter-grid {
    grid-template-columns: 1fr;
  }

  .employee-admin-filter-actions {
    align-items: stretch;
    flex-direction: column;
  }

  .employee-admin-filter-actions__buttons {
    justify-content: flex-start;
  }
}
</style>
