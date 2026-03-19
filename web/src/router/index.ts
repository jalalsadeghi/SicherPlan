import { createRouter, createWebHistory } from "vue-router";

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
  const role = authStore.activeRole;

  if (!to.meta || !("roles" in to.meta)) {
    return true;
  }

  const allowedRoles = (to.meta.roles as string[]) ?? [];
  if (allowedRoles.length === 0 || allowedRoles.includes(role)) {
    return true;
  }

  return { name: "shell" };
});
