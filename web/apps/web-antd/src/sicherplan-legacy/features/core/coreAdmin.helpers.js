export function resolveCoreAdminScopeState({
  effectiveRole,
  tenantScopeInput,
  rememberedTenantScopeId,
  sessionTenantId,
}) {
  const normalizedInput = typeof tenantScopeInput === "string" ? tenantScopeInput.trim() : "";
  const normalizedRemembered = typeof rememberedTenantScopeId === "string" ? rememberedTenantScopeId.trim() : "";
  const normalizedSession = typeof sessionTenantId === "string" ? sessionTenantId.trim() : "";

  if (effectiveRole === "tenant_admin") {
    const actorTenantId = normalizedSession || normalizedRemembered || "";

    return {
      actorTenantId: actorTenantId || null,
      scopeFieldValue: actorTenantId,
      scopeBadgeStatus: actorTenantId ? "active" : "inactive",
      scopeQueryValue: undefined,
      scopeFieldDisabled: true,
      canLoadScopedTenant: false,
    };
  }

  const effectiveScope = normalizedInput || normalizedRemembered;

  return {
    actorTenantId: null,
    scopeFieldValue: effectiveScope,
    scopeBadgeStatus: effectiveScope ? "active" : "inactive",
    scopeQueryValue: effectiveScope || undefined,
    scopeFieldDisabled: false,
    canLoadScopedTenant: true,
  };
}

export function resolveCoreAdminChromeVisibility(effectiveRole) {
  const isPlatformAdmin = effectiveRole === "platform_admin";

  return {
    showHero: false,
    showWorkspaceExplainer: false,
    showTenantScopeCard: isPlatformAdmin,
  };
}

export function resolveCoreAdminTenantIdToLoad(selectedTenantId, effectiveRole, actorTenantId) {
  if (selectedTenantId) {
    return selectedTenantId;
  }

  if (effectiveRole === "tenant_admin") {
    return actorTenantId ?? "";
  }

  return "";
}
