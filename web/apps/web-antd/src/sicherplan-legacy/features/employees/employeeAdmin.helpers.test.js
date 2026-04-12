import assert from "node:assert/strict";
import test from "node:test";

import {
  buildEmployeeImportTemplateRows,
  buildEmployeeAbsencePayload,
  buildEmployeeAvailabilityPayload,
  buildEmployeeCredentialPayload,
  buildEmployeeDocumentUploadPayload,
  buildEmployeeFunctionTypePayload,
  buildEmployeePrivateProfilePayload,
  buildEmployeeQualificationPayload,
  buildEmployeeQualificationTypePayload,
  buildWeekdayMask,
  deriveEmployeeActionState,
  EMPLOYEE_AVAILABILITY_RULE_KIND_OPTIONS,
  EMPLOYEE_CREDENTIAL_TYPE_OPTIONS,
  EMPLOYEE_DOCUMENT_TYPE_OPTIONS,
  hasEmployeePermission,
  isEmployeeAddressCurrent,
  mapEmployeeApiMessage,
  parseWeekdayMask,
  resolveEmployeeDetailTab,
  summarizeCurrentAddress,
  toLocalDateTimeInput,
  validateEmployeeAbsenceDraft,
  validateEmployeeAddressDraft,
  validateEmployeeAvailabilityDraft,
  validateEmployeeCredentialDraft,
  validateEmployeePrivateProfileDraft,
  validateEmployeeFunctionTypeDraft,
  validateEmployeeQualificationDraft,
  validateEmployeeQualificationTypeDraft,
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
  assert.equal(adminState.canManageCatalogs, true);
  assert.equal(dispatcherState.canReadPrivate, false);
  assert.equal(dispatcherState.canWrite, false);
  assert.equal(dispatcherState.canExport, true);
  assert.equal(dispatcherState.canManageCatalogs, false);
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
  assert.equal(
    mapEmployeeApiMessage("errors.docs.document_type.not_found"),
    "employeeAdmin.feedback.documentTypeNotConfigured",
  );
  assert.equal(
    mapEmployeeApiMessage("errors.employees.employee_qualification.target_mismatch"),
    "employeeAdmin.feedback.qualificationTargetMismatch",
  );
  assert.equal(
    mapEmployeeApiMessage("errors.employees.employee_qualification.expiry_required"),
    "employeeAdmin.feedback.qualificationExpiryRequired",
  );
});

test("detail tab resolver preserves valid tabs and falls back safely", () => {
  const tabs = ["overview", "qualifications", "credentials"];

  assert.equal(resolveEmployeeDetailTab("qualifications", tabs), "qualifications");
  assert.equal(resolveEmployeeDetailTab("private_profile", tabs), "overview");
  assert.equal(resolveEmployeeDetailTab("private_profile", ["credentials"], "overview"), "credentials");
  assert.equal(resolveEmployeeDetailTab("", []), "overview");
});

test("employee document type options expose the seeded employee-facing keys", () => {
  assert.deepEqual(
    EMPLOYEE_DOCUMENT_TYPE_OPTIONS.map((option) => option.value),
    [
      "employment_contract",
      "identity_card",
      "passport_copy",
      "residence_permit",
      "driving_licence",
      "qualification_certificate",
      "employee_misc",
    ],
  );
});

test("employee document upload payload normalizes empty and selected document type keys", async () => {
  const emptyPayload = await buildEmployeeDocumentUploadPayload(
    {
      title: " Arbeitsvertrag ",
      relation_type: "contract",
      label: " Vertragsakte ",
      document_type_key: "   ",
    },
    { name: "contract.pdf", type: "application/pdf" },
    async () => "YQ==",
  );
  assert.equal(emptyPayload.document_type_key, null);
  assert.equal(emptyPayload.title, "Arbeitsvertrag");

  const seededPayload = await buildEmployeeDocumentUploadPayload(
    {
      title: "Ausweis",
      relation_type: "id_proof",
      label: "",
      document_type_key: "identity_card",
    },
    { name: "id.pdf", type: "application/pdf" },
    async () => "Yg==",
  );
  assert.equal(seededPayload.document_type_key, "identity_card");
});

test("current address summary derives from the latest active history row, not primary flag alone", () => {
  const summary = summarizeCurrentAddress([
    {
      archived_at: null,
      status: "active",
      is_primary: false,
      valid_from: "2025-01-01",
      valid_to: "2025-12-31",
      address: { street_line_1: "Alt", postal_code: "11111", city: "Berlin" },
    },
    {
      archived_at: null,
      status: "active",
      is_primary: false,
      valid_from: "2026-01-01",
      valid_to: null,
      address: { street_line_1: "Neu", postal_code: "22222", city: "Hamburg" },
    },
  ]);

  assert.equal(summary, "Neu, 22222, Hamburg");
});

test("address current-state helper respects active validity windows", () => {
  assert.equal(
    isEmployeeAddressCurrent(
      { archived_at: null, status: "active", valid_from: "2026-01-01", valid_to: null },
      "2026-05-01",
    ),
    true,
  );
  assert.equal(
    isEmployeeAddressCurrent(
      { archived_at: null, status: "active", valid_from: "2026-06-01", valid_to: null },
      "2026-05-01",
    ),
    false,
  );
  assert.equal(
    isEmployeeAddressCurrent(
      { archived_at: null, status: "active", valid_from: "2026-01-01", valid_to: "2026-04-30" },
      "2026-05-01",
    ),
    false,
  );
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
      },
      [{ id: "hist-1", address_type: "home", valid_from: "2026-01-01", valid_to: null, archived_at: null }],
      "",
    ),
    "employeeAdmin.feedback.addressOverlap",
  );
});

test("address validation can ignore the active row that will be closed during a transition", () => {
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
      },
      [{ id: "hist-1", address_type: "home", valid_from: "2026-01-01", valid_to: null, archived_at: null }],
      "",
      { ignoreRowIds: ["hist-1"] },
    ),
    null,
  );
});

test("private profile payload normalizes the full supported contract", () => {
  assert.deepEqual(
    buildEmployeePrivateProfilePayload(
      {
        private_email: " private@example.com ",
        private_phone: " +49 171 1234567 ",
        birth_date: "2026-03-01",
        place_of_birth: " Berlin ",
        nationality_country_code: "de",
        marital_status: " married ",
        tax_id: " 123456789 ",
        social_security_no: " 987654321 ",
        bank_account_holder: " Max Mustermann ",
        bank_iban: " de02120300000000202051 ",
        bank_bic: " byla dem1001 ",
        emergency_contact_name: " Erika Muster ",
        emergency_contact_phone: " +49 30 555666 ",
        notes: " vertraulich ",
      },
      { tenantId: "tenant-1", employeeId: "employee-1" },
    ),
    {
      tenant_id: "tenant-1",
      employee_id: "employee-1",
      private_email: "private@example.com",
      private_phone: "+49 171 1234567",
      birth_date: "2026-03-01",
      place_of_birth: "Berlin",
      nationality_country_code: "DE",
      marital_status: "married",
      tax_id: "123456789",
      social_security_no: "987654321",
      bank_account_holder: "Max Mustermann",
      bank_iban: "DE02120300000000202051",
      bank_bic: "BYLADEM1001",
      emergency_contact_name: "Erika Muster",
      emergency_contact_phone: "+49 30 555666",
      notes: "vertraulich",
    },
  );
});

test("private profile validation rejects malformed email, short phone, and invalid country code", () => {
  assert.equal(
    validateEmployeePrivateProfileDraft({
      private_email: "invalid",
    }),
    "employeeAdmin.feedback.invalidPrivateEmail",
  );

  assert.equal(
    validateEmployeePrivateProfileDraft({
      private_phone: "12345",
    }),
    "employeeAdmin.feedback.invalidPrivatePhone",
  );

  assert.equal(
    validateEmployeePrivateProfileDraft({
      nationality_country_code: "DEU",
    }),
    "employeeAdmin.feedback.invalidNationalityCountryCode",
  );

  assert.equal(
    validateEmployeePrivateProfileDraft({
      private_email: " ok@example.com ",
      private_phone: "+49 171 1234567",
      emergency_contact_phone: "030 123456",
      nationality_country_code: "de",
    }),
    "",
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

  assert.deepEqual(
    buildEmployeeQualificationPayload(
      {
        record_kind: "qualification",
        function_type_id: "fn-stale",
        qualification_type_id: "qual-1",
      },
      { tenantId: "tenant-1", employeeId: "employee-1" },
    ),
    {
      tenant_id: "tenant-1",
      employee_id: "employee-1",
      record_kind: "qualification",
      function_type_id: null,
      qualification_type_id: "qual-1",
      certificate_no: null,
      issued_at: null,
      valid_until: null,
      issuing_authority: null,
      granted_internally: false,
      notes: null,
    },
  );

  assert.deepEqual(
    buildEmployeeQualificationPayload(
      {
        record_kind: "function",
        function_type_id: "fn-1",
        qualification_type_id: "qual-stale",
      },
      { tenantId: "tenant-1", employeeId: "employee-1" },
    ),
    {
      tenant_id: "tenant-1",
      employee_id: "employee-1",
      record_kind: "function",
      function_type_id: "fn-1",
      qualification_type_id: null,
      certificate_no: null,
      issued_at: null,
      valid_until: null,
      issuing_authority: null,
      granted_internally: false,
      notes: null,
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

  assert.equal(
    validateEmployeeQualificationDraft(
      {
        record_kind: "qualification",
        qualification_type_id: "qual-1",
        issued_at: "",
        valid_until: "",
      },
      { expiry_required: true, default_validity_days: null },
    ),
    "employeeAdmin.feedback.qualificationExpiryRequired",
  );

  assert.equal(
    validateEmployeeQualificationDraft(
      {
        record_kind: "qualification",
        qualification_type_id: "qual-1",
        issued_at: "2026-01-20",
        valid_until: "",
      },
      { expiry_required: true, default_validity_days: 730 },
    ),
    null,
  );
});

test("function-type catalog payload trims values and requires code plus label", () => {
  assert.deepEqual(
    buildEmployeeFunctionTypePayload(
      {
        code: " SEC_GUARD ",
        label: " Sicherheitsdienst ",
        category: " ops ",
        description: " Nachtwache ",
        is_active: true,
        planning_relevant: false,
      },
      { tenantId: "tenant-1" },
    ),
    {
      tenant_id: "tenant-1",
      code: "SEC_GUARD",
      label: "Sicherheitsdienst",
      category: "ops",
      description: "Nachtwache",
      is_active: true,
      planning_relevant: false,
    },
  );

  assert.equal(
    validateEmployeeFunctionTypeDraft({
      code: " ",
      label: " ",
    }),
    "employeeAdmin.feedback.catalogRequired",
  );
});

test("qualification-type catalog payload normalizes validity and rejects non-positive values", () => {
  assert.deepEqual(
    buildEmployeeQualificationTypePayload(
      {
        code: " G34A ",
        label: " Sachkunde G34a ",
        category: " security ",
        description: " Pflichtnachweis ",
        is_active: true,
        planning_relevant: true,
        compliance_relevant: true,
        expiry_required: true,
        default_validity_days: " 365 ",
        proof_required: true,
      },
      { tenantId: "tenant-1" },
    ),
    {
      tenant_id: "tenant-1",
      code: "G34A",
      label: "Sachkunde G34a",
      category: "security",
      description: "Pflichtnachweis",
      is_active: true,
      planning_relevant: true,
      compliance_relevant: true,
      expiry_required: true,
      default_validity_days: 365,
      proof_required: true,
    },
  );

  assert.equal(
    validateEmployeeQualificationTypeDraft({
      code: "G34A",
      label: "Sachkunde",
      default_validity_days: "0",
    }),
    "employeeAdmin.feedback.invalidQualificationTypeValidity",
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
    "employeeAdmin.feedback.invalidCredentialType",
  );

  assert.equal(
    validateEmployeeCredentialDraft({
      credential_no: "CARD-1",
      credential_type: "work_badge",
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
        credential_type: " work_badge ",
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
      credential_type: "work_badge",
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

test("credential type options expose only supported backend values", () => {
  assert.deepEqual(
    EMPLOYEE_CREDENTIAL_TYPE_OPTIONS.map((option) => option.value),
    ["company_id", "work_badge"],
  );
});

test("availability payloads map local datetime and weekday masks", () => {
  assert.equal(buildWeekdayMask([0, 2, 4]), "1010100");
  assert.deepEqual(parseWeekdayMask("1010100"), [0, 2, 4]);

  const payload = buildEmployeeAvailabilityPayload(
    {
      rule_kind: "availability",
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
  assert.equal(payload.rule_kind, "availability");
  assert.equal(payload.recurrence_type, "weekly");
  assert.equal(payload.weekday_mask, "1010100");
  assert.equal(typeof payload.starts_at, "string");
  assert.equal(typeof payload.ends_at, "string");
  assert.equal(validateEmployeeAvailabilityDraft({
    rule_kind: "preferred",
    starts_at: "2026-04-10T08:00",
    ends_at: "2026-04-10T16:00",
    recurrence_type: "none",
    weekday_indexes: [],
  }), "employeeAdmin.feedback.invalidAvailabilityKind");
  assert.equal(validateEmployeeAvailabilityDraft({
    rule_kind: "availability",
    starts_at: "2026-04-10T16:00",
    ends_at: "2026-04-10T08:00",
    recurrence_type: "none",
    weekday_indexes: [],
  }), "employeeAdmin.feedback.availabilityInvalidWindow");
  assert.equal(toLocalDateTimeInput(payload.starts_at).slice(0, 10), "2026-04-10");
});

test("availability rule kind options expose only supported backend values", () => {
  assert.deepEqual(
    EMPLOYEE_AVAILABILITY_RULE_KIND_OPTIONS.map((option) => option.value),
    ["availability", "unavailable", "free_wish"],
  );
});

test("import template rows use the stable employee operational header order", () => {
  assert.equal(
    buildEmployeeImportTemplateRows(),
    "personnel_no,first_name,last_name,preferred_name,work_email,work_phone,mobile_phone,default_branch_id,default_mandate_id,hire_date,termination_date,status,employment_type_code,target_weekly_hours,target_monthly_hours,user_id,notes",
  );
});
