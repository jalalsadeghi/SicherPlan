import { createRouter, createWebHistory } from "vue-router";

import { canAccessAppRoute } from "@/features/portal/customerPortal.helpers.js";
import { appRoutes, type AppRoute } from "@/router/routes";
import { useAuthStore } from "@/stores/auth";

const rootRoutes = [
  {
    path: "/",
    redirect: "/shell",
  },
  {
    path: "/shell",
    name: "shell",
    component: () => import("@/views/ShellHomeView.vue"),
  },
  {
    path: "/admin",
    component: () => import("@/layouts/AdminLayout.vue"),
    children: appRoutes.filter((route: AppRoute) => route.meta.section === "admin"),
  },
  {
    path: "/portal",
    component: () => import("@/layouts/PortalLayout.vue"),
    children: appRoutes.filter((route: AppRoute) => route.meta.section === "portal"),
  },
];

export const router = createRouter({
  history: createWebHistory(),
  routes: rootRoutes,
});

router.beforeEach((to) => {
  const authStore = useAuthStore();
  const role = authStore.effectiveRole;

  if (!to.meta || !("roles" in to.meta)) {
    return true;
  }

  const allowedRoles = (to.meta.roles as string[]) ?? [];
  if (
    canAccessAppRoute({
      allowedRoles,
      allowGuest: Boolean(to.meta.allowGuest),
      role,
      isAuthenticated: authStore.isAuthenticated,
    })
  ) {
    return true;
  }

  return { name: "shell" };
});
