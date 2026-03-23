import test from "node:test";
import assert from "node:assert/strict";

import {
  canAccessAppRoute,
  derivePortalCollectionState,
  derivePortalCustomerAccessState,
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

test("portal access state distinguishes login, ready, deactivated, and empty states", () => {
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
      lastErrorKey: "errors.customers.portal.customer_inactive",
    }),
    "deactivated",
  );
  assert.equal(
    derivePortalCustomerAccessState({
      isLoading: false,
      hasSession: true,
      hasContext: false,
      lastErrorKey: "errors.customers.portal.scope_not_resolved",
    }),
    "empty",
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
