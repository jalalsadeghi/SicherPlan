<script lang="ts" setup>
import StatCard from './stat-card.vue';

interface StatItem {
  hint?: string;
  label: string;
  value: string;
}

defineProps<{
  stats: StatItem[];
}>();
</script>

<template>
  <section class="sp-stats-row">
    <StatCard
      v-for="stat in stats"
      :key="stat.label"
      :hint="stat.hint"
      :label="stat.label"
      :value="stat.value"
    />
  </section>
</template>

<style scoped>
.sp-stats-row {
  display: grid;
  gap: 1rem;
  min-width: 0;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

@media (max-width: 960px) {
  .sp-stats-row {
    grid-template-columns: 1fr;
  }
}
</style>
