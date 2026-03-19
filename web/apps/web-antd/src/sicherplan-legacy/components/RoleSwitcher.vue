<template>
  <label class="role-switcher">
    <span>{{ t("role.label") }}</span>
    <select :value="authStore.activeRole" @change="onChange">
      <option v-for="role in availableRoles" :key="role" :value="role">
        {{ t(roleLabelKeys[role]) }}
      </option>
    </select>
  </label>
</template>

<script setup lang="ts">
import { useI18n } from "@/i18n";
import { useAuthStore } from "@/stores/auth";
import { roleLabelKeys, type AppRole } from "@/types/roles";

const authStore = useAuthStore();
const { t } = useI18n();
const availableRoles: AppRole[] = [
  "platform_admin",
  "tenant_admin",
  "dispatcher",
  "accounting",
  "controller_qm",
  "customer_user",
  "subcontractor_user",
];

function onChange(event: Event) {
  const target = event.target as HTMLSelectElement;
  authStore.setRole(target.value as AppRole);
}
</script>
