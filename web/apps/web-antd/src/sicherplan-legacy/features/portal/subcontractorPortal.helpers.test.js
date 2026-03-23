import test from "node:test";
import assert from "node:assert/strict";

import {
  derivePortalSubcontractorAccessState,
  mapSubcontractorPortalApiMessage,
} from "./subcontractorPortal.helpers.js";

test("subcontractor portal access state distinguishes login, ready, deactivated, and empty states", () => {
  assert.equal(
    derivePortalSubcontractorAccessState({
      isLoading: false,
      hasSession: false,
      hasContext: false,
      lastErrorKey: "",
    }),
    "login",
  );
  assert.equal(
    derivePortalSubcontractorAccessState({
      isLoading: false,
      hasSession: true,
      hasContext: true,
      lastErrorKey: "",
    }),
    "ready",
  );
  assert.equal(
    derivePortalSubcontractorAccessState({
      isLoading: false,
      hasSession: true,
      hasContext: false,
      lastErrorKey: "errors.subcontractors.portal.company_inactive",
    }),
    "deactivated",
  );
  assert.equal(
    derivePortalSubcontractorAccessState({
      isLoading: false,
      hasSession: true,
      hasContext: false,
      lastErrorKey: "errors.subcontractors.portal.scope_not_resolved",
    }),
    "empty",
  );
});

test("subcontractor portal api errors map to localized feedback keys", () => {
  assert.equal(
    mapSubcontractorPortalApiMessage("errors.subcontractors.portal.contact_not_linked"),
    "portalSubcontractor.feedback.contactNotLinked",
  );
  assert.equal(
    mapSubcontractorPortalApiMessage("errors.subcontractors.portal_allocation.blocked_by_validation"),
    "portalSubcontractor.feedback.allocationBlocked",
  );
  assert.equal(
    mapSubcontractorPortalApiMessage("errors.field.watchbook.closed"),
    "portalSubcontractor.feedback.watchbookClosed",
  );
  assert.equal(
    mapSubcontractorPortalApiMessage("errors.subcontractors.portal.invoice_check.not_found"),
    "portalSubcontractor.feedback.invoiceCheckNotFound",
  );
  assert.equal(
    mapSubcontractorPortalApiMessage("portalSubcontractor.feedback.allocationSubmitted"),
    "portalSubcontractor.feedback.allocationSubmitted",
  );
  assert.equal(
    mapSubcontractorPortalApiMessage("errors.platform.internal"),
    "portalSubcontractor.feedback.error",
  );
});
