import { defineStore } from "pinia";
import { useAccessStore, useUserStore } from "@vben/stores";

import {
  AuthApiError,
  getCurrentSession,
  getCustomerPortalContext,
  getSubcontractorPortalContext,
  login,
  logout,
  type AuthenticatedUser,
  type CustomerPortalContextRead,
  type LoginPayload,
  type LoginResponse,
  type SubcontractorPortalContextRead,
} from "../api/auth";
import type { AppRole } from "@/types/roles";

const ROLE_STORAGE_KEY = "sicherplan-role";
const TENANT_SCOPE_STORAGE_KEY = "sicherplan-tenant-scope";
const ACCESS_TOKEN_STORAGE_KEY = "sicherplan-access-token";
const REFRESH_TOKEN_STORAGE_KEY = "sicherplan-refresh-token";
const SESSION_USER_STORAGE_KEY = "sicherplan-session-user";
const SESSION_ID_STORAGE_KEY = "sicherplan-session-id";
const PORTAL_CUSTOMER_CONTEXT_STORAGE_KEY = "sicherplan-portal-customer-context";
const PORTAL_SUBCONTRACTOR_CONTEXT_STORAGE_KEY = "sicherplan-portal-subcontractor-context";

function readPrimaryAccessToken(): string {
  try {
    return useAccessStore().accessToken ?? "";
  } catch {
    return "";
  }
}

function readPrimaryRoleKeys(): string[] {
  try {
    const roles = useUserStore().userInfo?.roles;
    return Array.isArray(roles) ? roles.filter((role): role is string => typeof role === "string") : [];
  } catch {
    return [];
  }
}

function pickRoleFromKeys(roleKeys: string[]): AppRole | null {
  const roleSet = new Set(roleKeys);
  for (const roleKey of [
    "platform_admin",
    "tenant_admin",
    "dispatcher",
    "accounting",
    "controller_qm",
    "customer_user",
    "subcontractor_user",
  ] as const) {
    if (roleSet.has(roleKey)) {
      return roleKey;
    }
  }

  return null;
}

function readStoredRole(): AppRole {
  const primaryRole = pickRoleFromKeys(readPrimaryRoleKeys());
  if (primaryRole) {
    return primaryRole;
  }

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

  const roleKeys = new Set(user.roles.map((role) => role.role_key));
  for (const roleKey of [
    "platform_admin",
    "tenant_admin",
    "dispatcher",
    "accounting",
    "controller_qm",
    "customer_user",
    "subcontractor_user",
  ] as const) {
    if (roleKeys.has(roleKey)) {
      return roleKey;
    }
  }

  return null;
}

function isPortalSessionRole(role: AppRole | null): boolean {
  return role === "customer_user" || role === "subcontractor_user";
}

function resolveTenantScopeIdForRole(
  role: AppRole,
  sessionUser: AuthenticatedUser | null,
  rememberedTenantScopeId: string,
): string {
  if (role === "platform_admin") {
    return rememberedTenantScopeId;
  }

  return sessionUser?.tenant_id ?? "";
}

export const useAuthStore = defineStore("sicherplan-legacy-auth", {
  state: () => ({
    activeRole: readStoredRole() as AppRole,
    tenantScopeId: readStoredTenantScopeId(),
    accessToken: readStoredString(ACCESS_TOKEN_STORAGE_KEY) || readPrimaryAccessToken(),
    refreshToken: readStoredString(REFRESH_TOKEN_STORAGE_KEY),
    sessionId: readStoredString(SESSION_ID_STORAGE_KEY),
    sessionUser: readStoredJson<AuthenticatedUser | null>(SESSION_USER_STORAGE_KEY, null),
    portalCustomerContext: readStoredJson<CustomerPortalContextRead | null>(
      PORTAL_CUSTOMER_CONTEXT_STORAGE_KEY,
      null,
    ),
    portalSubcontractorContext: readStoredJson<SubcontractorPortalContextRead | null>(
      PORTAL_SUBCONTRACTOR_CONTEXT_STORAGE_KEY,
      null,
    ),
  }),
  getters: {
    effectiveRole(state): AppRole {
      return pickSessionRole(state.sessionUser) ?? pickRoleFromKeys(readPrimaryRoleKeys()) ?? state.activeRole;
    },
    accessRoles(): string[] {
      return [this.effectiveRole];
    },
    effectiveTenantScopeId(state): string {
      return resolveTenantScopeIdForRole(
        this.effectiveRole,
        state.sessionUser,
        state.tenantScopeId,
      );
    },
    effectiveAccessToken(state): string {
      return state.accessToken || readPrimaryAccessToken();
    },
    hasSession(state): boolean {
      return Boolean((state.accessToken || readPrimaryAccessToken()) && (state.sessionUser || readPrimaryRoleKeys().length));
    },
    isAuthenticated(): boolean {
      return true;
    },
    isSessionBacked(): boolean {
      return this.hasSession;
    },
  },
  actions: {
    syncFromPrimarySession() {
      const primaryAccessToken = readPrimaryAccessToken();
      const primaryRole = pickRoleFromKeys(readPrimaryRoleKeys());
      const sessionRole = pickSessionRole(this.sessionUser);
      const preservePortalSession =
        Boolean(this.accessToken && this.sessionUser)
        && isPortalSessionRole(sessionRole)
        && Boolean(primaryAccessToken)
        && primaryAccessToken !== this.accessToken;

      if (primaryAccessToken && primaryAccessToken !== this.accessToken && !preservePortalSession) {
        this.accessToken = primaryAccessToken;
        this.sessionId = "";
        this.sessionUser = null;
        this.clearPortalCustomerContext();
        this.clearPortalSubcontractorContext();
        persistString(ACCESS_TOKEN_STORAGE_KEY, this.accessToken);
        persistString(SESSION_ID_STORAGE_KEY, "");
        persistJson(SESSION_USER_STORAGE_KEY, null);
      }

      if (primaryRole && primaryRole !== this.activeRole) {
        this.activeRole = primaryRole;
        if (typeof window !== "undefined") {
          window.localStorage.setItem(ROLE_STORAGE_KEY, this.activeRole);
        }
      }
    },
    setRole(role: AppRole) {
      this.activeRole = role;

      if (typeof window !== "undefined") {
        window.localStorage.setItem(ROLE_STORAGE_KEY, role);
      }
    },
    setTenantScopeId(tenantId: string) {
      const requestedTenantId = tenantId.trim();
      const sessionTenantId = this.sessionUser?.tenant_id?.trim() ?? "";

      this.tenantScopeId =
        this.effectiveRole === "platform_admin"
          ? requestedTenantId
          : sessionTenantId || this.tenantScopeId || requestedTenantId;

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
      this.tenantScopeId = resolveTenantScopeIdForRole(
        this.activeRole,
        payload.user,
        this.tenantScopeId,
      );

      persistString(ACCESS_TOKEN_STORAGE_KEY, this.accessToken);
      persistString(REFRESH_TOKEN_STORAGE_KEY, this.refreshToken);
      persistString(SESSION_ID_STORAGE_KEY, this.sessionId);
      persistJson(SESSION_USER_STORAGE_KEY, this.sessionUser);
      persistString(TENANT_SCOPE_STORAGE_KEY, this.tenantScopeId);

      if (typeof window !== "undefined") {
        window.localStorage.setItem(ROLE_STORAGE_KEY, this.activeRole);
      }
    },
    clearPortalCustomerContext() {
      this.portalCustomerContext = null;
      persistJson(PORTAL_CUSTOMER_CONTEXT_STORAGE_KEY, null);
    },
    clearPortalSubcontractorContext() {
      this.portalSubcontractorContext = null;
      persistJson(PORTAL_SUBCONTRACTOR_CONTEXT_STORAGE_KEY, null);
    },
    clearSession() {
      this.accessToken = "";
      this.refreshToken = "";
      this.sessionId = "";
      this.tenantScopeId = "";
      this.sessionUser = null;
      this.clearPortalCustomerContext();
      this.clearPortalSubcontractorContext();
      persistString(ACCESS_TOKEN_STORAGE_KEY, "");
      persistString(REFRESH_TOKEN_STORAGE_KEY, "");
      persistString(SESSION_ID_STORAGE_KEY, "");
      persistString(TENANT_SCOPE_STORAGE_KEY, "");
      persistJson(SESSION_USER_STORAGE_KEY, null);
    },
    async loginCustomerPortal(payload: LoginPayload) {
      const response = await login(payload);
      this.setSession(response);
      return response;
    },
    async loadCurrentSession() {
      this.syncFromPrimarySession();

      if (!this.effectiveAccessToken) {
        this.clearSession();
        return null;
      }

      try {
        const response = await getCurrentSession(this.effectiveAccessToken);
        this.accessToken = this.effectiveAccessToken;
        this.sessionUser = response.user;
        this.sessionId = response.session.id;
        this.activeRole = pickSessionRole(response.user) ?? this.activeRole;
        this.tenantScopeId = resolveTenantScopeIdForRole(
          this.activeRole,
          response.user,
          this.tenantScopeId,
        );
        persistJson(SESSION_USER_STORAGE_KEY, this.sessionUser);
        persistString(SESSION_ID_STORAGE_KEY, this.sessionId);
        persistString(TENANT_SCOPE_STORAGE_KEY, this.tenantScopeId);
        if (typeof window !== "undefined") {
          window.localStorage.setItem(ROLE_STORAGE_KEY, this.activeRole);
        }
        return response;
      } catch (error) {
        if (error instanceof AuthApiError && error.statusCode === 401) {
          this.clearSession();
        }
        throw error;
      }
    },
    async loadCustomerPortalContext() {
      this.syncFromPrimarySession();

      if (!this.effectiveAccessToken) {
        this.clearPortalCustomerContext();
        return null;
      }

      try {
        const context = await getCustomerPortalContext(this.effectiveAccessToken);
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
    async loadSubcontractorPortalContext() {
      this.syncFromPrimarySession();

      if (!this.effectiveAccessToken) {
        this.clearPortalSubcontractorContext();
        return null;
      }

      try {
        const context = await getSubcontractorPortalContext(this.effectiveAccessToken);
        this.portalSubcontractorContext = context;
        persistJson(PORTAL_SUBCONTRACTOR_CONTEXT_STORAGE_KEY, context);
        return context;
      } catch (error) {
        this.clearPortalSubcontractorContext();
        if (error instanceof AuthApiError && error.statusCode === 401) {
          this.clearSession();
        }
        throw error;
      }
    },
    async logoutSession() {
      try {
        this.syncFromPrimarySession();
        if (this.effectiveAccessToken) {
          await logout(this.effectiveAccessToken);
        }
      } finally {
        this.clearSession();
      }
    },
  },
});

export { resolveTenantScopeIdForRole };
