import { computed } from "vue";

import { appRoutes } from "@/router/routes";
import { useI18n } from "@/i18n";
import { useAuthStore } from "@/stores/auth";
import type { AppRole } from "@/types/roles";
import type { AppRoute } from "@/router/routes";

export interface MenuEntry {
  title: string;
  icon: string;
  to: string;
}

function canAccess(role: AppRole, allowedRoles: AppRole[]) {
  return allowedRoles.includes(role);
}

export function useMenu(section: "admin" | "portal") {
  const authStore = useAuthStore();
  const { t } = useI18n();

  return computed<MenuEntry[]>(() =>
    appRoutes
      .filter((route: AppRoute) => route.meta.section === section)
      .filter((route: AppRoute) => canAccess(authStore.activeRole, route.meta.roles))
      .map((route: AppRoute) => ({
        title: t(route.meta.titleKey as never),
        icon: route.meta.icon,
        to: route.path,
      })),
  );
}
