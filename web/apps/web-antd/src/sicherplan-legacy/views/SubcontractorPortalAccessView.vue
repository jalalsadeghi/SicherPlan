<template>
  <section class="module-card portal-subcontractor-view">
    <p class="eyebrow">{{ t("portalSubcontractor.eyebrow") }}</p>
    <div class="portal-subcontractor-header">
      <div>
        <h2>{{ t("portalSubcontractor.title") }}</h2>
        <p>{{ t("portalSubcontractor.lead") }}</p>
      </div>
      <div class="portal-actions">
        <button class="secondary-button" type="button" @click="refreshPortalContext">
          {{ t("portalSubcontractor.actions.refresh") }}
        </button>
        <button
          v-if="authStore.hasSession"
          class="secondary-button"
          type="button"
          @click="logoutPortalSession"
        >
          {{ t("portalSubcontractor.actions.logout") }}
        </button>
      </div>
    </div>

    <p v-if="feedbackKey" class="portal-feedback" :data-tone="feedbackTone">
      {{ t(feedbackKey) }}
    </p>

    <form v-if="accessState === 'login'" class="portal-login-grid" @submit.prevent="submitLogin">
      <div class="field">
        <label for="tenant-code">{{ t("portalSubcontractor.login.tenantCode") }}</label>
        <input id="tenant-code" v-model.trim="tenantCode" autocomplete="organization" required />
      </div>
      <div class="field">
        <label for="identifier">{{ t("portalSubcontractor.login.identifier") }}</label>
        <input id="identifier" v-model.trim="identifier" autocomplete="username" required />
      </div>
      <div class="field">
        <label for="password">{{ t("portalSubcontractor.login.password") }}</label>
        <input id="password" v-model="password" autocomplete="current-password" type="password" required />
      </div>
      <div class="field">
        <label for="device-label">{{ t("portalSubcontractor.login.deviceLabel") }}</label>
        <input id="device-label" v-model.trim="deviceLabel" autocomplete="off" />
      </div>
      <div class="portal-login-actions">
        <button class="cta-button" type="submit" :disabled="loading">
          {{ t("portalSubcontractor.actions.login") }}
        </button>
      </div>
    </form>

    <div v-else-if="accessState === 'loading'" class="portal-state-card">
      <h3>{{ t("portalSubcontractor.loading.title") }}</h3>
      <p>{{ t("portalSubcontractor.loading.body") }}</p>
    </div>

    <div v-else-if="accessState === 'empty'" class="portal-state-card">
      <h3>{{ t("portalSubcontractor.empty.title") }}</h3>
      <p>{{ t("portalSubcontractor.empty.body") }}</p>
    </div>

    <div v-else-if="accessState === 'deactivated'" class="portal-state-card">
      <h3>{{ t("portalSubcontractor.deactivated.title") }}</h3>
      <p>{{ t("portalSubcontractor.deactivated.body") }}</p>
    </div>

    <div v-else-if="accessState === 'unauthorized'" class="portal-state-card">
      <h3>{{ t("portalSubcontractor.unauthorized.title") }}</h3>
      <p>{{ t("portalSubcontractor.unauthorized.body") }}</p>
    </div>

    <div v-else-if="portalContext" class="portal-stack">
      <div class="portal-summary-grid">
        <article class="portal-summary-card">
          <p class="eyebrow">{{ t("portalSubcontractor.summary.title") }}</p>
          <dl>
            <div>
              <dt>{{ t("portalSubcontractor.summary.companyNumber") }}</dt>
              <dd>{{ portalContext.company.subcontractor_number }}</dd>
            </div>
            <div>
              <dt>{{ t("portalSubcontractor.summary.companyName") }}</dt>
              <dd>{{ portalContext.company.display_name || portalContext.company.legal_name }}</dd>
            </div>
            <div>
              <dt>{{ t("portalSubcontractor.summary.contact") }}</dt>
              <dd>{{ portalContext.contact.full_name }}</dd>
            </div>
            <div>
              <dt>{{ t("portalSubcontractor.summary.email") }}</dt>
              <dd>{{ portalContext.contact.email || "-" }}</dd>
            </div>
            <div>
              <dt>{{ t("portalSubcontractor.summary.function") }}</dt>
              <dd>{{ portalContext.contact.function_label || "-" }}</dd>
            </div>
            <div>
              <dt>{{ t("portalSubcontractor.summary.scope") }}</dt>
              <dd>{{ portalScopeSummary }}</dd>
            </div>
          </dl>
        </article>

        <article class="portal-summary-card">
          <p class="eyebrow">{{ t("portalSubcontractor.readOnly.title") }}</p>
          <p>{{ t("portalSubcontractor.readOnly.body") }}</p>
          <ul class="portal-flags">
            <li>{{ t("portalSubcontractor.meta.releasedOnly") }}</li>
            <li>{{ t("portalSubcontractor.meta.subcontractorScoped") }}</li>
            <li>{{ t("portalSubcontractor.meta.noFakeData") }}</li>
          </ul>
        </article>
      </div>

      <article class="portal-summary-card portal-allocation-card">
        <div class="portal-dataset-header">
          <div>
            <p class="eyebrow">{{ t("portalSubcontractor.allocation.eyebrow") }}</p>
            <h3>{{ t("portalSubcontractor.allocation.title") }}</h3>
            <p>{{ t("portalSubcontractor.allocation.lead") }}</p>
          </div>
          <span
            v-if="allocationPreview || allocationResult"
            class="status-badge"
            :data-state="allocationStatusTone"
          >
            {{ t(allocationStatusLabel) }}
          </span>
        </div>

        <p class="dataset-meta">{{ t("portalSubcontractor.allocation.pendingPlanning") }}</p>

        <div v-if="!positions?.items.length" class="portal-state-card">
          <p>{{ t("portalSubcontractor.allocation.noPositions") }}</p>
        </div>
        <div v-else-if="!allocationCandidates?.items.length" class="portal-state-card">
          <p>{{ t("portalSubcontractor.allocation.noWorkers") }}</p>
        </div>
        <div v-else class="portal-login-grid">
          <div class="field">
            <label for="allocation-position">{{ t("portalSubcontractor.allocation.position") }}</label>
            <select id="allocation-position" v-model="allocationPositionId">
              <option v-for="item in positions.items" :key="item.id" :value="item.id">
                {{ item.reference_no }} · {{ item.title }}
              </option>
            </select>
          </div>
          <div class="field">
            <label for="allocation-worker">{{ t("portalSubcontractor.allocation.worker") }}</label>
            <select id="allocation-worker" v-model="allocationWorkerId">
              <option v-for="item in allocationCandidates.items" :key="item.worker_id" :value="item.worker_id">
                {{ item.worker_no }} · {{ item.display_name }} ·
                {{ t(readinessLabel(item.readiness_status)) }}
              </option>
            </select>
          </div>
          <div class="field">
            <label for="allocation-action">{{ t("portalSubcontractor.allocation.action") }}</label>
            <select id="allocation-action" v-model="allocationAction">
              <option value="assign">{{ t("portalSubcontractor.allocation.command.assign") }}</option>
              <option value="confirm">{{ t("portalSubcontractor.allocation.command.confirm") }}</option>
              <option value="reassign">{{ t("portalSubcontractor.allocation.command.reassign") }}</option>
              <option value="unassign">{{ t("portalSubcontractor.allocation.command.unassign") }}</option>
            </select>
          </div>
          <div class="portal-login-actions">
            <button class="secondary-button" type="button" :disabled="loading" @click="previewAllocation">
              {{ t("portalSubcontractor.allocation.preview") }}
            </button>
            <button
              class="cta-button"
              type="button"
              :disabled="loading || !allocationPreview?.can_submit"
              @click="submitAllocation"
            >
              {{ t("portalSubcontractor.allocation.submit") }}
            </button>
          </div>
        </div>

        <div v-if="allocationPreview" class="allocation-panel">
          <h4>{{ t("portalSubcontractor.allocation.validationTitle") }}</h4>
          <ul class="portal-flags">
            <li v-for="issue in allocationPreview.issues" :key="`${issue.issue_code}-${issue.reference_id || 'none'}`">
              <strong>{{ issue.severity.toUpperCase() }}</strong>
              · {{ issue.title }}
            </li>
          </ul>
        </div>

        <div v-if="allocationResult" class="allocation-panel">
          <h4>{{ t("portalSubcontractor.allocation.resultTitle") }}</h4>
          <p class="dataset-meta">{{ t(mapPortalMessage(allocationResult.message_key)) }}</p>
          <ul v-if="allocationResult.issues.length" class="portal-flags">
            <li v-for="issue in allocationResult.issues" :key="`result-${issue.issue_code}-${issue.reference_id || 'none'}`">
              <strong>{{ issue.severity.toUpperCase() }}</strong>
              · {{ issue.title }}
            </li>
          </ul>
        </div>
      </article>

      <article class="portal-summary-card portal-allocation-card">
        <div class="portal-dataset-header">
          <div>
            <p class="eyebrow">{{ t("sicherplan.subcontractors.workforce.eyebrow" as never) }}</p>
            <h3>{{ t("sicherplan.subcontractors.workforce.title" as never) }}</h3>
            <p>{{ t("portalSubcontractor.workforce.lead") }}</p>
          </div>
          <div class="portal-actions">
            <button class="secondary-button" type="button" @click="startCreateWorker">
              {{ t("sicherplan.subcontractors.workforce.actions.newWorker" as never) }}
            </button>
          </div>
        </div>
        <p class="dataset-meta">{{ t("portalSubcontractor.workforce.boundary") }}</p>

        <div class="portal-summary-grid">
          <section class="portal-summary-card">
            <h4>{{ t("portalSubcontractor.workforce.workerList") }}</h4>
            <div v-if="workerList.length" class="portal-flags">
              <button
                v-for="worker in workerList"
                :key="worker.id"
                class="secondary-button worker-select-button"
                type="button"
                @click="loadSelectedWorker(worker.id)"
              >
                {{ worker.worker_no }} · {{ worker.first_name }} {{ worker.last_name }}
              </button>
            </div>
            <p v-else class="dataset-meta">{{ t("portalSubcontractor.workforce.empty") }}</p>
          </section>

          <section class="portal-summary-card">
            <h4>
              {{
                isCreatingWorker
                  ? t("sicherplan.subcontractors.workforce.newTitle" as never)
                  : t("portalSubcontractor.workforce.editTitle")
              }}
            </h4>
            <div class="portal-login-grid">
              <div class="field">
                <label for="portal-worker-no">{{ t("sicherplan.subcontractors.workforce.fields.workerNo" as never) }}</label>
                <input id="portal-worker-no" v-model="workerForm.worker_no" />
              </div>
              <div class="field">
                <label for="portal-worker-first-name">{{ t("sicherplan.subcontractors.workforce.fields.firstName" as never) }}</label>
                <input id="portal-worker-first-name" v-model="workerForm.first_name" />
              </div>
              <div class="field">
                <label for="portal-worker-last-name">{{ t("sicherplan.subcontractors.workforce.fields.lastName" as never) }}</label>
                <input id="portal-worker-last-name" v-model="workerForm.last_name" />
              </div>
              <div class="field">
                <label for="portal-worker-preferred-name">{{ t("sicherplan.subcontractors.workforce.fields.preferredName" as never) }}</label>
                <input id="portal-worker-preferred-name" v-model="workerForm.preferred_name" />
              </div>
              <div class="field">
                <label for="portal-worker-birth-date">{{ t("sicherplan.subcontractors.workforce.fields.birthDate" as never) }}</label>
                <input id="portal-worker-birth-date" v-model="workerForm.birth_date" type="date" />
              </div>
              <div class="field">
                <label for="portal-worker-email">{{ t("sicherplan.subcontractors.workforce.fields.email" as never) }}</label>
                <input id="portal-worker-email" v-model="workerForm.email" type="email" />
              </div>
              <div class="field">
                <label for="portal-worker-phone">{{ t("sicherplan.subcontractors.workforce.fields.phone" as never) }}</label>
                <input id="portal-worker-phone" v-model="workerForm.phone" />
              </div>
              <div class="field">
                <label for="portal-worker-mobile">{{ t("sicherplan.subcontractors.workforce.fields.mobile" as never) }}</label>
                <input id="portal-worker-mobile" v-model="workerForm.mobile" />
              </div>
            </div>
            <div class="portal-login-actions">
              <button class="cta-button" type="button" @click="saveWorker">
                {{ t("portalSubcontractor.workforce.saveWorker") }}
              </button>
            </div>
          </section>
        </div>

        <section v-if="selectedWorker" class="portal-summary-card">
          <div class="portal-dataset-header">
            <div>
              <p class="eyebrow">{{ t("sicherplan.subcontractors.workforce.readiness.eyebrow" as never) }}</p>
              <h4>{{ selectedWorker.worker_no }} · {{ selectedWorker.first_name }} {{ selectedWorker.last_name }}</h4>
            </div>
          </div>

          <div class="portal-summary-grid">
            <section class="portal-summary-card">
              <h4>{{ t("portalSubcontractor.workforce.qualificationsTitle") }}</h4>
              <div class="portal-flags" v-if="selectedWorker.qualifications.length">
                <button
                  v-for="qualification in selectedWorker.qualifications"
                  :key="qualification.id"
                  class="secondary-button worker-select-button"
                  type="button"
                  @click="selectQualification(qualification.id)"
                >
                  {{ qualification.qualification_type_label || qualification.qualification_type_code || qualification.qualification_type_id }}
                </button>
              </div>
              <p v-else class="dataset-meta">{{ t("portalSubcontractor.workforce.noQualifications") }}</p>
            </section>

            <section class="portal-summary-card">
              <h4>{{ t("portalSubcontractor.workforce.qualificationEditor") }}</h4>
              <div class="portal-login-grid">
                <div class="field">
                  <label for="portal-qualification-type">{{ t("portalSubcontractor.workforce.qualificationType") }}</label>
                  <select id="portal-qualification-type" v-model="qualificationForm.qualification_type_id">
                    <option v-for="option in qualificationTypes" :key="option.id" :value="option.id">
                      {{ option.label }}
                    </option>
                  </select>
                </div>
                <div class="field">
                  <label for="portal-qualification-certificate">{{ t("sicherplan.subcontractors.workforce.fields.certificateNo" as never) }}</label>
                  <input id="portal-qualification-certificate" v-model="qualificationForm.certificate_no" />
                </div>
                <div class="field">
                  <label for="portal-qualification-issued-at">{{ t("sicherplan.subcontractors.workforce.fields.issuedAt" as never) }}</label>
                  <input id="portal-qualification-issued-at" v-model="qualificationForm.issued_at" type="date" />
                </div>
                <div class="field">
                  <label for="portal-qualification-valid-until">{{ t("sicherplan.subcontractors.workforce.fields.validUntil" as never) }}</label>
                  <input id="portal-qualification-valid-until" v-model="qualificationForm.valid_until" type="date" />
                </div>
                <div class="field">
                  <label for="portal-qualification-authority">{{ t("sicherplan.subcontractors.workforce.fields.issuingAuthority" as never) }}</label>
                  <input id="portal-qualification-authority" v-model="qualificationForm.issuing_authority" />
                </div>
              </div>
              <div class="portal-login-actions">
                <button class="cta-button" type="button" @click="saveQualification">
                  {{ t("portalSubcontractor.workforce.saveQualification") }}
                </button>
              </div>
            </section>
          </div>

          <section v-if="selectedQualification" class="portal-summary-card">
            <h4>{{ t("portalSubcontractor.workforce.proofsTitle") }}</h4>
            <ul v-if="selectedQualification.proofs.length" class="portal-flags">
              <li v-for="proof in selectedQualification.proofs" :key="proof.document_id">
                {{ proof.title }} · {{ proof.file_name || proof.document_id }}
              </li>
            </ul>
            <p v-else class="dataset-meta">{{ t("portalSubcontractor.workforce.noProofs") }}</p>
            <div class="portal-login-actions">
              <input type="file" @change="onQualificationUploadSelected" />
              <button class="cta-button" type="button" :disabled="!qualificationUpload" @click="uploadQualificationProof">
                {{ t("portalSubcontractor.workforce.uploadProof") }}
              </button>
            </div>
          </section>
        </section>
      </article>

      <article class="portal-summary-card portal-allocation-card">
        <div class="portal-dataset-header">
          <div>
            <p class="eyebrow">{{ t("portalSubcontractor.datasets.watchbooks.eyebrow") }}</p>
            <h3>{{ t("portalSubcontractor.datasets.watchbooks.title") }}</h3>
            <p>{{ t("portalSubcontractor.datasets.watchbooks.lead") }}</p>
          </div>
          <span class="status-badge" :data-state="collectionState(watchbooks)">
            {{ t(collectionStateKey(collectionState(watchbooks))) }}
          </span>
        </div>
        <p class="dataset-meta">
          {{ t(collectionMessageKey(watchbooks?.source.message_key, "portalSubcontractor.datasets.watchbooks.pending")) }}
        </p>
        <p class="dataset-meta">
          {{ t("portalSubcontractor.meta.sourceModule") }}:
          {{ watchbooks?.source.source_module_key || "field_execution" }}
        </p>
        <ul v-if="watchbooks?.items.length" class="portal-flags">
          <li v-for="item in watchbooks.items" :key="item.id">
            {{ item.log_date }} · {{ item.summary }}
            <span class="dataset-meta">
              {{ item.occurred_at }} · {{ item.entry_type_code }}
              <template v-if="item.pdf_document_id"> · PDF {{ item.pdf_document_id }}</template>
            </span>
          </li>
        </ul>
        <div v-if="watchbooks?.items.length" class="portal-login-grid">
          <div class="field">
            <label for="subcontractor-watchbook-select">{{ t("portalSubcontractor.watchbooks.fields.watchbook") }}</label>
            <select id="subcontractor-watchbook-select" v-model="selectedWatchbookId">
              <option v-for="item in watchbooks.items" :key="item.id" :value="item.id">
                {{ item.log_date }} · {{ item.summary }}
              </option>
            </select>
          </div>
          <div class="field">
            <label for="subcontractor-watchbook-note">{{ t("portalSubcontractor.watchbooks.fields.note") }}</label>
            <textarea
              id="subcontractor-watchbook-note"
              v-model.trim="watchbookNarrative"
              rows="4"
              :placeholder="t('portalSubcontractor.watchbooks.fields.notePlaceholder')"
            />
          </div>
          <div class="portal-login-actions">
            <button
              class="cta-button"
              type="button"
              :disabled="loading || !selectedWatchbookId || !watchbookNarrative"
              @click="submitWatchbookEntry"
            >
              {{ t("portalSubcontractor.watchbooks.actions.submit") }}
            </button>
          </div>
        </div>
      </article>

      <div class="portal-dataset-grid">
        <article v-for="dataset in datasets" :key="dataset.key" class="portal-dataset-card">
          <div class="portal-dataset-header">
            <div>
              <p class="eyebrow">{{ t(dataset.eyebrowKey) }}</p>
              <h3>{{ t(dataset.titleKey) }}</h3>
              <p>{{ t(dataset.leadKey) }}</p>
            </div>
            <span class="status-badge" :data-state="collectionState(dataset.collection)">
              {{ t(collectionStateKey(collectionState(dataset.collection))) }}
            </span>
          </div>
          <p class="dataset-meta">
            {{ t(collectionMessageKey(dataset.collection?.source.message_key, dataset.pendingKey)) }}
          </p>
          <p class="dataset-meta">
            {{ t("portalSubcontractor.meta.sourceModule") }}:
            {{ dataset.collection?.source.source_module_key || dataset.sourceModule }}
          </p>
          <ul v-if="dataset.items.length" class="portal-flags">
            <li v-for="item in dataset.items" :key="item.id">{{ item.label }}</li>
          </ul>
        </article>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";

import { AuthApiError } from "@/api/auth";
import {
  createSubcontractorPortalWatchbookEntry,
  createSubcontractorPortalWorker,
  createSubcontractorPortalWorkerQualification,
  getSubcontractorPortalActuals,
  getSubcontractorPortalAllocationCandidates,
  getSubcontractorPortalAttendance,
  getSubcontractorPortalInvoiceChecks,
  getSubcontractorPortalPositions,
  getSubcontractorPortalSchedules,
  getSubcontractorPortalWatchbooks,
  getSubcontractorPortalWorker,
  getSubcontractorPortalWorkerQualificationTypes,
  getSubcontractorPortalWorkers,
  previewSubcontractorPortalAllocation,
  submitSubcontractorPortalAllocation,
  updateSubcontractorPortalWorker,
  updateSubcontractorPortalWorkerQualification,
  uploadSubcontractorPortalWorkerQualificationProof,
  type SubcontractorPortalAllocationAction,
  type SubcontractorPortalAllocationCandidateCollectionRead,
  type SubcontractorPortalAllocationPreviewRead,
  type SubcontractorPortalAllocationResultRead,
  type SubcontractorPortalActualSummaryCollectionRead,
  type SubcontractorPortalAttendanceCollectionRead,
  type SubcontractorPortalInvoiceCheckCollectionRead,
  type SubcontractorPortalPositionCollectionRead,
  type SubcontractorPortalQualificationTypeOptionRead,
  type SubcontractorPortalScheduleCollectionRead,
  type SubcontractorPortalWatchbookCollectionRead,
  type SubcontractorPortalWorkerCreate,
  type SubcontractorPortalWorkerQualificationCreate,
  type SubcontractorPortalWorkerRead,
  type SubcontractorWorkerListItem,
  type SubcontractorWorkerQualificationProofUpload,
  type SubcontractorWorkerQualificationRead,
} from "@/api/subcontractorPortal";
import { derivePortalCollectionState } from "@/features/portal/customerPortal.helpers.js";
import {
  derivePortalSubcontractorAccessState,
  mapSubcontractorPortalApiMessage,
} from "@/features/portal/subcontractorPortal.helpers.js";
import { useI18n } from "@/i18n";
import type { MessageKey } from "@/i18n/messages";
import { useAuthStore } from "@/stores/auth";

const authStore = useAuthStore();
const { t } = useI18n();

const tenantCode = ref("");
const identifier = ref("");
const password = ref("");
const deviceLabel = ref("Subcontractor Portal");
const loading = ref(false);
const lastErrorKey = ref("");
const feedbackKey = ref<MessageKey | null>(null);
const feedbackTone = ref<"info" | "success" | "error">("info");
const positions = ref<SubcontractorPortalPositionCollectionRead | null>(null);
const schedules = ref<SubcontractorPortalScheduleCollectionRead | null>(null);
const actuals = ref<SubcontractorPortalActualSummaryCollectionRead | null>(null);
const attendance = ref<SubcontractorPortalAttendanceCollectionRead | null>(null);
const invoiceChecks = ref<SubcontractorPortalInvoiceCheckCollectionRead | null>(null);
const watchbooks = ref<SubcontractorPortalWatchbookCollectionRead | null>(null);
const allocationCandidates = ref<SubcontractorPortalAllocationCandidateCollectionRead | null>(null);
const allocationPreview = ref<SubcontractorPortalAllocationPreviewRead | null>(null);
const allocationResult = ref<SubcontractorPortalAllocationResultRead | null>(null);
const allocationPositionId = ref("");
const allocationWorkerId = ref("");
const allocationAction = ref<SubcontractorPortalAllocationAction>("assign");
const workerList = ref<SubcontractorWorkerListItem[]>([]);
const selectedWorkerId = ref("");
const selectedWorker = ref<SubcontractorPortalWorkerRead | null>(null);
const qualificationTypes = ref<SubcontractorPortalQualificationTypeOptionRead[]>([]);
const selectedQualificationId = ref("");
const qualificationUpload = ref<File | null>(null);
const selectedWatchbookId = ref("");
const watchbookNarrative = ref("");
const isCreatingWorker = ref(false);
const workerForm = reactive({
  worker_no: "",
  first_name: "",
  last_name: "",
  preferred_name: "",
  birth_date: "",
  email: "",
  phone: "",
  mobile: "",
  version_no: 0,
});
const qualificationForm = reactive({
  qualification_type_id: "",
  certificate_no: "",
  issued_at: "",
  valid_until: "",
  issuing_authority: "",
  notes: "",
  version_no: 0,
});

const portalContext = computed(() => authStore.portalSubcontractorContext);
const accessState = computed(() =>
  derivePortalSubcontractorAccessState({
    isLoading: loading.value,
    hasSession: authStore.hasSession,
    hasContext: Boolean(portalContext.value),
    lastErrorKey: lastErrorKey.value,
  }),
);
const portalScopeSummary = computed(() =>
  portalContext.value?.scopes.map((scope) => scope.subcontractor_id).join(", ") ?? "-",
);
const selectedQualification = computed<SubcontractorWorkerQualificationRead | null>(() =>
  selectedWorker.value?.qualifications.find((item) => item.id === selectedQualificationId.value) ?? null,
);
const allocationStatusLabel = computed<MessageKey>(() => {
  const status = allocationResult.value?.command_status ?? allocationPreview.value?.command_status;
  switch (status) {
    case "confirmed":
      return "portalSubcontractor.allocation.status.confirmed";
    case "ready_for_submit":
      return "portalSubcontractor.allocation.status.ready_for_submit";
    case "blocked_by_validation":
      return "portalSubcontractor.allocation.status.blocked_by_validation";
    default:
      return "portalSubcontractor.allocation.status.planning_contract_unavailable";
  }
});
const allocationStatusTone = computed(() => {
  const status = allocationResult.value?.command_status ?? allocationPreview.value?.command_status;
  if (status === "confirmed" || status === "ready_for_submit") {
    return "ready";
  }
  return "pending";
});
const datasets = computed(() => [
  {
    key: "positions",
    eyebrowKey: "portalSubcontractor.datasets.positions.eyebrow",
    titleKey: "portalSubcontractor.datasets.positions.title",
    leadKey: "portalSubcontractor.datasets.positions.lead",
    pendingKey: "portalSubcontractor.datasets.positions.pending",
    sourceModule: "planning",
    collection: positions.value,
    items:
      positions.value?.items.map((item) => ({
        id: item.id,
        label: `${item.reference_no} · ${item.title}`,
      })) ?? [],
  },
  {
    key: "schedules",
    eyebrowKey: "portalSubcontractor.datasets.schedules.eyebrow",
    titleKey: "portalSubcontractor.datasets.schedules.title",
    leadKey: "portalSubcontractor.datasets.schedules.lead",
    pendingKey: "portalSubcontractor.datasets.schedules.pending",
    sourceModule: "planning",
    collection: schedules.value,
    items:
      schedules.value?.items.map((item) => ({
        id: item.id,
        label: `${item.shift_label} · ${item.schedule_date}`,
      })) ?? [],
  },
  {
    key: "actuals",
    eyebrowKey: "portalSubcontractor.datasets.actuals.eyebrow",
    titleKey: "portalSubcontractor.datasets.actuals.title",
    leadKey: "portalSubcontractor.datasets.actuals.lead",
    pendingKey: "portalSubcontractor.datasets.actuals.pending",
    sourceModule: "finance",
    collection: actuals.value,
    items:
      actuals.value?.items.map((item) => ({
        id: item.id,
        label: `${item.period_start} - ${item.period_end} · ${item.status}`,
      })) ?? [],
  },
  {
    key: "attendance",
    eyebrowKey: "portalSubcontractor.datasets.attendance.eyebrow",
    titleKey: "portalSubcontractor.datasets.attendance.title",
    leadKey: "portalSubcontractor.datasets.attendance.lead",
    pendingKey: "portalSubcontractor.datasets.attendance.pending",
    sourceModule: "field_execution",
    collection: attendance.value,
    items:
      attendance.value?.items.map((item) => ({
        id: item.id,
        label: `${item.work_date} · ${item.status}`,
      })) ?? [],
  },
  {
    key: "invoiceChecks",
    eyebrowKey: "portalSubcontractor.datasets.invoiceChecks.eyebrow",
    titleKey: "portalSubcontractor.datasets.invoiceChecks.title",
    leadKey: "portalSubcontractor.datasets.invoiceChecks.lead",
    pendingKey: "portalSubcontractor.datasets.invoiceChecks.pending",
    sourceModule: "finance",
    collection: invoiceChecks.value,
    items:
      invoiceChecks.value?.items.map((item) => ({
        id: item.id,
        label: `${item.period_label} · ${item.status} · ${item.approved_amount ?? "-"} · ${item.submitted_invoice_ref || "-"}`,
      })) ?? [],
  },
]);

function setFeedback(messageKey: MessageKey, tone: "info" | "success" | "error") {
  feedbackKey.value = messageKey;
  feedbackTone.value = tone;
}

function clearFeedback() {
  feedbackKey.value = null;
}

function clearPortalCollections() {
  positions.value = null;
  schedules.value = null;
  actuals.value = null;
  attendance.value = null;
  invoiceChecks.value = null;
  watchbooks.value = null;
  allocationCandidates.value = null;
  allocationPreview.value = null;
  allocationResult.value = null;
  allocationPositionId.value = "";
  allocationWorkerId.value = "";
  allocationAction.value = "assign";
  workerList.value = [];
  selectedWorkerId.value = "";
  selectedWorker.value = null;
  qualificationTypes.value = [];
  selectedQualificationId.value = "";
  qualificationUpload.value = null;
  selectedWatchbookId.value = "";
  watchbookNarrative.value = "";
  isCreatingWorker.value = false;
}

function collectionState(collection: { items: unknown[]; source: { availability_status: string } } | null) {
  return derivePortalCollectionState(collection);
}

function collectionStateKey(state: string): MessageKey {
  switch (state) {
    case "ready":
      return "portalSubcontractor.states.ready";
    case "empty":
      return "portalSubcontractor.states.empty";
    case "pending":
      return "portalSubcontractor.states.pending";
    default:
      return "portalSubcontractor.states.loading";
  }
}

function collectionMessageKey(messageKey: string | undefined, fallback: MessageKey): MessageKey {
  return (messageKey as MessageKey | undefined) ?? fallback;
}

function mapPortalMessage(messageKey: string): MessageKey {
  return mapSubcontractorPortalApiMessage(messageKey);
}

function readinessLabel(status: string): MessageKey {
  switch (status) {
    case "ready":
      return "portalSubcontractor.allocation.readiness.ready";
    case "ready_with_warnings":
      return "portalSubcontractor.allocation.readiness.ready_with_warnings";
    default:
      return "portalSubcontractor.allocation.readiness.not_ready";
  }
}

function ensureAllocationDefaults() {
  if (!allocationPositionId.value && positions.value?.items.length) {
    allocationPositionId.value = positions.value.items[0].id;
  }
  if (!allocationWorkerId.value && allocationCandidates.value?.items.length) {
    allocationWorkerId.value = allocationCandidates.value.items[0].worker_id;
  }
}

function resetWorkerForm(worker?: SubcontractorPortalWorkerRead | null) {
  workerForm.worker_no = worker?.worker_no ?? "";
  workerForm.first_name = worker?.first_name ?? "";
  workerForm.last_name = worker?.last_name ?? "";
  workerForm.preferred_name = worker?.preferred_name ?? "";
  workerForm.birth_date = worker?.birth_date ?? "";
  workerForm.email = worker?.email ?? "";
  workerForm.phone = worker?.phone ?? "";
  workerForm.mobile = worker?.mobile ?? "";
  workerForm.version_no = worker?.version_no ?? 0;
}

function resetQualificationForm(qualification?: SubcontractorWorkerQualificationRead | null) {
  qualificationForm.qualification_type_id = qualification?.qualification_type_id ?? qualificationTypes.value[0]?.id ?? "";
  qualificationForm.certificate_no = qualification?.certificate_no ?? "";
  qualificationForm.issued_at = qualification?.issued_at ?? "";
  qualificationForm.valid_until = qualification?.valid_until ?? "";
  qualificationForm.issuing_authority = qualification?.issuing_authority ?? "";
  qualificationForm.notes = qualification?.notes ?? "";
  qualificationForm.version_no = qualification?.version_no ?? 0;
}

async function loadSelectedWorker(workerId: string) {
  if (!authStore.accessToken) {
    return;
  }
  selectedWorker.value = await getSubcontractorPortalWorker(authStore.accessToken, workerId);
  selectedWorkerId.value = workerId;
  isCreatingWorker.value = false;
  resetWorkerForm(selectedWorker.value);
  selectedQualificationId.value = selectedWorker.value.qualifications[0]?.id ?? "";
  resetQualificationForm(selectedQualification.value);
}

async function loadPortalCollections() {
  if (!authStore.accessToken) {
    clearPortalCollections();
    return;
  }

  const [
    nextPositions,
    nextSchedules,
    nextActuals,
    nextAttendance,
    nextInvoiceChecks,
    nextWatchbooks,
    nextAllocationCandidates,
    nextWorkers,
    nextQualificationTypes,
  ] = await Promise.all([
    getSubcontractorPortalPositions(authStore.accessToken),
    getSubcontractorPortalSchedules(authStore.accessToken),
    getSubcontractorPortalActuals(authStore.accessToken),
    getSubcontractorPortalAttendance(authStore.accessToken),
    getSubcontractorPortalInvoiceChecks(authStore.accessToken),
    getSubcontractorPortalWatchbooks(authStore.accessToken),
    getSubcontractorPortalAllocationCandidates(authStore.accessToken),
    getSubcontractorPortalWorkers(authStore.accessToken),
    getSubcontractorPortalWorkerQualificationTypes(authStore.accessToken),
  ]);
  positions.value = nextPositions;
  schedules.value = nextSchedules;
  actuals.value = nextActuals;
  attendance.value = nextAttendance;
  invoiceChecks.value = nextInvoiceChecks;
  watchbooks.value = nextWatchbooks;
  allocationCandidates.value = nextAllocationCandidates;
  workerList.value = nextWorkers;
  qualificationTypes.value = nextQualificationTypes;
  selectedWatchbookId.value = nextWatchbooks.items[0]?.id ?? "";
  ensureAllocationDefaults();
  if (selectedWorkerId.value && workerList.value.some((item) => item.id === selectedWorkerId.value)) {
    await loadSelectedWorker(selectedWorkerId.value);
  } else if (workerList.value.length) {
    await loadSelectedWorker(workerList.value[0].id);
  } else {
    selectedWorker.value = null;
    selectedWorkerId.value = "";
    resetWorkerForm(null);
    resetQualificationForm(null);
  }
}

function startCreateWorker() {
  isCreatingWorker.value = true;
  selectedWorker.value = null;
  selectedWorkerId.value = "";
  selectedQualificationId.value = "";
  resetWorkerForm(null);
  resetQualificationForm(null);
}

async function saveWorker() {
  if (!authStore.accessToken) {
    return;
  }

  const payload: SubcontractorPortalWorkerCreate = {
    worker_no: workerForm.worker_no,
    first_name: workerForm.first_name,
    last_name: workerForm.last_name,
    preferred_name: workerForm.preferred_name || null,
    birth_date: workerForm.birth_date || null,
    email: workerForm.email || null,
    phone: workerForm.phone || null,
    mobile: workerForm.mobile || null,
  };

  try {
    if (isCreatingWorker.value) {
      const created = await createSubcontractorPortalWorker(authStore.accessToken, payload);
      await loadPortalCollections();
      await loadSelectedWorker(created.id);
    } else if (selectedWorkerId.value) {
      const updated = await updateSubcontractorPortalWorker(authStore.accessToken, selectedWorkerId.value, {
        ...payload,
        version_no: workerForm.version_no,
      });
      await loadPortalCollections();
      await loadSelectedWorker(updated.id);
    }
    setFeedback("portalSubcontractor.feedback.sessionReady", "success");
  } catch (error) {
    const messageKey = error instanceof AuthApiError ? error.messageKey : "errors.platform.internal";
    setFeedback(mapSubcontractorPortalApiMessage(messageKey), "error");
  }
}

async function saveQualification() {
  if (!authStore.accessToken || !selectedWorkerId.value) {
    return;
  }

  const payload: SubcontractorPortalWorkerQualificationCreate = {
    qualification_type_id: qualificationForm.qualification_type_id,
    certificate_no: qualificationForm.certificate_no || null,
    issued_at: qualificationForm.issued_at || null,
    valid_until: qualificationForm.valid_until || null,
    issuing_authority: qualificationForm.issuing_authority || null,
    notes: qualificationForm.notes || null,
  };

  try {
    if (selectedQualification.value) {
      await updateSubcontractorPortalWorkerQualification(
        authStore.accessToken,
        selectedWorkerId.value,
        selectedQualification.value.id,
        {
          ...payload,
          version_no: qualificationForm.version_no,
        },
      );
    } else {
      await createSubcontractorPortalWorkerQualification(authStore.accessToken, selectedWorkerId.value, payload);
    }
    await loadSelectedWorker(selectedWorkerId.value);
    setFeedback("portalSubcontractor.feedback.sessionReady", "success");
  } catch (error) {
    const messageKey = error instanceof AuthApiError ? error.messageKey : "errors.platform.internal";
    setFeedback(mapSubcontractorPortalApiMessage(messageKey), "error");
  }
}

async function submitWatchbookEntry() {
  if (!authStore.accessToken || !selectedWatchbookId.value || !watchbookNarrative.value) {
    return;
  }

  try {
    await createSubcontractorPortalWatchbookEntry(authStore.accessToken, selectedWatchbookId.value, {
      entry_type_code: "subcontractor_note",
      narrative: watchbookNarrative.value,
    });
    watchbookNarrative.value = "";
    await loadPortalCollections();
    setFeedback("portalSubcontractor.feedback.watchbookEntrySubmitted", "success");
  } catch (error) {
    const messageKey = error instanceof AuthApiError ? error.messageKey : "errors.platform.internal";
    setFeedback(mapSubcontractorPortalApiMessage(messageKey), "error");
  }
}

function selectQualification(qualificationId: string) {
  selectedQualificationId.value = qualificationId;
  resetQualificationForm(selectedQualification.value);
}

function onQualificationUploadSelected(event: Event) {
  const input = event.target as HTMLInputElement;
  qualificationUpload.value = input.files?.[0] ?? null;
}

async function uploadQualificationProof() {
  if (!authStore.accessToken || !selectedWorkerId.value || !selectedQualification.value || !qualificationUpload.value) {
    return;
  }
  const file = qualificationUpload.value;
  const payload: SubcontractorWorkerQualificationProofUpload = {
    title: file.name,
    file_name: file.name,
    content_type: file.type || "application/octet-stream",
    content_base64: await file.arrayBuffer().then((buffer) =>
      btoa(Array.from(new Uint8Array(buffer), (byte) => String.fromCharCode(byte)).join("")),
    ),
  };
  try {
    await uploadSubcontractorPortalWorkerQualificationProof(
      authStore.accessToken,
      selectedWorkerId.value,
      selectedQualification.value.id,
      payload,
    );
    qualificationUpload.value = null;
    await loadSelectedWorker(selectedWorkerId.value);
    setFeedback("portalSubcontractor.feedback.sessionReady", "success");
  } catch (error) {
    const messageKey = error instanceof AuthApiError ? error.messageKey : "errors.platform.internal";
    setFeedback(mapSubcontractorPortalApiMessage(messageKey), "error");
  }
}

async function previewAllocation() {
  if (!authStore.accessToken || !allocationPositionId.value || !allocationWorkerId.value) {
    return;
  }

  allocationResult.value = null;
  try {
    allocationPreview.value = await previewSubcontractorPortalAllocation(authStore.accessToken, {
      position_id: allocationPositionId.value,
      worker_id: allocationWorkerId.value,
      action: allocationAction.value,
    });
    setFeedback(
      allocationPreview.value.can_submit
        ? "portalSubcontractor.feedback.sessionReady"
        : mapSubcontractorPortalApiMessage(
            allocationPreview.value.command_status === "blocked_by_validation"
              ? "errors.subcontractors.portal_allocation.blocked_by_validation"
              : "errors.subcontractors.portal_allocation.planning_contract_unavailable",
          ),
      allocationPreview.value.can_submit ? "success" : "info",
    );
  } catch (error) {
    const messageKey = error instanceof AuthApiError ? error.messageKey : "errors.platform.internal";
    setFeedback(mapSubcontractorPortalApiMessage(messageKey), "error");
  }
}

async function submitAllocation() {
  if (!authStore.accessToken || !allocationPositionId.value || !allocationWorkerId.value) {
    return;
  }

  try {
    allocationResult.value = await submitSubcontractorPortalAllocation(authStore.accessToken, {
      position_id: allocationPositionId.value,
      worker_id: allocationWorkerId.value,
      action: allocationAction.value,
    });
    setFeedback(mapSubcontractorPortalApiMessage(allocationResult.value.message_key), "info");
  } catch (error) {
    const messageKey = error instanceof AuthApiError ? error.messageKey : "errors.platform.internal";
    setFeedback(mapSubcontractorPortalApiMessage(messageKey), "error");
  }
}

async function bootstrapPortalContext() {
  if (!authStore.accessToken) {
    clearPortalCollections();
    return;
  }

  loading.value = true;
  clearFeedback();
  try {
    await authStore.loadCurrentSession();
    await authStore.loadSubcontractorPortalContext();
    await loadPortalCollections();
    lastErrorKey.value = "";
    setFeedback("portalSubcontractor.feedback.sessionReady", "success");
  } catch (error) {
    clearPortalCollections();
    const messageKey = error instanceof AuthApiError ? error.messageKey : "errors.platform.internal";
    lastErrorKey.value = messageKey;
    setFeedback(mapSubcontractorPortalApiMessage(messageKey), "error");
  } finally {
    loading.value = false;
  }
}

async function submitLogin() {
  loading.value = true;
  clearFeedback();
  authStore.clearPortalSubcontractorContext();
  clearPortalCollections();
  try {
    await authStore.loginCustomerPortal({
      tenant_code: tenantCode.value,
      identifier: identifier.value,
      password: password.value,
      device_label: deviceLabel.value || null,
    });
    await authStore.loadSubcontractorPortalContext();
    await loadPortalCollections();
    password.value = "";
    lastErrorKey.value = "";
    setFeedback("portalSubcontractor.feedback.sessionReady", "success");
  } catch (error) {
    const messageKey = error instanceof AuthApiError ? error.messageKey : "errors.platform.internal";
    lastErrorKey.value = messageKey;
    setFeedback(mapSubcontractorPortalApiMessage(messageKey), "error");
  } finally {
    loading.value = false;
  }
}

async function refreshPortalContext() {
  await bootstrapPortalContext();
}

async function logoutPortalSession() {
  loading.value = true;
  try {
    await authStore.logoutSession();
    clearPortalCollections();
    lastErrorKey.value = "";
    setFeedback("portalSubcontractor.feedback.loggedOut", "info");
  } finally {
    loading.value = false;
  }
}

onMounted(async () => {
  if (authStore.accessToken) {
    await bootstrapPortalContext();
  }
});
</script>

<style scoped>
.portal-subcontractor-view,
.portal-stack,
.portal-login-grid,
.portal-summary-grid,
.portal-dataset-grid {
  display: grid;
  gap: 1rem;
}

.portal-subcontractor-header,
.portal-dataset-header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: start;
}

.portal-actions,
.portal-login-actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.portal-login-grid,
.portal-summary-grid,
.portal-dataset-grid {
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
}

.portal-feedback {
  margin: 0;
  padding: 0.85rem 1rem;
  border-radius: 0.85rem;
  background: var(--sp-surface-muted);
  color: var(--sp-text-strong);
}

.portal-feedback[data-tone="error"] {
  background: color-mix(in srgb, #d94f4f 14%, var(--sp-surface-muted));
}

.portal-feedback[data-tone="success"] {
  background: color-mix(in srgb, var(--sp-primary) 18%, var(--sp-surface-muted));
}

.field {
  display: grid;
  gap: 0.45rem;
}

.field input {
  border: 1px solid var(--sp-border);
  border-radius: 0.85rem;
  padding: 0.85rem 0.95rem;
  background: var(--sp-surface-elevated);
  color: var(--sp-text-strong);
}

.field select {
  border: 1px solid var(--sp-border);
  border-radius: 0.85rem;
  padding: 0.85rem 0.95rem;
  background: var(--sp-surface-elevated);
  color: var(--sp-text-strong);
}

.portal-state-card,
.portal-summary-card,
.portal-dataset-card {
  padding: 1.15rem;
  border-radius: 1rem;
  background: var(--sp-surface-elevated);
  border: 1px solid var(--sp-border);
}

.portal-dataset-card {
  display: grid;
  gap: 0.75rem;
}

.allocation-panel {
  display: grid;
  gap: 0.6rem;
}

.worker-select-button {
  justify-content: flex-start;
  text-align: left;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 0.3rem 0.65rem;
  font-size: 0.76rem;
  font-weight: 700;
  background: color-mix(in srgb, #d8a846 18%, var(--sp-surface-muted));
  color: var(--sp-text-strong);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.dataset-meta {
  margin: 0;
  color: var(--sp-text-muted);
}

.portal-flags {
  margin: 0;
  padding-left: 1.1rem;
  display: grid;
  gap: 0.45rem;
}

dl {
  display: grid;
  gap: 0.8rem;
  margin: 0;
}

dt {
  font-size: 0.78rem;
  text-transform: uppercase;
  color: var(--sp-text-muted);
  letter-spacing: 0.08em;
}

dd {
  margin: 0.2rem 0 0;
  font-weight: 600;
}

@media (max-width: 720px) {
  .portal-subcontractor-header,
  .portal-dataset-header {
    flex-direction: column;
  }
}
</style>
