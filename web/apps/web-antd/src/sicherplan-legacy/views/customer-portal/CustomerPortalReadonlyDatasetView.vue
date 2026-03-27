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
            <p>{{ t("portalCustomer.pages.readOnlyNotice") }}</p>
          </div>
          <span class="status-badge" :data-state="datasetState">
            {{ t(collectionStateKey(datasetState)) }}
          </span>
        </div>
        <p v-if="datasetMessageKey" class="dataset-meta">{{ t(datasetMessageKey) }}</p>
        <p class="dataset-meta">
          {{ t("portalCustomer.meta.sourceModule") }}: {{ collection?.source.source_module_key || resolvedViewConfig.sourceModule }}
        </p>

        <ul v-if="domain === 'orders' && ordersItems.length" class="portal-list">
          <li v-for="item in ordersItems" :key="item.id">
            <strong>{{ item.order_number }}</strong> · {{ item.title }}
          </li>
        </ul>

        <ul v-else-if="domain === 'schedules' && scheduleItems.length" class="portal-list">
          <li v-for="item in scheduleItems" :key="item.id">
            <strong>{{ page.formatDate(item.schedule_date) }}</strong> · {{ item.shift_label }}
          </li>
        </ul>

        <ul v-else-if="domain === 'reports' && reportItems.length" class="portal-list">
          <li v-for="item in reportItems" :key="item.id">
            <strong>{{ item.title }}</strong> · {{ page.formatDateTime(item.published_at) }}
          </li>
        </ul>
      </article>
    </div>
  </CustomerPortalPageShell>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";

import type {
  CustomerPortalOrderListItemRead,
  CustomerPortalOrderCollectionRead,
  CustomerPortalReportPackageRead,
  CustomerPortalReportPackageCollectionRead,
  CustomerPortalScheduleListItemRead,
  CustomerPortalScheduleCollectionRead,
} from "@/api/customerPortal";
import {
  getCustomerPortalOrders,
  getCustomerPortalReports,
  getCustomerPortalSchedules,
} from "@/api/customerPortal";
import CustomerPortalContextCard from "@/components/portal/CustomerPortalContextCard.vue";
import CustomerPortalPageShell from "@/components/portal/CustomerPortalPageShell.vue";
import {
  derivePortalCollectionState,
  derivePortalDatasetMessage,
} from "@/features/portal/customerPortal.helpers.js";
import { useCustomerPortalPage } from "@/features/portal/useCustomerPortalPage";
import { useI18n } from "@/i18n";
import type { MessageKey } from "@/i18n/messages";
import { useAuthStore } from "@/stores/auth";

const props = defineProps<{
  domain: "orders" | "reports" | "schedules";
}>();

const { t } = useI18n();
const authStore = useAuthStore();
const collection = ref<
  CustomerPortalOrderCollectionRead | CustomerPortalReportPackageCollectionRead | CustomerPortalScheduleCollectionRead | null
>(null);

const loaders = {
  orders: () => getCustomerPortalOrders(authStore.accessToken!),
  reports: () => getCustomerPortalReports(authStore.accessToken!),
  schedules: () => getCustomerPortalSchedules(authStore.accessToken!),
} as const;

const viewConfig: Record<
  "orders" | "reports" | "schedules",
  {
    titleKey: MessageKey;
    leadKey: MessageKey;
    datasetTitleKey: MessageKey;
    emptyKey: MessageKey;
    sourceModule: string;
  }
> = {
  orders: {
    titleKey: "route.portal.customerOrders.title",
    leadKey: "portalCustomer.datasets.orders.lead",
    datasetTitleKey: "portalCustomer.datasets.orders.title",
    emptyKey: "portalCustomer.datasets.orders.empty",
    sourceModule: "planning",
  },
  reports: {
    titleKey: "route.portal.customerReports.title",
    leadKey: "portalCustomer.datasets.reports.lead",
    datasetTitleKey: "portalCustomer.datasets.reports.title",
    emptyKey: "portalCustomer.datasets.reports.empty",
    sourceModule: "reporting",
  },
  schedules: {
    titleKey: "route.portal.customerSchedules.title",
    leadKey: "portalCustomer.datasets.schedules.lead",
    datasetTitleKey: "portalCustomer.datasets.schedules.title",
    emptyKey: "portalCustomer.datasets.schedules.empty",
    sourceModule: "planning",
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
const ordersItems = computed<CustomerPortalOrderListItemRead[]>(() =>
  props.domain === "orders" ? ((collection.value?.items ?? []) as CustomerPortalOrderListItemRead[]) : [],
);
const scheduleItems = computed<CustomerPortalScheduleListItemRead[]>(() =>
  props.domain === "schedules" ? ((collection.value?.items ?? []) as CustomerPortalScheduleListItemRead[]) : [],
);
const reportItems = computed<CustomerPortalReportPackageRead[]>(() =>
  props.domain === "reports" ? ((collection.value?.items ?? []) as CustomerPortalReportPackageRead[]) : [],
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
  gap: 0.45rem;
}
</style>
