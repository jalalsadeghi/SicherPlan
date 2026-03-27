import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const source = readFileSync(
  new URL("../../components/planning/PlanningAddressSelect.vue", import.meta.url),
  "utf8",
);

test("address selector uses inline placeholder guidance for empty states", () => {
  assert.match(source, /:placeholder="resolvedPlaceholder"/);
  assert.match(source, /if \(!props\.customerId\) {\s*return props\.customerRequiredText;/);
  assert.match(source, /if \(!props\.loading && !props\.error && !props\.options\.length\) {\s*return props\.emptyText;/);
});

test("address selector no longer renders empty-state helper text below the control", () => {
  assert.doesNotMatch(source, /v-else-if="!customerId" class="field-help"/);
  assert.doesNotMatch(source, /v-else-if="!options.length" class="field-help"/);
});
