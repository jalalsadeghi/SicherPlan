<script lang="ts" setup>
import SectionHeader from './section-header.vue';

defineProps<{
  description?: string;
  showHeader?: boolean;
  title: string;
}>();
</script>

<template>
  <section class="sp-section-block">
    <SectionHeader
      v-if="showHeader !== false"
      :description="description"
      :title="title"
    />
    <div class="sp-section-block__body">
      <slot />
    </div>
  </section>
</template>

<style scoped>
.sp-section-block {
  display: grid;
  gap: 1rem;
  min-width: 0;
}

.sp-section-block__body {
  display: grid;
  gap: 1rem;
  min-width: 0;
}
</style>
