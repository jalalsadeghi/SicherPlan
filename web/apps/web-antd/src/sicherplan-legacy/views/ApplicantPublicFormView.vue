<template>
  <section class="applicant-public-page">
    <section class="module-card applicant-public-shell">
      <div class="applicant-public-header">
        <p class="eyebrow">{{ t("recruitingApplicant.eyebrow") }}</p>
        <h2>{{ config?.tenant_name || t("recruitingApplicant.title") }}</h2>
        <p class="applicant-public-lead">{{ t("recruitingApplicant.lead") }}</p>
        <p class="applicant-public-meta">
          {{ embedded ? t("recruitingApplicant.embed.embedded") : t("recruitingApplicant.embed.standalone") }}
        </p>
      </div>

      <section v-if="loading" class="module-card applicant-public-state">
        <h3>{{ t("recruitingApplicant.loading.title") }}</h3>
        <p>{{ t("recruitingApplicant.loading.body") }}</p>
      </section>

      <section v-else-if="loadError" class="module-card applicant-public-state applicant-public-state--error">
        <h3>{{ t("recruitingApplicant.error.title") }}</h3>
        <p>{{ loadError }}</p>
      </section>

      <section v-else-if="submitted" class="module-card applicant-public-state applicant-public-state--success">
        <p class="eyebrow">{{ t("recruitingApplicant.success.eyebrow") }}</p>
        <h3>{{ t("recruitingApplicant.success.title") }}</h3>
        <p>{{ t("recruitingApplicant.success.body") }}</p>
        <strong>{{ submitted.application_no }}</strong>
      </section>

      <form v-else-if="config" class="applicant-public-form" @submit.prevent="submitForm">
        <div class="applicant-public-grid">
          <label v-for="field in config.fields" :key="field.key" class="field-stack" :class="{ 'field-stack--wide': field.type === 'textarea' }">
            <span>{{ fieldLabel(field) }}<span v-if="field.required"> *</span></span>

            <select
              v-if="field.type === 'select'"
              v-model="fieldValues[field.key]"
            >
              <option value="">{{ t("recruitingApplicant.fields.selectPlaceholder") }}</option>
              <option v-for="option in field.options" :key="option.value" :value="option.value">
                {{ locale === "de" ? option.label_de : option.label_en }}
              </option>
            </select>

            <textarea
              v-else-if="field.type === 'textarea'"
              v-model="fieldValues[field.key]"
              rows="4"
            />

            <input
              v-else
              v-model="fieldValues[field.key]"
              :type="inputType(field.type)"
            />
          </label>
        </div>

        <label class="field-stack field-stack--wide">
          <span>{{ t("recruitingApplicant.fields.attachments") }}</span>
          <input
            type="file"
            multiple
            :accept="config.allowed_attachment_types.join(',')"
            @change="onFileChange"
          />
          <small class="field-help">
            {{ t("recruitingApplicant.fields.attachmentsHelp", { count: config.max_attachment_count, sizeMb: maxAttachmentSizeMb }) }}
          </small>
        </label>

        <ul v-if="selectedFiles.length" class="applicant-public-file-list">
          <li v-for="file in selectedFiles" :key="file.file_name">
            {{ file.file_name }} · {{ file.content_type }}
          </li>
        </ul>

        <label class="customer-admin-checkbox">
          <input v-model="consentConfirmed" type="checkbox" />
          <span>
            {{ t("recruitingApplicant.fields.consent") }}
            <a
              v-if="policyUrl"
              :href="policyUrl"
              target="_blank"
              rel="noreferrer"
            >
              {{ t("recruitingApplicant.fields.policyLink") }}
            </a>
          </span>
        </label>
        <p class="field-help">
          {{ t("recruitingApplicant.fields.policyVersion", { version: config.gdpr_policy_version }) }}
        </p>

        <div v-if="feedback.message" class="customer-admin-feedback" data-tone="error">
          <div>
            <strong>{{ feedback.title }}</strong>
            <span>{{ feedback.message }}</span>
          </div>
          <button type="button" @click="clearFeedback">{{ t("recruitingApplicant.actions.clearFeedback") }}</button>
        </div>

        <div class="cta-row">
          <button class="cta-button" type="submit" :disabled="submitting">
            {{ submitting ? t("recruitingApplicant.actions.submitting") : t("recruitingApplicant.actions.submit") }}
          </button>
        </div>
      </form>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { useRoute } from "vue-router";

import {
  getRecruitingApplicantForm,
  RecruitingPublicApiError,
  submitRecruitingApplicantForm,
  type RecruitingApplicantAttachmentPayload,
  type RecruitingApplicantFieldConfig,
  type RecruitingApplicantFormConfig,
  type RecruitingApplicantSubmissionResponse,
} from "@/api/recruitingPublic";
import { useI18n } from "@/i18n";

const route = useRoute();
const { locale, setLocale, t } = useI18n();

const loading = ref(true);
const submitting = ref(false);
const loadError = ref("");
const config = ref<RecruitingApplicantFormConfig | null>(null);
const submitted = ref<RecruitingApplicantSubmissionResponse | null>(null);
const consentConfirmed = ref(false);
const submissionKey = ref("");
const fieldValues = reactive<Record<string, string>>({});
const selectedFiles = ref<RecruitingApplicantAttachmentPayload[]>([]);
const feedback = reactive({
  title: "",
  message: "",
});

const embedded = computed(() => {
  if (typeof window === "undefined") {
    return false;
  }
  return window.self !== window.top;
});

const tenantCode = computed(() => String(route.params.tenantCode ?? ""));
const policyUrl = computed(() =>
  locale.value === "de" ? config.value?.gdpr_policy_url_de : config.value?.gdpr_policy_url_en,
);
const maxAttachmentSizeMb = computed(() =>
  config.value ? Math.max(1, Math.round(config.value.max_attachment_size_bytes / (1024 * 1024))) : 0,
);

function clearFeedback() {
  feedback.title = "";
  feedback.message = "";
}

function setFeedback(title: string, message: string) {
  feedback.title = title;
  feedback.message = message;
}

function createSubmissionKey() {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `submit-${Date.now()}`;
}

function inputType(fieldType: RecruitingApplicantFieldConfig["type"]) {
  if (fieldType === "email" || fieldType === "tel" || fieldType === "date") {
    return fieldType;
  }
  return "text";
}

function fieldLabel(field: RecruitingApplicantFieldConfig) {
  return locale.value === "de" ? field.label_de : field.label_en;
}

async function onFileChange(event: Event) {
  const input = event.target as HTMLInputElement;
  const files = Array.from(input.files ?? []);
  selectedFiles.value = await Promise.all(files.map(toAttachmentPayload));
}

function toAttachmentPayload(file: File): Promise<RecruitingApplicantAttachmentPayload> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = String(reader.result ?? "");
      const contentBase64 = result.includes(",") ? result.split(",", 2)[1] : result;
      resolve({
        kind: "attachment",
        file_name: file.name,
        content_type: file.type || "application/octet-stream",
        content_base64: contentBase64,
        label: file.name,
      });
    };
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}

function mapApiMessage(messageKey: string) {
  const map: Record<string, string> = {
    "errors.recruiting.applicant.tenant_not_found": "recruitingApplicant.feedback.tenantNotFound",
    "errors.recruiting.applicant.form_disabled": "recruitingApplicant.feedback.formDisabled",
    "errors.recruiting.applicant.origin_denied": "recruitingApplicant.feedback.originDenied",
    "errors.recruiting.applicant.rate_limited": "recruitingApplicant.feedback.rateLimited",
    "errors.recruiting.applicant.consent_required": "recruitingApplicant.feedback.consentRequired",
    "errors.recruiting.applicant.policy_mismatch": "recruitingApplicant.feedback.policyMismatch",
    "errors.recruiting.applicant.field_required": "recruitingApplicant.feedback.fieldRequired",
    "errors.recruiting.applicant.invalid_email": "recruitingApplicant.feedback.invalidEmail",
    "errors.recruiting.applicant.invalid_field_option": "recruitingApplicant.feedback.invalidFieldOption",
    "errors.recruiting.applicant.too_many_attachments": "recruitingApplicant.feedback.tooManyAttachments",
    "errors.recruiting.applicant.attachment_type_not_allowed": "recruitingApplicant.feedback.attachmentTypeNotAllowed",
    "errors.recruiting.applicant.attachment_too_large": "recruitingApplicant.feedback.attachmentTooLarge",
    "errors.recruiting.applicant.duplicate_submission": "recruitingApplicant.feedback.duplicateSubmission",
  };
  return map[messageKey] ?? "recruitingApplicant.feedback.error";
}

async function loadForm() {
  if (!tenantCode.value) {
    loadError.value = t("recruitingApplicant.feedback.tenantNotFound");
    loading.value = false;
    return;
  }
  loading.value = true;
  loadError.value = "";
  clearFeedback();
  try {
    config.value = await getRecruitingApplicantForm(tenantCode.value);
    submissionKey.value = createSubmissionKey();
    setLocale(route.query.lang === "en" ? "en" : config.value.default_locale);
    for (const field of config.value.fields) {
      fieldValues[field.key] = "";
    }
  } catch (error) {
    const messageKey =
      error instanceof RecruitingPublicApiError ? mapApiMessage(error.messageKey) : "recruitingApplicant.feedback.error";
    loadError.value = t(messageKey as never);
  } finally {
    loading.value = false;
  }
}

async function submitForm() {
  if (!config.value) {
    return;
  }
  submitting.value = true;
  clearFeedback();
  try {
    const additionalFields: Record<string, unknown> = {};
    for (const field of config.value.fields) {
      if (!["first_name", "last_name", "email", "phone", "desired_role", "availability_date", "message"].includes(field.key)) {
        additionalFields[field.key] = fieldValues[field.key];
      }
    }
    submitted.value = await submitRecruitingApplicantForm(tenantCode.value, {
      submission_key: submissionKey.value,
      locale: locale.value,
      first_name: fieldValues.first_name || null,
      last_name: fieldValues.last_name || null,
      email: fieldValues.email || null,
      phone: fieldValues.phone || null,
      desired_role: fieldValues.desired_role || null,
      availability_date: fieldValues.availability_date || null,
      message: fieldValues.message || null,
      additional_fields: additionalFields,
      attachments: selectedFiles.value,
      gdpr_consent_confirmed: consentConfirmed.value,
      gdpr_policy_ref: config.value.gdpr_policy_ref,
      gdpr_policy_version: config.value.gdpr_policy_version,
    });
  } catch (error) {
    const messageKey =
      error instanceof RecruitingPublicApiError ? mapApiMessage(error.messageKey) : "recruitingApplicant.feedback.error";
    setFeedback(t("recruitingApplicant.error.title"), t(messageKey as never));
  } finally {
    submitting.value = false;
  }
}

onMounted(() => {
  void loadForm();
});
</script>

<style scoped>
.applicant-public-page,
.applicant-public-form,
.applicant-public-grid {
  display: grid;
  gap: 1rem;
}

.applicant-public-page {
  padding: 1.5rem;
}

.applicant-public-shell {
  max-width: 960px;
  margin: 0 auto;
  gap: 1.25rem;
}

.applicant-public-header {
  display: grid;
  gap: 0.5rem;
}

.applicant-public-lead,
.applicant-public-meta,
.field-help {
  color: var(--sp-text-soft, #4b5563);
}

.applicant-public-grid {
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}

.applicant-public-state {
  gap: 0.75rem;
}

.applicant-public-state--error {
  border: 1px solid rgba(190, 24, 93, 0.2);
}

.applicant-public-state--success {
  border: 1px solid rgba(40, 170, 170, 0.2);
}

.applicant-public-file-list {
  margin: 0;
  padding-left: 1.25rem;
  color: var(--sp-text-soft, #4b5563);
}

@media (max-width: 720px) {
  .applicant-public-page {
    padding: 1rem;
  }
}
</style>
