import assert from "node:assert/strict";
import test from "node:test";

import {
  buildEmployeeImportTemplateRows,
  buildEmployeeAbsencePayload,
  buildEmployeeAvailabilityPayload,
  buildEmployeeCredentialPayload,
  buildEmployeePrivateProfilePayload,
  buildEmployeeQualificationPayload,
  buildWeekdayMask,
  deriveEmployeeActionState,
  hasEmployeePermission,
  mapEmployeeApiMessage,
  parseWeekdayMask,
  summarizeCurrentAddress,
  toLocalDateTimeInput,
  validateEmployeeAbsenceDraft,
  validateEmployeeAddressDraft,
  validateEmployeeAvailabilityDraft,
  validateEmployeeCredentialDraft,
  validateEmployeeQualificationDraft,
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
  assert.equal(adminState.canManagePrivateProfile, true);
  assert.equal(adminState.canManageAddresses, true);
  assert.equal(adminState.canManageQualifications, true);
  assert.equal(adminState.canManageCredentials, true);
  assert.equal(adminState.canManageAvailability, true);
  assert.equal(adminState.canManageAbsences, true);
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
  assert.equal(
    mapEmployeeApiMessage("errors.employees.credential.duplicate_no"),
    "employeeAdmin.feedback.credentialDuplicateNo",
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

test("private profile payload normalizes date and country code", () => {
  assert.deepEqual(
    buildEmployeePrivateProfilePayload(
      {
        birth_date: "2026-03-01",
        place_of_birth: " Berlin ",
        nationality_country_code: "de",
      },
      { tenantId: "tenant-1", employeeId: "employee-1" },
    ),
    {
      tenant_id: "tenant-1",
      employee_id: "employee-1",
      birth_date: "2026-03-01",
      place_of_birth: "Berlin",
      nationality_country_code: "DE",
    },
  );
});

test("qualification payload normalizes optional fields and validates target/window", () => {
  assert.deepEqual(
    buildEmployeeQualificationPayload(
      {
        record_kind: " qualification ",
        qualification_type_id: "qual-1",
        certificate_no: " CERT-9 ",
        issued_at: "2026-01-10",
        valid_until: "2026-12-31",
        issuing_authority: " HQ ",
        granted_internally: true,
        notes: " note ",
      },
      { tenantId: "tenant-1", employeeId: "employee-1" },
    ),
    {
      tenant_id: "tenant-1",
      employee_id: "employee-1",
      record_kind: "qualification",
      function_type_id: null,
      qualification_type_id: "qual-1",
      certificate_no: "CERT-9",
      issued_at: "2026-01-10",
      valid_until: "2026-12-31",
      issuing_authority: "HQ",
      granted_internally: true,
      notes: "note",
    },
  );

  assert.equal(
    validateEmployeeQualificationDraft({
      record_kind: "qualification",
      qualification_type_id: "",
      issued_at: "2026-01-10",
      valid_until: "2026-12-31",
    }),
    "employeeAdmin.feedback.qualificationTargetRequired",
  );
});

test("credential and absence validations catch required and invalid windows", () => {
  assert.equal(
    validateEmployeeCredentialDraft({
      credential_no: "CARD-1",
      credential_type: "badge",
      encoded_value: "ABC",
      valid_from: "2026-03-10",
      valid_until: "2026-03-01",
    }),
    "employeeAdmin.feedback.credentialInvalidWindow",
  );

  assert.deepEqual(
    buildEmployeeCredentialPayload(
      {
        credential_no: " CARD-2 ",
        credential_type: " badge ",
        encoded_value: " 123 ",
        valid_from: "2026-03-01",
        valid_until: "",
        notes: " test ",
      },
      { tenantId: "tenant-1", employeeId: "employee-1" },
    ),
    {
      tenant_id: "tenant-1",
      employee_id: "employee-1",
      credential_no: "CARD-2",
      credential_type: "badge",
      encoded_value: "123",
      valid_from: "2026-03-01",
      valid_until: null,
      notes: "test",
    },
  );

  assert.equal(
    validateEmployeeAbsenceDraft({
      absence_type: "vacation",
      starts_on: "2026-08-05",
      ends_on: "2026-08-01",
    }),
    "employeeAdmin.feedback.absenceInvalidWindow",
  );

  assert.deepEqual(
    buildEmployeeAbsencePayload(
      {
        absence_type: " vacation ",
        starts_on: "2026-08-01",
        ends_on: "2026-08-05",
        notes: " family ",
      },
      { tenantId: "tenant-1", employeeId: "employee-1" },
    ),
    {
      tenant_id: "tenant-1",
      employee_id: "employee-1",
      absence_type: "vacation",
      starts_on: "2026-08-01",
      ends_on: "2026-08-05",
      notes: "family",
    },
  );
});

test("availability payloads map local datetime and weekday masks", () => {
  assert.equal(buildWeekdayMask([0, 2, 4]), "1010100");
  assert.deepEqual(parseWeekdayMask("1010100"), [0, 2, 4]);

  const payload = buildEmployeeAvailabilityPayload(
    {
      rule_kind: "preferred",
      starts_at: "2026-04-10T08:00",
      ends_at: "2026-04-10T16:00",
      recurrence_type: "weekly",
      weekday_indexes: [0, 2, 4],
      notes: "day shift",
    },
    { tenantId: "tenant-1", employeeId: "employee-1" },
  );

  assert.equal(payload.tenant_id, "tenant-1");
  assert.equal(payload.employee_id, "employee-1");
  assert.equal(payload.rule_kind, "preferred");
  assert.equal(payload.recurrence_type, "weekly");
  assert.equal(payload.weekday_mask, "1010100");
  assert.equal(typeof payload.starts_at, "string");
  assert.equal(typeof payload.ends_at, "string");
  assert.equal(validateEmployeeAvailabilityDraft({
    rule_kind: "preferred",
    starts_at: "2026-04-10T16:00",
    ends_at: "2026-04-10T08:00",
    recurrence_type: "none",
    weekday_indexes: [],
  }), "employeeAdmin.feedback.availabilityInvalidWindow");
  assert.equal(toLocalDateTimeInput(payload.starts_at).slice(0, 10), "2026-04-10");
});

test("import template rows use the stable employee operational header order", () => {
  assert.equal(
    buildEmployeeImportTemplateRows(),
    "personnel_no,first_name,last_name,preferred_name,work_email,work_phone,mobile_phone,default_branch_id,default_mandate_id,hire_date,termination_date,status,employment_type_code,target_weekly_hours,target_monthly_hours,user_id,notes",
  );
});
