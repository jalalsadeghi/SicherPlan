const EMPTY_STATE_ERRORS = new Set([
  "errors.subcontractors.portal.scope_not_resolved",
  "errors.subcontractors.portal.contact_not_linked",
]);

const DEACTIVATED_STATE_ERRORS = new Set([
  "errors.subcontractors.portal.contact_portal_disabled",
  "errors.subcontractors.portal.contact_inactive",
  "errors.subcontractors.portal.company_inactive",
]);

export function derivePortalSubcontractorAccessState({ isLoading, hasSession, hasContext, lastErrorKey }) {
  if (isLoading) {
    return "loading";
  }

  if (hasContext) {
    return "ready";
  }

  if (!hasSession) {
    return "login";
  }

  if (DEACTIVATED_STATE_ERRORS.has(lastErrorKey)) {
    return "deactivated";
  }

  if (EMPTY_STATE_ERRORS.has(lastErrorKey)) {
    return "empty";
  }

  return "unauthorized";
}

export function mapSubcontractorPortalApiMessage(messageKey) {
  if (typeof messageKey === "string" && messageKey.startsWith("portalSubcontractor.")) {
    return messageKey;
  }

  const messageMap = {
    "errors.iam.auth.invalid_credentials": "portalSubcontractor.feedback.invalidCredentials",
    "errors.iam.auth.invalid_access_token": "portalSubcontractor.feedback.authRequired",
    "errors.iam.authorization.permission_denied": "portalSubcontractor.feedback.permissionDenied",
    "errors.iam.authorization.scope_denied": "portalSubcontractor.feedback.permissionDenied",
    "errors.field.watchbook.portal_write_denied": "portalSubcontractor.feedback.watchbookWriteDenied",
    "errors.field.watchbook.closed": "portalSubcontractor.feedback.watchbookClosed",
    "errors.subcontractors.portal.scope_not_resolved": "portalSubcontractor.feedback.scopeNotResolved",
    "errors.subcontractors.portal.contact_not_linked": "portalSubcontractor.feedback.contactNotLinked",
    "errors.subcontractors.portal.contact_portal_disabled": "portalSubcontractor.feedback.contactPortalDisabled",
    "errors.subcontractors.portal.contact_inactive": "portalSubcontractor.feedback.contactInactive",
    "errors.subcontractors.portal.company_inactive": "portalSubcontractor.feedback.companyInactive",
    "errors.subcontractors.portal.invoice_check.not_found": "portalSubcontractor.feedback.invoiceCheckNotFound",
    "errors.subcontractors.portal_allocation.position_not_found":
      "portalSubcontractor.feedback.allocationPositionNotFound",
    "errors.subcontractors.portal_allocation.planning_contract_unavailable":
      "portalSubcontractor.feedback.allocationPlanningUnavailable",
    "errors.subcontractors.portal_allocation.blocked_by_validation":
      "portalSubcontractor.feedback.allocationBlocked",
    "errors.subcontractors.worker.not_found": "portalSubcontractor.feedback.allocationWorkerNotFound",
    "errors.subcontractors.worker.duplicate_number": "portalSubcontractor.feedback.allocationBlocked",
    "errors.subcontractors.worker.stale_version": "portalSubcontractor.feedback.allocationBlocked",
    "errors.subcontractors.worker_qualification.not_found": "portalSubcontractor.feedback.allocationBlocked",
    "errors.subcontractors.worker_qualification.qualification_type_not_found":
      "portalSubcontractor.feedback.allocationBlocked",
    "errors.subcontractors.worker_qualification.invalid_window":
      "portalSubcontractor.feedback.allocationBlocked",
  };

  return messageMap[messageKey] ?? "portalSubcontractor.feedback.error";
}
