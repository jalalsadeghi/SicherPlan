import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";

const source = fs.readFileSync(
  path.resolve("web/apps/web-antd/src/components/sicherplan/local-loading-indicator.vue"),
  "utf8",
);

test("local loading indicator uses accessible non-overlay calendar-style markup", () => {
  assert.match(source, /role="status"/);
  assert.match(source, /aria-live="polite"/);
  assert.match(source, /sp-customer-plan-wizard-step__local-loading/);
  assert.match(source, /sp-local-loading-indicator__dot/);
  assert.match(source, /animation: sp-local-loading-pulse/);
  assert.doesNotMatch(source, /position:\s*fixed/);
});
