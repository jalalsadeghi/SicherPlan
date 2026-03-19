import { defineStore } from "pinia";

import type { AppRole } from "@/types/roles";

const ROLE_STORAGE_KEY = "sicherplan-role";
const TENANT_SCOPE_STORAGE_KEY = "sicherplan-tenant-scope";

function readStoredRole(): AppRole {
  if (typeof window === "undefined") {
    return "tenant_admin";
  }

  const value = window.localStorage.getItem(ROLE_STORAGE_KEY);
  switch (value) {
    case "platform_admin":
    case "tenant_admin":
    case "dispatcher":
    case "accounting":
    case "controller_qm":
    case "customer_user":
    case "subcontractor_user":
      return value;
    default:
      return "tenant_admin";
  }
}

function readStoredTenantScopeId(): string {
  if (typeof window === "undefined") {
    return "";
  }

  return window.localStorage.getItem(TENANT_SCOPE_STORAGE_KEY) ?? "";
}

export const useAuthStore = defineStore("auth", {
  state: () => ({
    activeRole: readStoredRole() as AppRole,
    isAuthenticated: true,
    tenantScopeId: readStoredTenantScopeId(),
  }),
  actions: {
    setRole(role: AppRole) {
      this.activeRole = role;

      if (typeof window !== "undefined") {
        window.localStorage.setItem(ROLE_STORAGE_KEY, role);
      }
    },
    setTenantScopeId(tenantId: string) {
      this.tenantScopeId = tenantId.trim();

      if (typeof window !== "undefined") {
        window.localStorage.setItem(TENANT_SCOPE_STORAGE_KEY, this.tenantScopeId);
      }
    },
  },
});
