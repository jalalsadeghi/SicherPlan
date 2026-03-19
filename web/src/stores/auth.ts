import { defineStore } from "pinia";

import type { AppRole } from "@/types/roles";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    activeRole: "tenant_admin" as AppRole,
    isAuthenticated: true,
  }),
  actions: {
    setRole(role: AppRole) {
      this.activeRole = role;
    },
  },
});
