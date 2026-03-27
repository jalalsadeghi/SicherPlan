<template>
  <CustomerPortalPageShell
    :access-state="page.accessState.value"
    :device-label="page.deviceLabel.value"
    :feedback-key="page.feedbackKey.value"
    :feedback-tone="page.feedbackTone.value"
    :has-session="page.authStore.hasSession"
    :identifier="page.identifier.value"
    :lead-key="'portalCustomer.datasets.watchbooks.lead'"
    :loading="page.loading.value"
    :password="page.password.value"
    :portal-diagnostic-body-key="page.portalDiagnosticBodyKey.value"
    :portal-diagnostic-title-key="page.portalDiagnosticTitleKey.value"
    :tenant-code="page.tenantCode.value"
    :title-key="'route.portal.customerWatchbooks.title'"
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
            <p class="eyebrow">{{ t("route.portal.customerWatchbooks.title") }}</p>
            <h3>{{ t("portalCustomer.datasets.watchbooks.title") }}</h3>
            <p>{{ t("portalCustomer.datasets.watchbooks.lead") }}</p>
          </div>
          <div class="portal-page-card__badges">
            <span class="status-badge" :data-state="datasetState">
              {{ t(collectionStateKey(datasetState)) }}
            </span>
            <span class="status-badge" :data-state="watchbookWriteState">
              {{ t(capabilityStateKey(watchbookWriteState)) }}
            </span>
          </div>
        </div>
        <p v-if="datasetMessageKey" class="dataset-meta">{{ t(datasetMessageKey) }}</p>
        <p class="dataset-meta">{{ t(watchbookPolicyMessageKey) }}</p>
        <p class="dataset-meta">
          {{ t("portalCustomer.meta.sourceModule") }}: {{ watchbooks?.source.source_module_key || "field_execution" }}
        </p>

        <ul v-if="watchbooks?.items.length" class="portal-list">
          <li v-for="item in watchbooks.items" :key="item.id">
            <strong>{{ page.formatDate(item.log_date) }}</strong> · {{ item.summary }}
            <span class="dataset-meta">
              {{ page.formatDateTime(item.occurred_at) }} · {{ item.entry_type_code || "-" }}
            </span>
          </li>
        </ul>

        <div
          v-if="watchbooks?.items.length && page.portalContext.value.capabilities.can_add_watchbook_entries"
          class="portal-watchbook-entry-form"
        >
          <div class="field">
            <label for="customer-watchbook-select">{{ t("portalCustomer.watchbooks.fields.watchbook") }}</label>
            <select id="customer-watchbook-select" v-model="selectedWatchbookId">
              <option v-for="item in watchbooks.items" :key="item.id" :value="item.id">
                {{ page.formatDate(item.log_date) }} · {{ item.summary }}
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
          <div class="portal-actions-row">
            <button
              class="cta-button"
              type="button"
              :disabled="page.loading.value || !selectedWatchbookId || !watchbookNarrative"
              @click="submitWatchbookEntry"
            >
              {{ t("portalCustomer.watchbooks.actions.submit") }}
            </button>
          </div>
        </div>

        <div
          v-else-if="watchbooks?.items.length && !page.portalContext.value.capabilities.can_add_watchbook_entries"
          class="portal-watchbook-disabled"
        >
          <strong>{{ t("portalCustomer.watchbooks.disabledTitle") }}</strong>
          <p>{{ t("portalCustomer.watchbooks.disabledBody") }}</p>
        </div>
      </article>
    </div>
  </CustomerPortalPageShell>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";

import { AuthApiError } from "@/api/auth";
import type { CustomerPortalWatchbookCollectionRead } from "@/api/customerPortal";
import {
  createCustomerPortalWatchbookEntry,
  getCustomerPortalWatchbooks,
} from "@/api/customerPortal";
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

const { t } = useI18n();
const authStore = useAuthStore();
const watchbooks = ref<CustomerPortalWatchbookCollectionRead | null>(null);
const selectedWatchbookId = ref("");
const watchbookNarrative = ref("");

const page = useCustomerPortalPage({
  clearPageData: () => {
    watchbooks.value = null;
    selectedWatchbookId.value = "";
    watchbookNarrative.value = "";
  },
  loadPageData: async () => {
    watchbooks.value = await getCustomerPortalWatchbooks(authStore.accessToken!);
    selectedWatchbookId.value = watchbooks.value.items[0]?.id ?? "";
  },
});

const datasetState = computed(() => derivePortalCollectionState(watchbooks.value));
const datasetMessageKey = computed<MessageKey | null>(() =>
  derivePortalDatasetMessage(watchbooks.value, "portalCustomer.datasets.watchbooks.empty") as MessageKey | null,
);
const watchbookWriteState = computed(() =>
  page.portalContext.value?.capabilities.can_add_watchbook_entries ? "enabled" : "not_enabled",
);
const watchbookPolicyMessageKey = computed<MessageKey>(() =>
  page.portalContext.value?.capabilities.can_add_watchbook_entries
    ? "portalCustomer.capabilities.watchbooks.writeEnabled"
    : "portalCustomer.capabilities.watchbooks.writeDisabled",
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

function capabilityStateKey(state: string): MessageKey {
  switch (state) {
    case "enabled":
      return "portalCustomer.access.states.enabled";
    case "not_enabled":
    default:
      return "portalCustomer.access.states.notEnabled";
  }
}

async function submitWatchbookEntry() {
  if (!authStore.accessToken || !selectedWatchbookId.value || !watchbookNarrative.value) {
    return;
  }

  page.loading.value = true;
  page.clearFeedback();

  try {
    await createCustomerPortalWatchbookEntry(authStore.accessToken, selectedWatchbookId.value, {
      entry_type_code: "customer_note",
      narrative: watchbookNarrative.value,
    });
    watchbookNarrative.value = "";
    await page.bootstrapPortalContext();
    page.setFeedback("portalCustomer.feedback.watchbookEntrySubmitted", "success");
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
.portal-page-card,
.portal-watchbook-entry-form {
  display: grid;
  gap: 1rem;
}

.portal-page-card__header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: start;
}

.portal-page-card__badges {
  display: inline-flex;
  flex-wrap: wrap;
  justify-content: end;
  gap: 0.5rem;
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

.status-badge[data-state="ready"],
.status-badge[data-state="enabled"] {
  background: color-mix(in srgb, var(--sp-primary) 18%, var(--sp-surface-muted));
}

.status-badge[data-state="not_enabled"] {
  background: color-mix(in srgb, #d94f4f 14%, var(--sp-surface-muted));
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

.portal-actions-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.portal-watchbook-disabled {
  display: grid;
  gap: 0.35rem;
  padding: 0.85rem 1rem;
  border-radius: 18px;
  background: color-mix(in srgb, #d94f4f 10%, var(--sp-surface-muted));
}

.portal-watchbook-disabled p {
  margin: 0;
}
</style>
