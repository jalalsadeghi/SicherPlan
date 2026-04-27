<template>
  <div class="shell shell-admin">
    <aside class="sidebar">
      <BrandPanel :subtitle="t('brand.adminSubtitle')" />
      <RoleSwitcher />
      <nav class="menu">
        <RouterLink
          v-for="item in menuEntries"
          :key="item.to"
          :to="item.to"
          custom
          v-slot="{ href, navigate, isActive }"
        >
          <a
            :href="href"
            class="menu-item"
            :class="{ 'router-link-active': isActive }"
            @click="handleMenuItemClick($event, item.to, navigate)"
          >
            <span class="menu-icon">{{ item.icon }}</span>
            <span>{{ item.title }}</span>
          </a>
        </RouterLink>
      </nav>
    </aside>
    <main class="content">
      <header class="content-header">
        <div>
          <p class="eyebrow">{{ t("layout.admin.eyebrow") }}</p>
          <h1>{{ t("layout.admin.title") }}</h1>
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
import { useRoute } from "vue-router";
import BrandPanel from "@/components/BrandPanel.vue";
import LocaleSwitcher from "@/components/LocaleSwitcher.vue";
import RoleSwitcher from "@/components/RoleSwitcher.vue";
import ThemeToggle from "@/components/ThemeToggle.vue";
import { dispatchAdminMenuReselect } from "./navigationEvents";

const { t } = useI18n();
const route = useRoute();
const menuEntries = useMenu("admin");

function handleMenuItemClick(event: MouseEvent, to: string, navigate: (event?: MouseEvent) => Promise<unknown>) {
  if (route.path === to) {
    event.preventDefault();
    dispatchAdminMenuReselect(to);
    return;
  }
  void navigate(event);
}
</script>
