import test from "node:test";
import assert from "node:assert/strict";

import {
  buildLifecyclePayload,
  deriveCustomerActionState,
  formatPrimaryContactSummary,
  hasCustomerPermission,
  mapCustomerApiMessage,
} from "./customerAdmin.helpers.js";

test("tenant admin has read and write permissions", () => {
  assert.equal(hasCustomerPermission("tenant_admin", "customers.customer.read"), true);
  assert.equal(hasCustomerPermission("tenant_admin", "customers.customer.write"), true);
  assert.equal(hasCustomerPermission("accounting", "customers.customer.read"), true);
  assert.equal(hasCustomerPermission("dispatcher", "customers.customer.read"), false);
});

test("action state follows lifecycle and role permissions", () => {
  const customer = { status: "inactive", archived_at: null };
  const state = deriveCustomerActionState("tenant_admin", customer);

  assert.equal(state.canCreate, true);
  assert.equal(state.canReactivate, true);
  assert.equal(state.canDeactivate, false);
  assert.equal(deriveCustomerActionState("accounting", customer).canRead, true);
  assert.equal(deriveCustomerActionState("accounting", customer).canCreate, false);
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
  assert.equal(mapCustomerApiMessage("errors.platform.internal"), "customerAdmin.feedback.error");
});
