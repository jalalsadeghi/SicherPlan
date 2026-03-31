import assert from "node:assert/strict";
import test from "node:test";

import {
  buildEmployeeImportTemplateRows,
  deriveEmployeeActionState,
  hasEmployeePermission,
  mapEmployeeApiMessage,
  summarizeCurrentAddress,
  validateEmployeeAddressDraft,
} from "./employeeAdmin.helpers.js";

test("tenant admin gets employee write and private access", () => {
  assert.equal(hasEmployeePermission("tenant_admin", "employees.employee.write"), true);
  assert.equal(hasEmployeePermission("tenant_admin", "employees.private.read"), true);
  assert.equal(hasEmployeePermission("dispatcher", "employees.employee.write"), false);
});

test("action state reflects selected employee and role", () => {
  const selectedEmployee = { status: "active", archived_at: null };
  const adminState = deriveEmployeeActionState("tenant_admin", selectedEmployee);
  const dispatcherState = deriveEmployeeActionState("dispatcher", selectedEmployee);

  assert.equal(adminState.canManageNotes, true);
  assert.equal(adminState.canManageAddresses, true);
  assert.equal(adminState.canManagePhoto, true);
  assert.equal(adminState.canImport, true);
  assert.equal(adminState.canManageAccess, true);
  assert.equal(dispatcherState.canReadPrivate, false);
  assert.equal(dispatcherState.canWrite, false);
  assert.equal(dispatcherState.canExport, true);
});

test("api message keys map to localized employee feedback keys", () => {
  assert.equal(
    mapEmployeeApiMessage("errors.employees.note.reminder_date_required"),
    "employeeAdmin.feedback.reminderDateRequired",
  );
  assert.equal(
    mapEmployeeApiMessage("errors.employees.photo.write_failed"),
    "employeeAdmin.feedback.photoUploadFailed",
  );
  assert.equal(
    mapEmployeeApiMessage("errors.employees.address_history.invalid_window"),
    "employeeAdmin.feedback.addressInvalidWindow",
  );
  assert.equal(
    mapEmployeeApiMessage("errors.employees.access.email_taken"),
    "employeeAdmin.feedback.accessEmailTaken",
  );
  assert.equal(
    mapEmployeeApiMessage("errors.employees.access.already_linked"),
    "employeeAdmin.feedback.accessAlreadyLinked",
  );
});

test("current address summary uses latest active primary address", () => {
  const summary = summarizeCurrentAddress([
    {
      archived_at: null,
      is_primary: true,
      valid_from: "2026-01-01",
      address: { street_line_1: "Alt", postal_code: "11111", city: "Berlin" },
    },
    {
      archived_at: null,
      is_primary: true,
      valid_from: "2026-05-01",
      address: { street_line_1: "Neu", postal_code: "22222", city: "Hamburg" },
    },
  ]);

  assert.equal(summary, "Neu, 22222, Hamburg");
});

test("employee address validation blocks invalid windows and overlap", () => {
  assert.equal(
    validateEmployeeAddressDraft(
      {
        street_line_1: "",
        postal_code: "10115",
        city: "Berlin",
        country_code: "DE",
        address_type: "home",
        valid_from: "2026-01-01",
        valid_to: "",
        is_current: true,
      },
      [],
      "",
    ),
    "employeeAdmin.feedback.addressRequired",
  );

  assert.equal(
    validateEmployeeAddressDraft(
      {
        street_line_1: "Musterstrasse 1",
        postal_code: "10115",
        city: "Berlin",
        country_code: "DE",
        address_type: "home",
        valid_from: "2026-02-01",
        valid_to: "2026-01-31",
        is_current: false,
      },
      [],
      "",
    ),
    "employeeAdmin.feedback.addressInvalidWindow",
  );

  assert.equal(
    validateEmployeeAddressDraft(
      {
        street_line_1: "Musterstrasse 1",
        postal_code: "10115",
        city: "Berlin",
        country_code: "DE",
        address_type: "home",
        valid_from: "2026-03-01",
        valid_to: "",
        is_current: true,
      },
      [{ id: "hist-1", address_type: "home", valid_from: "2026-01-01", valid_to: null, archived_at: null }],
      "",
    ),
    "employeeAdmin.feedback.addressOverlap",
  );
});

test("import template rows use the stable employee operational header order", () => {
  assert.equal(
    buildEmployeeImportTemplateRows(),
    "personnel_no,first_name,last_name,preferred_name,work_email,work_phone,mobile_phone,default_branch_id,default_mandate_id,hire_date,termination_date,status,user_id,notes",
  );
});
