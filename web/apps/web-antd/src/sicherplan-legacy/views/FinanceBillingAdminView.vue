<template>
  <section class="finance-billing-page">
    <section class="module-card finance-billing-hero">
      <div>
        <p class="eyebrow">{{ tp("eyebrow") }}</p>
        <h2>{{ tp("title") }}</h2>
        <p class="finance-billing-lead">{{ tp("lead") }}</p>
        <div class="finance-billing-meta">
          <span class="finance-billing-pill">{{ tp("permissionRead") }}: {{ actionState.canRead ? "on" : "off" }}</span>
          <span class="finance-billing-pill">{{ tp("permissionWrite") }}: {{ actionState.canWrite ? "on" : "off" }}</span>
          <span class="finance-billing-pill">{{ tp("permissionDelivery") }}: {{ actionState.canDeliver ? "on" : "off" }}</span>
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
          <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canRefresh || loading" @click="refreshAll">{{ tp("refresh") }}</button>
        </div>
      </div>
    </section>

    <section v-if="feedback.message" class="finance-billing-feedback" :data-tone="feedback.tone">
      <div>
        <strong>{{ feedback.title }}</strong>
        <span>{{ feedback.message }}</span>
      </div>
      <button type="button" @click="clearFeedback">{{ tp("clearFeedback") }}</button>
    </section>

    <section v-if="!tenantScopeId || !accessToken" class="module-card finance-billing-empty">
      <p class="eyebrow">{{ tp("missingScopeTitle") }}</p>
      <h3>{{ tp("missingScopeBody") }}</h3>
    </section>

    <section v-else-if="!actionState.canRead" class="module-card finance-billing-empty">
      <p class="eyebrow">{{ tp("missingPermissionTitle") }}</p>
      <h3>{{ tp("missingPermissionBody") }}</h3>
    </section>

    <div v-else class="finance-billing-grid">
      <section class="module-card finance-billing-panel">
        <div class="finance-billing-panel__header"><h3>{{ tp("timesheetsTitle") }}</h3></div>
        <form class="finance-billing-form-grid" @submit.prevent="submitTimesheetGeneration">
          <label class="field-stack"><span>{{ tp("customerId") }}</span><input v-model="timesheetDraft.customer_id" required /></label>
          <label class="field-stack"><span>{{ tp("orderId") }}</span><input v-model="timesheetDraft.order_id" /></label>
          <label class="field-stack"><span>{{ tp("planningRecordId") }}</span><input v-model="timesheetDraft.planning_record_id" /></label>
          <label class="field-stack"><span>{{ tp("periodStart") }}</span><input v-model="timesheetDraft.period_start" type="date" required /></label>
          <label class="field-stack"><span>{{ tp("periodEnd") }}</span><input v-model="timesheetDraft.period_end" type="date" required /></label>
          <button class="cta-button" type="submit" :disabled="!actionState.canGenerateTimesheet || loading">{{ tp("generateTimesheet") }}</button>
        </form>
        <div v-if="timesheets.length" class="finance-billing-list">
          <button
            v-for="row in timesheets"
            :key="row.id"
            class="finance-billing-row"
            :class="{ selected: row.id === selectedTimesheetId }"
            type="button"
            @click="selectedTimesheetId = row.id"
          >
            <strong>{{ row.headline }}</strong>
            <span>{{ row.period_start }} - {{ row.period_end }}</span>
            <span>{{ row.release_state_code }} · {{ row.total_billable_minutes }} min</span>
          </button>
        </div>
        <p v-else class="finance-billing-empty-copy">{{ tp("timesheetEmpty") }}</p>
      </section>

      <section class="module-card finance-billing-panel">
        <div class="finance-billing-panel__header">
          <h3>{{ tp("invoicesTitle") }}</h3>
        </div>
        <form class="finance-billing-form-grid" @submit.prevent="submitInvoiceGeneration">
          <label class="field-stack"><span>{{ tp("customerId") }}</span><input v-model="invoiceDraft.customer_id" required /></label>
          <label class="field-stack"><span>{{ tp("issueDate") }}</span><input v-model="invoiceDraft.issue_date" type="date" required /></label>
          <button class="cta-button" type="submit" :disabled="!actionState.canGenerateInvoice || loading || !selectedTimesheet">{{ tp("generateInvoice") }}</button>
        </form>
        <div class="finance-billing-summary">
          <article class="finance-billing-card"><strong>{{ summary.total }}</strong><span>{{ tp("summaryTotal") }}</span></article>
          <article class="finance-billing-card"><strong>{{ summary.released }}</strong><span>{{ tp("summaryReleased") }}</span></article>
          <article class="finance-billing-card"><strong>{{ summary.queued }}</strong><span>{{ tp("summaryQueued") }}</span></article>
          <article class="finance-billing-card"><strong>{{ summary.eInvoice }}</strong><span>{{ tp("summaryEInvoice") }}</span></article>
        </div>
        <div v-if="invoices.length" class="finance-billing-list">
          <button
            v-for="row in invoices"
            :key="row.id"
            class="finance-billing-row"
            :class="{ selected: row.id === selectedInvoiceId }"
            type="button"
            @click="selectedInvoiceId = row.id"
          >
            <strong>{{ row.invoice_no }}</strong>
            <span>{{ row.issue_date }} · {{ row.total_amount }} {{ row.currency_code }}</span>
            <span :data-tone="invoiceDeliveryTone(row.delivery_status_code)">{{ row.invoice_status_code }} · {{ row.delivery_status_code }}</span>
          </button>
        </div>
        <p v-else class="finance-billing-empty-copy">{{ tp("invoiceEmpty") }}</p>
      </section>

      <section class="module-card finance-billing-panel finance-billing-panel--wide">
        <div class="finance-billing-panel__header">
          <div>
            <p class="eyebrow">{{ tp("detailTitle") }}</p>
            <h3>{{ selectedInvoice?.invoice_no || selectedTimesheet?.headline || tp("detailTitle") }}</h3>
          </div>
        </div>

        <template v-if="selectedInvoice">
          <div class="cta-row">
            <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canIssueInvoice || loading" @click="issueSelectedInvoice">{{ tp("issueInvoice") }}</button>
            <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canReleaseInvoice || loading" @click="releaseSelectedInvoice">{{ tp("releaseInvoice") }}</button>
            <button class="cta-button" type="button" :disabled="!actionState.canQueueDispatch || loading" @click="queueSelectedDispatch">{{ tp("queueDispatch") }}</button>
          </div>
          <div class="finance-billing-metrics">
            <span>{{ selectedInvoice.subtotal_amount }} / {{ selectedInvoice.tax_amount }} / {{ selectedInvoice.total_amount }} {{ selectedInvoice.currency_code }}</span>
            <span>{{ selectedInvoice.issue_date }} → {{ selectedInvoice.due_date }}</span>
            <span>{{ selectedInvoice.layout_code || "-" }}</span>
          </div>
          <section class="module-card finance-billing-subpanel">
            <div class="finance-billing-panel__header"><h4>{{ tp("deliveryTitle") }}</h4></div>
            <div class="finance-billing-stack">
              <article class="finance-billing-chip"><strong>Method</strong><span>{{ selectedInvoice.dispatch_method_code || "-" }}</span></article>
              <article class="finance-billing-chip"><strong>Email</strong><span>{{ selectedInvoice.invoice_email || "-" }}</span></article>
              <article class="finance-billing-chip"><strong>Leitweg</strong><span>{{ selectedInvoice.leitweg_id || "-" }}</span></article>
              <article class="finance-billing-chip"><strong>Party</strong><span>{{ selectedInvoice.invoice_party_snapshot_json.name || "-" }}</span></article>
            </div>
          </section>
          <section class="module-card finance-billing-subpanel">
            <div class="finance-billing-panel__header"><h4>{{ tp("linesTitle") }}</h4></div>
            <div v-if="selectedInvoice.lines.length" class="finance-billing-stack">
              <article v-for="row in selectedInvoice.lines" :key="row.id" class="finance-billing-chip">
                <strong>{{ row.description }}</strong>
                <span>{{ row.quantity }} {{ row.unit_code }} · {{ row.net_amount }}</span>
              </article>
            </div>
          </section>
        </template>

        <template v-else-if="selectedTimesheet">
          <div class="cta-row">
            <button class="cta-button" type="button" :disabled="!actionState.canReleaseTimesheet || loading" @click="releaseSelectedTimesheet">{{ tp("releaseTimesheet") }}</button>
          </div>
          <div class="finance-billing-metrics">
            <span>{{ selectedTimesheet.total_planned_minutes }} / {{ selectedTimesheet.total_actual_minutes }} / {{ selectedTimesheet.total_billable_minutes }} min</span>
            <span>{{ selectedTimesheet.period_start }} → {{ selectedTimesheet.period_end }}</span>
            <span>{{ selectedTimesheet.release_state_code }}</span>
          </div>
          <section class="module-card finance-billing-subpanel">
            <div class="finance-billing-panel__header"><h4>{{ tp("linesTitle") }}</h4></div>
            <div v-if="selectedTimesheet.lines.length" class="finance-billing-stack">
              <article v-for="row in selectedTimesheet.lines" :key="row.id" class="finance-billing-chip">
                <strong>{{ row.line_label }}</strong>
                <span>{{ row.line_description }}</span>
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
  generateFinanceBillingInvoice,
  generateFinanceBillingTimesheet,
  issueFinanceBillingInvoice,
  listFinanceBillingInvoices,
  listFinanceBillingTimesheets,
  queueFinanceBillingInvoiceDispatch,
  releaseFinanceBillingInvoice,
  releaseFinanceBillingTimesheet,
  type FinanceBillingInvoiceRead,
  type FinanceBillingTimesheetRead,
} from "../api/financeBilling";
import {
  deriveFinanceBillingActionState,
  invoiceDeliveryTone,
  mapFinanceBillingApiMessage,
  summarizeBillingInvoices,
} from "../features/finance/financeBilling.helpers";
import { financeBillingMessages } from "../i18n/financeBilling.messages";

const locale = ref<"de" | "en">("de");
const role = ref("accounting");
const tenantScopeInput = ref("");
const accessTokenInput = ref("");
const tenantScopeId = ref("");
const accessToken = ref("");
const loading = ref(false);
const timesheets = ref<FinanceBillingTimesheetRead[]>([]);
const invoices = ref<FinanceBillingInvoiceRead[]>([]);
const selectedTimesheetId = ref("");
const selectedInvoiceId = ref("");
const feedback = reactive({ title: "", message: "", tone: "neutral" as "good" | "bad" | "neutral" });

const timesheetDraft = reactive({
  customer_id: "",
  order_id: "",
  planning_record_id: "",
  period_start: "",
  period_end: "",
});
const invoiceDraft = reactive({
  customer_id: "",
  issue_date: "",
});

const selectedTimesheet = computed(() => timesheets.value.find((row) => row.id === selectedTimesheetId.value) ?? null);
const selectedInvoice = computed(() => invoices.value.find((row) => row.id === selectedInvoiceId.value) ?? null);
const actionState = computed(() => deriveFinanceBillingActionState(role.value, selectedTimesheet.value, selectedInvoice.value));
const summary = computed(() => summarizeBillingInvoices(invoices.value));

function tp(key: keyof typeof financeBillingMessages.de) {
  return financeBillingMessages[locale.value][key];
}

function rememberScopeAndToken() {
  tenantScopeId.value = tenantScopeInput.value.trim();
  accessToken.value = accessTokenInput.value.trim();
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

async function refreshAll() {
  if (!tenantScopeId.value || !accessToken.value) {
    return;
  }
  loading.value = true;
  clearFeedback();
  try {
    timesheets.value = await listFinanceBillingTimesheets(tenantScopeId.value, accessToken.value, {});
    invoices.value = await listFinanceBillingInvoices(tenantScopeId.value, accessToken.value, {});
  } catch (error) {
    const messageKey = error instanceof Error && "messageKey" in error ? mapFinanceBillingApiMessage(error.messageKey as string) : "error";
    setFeedback("bad", tp("error"), tp(messageKey as keyof typeof financeBillingMessages.de));
  } finally {
    loading.value = false;
  }
}

async function submitTimesheetGeneration() {
  loading.value = true;
  clearFeedback();
  try {
    const row = await generateFinanceBillingTimesheet(tenantScopeId.value, accessToken.value, {
      ...timesheetDraft,
      order_id: timesheetDraft.order_id || null,
      planning_record_id: timesheetDraft.planning_record_id || null,
    });
    selectedTimesheetId.value = row.id;
    await refreshAll();
    setFeedback("good", tp("saveSuccess"), tp("saveSuccess"));
  } catch (error) {
    const messageKey = error instanceof Error && "messageKey" in error ? mapFinanceBillingApiMessage(error.messageKey as string) : "error";
    setFeedback("bad", tp("error"), tp(messageKey as keyof typeof financeBillingMessages.de));
    loading.value = false;
  }
}

async function releaseSelectedTimesheet() {
  if (!selectedTimesheet.value) {
    return;
  }
  loading.value = true;
  clearFeedback();
  try {
    const row = await releaseFinanceBillingTimesheet(tenantScopeId.value, selectedTimesheet.value.id, accessToken.value, {
      customer_visible_flag: true,
      version_no: selectedTimesheet.value.version_no,
    });
    selectedTimesheetId.value = row.id;
    await refreshAll();
    setFeedback("good", tp("saveSuccess"), tp("saveSuccess"));
  } catch (error) {
    const messageKey = error instanceof Error && "messageKey" in error ? mapFinanceBillingApiMessage(error.messageKey as string) : "error";
    setFeedback("bad", tp("error"), tp(messageKey as keyof typeof financeBillingMessages.de));
  } finally {
    loading.value = false;
  }
}

async function submitInvoiceGeneration() {
  if (!selectedTimesheet.value) {
    return;
  }
  loading.value = true;
  clearFeedback();
  try {
    const row = await generateFinanceBillingInvoice(tenantScopeId.value, accessToken.value, {
      customer_id: invoiceDraft.customer_id || selectedTimesheet.value.customer_id,
      timesheet_id: selectedTimesheet.value.id,
      issue_date: invoiceDraft.issue_date,
    });
    selectedInvoiceId.value = row.id;
    await refreshAll();
    setFeedback("good", tp("saveSuccess"), tp("saveSuccess"));
  } catch (error) {
    const messageKey = error instanceof Error && "messageKey" in error ? mapFinanceBillingApiMessage(error.messageKey as string) : "error";
    setFeedback("bad", tp("error"), tp(messageKey as keyof typeof financeBillingMessages.de));
  } finally {
    loading.value = false;
  }
}

async function issueSelectedInvoice() {
  if (!selectedInvoice.value) {
    return;
  }
  loading.value = true;
  clearFeedback();
  try {
    const row = await issueFinanceBillingInvoice(tenantScopeId.value, selectedInvoice.value.id, accessToken.value, {
      version_no: selectedInvoice.value.version_no,
    });
    selectedInvoiceId.value = row.id;
    await refreshAll();
    setFeedback("good", tp("saveSuccess"), tp("saveSuccess"));
  } catch (error) {
    const messageKey = error instanceof Error && "messageKey" in error ? mapFinanceBillingApiMessage(error.messageKey as string) : "error";
    setFeedback("bad", tp("error"), tp(messageKey as keyof typeof financeBillingMessages.de));
  } finally {
    loading.value = false;
  }
}

async function releaseSelectedInvoice() {
  if (!selectedInvoice.value) {
    return;
  }
  loading.value = true;
  clearFeedback();
  try {
    const row = await releaseFinanceBillingInvoice(tenantScopeId.value, selectedInvoice.value.id, accessToken.value, {
      customer_visible_flag: true,
      version_no: selectedInvoice.value.version_no,
    });
    selectedInvoiceId.value = row.id;
    await refreshAll();
    setFeedback("good", tp("saveSuccess"), tp("saveSuccess"));
  } catch (error) {
    const messageKey = error instanceof Error && "messageKey" in error ? mapFinanceBillingApiMessage(error.messageKey as string) : "error";
    setFeedback("bad", tp("error"), tp(messageKey as keyof typeof financeBillingMessages.de));
  } finally {
    loading.value = false;
  }
}

async function queueSelectedDispatch() {
  if (!selectedInvoice.value) {
    return;
  }
  loading.value = true;
  clearFeedback();
  try {
    const row = await queueFinanceBillingInvoiceDispatch(tenantScopeId.value, selectedInvoice.value.id, accessToken.value, {
      version_no: selectedInvoice.value.version_no,
    });
    selectedInvoiceId.value = row.id;
    await refreshAll();
    setFeedback("good", tp("saveSuccess"), tp("saveSuccess"));
  } catch (error) {
    const messageKey = error instanceof Error && "messageKey" in error ? mapFinanceBillingApiMessage(error.messageKey as string) : "error";
    setFeedback("bad", tp("error"), tp(messageKey as keyof typeof financeBillingMessages.de));
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.finance-billing-page,
.finance-billing-grid,
.finance-billing-list,
.finance-billing-stack,
.finance-billing-meta,
.finance-billing-summary,
.finance-billing-metrics {
  display: grid;
  gap: 1rem;
}

.finance-billing-grid {
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
}

.finance-billing-panel--wide {
  grid-column: 1 / -1;
}

.finance-billing-hero {
  display: grid;
  gap: 1rem;
  grid-template-columns: 2fr 1fr;
}

.finance-billing-row,
.finance-billing-chip,
.finance-billing-card,
.finance-billing-pill {
  border: 1px solid rgba(40, 170, 170, 0.25);
  border-radius: 1rem;
  padding: 0.85rem 1rem;
  background: rgba(40, 170, 170, 0.06);
}

.finance-billing-row {
  display: grid;
  gap: 0.2rem;
  text-align: left;
}

.finance-billing-row.selected {
  border-color: rgba(40, 170, 170, 0.65);
  background: rgba(40, 170, 170, 0.12);
}

.finance-billing-summary {
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
}

.finance-billing-feedback[data-tone="good"] {
  border-left: 4px solid #14805e;
}

.finance-billing-feedback[data-tone="bad"] {
  border-left: 4px solid #b42318;
}

.finance-billing-feedback,
.finance-billing-empty,
.finance-billing-subpanel {
  display: grid;
  gap: 0.75rem;
}

.finance-billing-form-grid {
  display: grid;
  gap: 0.75rem;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}

.finance-billing-lead,
.finance-billing-empty-copy {
  opacity: 0.8;
}

.finance-billing-panel__header,
.field-stack,
.cta-row {
  display: grid;
  gap: 0.5rem;
}

@media (max-width: 900px) {
  .finance-billing-hero {
    grid-template-columns: 1fr;
  }
}
</style>
