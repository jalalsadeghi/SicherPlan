<template>
  <section class="recruiting-page">
    <section class="module-card recruiting-hero">
      <div>
        <p class="eyebrow">{{ t("recruitingAdmin.eyebrow") }}</p>
        <h2>{{ t("recruitingAdmin.title") }}</h2>
        <p class="recruiting-lead">{{ t("recruitingAdmin.lead") }}</p>
        <div class="recruiting-meta">
          <span class="recruiting-meta__pill">
            {{ t("recruitingAdmin.permission.read") }}: {{ canRead ? "on" : "off" }}
          </span>
          <span class="recruiting-meta__pill">
            {{ t("recruitingAdmin.permission.write") }}: {{ canWrite ? "on" : "off" }}
          </span>
          <span class="recruiting-meta__pill">
            {{ t("recruitingAdmin.permission.docs") }}: {{ canReadDocs ? "on" : "off" }}
          </span>
        </div>
      </div>

      <div class="module-card recruiting-scope">
        <label class="field-stack">
          <span>{{ t("recruitingAdmin.scope.label") }}</span>
          <input
            v-model="tenantScopeInput"
            :disabled="!isPlatformAdmin"
            :placeholder="t('recruitingAdmin.scope.placeholder')"
          />
        </label>
        <p class="field-help">
          {{ isPlatformAdmin ? t("recruitingAdmin.scope.platformHelp") : t("recruitingAdmin.scope.sessionHelp") }}
        </p>
        <div class="cta-row">
          <button class="cta-button" type="button" :disabled="!isPlatformAdmin" @click="rememberScope">
            {{ t("recruitingAdmin.actions.rememberScope") }}
          </button>
          <button class="cta-button cta-secondary" type="button" @click="refreshApplicants">
            {{ t("recruitingAdmin.actions.refresh") }}
          </button>
        </div>
      </div>
    </section>

    <section v-if="feedback.message" class="recruiting-feedback" :data-tone="feedback.tone">
      <div>
        <strong>{{ feedback.title }}</strong>
        <span>{{ feedback.message }}</span>
      </div>
      <button type="button" @click="clearFeedback">{{ t("recruitingAdmin.actions.clearFeedback") }}</button>
    </section>

    <section v-if="!authStore.hasSession" class="module-card recruiting-empty">
      <p class="eyebrow">{{ t("recruitingAdmin.auth.missingTitle") }}</p>
      <h3>{{ t("recruitingAdmin.auth.missingBody") }}</h3>
    </section>

    <section v-else-if="!canAccess" class="module-card recruiting-empty">
      <p class="eyebrow">{{ t("recruitingAdmin.permission.missingTitle") }}</p>
      <h3>{{ t("recruitingAdmin.permission.missingBody") }}</h3>
    </section>

    <section v-else-if="!resolvedTenantScopeId" class="module-card recruiting-empty">
      <p class="eyebrow">{{ t("recruitingAdmin.scope.missingTitle") }}</p>
      <h3>{{ t("recruitingAdmin.scope.missingBody") }}</h3>
    </section>

    <div v-else class="recruiting-grid">
      <section class="module-card recruiting-panel">
        <div class="recruiting-panel__header">
          <div>
            <p class="eyebrow">{{ t("recruitingAdmin.list.eyebrow") }}</p>
            <h3>{{ t("recruitingAdmin.list.title") }}</h3>
          </div>
          <StatusBadge :status="loading.list ? 'inactive' : 'active'" />
        </div>

        <div class="recruiting-form-grid">
          <label class="field-stack">
            <span>{{ t("recruitingAdmin.filters.search") }}</span>
            <input v-model="filters.search" :placeholder="t('recruitingAdmin.filters.searchPlaceholder')" />
          </label>
          <label class="field-stack">
            <span>{{ t("recruitingAdmin.filters.status") }}</span>
            <select v-model="filters.status">
              <option value="">{{ t("recruitingAdmin.filters.allStatuses") }}</option>
              <option v-for="status in statusOptions" :key="status" :value="status">
                {{ statusLabel(status) }}
              </option>
            </select>
          </label>
          <label class="field-stack">
            <span>{{ t("recruitingAdmin.filters.sourceChannel") }}</span>
            <select v-model="filters.source_channel">
              <option value="">{{ t("recruitingAdmin.filters.allSources") }}</option>
              <option v-for="source in sourceOptions" :key="source" :value="source">
                {{ sourceLabel(source) }}
              </option>
            </select>
          </label>
        </div>

        <div class="cta-row">
          <button class="cta-button" type="button" @click="refreshApplicants">
            {{ t("recruitingAdmin.actions.search") }}
          </button>
        </div>

        <div v-if="applicants.length" class="recruiting-list">
          <button
            v-for="applicant in applicants"
            :key="applicant.id"
            type="button"
            class="recruiting-row"
            :class="{ selected: applicant.id === selectedApplicantId }"
            @click="selectApplicant(applicant.id)"
          >
            <div>
              <strong>{{ formatApplicantLabel(applicant) }}</strong>
              <span>{{ applicant.application_no }} · {{ applicant.email }}</span>
              <small>{{ sourceLabel(applicant.source_channel) }} · {{ formatDateTime(applicant.created_at) }}</small>
            </div>
            <StatusBadge :status="applicant.status" />
          </button>
        </div>
        <p v-else class="recruiting-list-empty">{{ t("recruitingAdmin.list.empty") }}</p>
      </section>

      <section class="module-card recruiting-panel recruiting-detail">
        <div class="recruiting-panel__header">
          <div>
            <p class="eyebrow">{{ t("recruitingAdmin.detail.eyebrow") }}</p>
            <h3>{{ selectedDetail ? formatApplicantLabel(selectedDetail.applicant) : t("recruitingAdmin.detail.emptyTitle") }}</h3>
          </div>
          <StatusBadge v-if="selectedDetail" :status="selectedDetail.applicant.status" />
        </div>

        <template v-if="selectedDetail">
          <div class="recruiting-summary">
            <article class="recruiting-summary__card">
              <span>{{ t("recruitingAdmin.summary.applicationNo") }}</span>
              <strong>{{ selectedDetail.applicant.application_no }}</strong>
            </article>
            <article class="recruiting-summary__card">
              <span>{{ t("recruitingAdmin.summary.desiredRole") }}</span>
              <strong>{{ selectedDetail.applicant.desired_role || t("recruitingAdmin.summary.none") }}</strong>
            </article>
            <article class="recruiting-summary__card">
              <span>{{ t("recruitingAdmin.summary.availability") }}</span>
              <strong>{{ formatDate(selectedDetail.applicant.availability_date) || t("recruitingAdmin.summary.none") }}</strong>
            </article>
            <article class="recruiting-summary__card">
              <span>{{ t("recruitingAdmin.summary.source") }}</span>
              <strong>{{ sourceLabel(selectedDetail.applicant.source_channel) }}</strong>
            </article>
            <article class="recruiting-summary__card">
              <span>{{ t("recruitingAdmin.summary.employeeFile") }}</span>
              <strong>{{ selectedDetail.applicant.converted_employee_id || t("recruitingAdmin.summary.none") }}</strong>
            </article>
          </div>

          <section class="recruiting-section">
            <div class="recruiting-panel__header">
              <div>
                <p class="eyebrow">{{ t("recruitingAdmin.detail.submissionEyebrow") }}</p>
                <h3>{{ t("recruitingAdmin.detail.submissionTitle") }}</h3>
              </div>
            </div>
            <div class="recruiting-form-grid">
              <label class="field-stack">
                <span>{{ t("recruitingAdmin.fields.fullName") }}</span>
                <input :value="formatApplicantLabel(selectedDetail.applicant)" disabled />
              </label>
              <label class="field-stack">
                <span>{{ t("recruitingAdmin.fields.email") }}</span>
                <input :value="selectedDetail.applicant.email" disabled />
              </label>
              <label class="field-stack">
                <span>{{ t("recruitingAdmin.fields.phone") }}</span>
                <input :value="selectedDetail.applicant.phone || ''" disabled />
              </label>
              <label class="field-stack">
                <span>{{ t("recruitingAdmin.fields.locale") }}</span>
                <input :value="selectedDetail.applicant.locale" disabled />
              </label>
              <label class="field-stack field-stack--wide">
                <span>{{ t("recruitingAdmin.fields.message") }}</span>
                <textarea :value="selectedDetail.applicant.message || ''" rows="4" disabled />
              </label>
            </div>
          </section>

          <section class="recruiting-section">
            <div class="recruiting-panel__header">
              <div>
                <p class="eyebrow">{{ t("recruitingAdmin.consent.eyebrow") }}</p>
                <h3>{{ t("recruitingAdmin.consent.title") }}</h3>
              </div>
            </div>
            <div class="recruiting-form-grid">
              <label class="field-stack">
                <span>{{ t("recruitingAdmin.consent.granted") }}</span>
                <input :value="selectedDetail.consent.consent_granted ? t('recruitingAdmin.common.yes') : t('recruitingAdmin.common.no')" disabled />
              </label>
              <label class="field-stack">
                <span>{{ t("recruitingAdmin.consent.timestamp") }}</span>
                <input :value="formatDateTime(selectedDetail.consent.consent_at)" disabled />
              </label>
              <label class="field-stack">
                <span>{{ t("recruitingAdmin.consent.policyRef") }}</span>
                <input :value="selectedDetail.consent.policy_ref" disabled />
              </label>
              <label class="field-stack">
                <span>{{ t("recruitingAdmin.consent.policyVersion") }}</span>
                <input :value="selectedDetail.consent.policy_version" disabled />
              </label>
              <label class="field-stack">
                <span>{{ t("recruitingAdmin.consent.origin") }}</span>
                <input :value="selectedDetail.consent.submitted_origin || ''" disabled />
              </label>
              <label class="field-stack">
                <span>{{ t("recruitingAdmin.consent.ip") }}</span>
                <input :value="selectedDetail.consent.submitted_ip || ''" disabled />
              </label>
            </div>
          </section>

          <section class="recruiting-section">
            <div class="recruiting-panel__header">
              <div>
                <p class="eyebrow">{{ t("recruitingAdmin.attachments.eyebrow") }}</p>
                <h3>{{ t("recruitingAdmin.attachments.title") }}</h3>
              </div>
            </div>
            <div v-if="selectedDetail.attachments.length" class="recruiting-list">
              <article v-for="attachment in selectedDetail.attachments" :key="attachment.document_id" class="recruiting-attachment">
                <div>
                  <strong>{{ attachment.label || attachment.title }}</strong>
                  <span>{{ attachment.file_name || t("recruitingAdmin.summary.none") }}</span>
                  <small>{{ attachment.document_type_key || attachment.relation_type }}</small>
                </div>
                <div class="cta-row">
                  <button
                    class="cta-button cta-secondary"
                    type="button"
                    :disabled="!canReadDocs || !attachment.current_version_no"
                    @click="openAttachment(attachment, 'preview')"
                  >
                    {{ t("recruitingAdmin.actions.previewAttachment") }}
                  </button>
                  <button
                    class="cta-button"
                    type="button"
                    :disabled="!canReadDocs || !attachment.current_version_no"
                    @click="openAttachment(attachment, 'download')"
                  >
                    {{ t("recruitingAdmin.actions.downloadAttachment") }}
                  </button>
                </div>
              </article>
            </div>
            <p v-else class="recruiting-list-empty">{{ t("recruitingAdmin.attachments.empty") }}</p>
          </section>

          <section class="recruiting-section">
            <div class="recruiting-panel__header">
              <div>
                <p class="eyebrow">{{ t("recruitingAdmin.actions.transitionEyebrow") }}</p>
                <h3>{{ t("recruitingAdmin.actions.transitionTitle") }}</h3>
              </div>
            </div>
            <div class="cta-row recruiting-actions">
              <button
                v-for="action in nextActions"
                :key="action.status"
                class="cta-button"
                type="button"
                :class="{ 'cta-secondary': transitionDraft.to_status !== action.status }"
                :disabled="!canWrite"
                @click="selectTransition(action.status)"
              >
                {{ statusLabel(action.status) }}
              </button>
            </div>
            <form class="recruiting-form-grid" @submit.prevent="submitTransition">
              <label class="field-stack">
                <span>{{ t("recruitingAdmin.fields.nextStatus") }}</span>
                <input :value="transitionDraft.to_status ? statusLabel(transitionDraft.to_status) : ''" disabled />
              </label>
              <label v-if="requiresInterviewSchedule" class="field-stack">
                <span>{{ t("recruitingAdmin.fields.interviewScheduledAt") }}</span>
                <input v-model="transitionDraft.interview_scheduled_at" type="datetime-local" />
              </label>
              <label v-if="requiresHiringTargetDate" class="field-stack">
                <span>{{ t("recruitingAdmin.fields.hiringTargetDate") }}</span>
                <input v-model="transitionDraft.hiring_target_date" type="date" />
              </label>
              <label v-if="requiresDecisionReason" class="field-stack field-stack--wide">
                <span>{{ t("recruitingAdmin.fields.decisionReason") }}</span>
                <textarea v-model="transitionDraft.decision_reason" rows="3" />
              </label>
              <label class="field-stack field-stack--wide">
                <span>{{ t("recruitingAdmin.fields.note") }}</span>
                <textarea v-model="transitionDraft.note" rows="3" />
              </label>
              <div class="cta-row">
                <button class="cta-button" type="submit" :disabled="!canWrite || !transitionDraft.to_status || loading.action">
                  {{ t("recruitingAdmin.actions.applyTransition") }}
                </button>
              </div>
            </form>
          </section>

          <section class="recruiting-section">
            <div class="recruiting-panel__header">
              <div>
                <p class="eyebrow">{{ t("recruitingAdmin.notes.eyebrow") }}</p>
                <h3>{{ t("recruitingAdmin.notes.title") }}</h3>
              </div>
            </div>
            <form class="recruiting-form-grid" @submit.prevent="submitActivity">
              <label class="field-stack">
                <span>{{ t("recruitingAdmin.fields.activityType") }}</span>
                <select v-model="activityDraft.activity_type">
                  <option value="recruiter_note">{{ t("recruitingAdmin.activity.recruiterNote") }}</option>
                  <option value="interview_note">{{ t("recruitingAdmin.activity.interviewNote") }}</option>
                </select>
              </label>
              <label v-if="activityDraft.activity_type === 'interview_note'" class="field-stack">
                <span>{{ t("recruitingAdmin.fields.interviewScheduledAt") }}</span>
                <input v-model="activityDraft.interview_scheduled_at" type="datetime-local" />
              </label>
              <label class="field-stack field-stack--wide">
                <span>{{ t("recruitingAdmin.fields.note") }}</span>
                <textarea v-model="activityDraft.note" rows="3" />
              </label>
              <div class="cta-row">
                <button class="cta-button" type="submit" :disabled="!canWrite || loading.action">
                  {{ t("recruitingAdmin.actions.addNote") }}
                </button>
              </div>
            </form>
          </section>

          <section class="recruiting-section">
            <div class="recruiting-panel__header">
              <div>
                <p class="eyebrow">{{ t("recruitingAdmin.timeline.eyebrow") }}</p>
                <h3>{{ t("recruitingAdmin.timeline.title") }}</h3>
              </div>
            </div>
            <div v-if="selectedDetail.events.length" class="recruiting-timeline">
              <article v-for="event in selectedDetail.events" :key="event.id" class="recruiting-timeline__entry">
                <div>
                  <strong>{{ eventLabel(event.event_type) }}</strong>
                  <p>{{ formatTimelineBody(event) }}</p>
                </div>
                <small>{{ formatDateTime(event.created_at) }}</small>
              </article>
            </div>
            <p v-else class="recruiting-list-empty">{{ t("recruitingAdmin.timeline.empty") }}</p>
          </section>
        </template>

        <section v-else class="recruiting-empty">
          <p class="eyebrow">{{ t("recruitingAdmin.detail.emptyEyebrow") }}</p>
          <h3>{{ t("recruitingAdmin.detail.emptyBody") }}</h3>
        </section>
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";

import {
  addApplicantActivity,
  downloadApplicantAttachment,
  getApplicantDetail,
  listApplicants,
  RecruitingAdminApiError,
  transitionApplicant,
  type ApplicantActivityEventRead,
  type ApplicantAttachmentRead,
  type ApplicantDetailRead,
  type ApplicantListItem,
} from "@/api/recruitingAdmin";
import StatusBadge from "@/components/StatusBadge.vue";
import { useI18n } from "@/i18n";
import {
  canAccessRecruitingAdmin,
  deriveNextActionDescriptors,
  formatApplicantLabel,
  hasRecruitingPermission,
  mapRecruitingApiMessage,
  requiresTransitionConfirmation,
} from "@/features/recruiting/recruitingAdmin.helpers.js";
import { useAuthStore } from "@/stores/auth";

const { t } = useI18n();
const authStore = useAuthStore();

const statusOptions = ["submitted", "in_review", "interview_scheduled", "accepted", "rejected", "ready_for_conversion"];
const sourceOptions = ["public_form"];

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
  source_channel: "",
});

const tenantScopeInput = ref(authStore.effectiveTenantScopeId || authStore.tenantScopeId || "");
const applicants = ref<ApplicantListItem[]>([]);
const selectedApplicantId = ref("");
const selectedDetail = ref<ApplicantDetailRead | null>(null);

const transitionDraft = reactive({
  to_status: "",
  note: "",
  decision_reason: "",
  interview_scheduled_at: "",
  hiring_target_date: "",
});

const activityDraft = reactive({
  activity_type: "recruiter_note" as "recruiter_note" | "interview_note",
  note: "",
  interview_scheduled_at: "",
});

const effectiveRole = computed(() => authStore.effectiveRole);
const isPlatformAdmin = computed(() => effectiveRole.value === "platform_admin");
const canRead = computed(() => hasRecruitingPermission(effectiveRole.value, "recruiting.applicant.read"));
const canWrite = computed(() => hasRecruitingPermission(effectiveRole.value, "recruiting.applicant.write"));
const canReadDocs = computed(() => hasRecruitingPermission(effectiveRole.value, "platform.docs.read"));
const canAccess = computed(() => canAccessRecruitingAdmin(effectiveRole.value, authStore.hasSession));
const resolvedTenantScopeId = computed(() => authStore.effectiveTenantScopeId);
const nextActions = computed(() => deriveNextActionDescriptors(selectedDetail.value?.next_allowed_statuses ?? []));
const requiresDecisionReason = computed(
  () => transitionDraft.to_status === "accepted" || transitionDraft.to_status === "rejected",
);
const requiresInterviewSchedule = computed(() => transitionDraft.to_status === "interview_scheduled");
const requiresHiringTargetDate = computed(() => transitionDraft.to_status === "ready_for_conversion");

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
  if (!isPlatformAdmin.value) {
    return;
  }
  authStore.setTenantScopeId(tenantScopeInput.value);
  void refreshApplicants();
}

function statusLabel(status: string) {
  return t(`recruitingAdmin.status.${status}` as never);
}

function sourceLabel(sourceChannel: string) {
  return t(`recruitingAdmin.source.${sourceChannel}` as never);
}

function eventLabel(eventType: string) {
  return t(`recruitingAdmin.event.${eventType}` as never);
}

function formatDate(value: string | null | undefined) {
  if (!value) return "";
  return new Intl.DateTimeFormat("de-DE", { dateStyle: "medium" }).format(new Date(value));
}

function formatDateTime(value: string | null | undefined) {
  if (!value) return "";
  return new Intl.DateTimeFormat("de-DE", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

function formatTimelineBody(event: ApplicantActivityEventRead) {
  const metadata = event.metadata_json ?? {};
  const convertedEmployeeId =
    typeof metadata.employee_id === "string" && metadata.employee_id ? metadata.employee_id : null;
  const convertedPersonnelNo =
    typeof metadata.personnel_no === "string" && metadata.personnel_no ? metadata.personnel_no : null;
  const fragments = [
    event.from_status && event.to_status && event.from_status !== event.to_status
      ? `${statusLabel(event.from_status)} -> ${statusLabel(event.to_status)}`
      : null,
    event.note,
    event.decision_reason,
    event.interview_scheduled_at ? formatDateTime(event.interview_scheduled_at) : null,
    event.hiring_target_date ? formatDate(event.hiring_target_date) : null,
    convertedPersonnelNo,
    convertedEmployeeId,
  ].filter(Boolean);

  return fragments.join(" · ");
}

function confirmTransition(status: string) {
  if (!requiresTransitionConfirmation(status)) {
    return true;
  }
  const messageKey =
    status === "accepted"
      ? "recruitingAdmin.confirm.accepted"
      : "recruitingAdmin.confirm.rejected";
  return window.confirm(t(messageKey as never));
}

function resetTransitionDraft() {
  transitionDraft.to_status = "";
  transitionDraft.note = "";
  transitionDraft.decision_reason = "";
  transitionDraft.interview_scheduled_at = "";
  transitionDraft.hiring_target_date = "";
}

function resetActivityDraft() {
  activityDraft.activity_type = "recruiter_note";
  activityDraft.note = "";
  activityDraft.interview_scheduled_at = "";
}

function selectTransition(status: string) {
  transitionDraft.to_status = status;
  if (status !== "interview_scheduled") {
    transitionDraft.interview_scheduled_at = "";
  }
  if (status !== "ready_for_conversion") {
    transitionDraft.hiring_target_date = "";
  }
  if (status !== "accepted" && status !== "rejected") {
    transitionDraft.decision_reason = "";
  }
}

async function refreshApplicants() {
  const tenantId = resolvedTenantScopeId.value;
  const accessToken = authStore.accessToken;
  if (!tenantId || !accessToken || !canRead.value) {
    applicants.value = [];
    selectedDetail.value = null;
    selectedApplicantId.value = "";
    return;
  }

  loading.list = true;
  try {
    applicants.value = await listApplicants(tenantId, accessToken, {
      search: filters.search || undefined,
      status: filters.status || undefined,
      source_channel: filters.source_channel || undefined,
    });
    if (selectedApplicantId.value) {
      const stillSelected = applicants.value.some((item) => item.id === selectedApplicantId.value);
      if (!stillSelected) {
        selectedApplicantId.value = "";
        selectedDetail.value = null;
      }
    }
    if (!selectedApplicantId.value && applicants.value.length > 0) {
      await selectApplicant(applicants.value[0].id);
    }
  } catch (error) {
    const key = error instanceof RecruitingAdminApiError ? mapRecruitingApiMessage(error.messageKey) : "recruitingAdmin.feedback.error";
    setFeedback("error", t("recruitingAdmin.feedback.titleError"), t(key as never));
  } finally {
    loading.list = false;
  }
}

async function selectApplicant(applicantId: string) {
  const tenantId = resolvedTenantScopeId.value;
  const accessToken = authStore.accessToken;
  if (!tenantId || !accessToken) {
    return;
  }

  selectedApplicantId.value = applicantId;
  loading.detail = true;
  try {
    selectedDetail.value = await getApplicantDetail(tenantId, applicantId, accessToken);
    resetTransitionDraft();
    resetActivityDraft();
  } catch (error) {
    const key = error instanceof RecruitingAdminApiError ? mapRecruitingApiMessage(error.messageKey) : "recruitingAdmin.feedback.error";
    setFeedback("error", t("recruitingAdmin.feedback.titleError"), t(key as never));
  } finally {
    loading.detail = false;
  }
}

async function submitTransition() {
  if (!selectedApplicantId.value || !resolvedTenantScopeId.value || !authStore.accessToken || !transitionDraft.to_status) {
    return;
  }
  if (!confirmTransition(transitionDraft.to_status)) {
    return;
  }

  loading.action = true;
  try {
    await transitionApplicant(resolvedTenantScopeId.value, selectedApplicantId.value, authStore.accessToken, {
      to_status: transitionDraft.to_status,
      note: transitionDraft.note || null,
      decision_reason: transitionDraft.decision_reason || null,
      interview_scheduled_at: transitionDraft.interview_scheduled_at
        ? new Date(transitionDraft.interview_scheduled_at).toISOString()
        : null,
      hiring_target_date: transitionDraft.hiring_target_date || null,
    });
    await selectApplicant(selectedApplicantId.value);
    await refreshApplicants();
    setFeedback("success", t("recruitingAdmin.feedback.titleSuccess"), t("recruitingAdmin.feedback.transitionSaved"));
  } catch (error) {
    const key = error instanceof RecruitingAdminApiError ? mapRecruitingApiMessage(error.messageKey) : "recruitingAdmin.feedback.error";
    setFeedback("error", t("recruitingAdmin.feedback.titleError"), t(key as never));
  } finally {
    loading.action = false;
  }
}

async function submitActivity() {
  if (!selectedApplicantId.value || !resolvedTenantScopeId.value || !authStore.accessToken) {
    return;
  }

  loading.action = true;
  try {
    await addApplicantActivity(resolvedTenantScopeId.value, selectedApplicantId.value, authStore.accessToken, {
      activity_type: activityDraft.activity_type,
      note: activityDraft.note,
      interview_scheduled_at: activityDraft.interview_scheduled_at
        ? new Date(activityDraft.interview_scheduled_at).toISOString()
        : null,
    });
    await selectApplicant(selectedApplicantId.value);
    setFeedback("success", t("recruitingAdmin.feedback.titleSuccess"), t("recruitingAdmin.feedback.noteSaved"));
  } catch (error) {
    const key = error instanceof RecruitingAdminApiError ? mapRecruitingApiMessage(error.messageKey) : "recruitingAdmin.feedback.error";
    setFeedback("error", t("recruitingAdmin.feedback.titleError"), t(key as never));
  } finally {
    loading.action = false;
  }
}

function triggerBlobDownload(blob: Blob, fileName: string) {
  const url = URL.createObjectURL(blob);
  const anchor = window.document.createElement("a");
  anchor.href = url;
  anchor.download = fileName;
  anchor.click();
  URL.revokeObjectURL(url);
}

async function openAttachment(attachment: ApplicantAttachmentRead, mode: "download" | "preview") {
  if (!resolvedTenantScopeId.value || !authStore.accessToken || !attachment.current_version_no) {
    return;
  }

  try {
    const file = await downloadApplicantAttachment(
      resolvedTenantScopeId.value,
      attachment.document_id,
      attachment.current_version_no,
      authStore.accessToken,
    );
    if (mode === "preview" && (file.contentType.includes("pdf") || file.contentType.startsWith("image/"))) {
      const url = URL.createObjectURL(file.blob);
      window.open(url, "_blank", "noopener,noreferrer");
      return;
    }
    triggerBlobDownload(file.blob, file.fileName);
  } catch (error) {
    const key = error instanceof RecruitingAdminApiError ? mapRecruitingApiMessage(error.messageKey) : "recruitingAdmin.feedback.error";
    setFeedback("error", t("recruitingAdmin.feedback.titleError"), t(key as never));
  }
}

onMounted(async () => {
  if (authStore.accessToken && !authStore.sessionUser) {
    try {
      await authStore.loadCurrentSession();
    } catch {
      // session fallback is handled by the store
    }
  }
  if (!isPlatformAdmin.value) {
    tenantScopeInput.value = authStore.effectiveTenantScopeId || authStore.tenantScopeId;
  }
  await refreshApplicants();
});
</script>

<style scoped>
.recruiting-page,
.recruiting-grid,
.recruiting-list,
.recruiting-timeline,
.recruiting-form-grid {
  display: grid;
  gap: 1rem;
}

.recruiting-grid {
  grid-template-columns: minmax(320px, 0.9fr) minmax(420px, 1.3fr);
  align-items: start;
}

.recruiting-hero {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: start;
}

.recruiting-scope,
.recruiting-empty,
.recruiting-panel,
.recruiting-section {
  display: grid;
  gap: 1rem;
}

.recruiting-meta,
.recruiting-summary,
.recruiting-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.recruiting-meta__pill,
.recruiting-summary__card {
  padding: 0.75rem 1rem;
  border-radius: 16px;
  background: var(--sp-color-surface-page);
  border: 1px solid var(--sp-color-border-soft);
}

.recruiting-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}

.recruiting-summary__card {
  display: grid;
  gap: 0.35rem;
}

.recruiting-panel__header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: start;
}

.recruiting-row,
.recruiting-attachment,
.recruiting-timeline__entry {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: center;
  padding: 1rem;
  border-radius: 16px;
  border: 1px solid var(--sp-color-border-soft);
  background: var(--sp-color-surface-page);
}

.recruiting-row {
  text-align: left;
}

.recruiting-row.selected {
  border-color: var(--sp-color-primary);
  box-shadow: 0 0 0 1px var(--sp-color-primary-muted);
}

.recruiting-feedback {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.9rem 1rem;
  border-radius: 16px;
  background: var(--sp-color-primary-muted);
  color: var(--sp-color-primary-strong);
}

.recruiting-feedback[data-tone="error"] {
  background: color-mix(in srgb, #c84d3a 18%, var(--sp-color-surface-panel));
  color: #8b2417;
}

.recruiting-feedback[data-tone="success"] {
  background: color-mix(in srgb, #2f8f67 18%, var(--sp-color-surface-panel));
  color: #17674a;
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

.recruiting-lead,
.recruiting-row span,
.recruiting-row small,
.recruiting-timeline__entry p {
  margin: 0.35rem 0 0 0;
  color: var(--sp-color-text-secondary);
}

@media (max-width: 1100px) {
  .recruiting-grid {
    grid-template-columns: 1fr;
  }

  .recruiting-hero,
  .recruiting-row,
  .recruiting-attachment,
  .recruiting-timeline__entry,
  .recruiting-feedback {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
