<script setup lang="ts">
defineProps<{
  eyebrow?: string;
  title: string;
  lead?: string;
}>();
</script>

<template>
  <section class="sp-page-shell">
    <header class="module-card sp-page-shell__hero">
      <div class="sp-page-shell__copy">
        <p v-if="eyebrow" class="eyebrow">{{ eyebrow }}</p>
        <h1 class="sp-page-shell__title">{{ title }}</h1>
        <p v-if="lead" class="sp-page-shell__lead">{{ lead }}</p>
        <div v-if="$slots.meta" class="sp-page-shell__meta">
          <slot name="meta" />
        </div>
      </div>
      <div v-if="$slots.actions" class="sp-page-shell__actions">
        <slot name="actions" />
      </div>
    </header>

    <div v-if="$slots.stats" class="sp-page-shell__stats">
      <slot name="stats" />
    </div>

    <div class="sp-page-shell__body">
      <slot />
    </div>
  </section>
</template>

<style scoped>
.sp-page-shell {
  display: grid;
  gap: 1.25rem;
}

.sp-page-shell__hero {
  display: grid;
  gap: 1.25rem;
  grid-template-columns: minmax(0, 1.6fr) minmax(18rem, 1fr);
  align-items: start;
}

.sp-page-shell__copy {
  display: grid;
  gap: 0.75rem;
}

.sp-page-shell__title {
  margin: 0;
  font-size: clamp(1.8rem, 2.6vw, 2.5rem);
  line-height: 1.05;
}

.sp-page-shell__lead {
  margin: 0;
  max-width: 62ch;
  color: var(--vp-c-text-2, rgb(84 96 111));
  font-size: 1rem;
  line-height: 1.6;
}

.sp-page-shell__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.sp-page-shell__actions {
  display: grid;
  gap: 0.9rem;
}

.sp-page-shell__stats {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(auto-fit, minmax(12rem, 1fr));
}

.sp-page-shell__body {
  display: grid;
  gap: 1.25rem;
}

@media (max-width: 960px) {
  .sp-page-shell__hero {
    grid-template-columns: 1fr;
  }
}
</style>

