<template>
  <div class="landing">
    <section class="hero-card">
      <div class="hero-copy">
        <p class="eyebrow">{{ t("shell.eyebrow") }}</p>
        <h1>{{ t("shell.title") }}</h1>
        <p class="lead">
          {{ t("shell.lead") }}
        </p>
        <div class="cta-row">
          <RouterLink class="cta-button" to="/admin/dashboard">{{ t("shell.cta.admin") }}</RouterLink>
          <RouterLink class="cta-button cta-secondary" to="/portal/customer">
            {{ t("shell.cta.portal") }}
          </RouterLink>
        </div>
      </div>
      <div class="hero-panel">
        <div class="hero-stat">
          <span>{{ t("shell.stat.roles") }}</span>
          <strong>7</strong>
        </div>
        <div class="hero-stat">
          <span>{{ t("shell.stat.modules") }}</span>
          <strong>9</strong>
        </div>
        <div class="hero-stat">
          <span>{{ t("shell.stat.portals") }}</span>
          <strong>2</strong>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from "@/i18n";

const { t } = useI18n();
</script>
