<template>
  <CustomerPortalPageShell
    :access-state="page.accessState.value"
    :device-label="page.deviceLabel.value"
    :feedback-key="page.feedbackKey.value"
    :feedback-tone="page.feedbackTone.value"
    :has-session="page.authStore.hasSession"
    :identifier="page.identifier.value"
    :lead-key="'portalCustomer.lead'"
    :loading="page.loading.value"
    :password="page.password.value"
    :portal-diagnostic-body-key="page.portalDiagnosticBodyKey.value"
    :portal-diagnostic-title-key="page.portalDiagnosticTitleKey.value"
    :tenant-code="page.tenantCode.value"
    :title-key="'portalCustomer.title'"
    @logout="page.logoutPortalSession"
    @refresh="page.refreshPortalContext"
    @submit-login="page.submitLogin"
    @update:device-label="page.deviceLabel.value = $event"
    @update:identifier="page.identifier.value = $event"
    @update:password="page.password.value = $event"
    @update:tenant-code="page.tenantCode.value = $event"
  >
    <div v-if="page.portalContext.value" class="portal-page-stack">
      <div class="portal-summary-grid">
        <CustomerPortalContextCard
          :portal-context="page.portalContext.value"
          :portal-scope-summary="page.portalScopeSummary.value"
        />

        <article class="module-card">
          <p class="eyebrow">{{ t("portalCustomer.access.eyebrow") }}</p>
          <h3>{{ t("portalCustomer.access.title") }}</h3>
          <p>{{ t("portalCustomer.access.body") }}</p>
          <ul class="portal-capability-list">
            <li v-for="item in capabilitySummaryRows" :key="item.labelKey" class="portal-capability-item">
              <div>
                <strong>{{ t(item.labelKey) }}</strong>
                <p>{{ t(item.bodyKey) }}</p>
              </div>
              <span class="status-badge" :data-state="item.state">
                {{ t(capabilityStateKey(item.state)) }}
              </span>
            </li>
          </ul>
        </article>

        <article class="module-card">
          <p class="eyebrow">{{ t("portalCustomer.readOnly.title") }}</p>
          <p>{{ t("portalCustomer.readOnly.body") }}</p>
          <ul class="portal-flags">
            <li>{{ t("portalCustomer.meta.releasedOnly") }}</li>
            <li>{{ t("portalCustomer.meta.customerScoped") }}</li>
            <li>
              {{
                t(
                  page.portalContext.value.capabilities.personal_names_visible
                    ? "portalCustomer.meta.personalNamesVisible"
                    : "portalCustomer.meta.personalNamesRestricted",
                )
              }}
            </li>
          </ul>
        </article>
      </div>
    </div>
  </CustomerPortalPageShell>
</template>

<script setup lang="ts">
import { computed } from "vue";

import CustomerPortalPageShell from "@/components/portal/CustomerPortalPageShell.vue";
import CustomerPortalContextCard from "@/components/portal/CustomerPortalContextCard.vue";
import { useI18n } from "@/i18n";
import type { MessageKey } from "@/i18n/messages";
import { derivePortalCapabilityState } from "@/features/portal/customerPortal.helpers.js";
import { useCustomerPortalPage } from "@/features/portal/useCustomerPortalPage";

const { t } = useI18n();
const page = useCustomerPortalPage();

type CapabilitySummaryRow = {
  labelKey: MessageKey;
  bodyKey: MessageKey;
  state: "available" | "enabled" | "not_enabled" | "pending_integration" | "read_only";
};

const portalDatasetCapabilities = computed(
  () => new Map((page.portalContext.value?.capabilities.datasets ?? []).map((item) => [item.domain_key, item])),
);

const capabilitySummaryRows = computed(() => {
  const capabilities = page.portalContext.value?.capabilities;
  if (!capabilities) {
    return [] as CapabilitySummaryRow[];
  }

  return [
    {
      labelKey: "portalCustomer.access.base.label",
      bodyKey: "portalCustomer.access.base.body",
      state: "available",
    },
    {
      labelKey: "portalCustomer.capabilities.orders.label",
      bodyKey: "portalCustomer.capabilities.orders.body",
      state: derivePortalCapabilityState(portalDatasetCapabilities.value.get("orders")),
    },
    {
      labelKey: "portalCustomer.capabilities.schedules.label",
      bodyKey: "portalCustomer.capabilities.schedules.body",
      state: derivePortalCapabilityState(portalDatasetCapabilities.value.get("schedules")),
    },
    {
      labelKey: "portalCustomer.capabilities.watchbooks.label",
      bodyKey: "portalCustomer.capabilities.watchbooks.body",
      state: derivePortalCapabilityState(portalDatasetCapabilities.value.get("watchbooks")),
    },
    {
      labelKey: "portalCustomer.capabilities.watchbookWrite.label",
      bodyKey: "portalCustomer.capabilities.watchbookWrite.body",
      state: capabilities.can_add_watchbook_entries ? "enabled" : "not_enabled",
    },
    {
      labelKey: "portalCustomer.capabilities.timesheets.label",
      bodyKey: "portalCustomer.capabilities.timesheets.body",
      state: capabilities.can_download_timesheet_documents ? "available" : "not_enabled",
    },
    {
      labelKey: "portalCustomer.capabilities.invoices.label",
      bodyKey: "portalCustomer.capabilities.invoices.body",
      state: capabilities.can_download_invoice_documents ? "available" : "not_enabled",
    },
    {
      labelKey: "portalCustomer.capabilities.reports.label",
      bodyKey: "portalCustomer.capabilities.reports.body",
      state: derivePortalCapabilityState(portalDatasetCapabilities.value.get("reports")),
    },
    {
      labelKey: "portalCustomer.capabilities.history.label",
      bodyKey: "portalCustomer.capabilities.history.body",
      state: capabilities.can_view_history ? "read_only" : "not_enabled",
    },
  ] satisfies CapabilitySummaryRow[];
});

function capabilityStateKey(state: string): MessageKey {
  switch (state) {
    case "available":
      return "portalCustomer.access.states.available";
    case "enabled":
      return "portalCustomer.access.states.enabled";
    case "not_enabled":
      return "portalCustomer.access.states.notEnabled";
    case "pending_integration":
      return "portalCustomer.access.states.pendingIntegration";
    case "read_only":
    default:
      return "portalCustomer.access.states.readOnly";
  }
}
</script>

<style scoped>
.portal-page-stack,
.portal-summary-grid {
  display: grid;
  gap: 1rem;
}

.portal-summary-grid {
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
}

.portal-capability-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 0.85rem;
}

.portal-capability-item {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: start;
  padding-top: 0.85rem;
  border-top: 1px solid var(--sp-border);
}

.portal-capability-item:first-child {
  padding-top: 0;
  border-top: 0;
}

.portal-capability-item p {
  margin: 0.35rem 0 0;
  color: var(--sp-text-muted);
}

.portal-flags {
  margin: 0;
  padding-left: 1.1rem;
  display: grid;
  gap: 0.45rem;
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

.status-badge[data-state="available"],
.status-badge[data-state="enabled"] {
  background: color-mix(in srgb, var(--sp-primary) 18%, var(--sp-surface-muted));
}

.status-badge[data-state="not_enabled"] {
  background: color-mix(in srgb, #d94f4f 14%, var(--sp-surface-muted));
}

.status-badge[data-state="pending_integration"] {
  background: color-mix(in srgb, #d8a846 18%, var(--sp-surface-muted));
}

.status-badge[data-state="read_only"] {
  background: color-mix(in srgb, #4a80d9 16%, var(--sp-surface-muted));
}
</style>
