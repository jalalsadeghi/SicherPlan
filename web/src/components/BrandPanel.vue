<template>
  <div class="brand-panel">
    <div class="brand-mark" aria-hidden="true">
      <span class="brand-s">S</span>
    </div>
    <div>
      <div class="brand-title">{{ webAppConfig.appTitle }}</div>
      <div class="brand-subtitle">{{ subtitle }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { webAppConfig } from "@/config/env";

defineProps<{
  subtitle: string;
}>();
</script>
