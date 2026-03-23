<template>
  <section class="finance-billing-page">
    <section class="module-card finance-billing-hero">
      <div>
        <p class="eyebrow">{{ tp("eyebrow") }}</p>
        <h2>{{ tp("title") }}</h2>
        <p class="finance-billing-lead">{{ tp("lead") }}</p>
        <div class="finance-billing-meta">
          <span class="finance-billing-pill">{{ tp("permissionRead") }}: {{ state.canRead ? "on" : "off" }}</span>
          <span class="finance-billing-pill">{{ tp("permissionWrite") }}: {{ state.canWrite ? "on" : "off" }}</span>
        </div>
      </div>
      <div class="module-card">
        <label class="field-stack">
          <span>{{ tp("scopeLabel") }}</span>
          <input v-model="tenantScopeInput" :placeholder="tp('scopePlaceholder')" />
        </label>
        <label class="field-stack">
          <span>{{ tp("tokenLabel") }}</span>
          <input v-model="accessTokenInput" type="password" :placeholder="tp('tokenPlaceholder')" />
        </label>
        <div class="cta-row">
          <button class="cta-button" type="button" @click="rememberScopeAndToken">{{ tp("remember") }}</button>
          <button class="cta-button cta-secondary" type="button" :disabled="loading || !state.canRefresh" @click="refreshAll">{{ tp("refresh") }}</button>
        </div>
      </div>
    </section>

    <section v-if="feedback.message" class="finance-billing-feedback" :data-tone="feedback.tone">
      <div><strong>{{ feedback.title }}</strong><span>{{ feedback.message }}</span></div>
      <button type="button" @click="clearFeedback">{{ tp("clearFeedback") }}</button>
    </section>

    <section v-if="!tenantScopeId || !accessToken" class="module-card finance-billing-empty">
      <p class="eyebrow">{{ tp("missingScopeTitle") }}</p>
      <h3>{{ tp("missingScopeBody") }}</h3>
    </section>

    <section v-else-if="!state.canRead" class="module-card finance-billing-empty">
      <p class="eyebrow">{{ tp("missingPermissionTitle") }}</p>
      <h3>{{ tp("missingPermissionBody") }}</h3>
    </section>

    <div v-else class="finance-billing-grid">
      <section class="module-card finance-billing-panel">
        <div class="finance-billing-panel__header"><h3>{{ tp("filtersTitle") }}</h3></div>
        <form class="finance-billing-form-grid" @submit.prevent="generateCheck">
          <label class="field-stack"><span>{{ tp("subcontractorId") }}</span><input v-model="filters.subcontractor_id" required /></label>
          <label class="field-stack"><span>{{ tp("statusCode") }}</span><input v-model="filters.status_code" /></label>
          <label class="field-stack"><span>{{ tp("periodStart") }}</span><input v-model="filters.period_start" type="date" required /></label>
          <label class="field-stack"><span>{{ tp("periodEnd") }}</span><input v-model="filters.period_end" type="date" required /></label>
          <button class="cta-button" type="submit" :disabled="loading || !state.canGenerate">{{ tp("generate") }}</button>
        </form>
        <div class="finance-billing-summary">
          <article class="finance-billing-card"><strong>{{ summary.total }}</strong><span>{{ tp("summaryTotal") }}</span></article>
          <article class="finance-billing-card"><strong>{{ summary.released }}</strong><span>{{ tp("summaryReleased") }}</span></article>
          <article class="finance-billing-card"><strong>{{ summary.reviewRequired }}</strong><span>{{ tp("summaryReview") }}</span></article>
          <article class="finance-billing-card"><strong>{{ summary.exceptions }}</strong><span>{{ tp("summaryExceptions") }}</span></article>
        </div>
        <div v-if="rows.length" class="finance-billing-list">
          <button
            v-for="row in rows"
            :key="row.id"
            class="finance-billing-row"
            :class="{ selected: row.id === selectedId }"
            type="button"
            @click="selectRow(row.id)"
          >
            <strong>{{ row.check_no }}</strong>
            <span>{{ row.period_label }}</span>
            <span :data-tone="invoiceCheckStatusTone(row.status_code)">{{ row.status_code }} · {{ row.approved_amount_total }}</span>
          </button>
        </div>
      </section>

      <section class="module-card finance-billing-panel finance-billing-panel--wide">
        <div class="finance-billing-panel__header"><h3>{{ selectedRow?.check_no || tp("detailTitle") }}</h3></div>
        <template v-if="selectedRow">
          <div class="finance-billing-metrics">
            <span>{{ selectedRow.assigned_minutes_total }} / {{ selectedRow.actual_minutes_total }} / {{ selectedRow.approved_minutes_total }} min</span>
            <span>{{ selectedRow.expected_amount_total }} / {{ selectedRow.approved_amount_total }}</span>
            <span :data-tone="invoiceCheckStatusTone(selectedRow.status_code)">{{ selectedRow.status_code }}</span>
          </div>
          <div class="finance-billing-form-grid">
            <label class="field-stack"><span>{{ tp("submittedRef") }}</span><input v-model="submittedInvoice.submitted_invoice_ref" /></label>
            <label class="field-stack"><span>{{ tp("submittedAmount") }}</span><input v-model="submittedInvoice.submitted_invoice_amount" type="number" min="0" step="0.01" /></label>
          </div>
          <div class="cta-row">
            <button class="cta-button cta-secondary" type="button" :disabled="loading || !state.canWrite" @click="saveSubmittedInvoice">{{ tp("saveSubmitted") }}</button>
            <button class="cta-button cta-secondary" type="button" :disabled="loading || !state.canApprove" @click="changeStatus('approved')">{{ tp("approve") }}</button>
            <button class="cta-button cta-secondary" type="button" :disabled="loading || !state.canException" @click="changeStatus('exception')">{{ tp("exception") }}</button>
            <button class="cta-button" type="button" :disabled="loading || !state.canRelease" @click="changeStatus('released')">{{ tp("release") }}</button>
          </div>
          <div class="finance-billing-form-grid">
            <label class="field-stack">
              <span>{{ tp("noteText") }}</span>
              <textarea v-model="noteText" rows="3" />
            </label>
          </div>
          <div class="cta-row">
            <button class="cta-button cta-secondary" type="button" :disabled="loading || !state.canNote || !noteText" @click="addNote">{{ tp("addNote") }}</button>
          </div>
          <section class="module-card finance-billing-subpanel">
            <div class="finance-billing-panel__header"><h4>Lines</h4></div>
            <div class="finance-billing-stack">
              <article v-for="line in selectedRow.lines" :key="line.id" class="finance-billing-chip">
                <strong>{{ line.label }}</strong>
                <span>{{ line.assigned_minutes }} / {{ line.actual_minutes }} / {{ line.approved_minutes }} min</span>
                <span>{{ line.expected_amount }} / {{ line.approved_amount }} · {{ line.variance_reason_codes_json.join(", ") || "clean" }}</span>
              </article>
            </div>
          </section>
          <section class="module-card finance-billing-subpanel">
            <div class="finance-billing-panel__header"><h4>Notes</h4></div>
            <div class="finance-billing-stack">
              <article v-for="note in selectedRow.notes" :key="note.id" class="finance-billing-chip">
                <strong>{{ note.note_kind_code }}</strong>
                <span>{{ note.note_text }}</span>
              </article>
            </div>
          </section>
        </template>
        <p v-else class="finance-billing-empty-copy">{{ tp("noSelection") }}</p>
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from "vue";

import {
  addFinanceSubcontractorInvoiceCheckNote,
  changeFinanceSubcontractorInvoiceCheckStatus,
  generateFinanceSubcontractorInvoiceCheck,
  getFinanceSubcontractorInvoiceCheck,
  listFinanceSubcontractorInvoiceChecks,
  updateFinanceSubcontractorSubmittedInvoice,
  type FinanceSubcontractorInvoiceCheckRead,
} from "../api/financeSubcontractorChecks";
import {
  deriveFinanceSubcontractorControlState,
  invoiceCheckStatusTone,
  mapFinanceSubcontractorControlApiMessage,
  summarizeInvoiceChecks,
} from "../features/finance/financeSubcontractorChecks.helpers";
import { financeSubcontractorChecksMessages } from "../i18n/financeSubcontractorChecks.messages";

const locale = ref<"de" | "en">("de");
const role = ref("accounting");
const loading = ref(false);
const rows = ref<FinanceSubcontractorInvoiceCheckRead[]>([]);
const selectedId = ref("");
const noteText = ref("");
const tenantScopeInput = ref("");
const accessTokenInput = ref("");
const tenantScopeId = ref("");
const accessToken = ref("");
const feedback = reactive({ title: "", message: "", tone: "neutral" as "good" | "bad" | "neutral" });
const filters = reactive({
  subcontractor_id: "",
  status_code: "",
  period_start: "",
  period_end: "",
});
const submittedInvoice = reactive({
  submitted_invoice_ref: "",
  submitted_invoice_amount: "",
  submitted_invoice_currency_code: "EUR",
});

const selectedRow = computed(() => rows.value.find((row) => row.id === selectedId.value) ?? null);
const state = computed(() => deriveFinanceSubcontractorControlState(role.value, selectedRow.value));
const summary = computed(() => summarizeInvoiceChecks(rows.value));

function tp(key: keyof typeof financeSubcontractorChecksMessages.de) {
  return financeSubcontractorChecksMessages[locale.value][key];
}

function clearFeedback() {
  feedback.title = "";
  feedback.message = "";
  feedback.tone = "neutral";
}

function setFeedback(kind: "good" | "bad" | "neutral", title: string, message: string) {
  feedback.tone = kind;
  feedback.title = title;
  feedback.message = message;
}

function rememberScopeAndToken() {
  tenantScopeId.value = tenantScopeInput.value.trim();
  accessToken.value = accessTokenInput.value.trim();
}

async function refreshAll() {
  if (!tenantScopeId.value || !accessToken.value) {
    return;
  }
  loading.value = true;
  clearFeedback();
  try {
    rows.value = await listFinanceSubcontractorInvoiceChecks(tenantScopeId.value, accessToken.value, filters);
    if (selectedId.value) {
      await selectRow(selectedId.value);
    }
  } catch (error) {
    const key = error instanceof Error && "messageKey" in error ? mapFinanceSubcontractorControlApiMessage(error.messageKey as string) : "error";
    setFeedback("bad", tp("error"), tp(key as keyof typeof financeSubcontractorChecksMessages.de));
  } finally {
    loading.value = false;
  }
}

async function generateCheck() {
  if (!tenantScopeId.value || !accessToken.value) {
    return;
  }
  loading.value = true;
  try {
    const row = await generateFinanceSubcontractorInvoiceCheck(tenantScopeId.value, accessToken.value, filters);
    await refreshAll();
    selectedId.value = row.id;
    await selectRow(row.id);
    setFeedback("good", tp("title"), row.status_code);
  } catch (error) {
    const key = error instanceof Error && "messageKey" in error ? mapFinanceSubcontractorControlApiMessage(error.messageKey as string) : "error";
    setFeedback("bad", tp("error"), tp(key as keyof typeof financeSubcontractorChecksMessages.de));
  } finally {
    loading.value = false;
  }
}

async function selectRow(id: string) {
  if (!tenantScopeId.value || !accessToken.value) {
    return;
  }
  selectedId.value = id;
  const detail = await getFinanceSubcontractorInvoiceCheck(tenantScopeId.value, id, accessToken.value);
  rows.value = rows.value.map((row) => (row.id === id ? detail : row));
  submittedInvoice.submitted_invoice_ref = detail.submitted_invoice_ref ?? "";
  submittedInvoice.submitted_invoice_amount = detail.submitted_invoice_amount ?? "";
}

async function saveSubmittedInvoice() {
  if (!selectedRow.value || !tenantScopeId.value || !accessToken.value) {
    return;
  }
  const detail = await updateFinanceSubcontractorSubmittedInvoice(tenantScopeId.value, selectedRow.value.id, accessToken.value, {
    submitted_invoice_ref: submittedInvoice.submitted_invoice_ref || null,
    submitted_invoice_amount: submittedInvoice.submitted_invoice_amount || null,
    submitted_invoice_currency_code: submittedInvoice.submitted_invoice_currency_code,
  });
  rows.value = rows.value.map((row) => (row.id === detail.id ? detail : row));
}

async function addNote() {
  if (!selectedRow.value || !tenantScopeId.value || !accessToken.value || !noteText.value) {
    return;
  }
  const detail = await addFinanceSubcontractorInvoiceCheckNote(tenantScopeId.value, selectedRow.value.id, accessToken.value, {
    note_text: noteText.value,
    note_kind_code: "note",
  });
  rows.value = rows.value.map((row) => (row.id === detail.id ? detail : row));
  noteText.value = "";
}

async function changeStatus(statusCode: string) {
  if (!selectedRow.value || !tenantScopeId.value || !accessToken.value) {
    return;
  }
  const detail = await changeFinanceSubcontractorInvoiceCheckStatus(tenantScopeId.value, selectedRow.value.id, accessToken.value, {
    status_code: statusCode,
    note_text: noteText.value || null,
  });
  rows.value = rows.value.map((row) => (row.id === detail.id ? detail : row));
  noteText.value = "";
}
</script>
