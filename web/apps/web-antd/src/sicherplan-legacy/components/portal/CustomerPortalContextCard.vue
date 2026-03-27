<template>
  <article class="module-card portal-customer-context-card">
    <p class="eyebrow">{{ t("portalCustomer.summary.title") }}</p>
    <dl class="portal-context-grid">
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
        <dt>{{ t("portalCustomer.summary.scope") }}</dt>
        <dd>{{ portalScopeSummary }}</dd>
      </div>
    </dl>
  </article>
</template>

<script setup lang="ts">
import { useI18n } from "@/i18n";
import type { CustomerPortalContextRead } from "@/api/auth";

defineProps<{
  portalContext: CustomerPortalContextRead;
  portalScopeSummary: string;
}>();

const { t } = useI18n();
</script>

<style scoped>
.portal-customer-context-card,
.portal-context-grid {
  display: grid;
  gap: 0.85rem;
}

.portal-context-grid {
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}

.portal-context-grid dt {
  color: var(--sp-text-muted);
  font-size: 0.8rem;
}

.portal-context-grid dd {
  margin: 0.2rem 0 0;
  font-weight: 600;
}
</style>
