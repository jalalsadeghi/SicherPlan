<template>
  <AdminPageShell :eyebrow="t('shell.eyebrow')" :title="t('shell.title')" :lead="t('shell.lead')">
    <template #actions>
      <div class="hero-panel">
        <div class="cta-row">
          <RouterLink class="cta-button" to="/admin/core">{{ t("shell.cta.admin") }}</RouterLink>
          <RouterLink class="cta-button cta-secondary" to="/portal/customer">
            {{ t("shell.cta.portal") }}
          </RouterLink>
        </div>
      </div>
    </template>
    <template #stats>
      <AdminStatCard :label="t('shell.stat.roles')" :value="7" tone="accent" />
      <AdminStatCard :label="t('shell.stat.modules')" :value="6" />
      <AdminStatCard :label="t('shell.stat.portals')" :value="2" />
    </template>
    <section class="landing-grid">
      <RouterLink v-for="entry in entries" :key="entry.to" class="module-card landing-card" :to="entry.to">
        <p class="eyebrow">{{ entry.eyebrow }}</p>
        <h2>{{ entry.title }}</h2>
        <p>{{ entry.lead }}</p>
      </RouterLink>
    </section>
  </AdminPageShell>
</template>

<script setup lang="ts">
import { computed } from "vue";

import AdminPageShell from "@/components/AdminPageShell.vue";
import AdminStatCard from "@/components/AdminStatCard.vue";
import { useI18n } from "@/i18n";

const { t } = useI18n();

const entries = computed(() => [
  {
    to: "/admin/core",
    eyebrow: t("module.eyebrow"),
    title: t("route.admin.core.title"),
    lead: t("route.admin.core.description"),
  },
  {
    to: "/admin/customers",
    eyebrow: t("module.eyebrow"),
    title: t("route.admin.customers.title"),
    lead: t("route.admin.customers.description"),
  },
  {
    to: "/admin/planning",
    eyebrow: t("module.eyebrow"),
    title: t("route.admin.planning.title"),
    lead: t("route.admin.planning.description"),
  },
  {
    to: "/admin/reporting",
    eyebrow: t("module.eyebrow"),
    title: t("route.admin.reporting.title"),
    lead: t("route.admin.reporting.description"),
  },
]);
</script>

<style scoped>
.landing-grid {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr));
}

.landing-card {
  color: inherit;
  text-decoration: none;
  transition:
    transform 0.18s ease,
    box-shadow 0.18s ease,
    border-color 0.18s ease;
}

.landing-card:hover {
  transform: translateY(-2px);
  border-color: rgb(40 170 170 / 24%);
  box-shadow: 0 16px 38px rgb(15 23 42 / 0.08);
}

.landing-card h2 {
  margin: 0 0 0.5rem;
}

.landing-card p:last-child {
  margin: 0;
}
</style>
