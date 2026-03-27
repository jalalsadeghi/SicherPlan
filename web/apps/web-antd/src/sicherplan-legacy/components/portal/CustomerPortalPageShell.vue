<template>
  <section class="module-card portal-customer-view">
    <p class="eyebrow">{{ t("portalCustomer.eyebrow") }}</p>
    <div class="portal-customer-header">
      <div>
        <h2>{{ t(titleKey) }}</h2>
        <p>{{ t(leadKey) }}</p>
      </div>
      <div class="portal-actions">
        <button class="secondary-button" type="button" @click="$emit('refresh')">
          {{ t("portalCustomer.actions.refresh") }}
        </button>
        <button
          v-if="hasSession"
          class="secondary-button"
          type="button"
          @click="$emit('logout')"
        >
          {{ t("portalCustomer.actions.logout") }}
        </button>
      </div>
    </div>

    <p v-if="feedbackKey" class="portal-feedback" :data-tone="feedbackTone">
      {{ t(feedbackKey) }}
    </p>

    <form v-if="accessState === 'login'" class="portal-login-grid" @submit.prevent="$emit('submitLogin')">
      <div class="field">
        <label for="tenant-code">{{ t("portalCustomer.login.tenantCode") }}</label>
        <input
          id="tenant-code"
          :value="tenantCode"
          autocomplete="organization"
          required
          @input="$emit('update:tenantCode', (($event.target as HTMLInputElement).value ?? '').trim())"
        />
      </div>
      <div class="field">
        <label for="identifier">{{ t("portalCustomer.login.identifier") }}</label>
        <input
          id="identifier"
          :value="identifier"
          autocomplete="username"
          required
          @input="$emit('update:identifier', (($event.target as HTMLInputElement).value ?? '').trim())"
        />
      </div>
      <div class="field">
        <label for="password">{{ t("portalCustomer.login.password") }}</label>
        <input
          id="password"
          :value="password"
          autocomplete="current-password"
          type="password"
          required
          @input="$emit('update:password', ($event.target as HTMLInputElement).value ?? '')"
        />
      </div>
      <div class="field">
        <label for="device-label">{{ t("portalCustomer.login.deviceLabel") }}</label>
        <input
          id="device-label"
          :value="deviceLabel"
          autocomplete="off"
          @input="$emit('update:deviceLabel', (($event.target as HTMLInputElement).value ?? '').trim())"
        />
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

    <div v-else-if="portalDiagnosticTitleKey && portalDiagnosticBodyKey" class="portal-state-card">
      <h3>{{ t(portalDiagnosticTitleKey) }}</h3>
      <p>{{ t(portalDiagnosticBodyKey) }}</p>
    </div>

    <slot v-else />
  </section>
</template>

<script setup lang="ts">
import { useI18n } from "@/i18n";
import type { MessageKey } from "@/i18n/messages";

defineProps<{
  titleKey: MessageKey;
  leadKey: MessageKey;
  feedbackKey: MessageKey | null;
  feedbackTone: "info" | "success" | "error";
  loading: boolean;
  accessState: string;
  hasSession: boolean;
  portalDiagnosticTitleKey: MessageKey | null;
  portalDiagnosticBodyKey: MessageKey | null;
  tenantCode: string;
  identifier: string;
  password: string;
  deviceLabel: string;
}>();

defineEmits<{
  (event: "refresh"): void;
  (event: "logout"): void;
  (event: "submitLogin"): void;
  (event: "update:tenantCode", value: string): void;
  (event: "update:identifier", value: string): void;
  (event: "update:password", value: string): void;
  (event: "update:deviceLabel", value: string): void;
}>();

const { t } = useI18n();
</script>

<style scoped>
.portal-customer-view,
.portal-customer-header,
.portal-actions,
.portal-login-grid,
.portal-state-card {
  display: grid;
  gap: 1rem;
}

.portal-customer-header {
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: start;
}

.portal-actions {
  grid-auto-flow: column;
  align-items: start;
}

.portal-feedback {
  margin: 0;
  padding: 0.85rem 1rem;
  border-radius: 16px;
  background: var(--sp-surface-muted);
}

.portal-feedback[data-tone="error"] {
  background: color-mix(in srgb, #d94f4f 12%, var(--sp-surface-muted));
}

.portal-feedback[data-tone="success"] {
  background: color-mix(in srgb, var(--sp-primary) 14%, var(--sp-surface-muted));
}

.portal-login-grid {
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}

.portal-login-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: center;
}

.portal-state-card {
  padding: 1rem;
  border-radius: 18px;
  background: var(--sp-surface-muted);
}

@media (max-width: 700px) {
  .portal-customer-header {
    grid-template-columns: 1fr;
  }

  .portal-actions {
    grid-auto-flow: row;
  }
}
</style>
