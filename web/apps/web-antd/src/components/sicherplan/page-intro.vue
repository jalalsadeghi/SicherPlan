<script lang="ts" setup>
interface BadgeItem {
  key: string;
  tone?: 'default' | 'success' | 'warning';
}

withDefaults(
  defineProps<{
    eyebrow?: string;
    title: string;
    description: string;
    badges?: BadgeItem[];
  }>(),
  {
    eyebrow: '',
    badges: () => [],
  },
);
</script>

<template>
  <section class="sp-page-intro">
    <div class="sp-page-intro__copy">
      <p v-if="eyebrow" class="sp-page-intro__eyebrow">{{ eyebrow }}</p>
      <h1 class="sp-page-intro__title">{{ title }}</h1>
      <p class="sp-page-intro__description">{{ description }}</p>
      <div v-if="badges.length" class="sp-page-intro__badges">
        <a-tag
          v-for="badge in badges"
          :key="badge.key"
          :color="badge.tone === 'success' ? 'success' : badge.tone === 'warning' ? 'gold' : 'default'"
          bordered
        >
          {{ badge.key }}
        </a-tag>
      </div>
    </div>
    <div v-if="$slots.actions" class="sp-page-intro__actions">
      <slot name="actions" />
    </div>
  </section>
</template>

<style scoped>
.sp-page-intro {
  position: relative;
  display: grid;
  gap: 1.25rem;
  align-items: start;
  grid-template-columns: minmax(0, 1.8fr) minmax(18rem, 1fr);
  padding: 1.5rem;
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 1.25rem;
  background:
    linear-gradient(135deg, rgb(255 255 255 / 0.84), rgb(255 255 255 / 0.62)),
    var(--sp-gradient-hero);
  box-shadow: var(--sp-shadow-card);
}

[data-theme='dark'] .sp-page-intro {
  background:
    linear-gradient(135deg, rgb(11 25 27 / 0.92), rgb(12 28 30 / 0.78)),
    var(--sp-gradient-hero);
}

.sp-page-intro__copy {
  min-width: 0;
}

.sp-page-intro__eyebrow {
  margin: 0 0 0.5rem;
  color: var(--sp-color-primary-strong);
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.sp-page-intro__title {
  margin: 0;
  color: var(--sp-color-text-primary);
  font-size: clamp(1.75rem, 2.3vw, 2.6rem);
  font-weight: 700;
  line-height: 1.1;
}

.sp-page-intro__description {
  max-width: 60rem;
  margin: 0.85rem 0 0;
  color: var(--sp-color-text-secondary);
  font-size: 1rem;
  line-height: 1.6;
}

.sp-page-intro__badges {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 1rem;
}

.sp-page-intro__actions {
  display: flex;
  align-items: flex-start;
  align-self: start;
}

.sp-page-intro__actions > :deep(*) {
  width: 100%;
}

@media (max-width: 960px) {
  .sp-page-intro {
    grid-template-columns: 1fr;
  }
}
</style>
