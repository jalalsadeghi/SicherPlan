<template>
  <CustomerPortalPageShell
    :access-state="page.accessState.value"
    :device-label="page.deviceLabel.value"
    :feedback-key="page.feedbackKey.value"
    :feedback-tone="page.feedbackTone.value"
    :has-session="page.authStore.hasSession"
    :identifier="page.identifier.value"
    :lead-key="'portalCustomer.history.lead'"
    :loading="page.loading.value"
    :password="page.password.value"
    :portal-diagnostic-body-key="page.portalDiagnosticBodyKey.value"
    :portal-diagnostic-title-key="page.portalDiagnosticTitleKey.value"
    :tenant-code="page.tenantCode.value"
    :title-key="'route.portal.customerHistory.title'"
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
            <p class="eyebrow">{{ t("route.portal.customerHistory.title") }}</p>
            <h3>{{ t("portalCustomer.history.title") }}</h3>
            <p>{{ t("portalCustomer.pages.readOnlyNotice") }}</p>
          </div>
          <span class="status-badge" data-state="read_only">
            {{ t("portalCustomer.access.states.readOnly") }}
          </span>
        </div>
        <div v-if="history?.items.length" class="portal-history-list">
          <article v-for="entry in history.items" :key="entry.id" class="portal-history-item">
            <strong>{{ entry.title }}</strong>
            <p>{{ entry.summary }}</p>
            <span class="dataset-meta">{{ page.formatDateTime(entry.created_at) }}</span>
            <ul v-if="entry.attachments.length" class="portal-list">
              <li v-for="attachment in entry.attachments" :key="attachment.document_id">
                {{ attachment.title }}
              </li>
            </ul>
          </article>
        </div>
        <p v-else class="dataset-meta">{{ t("portalCustomer.history.empty") }}</p>
      </article>
    </div>
  </CustomerPortalPageShell>
</template>

<script setup lang="ts">
import { ref } from "vue";

import type { CustomerPortalHistoryCollectionRead } from "@/api/customerPortal";
import { getCustomerPortalHistory } from "@/api/customerPortal";
import CustomerPortalContextCard from "@/components/portal/CustomerPortalContextCard.vue";
import CustomerPortalPageShell from "@/components/portal/CustomerPortalPageShell.vue";
import { useCustomerPortalPage } from "@/features/portal/useCustomerPortalPage";
import { useI18n } from "@/i18n";
import { useAuthStore } from "@/stores/auth";

const { t } = useI18n();
const authStore = useAuthStore();
const history = ref<CustomerPortalHistoryCollectionRead | null>(null);

const page = useCustomerPortalPage({
  clearPageData: () => {
    history.value = null;
  },
  loadPageData: async () => {
    history.value = await getCustomerPortalHistory(authStore.accessToken!);
  },
});
</script>

<style scoped>
.portal-page-stack,
.portal-page-card,
.portal-history-list {
  display: grid;
  gap: 1rem;
}

.portal-page-card__header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: start;
}

.portal-history-item {
  display: grid;
  gap: 0.35rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--sp-border);
}

.portal-history-item:first-child {
  padding-top: 0;
  border-top: 0;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 0.3rem 0.65rem;
  font-size: 0.76rem;
  font-weight: 700;
  background: color-mix(in srgb, #4a80d9 16%, var(--sp-surface-muted));
  color: var(--sp-text-strong);
  text-transform: uppercase;
  letter-spacing: 0.08em;
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
