<template>
  <section class="finance-payroll-page">
    <section class="module-card finance-payroll-hero">
      <div>
        <p class="eyebrow">{{ tp("eyebrow") }}</p>
        <h2>{{ tp("title") }}</h2>
        <p class="finance-payroll-lead">{{ tp("lead") }}</p>
        <div class="finance-payroll-meta">
          <span class="finance-payroll-pill">{{ tp("permissionRead") }}: {{ actionState.canRead ? "on" : "off" }}</span>
          <span class="finance-payroll-pill">{{ tp("permissionWrite") }}: {{ actionState.canWrite ? "on" : "off" }}</span>
          <span class="finance-payroll-pill">{{ tp("permissionExport") }}: {{ actionState.canExport ? "on" : "off" }}</span>
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
          <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canRead || loading" @click="refreshAll">{{ tp("refresh") }}</button>
        </div>
      </div>
    </section>

    <section v-if="feedback.message" class="finance-payroll-feedback" :data-tone="feedback.tone">
      <div>
        <strong>{{ feedback.title }}</strong>
        <span>{{ feedback.message }}</span>
      </div>
      <button type="button" @click="clearFeedback">{{ tp("clearFeedback") }}</button>
    </section>

    <section v-if="!tenantScopeId || !accessToken" class="module-card finance-payroll-empty">
      <p class="eyebrow">{{ tp("missingScopeTitle") }}</p>
      <h3>{{ tp("missingScopeBody") }}</h3>
    </section>

    <section v-else-if="!actionState.canRead" class="module-card finance-payroll-empty">
      <p class="eyebrow">{{ tp("missingPermissionTitle") }}</p>
      <h3>{{ tp("missingPermissionBody") }}</h3>
    </section>

    <div v-else class="finance-payroll-grid">
      <section class="module-card finance-payroll-panel">
        <div class="finance-payroll-panel__header"><h3>{{ tp("tariffsTitle") }}</h3></div>
        <form class="finance-payroll-form-grid" @submit.prevent="submitTariffTable">
          <label class="field-stack"><span>{{ tp("tariffCode") }}</span><input v-model="tariffDraft.code" required /></label>
          <label class="field-stack"><span>{{ tp("tariffTitle") }}</span><input v-model="tariffDraft.title" required /></label>
          <label class="field-stack"><span>{{ tp("tariffRegion") }}</span><input v-model="tariffDraft.region_code" required /></label>
          <label class="field-stack"><span>{{ tp("tariffStatus") }}</span><select v-model="tariffDraft.status"><option value="draft">draft</option><option value="active">active</option><option value="archived">archived</option></select></label>
          <label class="field-stack"><span>{{ tp("effectiveFrom") }}</span><input v-model="tariffDraft.effective_from" type="date" required /></label>
          <label class="field-stack"><span>{{ tp("effectiveUntil") }}</span><input v-model="tariffDraft.effective_until" type="date" /></label>
          <button class="cta-button" type="submit" :disabled="!actionState.canWrite || loading">{{ tp("createTariff") }}</button>
        </form>
        <div v-if="tariffTables.length" class="finance-payroll-list">
          <button v-for="row in tariffTables" :key="row.id" class="finance-payroll-row" :class="{ selected: row.id === selectedTariffId }" type="button" @click="selectedTariffId = row.id">
            <strong>{{ row.code }}</strong>
            <span>{{ row.region_code }} · {{ row.status }}</span>
          </button>
        </div>
        <p v-else class="finance-payroll-empty-copy">{{ tp("tariffsEmpty") }}</p>
      </section>

      <section class="module-card finance-payroll-panel">
        <div class="finance-payroll-panel__header"><h3>{{ tp("ratesTitle") }}</h3></div>
        <form class="finance-payroll-form-grid" @submit.prevent="submitTariffRate">
          <label class="field-stack"><span>{{ tp("functionTypeId") }}</span><input v-model="rateDraft.function_type_id" /></label>
          <label class="field-stack"><span>{{ tp("qualificationTypeId") }}</span><input v-model="rateDraft.qualification_type_id" /></label>
          <label class="field-stack"><span>{{ tp("employmentType") }}</span><input v-model="rateDraft.employment_type_code" /></label>
          <label class="field-stack"><span>{{ tp("payUnit") }}</span><input v-model="rateDraft.pay_unit_code" /></label>
          <label class="field-stack"><span>{{ tp("currency") }}</span><input v-model="rateDraft.currency_code" /></label>
          <label class="field-stack"><span>{{ tp("amount") }}</span><input v-model.number="rateDraft.base_amount" type="number" step="0.01" /></label>
          <label class="field-stack"><span>{{ tp("payrollCode") }}</span><input v-model="rateDraft.payroll_code" /></label>
          <button class="cta-button" type="submit" :disabled="!actionState.canWrite || !selectedTariffId || loading">{{ tp("addRate") }}</button>
        </form>
        <form class="finance-payroll-form-grid" @submit.prevent="submitSurchargeRule">
          <label class="field-stack"><span>{{ tp("surchargeType") }}</span><input v-model="surchargeDraft.surcharge_type_code" required /></label>
          <label class="field-stack"><span>{{ tp("weekdayMask") }}</span><input v-model.number="surchargeDraft.weekday_mask" type="number" min="0" max="127" /></label>
          <label class="field-stack"><span>{{ tp("startMinute") }}</span><input v-model.number="surchargeDraft.start_minute_local" type="number" min="0" max="1439" /></label>
          <label class="field-stack"><span>{{ tp("endMinute") }}</span><input v-model.number="surchargeDraft.end_minute_local" type="number" min="1" max="1440" /></label>
          <label class="field-stack"><span>{{ tp("percentValue") }}</span><input v-model.number="surchargeDraft.percent_value" type="number" step="0.01" /></label>
          <label class="field-stack"><span>{{ tp("fixedAmount") }}</span><input v-model.number="surchargeDraft.fixed_amount" type="number" step="0.01" /></label>
          <label class="field-stack"><span>{{ tp("payrollCode") }}</span><input v-model="surchargeDraft.payroll_code" /></label>
          <button class="cta-button" type="submit" :disabled="!actionState.canWrite || !selectedTariffId || loading">{{ tp("addSurcharge") }}</button>
        </form>
        <div v-if="selectedTariff?.rates.length" class="finance-payroll-stack">
          <article v-for="row in selectedTariff.rates" :key="row.id" class="finance-payroll-chip">
            <strong>{{ row.payroll_code || row.id }}</strong><span>{{ row.base_amount }} {{ row.currency_code }}</span>
          </article>
        </div>
        <div v-if="selectedTariff?.surcharge_rules.length" class="finance-payroll-stack">
          <article v-for="row in selectedTariff.surcharge_rules" :key="row.id" class="finance-payroll-chip">
            <strong>{{ row.surcharge_type_code }}</strong><span>{{ row.percent_value ?? row.fixed_amount }}</span>
          </article>
        </div>
      </section>

      <section class="module-card finance-payroll-panel">
        <div class="finance-payroll-panel__header"><h3>{{ tp("profilesTitle") }}</h3></div>
        <form class="finance-payroll-form-grid" @submit.prevent="submitPayProfile">
          <label class="field-stack"><span>{{ tp("employeeId") }}</span><input v-model="profileDraft.employee_id" required /></label>
          <label class="field-stack"><span>{{ tp("tariffTableId") }}</span><input v-model="profileDraft.tariff_table_id" /></label>
          <label class="field-stack"><span>{{ tp("tariffRegion") }}</span><input v-model="profileDraft.payroll_region_code" required /></label>
          <label class="field-stack"><span>{{ tp("employmentType") }}</span><input v-model="profileDraft.employment_type_code" required /></label>
          <label class="field-stack"><span>{{ tp("payCycle") }}</span><input v-model="profileDraft.pay_cycle_code" /></label>
          <label class="field-stack"><span>{{ tp("payUnit") }}</span><input v-model="profileDraft.pay_unit_code" /></label>
          <label class="field-stack"><span>{{ tp("currency") }}</span><input v-model="profileDraft.currency_code" /></label>
          <label class="field-stack"><span>{{ tp("exportEmployeeCode") }}</span><input v-model="profileDraft.export_employee_code" /></label>
          <label class="field-stack"><span>{{ tp("costCenter") }}</span><input v-model="profileDraft.cost_center_code" /></label>
          <label class="field-stack"><span>{{ tp("baseRateOverride") }}</span><input v-model.number="profileDraft.base_rate_override" type="number" step="0.01" /></label>
          <label class="field-stack"><span>{{ tp("effectiveFrom") }}</span><input v-model="profileDraft.effective_from" type="date" required /></label>
          <button class="cta-button" type="submit" :disabled="!actionState.canWrite || loading">{{ tp("createProfile") }}</button>
        </form>
        <div v-if="payProfiles.length" class="finance-payroll-stack">
          <article v-for="row in payProfiles" :key="row.id" class="finance-payroll-chip">
            <strong>{{ row.employee_id }}</strong><span>{{ row.employment_type_code }} · {{ row.export_employee_code || "-" }}</span>
          </article>
        </div>
        <p v-else class="finance-payroll-empty-copy">{{ tp("profilesEmpty") }}</p>
      </section>

      <section class="module-card finance-payroll-panel">
        <div class="finance-payroll-panel__header"><h3>{{ tp("exportTitle") }}</h3></div>
        <form class="finance-payroll-form-grid" @submit.prevent="submitExportBatch">
          <label class="field-stack"><span>{{ tp("providerKey") }}</span><input v-model="exportDraft.provider_key" required /></label>
          <label class="field-stack"><span>{{ tp("periodStart") }}</span><input v-model="exportDraft.period_start" type="date" required /></label>
          <label class="field-stack"><span>{{ tp("periodEnd") }}</span><input v-model="exportDraft.period_end" type="date" required /></label>
          <button class="cta-button" type="submit" :disabled="!actionState.canExport || loading">{{ tp("generateExport") }}</button>
        </form>
        <div v-if="exportBatches.length" class="finance-payroll-stack">
          <article v-for="row in exportBatches" :key="row.id" class="finance-payroll-chip">
            <strong>{{ row.batch_no }}</strong><span :data-tone="payrollBatchTone(row.status)">{{ row.status }} · {{ row.item_count }} · {{ row.total_amount }} {{ row.currency_code }}</span>
          </article>
        </div>
        <p v-else class="finance-payroll-empty-copy">{{ tp("exportEmpty") }}</p>
      </section>

      <section class="module-card finance-payroll-panel">
        <div class="finance-payroll-panel__header"><h3>{{ tp("archiveTitle") }}</h3></div>
        <form class="finance-payroll-form-grid" @submit.prevent="submitArchive">
          <label class="field-stack"><span>{{ tp("employeeId") }}</span><input v-model="archiveDraft.employee_id" required /></label>
          <label class="field-stack"><span>{{ tp("providerKey") }}</span><input v-model="archiveDraft.provider_key" required /></label>
          <label class="field-stack"><span>{{ tp("periodStart") }}</span><input v-model="archiveDraft.period_start" type="date" required /></label>
          <label class="field-stack"><span>{{ tp("periodEnd") }}</span><input v-model="archiveDraft.period_end" type="date" required /></label>
          <label class="field-stack"><span>{{ tp("sourceDocumentId") }}</span><input v-model="archiveDraft.source_document_id" required /></label>
          <button class="cta-button" type="submit" :disabled="!actionState.canWrite || loading">{{ tp("createArchive") }}</button>
        </form>
        <div v-if="archives.length" class="finance-payroll-stack">
          <article v-for="row in archives" :key="row.id" class="finance-payroll-chip">
            <strong>{{ row.employee_id }}</strong><span>{{ row.provider_key }} · {{ row.archive_status_code }}</span>
          </article>
        </div>
        <p v-else class="finance-payroll-empty-copy">{{ tp("archiveEmpty") }}</p>
      </section>

      <section class="module-card finance-payroll-panel finance-payroll-panel--wide">
        <div class="finance-payroll-panel__header"><h3>{{ tp("reconciliationTitle") }}</h3></div>
        <div class="finance-payroll-summary">
          <article class="finance-payroll-card"><strong>{{ reconciliationSummary.total }}</strong><span>Total</span></article>
          <article class="finance-payroll-card"><strong>{{ reconciliationSummary.missingExport }}</strong><span>{{ tp("missingExport") }}</span></article>
          <article class="finance-payroll-card"><strong>{{ reconciliationSummary.missingPayslip }}</strong><span>{{ tp("missingPayslip") }}</span></article>
          <article class="finance-payroll-card"><strong>{{ reconciliationSummary.exportedAmountTotal }}</strong><span>{{ tp("exportedAmountTotal") }}</span></article>
        </div>
        <div v-if="reconciliationRows.length" class="finance-payroll-stack">
          <article v-for="row in reconciliationRows" :key="row.employee_id" class="finance-payroll-chip">
            <strong>{{ row.employee_id }}</strong>
            <span>{{ tp("payableMinutes") }}: {{ row.payable_minutes }}</span>
            <span>{{ tp("missingExport") }}: {{ row.missing_export ? "yes" : "no" }}</span>
            <span>{{ tp("missingPayslip") }}: {{ row.missing_payslip ? "yes" : "no" }}</span>
          </article>
        </div>
        <p v-else class="finance-payroll-empty-copy">{{ tp("reconciliationEmpty") }}</p>
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from "vue";

import {
  addPayrollSurchargeRule,
  addPayrollTariffRate,
  createEmployeePayProfile,
  createPayrollPayslipArchive,
  createPayrollTariffTable,
  generatePayrollExportBatch,
  listEmployeePayProfiles,
  listPayrollExportBatches,
  listPayrollPayslipArchives,
  listPayrollReconciliationRows,
  listPayrollTariffTables,
  type PayrollTariffTableRead,
} from "../api/financePayroll";
import {
  deriveFinancePayrollActionState,
  mapFinancePayrollApiMessage,
  payrollBatchTone,
  summarizePayrollReconciliation,
} from "../features/finance/financePayroll.helpers";
import { financePayrollMessages } from "../i18n/financePayroll.messages";

const locale = ref<"de" | "en">("de");
const role = ref("accounting");
const tenantScopeInput = ref("");
const accessTokenInput = ref("");
const tenantScopeId = ref("");
const accessToken = ref("");
const loading = ref(false);
const tariffTables = ref<any[]>([]);
const selectedTariffId = ref("");
const payProfiles = ref<any[]>([]);
const exportBatches = ref<any[]>([]);
const archives = ref<any[]>([]);
const reconciliationRows = ref<any[]>([]);

const tariffDraft = reactive({
  code: "",
  title: "",
  region_code: "",
  status: "draft",
  effective_from: "",
  effective_until: "",
});
const rateDraft = reactive({
  function_type_id: "",
  qualification_type_id: "",
  employment_type_code: "",
  pay_unit_code: "hour",
  currency_code: "EUR",
  base_amount: 0,
  payroll_code: "",
});
const surchargeDraft = reactive({
  surcharge_type_code: "",
  weekday_mask: 127,
  start_minute_local: 0,
  end_minute_local: 1440,
  percent_value: undefined as number | undefined,
  fixed_amount: undefined as number | undefined,
  payroll_code: "",
});
const profileDraft = reactive({
  employee_id: "",
  tariff_table_id: "",
  payroll_region_code: "",
  employment_type_code: "",
  pay_cycle_code: "monthly",
  pay_unit_code: "hour",
  currency_code: "EUR",
  export_employee_code: "",
  cost_center_code: "",
  base_rate_override: undefined as number | undefined,
  effective_from: "",
});
const exportDraft = reactive({
  provider_key: "generic_csv",
  period_start: "",
  period_end: "",
});
const archiveDraft = reactive({
  employee_id: "",
  provider_key: "generic_csv",
  period_start: "",
  period_end: "",
  source_document_id: "",
});
const feedback = reactive({ tone: "neutral", title: "", message: "" });

const actionState = computed(() => deriveFinancePayrollActionState(role.value));
const selectedTariff = computed(() => tariffTables.value.find((row) => row.id === selectedTariffId.value) ?? null);
const reconciliationSummary = computed(() => summarizePayrollReconciliation(reconciliationRows.value));

function tp(key: keyof typeof financePayrollMessages.de) {
  return financePayrollMessages[locale.value][key];
}

function setFeedback(tone: string, title: string, message: string) {
  feedback.tone = tone;
  feedback.title = title;
  feedback.message = message;
}

function clearFeedback() {
  feedback.tone = "neutral";
  feedback.title = "";
  feedback.message = "";
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
  try {
    const today = new Date().toISOString().slice(0, 10);
    tariffTables.value = await listPayrollTariffTables(tenantScopeId.value, accessToken.value, {});
    selectedTariffId.value = selectedTariffId.value || tariffTables.value[0]?.id || "";
    payProfiles.value = await listEmployeePayProfiles(tenantScopeId.value, accessToken.value, {});
    exportBatches.value = await listPayrollExportBatches(tenantScopeId.value, accessToken.value, {});
    archives.value = await listPayrollPayslipArchives(tenantScopeId.value, accessToken.value, {});
    reconciliationRows.value = await listPayrollReconciliationRows(tenantScopeId.value, accessToken.value, {
      period_start: exportDraft.period_start || today.slice(0, 8) + "01",
      period_end: exportDraft.period_end || today,
    });
  } catch (error) {
    handleApiError(error);
  } finally {
    loading.value = false;
  }
}

async function submitTariffTable() {
  await runSave(async () => {
    const created = await createPayrollTariffTable(tenantScopeId.value, accessToken.value, {
      ...tariffDraft,
      effective_until: tariffDraft.effective_until || null,
    });
    tariffTables.value = [...tariffTables.value, created];
    selectedTariffId.value = created.id;
  });
}

async function submitTariffRate() {
  if (!selectedTariffId.value) return;
  await runSave(async () => {
    const updated = await addPayrollTariffRate(tenantScopeId.value, selectedTariffId.value, accessToken.value, {
      ...rateDraft,
      function_type_id: rateDraft.function_type_id || null,
      qualification_type_id: rateDraft.qualification_type_id || null,
      employment_type_code: rateDraft.employment_type_code || null,
      payroll_code: rateDraft.payroll_code || null,
    });
    replaceTariff(updated);
  });
}

async function submitSurchargeRule() {
  if (!selectedTariffId.value) return;
  await runSave(async () => {
    const updated = await addPayrollSurchargeRule(tenantScopeId.value, selectedTariffId.value, accessToken.value, {
      ...surchargeDraft,
      percent_value: surchargeDraft.percent_value ?? null,
      fixed_amount: surchargeDraft.fixed_amount ?? null,
      payroll_code: surchargeDraft.payroll_code || null,
    });
    replaceTariff(updated);
  });
}

async function submitPayProfile() {
  await runSave(async () => {
    const created = await createEmployeePayProfile(tenantScopeId.value, accessToken.value, {
      ...profileDraft,
      tariff_table_id: profileDraft.tariff_table_id || null,
      export_employee_code: profileDraft.export_employee_code || null,
      cost_center_code: profileDraft.cost_center_code || null,
      base_rate_override: profileDraft.base_rate_override ?? null,
      effective_until: null,
    });
    payProfiles.value = [created, ...payProfiles.value];
  });
}

async function submitExportBatch() {
  await runSave(async () => {
    const created = await generatePayrollExportBatch(tenantScopeId.value, accessToken.value, exportDraft);
    exportBatches.value = [created, ...exportBatches.value];
    await refreshAll();
  });
}

async function submitArchive() {
  await runSave(async () => {
    const created = await createPayrollPayslipArchive(tenantScopeId.value, accessToken.value, archiveDraft);
    archives.value = [created, ...archives.value];
    await refreshAll();
  });
}

async function runSave(action: () => Promise<void>) {
  loading.value = true;
  try {
    await action();
    setFeedback("success", tp("saveSuccess"), tp("saveSuccess"));
  } catch (error) {
    handleApiError(error);
  } finally {
    loading.value = false;
  }
}

function replaceTariff(updated: PayrollTariffTableRead) {
  tariffTables.value = tariffTables.value.map((row) => (row.id === updated.id ? updated : row));
}

function handleApiError(error: unknown) {
  const messageKey = typeof error === "object" && error && "messageKey" in error ? String((error as any).messageKey) : "errors.platform.internal";
  setFeedback("error", tp("error"), tp(mapFinancePayrollApiMessage(messageKey) as keyof typeof financePayrollMessages.de));
}
</script>

<style scoped>
.finance-payroll-page,
.finance-payroll-grid,
.finance-payroll-form-grid,
.finance-payroll-summary,
.finance-payroll-meta,
.finance-payroll-stack {
  display: grid;
  gap: 1rem;
}

.finance-payroll-grid {
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
}

.finance-payroll-panel--wide {
  grid-column: 1 / -1;
}

.finance-payroll-hero,
.finance-payroll-row,
.finance-payroll-chip,
.finance-payroll-card,
.finance-payroll-pill,
.finance-payroll-feedback,
.finance-payroll-empty {
  border-radius: 18px;
  padding: 1rem;
  background: #f5fbfb;
}

.finance-payroll-row,
.finance-payroll-chip {
  text-align: left;
  border: 0;
}

.finance-payroll-row.selected {
  outline: 2px solid rgb(40,170,170);
}

.finance-payroll-summary {
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
}

.finance-payroll-feedback[data-tone="error"] {
  background: #fff0f0;
}

.finance-payroll-feedback[data-tone="success"] {
  background: #effaf3;
}

@media (max-width: 900px) {
  .finance-payroll-grid {
    grid-template-columns: 1fr;
  }
}
</style>
