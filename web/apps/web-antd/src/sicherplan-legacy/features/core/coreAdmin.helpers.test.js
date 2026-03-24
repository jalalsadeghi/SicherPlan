import assert from "node:assert/strict";
import test from "node:test";

import {
  resolveCoreAdminChromeVisibility,
  resolveCoreAdminScopeState,
  resolveCoreAdminTenantIdToLoad,
} from "./coreAdmin.helpers.js";

test("tenant admin top chrome is fully removed", () => {
  const visibility = resolveCoreAdminChromeVisibility("tenant_admin");

  assert.equal(visibility.showHero, false);
  assert.equal(visibility.showWorkspaceExplainer, false);
  assert.equal(visibility.showTenantScopeCard, false);
});

test("platform admin keeps only the tenant scope card", () => {
  const visibility = resolveCoreAdminChromeVisibility("platform_admin");

  assert.equal(visibility.showHero, false);
  assert.equal(visibility.showWorkspaceExplainer, false);
  assert.equal(visibility.showTenantScopeCard, true);
});

test("tenant admin scope is resolved from the session tenant and ignores mismatching remembered scope", () => {
  const state = resolveCoreAdminScopeState({
    effectiveRole: "tenant_admin",
    tenantScopeInput: "",
    rememberedTenantScopeId: "other-tenant",
    sessionTenantId: "tenant-1",
  });

  assert.equal(state.actorTenantId, "tenant-1");
  assert.equal(state.scopeFieldValue, "tenant-1");
  assert.equal(state.scopeBadgeStatus, "active");
  assert.equal(state.scopeFieldDisabled, true);
  assert.equal(state.canLoadScopedTenant, false);
  assert.equal(state.scopeQueryValue, undefined);
});

test("tenant admin scope is inactive only when no session-backed tenant can be resolved", () => {
  const state = resolveCoreAdminScopeState({
    effectiveRole: "tenant_admin",
    tenantScopeInput: "",
    rememberedTenantScopeId: "",
    sessionTenantId: "",
  });

  assert.equal(state.actorTenantId, null);
  assert.equal(state.scopeBadgeStatus, "inactive");
});

test("platform admin keeps the editable remembered scope behavior", () => {
  const state = resolveCoreAdminScopeState({
    effectiveRole: "platform_admin",
    tenantScopeInput: "tenant-2",
    rememberedTenantScopeId: "tenant-1",
    sessionTenantId: "system",
  });

  assert.equal(state.actorTenantId, null);
  assert.equal(state.scopeFieldValue, "tenant-2");
  assert.equal(state.scopeBadgeStatus, "active");
  assert.equal(state.scopeFieldDisabled, false);
  assert.equal(state.canLoadScopedTenant, true);
  assert.equal(state.scopeQueryValue, "tenant-2");
});

test("tenant admin auto-loads their own tenant context when nothing is selected", () => {
  assert.equal(resolveCoreAdminTenantIdToLoad("", "tenant_admin", "tenant-1"), "tenant-1");
  assert.equal(resolveCoreAdminTenantIdToLoad("tenant-2", "tenant_admin", "tenant-1"), "tenant-2");
});
