<template>
  <section class="reporting-page">
    <AdminPageShell :eyebrow="tp('eyebrow')" :title="tp('title')" :lead="tp('lead')">
      <template #meta>
        <div class="reporting-meta">
          <span class="reporting-pill">{{ tp("permissionRead") }}: {{ actionState.canRead ? "on" : "off" }}</span>
          <span class="reporting-pill">{{ tp("permissionExport") }}: {{ actionState.canExport ? "on" : "off" }}</span>
        </div>
      </template>
      <template #actions>
        <div class="module-card">
          <label class="field-stack">
            <span>{{ tp("scopeLabel") }}</span>
            <input v-model="tenantScopeInput" :placeholder="tp('scopePlaceholder')" />
          </label>
          <label class="field-stack">
            <span>{{ tp("tokenLabel") }}</span>
            <input v-model="accessTokenInput" type="password" :placeholder="tp('tokenPlaceholder')" />
          </label>
          <label class="field-stack">
            <span>{{ tp("roleLabel") }}</span>
            <select v-model="role">
              <option value="tenant_admin">tenant_admin</option>
              <option value="accounting">accounting</option>
              <option value="controller_qm">controller_qm</option>
              <option value="dispatcher">dispatcher</option>
            </select>
          </label>
          <div class="cta-row">
            <button class="cta-button" type="button" @click="rememberScopeAndToken">{{ tp("remember") }}</button>
            <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canRefresh || loading" @click="refreshRows">{{ tp("refresh") }}</button>
            <button class="cta-button" type="button" :disabled="!actionState.canDownload || loading" @click="downloadCsv">{{ tp("download") }}</button>
            <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canQueueDelivery || loading" @click="queueDelivery">{{ tp("queueDelivery") }}</button>
          </div>
        </div>
      </template>
      <template #stats>
        <AdminStatCard :label="tp('summaryRows')" :value="summary.total" tone="accent" />
        <AdminStatCard :label="tp('summaryAmount')" :value="summary.amount" />
      </template>
    </AdminPageShell>

    <section v-if="feedback.message" class="reporting-feedback" :data-tone="feedback.tone">
      <div>
        <strong>{{ feedback.title }}</strong>
        <span>{{ feedback.message }}</span>
      </div>
      <button type="button" @click="clearFeedback">{{ tp("clearFeedback") }}</button>
    </section>

    <section v-if="!tenantScopeId || !accessToken" class="module-card reporting-empty">
      <p class="eyebrow">{{ tp("missingScopeTitle") }}</p>
      <h3>{{ tp("missingScopeBody") }}</h3>
    </section>

    <section v-else-if="!actionState.canRead" class="module-card reporting-empty">
      <p class="eyebrow">{{ tp("missingPermissionTitle") }}</p>
      <h3>{{ tp("missingPermissionBody") }}</h3>
    </section>

    <div v-else class="reporting-grid">
      <section class="module-card reporting-panel">
        <div class="reporting-panel__header"><h3>{{ tp("reportLabel") }}</h3></div>
        <label class="field-stack">
          <span>{{ tp("reportLabel") }}</span>
          <select v-model="reportKey">
            <option v-for="key in reportKeys" :key="key" :value="key">{{ key }}</option>
          </select>
        </label>
        <label class="field-stack"><span>{{ tp("dateFrom") }}</span><input v-model="filters.date_from" type="date" /></label>
        <label class="field-stack"><span>{{ tp("dateTo") }}</span><input v-model="filters.date_to" type="date" /></label>
        <label class="field-stack"><span>{{ tp("customerId") }}</span><input v-model="filters.customer_id" /></label>
        <label class="field-stack"><span>{{ tp("subcontractorId") }}</span><input v-model="filters.subcontractor_id" /></label>
        <label class="field-stack"><span>{{ tp("employeeId") }}</span><input v-model="filters.employee_id" /></label>
        <label class="field-stack"><span>{{ tp("deliveryTarget") }}</span><input v-model="delivery.target_label" :placeholder="tp('deliveryTargetPlaceholder')" /></label>
        <label class="field-stack"><span>{{ tp("deliveryAddress") }}</span><input v-model="delivery.target_address" :placeholder="tp('deliveryAddressPlaceholder')" /></label>
        <label class="field-stack"><span>{{ tp("deliveryWhen") }}</span><input v-model="delivery.scheduled_for" type="datetime-local" /></label>
      </section>

      <section class="module-card reporting-panel">
        <div class="reporting-panel__header"><h3>{{ tp("summaryTitle") }}</h3></div>
        <div class="reporting-summary">
          <article class="reporting-card"><strong>{{ summary.total }}</strong><span>{{ tp("summaryRows") }}</span></article>
          <article class="reporting-card"><strong>{{ summary.amount }}</strong><span>{{ tp("summaryAmount") }}</span></article>
        </div>
      </section>

      <section class="module-card reporting-panel reporting-panel--wide">
        <div class="reporting-panel__header"><h3>{{ tp("tableTitle") }}</h3></div>
        <div v-if="rows.length" class="reporting-table-wrapper">
          <table class="reporting-table">
            <thead>
              <tr><th v-for="column in columns" :key="column">{{ column }}</th></tr>
            </thead>
            <tbody>
              <tr v-for="(row, index) in rows" :key="`${reportKey}-${index}`">
                <td v-for="column in columns" :key="column">{{ row[column] }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p v-else class="reporting-empty-copy">{{ tp("empty") }}</p>
      </section>

      <section class="module-card reporting-panel reporting-panel--wide">
        <div class="reporting-panel__header"><h3>{{ tp("deliveryHistory") }}</h3></div>
        <div v-if="deliveryJobs.length" class="reporting-table-wrapper">
          <table class="reporting-table">
            <thead>
              <tr>
                <th>{{ tp("reportLabel") }}</th>
                <th>{{ tp("deliveryStatus") }}</th>
                <th>{{ tp("deliveryRows") }}</th>
                <th>{{ tp("deliveryTarget") }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="job in deliveryJobs" :key="job.job_id" :data-tone="deliveryStatusTone(job.job_status)">
                <td>{{ job.report_key }}</td>
                <td>{{ job.job_status }}</td>
                <td>{{ job.row_count }}</td>
                <td>{{ job.target_label || "-" }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p v-else class="reporting-empty-copy">{{ tp("empty") }}</p>
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from "vue";

import AdminPageShell from "@/components/AdminPageShell.vue";
import AdminStatCard from "@/components/AdminStatCard.vue";
import { downloadReportingCsv, listReportingDeliveryJobs, listReportingRows, queueReportingDeliveryJob, type ReportingDeliveryJob, type ReportingRow } from "../api/reporting";
import { REPORTING_REPORT_KEYS, deliveryStatusTone, deriveReportingActionState, mapReportingApiMessage, summarizeReportingRows } from "../features/reporting/reporting.helpers";
import { reportingMessages } from "../i18n/reporting.messages";

const locale = ref<"de" | "en">("de");
const role = ref("controller_qm");
const reportKey = ref("employee-activity");
const reportKeys = REPORTING_REPORT_KEYS;
const tenantScopeInput = ref("");
const accessTokenInput = ref("");
const tenantScopeId = ref("");
const accessToken = ref("");
const loading = ref(false);
const rows = ref<ReportingRow[]>([]);
const deliveryJobs = ref<ReportingDeliveryJob[]>([]);
const feedback = reactive({ title: "", message: "", tone: "neutral" as "good" | "bad" | "neutral" });
const filters = reactive({
  date_from: "",
  date_to: "",
  customer_id: "",
  subcontractor_id: "",
  employee_id: "",
});
const delivery = reactive({
  target_label: "",
  target_address: "",
  scheduled_for: "",
});

const actionState = computed(() => deriveReportingActionState(role.value, reportKey.value));
const columns = computed(() => (rows.value[0] ? Object.keys(rows.value[0]) : []));
const summary = computed(() => {
  const numericField = columns.value.find((column) => /amount|total|minutes|count|ratio/i.test(column)) ?? "total_amount";
  return summarizeReportingRows(rows.value, numericField);
});

function tp(key: keyof typeof reportingMessages.de) {
  return reportingMessages[locale.value][key];
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

function setFeedback(tone: "good" | "bad" | "neutral", title: string, message: string) {
  feedback.tone = tone;
  feedback.title = title;
  feedback.message = message;
}

async function refreshRows() {
  if (!tenantScopeId.value || !accessToken.value) {
    return;
  }
  loading.value = true;
  clearFeedback();
  try {
    rows.value = await listReportingRows(reportKey.value, tenantScopeId.value, accessToken.value, filters);
    deliveryJobs.value = await listReportingDeliveryJobs(tenantScopeId.value, accessToken.value, { report_key: reportKey.value });
  } catch (error) {
    const messageKey = error instanceof Error && "messageKey" in error ? mapReportingApiMessage(error.messageKey as string) : "error";
    setFeedback("bad", tp("error"), tp(messageKey as keyof typeof reportingMessages.de));
  } finally {
    loading.value = false;
  }
}

async function downloadCsv() {
  if (!tenantScopeId.value || !accessToken.value) {
    return;
  }
  loading.value = true;
  clearFeedback();
  try {
    const file = await downloadReportingCsv(reportKey.value, tenantScopeId.value, accessToken.value, filters);
    const blob = new Blob([file.content], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = file.fileName;
    anchor.click();
    URL.revokeObjectURL(url);
    setFeedback("good", tp("success"), tp("exportDone"));
  } catch (error) {
    const messageKey = error instanceof Error && "messageKey" in error ? mapReportingApiMessage(error.messageKey as string) : "error";
    setFeedback("bad", tp("error"), tp(messageKey as keyof typeof reportingMessages.de));
  } finally {
    loading.value = false;
  }
}

async function queueDelivery() {
  if (!tenantScopeId.value || !accessToken.value) {
    return;
  }
  loading.value = true;
  clearFeedback();
  try {
    const job = await queueReportingDeliveryJob(reportKey.value, tenantScopeId.value, accessToken.value, filters, {
      target_label: delivery.target_label || undefined,
      target_address: delivery.target_address || undefined,
      scheduled_for: delivery.scheduled_for ? new Date(delivery.scheduled_for).toISOString() : undefined,
    });
    deliveryJobs.value = [job, ...deliveryJobs.value.filter((row) => row.job_id !== job.job_id)];
    setFeedback("good", tp("success"), tp("deliveryQueued"));
  } catch (error) {
    const messageKey = error instanceof Error && "messageKey" in error ? mapReportingApiMessage(error.messageKey as string) : "error";
    setFeedback("bad", tp("error"), tp(messageKey as keyof typeof reportingMessages.de));
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.reporting-page { display: grid; gap: 1rem; }
.reporting-hero, .reporting-grid { display: grid; gap: 1rem; }
.reporting-grid { grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); }
.reporting-panel--wide { grid-column: 1 / -1; }
.reporting-meta, .reporting-summary, .cta-row { display: flex; gap: 0.75rem; flex-wrap: wrap; }
.reporting-pill, .reporting-card { border: 1px solid var(--el-border-color, #d5d7de); border-radius: 999px; padding: 0.4rem 0.8rem; }
.reporting-card { border-radius: 1rem; }
.reporting-table-wrapper { overflow: auto; }
.reporting-table { width: 100%; border-collapse: collapse; }
.reporting-table th, .reporting-table td {
  border-bottom: 1px solid var(--el-border-color, #d5d7de);
  padding: 0.55rem 0.75rem;
  text-align: left;
  vertical-align: top;
}
</style>
