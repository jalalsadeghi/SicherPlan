<template>
  <section class="module-card portal-customer-view">
    <p class="eyebrow">{{ t("portalCustomer.eyebrow") }}</p>
    <div class="portal-customer-header">
      <div>
        <h2>{{ t("portalCustomer.title") }}</h2>
        <p>{{ t("portalCustomer.lead") }}</p>
      </div>
      <div class="portal-actions">
        <button class="secondary-button" type="button" @click="refreshPortalContext">
          {{ t("portalCustomer.actions.refresh") }}
        </button>
        <button
          v-if="authStore.hasSession"
          class="secondary-button"
          type="button"
          @click="logoutPortalSession"
        >
          {{ t("portalCustomer.actions.logout") }}
        </button>
      </div>
    </div>

    <p v-if="feedbackKey" class="portal-feedback" :data-tone="feedbackTone">
      {{ t(feedbackKey) }}
    </p>

    <form v-if="accessState === 'login'" class="portal-login-grid" @submit.prevent="submitLogin">
      <div class="field">
        <label for="tenant-code">{{ t("portalCustomer.login.tenantCode") }}</label>
        <input id="tenant-code" v-model.trim="tenantCode" autocomplete="organization" required />
      </div>
      <div class="field">
        <label for="identifier">{{ t("portalCustomer.login.identifier") }}</label>
        <input id="identifier" v-model.trim="identifier" autocomplete="username" required />
      </div>
      <div class="field">
        <label for="password">{{ t("portalCustomer.login.password") }}</label>
        <input id="password" v-model="password" autocomplete="current-password" type="password" required />
      </div>
      <div class="field">
        <label for="device-label">{{ t("portalCustomer.login.deviceLabel") }}</label>
        <input id="device-label" v-model.trim="deviceLabel" autocomplete="off" />
      </div>
      <div class="portal-login-actions">
        <button class="cta-button" type="submit" :disabled="loading">
          {{ t("portalCustomer.actions.login") }}
        </button>
      </div>
    </form>

    <div v-else-if="accessState === 'loading'" class="portal-state-card">
      <h3>{{ t("portalCustomer.loading.title") }}</h3>
      <p>{{ t("portalCustomer.loading.body") }}</p>
    </div>

    <div v-else-if="accessState === 'empty'" class="portal-state-card">
      <h3>{{ t("portalCustomer.empty.title") }}</h3>
      <p>{{ t("portalCustomer.empty.body") }}</p>
    </div>

    <div v-else-if="accessState === 'deactivated'" class="portal-state-card">
      <h3>{{ t("portalCustomer.deactivated.title") }}</h3>
      <p>{{ t("portalCustomer.deactivated.body") }}</p>
    </div>

    <div v-else-if="accessState === 'unauthorized'" class="portal-state-card">
      <h3>{{ t("portalCustomer.unauthorized.title") }}</h3>
      <p>{{ t("portalCustomer.unauthorized.body") }}</p>
    </div>

    <div v-else-if="portalContext" class="portal-stack">
      <div class="portal-summary-grid">
        <article class="portal-summary-card">
          <p class="eyebrow">{{ t("portalCustomer.summary.title") }}</p>
          <dl>
            <div>
              <dt>{{ t("portalCustomer.summary.customerNumber") }}</dt>
              <dd>{{ portalContext.customer.customer_number }}</dd>
            </div>
            <div>
              <dt>{{ t("portalCustomer.summary.customerName") }}</dt>
              <dd>{{ portalContext.customer.name }}</dd>
            </div>
            <div>
              <dt>{{ t("portalCustomer.summary.contact") }}</dt>
              <dd>{{ portalContext.contact.full_name }}</dd>
            </div>
            <div>
              <dt>{{ t("portalCustomer.summary.email") }}</dt>
              <dd>{{ portalContext.contact.email || "-" }}</dd>
            </div>
            <div>
              <dt>{{ t("portalCustomer.summary.function") }}</dt>
              <dd>{{ portalContext.contact.function_label || "-" }}</dd>
            </div>
            <div>
              <dt>{{ t("portalCustomer.summary.tenant") }}</dt>
              <dd>{{ portalContext.tenant_id }}</dd>
            </div>
            <div>
              <dt>{{ t("portalCustomer.summary.scope") }}</dt>
              <dd>{{ portalScopeSummary }}</dd>
            </div>
          </dl>
        </article>

        <article class="portal-summary-card">
          <p class="eyebrow">{{ t("portalCustomer.readOnly.title") }}</p>
          <p>{{ t("portalCustomer.readOnly.body") }}</p>
          <ul class="portal-flags">
            <li>{{ t("portalCustomer.meta.releasedOnly") }}</li>
            <li>{{ t("portalCustomer.meta.customerScoped") }}</li>
            <li>{{ t("portalCustomer.meta.personalNamesRestricted") }}</li>
          </ul>
        </article>
      </div>

      <article class="portal-summary-card">
        <div class="portal-dataset-header">
          <div>
            <p class="eyebrow">{{ t("portalCustomer.history.eyebrow") }}</p>
            <h3>{{ t("portalCustomer.history.title") }}</h3>
            <p>{{ t("portalCustomer.history.lead") }}</p>
          </div>
        </div>
        <div v-if="portalHistory?.items.length" class="portal-history-list">
          <article v-for="entry in portalHistory.items" :key="entry.id" class="portal-history-item">
            <strong>{{ entry.title }}</strong>
            <p>{{ entry.summary }}</p>
            <span class="dataset-meta">{{ formatDateTime(entry.created_at) }}</span>
            <ul v-if="entry.attachments.length" class="portal-list">
              <li v-for="attachment in entry.attachments" :key="attachment.document_id">
                {{ attachment.title }}
              </li>
            </ul>
          </article>
        </div>
        <p v-else class="dataset-meta">{{ t("portalCustomer.history.empty") }}</p>
      </article>

      <div class="portal-dataset-grid">
        <article class="portal-dataset-card">
          <div class="portal-dataset-header">
            <div>
              <p class="eyebrow">{{ t("portalCustomer.datasets.orders.eyebrow") }}</p>
              <h3>{{ t("portalCustomer.datasets.orders.title") }}</h3>
              <p>{{ t("portalCustomer.datasets.orders.lead") }}</p>
            </div>
            <span class="status-badge" :data-state="ordersState">
              {{ t(collectionStateKey(ordersState)) }}
            </span>
          </div>
          <p class="dataset-meta">
            {{ t(collectionMessageKey(orders?.source.message_key, "portalCustomer.datasets.orders.pending")) }}
          </p>
          <p class="dataset-meta">
            {{ t("portalCustomer.meta.sourceModule") }}: {{ orders?.source.source_module_key || "planning" }}
          </p>
          <ul v-if="orders?.items.length" class="portal-list">
            <li v-for="item in orders.items" :key="item.id">
              <strong>{{ item.order_number }}</strong> · {{ item.title }}
            </li>
          </ul>
        </article>

        <article class="portal-dataset-card">
          <div class="portal-dataset-header">
            <div>
              <p class="eyebrow">{{ t("portalCustomer.datasets.schedules.eyebrow") }}</p>
              <h3>{{ t("portalCustomer.datasets.schedules.title") }}</h3>
              <p>{{ t("portalCustomer.datasets.schedules.lead") }}</p>
            </div>
            <span class="status-badge" :data-state="schedulesState">
              {{ t(collectionStateKey(schedulesState)) }}
            </span>
          </div>
          <p class="dataset-meta">
            {{ t(collectionMessageKey(schedules?.source.message_key, "portalCustomer.datasets.schedules.pending")) }}
          </p>
          <p class="dataset-meta">
            {{ t("portalCustomer.meta.sourceModule") }}: {{ schedules?.source.source_module_key || "planning" }}
          </p>
          <ul v-if="schedules?.items.length" class="portal-list">
            <li v-for="item in schedules.items" :key="item.id">
              <strong>{{ formatDate(item.schedule_date) }}</strong> · {{ item.shift_label }}
            </li>
          </ul>
        </article>

        <article class="portal-dataset-card">
          <div class="portal-dataset-header">
            <div>
              <p class="eyebrow">{{ t("portalCustomer.datasets.watchbooks.eyebrow") }}</p>
              <h3>{{ t("portalCustomer.datasets.watchbooks.title") }}</h3>
              <p>{{ t("portalCustomer.datasets.watchbooks.lead") }}</p>
            </div>
            <span class="status-badge" :data-state="watchbooksState">
              {{ t(collectionStateKey(watchbooksState)) }}
            </span>
          </div>
          <p class="dataset-meta">
            {{ t(collectionMessageKey(watchbooks?.source.message_key, "portalCustomer.datasets.watchbooks.pending")) }}
          </p>
          <p class="dataset-meta">
            {{ t("portalCustomer.meta.sourceModule") }}:
            {{ watchbooks?.source.source_module_key || "field_execution" }}
          </p>
          <ul v-if="watchbooks?.items.length" class="portal-list">
            <li v-for="item in watchbooks.items" :key="item.id">
              <strong>{{ formatDate(item.log_date) }}</strong> · {{ item.summary }}
              <span class="dataset-meta">
                {{ formatDateTime(item.occurred_at) }} · {{ item.entry_type_code || "-" }}
                <template v-if="item.pdf_document_id"> · PDF {{ item.pdf_document_id }}</template>
              </span>
            </li>
          </ul>
          <div v-if="watchbooks?.items.length" class="portal-watchbook-entry-form">
            <div class="field">
              <label for="customer-watchbook-select">{{ t("portalCustomer.watchbooks.fields.watchbook") }}</label>
              <select id="customer-watchbook-select" v-model="selectedWatchbookId">
                <option v-for="item in watchbooks.items" :key="item.id" :value="item.id">
                  {{ formatDate(item.log_date) }} · {{ item.summary }}
                </option>
              </select>
            </div>
            <div class="field">
              <label for="customer-watchbook-note">{{ t("portalCustomer.watchbooks.fields.note") }}</label>
              <textarea
                id="customer-watchbook-note"
                v-model.trim="watchbookNarrative"
                rows="4"
                :placeholder="t('portalCustomer.watchbooks.fields.notePlaceholder')"
              />
            </div>
            <div class="portal-login-actions">
              <button
                class="cta-button"
                type="button"
                :disabled="loading || !selectedWatchbookId || !watchbookNarrative"
                @click="submitWatchbookEntry"
              >
                {{ t("portalCustomer.watchbooks.actions.submit") }}
              </button>
            </div>
          </div>
        </article>

        <article class="portal-dataset-card">
          <div class="portal-dataset-header">
            <div>
              <p class="eyebrow">{{ t("portalCustomer.datasets.timesheets.eyebrow") }}</p>
              <h3>{{ t("portalCustomer.datasets.timesheets.title") }}</h3>
              <p>{{ t("portalCustomer.datasets.timesheets.lead") }}</p>
            </div>
            <span class="status-badge" :data-state="timesheetsState">
              {{ t(collectionStateKey(timesheetsState)) }}
            </span>
          </div>
          <p class="dataset-meta">
            {{ t(collectionMessageKey(timesheets?.source.message_key, "portalCustomer.datasets.timesheets.pending")) }}
          </p>
          <p class="dataset-meta">
            {{ t("portalCustomer.meta.sourceModule") }}: {{ timesheets?.source.source_module_key || "finance" }}
          </p>
          <p class="dataset-meta">{{ t("portalCustomer.meta.docsBacked") }}</p>
          <ul v-if="timesheets?.items.length" class="portal-list">
            <li v-for="item in timesheets.items" :key="item.id">
              <strong>{{ formatDate(item.period_start) }} - {{ formatDate(item.period_end) }}</strong>
              <span class="dataset-meta">{{ item.total_minutes || 0 }} min · {{ formatDateTime(item.released_at) }}</span>
              <div v-if="item.documents.length" class="portal-inline-actions">
                <button
                  v-for="document in item.documents"
                  :key="document.document_id"
                  class="secondary-button"
                  type="button"
                  @click="downloadTimesheetDocument(item.id, document.document_id, document.current_version_no)"
                >
                  {{ t("portalCustomer.actions.download") }} · {{ document.title }}
                </button>
              </div>
            </li>
          </ul>
        </article>

        <article class="portal-dataset-card">
          <div class="portal-dataset-header">
            <div>
              <p class="eyebrow">{{ t("portalCustomer.datasets.invoices.eyebrow") }}</p>
              <h3>{{ t("portalCustomer.datasets.invoices.title") }}</h3>
              <p>{{ t("portalCustomer.datasets.invoices.lead") }}</p>
            </div>
            <span class="status-badge" :data-state="invoicesState">
              {{ t(collectionStateKey(invoicesState)) }}
            </span>
          </div>
          <p class="dataset-meta">
            {{ t(collectionMessageKey(invoices?.source.message_key, "portalCustomer.datasets.invoices.pending")) }}
          </p>
          <p class="dataset-meta">
            {{ t("portalCustomer.meta.sourceModule") }}: {{ invoices?.source.source_module_key || "finance" }}
          </p>
          <p class="dataset-meta">{{ t("portalCustomer.meta.docsBacked") }}</p>
          <ul v-if="invoices?.items.length" class="portal-list">
            <li v-for="item in invoices.items" :key="item.id">
              <strong>{{ item.invoice_no }}</strong>
              <span class="dataset-meta">
                {{ formatDate(item.issue_date) }} · {{ formatDate(item.due_date) }} · {{ item.total_amount }} {{ item.currency_code }}
              </span>
              <div v-if="item.documents.length" class="portal-inline-actions">
                <button
                  v-for="document in item.documents"
                  :key="document.document_id"
                  class="secondary-button"
                  type="button"
                  @click="downloadInvoiceDocument(item.id, document.document_id, document.current_version_no)"
                >
                  {{ t("portalCustomer.actions.download") }} · {{ document.title }}
                </button>
              </div>
            </li>
          </ul>
        </article>

        <article class="portal-dataset-card">
          <div class="portal-dataset-header">
            <div>
              <p class="eyebrow">{{ t("portalCustomer.datasets.reports.eyebrow") }}</p>
              <h3>{{ t("portalCustomer.datasets.reports.title") }}</h3>
              <p>{{ t("portalCustomer.datasets.reports.lead") }}</p>
            </div>
            <span class="status-badge" :data-state="reportsState">
              {{ t(collectionStateKey(reportsState)) }}
            </span>
          </div>
          <p class="dataset-meta">
            {{ t(collectionMessageKey(reports?.source.message_key, "portalCustomer.datasets.reports.pending")) }}
          </p>
          <p class="dataset-meta">
            {{ t("portalCustomer.meta.sourceModule") }}: {{ reports?.source.source_module_key || "reporting" }}
          </p>
          <p class="dataset-meta">{{ t("portalCustomer.meta.docsBacked") }}</p>
          <ul v-if="reports?.items.length" class="portal-list">
            <li v-for="item in reports.items" :key="item.id">
              <strong>{{ item.title }}</strong> · {{ formatDateTime(item.published_at) }}
            </li>
          </ul>
        </article>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { AuthApiError } from "@/api/auth";
import {
  createCustomerPortalWatchbookEntry,
  downloadCustomerPortalInvoiceDocument,
  downloadCustomerPortalTimesheetDocument,
  getCustomerPortalOrders,
  getCustomerPortalHistory,
  getCustomerPortalInvoices,
  getCustomerPortalReports,
  getCustomerPortalSchedules,
  getCustomerPortalTimesheets,
  getCustomerPortalWatchbooks,
  type CustomerPortalInvoiceCollectionRead,
  type CustomerPortalOrderCollectionRead,
  type CustomerPortalHistoryCollectionRead,
  type CustomerPortalReportPackageCollectionRead,
  type CustomerPortalScheduleCollectionRead,
  type CustomerPortalTimesheetCollectionRead,
  type CustomerPortalWatchbookCollectionRead,
} from "@/api/customerPortal";
import {
  derivePortalCollectionState,
  derivePortalCustomerAccessState,
  mapPortalApiMessage,
} from "@/features/portal/customerPortal.helpers.js";
import { useI18n } from "@/i18n";
import type { MessageKey } from "@/i18n/messages";
import { useAuthStore } from "@/stores/auth";

const authStore = useAuthStore();
const { locale, t } = useI18n();

const tenantCode = ref("");
const identifier = ref("");
const password = ref("");
const deviceLabel = ref("Customer Portal");
const loading = ref(false);
const lastErrorKey = ref("");
const feedbackKey = ref<MessageKey | null>(null);
const feedbackTone = ref<"info" | "success" | "error">("info");

const orders = ref<CustomerPortalOrderCollectionRead | null>(null);
const schedules = ref<CustomerPortalScheduleCollectionRead | null>(null);
const watchbooks = ref<CustomerPortalWatchbookCollectionRead | null>(null);
const timesheets = ref<CustomerPortalTimesheetCollectionRead | null>(null);
const invoices = ref<CustomerPortalInvoiceCollectionRead | null>(null);
const reports = ref<CustomerPortalReportPackageCollectionRead | null>(null);
const portalHistory = ref<CustomerPortalHistoryCollectionRead | null>(null);
const selectedWatchbookId = ref("");
const watchbookNarrative = ref("");

const portalContext = computed(() => authStore.portalCustomerContext);
const accessState = computed(() =>
  derivePortalCustomerAccessState({
    isLoading: loading.value,
    hasSession: authStore.hasSession,
    hasContext: Boolean(portalContext.value),
    lastErrorKey: lastErrorKey.value,
  }),
);
const portalScopeSummary = computed(() =>
  portalContext.value?.scopes.map((scope) => scope.customer_id).join(", ") ?? "-",
);
const ordersState = computed(() => derivePortalCollectionState(orders.value));
const schedulesState = computed(() => derivePortalCollectionState(schedules.value));
const watchbooksState = computed(() => derivePortalCollectionState(watchbooks.value));
const timesheetsState = computed(() => derivePortalCollectionState(timesheets.value));
const invoicesState = computed(() => derivePortalCollectionState(invoices.value));
const reportsState = computed(() => derivePortalCollectionState(reports.value));

function setFeedback(messageKey: MessageKey, tone: "info" | "success" | "error") {
  feedbackKey.value = messageKey;
  feedbackTone.value = tone;
}

function clearFeedback() {
  feedbackKey.value = null;
}

function clearPortalCollections() {
  orders.value = null;
  schedules.value = null;
  watchbooks.value = null;
  timesheets.value = null;
  invoices.value = null;
  reports.value = null;
  portalHistory.value = null;
  selectedWatchbookId.value = "";
  watchbookNarrative.value = "";
}

function collectionStateKey(state: string): MessageKey {
  switch (state) {
    case "ready":
      return "portalCustomer.states.ready";
    case "empty":
      return "portalCustomer.states.empty";
    case "pending":
      return "portalCustomer.states.pending";
    default:
      return "portalCustomer.states.loading";
  }
}

function collectionMessageKey(messageKey: string | undefined, fallback: MessageKey): MessageKey {
  return (messageKey as MessageKey | undefined) ?? fallback;
}

function formatDate(value: string | null) {
  if (!value) {
    return "-";
  }

  return new Intl.DateTimeFormat(locale.value === "de" ? "de-DE" : "en-US", {
    dateStyle: "medium",
  }).format(new Date(value));
}

function formatDateTime(value: string | null) {
  if (!value) {
    return "-";
  }

  return new Intl.DateTimeFormat(locale.value === "de" ? "de-DE" : "en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

async function loadPortalCollections() {
  if (!authStore.accessToken) {
    clearPortalCollections();
    return;
  }

  const [nextOrders, nextSchedules, nextWatchbooks, nextTimesheets, nextInvoices, nextReports, nextHistory] = await Promise.all([
    getCustomerPortalOrders(authStore.accessToken),
    getCustomerPortalSchedules(authStore.accessToken),
    getCustomerPortalWatchbooks(authStore.accessToken),
    getCustomerPortalTimesheets(authStore.accessToken),
    getCustomerPortalInvoices(authStore.accessToken),
    getCustomerPortalReports(authStore.accessToken),
    getCustomerPortalHistory(authStore.accessToken),
  ]);

  orders.value = nextOrders;
  schedules.value = nextSchedules;
  watchbooks.value = nextWatchbooks;
  selectedWatchbookId.value = nextWatchbooks.items[0]?.id ?? "";
  timesheets.value = nextTimesheets;
  invoices.value = nextInvoices;
  reports.value = nextReports;
  portalHistory.value = nextHistory;
}

function triggerBrowserDownload(fileName: string, blob: Blob) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = fileName;
  document.body.append(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

async function downloadTimesheetDocument(timesheetId: string, documentId: string, versionNo: number | null) {
  if (!authStore.accessToken || versionNo == null) {
    return;
  }

  loading.value = true;
  clearFeedback();
  try {
    const download = await downloadCustomerPortalTimesheetDocument(authStore.accessToken, timesheetId, documentId, versionNo);
    triggerBrowserDownload(download.fileName, download.blob);
  } catch (error) {
    const messageKey = error instanceof AuthApiError ? error.messageKey : "errors.platform.internal";
    lastErrorKey.value = messageKey;
    setFeedback(mapPortalApiMessage(messageKey), "error");
  } finally {
    loading.value = false;
  }
}

async function downloadInvoiceDocument(invoiceId: string, documentId: string, versionNo: number | null) {
  if (!authStore.accessToken || versionNo == null) {
    return;
  }

  loading.value = true;
  clearFeedback();
  try {
    const download = await downloadCustomerPortalInvoiceDocument(authStore.accessToken, invoiceId, documentId, versionNo);
    triggerBrowserDownload(download.fileName, download.blob);
  } catch (error) {
    const messageKey = error instanceof AuthApiError ? error.messageKey : "errors.platform.internal";
    lastErrorKey.value = messageKey;
    setFeedback(mapPortalApiMessage(messageKey), "error");
  } finally {
    loading.value = false;
  }
}

async function submitWatchbookEntry() {
  if (!authStore.accessToken || !selectedWatchbookId.value || !watchbookNarrative.value) {
    return;
  }

  loading.value = true;
  clearFeedback();
  try {
    await createCustomerPortalWatchbookEntry(authStore.accessToken, selectedWatchbookId.value, {
      entry_type_code: "customer_note",
      narrative: watchbookNarrative.value,
    });
    watchbookNarrative.value = "";
    await loadPortalCollections();
    setFeedback("portalCustomer.feedback.watchbookEntrySubmitted", "success");
  } catch (error) {
    const messageKey = error instanceof AuthApiError ? error.messageKey : "errors.platform.internal";
    lastErrorKey.value = messageKey;
    setFeedback(mapPortalApiMessage(messageKey), "error");
  } finally {
    loading.value = false;
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
    await authStore.loadCustomerPortalContext();
    await loadPortalCollections();
    lastErrorKey.value = "";
    setFeedback("portalCustomer.feedback.sessionReady", "success");
  } catch (error) {
    clearPortalCollections();
    const messageKey = error instanceof AuthApiError ? error.messageKey : "errors.platform.internal";
    lastErrorKey.value = messageKey;
    setFeedback(mapPortalApiMessage(messageKey), "error");
  } finally {
    loading.value = false;
  }
}

async function submitLogin() {
  loading.value = true;
  clearFeedback();
  authStore.clearPortalCustomerContext();
  clearPortalCollections();
  try {
    await authStore.loginCustomerPortal({
      tenant_code: tenantCode.value,
      identifier: identifier.value,
      password: password.value,
      device_label: deviceLabel.value || null,
    });
    await authStore.loadCustomerPortalContext();
    await loadPortalCollections();
    password.value = "";
    lastErrorKey.value = "";
    setFeedback("portalCustomer.feedback.sessionReady", "success");
  } catch (error) {
    const messageKey = error instanceof AuthApiError ? error.messageKey : "errors.platform.internal";
    lastErrorKey.value = messageKey;
    setFeedback(mapPortalApiMessage(messageKey), "error");
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
    setFeedback("portalCustomer.feedback.loggedOut", "info");
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
.portal-customer-view {
  display: grid;
  gap: 1.25rem;
}

.portal-customer-header {
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

.portal-watchbook-entry-form {
  margin-top: 1rem;
  display: grid;
  gap: 0.85rem;
}

.portal-login-grid,
.portal-summary-grid,
.portal-dataset-grid,
.portal-stack {
  display: grid;
  gap: 1rem;
}

.portal-login-grid {
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  align-items: end;
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

.field textarea,
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

.portal-summary-grid,
.portal-dataset-grid {
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
}

.portal-dataset-card {
  display: grid;
  gap: 0.75rem;
}

.portal-history-list {
  display: grid;
  gap: 0.85rem;
}

.portal-history-item {
  display: grid;
  gap: 0.35rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--sp-border);
}

.portal-dataset-header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: start;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 0.3rem 0.65rem;
  font-size: 0.76rem;
  font-weight: 700;
  background: var(--sp-surface-muted);
  color: var(--sp-text-strong);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.status-badge[data-state="pending"] {
  background: color-mix(in srgb, #d8a846 18%, var(--sp-surface-muted));
}

.status-badge[data-state="ready"] {
  background: color-mix(in srgb, var(--sp-primary) 18%, var(--sp-surface-muted));
}

.dataset-meta {
  margin: 0;
  color: var(--sp-text-muted);
}

.portal-list,
.portal-flags {
  margin: 0;
  padding-left: 1.1rem;
  display: grid;
  gap: 0.45rem;
}

.portal-inline-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.5rem;
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
  .portal-customer-header,
  .portal-dataset-header {
    flex-direction: column;
  }
}
</style>
