import test from "node:test";
import assert from "node:assert/strict";

import {
  canAccessAppRoute,
  derivePortalCapabilityState,
  derivePortalCollectionState,
  derivePortalCustomerAccessState,
  derivePortalDatasetMessage,
  mapPortalApiMessage,
} from "./customerPortal.helpers.js";

test("guest-allowed portal route remains reachable before login", () => {
  assert.equal(
    canAccessAppRoute({
      allowedRoles: ["customer_user"],
      allowGuest: true,
      role: "tenant_admin",
      isAuthenticated: false,
    }),
    true,
  );
});

test("protected routes require an authenticated matching role", () => {
  assert.equal(
    canAccessAppRoute({
      allowedRoles: ["tenant_admin"],
      allowGuest: false,
      role: "tenant_admin",
      isAuthenticated: true,
    }),
    true,
  );
  assert.equal(
    canAccessAppRoute({
      allowedRoles: ["tenant_admin"],
      allowGuest: false,
      role: "customer_user",
      isAuthenticated: true,
    }),
    false,
  );
});

test("portal access state distinguishes exact customer portal denial reasons", () => {
  assert.equal(
    derivePortalCustomerAccessState({
      isLoading: false,
      hasSession: false,
      hasContext: false,
      lastErrorKey: "",
    }),
    "login",
  );
  assert.equal(
    derivePortalCustomerAccessState({
      isLoading: false,
      hasSession: true,
      hasContext: true,
      lastErrorKey: "",
    }),
    "ready",
  );
  assert.equal(
    derivePortalCustomerAccessState({
      isLoading: false,
      hasSession: true,
      hasContext: false,
      lastErrorKey: "errors.iam.authorization.permission_denied",
    }),
    "missing_permission",
  );
  assert.equal(
    derivePortalCustomerAccessState({
      isLoading: false,
      hasSession: true,
      hasContext: false,
      lastErrorKey: "errors.customers.portal.scope_not_resolved",
    }),
    "missing_scope",
  );
  assert.equal(
    derivePortalCustomerAccessState({
      isLoading: false,
      hasSession: true,
      hasContext: false,
      lastErrorKey: "errors.customers.portal.contact_not_linked",
    }),
    "contact_not_linked",
  );
  assert.equal(
    derivePortalCustomerAccessState({
      isLoading: false,
      hasSession: true,
      hasContext: false,
      lastErrorKey: "errors.customers.portal.contact_inactive",
    }),
    "contact_inactive",
  );
  assert.equal(
    derivePortalCustomerAccessState({
      isLoading: false,
      hasSession: true,
      hasContext: false,
      lastErrorKey: "errors.customers.portal.customer_inactive",
    }),
    "customer_inactive",
  );
});

test("portal api errors are mapped to localized feedback keys", () => {
  assert.equal(
    mapPortalApiMessage("errors.customers.portal.contact_not_linked"),
    "portalCustomer.feedback.contactNotLinked",
  );
  assert.equal(
    mapPortalApiMessage("errors.field.watchbook.portal_write_denied"),
    "portalCustomer.feedback.watchbookWriteDenied",
  );
  assert.equal(
    mapPortalApiMessage("errors.finance.invoice.not_found"),
    "portalCustomer.feedback.financeDocumentDenied",
  );
  assert.equal(mapPortalApiMessage("errors.platform.internal"), "portalCustomer.feedback.error");
});

test("portal collection state distinguishes pending, empty, and ready data", () => {
  assert.equal(derivePortalCollectionState(null), "loading");
  assert.equal(
    derivePortalCollectionState({
      items: [],
      source: { availability_status: "pending_source_module" },
    }),
    "pending",
  );
  assert.equal(
    derivePortalCollectionState({
      items: [],
      source: { availability_status: "ready" },
    }),
    "empty",
  );
  assert.equal(
    derivePortalCollectionState({
      items: [{ id: "row-1" }],
      source: { availability_status: "ready" },
    }),
    "ready",
  );
});

test("portal capability state reflects backend capability metadata", () => {
  assert.equal(
    derivePortalCapabilityState({
      availability_status: "pending_source_module",
      interaction_mode: "read_only",
      can_download_documents: false,
      can_write: false,
    }),
    "pending_integration",
  );
  assert.equal(
    derivePortalCapabilityState({
      availability_status: "ready",
      interaction_mode: "write_optional",
      can_download_documents: false,
      can_view: true,
      can_write: false,
    }),
    "available",
  );
  assert.equal(
    derivePortalCapabilityState({
      availability_status: "ready",
      interaction_mode: "write_optional",
      can_download_documents: false,
      can_view: false,
      can_write: false,
    }),
    "not_enabled",
  );
  assert.equal(
    derivePortalCapabilityState({
      availability_status: "ready",
      interaction_mode: "write_optional",
      can_download_documents: false,
      can_view: false,
      can_write: true,
    }),
    "enabled",
  );
  assert.equal(
    derivePortalCapabilityState({
      availability_status: "ready",
      interaction_mode: "download",
      can_download_documents: true,
      can_write: false,
    }),
    "available",
  );
  assert.equal(
    derivePortalCapabilityState({
      availability_status: "ready",
      interaction_mode: "read_only",
      can_download_documents: false,
      can_write: false,
    }),
    "read_only",
  );
});

test("portal dataset message distinguishes pending integrations from empty released datasets", () => {
  assert.equal(
    derivePortalDatasetMessage(
      {
        items: [],
        source: { availability_status: "pending_source_module", message_key: "portal.pending" },
      },
      "portal.empty",
    ),
    "portal.pending",
  );
  assert.equal(
    derivePortalDatasetMessage(
      {
        items: [],
        source: { availability_status: "ready", message_key: "portal.source" },
      },
      "portal.empty",
    ),
    "portal.empty",
  );
  assert.equal(
    derivePortalDatasetMessage(
      {
        items: [{ id: "row-1" }],
        source: { availability_status: "ready", message_key: "portal.source" },
      },
      "portal.empty",
    ),
    null,
  );
});
