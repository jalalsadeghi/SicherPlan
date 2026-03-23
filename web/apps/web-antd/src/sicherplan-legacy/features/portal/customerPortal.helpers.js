const EMPTY_STATE_ERRORS = new Set([
  "errors.customers.portal.scope_not_resolved",
  "errors.customers.portal.contact_not_linked",
]);

const DEACTIVATED_STATE_ERRORS = new Set([
  "errors.customers.portal.contact_inactive",
  "errors.customers.portal.customer_inactive",
]);

export function canAccessAppRoute({ allowedRoles, allowGuest = false, role, isAuthenticated }) {
  if (allowGuest) {
    return true;
  }

  if (!allowedRoles?.length) {
    return true;
  }

  if (!isAuthenticated) {
    return false;
  }

  return allowedRoles.includes(role);
}

export function derivePortalCustomerAccessState({ isLoading, hasSession, hasContext, lastErrorKey }) {
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

export function mapPortalApiMessage(messageKey) {
  const messageMap = {
    "errors.iam.auth.invalid_credentials": "portalCustomer.feedback.invalidCredentials",
    "errors.iam.auth.invalid_access_token": "portalCustomer.feedback.authRequired",
    "errors.iam.authorization.permission_denied": "portalCustomer.feedback.permissionDenied",
    "errors.iam.authorization.scope_denied": "portalCustomer.feedback.permissionDenied",
    "errors.field.watchbook.portal_write_denied": "portalCustomer.feedback.watchbookWriteDenied",
    "errors.field.watchbook.closed": "portalCustomer.feedback.watchbookClosed",
    "errors.finance.timesheet.not_found": "portalCustomer.feedback.financeDocumentDenied",
    "errors.finance.invoice.not_found": "portalCustomer.feedback.financeDocumentDenied",
    "errors.docs.document.not_found": "portalCustomer.feedback.financeDocumentDenied",
    "errors.customers.portal.scope_not_resolved": "portalCustomer.feedback.scopeNotResolved",
    "errors.customers.portal.contact_not_linked": "portalCustomer.feedback.contactNotLinked",
    "errors.customers.portal.contact_inactive": "portalCustomer.feedback.contactInactive",
    "errors.customers.portal.customer_inactive": "portalCustomer.feedback.customerInactive",
  };

  return messageMap[messageKey] ?? "portalCustomer.feedback.error";
}

export function derivePortalCollectionState(collection) {
  if (!collection) {
    return "loading";
  }

  if (collection.items.length > 0) {
    return "ready";
  }

  return collection.source.availability_status === "pending_source_module" ? "pending" : "empty";
}
