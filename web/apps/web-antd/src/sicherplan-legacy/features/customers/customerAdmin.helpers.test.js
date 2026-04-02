import test from "node:test";
import assert from "node:assert/strict";

import {
  buildCustomerCommercialLocation,
  CUSTOMER_COMMERCIAL_TAB_ORDER,
  CUSTOMER_PRICING_RULES_TAB_ORDER,
  buildCustomerDetailTabs,
  buildCustomerPricingRulesTabs,
  buildLifecyclePayload,
  buildCustomerDraftPayload,
  buildCustomerReferenceMaps,
  deriveCustomerActionState,
  filterCustomerMandatesByBranch,
  formatPrimaryContactSummary,
  formatCustomerReferenceDisplayLabel,
  formatCustomerReferenceOptionLabel,
  hasCustomerPermission,
  mapCustomerApiMessage,
  normalizeCustomerCommercialTab,
  normalizeCustomerDetailTab,
  normalizeCustomerPricingRulesTab,
  resolveCustomerSelectedRateCardId,
  resolveCustomerAdminRouteContext,
  resolveCustomerAdminSectionVisibility,
  resolveCustomerAdminSessionScope,
  resolveCustomerCancelSelection,
} from "./customerAdmin.helpers.js";

test("tenant admin has read and write permissions", () => {
  assert.equal(hasCustomerPermission("tenant_admin", "customers.customer.read"), true);
  assert.equal(hasCustomerPermission("tenant_admin", "customers.customer.write"), true);
  assert.equal(hasCustomerPermission("tenant_admin", "customers.portal_access.write"), true);
  assert.equal(hasCustomerPermission("accounting", "customers.customer.read"), true);
  assert.equal(hasCustomerPermission("dispatcher", "customers.customer.read"), true);
  assert.equal(hasCustomerPermission("controller_qm", "customers.customer.read"), true);
});

test("tenant admin embedded customers view hides the governance hero", () => {
  assert.deepEqual(
    resolveCustomerAdminSectionVisibility({ effectiveRole: "tenant_admin", embedded: true }),
    { showGovernanceHero: false },
  );
  assert.deepEqual(
    resolveCustomerAdminSectionVisibility({ effectiveRole: "platform_admin", embedded: true }),
    { showGovernanceHero: true },
  );
});

test("tenant admin uses session-backed scope and token for customers page", () => {
  assert.deepEqual(
    resolveCustomerAdminSessionScope({
      effectiveRole: "tenant_admin",
      effectiveTenantScopeId: "tenant-1",
      effectiveAccessToken: "token-1",
      storedAccessToken: "legacy-token",
    }),
    {
      tenantScopeId: "tenant-1",
      accessToken: "token-1",
    },
  );
});

test("action state follows lifecycle and role permissions", () => {
  const customer = { status: "inactive", archived_at: null };
  const state = deriveCustomerActionState("tenant_admin", customer);

  assert.equal(state.canCreate, true);
  assert.equal(state.canReactivate, true);
  assert.equal(state.canDeactivate, false);
  assert.equal(deriveCustomerActionState("accounting", customer).canRead, true);
  assert.equal(deriveCustomerActionState("accounting", customer).canCreate, false);
  assert.equal(deriveCustomerActionState("dispatcher", customer).canRead, true);
  assert.equal(deriveCustomerActionState("dispatcher", customer).canCreate, false);
});

test("lifecycle payload archives with version and timestamp", () => {
  const payload = buildLifecyclePayload({ version_no: 4 }, "archived");
  assert.equal(payload.version_no, 4);
  assert.equal(payload.status, "archived");
  assert.ok(payload.archived_at);
});

test("primary contact summary prefers primary contact name and email", () => {
  const summary = formatPrimaryContactSummary({
    contacts: [
      { full_name: "Other", email: null, is_primary_contact: false },
      { full_name: "Alex Kunde", email: "alex@example.invalid", is_primary_contact: true },
    ],
  });

  assert.equal(summary, "Alex Kunde · alex@example.invalid");
});

test("api message keys are mapped to customer-admin feedback keys", () => {
  assert.equal(
    mapCustomerApiMessage("errors.customers.customer.duplicate_number"),
    "customerAdmin.feedback.duplicateNumber",
  );
  assert.equal(
    mapCustomerApiMessage("errors.customers.contact.invalid_user_id_format"),
    "customerAdmin.feedback.invalidPortalUserFormat",
  );
  assert.equal(
    mapCustomerApiMessage("errors.customers.portal_access.contact_already_linked"),
    "customerAdmin.feedback.portalAccessAlreadyLinked",
  );
  assert.equal(mapCustomerApiMessage("errors.platform.internal"), "customerAdmin.feedback.error");
});

test("customer reference option labels use human-readable names only", () => {
  assert.equal(formatCustomerReferenceOptionLabel({ code: "A", label: "A-Kunde" }), "A-Kunde");
  assert.equal(formatCustomerReferenceOptionLabel({ code: "BER", name: "Berlin" }), "Berlin");
});

test("customer reference display labels can still preserve code plus business label", () => {
  assert.equal(formatCustomerReferenceDisplayLabel({ code: "A", label: "A-Kunde" }), "A - A-Kunde");
  assert.equal(formatCustomerReferenceDisplayLabel({ code: "BER", name: "Berlin" }), "BER - Berlin");
});

test("customer payload keeps lifecycle separate from customer-status metadata", () => {
  const payload = buildCustomerDraftPayload(
    {
      tenant_id: "tenant-1",
      customer_number: " K-1001 ",
      name: " Nord Security ",
      status: "inactive",
      legal_name: "",
      external_ref: "",
      legal_form_lookup_id: "lookup-legal",
      classification_lookup_id: "lookup-category",
      ranking_lookup_id: "lookup-ranking",
      customer_status_lookup_id: "lookup-status",
      default_branch_id: "branch-1",
      default_mandate_id: "mandate-1",
      notes: "",
    },
    { allowedBranchIds: ["branch-1"], allowedMandateIds: ["mandate-1"] },
  );

  assert.equal(payload.status, "inactive");
  assert.equal(payload.customer_status_lookup_id, "lookup-status");
  assert.equal(payload.default_branch_id, "branch-1");
  assert.equal(payload.default_mandate_id, "mandate-1");
});

test("customer payload drops stale branch and mandate labels", () => {
  const payload = buildCustomerDraftPayload(
    {
      tenant_id: "tenant-1",
      customer_number: "K-1002",
      name: "Atlas",
      status: "active",
      legal_name: "",
      external_ref: "",
      legal_form_lookup_id: "",
      classification_lookup_id: "",
      ranking_lookup_id: "",
      customer_status_lookup_id: "",
      default_branch_id: "BER - Berlin",
      default_mandate_id: "M-1 - Nord",
      notes: "",
    },
    { allowedBranchIds: ["branch-1"], allowedMandateIds: ["mandate-1"] },
  );

  assert.equal(payload.default_branch_id, null);
  assert.equal(payload.default_mandate_id, null);
});

test("mandates are filtered by selected branch", () => {
  const mandates = [
    { id: "m-1", branch_id: "b-1", code: "M-1", name: "North" },
    { id: "m-2", branch_id: "b-2", code: "M-2", name: "South" },
  ];

  assert.deepEqual(filterCustomerMandatesByBranch(mandates, "b-1").map((item) => item.id), ["m-1"]);
  assert.deepEqual(filterCustomerMandatesByBranch(mandates, "").map((item) => item.id), ["m-1", "m-2"]);
});

test("cancel exits create mode and restores previous customer context", () => {
  assert.deepEqual(resolveCustomerCancelSelection({ id: "customer-1", name: "Nord" }), {
    isCreatingCustomer: false,
    selectedCustomerId: "customer-1",
    selectedCustomer: { id: "customer-1", name: "Nord" },
  });
  assert.deepEqual(resolveCustomerCancelSelection(null), {
    isCreatingCustomer: false,
    selectedCustomerId: "",
    selectedCustomer: null,
  });
});

test("reference maps resolve human-readable summary labels", () => {
  const maps = buildCustomerReferenceMaps({
    classifications: [{ id: "lookup-category", code: "standard", label: "Standardkunde" }],
    rankings: [{ id: "lookup-ranking", code: "a", label: "A-Kunde" }],
    customer_statuses: [{ id: "lookup-status", code: "qualified", label: "Qualifiziert" }],
    branches: [{ id: "branch-1", code: "BER", name: "Berlin" }],
    mandates: [{ id: "mandate-1", branch_id: "branch-1", code: "M-1", name: "Nord" }],
  });

  assert.equal(maps.classifications.get("lookup-category"), "standard - Standardkunde");
  assert.equal(maps.rankings.get("lookup-ranking"), "a - A-Kunde");
  assert.equal(maps.customerStatuses.get("lookup-status"), "qualified - Qualifiziert");
  assert.equal(maps.branches.get("branch-1"), "BER - Berlin");
  assert.equal(maps.mandates.get("mandate-1"), "M-1 - Nord");
});

test("customer detail tabs default to overview-first and hide commercial without permission", () => {
  assert.deepEqual(
    buildCustomerDetailTabs({
      canReadCommercial: false,
      hasSelectedCustomer: true,
      isCreatingCustomer: false,
    }),
    ["overview", "contacts", "addresses", "portal", "history", "employee_blocks"],
  );
  assert.deepEqual(
    buildCustomerDetailTabs({
      canReadCommercial: true,
      hasSelectedCustomer: true,
      isCreatingCustomer: false,
    }),
    ["overview", "contacts", "addresses", "commercial", "portal", "history", "employee_blocks"],
  );
});

test("customer detail tab state falls back to overview and create mode stays on overview only", () => {
  assert.equal(
    normalizeCustomerDetailTab("history", {
      canReadCommercial: true,
      hasSelectedCustomer: false,
      isCreatingCustomer: false,
    }),
    "",
  );
  assert.equal(
    normalizeCustomerDetailTab("history", {
      canReadCommercial: true,
      hasSelectedCustomer: true,
      isCreatingCustomer: true,
    }),
    "overview",
  );
  assert.equal(
    normalizeCustomerDetailTab("commercial", {
      canReadCommercial: false,
      hasSelectedCustomer: true,
      isCreatingCustomer: false,
    }),
    "overview",
  );
});

test("commercial subtab state falls back to billing profile", () => {
  assert.deepEqual(CUSTOMER_COMMERCIAL_TAB_ORDER, [
    "billing_profile",
    "invoice_parties",
    "pricing_rules",
  ]);
  assert.equal(normalizeCustomerCommercialTab("pricing_rules"), "pricing_rules");
  assert.equal(normalizeCustomerCommercialTab("unknown"), "billing_profile");
});

test("pricing-rules subtab state and selected rate card fall back safely", () => {
  assert.deepEqual(CUSTOMER_PRICING_RULES_TAB_ORDER, [
    "rate_cards",
    "rate_lines",
    "surcharges",
  ]);
  assert.deepEqual(buildCustomerPricingRulesTabs({ hasRateCards: false }), ["rate_cards"]);
  assert.deepEqual(buildCustomerPricingRulesTabs({ hasRateCards: true }), [
    "rate_cards",
    "rate_lines",
    "surcharges",
  ]);
  assert.equal(normalizeCustomerPricingRulesTab("surcharges", { hasRateCards: true }), "surcharges");
  assert.equal(normalizeCustomerPricingRulesTab("rate_lines", { hasRateCards: false }), "rate_cards");
  assert.equal(
    resolveCustomerSelectedRateCardId("rate-card-2", [{ id: "rate-card-1" }, { id: "rate-card-2" }]),
    "rate-card-2",
  );
  assert.equal(
    resolveCustomerSelectedRateCardId("missing-rate-card", [{ id: "rate-card-1" }, { id: "rate-card-2" }]),
    "rate-card-1",
  );
  assert.equal(resolveCustomerSelectedRateCardId("missing-rate-card", []), "");
});

test("customer admin route context extracts commercial deep-link state", () => {
  assert.deepEqual(
    resolveCustomerAdminRouteContext({ customer_id: "customer-1", tab: "commercial" }),
    { customerId: "customer-1", detailTab: "commercial" },
  );
  assert.deepEqual(
    resolveCustomerAdminRouteContext({ customer_id: ["customer-1"], tab: null }),
    { customerId: "", detailTab: "" },
  );
  assert.deepEqual(
    buildCustomerCommercialLocation("customer-1"),
    { path: "/admin/customers", query: { tab: "commercial", customer_id: "customer-1" } },
  );
});
