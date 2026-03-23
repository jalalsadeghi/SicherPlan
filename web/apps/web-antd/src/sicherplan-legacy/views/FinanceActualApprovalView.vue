<template>
  <section class="finance-actuals-page">
    <section class="module-card finance-actuals-hero">
      <div>
        <p class="eyebrow">{{ tp("eyebrow") }}</p>
        <h2>{{ tp("title") }}</h2>
        <p class="finance-actuals-lead">{{ tp("lead") }}</p>
        <div class="finance-actuals-meta">
          <span class="finance-actuals-pill">{{ tp("permissionRead") }}: {{ actionState.canRead ? "on" : "off" }}</span>
          <span class="finance-actuals-pill">{{ tp("permissionWrite") }}: {{ actionState.canWrite ? "on" : "off" }}</span>
          <span class="finance-actuals-pill">{{ tp("permissionApprove") }}: {{ actionState.canApprove ? "on" : "off" }}</span>
          <span class="finance-actuals-pill">{{ tp("permissionSignoff") }}: {{ actionState.canSignoff ? "on" : "off" }}</span>
        </div>
      </div>

      <div class="module-card finance-actuals-scope">
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

    <section v-if="feedback.message" class="finance-actuals-feedback" :data-tone="feedback.tone">
      <div>
        <strong>{{ feedback.title }}</strong>
        <span>{{ feedback.message }}</span>
      </div>
      <button type="button" @click="clearFeedback">{{ tp("clearFeedback") }}</button>
    </section>

    <section v-if="!tenantScopeId || !accessToken" class="module-card finance-actuals-empty">
      <p class="eyebrow">{{ tp("missingScopeTitle") }}</p>
      <h3>{{ tp("missingScopeBody") }}</h3>
    </section>

    <section v-else-if="!actionState.canRead" class="module-card finance-actuals-empty">
      <p class="eyebrow">{{ tp("missingPermissionTitle") }}</p>
      <h3>{{ tp("missingPermissionBody") }}</h3>
    </section>

    <div v-else class="finance-actuals-grid">
      <section class="module-card finance-actuals-panel">
        <div class="finance-actuals-filter-grid">
          <label class="field-stack">
            <span>{{ tp("filtersShift") }}</span>
            <input v-model="filters.shift_id" />
          </label>
          <label class="field-stack">
            <span>{{ tp("filtersAssignment") }}</span>
            <input v-model="filters.assignment_id" />
          </label>
          <label class="field-stack">
            <span>{{ tp("filtersApprovalStage") }}</span>
            <select v-model="filters.approval_stage_code">
              <option value=""></option>
              <option value="draft">{{ tp("stageDraft") }}</option>
              <option value="preliminary_submitted">{{ tp("stagePreliminarySubmitted") }}</option>
              <option value="operational_confirmed">{{ tp("stageOperationalConfirmed") }}</option>
              <option value="finance_signed_off">{{ tp("stageFinanceSignedOff") }}</option>
            </select>
          </label>
        </div>

        <div class="finance-actuals-summary">
          <article class="finance-actuals-card"><strong>{{ summary.total }}</strong><span>{{ tp("summaryTotal") }}</span></article>
          <article class="finance-actuals-card" data-tone="bad"><strong>{{ summary.draft }}</strong><span>{{ tp("summaryDraft") }}</span></article>
          <article class="finance-actuals-card" data-tone="neutral"><strong>{{ summary.preliminarySubmitted }}</strong><span>{{ tp("summaryPreliminary") }}</span></article>
          <article class="finance-actuals-card" data-tone="warn"><strong>{{ summary.operationalConfirmed }}</strong><span>{{ tp("summaryOperational") }}</span></article>
          <article class="finance-actuals-card" data-tone="good"><strong>{{ summary.financeSignedOff }}</strong><span>{{ tp("summaryFinance") }}</span></article>
        </div>
      </section>

      <section class="module-card finance-actuals-panel">
        <div class="finance-actuals-panel__header">
          <div>
            <p class="eyebrow">{{ tp("listTitle") }}</p>
            <h3>{{ tp("listTitle") }}</h3>
          </div>
        </div>
        <div v-if="actualRows.length" class="finance-actuals-list">
          <button
            v-for="row in actualRows"
            :key="row.id"
            type="button"
            class="finance-actuals-row"
            :class="{ selected: row.id === selectedActualId }"
            @click="selectedActualId = row.id"
          >
            <div>
              <strong>{{ row.assignment_id }}</strong>
              <span>{{ row.payable_minutes }} / {{ row.billable_minutes }} min</span>
              <span>{{ row.discrepancy_state_code }}</span>
            </div>
            <span class="finance-actuals-state" :data-tone="approvalStageTone(row.approval_stage_code)">
              {{ stageLabel(row.approval_stage_code) }}
            </span>
          </button>
        </div>
        <p v-else class="finance-actuals-list-empty">{{ tp("listEmpty") }}</p>
      </section>

      <section class="module-card finance-actuals-panel finance-actuals-detail">
        <div class="finance-actuals-panel__header">
          <div>
            <p class="eyebrow">{{ tp("detailTitle") }}</p>
            <h3>{{ selectedActual ? selectedActual.assignment_id : tp("detailTitle") }}</h3>
          </div>
          <span v-if="selectedActual" class="finance-actuals-state" :data-tone="approvalStageTone(selectedActual.approval_stage_code)">
            {{ stageLabel(selectedActual.approval_stage_code) }}
          </span>
        </div>

        <template v-if="selectedActual">
          <div class="finance-actuals-metrics">
            <span>Payable: {{ selectedActual.payable_minutes }}</span>
            <span>Billable: {{ selectedActual.billable_minutes }}</span>
            <span>Cust adj: {{ selectedActual.customer_adjustment_minutes }}</span>
            <span>Discrepancy: {{ selectedActual.discrepancy_state_code }}</span>
          </div>

          <section class="module-card finance-actuals-subpanel">
            <div class="cta-row">
              <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canSubmitPreliminary || loading" @click="runPreliminary">{{ tp("preliminaryAction") }}</button>
              <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canConfirmOperational || loading" @click="runOperational">{{ tp("operationalAction") }}</button>
              <button class="cta-button" type="button" :disabled="!actionState.canFinanceSignoff || loading" @click="runFinanceSignoff">{{ tp("financeAction") }}</button>
            </div>
            <label class="field-stack">
              <span>{{ tp("noteLabel") }}</span>
              <textarea v-model="noteText" rows="2" />
            </label>
          </section>

          <section class="module-card finance-actuals-subpanel">
            <div class="finance-actuals-panel__header"><h4>{{ tp("discrepancyTitle") }}</h4></div>
            <div v-if="selectedActual.discrepancies.length" class="finance-actuals-stack">
              <article v-for="issue in selectedActual.discrepancies" :key="issue.code" class="finance-actuals-issue">
                <strong>{{ issue.code }}</strong>
                <span>{{ issue.message_key }}</span>
              </article>
            </div>
            <p v-else class="finance-actuals-list-empty">{{ tp("discrepancyEmpty") }}</p>
          </section>

          <section class="module-card finance-actuals-subpanel">
            <div class="finance-actuals-panel__header"><h4>{{ tp("approvalTitle") }}</h4></div>
            <div v-if="selectedActual.approvals.length" class="finance-actuals-stack">
              <article v-for="row in selectedActual.approvals" :key="row.id" class="finance-actuals-issue">
                <strong>{{ stageLabel(row.stage_code) }}</strong>
                <span>{{ row.actor_scope_code }} · {{ row.note_text || "-" }}</span>
              </article>
            </div>
            <p v-else class="finance-actuals-list-empty">{{ tp("approvalEmpty") }}</p>
          </section>

          <section class="module-card finance-actuals-subpanel">
            <div class="finance-actuals-panel__header"><h4>{{ tp("reconciliationTitle") }}</h4></div>
            <form class="finance-actuals-form-grid" @submit.prevent="submitReconciliation">
              <label class="field-stack"><span>{{ tp("reconciliationKind") }}</span><select v-model="reconciliationDraft.reconciliation_kind_code"><option value="sickness">sickness</option><option value="cancellation">cancellation</option><option value="replacement">replacement</option><option value="customer_adjustment">customer_adjustment</option><option value="flat_rate">flat_rate</option></select></label>
              <label class="field-stack"><span>{{ tp("reasonCode") }}</span><input v-model="reconciliationDraft.reason_code" required /></label>
              <label class="field-stack"><span>{{ tp("payrollDelta") }}</span><input v-model.number="reconciliationDraft.payroll_minutes_delta" type="number" /></label>
              <label class="field-stack"><span>{{ tp("billableDelta") }}</span><input v-model.number="reconciliationDraft.billable_minutes_delta" type="number" /></label>
              <label class="field-stack"><span>{{ tp("customerAdjustmentDelta") }}</span><input v-model.number="reconciliationDraft.customer_adjustment_minutes_delta" type="number" /></label>
              <label class="field-stack"><span>{{ tp("replacementActorType") }}</span><select v-model="reconciliationDraft.replacement_actor_type_code"><option value=""></option><option value="employee">employee</option><option value="subcontractor_worker">subcontractor_worker</option></select></label>
              <label class="field-stack"><span>{{ tp("replacementEmployeeId") }}</span><input v-model="reconciliationDraft.replacement_employee_id" /></label>
              <label class="field-stack field-stack--wide"><span>{{ tp("noteLabel") }}</span><textarea v-model="reconciliationDraft.note_text" rows="2" /></label>
              <button class="cta-button" type="submit" :disabled="!actionState.canEditFinanceLines || loading">{{ tp("addReconciliation") }}</button>
            </form>
            <div v-if="selectedActual.reconciliations.length" class="finance-actuals-stack">
              <article v-for="row in selectedActual.reconciliations" :key="row.id" class="finance-actuals-issue">
                <strong>{{ row.reconciliation_kind_code }} · {{ row.reason_code }}</strong>
                <span>{{ row.payroll_minutes_delta }} / {{ row.billable_minutes_delta }} / {{ row.customer_adjustment_minutes_delta }}</span>
              </article>
            </div>
            <p v-else class="finance-actuals-list-empty">{{ tp("reconciliationEmpty") }}</p>
          </section>

          <section class="module-card finance-actuals-subpanel">
            <div class="finance-actuals-panel__header"><h4>{{ tp("allowanceTitle") }}</h4></div>
            <form class="finance-actuals-form-grid" @submit.prevent="submitAllowance">
              <label class="field-stack"><span>{{ tp("allowanceType") }}</span><select v-model="allowanceDraft.line_type_code"><option value="allowance">allowance</option><option value="flat_rate">flat_rate</option><option value="customer_flat_rate">customer_flat_rate</option></select></label>
              <label class="field-stack"><span>{{ tp("reasonCode") }}</span><input v-model="allowanceDraft.reason_code" required /></label>
              <label class="field-stack"><span>{{ tp("amountTotal") }}</span><input v-model.number="allowanceDraft.amount_total" type="number" step="0.01" /></label>
              <label class="field-stack"><span>{{ tp("currencyCode") }}</span><input v-model="allowanceDraft.currency_code" /></label>
              <button class="cta-button" type="submit" :disabled="!actionState.canEditFinanceLines || loading">{{ tp("addAllowance") }}</button>
            </form>
            <div v-if="selectedActual.allowances.length" class="finance-actuals-stack">
              <article v-for="row in selectedActual.allowances" :key="row.id" class="finance-actuals-issue"><strong>{{ row.line_type_code }}</strong><span>{{ row.amount_total }} {{ row.currency_code }}</span></article>
            </div>
            <p v-else class="finance-actuals-list-empty">{{ tp("allowanceEmpty") }}</p>
          </section>

          <section class="module-card finance-actuals-subpanel">
            <div class="finance-actuals-panel__header"><h4>{{ tp("expenseTitle") }}</h4></div>
            <form class="finance-actuals-form-grid" @submit.prevent="submitExpense">
              <label class="field-stack"><span>{{ tp("expenseType") }}</span><input v-model="expenseDraft.expense_type_code" required /></label>
              <label class="field-stack"><span>{{ tp("reasonCode") }}</span><input v-model="expenseDraft.reason_code" required /></label>
              <label class="field-stack"><span>{{ tp("amountTotal") }}</span><input v-model.number="expenseDraft.amount_total" type="number" step="0.01" /></label>
              <label class="field-stack"><span>{{ tp("currencyCode") }}</span><input v-model="expenseDraft.currency_code" /></label>
              <button class="cta-button" type="submit" :disabled="!actionState.canEditFinanceLines || loading">{{ tp("addExpense") }}</button>
            </form>
            <div v-if="selectedActual.expenses.length" class="finance-actuals-stack">
              <article v-for="row in selectedActual.expenses" :key="row.id" class="finance-actuals-issue"><strong>{{ row.expense_type_code }}</strong><span>{{ row.amount_total }} {{ row.currency_code }}</span></article>
            </div>
            <p v-else class="finance-actuals-list-empty">{{ tp("expenseEmpty") }}</p>
          </section>

          <section class="module-card finance-actuals-subpanel">
            <div class="finance-actuals-panel__header"><h4>{{ tp("commentTitle") }}</h4></div>
            <form class="finance-actuals-form-grid" @submit.prevent="submitComment">
              <label class="field-stack"><span>{{ tp("commentVisibility") }}</span><select v-model="commentDraft.visibility_code"><option value="shared">{{ tp("visibilityShared") }}</option><option value="finance_only">{{ tp("visibilityFinanceOnly") }}</option></select></label>
              <label class="field-stack field-stack--wide"><span>{{ tp("noteLabel") }}</span><textarea v-model="commentDraft.note_text" rows="2" /></label>
              <button class="cta-button" type="submit" :disabled="!selectedActual || loading">{{ tp("addComment") }}</button>
            </form>
            <div v-if="selectedActual.comments.length" class="finance-actuals-stack">
              <article v-for="row in selectedActual.comments" :key="row.id" class="finance-actuals-issue"><strong>{{ row.visibility_code }}</strong><span>{{ row.note_text }}</span></article>
            </div>
            <p v-else class="finance-actuals-list-empty">{{ tp("commentEmpty") }}</p>
          </section>

          <section class="module-card finance-actuals-subpanel">
            <div class="finance-actuals-panel__header"><h4>{{ tp("auditTitle") }}</h4></div>
            <div v-if="auditRows.length" class="finance-actuals-stack">
              <article v-for="row in auditRows" :key="row.id" class="finance-actuals-issue"><strong>{{ row.event_type }}</strong><span>{{ row.created_at }}</span></article>
            </div>
            <p v-else class="finance-actuals-list-empty">{{ tp("auditEmpty") }}</p>
          </section>
        </template>

        <section v-else class="finance-actuals-empty">
          <h3>{{ tp("noSelection") }}</h3>
        </section>
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";

import {
  createFinanceAllowance,
  createFinanceComment,
  createFinanceExpense,
  createFinanceReconciliation,
  financeSignoffActual,
  getFinanceActual,
  getFinanceActualAuditHistory,
  listFinanceActuals,
  confirmOperationalActual,
  submitPreliminaryActual,
  type FinanceActualRead,
} from "../api/financeActuals";
import {
  approvalStageTone,
  deriveFinanceActualActionState,
  mapFinanceActualApiMessage,
  summarizeActuals,
} from "../features/finance/financeActuals.helpers";
import { financeActualsMessages } from "../i18n/financeActuals.messages";

const locale = ref<"de" | "en">("de");
const role = ref("accounting");
const tenantScopeInput = ref("");
const accessTokenInput = ref("");
const tenantScopeId = ref("");
const accessToken = ref("");
const loading = ref(false);
const actualRows = ref<any[]>([]);
const selectedActualId = ref("");
const selectedActual = ref<FinanceActualRead | null>(null);
const auditRows = ref<any[]>([]);
const noteText = ref("");

const filters = reactive({
  shift_id: "",
  assignment_id: "",
  approval_stage_code: "",
});

const reconciliationDraft = reactive({
  reconciliation_kind_code: "sickness",
  reason_code: "",
  payroll_minutes_delta: 0,
  billable_minutes_delta: 0,
  customer_adjustment_minutes_delta: 0,
  replacement_actor_type_code: "",
  replacement_employee_id: "",
  note_text: "",
});

const allowanceDraft = reactive({
  line_type_code: "allowance",
  reason_code: "",
  amount_total: 0,
  currency_code: "EUR",
});

const expenseDraft = reactive({
  expense_type_code: "",
  reason_code: "",
  amount_total: 0,
  currency_code: "EUR",
});

const commentDraft = reactive({
  visibility_code: "shared",
  note_text: "",
});

const feedback = reactive({
  tone: "neutral",
  title: "",
  message: "",
});

const actionState = computed(() => deriveFinanceActualActionState(role.value, selectedActual.value));
const summary = computed(() => summarizeActuals(actualRows.value));

function tp(key: keyof typeof financeActualsMessages.de) {
  return financeActualsMessages[locale.value][key];
}

function stageLabel(stage: string) {
  switch (stage) {
    case "preliminary_submitted":
      return tp("stagePreliminarySubmitted");
    case "operational_confirmed":
      return tp("stageOperationalConfirmed");
    case "finance_signed_off":
      return tp("stageFinanceSignedOff");
    default:
      return tp("stageDraft");
  }
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
    actualRows.value = await listFinanceActuals(tenantScopeId.value, accessToken.value, filters);
    if (!selectedActualId.value && actualRows.value.length) {
      selectedActualId.value = actualRows.value[0].id;
    }
    if (selectedActualId.value) {
      await loadSelectedActual();
    }
  } catch (error: any) {
    setFeedback("error", tp("error"), tp(mapFinanceActualApiMessage(error.messageKey) as keyof typeof financeActualsMessages.de));
  } finally {
    loading.value = false;
  }
}

async function loadSelectedActual() {
  if (!selectedActualId.value || !tenantScopeId.value || !accessToken.value) {
    return;
  }
  selectedActual.value = await getFinanceActual(tenantScopeId.value, selectedActualId.value, accessToken.value);
  auditRows.value = await getFinanceActualAuditHistory(tenantScopeId.value, selectedActualId.value, accessToken.value);
}

async function runPreliminary() {
  if (!selectedActual.value) return;
  selectedActual.value = await submitPreliminaryActual(tenantScopeId.value, selectedActual.value.id, accessToken.value, noteText.value);
  setFeedback("success", tp("saveSuccess"), tp("saveSuccess"));
  await refreshAll();
}

async function runOperational() {
  if (!selectedActual.value) return;
  selectedActual.value = await confirmOperationalActual(tenantScopeId.value, selectedActual.value.id, accessToken.value, noteText.value);
  setFeedback("success", tp("saveSuccess"), tp("saveSuccess"));
  await refreshAll();
}

async function runFinanceSignoff() {
  if (!selectedActual.value) return;
  selectedActual.value = await financeSignoffActual(tenantScopeId.value, selectedActual.value.id, accessToken.value, noteText.value);
  setFeedback("success", tp("saveSuccess"), tp("saveSuccess"));
  await refreshAll();
}

async function submitReconciliation() {
  if (!selectedActual.value) return;
  selectedActual.value = await createFinanceReconciliation(tenantScopeId.value, selectedActual.value.id, accessToken.value, {
    ...reconciliationDraft,
    replacement_actor_type_code: reconciliationDraft.replacement_actor_type_code || null,
    replacement_employee_id: reconciliationDraft.replacement_employee_id || null,
    note_text: reconciliationDraft.note_text || null,
  });
  setFeedback("success", tp("saveSuccess"), tp("saveSuccess"));
  await refreshAll();
}

async function submitAllowance() {
  if (!selectedActual.value) return;
  selectedActual.value = await createFinanceAllowance(tenantScopeId.value, selectedActual.value.id, accessToken.value, allowanceDraft);
  setFeedback("success", tp("saveSuccess"), tp("saveSuccess"));
  await refreshAll();
}

async function submitExpense() {
  if (!selectedActual.value) return;
  selectedActual.value = await createFinanceExpense(tenantScopeId.value, selectedActual.value.id, accessToken.value, expenseDraft);
  setFeedback("success", tp("saveSuccess"), tp("saveSuccess"));
  await refreshAll();
}

async function submitComment() {
  if (!selectedActual.value) return;
  selectedActual.value = await createFinanceComment(tenantScopeId.value, selectedActual.value.id, accessToken.value, commentDraft);
  setFeedback("success", tp("saveSuccess"), tp("saveSuccess"));
  await refreshAll();
}

watch(selectedActualId, async () => {
  if (!selectedActualId.value || !tenantScopeId.value || !accessToken.value) {
    selectedActual.value = null;
    auditRows.value = [];
    return;
  }
  try {
    await loadSelectedActual();
  } catch (error: any) {
    setFeedback("error", tp("error"), tp(mapFinanceActualApiMessage(error.messageKey) as keyof typeof financeActualsMessages.de));
  }
});
</script>

<style scoped>
.finance-actuals-page,
.finance-actuals-grid,
.finance-actuals-list,
.finance-actuals-stack,
.finance-actuals-form-grid,
.finance-actuals-filter-grid,
.finance-actuals-summary,
.finance-actuals-meta,
.finance-actuals-metrics {
  display: grid;
  gap: 1rem;
}
.finance-actuals-grid {
  grid-template-columns: 1fr 1fr 1.3fr;
}
.finance-actuals-hero {
  display: grid;
  gap: 1rem;
  grid-template-columns: 1.3fr 0.8fr;
}
.finance-actuals-list,
.finance-actuals-stack {
  align-content: start;
}
.finance-actuals-row,
.finance-actuals-issue {
  border: 1px solid var(--el-border-color);
  border-radius: 16px;
  padding: 0.9rem;
  background: rgba(40, 170, 170, 0.06);
}
.finance-actuals-row {
  display: flex;
  justify-content: space-between;
  text-align: left;
}
.finance-actuals-row.selected {
  border-color: rgb(40, 170, 170);
}
.finance-actuals-summary {
  grid-template-columns: repeat(5, minmax(0, 1fr));
}
.finance-actuals-card,
.finance-actuals-pill {
  border: 1px solid var(--el-border-color);
  border-radius: 999px;
  padding: 0.65rem 0.9rem;
}
.finance-actuals-form-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}
.field-stack--wide {
  grid-column: 1 / -1;
}
.finance-actuals-state[data-tone="good"] { color: #177245; }
.finance-actuals-state[data-tone="warn"] { color: #946200; }
.finance-actuals-state[data-tone="bad"] { color: #ab2f2f; }
.finance-actuals-state[data-tone="neutral"] { color: #366a6a; }
.finance-actuals-feedback,
.finance-actuals-empty {
  border: 1px solid var(--el-border-color);
  border-radius: 18px;
  padding: 1rem;
}
@media (max-width: 1100px) {
  .finance-actuals-grid,
  .finance-actuals-hero,
  .finance-actuals-summary,
  .finance-actuals-form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
