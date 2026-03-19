import { defineStore } from "pinia";

import {
  AuthApiError,
  getCurrentSession,
  getCustomerPortalContext,
  login,
  logout,
  type AuthenticatedUser,
  type CustomerPortalContextRead,
  type LoginPayload,
  type LoginResponse,
} from "@/api/auth";
import type { AppRole } from "@/types/roles";

const ROLE_STORAGE_KEY = "sicherplan-role";
const TENANT_SCOPE_STORAGE_KEY = "sicherplan-tenant-scope";
const ACCESS_TOKEN_STORAGE_KEY = "sicherplan-access-token";
const REFRESH_TOKEN_STORAGE_KEY = "sicherplan-refresh-token";
const SESSION_USER_STORAGE_KEY = "sicherplan-session-user";
const SESSION_ID_STORAGE_KEY = "sicherplan-session-id";
const PORTAL_CUSTOMER_CONTEXT_STORAGE_KEY = "sicherplan-portal-customer-context";

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

function readStoredString(key: string): string {
  if (typeof window === "undefined") {
    return "";
  }

  return window.localStorage.getItem(key) ?? "";
}

function readStoredJson<T>(key: string, fallback: T): T {
  if (typeof window === "undefined") {
    return fallback;
  }

  const value = window.localStorage.getItem(key);
  if (!value) {
    return fallback;
  }

  try {
    return JSON.parse(value) as T;
  } catch {
    return fallback;
  }
}

function persistString(key: string, value: string) {
  if (typeof window === "undefined") {
    return;
  }

  if (!value) {
    window.localStorage.removeItem(key);
    return;
  }

  window.localStorage.setItem(key, value);
}

function persistJson(key: string, value: unknown) {
  if (typeof window === "undefined") {
    return;
  }

  if (value == null) {
    window.localStorage.removeItem(key);
    return;
  }

  window.localStorage.setItem(key, JSON.stringify(value));
}

function pickSessionRole(user: AuthenticatedUser | null): AppRole | null {
  if (!user) {
    return null;
  }

  for (const role of user.roles) {
    switch (role.role_key) {
      case "platform_admin":
      case "tenant_admin":
      case "dispatcher":
      case "accounting":
      case "controller_qm":
      case "customer_user":
      case "subcontractor_user":
        return role.role_key;
      default:
        break;
    }
  }

  return null;
}

export const useAuthStore = defineStore("sicherplan-legacy-auth", {
  state: () => ({
    activeRole: readStoredRole() as AppRole,
    tenantScopeId: readStoredTenantScopeId(),
    accessToken: readStoredString(ACCESS_TOKEN_STORAGE_KEY),
    refreshToken: readStoredString(REFRESH_TOKEN_STORAGE_KEY),
    sessionId: readStoredString(SESSION_ID_STORAGE_KEY),
    sessionUser: readStoredJson<AuthenticatedUser | null>(SESSION_USER_STORAGE_KEY, null),
    portalCustomerContext: readStoredJson<CustomerPortalContextRead | null>(
      PORTAL_CUSTOMER_CONTEXT_STORAGE_KEY,
      null,
    ),
  }),
  getters: {
    effectiveRole(state): AppRole {
      return pickSessionRole(state.sessionUser) ?? state.activeRole;
    },
    hasSession(state): boolean {
      return Boolean(state.accessToken && state.sessionUser);
    },
    isAuthenticated(): boolean {
      return true;
    },
    isSessionBacked(): boolean {
      return this.hasSession;
    },
  },
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
    setSession(payload: LoginResponse) {
      this.accessToken = payload.session.access_token;
      this.refreshToken = payload.session.refresh_token;
      this.sessionId = payload.session.session_id;
      this.sessionUser = payload.user;
      this.activeRole = pickSessionRole(payload.user) ?? this.activeRole;

      persistString(ACCESS_TOKEN_STORAGE_KEY, this.accessToken);
      persistString(REFRESH_TOKEN_STORAGE_KEY, this.refreshToken);
      persistString(SESSION_ID_STORAGE_KEY, this.sessionId);
      persistJson(SESSION_USER_STORAGE_KEY, this.sessionUser);

      if (typeof window !== "undefined") {
        window.localStorage.setItem(ROLE_STORAGE_KEY, this.activeRole);
      }
    },
    clearPortalCustomerContext() {
      this.portalCustomerContext = null;
      persistJson(PORTAL_CUSTOMER_CONTEXT_STORAGE_KEY, null);
    },
    clearSession() {
      this.accessToken = "";
      this.refreshToken = "";
      this.sessionId = "";
      this.sessionUser = null;
      this.clearPortalCustomerContext();
      persistString(ACCESS_TOKEN_STORAGE_KEY, "");
      persistString(REFRESH_TOKEN_STORAGE_KEY, "");
      persistString(SESSION_ID_STORAGE_KEY, "");
      persistJson(SESSION_USER_STORAGE_KEY, null);
    },
    async loginCustomerPortal(payload: LoginPayload) {
      const response = await login(payload);
      this.setSession(response);
      return response;
    },
    async loadCurrentSession() {
      if (!this.accessToken) {
        this.clearSession();
        return null;
      }

      try {
        const response = await getCurrentSession(this.accessToken);
        this.sessionUser = response.user;
        this.sessionId = response.session.id;
        persistJson(SESSION_USER_STORAGE_KEY, this.sessionUser);
        persistString(SESSION_ID_STORAGE_KEY, this.sessionId);
        return response;
      } catch (error) {
        if (error instanceof AuthApiError && error.statusCode === 401) {
          this.clearSession();
        }
        throw error;
      }
    },
    async loadCustomerPortalContext() {
      if (!this.accessToken) {
        this.clearPortalCustomerContext();
        return null;
      }

      try {
        const context = await getCustomerPortalContext(this.accessToken);
        this.portalCustomerContext = context;
        persistJson(PORTAL_CUSTOMER_CONTEXT_STORAGE_KEY, context);
        return context;
      } catch (error) {
        this.clearPortalCustomerContext();
        if (error instanceof AuthApiError && error.statusCode === 401) {
          this.clearSession();
        }
        throw error;
      }
    },
    async logoutSession() {
      try {
        if (this.accessToken) {
          await logout(this.accessToken);
        }
      } finally {
        this.clearSession();
      }
    },
  },
});
