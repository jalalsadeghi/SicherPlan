export const SUBCONTRACTOR_PERMISSION_MATRIX = {
  platform_admin: [
    "subcontractors.company.read",
    "subcontractors.company.write",
    "subcontractors.finance.read",
    "subcontractors.finance.write",
  ],
  tenant_admin: [
    "subcontractors.company.read",
    "subcontractors.company.write",
    "subcontractors.finance.read",
    "subcontractors.finance.write",
  ],
  dispatcher: ["subcontractors.company.read"],
  accounting: ["subcontractors.company.read", "subcontractors.finance.read"],
  controller_qm: ["subcontractors.company.read"],
  employee_user: [],
  customer_user: [],
  subcontractor_user: [],
};

export function hasSubcontractorPermission(role, permissionKey) {
  return (SUBCONTRACTOR_PERMISSION_MATRIX[role] ?? []).includes(permissionKey);
}

export function deriveSubcontractorActionState(role, selectedSubcontractor) {
  const canRead = hasSubcontractorPermission(role, "subcontractors.company.read");
  const canWrite = hasSubcontractorPermission(role, "subcontractors.company.write");
  const canReadFinance = hasSubcontractorPermission(role, "subcontractors.finance.read");
  const canWriteFinance = hasSubcontractorPermission(role, "subcontractors.finance.write");
  const status = selectedSubcontractor?.status ?? "active";
  const archivedAt = selectedSubcontractor?.archived_at ?? null;

  return {
    canRead,
    canWrite,
    canReadFinance,
    canWriteFinance,
    canCreate: canWrite,
    canEdit: canWrite && !!selectedSubcontractor,
    canManageContacts: canWrite && !!selectedSubcontractor,
    canManageScopes: canWrite && !!selectedSubcontractor,
    canManageFinance: canWriteFinance && !!selectedSubcontractor,
    canManageHistory: canWrite && !!selectedSubcontractor,
    canManageWorkforce: canWrite && !!selectedSubcontractor,
    canImportWorkforce: canWrite && !!selectedSubcontractor,
    canExportWorkforce: canRead && !!selectedSubcontractor,
    canArchive: canWrite && !!selectedSubcontractor && !archivedAt && status !== "archived",
    canReactivate: canWrite && !!selectedSubcontractor && status === "archived",
  };
}

export function buildSubcontractorLifecyclePayload(subcontractor) {
  return {
    version_no: subcontractor.version_no,
  };
}

export function summarizePrimaryContact(contacts) {
  const primary = (contacts ?? []).find((contact) => contact.is_primary_contact);
  if (!primary) {
    return "";
  }
  return [primary.full_name, primary.email].filter(Boolean).join(" · ");
}

export function summarizeScopeRows(scopes) {
  return (scopes ?? [])
    .filter((scope) => !scope.archived_at)
    .map((scope) => [scope.branch_id, scope.mandate_id].filter(Boolean).join(" / "))
    .filter(Boolean)
    .join(", ");
}

export function hasPortalEnabledContact(contacts) {
  return (contacts ?? []).some((contact) => contact.portal_enabled && !contact.archived_at);
}

export function buildSubcontractorWorkerImportTemplateRows() {
  return [
    "worker_no,first_name,last_name,preferred_name,birth_date,email,phone,mobile,status,notes",
    "WK-100,Erika,Partner,,1990-05-12,erika@example.com,,+491701234567,active,Ersteinsatz bereit",
  ].join("\n");
}

export function deriveWorkerIndicators(worker, today = new Date()) {
  const isoToday = today.toISOString().slice(0, 10);
  const qualifications = worker?.qualifications ?? [];
  const credentials = worker?.credentials ?? [];
  const activeQualifications = qualifications.filter((row) => !row.archived_at && row.status !== "archived");
  const activeCredentials = credentials.filter((row) => !row.archived_at && row.status !== "archived");
  const expiredQualifications = activeQualifications.filter((row) => row.valid_until && row.valid_until < isoToday);

  return {
    qualificationCount: activeQualifications.length,
    credentialCount: activeCredentials.length,
    expiredQualificationCount: expiredQualifications.length,
    hasQualifications: activeQualifications.length > 0,
    hasCredentials: activeCredentials.length > 0,
    hasExpiredQualifications: expiredQualifications.length > 0,
  };
}

export function filterWorkersByQuickState(workers, quickFilter, today = new Date()) {
  if (!quickFilter || quickFilter === "all") {
    return workers ?? [];
  }

  return (workers ?? []).filter((worker) => {
    const indicators = deriveWorkerIndicators(worker, today);
    if (quickFilter === "needs_qualification") {
      return !indicators.hasQualifications;
    }
    if (quickFilter === "missing_credential") {
      return !indicators.hasCredentials;
    }
    if (quickFilter === "expired_qualification") {
      return indicators.hasExpiredQualifications;
    }
    return true;
  });
}

export function mapSubcontractorImportRowMessage(code) {
  const messageMap = {
    created_worker: "sicherplan.subcontractors.workforce.import.row.createdWorker",
    updated_worker: "sicherplan.subcontractors.workforce.import.row.updatedWorker",
    "subcontractors.worker_import.missing_worker_no": "sicherplan.subcontractors.workforce.import.row.missingWorkerNo",
    "subcontractors.worker_import.missing_first_name": "sicherplan.subcontractors.workforce.import.row.missingFirstName",
    "subcontractors.worker_import.missing_last_name": "sicherplan.subcontractors.workforce.import.row.missingLastName",
    "subcontractors.worker_import.invalid_birth_date": "sicherplan.subcontractors.workforce.import.row.invalidBirthDate",
    "subcontractors.worker_import.invalid_status": "sicherplan.subcontractors.workforce.import.row.invalidStatus",
  };

  return messageMap[code] ?? "sicherplan.subcontractors.feedback.error";
}

export function mapSubcontractorApiMessage(messageKey) {
  const messageMap = {
    "errors.iam.auth.invalid_access_token": "sicherplan.subcontractors.feedback.authRequired",
    "errors.iam.authorization.permission_denied": "sicherplan.subcontractors.feedback.permissionDenied",
    "errors.iam.authorization.scope_denied": "sicherplan.subcontractors.feedback.permissionDenied",
    "errors.subcontractors.authorization.portal_forbidden": "sicherplan.subcontractors.feedback.permissionDenied",
    "errors.subcontractors.authorization.internal_scope_required": "sicherplan.subcontractors.feedback.permissionDenied",
    "errors.subcontractors.subcontractor.not_found": "sicherplan.subcontractors.feedback.notFound",
    "errors.subcontractors.contact.not_found": "sicherplan.subcontractors.feedback.notFound",
    "errors.subcontractors.scope.not_found": "sicherplan.subcontractors.feedback.notFound",
    "errors.subcontractors.finance_profile.not_found": "sicherplan.subcontractors.feedback.notFound",
    "errors.subcontractors.subcontractor.duplicate_number": "sicherplan.subcontractors.feedback.duplicateNumber",
    "errors.subcontractors.contact.primary_conflict": "sicherplan.subcontractors.feedback.primaryConflict",
    "errors.subcontractors.contact.duplicate_user_link": "sicherplan.subcontractors.feedback.duplicateUserLink",
    "errors.subcontractors.contact.portal_user_required": "sicherplan.subcontractors.feedback.portalUserRequired",
    "errors.subcontractors.scope.overlap": "sicherplan.subcontractors.feedback.scopeOverlap",
    "errors.subcontractors.scope.mandate_branch_mismatch": "sicherplan.subcontractors.feedback.scopeBranchMismatch",
    "errors.subcontractors.subcontractor.stale_version": "sicherplan.subcontractors.feedback.staleVersion",
    "errors.subcontractors.subcontractor_contact.stale_version": "sicherplan.subcontractors.feedback.staleVersion",
    "errors.subcontractors.subcontractor_scope.stale_version": "sicherplan.subcontractors.feedback.staleVersion",
    "errors.subcontractors.subcontractor_finance_profile.stale_version": "sicherplan.subcontractors.feedback.staleVersion",
    "errors.subcontractors.history_entry.not_found": "sicherplan.subcontractors.feedback.historyNotFound",
    "errors.subcontractors.history_entry.invalid_type": "sicherplan.subcontractors.feedback.historyTypeInvalid",
    "errors.subcontractors.history_entry.contact_not_found": "sicherplan.subcontractors.feedback.historyContactMissing",
    "errors.subcontractors.lifecycle.archive_not_allowed": "sicherplan.subcontractors.feedback.lifecycleDenied",
    "errors.subcontractors.lifecycle.reactivate_not_allowed": "sicherplan.subcontractors.feedback.lifecycleDenied",
    "errors.subcontractors.worker.not_found": "sicherplan.subcontractors.feedback.workerNotFound",
    "errors.subcontractors.worker.duplicate_number": "sicherplan.subcontractors.feedback.workerDuplicateNumber",
    "errors.subcontractors.worker.stale_version": "sicherplan.subcontractors.feedback.staleVersion",
    "errors.subcontractors.worker_qualification.not_found": "sicherplan.subcontractors.feedback.workerQualificationNotFound",
    "errors.subcontractors.worker_qualification.qualification_type_not_found":
      "sicherplan.subcontractors.feedback.workerQualificationTypeMissing",
    "errors.subcontractors.worker_qualification.invalid_window": "sicherplan.subcontractors.feedback.workerQualificationInvalidWindow",
    "errors.subcontractors.worker_qualification.expiry_required":
      "sicherplan.subcontractors.feedback.workerQualificationExpiryRequired",
    "errors.subcontractors.worker_qualification.stale_version": "sicherplan.subcontractors.feedback.staleVersion",
    "errors.subcontractors.worker_credential.not_found": "sicherplan.subcontractors.feedback.workerCredentialNotFound",
    "errors.subcontractors.worker_credential.invalid_type": "sicherplan.subcontractors.feedback.workerCredentialInvalidType",
    "errors.subcontractors.worker_credential.invalid_status": "sicherplan.subcontractors.feedback.workerCredentialInvalidStatus",
    "errors.subcontractors.worker_credential.invalid_window": "sicherplan.subcontractors.feedback.workerCredentialInvalidWindow",
    "errors.subcontractors.worker_credential.duplicate_no": "sicherplan.subcontractors.feedback.workerCredentialDuplicateNo",
    "errors.subcontractors.worker_credential.duplicate_encoded_value":
      "sicherplan.subcontractors.feedback.workerCredentialDuplicateEncodedValue",
    "errors.subcontractors.worker_credential.stale_version": "sicherplan.subcontractors.feedback.staleVersion",
    "errors.subcontractors.worker_import.invalid_csv": "sicherplan.subcontractors.feedback.workerImportInvalidCsv",
    "errors.subcontractors.worker_import.invalid_headers": "sicherplan.subcontractors.feedback.workerImportInvalidHeaders",
    "errors.subcontractors.worker_import.scope_mismatch": "sicherplan.subcontractors.feedback.permissionDenied",
  };

  return messageMap[messageKey] ?? "sicherplan.subcontractors.feedback.error";
}
