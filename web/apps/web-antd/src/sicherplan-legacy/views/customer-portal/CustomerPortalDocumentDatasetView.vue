<template>
  <CustomerPortalPageShell
    :access-state="page.accessState.value"
    :device-label="page.deviceLabel.value"
    :feedback-key="page.feedbackKey.value"
    :feedback-tone="page.feedbackTone.value"
    :has-session="page.authStore.hasSession"
    :identifier="page.identifier.value"
    :lead-key="resolvedViewConfig.leadKey"
    :loading="page.loading.value"
    :password="page.password.value"
    :portal-diagnostic-body-key="page.portalDiagnosticBodyKey.value"
    :portal-diagnostic-title-key="page.portalDiagnosticTitleKey.value"
    :tenant-code="page.tenantCode.value"
    :title-key="resolvedViewConfig.titleKey"
    @logout="page.logoutPortalSession"
    @refresh="page.refreshPortalContext"
    @submit-login="page.submitLogin"
    @update:device-label="page.deviceLabel.value = $event"
    @update:identifier="page.identifier.value = $event"
    @update:password="page.password.value = $event"
    @update:tenant-code="page.tenantCode.value = $event"
  >
    <div v-if="page.portalContext.value" class="portal-page-stack">
      <CustomerPortalContextCard
        :portal-context="page.portalContext.value"
        :portal-scope-summary="page.portalScopeSummary.value"
      />

      <article class="module-card portal-page-card">
        <div class="portal-page-card__header">
          <div>
            <p class="eyebrow">{{ t(resolvedViewConfig.titleKey) }}</p>
            <h3>{{ t(resolvedViewConfig.datasetTitleKey) }}</h3>
            <p>{{ t("portalCustomer.pages.downloadNotice") }}</p>
          </div>
          <span class="status-badge" :data-state="datasetState">
            {{ t(collectionStateKey(datasetState)) }}
          </span>
        </div>
        <p v-if="datasetMessageKey" class="dataset-meta">{{ t(datasetMessageKey) }}</p>
        <p class="dataset-meta">
          {{ t("portalCustomer.meta.sourceModule") }}: {{ collection?.source.source_module_key || resolvedViewConfig.sourceModule }}
        </p>
        <p class="dataset-meta">{{ t("portalCustomer.meta.docsBacked") }}</p>

        <ul v-if="domain === 'timesheets' && timesheetItems.length" class="portal-list">
          <li v-for="item in timesheetItems" :key="item.id">
              <strong>{{ page.formatDate(item.period_start) }} - {{ page.formatDate(item.period_end) }}</strong>
              <span class="dataset-meta">{{ item.total_minutes || 0 }} min · {{ page.formatDateTime(item.released_at) }}</span>
            <div v-if="item.documents.length" class="portal-inline-actions">
              <button
                v-for="document in item.documents"
                :key="document.document_id"
                class="secondary-button"
                type="button"
                @click="downloadDocument(item.id, document.document_id, document.current_version_no)"
              >
                {{ t("portalCustomer.actions.download") }} · {{ document.title }}
              </button>
            </div>
          </li>
        </ul>

        <ul v-else-if="invoiceItems.length" class="portal-list">
          <li v-for="item in invoiceItems" :key="item.id">
              <strong>{{ item.invoice_no }}</strong>
              <span class="dataset-meta">
                {{ page.formatDate(item.issue_date) }} · {{ page.formatDate(item.due_date) }} · {{ item.total_amount }} {{ item.currency_code }}
              </span>
            <div v-if="item.documents.length" class="portal-inline-actions">
              <button
                v-for="document in item.documents"
                :key="document.document_id"
                class="secondary-button"
                type="button"
                @click="downloadDocument(item.id, document.document_id, document.current_version_no)"
              >
                {{ t("portalCustomer.actions.download") }} · {{ document.title }}
              </button>
            </div>
          </li>
        </ul>
      </article>
    </div>
  </CustomerPortalPageShell>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";

import type {
  CustomerPortalInvoiceCollectionRead,
  CustomerPortalInvoiceRead,
  CustomerPortalTimesheetCollectionRead,
  CustomerPortalTimesheetRead,
} from "@/api/customerPortal";
import {
  downloadCustomerPortalInvoiceDocument,
  downloadCustomerPortalTimesheetDocument,
  getCustomerPortalInvoices,
  getCustomerPortalTimesheets,
} from "@/api/customerPortal";
import { AuthApiError } from "@/api/auth";
import CustomerPortalContextCard from "@/components/portal/CustomerPortalContextCard.vue";
import CustomerPortalPageShell from "@/components/portal/CustomerPortalPageShell.vue";
import {
  derivePortalCollectionState,
  derivePortalDatasetMessage,
  mapPortalApiMessage,
} from "@/features/portal/customerPortal.helpers.js";
import { useCustomerPortalPage } from "@/features/portal/useCustomerPortalPage";
import { useI18n } from "@/i18n";
import type { MessageKey } from "@/i18n/messages";
import { useAuthStore } from "@/stores/auth";

const props = defineProps<{
  domain: "invoices" | "timesheets";
}>();

const { t } = useI18n();
const authStore = useAuthStore();
const collection = ref<CustomerPortalInvoiceCollectionRead | CustomerPortalTimesheetCollectionRead | null>(null);

const loaders = {
  invoices: () => getCustomerPortalInvoices(authStore.accessToken!),
  timesheets: () => getCustomerPortalTimesheets(authStore.accessToken!),
} as const;

const viewConfig: Record<
  "invoices" | "timesheets",
  {
    titleKey: MessageKey;
    leadKey: MessageKey;
    datasetTitleKey: MessageKey;
    emptyKey: MessageKey;
    sourceModule: string;
  }
> = {
  invoices: {
    titleKey: "route.portal.customerInvoices.title",
    leadKey: "portalCustomer.datasets.invoices.lead",
    datasetTitleKey: "portalCustomer.datasets.invoices.title",
    emptyKey: "portalCustomer.datasets.invoices.empty",
    sourceModule: "finance",
  },
  timesheets: {
    titleKey: "route.portal.customerTimesheets.title",
    leadKey: "portalCustomer.datasets.timesheets.lead",
    datasetTitleKey: "portalCustomer.datasets.timesheets.title",
    emptyKey: "portalCustomer.datasets.timesheets.empty",
    sourceModule: "finance",
  },
};

const page = useCustomerPortalPage({
  clearPageData: () => {
    collection.value = null;
  },
  loadPageData: async () => {
    collection.value = await loaders[props.domain]();
  },
});
const resolvedViewConfig = computed(() => viewConfig[props.domain]);

const datasetState = computed(() => derivePortalCollectionState(collection.value));
const datasetMessageKey = computed<MessageKey | null>(() =>
  derivePortalDatasetMessage(collection.value, resolvedViewConfig.value.emptyKey) as MessageKey | null,
);
const timesheetItems = computed<CustomerPortalTimesheetRead[]>(() =>
  props.domain === "timesheets" ? ((collection.value?.items ?? []) as CustomerPortalTimesheetRead[]) : [],
);
const invoiceItems = computed<CustomerPortalInvoiceRead[]>(() =>
  props.domain === "invoices" ? ((collection.value?.items ?? []) as CustomerPortalInvoiceRead[]) : [],
);

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

async function downloadDocument(recordId: string, documentId: string, versionNo: number | null) {
  if (!authStore.accessToken || versionNo == null) {
    return;
  }

  page.loading.value = true;
  page.clearFeedback();
  try {
    const download =
      props.domain === "timesheets"
        ? await downloadCustomerPortalTimesheetDocument(authStore.accessToken, recordId, documentId, versionNo)
        : await downloadCustomerPortalInvoiceDocument(authStore.accessToken, recordId, documentId, versionNo);
    triggerBrowserDownload(download.fileName, download.blob);
  } catch (error) {
    const messageKey = error instanceof AuthApiError ? error.messageKey : "errors.platform.internal";
    page.lastErrorKey.value = messageKey;
    page.setFeedback(mapPortalApiMessage(messageKey), "error");
  } finally {
    page.loading.value = false;
  }
}
</script>

<style scoped>
.portal-page-stack,
.portal-page-card {
  display: grid;
  gap: 1rem;
}

.portal-page-card__header {
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

.portal-list {
  margin: 0;
  padding-left: 1.1rem;
  display: grid;
  gap: 0.75rem;
}

.portal-inline-actions {
  margin-top: 0.5rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}
</style>
