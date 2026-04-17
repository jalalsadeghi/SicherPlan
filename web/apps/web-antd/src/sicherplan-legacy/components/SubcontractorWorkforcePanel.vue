<template>
  <section class="subcontractor-workforce">
    <div class="subcontractor-admin-panel__header">
      <div>
        <p class="eyebrow">{{ t("sicherplan.subcontractors.workforce.eyebrow") }}</p>
        <h3>{{ t("sicherplan.subcontractors.workforce.title") }}</h3>
        <p class="field-help">{{ t("sicherplan.subcontractors.workforce.lead") }}</p>
      </div>
      <StatusBadge :status="loading.list ? 'inactive' : 'active'" />
    </div>

    <section v-if="feedback.message" class="subcontractor-admin-feedback" :data-tone="feedback.tone">
      <div>
        <strong>{{ feedback.title }}</strong>
        <span>{{ feedback.message }}</span>
      </div>
      <button type="button" @click="clearFeedback">{{ t("sicherplan.subcontractors.actions.clearFeedback") }}</button>
    </section>

    <div class="subcontractor-workforce-grid">
      <section class="module-card subcontractor-admin-panel">
        <div class="subcontractor-admin-form-grid">
          <label class="field-stack">
            <span>{{ t("sicherplan.subcontractors.workforce.filters.search") }}</span>
            <input v-model="workerFilters.search" :placeholder="t('sicherplan.subcontractors.workforce.filters.searchPlaceholder')" />
          </label>
          <label class="field-stack">
            <span>{{ t("sicherplan.subcontractors.workforce.filters.status") }}</span>
            <select v-model="workerFilters.status">
              <option value="">{{ t("sicherplan.subcontractors.workforce.filters.allStatuses") }}</option>
              <option value="active">{{ t("sicherplan.subcontractors.status.active") }}</option>
              <option value="inactive">{{ t("sicherplan.subcontractors.status.inactive") }}</option>
              <option value="archived">{{ t("sicherplan.subcontractors.status.archived") }}</option>
            </select>
          </label>
          <label class="field-stack">
            <span>{{ t("sicherplan.subcontractors.workforce.filters.readinessStatus") }}</span>
            <select v-model="workerFilters.readiness_status">
              <option value="">{{ t("sicherplan.subcontractors.workforce.filters.allReadinessStatuses") }}</option>
              <option value="ready">{{ t("sicherplan.subcontractors.workforce.readiness.status.ready") }}</option>
              <option value="ready_with_warnings">{{ t("sicherplan.subcontractors.workforce.readiness.status.readyWithWarnings") }}</option>
              <option value="not_ready">{{ t("sicherplan.subcontractors.workforce.readiness.status.notReady") }}</option>
            </select>
          </label>
        </div>

        <label class="subcontractor-admin-checkbox">
          <input v-model="workerFilters.include_archived" type="checkbox" />
          <span>{{ t("sicherplan.subcontractors.workforce.filters.includeArchived") }}</span>
        </label>

        <div class="cta-row">
          <button class="cta-button" type="button" :disabled="!canRead" @click="refreshWorkers">
            {{ t("sicherplan.subcontractors.actions.search") }}
          </button>
          <button class="cta-button cta-secondary" type="button" :disabled="!canWrite" @click="startCreateWorker">
            {{ t("sicherplan.subcontractors.workforce.actions.newWorker") }}
          </button>
          <button class="cta-button cta-secondary" type="button" :disabled="!canRead" @click="runExport">
            {{ t("sicherplan.subcontractors.workforce.actions.exportWorkers") }}
          </button>
        </div>

        <section class="subcontractor-admin-section">
          <div class="subcontractor-admin-panel__header">
            <div>
              <p class="eyebrow">{{ t("sicherplan.subcontractors.workforce.import.eyebrow") }}</p>
              <h3>{{ t("sicherplan.subcontractors.workforce.import.title") }}</h3>
            </div>
          </div>
          <input type="file" accept=".csv,text/csv" :disabled="!canWrite" @change="onImportSelected" />
          <div class="cta-row">
            <button class="cta-button cta-secondary" type="button" :disabled="!pendingImportFile || !canWrite" @click="loadImportFile">
              {{ t("sicherplan.subcontractors.workforce.actions.loadImportFile") }}
            </button>
            <button class="cta-button cta-secondary" type="button" :disabled="!canWrite" @click="downloadTemplate">
              {{ t("sicherplan.subcontractors.workforce.actions.downloadTemplate") }}
            </button>
          </div>
          <label class="field-stack">
            <span>{{ t("sicherplan.subcontractors.workforce.import.csvLabel") }}</span>
            <textarea v-model="importDraft.csv_text" rows="7" :disabled="!canWrite" />
          </label>
          <label class="subcontractor-admin-checkbox">
            <input v-model="importDraft.continue_on_error" type="checkbox" :disabled="!canWrite" />
            <span>{{ t("sicherplan.subcontractors.workforce.import.continueOnError") }}</span>
          </label>
          <div class="cta-row">
            <button class="cta-button" type="button" :disabled="!canWrite" @click="runImportDryRun">
              {{ t("sicherplan.subcontractors.workforce.actions.importDryRun") }}
            </button>
            <button class="cta-button cta-secondary" type="button" :disabled="!canWrite" @click="runImportExecute">
              {{ t("sicherplan.subcontractors.workforce.actions.importExecute") }}
            </button>
          </div>
          <p v-if="importDryRunResult" class="field-help">
            {{
              t("sicherplan.subcontractors.workforce.import.dryRunSummary", {
                total: importDryRunResult.total_rows,
                invalid: importDryRunResult.invalid_rows,
              })
            }}
          </p>
          <p v-if="lastImportResult" class="field-help">
            {{
              t("sicherplan.subcontractors.workforce.import.executeSummary", {
                total: lastImportResult.total_rows,
                created: lastImportResult.created_workers,
                updated: lastImportResult.updated_workers,
              })
            }}
          </p>
          <p v-if="lastExportResult" class="field-help">
            {{
              t("sicherplan.subcontractors.workforce.import.exportSummary", {
                rows: lastExportResult.row_count,
                documentId: lastExportResult.document_id,
              })
            }}
          </p>
          <div v-if="importRows.length" class="subcontractor-workforce-import-results">
            <article v-for="row in importRows" :key="`row-${row.row_no}`" class="subcontractor-workforce-import-results__row">
              <strong>#{{ row.row_no }} · {{ row.worker_no || "?" }}</strong>
              <span>{{ row.status }}</span>
              <span>{{ row.messages.map(mapImportMessage).map((key) => t(key as never)).join(" · ") }}</span>
            </article>
          </div>
        </section>

        <section class="subcontractor-admin-section">
          <div class="subcontractor-admin-panel__header">
            <div>
              <p class="eyebrow">{{ t("sicherplan.subcontractors.workforce.readiness.eyebrow") }}</p>
              <h3>{{ t("sicherplan.subcontractors.workforce.readiness.title") }}</h3>
            </div>
          </div>
          <div class="subcontractor-admin-summary">
            <article class="subcontractor-admin-summary__card">
              <span>{{ t("sicherplan.subcontractors.workforce.readiness.summary.ready") }}</span>
              <strong>{{ readinessSummary?.ready_workers ?? 0 }}</strong>
            </article>
            <article class="subcontractor-admin-summary__card">
              <span>{{ t("sicherplan.subcontractors.workforce.readiness.summary.warningOnly") }}</span>
              <strong>{{ readinessSummary?.warning_only_workers ?? 0 }}</strong>
            </article>
            <article class="subcontractor-admin-summary__card">
              <span>{{ t("sicherplan.subcontractors.workforce.readiness.summary.notReady") }}</span>
              <strong>{{ readinessSummary?.not_ready_workers ?? 0 }}</strong>
            </article>
            <article class="subcontractor-admin-summary__card">
              <span>{{ t("sicherplan.subcontractors.workforce.readiness.summary.missingProofs") }}</span>
              <strong>{{ readinessSummary?.missing_proof_workers ?? 0 }}</strong>
            </article>
          </div>
        </section>

        <div v-if="workers.length" class="subcontractor-admin-list">
          <button
            v-for="worker in workers"
            :key="worker.id"
            type="button"
            class="subcontractor-admin-row"
            :class="{ selected: worker.id === selectedWorkerId }"
            @click="selectWorker(worker.id)"
          >
            <div>
              <strong>{{ worker.worker_no }} · {{ worker.first_name }} {{ worker.last_name }}</strong>
              <span>{{ worker.email || worker.mobile || t("sicherplan.subcontractors.summary.none") }}</span>
            </div>
            <div class="subcontractor-workforce-row-status">
              <StatusBadge :status="worker.status" />
              <span class="subcontractor-workforce-readiness-pill" :data-readiness="workerReadinessMap[worker.id]?.readiness_status ?? 'ready'">
                {{ mapReadinessStatusLabel(workerReadinessMap[worker.id]?.readiness_status) }}
              </span>
            </div>
          </button>
        </div>
        <p v-else class="subcontractor-admin-list-empty">{{ t("sicherplan.subcontractors.workforce.empty") }}</p>
      </section>

      <section class="module-card subcontractor-admin-panel subcontractor-admin-detail">
        <div class="subcontractor-admin-panel__header">
          <div>
            <p class="eyebrow">{{ t("sicherplan.subcontractors.workforce.detailEyebrow") }}</p>
            <h3>
              {{
                isCreatingWorker
                  ? t("sicherplan.subcontractors.workforce.newTitle")
                  : selectedWorkerLabel
              }}
            </h3>
          </div>
          <StatusBadge v-if="selectedWorker && !isCreatingWorker" :status="selectedWorker.status" />
        </div>

        <template v-if="isCreatingWorker || selectedWorker">
          <div v-if="selectedWorker && !isCreatingWorker" class="subcontractor-admin-summary">
            <article class="subcontractor-admin-summary__card">
              <span>{{ t("sicherplan.subcontractors.workforce.summary.qualifications") }}</span>
              <strong>{{ selectedWorkerReadiness?.qualification_count ?? 0 }}</strong>
            </article>
            <article class="subcontractor-admin-summary__card">
              <span>{{ t("sicherplan.subcontractors.workforce.summary.credentials") }}</span>
              <strong>{{ selectedWorkerReadiness?.credential_count ?? 0 }}</strong>
            </article>
            <article class="subcontractor-admin-summary__card">
              <span>{{ t("sicherplan.subcontractors.workforce.summary.expiredQualifications") }}</span>
              <strong>{{ selectedWorkerReadiness?.expired_qualification_count ?? 0 }}</strong>
            </article>
            <article class="subcontractor-admin-summary__card">
              <span>{{ t("sicherplan.subcontractors.workforce.readiness.title") }}</span>
              <strong>{{ mapReadinessStatusLabel(selectedWorkerReadiness?.readiness_status) }}</strong>
            </article>
          </div>

          <section v-if="selectedWorker && !isCreatingWorker" class="subcontractor-admin-section">
            <div class="subcontractor-admin-panel__header">
              <div>
                <p class="eyebrow">{{ t("sicherplan.subcontractors.workforce.readiness.eyebrow") }}</p>
                <h3>{{ t("sicherplan.subcontractors.workforce.readiness.detailTitle") }}</h3>
              </div>
            </div>
            <p class="field-help">
              {{
                t("sicherplan.subcontractors.workforce.readiness.checkedAt", {
                  checkedAt: selectedWorkerReadiness?.checked_at || t("sicherplan.subcontractors.summary.none"),
                })
              }}
            </p>
            <div v-if="selectedWorkerReadiness" class="subcontractor-workforce-readiness-overview">
              <span class="subcontractor-workforce-readiness-pill" :data-readiness="selectedWorkerReadiness.readiness_status">
                {{ mapReadinessStatusLabel(selectedWorkerReadiness.readiness_status) }}
              </span>
              <span class="field-help">
                {{
                  t("sicherplan.subcontractors.workforce.readiness.issueSummary", {
                    blocking: selectedWorkerReadiness.blocking_issue_count,
                    warning: selectedWorkerReadiness.warning_issue_count,
                  })
                }}
              </span>
            </div>
            <div v-if="selectedWorkerReadiness?.issues.length" class="subcontractor-workforce-readiness-issues">
              <article
                v-for="issue in selectedWorkerReadiness.issues"
                :key="`${issue.issue_code}-${issue.reference_id || 'global'}`"
                class="subcontractor-workforce-readiness-issue"
                :data-severity="issue.severity"
              >
                <strong>{{ t(issue.message_key as never) }}</strong>
                <span>{{ issue.title }}</span>
                <span v-if="issue.due_on" class="field-help">
                  {{ t("sicherplan.subcontractors.workforce.readiness.dueOn", { dueOn: issue.due_on }) }}
                </span>
              </article>
            </div>
            <p v-else class="subcontractor-admin-list-empty">{{ t("sicherplan.subcontractors.workforce.readiness.noIssues") }}</p>
          </section>

          <div v-if="selectedWorker && !isCreatingWorker" class="subcontractor-admin-lifecycle">
            <div>
              <strong>{{ t("sicherplan.subcontractors.workforce.lifecycle.title") }}</strong>
              <p class="field-help">{{ t("sicherplan.subcontractors.workforce.lifecycle.help") }}</p>
            </div>
            <div class="cta-row">
              <button
                v-if="selectedWorker.archived_at == null && selectedWorker.status !== 'archived'"
                class="cta-button cta-secondary"
                type="button"
                :disabled="!canWrite"
                @click="archiveWorker"
              >
                {{ t("sicherplan.subcontractors.actions.archive") }}
              </button>
              <button
                v-else
                class="cta-button"
                type="button"
                :disabled="!canWrite"
                @click="reactivateWorker"
              >
                {{ t("sicherplan.subcontractors.actions.reactivate") }}
              </button>
            </div>
          </div>

          <form class="subcontractor-admin-form" @submit.prevent="submitWorker">
            <div class="subcontractor-admin-form-grid">
              <label class="field-stack">
                <span>{{ t("sicherplan.subcontractors.workforce.fields.workerNo") }}</span>
                <input v-model="workerDraft.worker_no" required />
              </label>
              <label class="field-stack">
                <span>{{ t("sicherplan.subcontractors.workforce.fields.firstName") }}</span>
                <input v-model="workerDraft.first_name" required />
              </label>
              <label class="field-stack">
                <span>{{ t("sicherplan.subcontractors.workforce.fields.lastName") }}</span>
                <input v-model="workerDraft.last_name" required />
              </label>
              <label class="field-stack">
                <span>{{ t("sicherplan.subcontractors.workforce.fields.preferredName") }}</span>
                <input v-model="workerDraft.preferred_name" />
              </label>
              <label class="field-stack">
                <span>{{ t("sicherplan.subcontractors.workforce.fields.birthDate") }}</span>
                <input v-model="workerDraft.birth_date" type="date" />
              </label>
              <label class="field-stack">
                <span>{{ t("sicherplan.subcontractors.workforce.fields.email") }}</span>
                <input v-model="workerDraft.email" type="email" />
              </label>
              <label class="field-stack">
                <span>{{ t("sicherplan.subcontractors.workforce.fields.phone") }}</span>
                <input v-model="workerDraft.phone" />
              </label>
              <label class="field-stack">
                <span>{{ t("sicherplan.subcontractors.workforce.fields.mobile") }}</span>
                <input v-model="workerDraft.mobile" />
              </label>
              <label class="field-stack">
                <span>{{ t("sicherplan.subcontractors.workforce.fields.status") }}</span>
                <select v-model="workerDraft.status">
                  <option value="active">{{ t("sicherplan.subcontractors.status.active") }}</option>
                  <option value="inactive">{{ t("sicherplan.subcontractors.status.inactive") }}</option>
                  <option value="archived">{{ t("sicherplan.subcontractors.status.archived") }}</option>
                </select>
              </label>
              <label class="field-stack field-stack--wide">
                <span>{{ t("sicherplan.subcontractors.workforce.fields.notes") }}</span>
                <textarea v-model="workerDraft.notes" rows="4" />
              </label>
            </div>
            <div class="cta-row">
              <button class="cta-button" type="submit" :disabled="!canWrite">
                {{ isCreatingWorker ? t("sicherplan.subcontractors.workforce.actions.createWorker") : t("sicherplan.subcontractors.workforce.actions.saveWorker") }}
              </button>
              <button class="cta-button cta-secondary" type="button" @click="resetWorkerDraft">
                {{ t("sicherplan.subcontractors.actions.reset") }}
              </button>
            </div>
          </form>

          <section v-if="selectedWorker && !isCreatingWorker" class="subcontractor-admin-section">
            <div class="subcontractor-admin-panel__header">
              <div>
                <p class="eyebrow">{{ t("sicherplan.subcontractors.workforce.qualifications.eyebrow") }}</p>
                <h3>{{ t("sicherplan.subcontractors.workforce.qualifications.title") }}</h3>
              </div>
            </div>
            <div v-if="selectedWorker.qualifications.length" class="subcontractor-admin-list">
              <button
                v-for="qualification in selectedWorker.qualifications"
                :key="qualification.id"
                type="button"
                class="subcontractor-admin-row"
                :class="{ selected: qualification.id === selectedQualificationId }"
                @click="selectQualification(qualification.id)"
              >
                <div>
                  <strong>{{ qualification.qualification_type_label || qualification.qualification_type_id }}</strong>
                  <span>{{ qualification.valid_until || t("sicherplan.subcontractors.summary.none") }}</span>
                </div>
                <StatusBadge :status="qualification.status" />
              </button>
            </div>
            <p v-else class="subcontractor-admin-list-empty">{{ t("sicherplan.subcontractors.workforce.qualifications.empty") }}</p>

            <form class="subcontractor-admin-form" @submit.prevent="submitQualification">
              <div class="subcontractor-admin-form-grid">
                <label class="field-stack">
                  <span>{{ t("sicherplan.subcontractors.workforce.fields.qualificationTypeId") }}</span>
                  <select v-if="qualificationTypeOptions.length" v-model="qualificationDraft.qualification_type_id" required>
                    <option value="">{{ t("sicherplan.subcontractors.workforce.fields.qualificationTypePlaceholder") }}</option>
                    <option v-for="option in qualificationTypeOptionsWithDraft" :key="option.id" :value="option.id">{{ option.label }}</option>
                  </select>
                  <input v-else v-model="qualificationDraft.qualification_type_id" required />
                </label>
                <label class="field-stack">
                  <span>{{ t("sicherplan.subcontractors.workforce.fields.certificateNo") }}</span>
                  <input v-model="qualificationDraft.certificate_no" />
                </label>
                <label class="field-stack">
                  <span>{{ t("sicherplan.subcontractors.workforce.fields.issuedAt") }}</span>
                  <input v-model="qualificationDraft.issued_at" type="date" />
                </label>
                <label class="field-stack">
                  <span>{{ t("sicherplan.subcontractors.workforce.fields.validUntil") }}</span>
                  <input v-model="qualificationDraft.valid_until" type="date" />
                </label>
                <label class="field-stack">
                  <span>{{ t("sicherplan.subcontractors.workforce.fields.issuingAuthority") }}</span>
                  <input v-model="qualificationDraft.issuing_authority" />
                </label>
                <label class="field-stack">
                  <span>{{ t("sicherplan.subcontractors.workforce.fields.status") }}</span>
                  <select v-model="qualificationDraft.status">
                    <option value="active">{{ t("sicherplan.subcontractors.status.active") }}</option>
                    <option value="inactive">{{ t("sicherplan.subcontractors.status.inactive") }}</option>
                    <option value="archived">{{ t("sicherplan.subcontractors.status.archived") }}</option>
                  </select>
                </label>
                <label class="field-stack field-stack--wide">
                  <span>{{ t("sicherplan.subcontractors.workforce.fields.notes") }}</span>
                  <textarea v-model="qualificationDraft.notes" rows="3" />
                </label>
              </div>
              <div class="cta-row">
                <button class="cta-button" type="submit" :disabled="!canWrite">
                  {{
                    selectedQualificationId
                      ? t("sicherplan.subcontractors.workforce.actions.saveQualification")
                      : t("sicherplan.subcontractors.workforce.actions.createQualification")
                  }}
                </button>
                <button class="cta-button cta-secondary" type="button" @click="resetQualificationDraft">
                  {{ t("sicherplan.subcontractors.actions.reset") }}
                </button>
              </div>
            </form>

            <div v-if="selectedQualification" class="subcontractor-workforce-proof-block">
              <strong>{{ t("sicherplan.subcontractors.workforce.proofs.title") }}</strong>
              <div v-if="selectedQualification.proofs.length" class="subcontractor-workforce-proof-list">
                <button
                  v-for="proof in selectedQualification.proofs"
                  :key="proof.document_id"
                  type="button"
                  class="subcontractor-admin-row"
                  @click="downloadProof(proof)"
                >
                  <div>
                    <strong>{{ proof.title }}</strong>
                    <span>{{ proof.file_name || proof.document_id }}</span>
                  </div>
                </button>
              </div>
              <p v-else class="subcontractor-admin-list-empty">{{ t("sicherplan.subcontractors.workforce.proofs.empty") }}</p>
              <input type="file" :disabled="!canWrite" @change="onProofSelected" />
              <div class="cta-row">
                <button class="cta-button cta-secondary" type="button" :disabled="!pendingProofFile || !canWrite" @click="uploadProof">
                  {{ t("sicherplan.subcontractors.workforce.actions.uploadProof") }}
                </button>
              </div>
              <div class="subcontractor-admin-form-grid">
                <label class="field-stack">
                  <span>{{ t("sicherplan.subcontractors.workforce.fields.linkDocumentId") }}</span>
                  <input v-model="proofLinkDraft.document_id" :disabled="!canWrite" />
                </label>
                <label class="field-stack">
                  <span>{{ t("sicherplan.subcontractors.workforce.fields.linkLabel") }}</span>
                  <input v-model="proofLinkDraft.label" :disabled="!canWrite" />
                </label>
              </div>
              <div class="cta-row">
                <button class="cta-button cta-secondary" type="button" :disabled="!canWrite" @click="linkProof">
                  {{ t("sicherplan.subcontractors.workforce.actions.linkProof") }}
                </button>
              </div>
            </div>
          </section>

          <section v-if="selectedWorker && !isCreatingWorker" class="subcontractor-admin-section">
            <div class="subcontractor-admin-panel__header">
              <div>
                <p class="eyebrow">{{ t("sicherplan.subcontractors.workforce.credentials.eyebrow") }}</p>
                <h3>{{ t("sicherplan.subcontractors.workforce.credentials.title") }}</h3>
              </div>
            </div>
            <div v-if="selectedWorker.credentials.length" class="subcontractor-admin-list">
              <button
                v-for="credential in selectedWorker.credentials"
                :key="credential.id"
                type="button"
                class="subcontractor-admin-row"
                :class="{ selected: credential.id === selectedCredentialId }"
                @click="selectCredential(credential.id)"
              >
                <div>
                  <strong>{{ credential.credential_no }} · {{ credential.credential_type }}</strong>
                  <span>{{ credential.valid_until || t("sicherplan.subcontractors.summary.none") }}</span>
                </div>
                <StatusBadge :status="credential.status" />
              </button>
            </div>
            <p v-else class="subcontractor-admin-list-empty">{{ t("sicherplan.subcontractors.workforce.credentials.empty") }}</p>

            <form class="subcontractor-admin-form" @submit.prevent="submitCredential">
              <div class="subcontractor-admin-form-grid">
                <label class="field-stack">
                  <span>{{ t("sicherplan.subcontractors.workforce.fields.credentialNo") }}</span>
                  <input v-model="credentialDraft.credential_no" required />
                </label>
                <label class="field-stack">
                  <span>{{ t("sicherplan.subcontractors.workforce.fields.credentialType") }}</span>
                  <select v-model="credentialDraft.credential_type" required>
                    <option value="">{{ t("sicherplan.subcontractors.workforce.fields.credentialTypePlaceholder") }}</option>
                    <option v-for="option in credentialTypeOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
                  </select>
                </label>
                <label class="field-stack">
                  <span>{{ t("sicherplan.subcontractors.workforce.fields.encodedValue") }}</span>
                  <input v-model="credentialDraft.encoded_value" required />
                </label>
                <label class="field-stack">
                  <span>{{ t("sicherplan.subcontractors.workforce.fields.validFrom") }}</span>
                  <input v-model="credentialDraft.valid_from" type="date" />
                </label>
                <label class="field-stack">
                  <span>{{ t("sicherplan.subcontractors.workforce.fields.validUntil") }}</span>
                  <input v-model="credentialDraft.valid_until" type="date" />
                </label>
                <label class="field-stack">
                  <span>{{ t("sicherplan.subcontractors.workforce.fields.status") }}</span>
                  <select v-model="credentialDraft.status">
                    <option value="active">{{ t("sicherplan.subcontractors.status.active") }}</option>
                    <option value="inactive">{{ t("sicherplan.subcontractors.status.inactive") }}</option>
                    <option value="archived">{{ t("sicherplan.subcontractors.status.archived") }}</option>
                  </select>
                </label>
                <label class="field-stack field-stack--wide">
                  <span>{{ t("sicherplan.subcontractors.workforce.fields.notes") }}</span>
                  <textarea v-model="credentialDraft.notes" rows="3" />
                </label>
              </div>
              <div class="cta-row">
                <button class="cta-button" type="submit" :disabled="!canWrite">
                  {{
                    selectedCredentialId
                      ? t("sicherplan.subcontractors.workforce.actions.saveCredential")
                      : t("sicherplan.subcontractors.workforce.actions.createCredential")
                  }}
                </button>
                <button class="cta-button cta-secondary" type="button" @click="resetCredentialDraft">
                  {{ t("sicherplan.subcontractors.actions.reset") }}
                </button>
              </div>
            </form>
          </section>
        </template>

        <section v-else class="subcontractor-admin-empty">
          <p class="eyebrow">{{ t("sicherplan.subcontractors.workforce.detailEyebrow") }}</p>
          <h3>{{ t("sicherplan.subcontractors.workforce.emptyDetail") }}</h3>
        </section>
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";

import { useI18n } from "@vben/locales";

import StatusBadge from "@/components/StatusBadge.vue";
import { listQualificationTypes, type QualificationTypeRead } from "@/api/employeeAdmin";
import {
  createSubcontractorWorker,
  createSubcontractorWorkerCredential,
  createSubcontractorWorkerQualification,
  downloadSubcontractorDocument,
  exportSubcontractorWorkers,
  getSubcontractorWorker,
  getSubcontractorWorkerReadiness,
  getSubcontractorWorkerReadinessSummary,
  importSubcontractorWorkersDryRun,
  importSubcontractorWorkersExecute,
  linkSubcontractorQualificationProof,
  listSubcontractorWorkerReadiness,
  listSubcontractorWorkers,
  type SubcontractorWorkerCredentialRead,
  SubcontractorAdminApiError,
  type SubcontractorWorkerExportResult,
  type SubcontractorWorkerImportDryRunResult,
  type SubcontractorWorkerImportExecuteResult,
  type SubcontractorWorkerListItem,
  type SubcontractorWorkerQualificationProofRead,
  type SubcontractorWorkerQualificationRead,
  type SubcontractorWorkerRead,
  type SubcontractorWorkerReadinessListItem,
  type SubcontractorWorkerReadinessRead,
  type SubcontractorWorkforceReadinessSummaryRead,
  updateSubcontractorWorker,
  updateSubcontractorWorkerCredential,
  updateSubcontractorWorkerQualification,
  uploadSubcontractorQualificationProof,
} from "@/api/subcontractors";
import { EMPLOYEE_CREDENTIAL_TYPE_OPTIONS } from "@/features/employees/employeeAdmin.helpers.js";
import {
  buildSubcontractorWorkerImportTemplateRows,
  mapSubcontractorApiMessage,
  mapSubcontractorImportRowMessage,
} from "@/features/subcontractors/subcontractorAdmin.helpers.js";

const props = defineProps<{
  tenantId: string;
  subcontractorId: string;
  accessToken: string;
  canRead: boolean;
  canWrite: boolean;
}>();

const { t } = useI18n();

const feedback = reactive({
  tone: "neutral",
  title: "",
  message: "",
});

const loading = reactive({
  list: false,
  detail: false,
  action: false,
});

const workerFilters = reactive({
  search: "",
  status: "",
  readiness_status: "",
  include_archived: false,
});

const importDraft = reactive({
  csv_text: buildSubcontractorWorkerImportTemplateRows(),
  continue_on_error: true,
});

const workerDraft = reactive({
  worker_no: "",
  first_name: "",
  last_name: "",
  preferred_name: "",
  birth_date: "",
  email: "",
  phone: "",
  mobile: "",
  status: "active",
  notes: "",
  version_no: 0,
});

const qualificationDraft = reactive({
  qualification_type_id: "",
  certificate_no: "",
  issued_at: "",
  valid_until: "",
  issuing_authority: "",
  status: "active",
  notes: "",
  version_no: 0,
});

const credentialDraft = reactive({
  credential_no: "",
  credential_type: "",
  encoded_value: "",
  valid_from: "",
  valid_until: "",
  status: "active",
  notes: "",
  version_no: 0,
});

const proofLinkDraft = reactive({
  document_id: "",
  label: "",
});

const workers = ref<SubcontractorWorkerListItem[]>([]);
const workerReadinessItems = ref<SubcontractorWorkerReadinessListItem[]>([]);
const readinessSummary = ref<SubcontractorWorkforceReadinessSummaryRead | null>(null);
const qualificationTypes = ref<QualificationTypeRead[]>([]);
const selectedWorker = ref<SubcontractorWorkerRead | null>(null);
const selectedWorkerReadiness = ref<SubcontractorWorkerReadinessRead | null>(null);
const selectedWorkerId = ref("");
const selectedQualificationId = ref("");
const selectedCredentialId = ref("");
const isCreatingWorker = ref(false);
const importDryRunResult = ref<SubcontractorWorkerImportDryRunResult | null>(null);
const lastImportResult = ref<SubcontractorWorkerImportExecuteResult | null>(null);
const lastExportResult = ref<SubcontractorWorkerExportResult | null>(null);
const pendingImportFile = ref<File | null>(null);
const pendingProofFile = ref<File | null>(null);

const selectedWorkerLabel = computed(() =>
  selectedWorker.value
    ? `${selectedWorker.value.worker_no} · ${selectedWorker.value.first_name} ${selectedWorker.value.last_name}`
    : t("sicherplan.subcontractors.workforce.emptyDetail"),
);
const importRows = computed(() => lastImportResult.value?.rows ?? importDryRunResult.value?.rows ?? []);
const selectedQualification = computed<SubcontractorWorkerQualificationRead | null>(
  () => selectedWorker.value?.qualifications.find((row) => row.id === selectedQualificationId.value) ?? null,
);
const qualificationTypeOptions = computed(() =>
  qualificationTypes.value
    .filter((row) => row.archived_at == null)
    .map((row) => ({
      id: row.id,
      label: [row.code, row.label].filter(Boolean).join(" · "),
    })),
);
const qualificationTypeOptionsWithDraft = computed(() => {
  const currentValue = qualificationDraft.qualification_type_id.trim();
  if (!currentValue || qualificationTypeOptions.value.some((option) => option.id === currentValue)) {
    return qualificationTypeOptions.value;
  }
  return [...qualificationTypeOptions.value, { id: currentValue, label: currentValue }];
});
const credentialTypeOptions = computed(() =>
  EMPLOYEE_CREDENTIAL_TYPE_OPTIONS.map((option) => ({
    value: option.value,
    label: t(option.labelKey as never),
  })),
);
const workerReadinessMap = computed<Record<string, SubcontractorWorkerReadinessListItem>>(() =>
  Object.fromEntries(workerReadinessItems.value.map((row) => [row.worker_id, row])),
);

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

function resetWorkerDraft() {
  workerDraft.worker_no = "";
  workerDraft.first_name = "";
  workerDraft.last_name = "";
  workerDraft.preferred_name = "";
  workerDraft.birth_date = "";
  workerDraft.email = "";
  workerDraft.phone = "";
  workerDraft.mobile = "";
  workerDraft.status = "active";
  workerDraft.notes = "";
  workerDraft.version_no = 0;
}

function syncWorkerDraft(worker: SubcontractorWorkerRead) {
  workerDraft.worker_no = worker.worker_no;
  workerDraft.first_name = worker.first_name;
  workerDraft.last_name = worker.last_name;
  workerDraft.preferred_name = worker.preferred_name || "";
  workerDraft.birth_date = worker.birth_date || "";
  workerDraft.email = worker.email || "";
  workerDraft.phone = worker.phone || "";
  workerDraft.mobile = worker.mobile || "";
  workerDraft.status = worker.status;
  workerDraft.notes = worker.notes || "";
  workerDraft.version_no = worker.version_no;
}

function resetQualificationDraft() {
  selectedQualificationId.value = "";
  qualificationDraft.qualification_type_id = "";
  qualificationDraft.certificate_no = "";
  qualificationDraft.issued_at = "";
  qualificationDraft.valid_until = "";
  qualificationDraft.issuing_authority = "";
  qualificationDraft.status = "active";
  qualificationDraft.notes = "";
  qualificationDraft.version_no = 0;
  proofLinkDraft.document_id = "";
  proofLinkDraft.label = "";
}

function syncQualificationDraft(qualification: SubcontractorWorkerQualificationRead) {
  qualificationDraft.qualification_type_id = qualification.qualification_type_id;
  qualificationDraft.certificate_no = qualification.certificate_no || "";
  qualificationDraft.issued_at = qualification.issued_at || "";
  qualificationDraft.valid_until = qualification.valid_until || "";
  qualificationDraft.issuing_authority = qualification.issuing_authority || "";
  qualificationDraft.status = qualification.status;
  qualificationDraft.notes = qualification.notes || "";
  qualificationDraft.version_no = qualification.version_no;
}

function resetCredentialDraft() {
  selectedCredentialId.value = "";
  credentialDraft.credential_no = "";
  credentialDraft.credential_type = "";
  credentialDraft.encoded_value = "";
  credentialDraft.valid_from = "";
  credentialDraft.valid_until = "";
  credentialDraft.status = "active";
  credentialDraft.notes = "";
  credentialDraft.version_no = 0;
}

function syncCredentialDraft(credential: SubcontractorWorkerCredentialRead) {
  credentialDraft.credential_no = credential.credential_no;
  credentialDraft.credential_type = credential.credential_type;
  credentialDraft.encoded_value = credential.encoded_value;
  credentialDraft.valid_from = credential.valid_from;
  credentialDraft.valid_until = credential.valid_until || "";
  credentialDraft.status = credential.status;
  credentialDraft.notes = credential.notes || "";
  credentialDraft.version_no = credential.version_no;
}

async function refreshWorkers() {
  if (!props.tenantId || !props.subcontractorId || !props.accessToken || !props.canRead) {
    workers.value = [];
    workerReadinessItems.value = [];
    readinessSummary.value = null;
    selectedWorker.value = null;
    selectedWorkerReadiness.value = null;
    return;
  }
  loading.list = true;
  try {
    const filters = {
      ...(workerFilters.search.trim() ? { search: workerFilters.search.trim() } : {}),
      ...(workerFilters.status ? { status: workerFilters.status } : {}),
      include_archived: workerFilters.include_archived,
    };
    const readinessFilters = {
      ...filters,
      ...(workerFilters.readiness_status ? { readiness_status: workerFilters.readiness_status } : {}),
    };
    const [workerList, readinessList, readinessSummaryValue] = await Promise.all([
      listSubcontractorWorkers(props.tenantId, props.subcontractorId, props.accessToken, filters),
      listSubcontractorWorkerReadiness(props.tenantId, props.subcontractorId, props.accessToken, readinessFilters),
      getSubcontractorWorkerReadinessSummary(props.tenantId, props.subcontractorId, props.accessToken),
    ]);
    const readinessIds = new Set(readinessList.map((row) => row.worker_id));
    workers.value = workerList.filter((row) => readinessIds.has(row.id));
    workerReadinessItems.value = readinessList;
    readinessSummary.value = readinessSummaryValue;
    if (selectedWorkerId.value) {
      const stillVisible = workers.value.some((row) => row.id === selectedWorkerId.value);
      if (stillVisible) {
        await selectWorker(selectedWorkerId.value);
      } else {
        const firstWorker = workers.value[0];
        if (firstWorker) {
          await selectWorker(firstWorker.id);
        } else {
          selectedWorkerId.value = "";
          selectedWorker.value = null;
          selectedWorkerReadiness.value = null;
        }
      }
    } else {
      const firstWorker = workers.value[0];
      if (firstWorker) {
        await selectWorker(firstWorker.id);
      } else {
        selectedWorkerId.value = "";
      }
    }
  } catch (error) {
    const key = error instanceof SubcontractorAdminApiError ? mapSubcontractorApiMessage(error.messageKey) : "sicherplan.subcontractors.feedback.error";
    setFeedback("error", t("sicherplan.subcontractors.feedback.titleError"), t(key as never));
  } finally {
    loading.list = false;
  }
}

async function loadQualificationTypeOptions() {
  if (!props.tenantId || !props.accessToken) {
    qualificationTypes.value = [];
    return;
  }
  try {
    qualificationTypes.value = await listQualificationTypes(props.tenantId, props.accessToken);
  } catch {
    qualificationTypes.value = [];
  }
}

async function selectWorker(workerId: string) {
  if (!props.tenantId || !props.subcontractorId || !props.accessToken) {
    return;
  }
  loading.detail = true;
  try {
    const [worker, readiness] = await Promise.all([
      getSubcontractorWorker(props.tenantId, props.subcontractorId, workerId, props.accessToken),
      getSubcontractorWorkerReadiness(props.tenantId, props.subcontractorId, workerId, props.accessToken),
    ]);
    selectedWorker.value = worker;
    selectedWorkerReadiness.value = readiness;
    selectedWorkerId.value = worker.id;
    isCreatingWorker.value = false;
    syncWorkerDraft(worker);
    resetQualificationDraft();
    resetCredentialDraft();
  } catch (error) {
    const key = error instanceof SubcontractorAdminApiError ? mapSubcontractorApiMessage(error.messageKey) : "sicherplan.subcontractors.feedback.error";
    setFeedback("error", t("sicherplan.subcontractors.feedback.titleError"), t(key as never));
  } finally {
    loading.detail = false;
  }
}

function startCreateWorker() {
  isCreatingWorker.value = true;
  selectedWorkerId.value = "";
  selectedWorker.value = null;
  selectedWorkerReadiness.value = null;
  resetWorkerDraft();
  resetQualificationDraft();
  resetCredentialDraft();
}

async function submitWorker() {
  if (!props.tenantId || !props.subcontractorId || !props.accessToken || !props.canWrite) {
    return;
  }
  loading.action = true;
  try {
    const payload = {
      tenant_id: props.tenantId,
      subcontractor_id: props.subcontractorId,
      worker_no: workerDraft.worker_no.trim(),
      first_name: workerDraft.first_name.trim(),
      last_name: workerDraft.last_name.trim(),
      preferred_name: emptyToNull(workerDraft.preferred_name),
      birth_date: emptyToNull(workerDraft.birth_date),
      email: emptyToNull(workerDraft.email),
      phone: emptyToNull(workerDraft.phone),
      mobile: emptyToNull(workerDraft.mobile),
      status: emptyToNull(workerDraft.status),
      notes: emptyToNull(workerDraft.notes),
    };
    const worker = isCreatingWorker.value
      ? await createSubcontractorWorker(props.tenantId, props.subcontractorId, props.accessToken, payload)
      : await updateSubcontractorWorker(props.tenantId, props.subcontractorId, selectedWorkerId.value, props.accessToken, {
          ...payload,
          version_no: workerDraft.version_no,
        });
    await refreshWorkers();
    await selectWorker(worker.id);
    setFeedback("success", t("sicherplan.subcontractors.feedback.titleSuccess"), t("sicherplan.subcontractors.workforce.feedback.workerSaved"));
  } catch (error) {
    const key = error instanceof SubcontractorAdminApiError ? mapSubcontractorApiMessage(error.messageKey) : "sicherplan.subcontractors.feedback.error";
    setFeedback("error", t("sicherplan.subcontractors.feedback.titleError"), t(key as never));
  } finally {
    loading.action = false;
  }
}

async function archiveWorker() {
  if (!selectedWorker.value) {
    return;
  }
  loading.action = true;
  try {
    await updateSubcontractorWorker(props.tenantId, props.subcontractorId, selectedWorker.value.id, props.accessToken, {
      status: "archived",
      archived_at: new Date().toISOString(),
      version_no: selectedWorker.value.version_no,
    });
    await refreshWorkers();
    setFeedback("success", t("sicherplan.subcontractors.feedback.titleSuccess"), t("sicherplan.subcontractors.feedback.lifecycleSaved"));
  } catch (error) {
    const key = error instanceof SubcontractorAdminApiError ? mapSubcontractorApiMessage(error.messageKey) : "sicherplan.subcontractors.feedback.error";
    setFeedback("error", t("sicherplan.subcontractors.feedback.titleError"), t(key as never));
  } finally {
    loading.action = false;
  }
}

async function reactivateWorker() {
  if (!selectedWorker.value) {
    return;
  }
  loading.action = true;
  try {
    await updateSubcontractorWorker(props.tenantId, props.subcontractorId, selectedWorker.value.id, props.accessToken, {
      status: "active",
      archived_at: null,
      version_no: selectedWorker.value.version_no,
    });
    await refreshWorkers();
    setFeedback("success", t("sicherplan.subcontractors.feedback.titleSuccess"), t("sicherplan.subcontractors.feedback.lifecycleSaved"));
  } catch (error) {
    const key = error instanceof SubcontractorAdminApiError ? mapSubcontractorApiMessage(error.messageKey) : "sicherplan.subcontractors.feedback.error";
    setFeedback("error", t("sicherplan.subcontractors.feedback.titleError"), t(key as never));
  } finally {
    loading.action = false;
  }
}

function selectQualification(qualificationId: string) {
  selectedQualificationId.value = qualificationId;
  const qualification = selectedWorker.value?.qualifications.find((row) => row.id === qualificationId);
  if (qualification) {
    syncQualificationDraft(qualification);
  }
}

async function submitQualification() {
  if (!selectedWorker.value || !props.canWrite) {
    return;
  }
  loading.action = true;
  try {
    const payload = {
      tenant_id: props.tenantId,
      subcontractor_id: props.subcontractorId,
      worker_id: selectedWorker.value.id,
      qualification_type_id: qualificationDraft.qualification_type_id.trim(),
      certificate_no: emptyToNull(qualificationDraft.certificate_no),
      issued_at: emptyToNull(qualificationDraft.issued_at),
      valid_until: emptyToNull(qualificationDraft.valid_until),
      issuing_authority: emptyToNull(qualificationDraft.issuing_authority),
      status: emptyToNull(qualificationDraft.status),
      notes: emptyToNull(qualificationDraft.notes),
    };
    if (selectedQualificationId.value) {
      await updateSubcontractorWorkerQualification(
        props.tenantId,
        props.subcontractorId,
        selectedWorker.value.id,
        selectedQualificationId.value,
        props.accessToken,
        {
          ...payload,
          version_no: qualificationDraft.version_no,
        },
      );
    } else {
      await createSubcontractorWorkerQualification(props.tenantId, props.subcontractorId, selectedWorker.value.id, props.accessToken, payload);
    }
    await selectWorker(selectedWorker.value.id);
    resetQualificationDraft();
    setFeedback("success", t("sicherplan.subcontractors.feedback.titleSuccess"), t("sicherplan.subcontractors.workforce.feedback.qualificationSaved"));
  } catch (error) {
    const key = error instanceof SubcontractorAdminApiError ? mapSubcontractorApiMessage(error.messageKey) : "sicherplan.subcontractors.feedback.error";
    setFeedback("error", t("sicherplan.subcontractors.feedback.titleError"), t(key as never));
  } finally {
    loading.action = false;
  }
}

function selectCredential(credentialId: string) {
  selectedCredentialId.value = credentialId;
  const credential = selectedWorker.value?.credentials.find((row) => row.id === credentialId);
  if (credential) {
    syncCredentialDraft(credential);
  }
}

async function submitCredential() {
  if (!selectedWorker.value || !props.canWrite) {
    return;
  }
  loading.action = true;
  try {
    const payload = {
      tenant_id: props.tenantId,
      subcontractor_id: props.subcontractorId,
      worker_id: selectedWorker.value.id,
      credential_no: credentialDraft.credential_no.trim(),
      credential_type: credentialDraft.credential_type.trim(),
      encoded_value: credentialDraft.encoded_value.trim(),
      valid_from: credentialDraft.valid_from || new Date().toISOString().slice(0, 10),
      valid_until: emptyToNull(credentialDraft.valid_until),
      status: emptyToNull(credentialDraft.status),
      notes: emptyToNull(credentialDraft.notes),
    };
    if (selectedCredentialId.value) {
      await updateSubcontractorWorkerCredential(
        props.tenantId,
        props.subcontractorId,
        selectedWorker.value.id,
        selectedCredentialId.value,
        props.accessToken,
        {
          encoded_value: payload.encoded_value,
          valid_from: payload.valid_from,
          valid_until: payload.valid_until,
          status: payload.status,
          notes: payload.notes,
          version_no: credentialDraft.version_no,
        },
      );
    } else {
      await createSubcontractorWorkerCredential(props.tenantId, props.subcontractorId, selectedWorker.value.id, props.accessToken, payload);
    }
    await selectWorker(selectedWorker.value.id);
    resetCredentialDraft();
    setFeedback("success", t("sicherplan.subcontractors.feedback.titleSuccess"), t("sicherplan.subcontractors.workforce.feedback.credentialSaved"));
  } catch (error) {
    const key = error instanceof SubcontractorAdminApiError ? mapSubcontractorApiMessage(error.messageKey) : "sicherplan.subcontractors.feedback.error";
    setFeedback("error", t("sicherplan.subcontractors.feedback.titleError"), t(key as never));
  } finally {
    loading.action = false;
  }
}

function onImportSelected(event: Event) {
  const target = event.target as HTMLInputElement;
  pendingImportFile.value = target.files?.[0] ?? null;
}

async function loadImportFile() {
  if (!pendingImportFile.value) {
    return;
  }
  importDraft.csv_text = await pendingImportFile.value.text();
}

function downloadTemplate() {
  downloadBlob(buildSubcontractorWorkerImportTemplateRows(), "subcontractor-workers-template.csv", "text/csv");
}

async function runImportDryRun() {
  loading.action = true;
  try {
    importDryRunResult.value = await importSubcontractorWorkersDryRun(props.tenantId, props.subcontractorId, props.accessToken, {
      tenant_id: props.tenantId,
      subcontractor_id: props.subcontractorId,
      csv_content_base64: stringToBase64(importDraft.csv_text),
    });
    setFeedback("success", t("sicherplan.subcontractors.feedback.titleSuccess"), t("sicherplan.subcontractors.workforce.feedback.importDryRunReady"));
  } catch (error) {
    const key = error instanceof SubcontractorAdminApiError ? mapSubcontractorApiMessage(error.messageKey) : "sicherplan.subcontractors.feedback.error";
    setFeedback("error", t("sicherplan.subcontractors.feedback.titleError"), t(key as never));
  } finally {
    loading.action = false;
  }
}

async function runImportExecute() {
  loading.action = true;
  try {
    lastImportResult.value = await importSubcontractorWorkersExecute(props.tenantId, props.subcontractorId, props.accessToken, {
      tenant_id: props.tenantId,
      subcontractor_id: props.subcontractorId,
      csv_content_base64: stringToBase64(importDraft.csv_text),
      continue_on_error: importDraft.continue_on_error,
    });
    await refreshWorkers();
    setFeedback("success", t("sicherplan.subcontractors.feedback.titleSuccess"), t("sicherplan.subcontractors.workforce.feedback.importExecuted"));
  } catch (error) {
    const key = error instanceof SubcontractorAdminApiError ? mapSubcontractorApiMessage(error.messageKey) : "sicherplan.subcontractors.feedback.error";
    setFeedback("error", t("sicherplan.subcontractors.feedback.titleError"), t(key as never));
  } finally {
    loading.action = false;
  }
}

async function runExport() {
  loading.action = true;
  try {
    lastExportResult.value = await exportSubcontractorWorkers(props.tenantId, props.subcontractorId, props.accessToken, {
      tenant_id: props.tenantId,
      subcontractor_id: props.subcontractorId,
      search: emptyToNull(workerFilters.search),
      status: emptyToNull(workerFilters.status),
      include_archived: workerFilters.include_archived,
    });
    setFeedback("success", t("sicherplan.subcontractors.feedback.titleSuccess"), t("sicherplan.subcontractors.workforce.feedback.exportReady"));
  } catch (error) {
    const key = error instanceof SubcontractorAdminApiError ? mapSubcontractorApiMessage(error.messageKey) : "sicherplan.subcontractors.feedback.error";
    setFeedback("error", t("sicherplan.subcontractors.feedback.titleError"), t(key as never));
  } finally {
    loading.action = false;
  }
}

function onProofSelected(event: Event) {
  const target = event.target as HTMLInputElement;
  pendingProofFile.value = target.files?.[0] ?? null;
}

async function uploadProof() {
  if (!selectedWorker.value || !selectedQualification.value || !pendingProofFile.value) {
    return;
  }
  loading.action = true;
  try {
    await uploadSubcontractorQualificationProof(
      props.tenantId,
      props.subcontractorId,
      selectedWorker.value.id,
      selectedQualification.value.id,
      props.accessToken,
      {
        title: pendingProofFile.value.name,
        file_name: pendingProofFile.value.name,
        content_type: pendingProofFile.value.type || "application/octet-stream",
        content_base64: await fileToBase64(pendingProofFile.value),
      },
    );
    pendingProofFile.value = null;
    await selectWorker(selectedWorker.value.id);
    setFeedback("success", t("sicherplan.subcontractors.feedback.titleSuccess"), t("sicherplan.subcontractors.workforce.feedback.proofSaved"));
  } catch (error) {
    const key = error instanceof SubcontractorAdminApiError ? mapSubcontractorApiMessage(error.messageKey) : "sicherplan.subcontractors.feedback.error";
    setFeedback("error", t("sicherplan.subcontractors.feedback.titleError"), t(key as never));
  } finally {
    loading.action = false;
  }
}

async function linkProof() {
  if (!selectedWorker.value || !selectedQualification.value) {
    return;
  }
  loading.action = true;
  try {
    await linkSubcontractorQualificationProof(
      props.tenantId,
      props.subcontractorId,
      selectedWorker.value.id,
      selectedQualification.value.id,
      props.accessToken,
      {
        document_id: proofLinkDraft.document_id.trim(),
        label: emptyToNull(proofLinkDraft.label),
      },
    );
    proofLinkDraft.document_id = "";
    proofLinkDraft.label = "";
    await selectWorker(selectedWorker.value.id);
    setFeedback("success", t("sicherplan.subcontractors.feedback.titleSuccess"), t("sicherplan.subcontractors.workforce.feedback.proofLinked"));
  } catch (error) {
    const key = error instanceof SubcontractorAdminApiError ? mapSubcontractorApiMessage(error.messageKey) : "sicherplan.subcontractors.feedback.error";
    setFeedback("error", t("sicherplan.subcontractors.feedback.titleError"), t(key as never));
  } finally {
    loading.action = false;
  }
}

async function downloadProof(proof: SubcontractorWorkerQualificationProofRead) {
  if (!proof.current_version_no) {
    return;
  }
  loading.action = true;
  try {
    const file = await downloadSubcontractorDocument(props.tenantId, proof.document_id, proof.current_version_no, props.accessToken);
    downloadBlob(file.blob, file.fileName, file.blob.type || "application/octet-stream");
  } catch (error) {
    const key = error instanceof SubcontractorAdminApiError ? mapSubcontractorApiMessage(error.messageKey) : "sicherplan.subcontractors.feedback.error";
    setFeedback("error", t("sicherplan.subcontractors.feedback.titleError"), t(key as never));
  } finally {
    loading.action = false;
  }
}

function mapImportMessage(code: string) {
  return mapSubcontractorImportRowMessage(code);
}

function mapReadinessStatusLabel(readinessStatus?: string | null) {
  if (readinessStatus === "not_ready") {
    return t("sicherplan.subcontractors.workforce.readiness.status.notReady");
  }
  if (readinessStatus === "ready_with_warnings") {
    return t("sicherplan.subcontractors.workforce.readiness.status.readyWithWarnings");
  }
  return t("sicherplan.subcontractors.workforce.readiness.status.ready");
}

function emptyToNull(value: string | null | undefined) {
  if (value == null) {
    return null;
  }
  const trimmed = value.trim();
  return trimmed || null;
}

function stringToBase64(value: string) {
  return btoa(unescape(encodeURIComponent(value)));
}

async function fileToBase64(file: File) {
  const buffer = await file.arrayBuffer();
  let binary = "";
  const bytes = new Uint8Array(buffer);
  for (const byte of bytes) {
    binary += String.fromCharCode(byte);
  }
  return btoa(binary);
}

function downloadBlob(content: Blob | string, fileName: string, contentType: string) {
  const blob = typeof content === "string" ? new Blob([content], { type: contentType }) : content;
  const href = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = href;
  anchor.download = fileName;
  anchor.click();
  URL.revokeObjectURL(href);
}

watch(
  () => [props.tenantId, props.subcontractorId, props.accessToken, props.canRead],
  () => {
    resetWorkerDraft();
    resetQualificationDraft();
    resetCredentialDraft();
    void loadQualificationTypeOptions();
    void refreshWorkers();
  },
);

onMounted(() => {
  void loadQualificationTypeOptions();
  void refreshWorkers();
});
</script>

<style scoped>
.subcontractor-workforce {
  margin-top: 1.5rem;
}

.subcontractor-workforce-grid {
  display: grid;
  gap: 1rem;
  grid-template-columns: minmax(18rem, 24rem) minmax(0, 1fr);
}

.subcontractor-workforce-import-results {
  display: grid;
  gap: 0.5rem;
}

.subcontractor-workforce-import-results__row {
  border: 1px solid var(--vben-border-color, #d6dee6);
  border-radius: 0.75rem;
  display: grid;
  gap: 0.25rem;
  padding: 0.75rem;
}

.subcontractor-workforce-proof-block {
  display: grid;
  gap: 0.75rem;
  margin-top: 1rem;
}

.subcontractor-workforce-proof-list {
  display: grid;
  gap: 0.5rem;
}

.subcontractor-workforce-row-status {
  align-items: flex-end;
  display: grid;
  gap: 0.5rem;
  justify-items: end;
}

.subcontractor-workforce-readiness-overview {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.subcontractor-workforce-readiness-pill {
  border-radius: 999px;
  display: inline-flex;
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.3rem 0.7rem;
}

.subcontractor-workforce-readiness-pill[data-readiness="ready"] {
  background: rgb(220 248 240);
  color: rgb(17 94 70);
}

.subcontractor-workforce-readiness-pill[data-readiness="ready_with_warnings"] {
  background: rgb(255 242 204);
  color: rgb(146 93 0);
}

.subcontractor-workforce-readiness-pill[data-readiness="not_ready"] {
  background: rgb(255 226 226);
  color: rgb(151 28 28);
}

.subcontractor-workforce-readiness-issues {
  display: grid;
  gap: 0.75rem;
}

.subcontractor-workforce-readiness-issue {
  border: 1px solid var(--vben-border-color, #d6dee6);
  border-radius: 0.75rem;
  display: grid;
  gap: 0.25rem;
  padding: 0.75rem;
}

.subcontractor-workforce-readiness-issue[data-severity="blocking"] {
  border-color: rgb(232 98 98);
}

.subcontractor-workforce-readiness-issue[data-severity="warning"] {
  border-color: rgb(230 188 89);
}

@media (width <= 960px) {
  .subcontractor-workforce-grid {
    grid-template-columns: 1fr;
  }
}
</style>
