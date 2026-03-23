<template>
  <section class="sp-split-view-layout">
    <div class="sp-split-view-layout__main">
      <slot name="main" />
    </div>
    <aside class="sp-split-view-layout__aside">
      <slot name="aside" />
    </aside>
  </section>
</template>

<style scoped>
.sp-split-view-layout {
  display: grid;
  gap: 1rem;
  align-items: start;
  grid-template-columns: minmax(0, 2fr) minmax(18rem, 1fr);
}

.sp-split-view-layout__main,
.sp-split-view-layout__aside {
  display: grid;
  gap: 1rem;
  align-content: start;
  min-width: 0;
}

@media (max-width: 1100px) {
  .sp-split-view-layout {
    grid-template-columns: 1fr;
  }
}
</style>
