<template>
  <span class="status-badge" :data-status="normalizedStatus">
    {{ label }}
  </span>
</template>

<script setup lang="ts">
import { computed } from "vue";

import { useI18n } from "@/i18n";

const props = defineProps<{
  status: string;
}>();

const { t } = useI18n();

const normalizedStatus = computed(() => {
  if (props.status === "active" || props.status === "inactive" || props.status === "archived") {
    return props.status;
  }

  return "inactive";
});

const label = computed(() => t(`coreAdmin.status.${normalizedStatus.value}` as never));
</script>

<style scoped>
.status-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.28rem 0.7rem;
  border-radius: 999px;
  border: 1px solid var(--sp-color-border-soft);
  background: color-mix(in srgb, var(--sp-color-surface-card) 92%, transparent);
  color: var(--sp-color-text-primary);
  font-size: 0.78rem;
  font-weight: 700;
  white-space: nowrap;
}

.status-badge[data-status="active"] {
  background: color-mix(in srgb, var(--sp-color-success) 16%, white);
  color: color-mix(in srgb, var(--sp-color-success) 75%, black);
}

.status-badge[data-status="inactive"] {
  background: color-mix(in srgb, var(--sp-color-warning) 16%, white);
  color: color-mix(in srgb, var(--sp-color-warning) 85%, black);
}

.status-badge[data-status="archived"] {
  background: color-mix(in srgb, var(--sp-color-danger) 16%, white);
  color: color-mix(in srgb, var(--sp-color-danger) 82%, black);
}
</style>
