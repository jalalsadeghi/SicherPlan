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

    <div class="module-card employee-admin-scope" :class="{ 'employee-admin-scope--embedded': embedded }">
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

    <section v-if="feedback.message" class="employee-admin-feedback" :data-tone="feedback.tone">
      <div>
        <strong>{{ feedback.title }}</strong>
        <span>{{ feedback.message }}</span>
      </div>
      <button type="button" @click="clearFeedback">{{ t("employeeAdmin.actions.clearFeedback") }}</button>
    </section>

    <section v-if="!resolvedTenantScopeId" class="module-card employee-admin-empty">
      <p class="eyebrow">{{ t("employeeAdmin.scope.missingTitle") }}</p>
      <h3>{{ t("employeeAdmin.scope.missingBody") }}</h3>
    </section>

    <section v-else-if="!canRead" class="module-card employee-admin-empty">
      <p class="eyebrow">{{ t("employeeAdmin.permission.missingTitle") }}</p>
      <h3>{{ t("employeeAdmin.permission.missingBody") }}</h3>
    </section>

    <div v-else class="employee-admin-grid">
      <section class="module-card employee-admin-panel">
        <div class="employee-admin-panel__header">
          <div>
            <p class="eyebrow">{{ t("employeeAdmin.list.eyebrow") }}</p>
            <h3>{{ t("employeeAdmin.list.title") }}</h3>
          </div>
          <StatusBadge :status="loading.list ? 'inactive' : 'active'" />
        </div>

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
            <input v-model="filters.default_branch_id" />
          </label>
          <label class="field-stack">
            <span>{{ t("employeeAdmin.fields.defaultMandateId") }}</span>
            <input v-model="filters.default_mandate_id" />
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
          <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canExport" @click="runExport">
            {{ t("employeeAdmin.actions.exportEmployees") }}
          </button>
        </div>

        <section class="employee-admin-section">
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
            <div>
              <strong>{{ employee.personnel_no }} · {{ employee.first_name }} {{ employee.last_name }}</strong>
              <span>{{ employee.work_email || employee.mobile_phone || t("employeeAdmin.summary.none") }}</span>
            </div>
            <StatusBadge :status="employee.status" />
          </button>
        </div>
        <p v-else class="employee-admin-list-empty">{{ t("employeeAdmin.list.empty") }}</p>
      </section>

      <section class="module-card employee-admin-panel employee-admin-detail">
        <div class="employee-admin-panel__header">
          <div>
            <p class="eyebrow">{{ t("employeeAdmin.detail.eyebrow") }}</p>
            <h3>{{ isCreatingEmployee ? t("employeeAdmin.detail.newTitle") : selectedEmployeeLabel }}</h3>
          </div>
          <StatusBadge v-if="selectedEmployee && !isCreatingEmployee" :status="selectedEmployee.status" />
        </div>

        <template v-if="isCreatingEmployee || selectedEmployee">
          <div v-if="selectedEmployee && !isCreatingEmployee" class="employee-admin-summary">
            <article class="employee-admin-summary__card">
              <span>{{ t("employeeAdmin.summary.branch") }}</span>
              <strong>{{ selectedEmployee.default_branch_id || t("employeeAdmin.summary.none") }}</strong>
            </article>
            <article class="employee-admin-summary__card">
              <span>{{ t("employeeAdmin.summary.mandate") }}</span>
              <strong>{{ selectedEmployee.default_mandate_id || t("employeeAdmin.summary.none") }}</strong>
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
                  <input v-model="employeeDraft.default_branch_id" />
                </label>
                <label class="field-stack">
                  <span>{{ t("employeeAdmin.fields.defaultMandateId") }}</span>
                  <input v-model="employeeDraft.default_mandate_id" />
                </label>
                <label class="field-stack">
                  <span>{{ t("employeeAdmin.fields.hireDate") }}</span>
                  <input v-model="employeeDraft.hire_date" type="date" />
                </label>
                <label class="field-stack">
                  <span>{{ t("employeeAdmin.fields.terminationDate") }}</span>
                  <input v-model="employeeDraft.termination_date" type="date" />
                </label>
              </div>
            </section>

            <section class="employee-admin-form-section">
              <div class="employee-admin-form-section__header">
                <p class="eyebrow">{{ t("employeeAdmin.form.accessEyebrow") }}</p>
                <h4>{{ t("employeeAdmin.form.accessTitle") }}</h4>
              </div>
              <div class="employee-admin-form-grid employee-admin-form-grid--editor">
                <label class="field-stack">
                  <span>{{ t("employeeAdmin.fields.userId") }}</span>
                  <input v-model="employeeDraft.user_id" />
                </label>
              </div>
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

          <section v-if="selectedEmployee && !isCreatingEmployee" class="employee-admin-section">
            <div class="employee-admin-panel__header">
              <div>
                <p class="eyebrow">{{ t("employeeAdmin.access.eyebrow") }}</p>
                <h3>{{ t("employeeAdmin.access.title") }}</h3>
              </div>
            </div>
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
            </div>
            <div class="employee-admin-form-grid">
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
            <div class="cta-row">
              <button class="cta-button" type="button" :disabled="!actionState.canManageAccess" @click="createAccessUser">
                {{ t("employeeAdmin.actions.createAccessUser") }}
              </button>
              <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canManageAccess" @click="reconcileAccessUser">
                {{ t("employeeAdmin.actions.reconcileAccessUser") }}
              </button>
              <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canManageAccess || !accessLink?.user_id" @click="detachAccessUser">
                {{ t("employeeAdmin.actions.detachAccessUser") }}
              </button>
            </div>
            <div class="employee-admin-form-grid">
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

          <section v-if="selectedEmployee && !isCreatingEmployee" class="employee-admin-section">
            <div class="employee-admin-panel__header">
              <div>
                <p class="eyebrow">{{ t("employeeAdmin.photo.eyebrow") }}</p>
                <h3>{{ t("employeeAdmin.photo.title") }}</h3>
              </div>
            </div>

            <div class="employee-admin-photo">
              <div class="employee-admin-photo__preview">
                <img v-if="photoPreviewUrl" :src="photoPreviewUrl" :alt="t('employeeAdmin.photo.alt')" />
                <span v-else>{{ t("employeeAdmin.photo.empty") }}</span>
              </div>
              <div class="employee-admin-photo__controls">
                <p class="field-help">{{ currentPhoto?.file_name || t("employeeAdmin.photo.help") }}</p>
                <input :disabled="!actionState.canManagePhoto" type="file" accept="image/*" @change="onPhotoSelected" />
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

          <section v-if="selectedEmployee && !isCreatingEmployee" class="employee-admin-section">
            <div class="employee-admin-panel__header">
              <div>
                <p class="eyebrow">{{ t("employeeAdmin.notes.eyebrow") }}</p>
                <h3>{{ t("employeeAdmin.notes.title") }}</h3>
              </div>
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
                <div>
                  <strong>{{ note.title }}</strong>
                  <span>{{ t(`employeeAdmin.noteType.${note.note_type}` as never) }} · {{ note.reminder_at || t("employeeAdmin.summary.none") }}</span>
                </div>
                <StatusBadge :status="note.completed_at ? 'active' : note.status" />
              </button>
            </div>
            <p v-else class="employee-admin-list-empty">{{ t("employeeAdmin.notes.empty") }}</p>

            <form class="employee-admin-inline-form" @submit.prevent="submitNote">
              <div class="employee-admin-form-grid">
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
          </section>

          <section v-if="selectedEmployee && !isCreatingEmployee" class="employee-admin-section">
            <div class="employee-admin-panel__header">
              <div>
                <p class="eyebrow">{{ t("employeeAdmin.groups.eyebrow") }}</p>
                <h3>{{ t("employeeAdmin.groups.title") }}</h3>
              </div>
            </div>

            <div class="employee-admin-form-grid">
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

            <div class="employee-admin-form-grid">
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

            <div v-if="selectedEmployee?.group_memberships.length" class="employee-admin-record-list">
              <button
                v-for="membership in selectedEmployee.group_memberships"
                :key="membership.id"
                type="button"
                class="employee-admin-record"
                :class="{ selected: membership.id === editingMembershipId }"
                @click="editMembership(membership)"
              >
                <div>
                  <strong>{{ membership.group?.name || membership.group_id }}</strong>
                  <span>{{ membership.valid_from }} · {{ membership.valid_until || t("employeeAdmin.summary.none") }}</span>
                </div>
                <StatusBadge :status="membership.status" />
              </button>
            </div>
            <p v-else class="employee-admin-list-empty">{{ t("employeeAdmin.groups.empty") }}</p>
          </section>

          <section v-if="selectedEmployee && !isCreatingEmployee && canReadPrivate" class="employee-admin-section">
            <div class="employee-admin-panel__header">
              <div>
                <p class="eyebrow">{{ t("employeeAdmin.addresses.eyebrow") }}</p>
                <h3>{{ t("employeeAdmin.addresses.title") }}</h3>
              </div>
            </div>

            <div v-if="employeeAddresses.length" class="employee-admin-record-list">
              <article v-for="addressRow in employeeAddresses" :key="addressRow.id" class="employee-admin-record employee-admin-record--static">
                <div>
                  <strong>{{ addressRow.address?.street_line_1 || addressRow.address_id }}</strong>
                  <span>{{ addressRow.valid_from }} · {{ addressRow.valid_to || t("employeeAdmin.summary.none") }}</span>
                </div>
                <StatusBadge :status="addressRow.status" />
              </article>
            </div>
            <p v-else class="employee-admin-list-empty">{{ t("employeeAdmin.addresses.empty") }}</p>
          </section>

          <section v-if="selectedEmployee && !isCreatingEmployee" class="employee-admin-section">
            <div class="employee-admin-panel__header">
              <div>
                <p class="eyebrow">{{ t("employeeAdmin.documents.eyebrow") }}</p>
                <h3>{{ t("employeeAdmin.documents.title") }}</h3>
              </div>
            </div>
            <div v-if="employeeDocuments.length" class="employee-admin-record-list">
              <button
                v-for="document in employeeDocuments"
                :key="document.document_id"
                type="button"
                class="employee-admin-record"
                @click="downloadDocument(document)"
              >
                <div>
                  <strong>{{ document.title }}</strong>
                  <span>{{ document.file_name || t("employeeAdmin.summary.none") }} · {{ document.relation_type }}</span>
                </div>
                <StatusBadge :status="document.current_version_no ? 'active' : 'inactive'" />
              </button>
            </div>
            <p v-else class="employee-admin-list-empty">{{ t("employeeAdmin.documents.empty") }}</p>
          </section>
        </template>

        <section v-else class="employee-admin-empty">
          <p class="eyebrow">{{ t("employeeAdmin.detail.emptyEyebrow") }}</p>
          <h3>{{ t("employeeAdmin.detail.emptyTitle") }}</h3>
          <p>{{ t("employeeAdmin.detail.emptyBody") }}</p>
        </section>
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref } from "vue";

import {
  attachEmployeeAccessUser,
  createEmployeeAccessUser,
  createEmployee,
  createEmployeeGroup,
  createEmployeeGroupMembership,
  createEmployeeNote,
  detachEmployeeAccessUser,
  downloadEmployeeDocument,
  EmployeeAdminApiError,
  exportEmployees,
  getEmployee,
  getEmployeeAccessLink,
  getEmployeePhoto,
  importEmployeesDryRun,
  importEmployeesExecute,
  listEmployeeAddresses,
  listEmployeeDocuments,
  listEmployeeGroups,
  listEmployeeNotes,
  listEmployees,
  reconcileEmployeeAccessUser,
  updateEmployee,
  updateEmployeeGroup,
  updateEmployeeGroupMembership,
  updateEmployeeNote,
  uploadEmployeePhoto,
  type EmployeeAccessLinkRead,
    type EmployeeAddressHistoryRead,
    type EmployeeDocumentListItemRead,
    type EmployeeExportResult,
    type EmployeeGroupMembershipRead,
    type EmployeeGroupRead,
    type EmployeeImportDryRunResult,
    type EmployeeImportExecuteResult,
    type EmployeeListItem,
    type EmployeeNoteRead,
    type EmployeeOperationalRead,
  type EmployeePhotoRead,
} from "@/api/employeeAdmin";
import StatusBadge from "@/components/StatusBadge.vue";
import { useI18n } from "@/i18n";
import {
  buildEmployeeImportTemplateRows,
  deriveEmployeeActionState,
  mapEmployeeApiMessage,
  summarizeCurrentAddress,
} from "@/features/employees/employeeAdmin.helpers.js";
import { useAuthStore } from "@/stores/auth";

withDefaults(defineProps<{ embedded?: boolean }>(), {
  embedded: false,
});

const { t } = useI18n();
const authStore = useAuthStore();

const loading = reactive({
  list: false,
  detail: false,
  action: false,
});

const feedback = reactive({
  tone: "neutral",
  title: "",
  message: "",
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
  user_id: "",
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

const importDraft = reactive({
  csv_text: buildEmployeeImportTemplateRows(),
  continue_on_error: true,
});

const accessCreateDraft = reactive({
  username: "",
  email: "",
  password: "",
});

const accessAttachDraft = reactive({
  user_id: "",
  username: "",
  email: "",
});

const tenantScopeInput = ref(authStore.tenantScopeId || authStore.sessionUser?.tenant_id || "");
const employees = ref<EmployeeListItem[]>([]);
const selectedEmployeeId = ref("");
const selectedEmployee = ref<EmployeeOperationalRead | null>(null);
const employeeAddresses = ref<EmployeeAddressHistoryRead[]>([]);
const employeeNotes = ref<EmployeeNoteRead[]>([]);
const employeeGroups = ref<EmployeeGroupRead[]>([]);
const employeeDocuments = ref<EmployeeDocumentListItemRead[]>([]);
const currentPhoto = ref<EmployeePhotoRead | null>(null);
const accessLink = ref<EmployeeAccessLinkRead | null>(null);
const importDryRunResult = ref<EmployeeImportDryRunResult | null>(null);
const lastImportResult = ref<EmployeeImportExecuteResult | null>(null);
const lastExportResult = ref<EmployeeExportResult | null>(null);
const photoPreviewUrl = ref("");
const pendingPhotoFile = ref<File | null>(null);
const pendingImportFile = ref<File | null>(null);
const isCreatingEmployee = ref(false);
const editingNoteId = ref("");
const editingGroupId = ref("");
const editingMembershipId = ref("");

const effectiveRole = computed(() => authStore.effectiveRole);
const isPlatformAdmin = computed(() => effectiveRole.value === "platform_admin");
const actionState = computed(() => deriveEmployeeActionState(effectiveRole.value, selectedEmployee.value));
const canRead = computed(() => actionState.value.canRead);
const canWrite = computed(() => actionState.value.canWrite);
const canReadPrivate = computed(() => actionState.value.canReadPrivate);
const resolvedTenantScopeId = computed(() =>
  isPlatformAdmin.value ? authStore.tenantScopeId : (authStore.sessionUser?.tenant_id ?? authStore.tenantScopeId),
);
const selectedEmployeeLabel = computed(() =>
  selectedEmployee.value
    ? `${selectedEmployee.value.personnel_no} · ${selectedEmployee.value.first_name} ${selectedEmployee.value.last_name}`
    : t("employeeAdmin.detail.emptyTitle"),
);
const currentAddressSummary = computed(() => summarizeCurrentAddress(employeeAddresses.value));

function setFeedback(tone: "error" | "neutral" | "success", title: string, message: string) {
  feedback.tone = tone;
  feedback.title = title;
  feedback.message = message;
}

function clearFeedback() {
  feedback.tone = "neutral";
  feedback.title = "";
  feedback.message = "";
}

function rememberScope() {
  authStore.setTenantScopeId(tenantScopeInput.value);
  void refreshEmployees();
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
  employeeDraft.user_id = "";
  employeeDraft.notes = "";
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
  employeeDraft.user_id = employee.user_id || "";
  employeeDraft.notes = employee.notes || "";
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

function resetAccessDrafts() {
  accessCreateDraft.username = "";
  accessCreateDraft.email = "";
  accessCreateDraft.password = "";
  accessAttachDraft.user_id = "";
  accessAttachDraft.username = "";
  accessAttachDraft.email = "";
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
  selectedEmployeeId.value = "";
  selectedEmployee.value = null;
  employeeAddresses.value = [];
  employeeNotes.value = [];
  employeeDocuments.value = [];
  currentPhoto.value = null;
  accessLink.value = null;
  clearPhotoPreview();
  resetEmployeeDraft();
  resetNoteDraft();
  resetMembershipDraft();
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
    employees.value = [];
    selectedEmployee.value = null;
    return;
  }

  loading.list = true;
  try {
    employees.value = await listEmployees(resolvedTenantScopeId.value, authStore.accessToken, filters);
    await listSupplementalGroups();
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
  } finally {
    loading.list = false;
  }
}

async function listSupplementalGroups() {
  if (!resolvedTenantScopeId.value || !authStore.accessToken || !canRead.value) {
    employeeGroups.value = [];
    return;
  }
  employeeGroups.value = await listEmployeeGroups(resolvedTenantScopeId.value, authStore.accessToken);
}

async function selectEmployee(employeeId: string) {
  if (!resolvedTenantScopeId.value || !authStore.accessToken) {
    return;
  }
  isCreatingEmployee.value = false;
  selectedEmployeeId.value = employeeId;
  loading.detail = true;
  try {
    const [employee, notes, documents, photo] = await Promise.all([
      getEmployee(resolvedTenantScopeId.value, employeeId, authStore.accessToken),
      listEmployeeNotes(resolvedTenantScopeId.value, employeeId, authStore.accessToken),
      listEmployeeDocuments(resolvedTenantScopeId.value, employeeId, authStore.accessToken),
      getEmployeePhoto(resolvedTenantScopeId.value, employeeId, authStore.accessToken),
    ]);
    selectedEmployee.value = employee;
    employeeNotes.value = notes;
    employeeDocuments.value = documents;
    currentPhoto.value = photo;
    accessLink.value = actionState.value.canManageAccess
      ? await getEmployeeAccessLink(resolvedTenantScopeId.value, employeeId, authStore.accessToken)
      : null;
    syncEmployeeDraft(employee);
    resetNoteDraft();
    resetMembershipDraft();
    resetAccessDrafts();
    if (canReadPrivate.value) {
      employeeAddresses.value = await listEmployeeAddresses(resolvedTenantScopeId.value, employeeId, authStore.accessToken);
    } else {
      employeeAddresses.value = [];
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
    const payload = {
      tenant_id: resolvedTenantScopeId.value,
      personnel_no: employeeDraft.personnel_no.trim(),
      first_name: employeeDraft.first_name.trim(),
      last_name: employeeDraft.last_name.trim(),
      preferred_name: emptyToNull(employeeDraft.preferred_name),
      work_email: emptyToNull(employeeDraft.work_email),
      work_phone: emptyToNull(employeeDraft.work_phone),
      mobile_phone: emptyToNull(employeeDraft.mobile_phone),
      default_branch_id: emptyToNull(employeeDraft.default_branch_id),
      default_mandate_id: emptyToNull(employeeDraft.default_mandate_id),
      hire_date: emptyToNull(employeeDraft.hire_date),
      termination_date: emptyToNull(employeeDraft.termination_date),
      user_id: emptyToNull(employeeDraft.user_id),
      notes: emptyToNull(employeeDraft.notes),
    };
    const employee = isCreatingEmployee.value
      ? await createEmployee(resolvedTenantScopeId.value, authStore.accessToken, payload)
      : await updateEmployee(resolvedTenantScopeId.value, selectedEmployeeId.value, authStore.accessToken, {
          ...payload,
          version_no: selectedEmployee.value?.version_no,
        });
    setFeedback("success", t("employeeAdmin.feedback.titleSuccess"), t("employeeAdmin.feedback.employeeSaved"));
    await refreshEmployees();
    await selectEmployee(employee.id);
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
    await selectEmployee(selectedEmployeeId.value);
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
    await selectEmployee(selectedEmployeeId.value);
    setFeedback("success", t("employeeAdmin.feedback.titleSuccess"), t("employeeAdmin.feedback.membershipSaved"));
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

function onImportSelected(event: Event) {
  const target = event.target as HTMLInputElement;
  pendingImportFile.value = target.files?.[0] ?? null;
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
    await selectEmployee(selectedEmployeeId.value);
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
    await selectEmployee(selectedEmployeeId.value);
    setFeedback("success", t("employeeAdmin.feedback.titleSuccess"), t("employeeAdmin.feedback.accessLinked"));
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
    await selectEmployee(selectedEmployeeId.value);
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
    await selectEmployee(selectedEmployeeId.value);
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
    await selectEmployee(selectedEmployeeId.value);
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
  if (authStore.accessToken && !authStore.sessionUser) {
    try {
      await authStore.loadCurrentSession();
    } catch {
      // handled by store
    }
  }
  if (!isPlatformAdmin.value) {
    tenantScopeInput.value = authStore.sessionUser?.tenant_id ?? authStore.tenantScopeId;
  }
  resetEmployeeDraft();
  await refreshEmployees();
});

onBeforeUnmount(() => {
  clearPhotoPreview();
});
</script>

<style scoped>
.employee-admin-page,
.employee-admin-grid,
.employee-admin-list,
.employee-admin-form-grid,
.employee-admin-record-list {
  display: grid;
  gap: 1rem;
  min-width: 0;
}

.employee-admin-grid {
  grid-template-columns: minmax(320px, 0.9fr) minmax(420px, 1.3fr);
  align-items: start;
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
.employee-admin-photo,
.employee-admin-photo__controls {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
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
  gap: 0.75rem;
  align-items: center;
  min-width: 0;
  border: 0;
  text-align: left;
  cursor: pointer;
}

.employee-admin-row.selected,
.employee-admin-record.selected {
  outline: 2px solid var(--sp-color-primary);
}

.employee-admin-record--static {
  cursor: default;
}

.employee-admin-panel__header {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 1rem;
  align-items: start;
  min-width: 0;
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
}

@media (max-width: 820px) {
  .employee-admin-form-grid--editor,
  .employee-admin-form-actions {
    grid-template-columns: 1fr;
  }
}
</style>
