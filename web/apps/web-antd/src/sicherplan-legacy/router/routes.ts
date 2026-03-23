import type { RouteRecordRaw } from "vue-router";

import type { AppRole } from "@/types/roles";

export interface AppRouteMeta {
  titleKey: string;
  icon: string;
  roles: AppRole[];
  section: "admin" | "portal";
  placeholder?: boolean;
  allowGuest?: boolean;
  permissionKey?: string;
  actionKeys?: string[];
}

export type AppRoute = RouteRecordRaw & {
  meta: AppRouteMeta;
  children?: AppRoute[];
};

export const appRoutes: AppRoute[] = [
  {
    path: "/admin/dashboard",
    name: "admin-dashboard",
    component: () => import("@/views/ModulePlaceholderView.vue"),
    meta: {
      titleKey: "route.admin.dashboard.title",
      icon: "grid",
      roles: ["platform_admin", "tenant_admin", "dispatcher", "accounting", "controller_qm"],
      section: "admin",
    },
    props: {
      titleKey: "route.admin.dashboard.title",
      descriptionKey: "route.admin.dashboard.description",
    },
  },
  {
    path: "/admin/core",
    name: "admin-core",
    component: () => import("@/views/CoreAdminView.vue"),
    meta: {
      titleKey: "route.admin.core.title",
      icon: "building",
      roles: ["platform_admin", "tenant_admin"],
      section: "admin",
      permissionKey: "core.admin.access",
      actionKeys: [
        "core.admin.tenant.read",
        "core.admin.tenant.write",
        "core.admin.branch.write",
        "core.admin.mandate.write",
        "core.admin.setting.write",
      ],
    },
  },
  {
    path: "/admin/platform-services",
    name: "admin-platform-services",
    component: () => import("@/views/NoticeAdminView.vue"),
    meta: {
      titleKey: "route.admin.platform_services.title",
      icon: "layers",
      roles: ["platform_admin", "tenant_admin", "controller_qm"],
      section: "admin",
      permissionKey: "platform.info.write",
      actionKeys: ["platform.info.read", "platform.info.write"],
    },
  },
  {
    path: "/admin/customers",
    name: "admin-customers",
    component: () => import("@/views/CustomerAdminView.vue"),
    meta: {
      titleKey: "route.admin.customers.title",
      icon: "users",
      roles: ["platform_admin", "tenant_admin", "accounting"],
      section: "admin",
      permissionKey: "customers.customer.read",
      actionKeys: [
        "customers.customer.read",
        "customers.customer.write",
        "customers.billing.read",
        "customers.billing.write",
      ],
    },
  },
  {
    path: "/admin/employees",
    name: "admin-employees",
    component: () => import("@/views/ModulePlaceholderView.vue"),
    meta: {
      titleKey: "route.admin.employees.title",
      icon: "badge",
      roles: ["tenant_admin", "dispatcher", "controller_qm"],
      section: "admin",
      placeholder: true,
    },
    props: {
      titleKey: "route.admin.employees.title",
      descriptionKey: "route.admin.employees.description",
    },
  },
  {
    path: "/admin/subcontractors",
    name: "admin-subcontractors",
    component: () => import("@/views/ModulePlaceholderView.vue"),
    meta: {
      titleKey: "route.admin.subcontractors.title",
      icon: "handshake",
      roles: ["tenant_admin", "dispatcher", "controller_qm"],
      section: "admin",
      placeholder: true,
    },
    props: {
      titleKey: "route.admin.subcontractors.title",
      descriptionKey: "route.admin.subcontractors.description",
    },
  },
  {
    path: "/admin/planning",
    name: "admin-planning",
    component: () => import("@/views/ModulePlaceholderView.vue"),
    meta: {
      titleKey: "route.admin.planning.title",
      icon: "calendar",
      roles: ["tenant_admin", "dispatcher", "controller_qm"],
      section: "admin",
      placeholder: true,
    },
    props: {
      titleKey: "route.admin.planning.title",
      descriptionKey: "route.admin.planning.description",
    },
  },
  {
    path: "/admin/field-execution",
    name: "admin-field-execution",
    component: () => import("@/views/ModulePlaceholderView.vue"),
    meta: {
      titleKey: "route.admin.field_execution.title",
      icon: "shield",
      roles: ["tenant_admin", "dispatcher", "controller_qm"],
      section: "admin",
      placeholder: true,
    },
    props: {
      titleKey: "route.admin.field_execution.title",
      descriptionKey: "route.admin.field_execution.description",
    },
  },
  {
    path: "/admin/finance",
    name: "admin-finance",
    component: () => import("@/views/ModulePlaceholderView.vue"),
    meta: {
      titleKey: "route.admin.finance.title",
      icon: "wallet",
      roles: ["tenant_admin", "accounting", "controller_qm"],
      section: "admin",
      placeholder: true,
    },
    props: {
      titleKey: "route.admin.finance.title",
      descriptionKey: "route.admin.finance.description",
    },
  },
  {
    path: "/admin/reporting",
    name: "admin-reporting",
    component: () => import("@/views/ModulePlaceholderView.vue"),
    meta: {
      titleKey: "route.admin.reporting.title",
      icon: "chart",
      roles: ["platform_admin", "tenant_admin", "accounting", "controller_qm"],
      section: "admin",
      placeholder: true,
    },
    props: {
      titleKey: "route.admin.reporting.title",
      descriptionKey: "route.admin.reporting.description",
    },
  },
  {
    path: "/portal/customer",
    name: "portal-customer",
    component: () => import("@/views/CustomerPortalAccessView.vue"),
    meta: {
      titleKey: "route.portal.customer.title",
      icon: "portal",
      roles: ["customer_user"],
      section: "portal",
      allowGuest: true,
      permissionKey: "portal.customer.access",
    },
  },
  {
    path: "/portal/subcontractor",
    name: "portal-subcontractor",
    component: () => import("@/views/SubcontractorPortalAccessView.vue"),
    meta: {
      titleKey: "route.portal.subcontractor.title",
      icon: "briefcase",
      roles: ["subcontractor_user"],
      section: "portal",
      allowGuest: true,
      permissionKey: "portal.subcontractor.access",
    },
  },
];
