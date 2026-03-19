<template>
  <div class="shell shell-portal">
    <aside class="sidebar portal-sidebar">
      <BrandPanel :subtitle="t('brand.portalSubtitle')" />
      <RoleSwitcher v-if="!authStore.hasSession" />
      <nav class="menu">
        <RouterLink
          v-for="item in menuEntries"
          :key="item.to"
          class="menu-item"
          :to="item.to"
        >
          <span class="menu-icon">{{ item.icon }}</span>
          <span>{{ item.title }}</span>
        </RouterLink>
      </nav>
    </aside>
    <main class="content">
      <header class="content-header">
        <div>
          <p class="eyebrow">{{ t("layout.portal.eyebrow") }}</p>
          <h1>{{ t("layout.portal.title") }}</h1>
        </div>
        <LocaleSwitcher />
        <ThemeToggle />
      </header>
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from "@/i18n";
import { useMenu } from "@/config/menu";
import BrandPanel from "@/components/BrandPanel.vue";
import LocaleSwitcher from "@/components/LocaleSwitcher.vue";
import RoleSwitcher from "@/components/RoleSwitcher.vue";
import ThemeToggle from "@/components/ThemeToggle.vue";
import { useAuthStore } from "@/stores/auth";

const { t } = useI18n();
const menuEntries = useMenu("portal");
const authStore = useAuthStore();
</script>
