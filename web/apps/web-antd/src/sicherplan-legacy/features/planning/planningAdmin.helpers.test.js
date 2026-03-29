import test from "node:test";
import assert from "node:assert/strict";

import {
  buildPlanningImportTemplate,
  derivePlanningActionState,
  formatPlanningAddressOption,
  filterPlanningCustomerOptions,
  formatPlanningCustomerOption,
  mapPlanningApiMessage,
  parseOptionalCoordinate,
  resolvePlanningRouteContext,
  resolveInitialMapCenter,
} from "./planningAdmin.helpers.js";

test("derivePlanningActionState grants dispatcher planning write access", () => {
  const state = derivePlanningActionState("dispatcher", "site", { id: "1" });
  assert.equal(state.canRead, true);
  assert.equal(state.canWrite, true);
  assert.equal(state.canManageChildren, false);
});

test("derivePlanningActionState enables child editing for fair and route records", () => {
  assert.equal(derivePlanningActionState("tenant_admin", "trade_fair", { id: "1" }).canManageChildren, true);
  assert.equal(derivePlanningActionState("tenant_admin", "patrol_route", { id: "1" }).canManageChildren, true);
});

test("buildPlanningImportTemplate returns stable CSV headers", () => {
  assert.equal(
    buildPlanningImportTemplate("site"),
    "customer_id,site_no,name,address_id,timezone,latitude,longitude,watchbook_enabled,notes,status",
  );
});

test("mapPlanningApiMessage maps import and duplicate errors", () => {
  assert.equal(mapPlanningApiMessage("errors.planning.import.invalid_headers"), "invalidImportHeaders");
  assert.equal(mapPlanningApiMessage("errors.planning.patrol_checkpoint.duplicate_sequence"), "duplicateChild");
});

test("formatPlanningCustomerOption renders customer number and name together", () => {
  assert.equal(
    formatPlanningCustomerOption({ customer_number: "CUS-200", name: "Messe Nord" }),
    "CUS-200 — Messe Nord",
  );
});

test("filterPlanningCustomerOptions matches across the combined customer label", () => {
  const customers = [
    { customer_number: "CUS-100", name: "Alpha Security" },
    { customer_number: "CUS-200", name: "Messe Nord" },
  ];

  assert.deepEqual(filterPlanningCustomerOptions(customers, "nord"), [customers[1]]);
  assert.deepEqual(filterPlanningCustomerOptions(customers, "cus-100"), [customers[0]]);
});

test("formatPlanningAddressOption renders a readable postal label", () => {
  assert.equal(
    formatPlanningAddressOption({
      address_id: "address-1",
      address: {
        street_line_1: "Musterstrasse 12",
        postal_code: "50667",
        city: "Koeln",
        country_code: "DE",
      },
    }),
    "Musterstrasse 12 · 50667 Koeln · DE",
  );
});

test("parseOptionalCoordinate keeps blank values unset instead of coercing to zero", () => {
  assert.equal(parseOptionalCoordinate(""), null);
  assert.equal(parseOptionalCoordinate("   "), null);
  assert.equal(parseOptionalCoordinate(undefined), null);
  assert.equal(parseOptionalCoordinate(null), null);
  assert.equal(parseOptionalCoordinate("0"), 0);
});

test("resolveInitialMapCenter ignores blank form coordinates and falls back truthfully", () => {
  const center = resolveInitialMapCenter({
    currentLatitude: "",
    currentLongitude: "",
    customerCoordinates: null,
    customerGeocode: null,
    fallback: { lat: 51.662973, lng: 8.174013 },
  });

  assert.deepEqual(center, {
    lat: 51.662973,
    lng: 8.174013,
    source: "fallback",
  });
});

test("resolveInitialMapCenter uses existing form coordinates only when both values are present", () => {
  const center = resolveInitialMapCenter({
    currentLatitude: "51.5",
    currentLongitude: "8.1",
    customerCoordinates: { lat: 52.1, lng: 13.1 },
    customerGeocode: { lat: 53.1, lng: 9.1 },
    fallback: { lat: 51.662973, lng: 8.174013 },
  });

  assert.deepEqual(center, {
    lat: 51.5,
    lng: 8.1,
    source: "existing-record",
  });
});

test("resolvePlanningRouteContext keeps only supported entity and customer query context", () => {
  assert.deepEqual(
    resolvePlanningRouteContext({ entity: "requirement_type", customer_id: "customer-1" }),
    { entity: "requirement_type", customerId: "customer-1" },
  );
  assert.deepEqual(
    resolvePlanningRouteContext({ entity: "unknown", customer_id: 7 }),
    { entity: null, customerId: "" },
  );
});
