import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import {
  buildSubcontractorWorkerImportTemplateRows,
  buildSubcontractorLifecyclePayload,
  deriveSubcontractorActionState,
  deriveWorkerIndicators,
  filterWorkersByQuickState,
  hasPortalEnabledContact,
  hasSubcontractorPermission,
  mapSubcontractorImportRowMessage,
  mapSubcontractorApiMessage,
  summarizePrimaryContact,
  summarizeScopeRows,
} from "./subcontractorAdmin.helpers.js";

const THIS_DIR = path.dirname(fileURLToPath(import.meta.url));

test("tenant admin gets subcontractor write and finance access", () => {
  assert.equal(hasSubcontractorPermission("tenant_admin", "subcontractors.company.write"), true);
  assert.equal(hasSubcontractorPermission("accounting", "subcontractors.finance.read"), true);
  assert.equal(hasSubcontractorPermission("dispatcher", "subcontractors.finance.write"), false);
});

test("action state reflects selected subcontractor and role", () => {
  const selected = { status: "active", archived_at: null };
  const adminState = deriveSubcontractorActionState("tenant_admin", selected);
  const accountingState = deriveSubcontractorActionState("accounting", selected);

  assert.equal(adminState.canManageContacts, true);
  assert.equal(adminState.canManageScopes, true);
  assert.equal(adminState.canManageFinance, true);
  assert.equal(adminState.canManageHistory, true);
  assert.equal(adminState.canManageWorkforce, true);
  assert.equal(adminState.canImportWorkforce, true);
  assert.equal(adminState.canExportWorkforce, true);
  assert.equal(accountingState.canReadFinance, true);
  assert.equal(accountingState.canManageFinance, false);
});

test("lifecycle payload carries only optimistic-lock version", () => {
  const subcontractor = { version_no: 3 };
  const payload = buildSubcontractorLifecyclePayload(subcontractor);

  assert.deepEqual(payload, { version_no: 3 });
});

test("contact and scope summaries use stable derived display values", () => {
  assert.equal(
    summarizePrimaryContact([{ full_name: "Erika Partner", email: "erika@example.com", is_primary_contact: true }]),
    "Erika Partner · erika@example.com",
  );
  assert.equal(
    summarizeScopeRows([
      { branch_id: "branch-1", mandate_id: "mandate-1", archived_at: null },
      { branch_id: "branch-2", mandate_id: null, archived_at: null },
    ]),
    "branch-1 / mandate-1, branch-2",
  );
  assert.equal(hasPortalEnabledContact([{ portal_enabled: false, archived_at: null }, { portal_enabled: true, archived_at: null }]), true);
});

test("api message keys map to localized subcontractor feedback keys", () => {
  assert.equal(
    mapSubcontractorApiMessage("errors.subcontractors.contact.primary_conflict"),
    "sicherplan.subcontractors.feedback.primaryConflict",
  );
  assert.equal(
    mapSubcontractorApiMessage("errors.subcontractors.scope.overlap"),
    "sicherplan.subcontractors.feedback.scopeOverlap",
  );
  assert.equal(
    mapSubcontractorApiMessage("errors.subcontractors.history_entry.invalid_type"),
    "sicherplan.subcontractors.feedback.historyTypeInvalid",
  );
  assert.equal(
    mapSubcontractorApiMessage("errors.subcontractors.authorization.portal_forbidden"),
    "sicherplan.subcontractors.feedback.permissionDenied",
  );
  assert.equal(
    mapSubcontractorApiMessage("errors.subcontractors.worker_import.invalid_headers"),
    "sicherplan.subcontractors.feedback.workerImportInvalidHeaders",
  );
  assert.equal(
    mapSubcontractorApiMessage("errors.subcontractors.worker_credential.duplicate_no"),
    "sicherplan.subcontractors.feedback.workerCredentialDuplicateNo",
  );
});

test("worker helper utilities expose import template, indicators, and quick filters", () => {
  assert.match(buildSubcontractorWorkerImportTemplateRows(), /^worker_no,first_name,last_name,/);
  const worker = {
    qualifications: [
      { archived_at: null, status: "active", valid_until: "2024-01-10" },
      { archived_at: null, status: "active", valid_until: null },
    ],
    credentials: [{ archived_at: null, status: "active" }],
  };
  const indicators = deriveWorkerIndicators(worker, new Date("2025-01-15T12:00:00Z"));
  assert.equal(indicators.qualificationCount, 2);
  assert.equal(indicators.credentialCount, 1);
  assert.equal(indicators.expiredQualificationCount, 1);
  assert.equal(filterWorkersByQuickState([worker], "expired_qualification", new Date("2025-01-15T12:00:00Z")).length, 1);
  assert.equal(mapSubcontractorImportRowMessage("created_worker"), "sicherplan.subcontractors.workforce.import.row.createdWorker");
});

test("de and en locale files expose subcontractor admin route and page keys", () => {
  const de = JSON.parse(
    readFileSync(path.resolve(THIS_DIR, "../../../locales/langs/de-DE/sicherplan.json"), "utf8"),
  );
  const en = JSON.parse(
    readFileSync(path.resolve(THIS_DIR, "../../../locales/langs/en-US/sicherplan.json"), "utf8"),
  );

  assert.equal(typeof de.admin.subcontractors, "string");
  assert.equal(typeof en.admin.subcontractors, "string");
  assert.equal(typeof de.subcontractors.title, "string");
  assert.equal(typeof en.subcontractors.title, "string");
  assert.equal(typeof de.subcontractors.feedback.portalUserRequired, "string");
  assert.equal(typeof en.subcontractors.feedback.portalUserRequired, "string");
  assert.equal(typeof de.subcontractors.history.title, "string");
  assert.equal(typeof en.subcontractors.history.title, "string");
  assert.equal(typeof de.subcontractors.detail.workspaceLead, "string");
  assert.equal(typeof en.subcontractors.detail.workspaceLead, "string");
  assert.equal(typeof de.subcontractors.tabs.scopeRelease, "string");
  assert.equal(typeof en.subcontractors.tabs.scopeRelease, "string");
  assert.equal(typeof de.subcontractors.filters.allBranches, "string");
  assert.equal(typeof en.subcontractors.filters.allBranches, "string");
  assert.equal(typeof de.subcontractors.fields.legalFormPlaceholder, "string");
  assert.equal(typeof en.subcontractors.fields.legalFormPlaceholder, "string");
  assert.equal(typeof de.subcontractors.fields.legalFormUnavailablePlaceholder, "string");
  assert.equal(typeof en.subcontractors.fields.legalFormUnavailablePlaceholder, "string");
  assert.equal(typeof de.subcontractors.fields.legalFormHelpUnavailable, "string");
  assert.equal(typeof en.subcontractors.fields.legalFormHelpUnavailable, "string");
  assert.equal(typeof de.subcontractors.fields.legalFormHelpLegacy, "string");
  assert.equal(typeof en.subcontractors.fields.legalFormHelpLegacy, "string");
  assert.equal(typeof de.subcontractors.fields.lifecycleStatus, "string");
  assert.equal(typeof en.subcontractors.fields.lifecycleStatus, "string");
  assert.equal(typeof de.subcontractors.fields.addressPlaceholder, "string");
  assert.equal(typeof en.subcontractors.fields.addressPlaceholder, "string");
  assert.equal(typeof de.subcontractors.fields.addressAction, "string");
  assert.equal(typeof en.subcontractors.fields.addressAction, "string");
  assert.equal(typeof de.subcontractors.fields.branchUnavailablePlaceholder, "string");
  assert.equal(typeof en.subcontractors.fields.branchUnavailablePlaceholder, "string");
  assert.equal(typeof de.subcontractors.fields.branchLoadingPlaceholder, "string");
  assert.equal(typeof en.subcontractors.fields.branchLoadingPlaceholder, "string");
  assert.equal(typeof de.subcontractors.fields.branchEmptyPlaceholder, "string");
  assert.equal(typeof en.subcontractors.fields.branchEmptyPlaceholder, "string");
  assert.equal(typeof de.subcontractors.fields.mandateUnavailablePlaceholder, "string");
  assert.equal(typeof en.subcontractors.fields.mandateUnavailablePlaceholder, "string");
  assert.equal(typeof de.subcontractors.fields.mandateLoadingPlaceholder, "string");
  assert.equal(typeof en.subcontractors.fields.mandateLoadingPlaceholder, "string");
  assert.equal(typeof de.subcontractors.fields.mandateEmptyPlaceholder, "string");
  assert.equal(typeof en.subcontractors.fields.mandateEmptyPlaceholder, "string");
  assert.equal(typeof de.subcontractors.fields.mandateEmptyForBranchPlaceholder, "string");
  assert.equal(typeof en.subcontractors.fields.mandateEmptyForBranchPlaceholder, "string");
  assert.equal(typeof de.subcontractors.actions.pickLocationOnMap, "string");
  assert.equal(typeof en.subcontractors.actions.pickLocationOnMap, "string");
  assert.equal(typeof de.subcontractors.mapPicker.title, "string");
  assert.equal(typeof en.subcontractors.mapPicker.title, "string");
  assert.equal(typeof de.subcontractors.fields.contactUserHelp, "string");
  assert.equal(typeof en.subcontractors.fields.contactUserHelp, "string");
  assert.equal(typeof de.subcontractors.addressModal.title, "string");
  assert.equal(typeof en.subcontractors.addressModal.title, "string");
  assert.equal(typeof de.subcontractors.workforce.fields.qualificationTypePlaceholder, "string");
  assert.equal(typeof en.subcontractors.workforce.fields.qualificationTypePlaceholder, "string");
  assert.equal(typeof de.subcontractors.history.types.lifecycle_event, "string");
  assert.equal(typeof en.subcontractors.history.types.lifecycle_event, "string");
  assert.equal(typeof de.subcontractors.workforce.title, "string");
  assert.equal(typeof en.subcontractors.workforce.title, "string");
  assert.equal(typeof de.subcontractors.workforce.import.title, "string");
  assert.equal(typeof en.subcontractors.workforce.import.title, "string");
});
