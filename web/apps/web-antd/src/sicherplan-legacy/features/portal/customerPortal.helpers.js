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

  switch (lastErrorKey) {
    case "errors.iam.authorization.permission_denied":
    case "errors.iam.authorization.scope_denied":
      return "missing_permission";
    case "errors.customers.portal.scope_not_resolved":
      return "missing_scope";
    case "errors.customers.portal.contact_not_linked":
      return "contact_not_linked";
    case "errors.customers.portal.contact_inactive":
      return "contact_inactive";
    case "errors.customers.portal.customer_inactive":
      return "customer_inactive";
    default:
      return "error";
  }
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

export function derivePortalCapabilityState(capability) {
  if (!capability) {
    return "not_enabled";
  }

  if (capability.availability_status === "pending_source_module") {
    return "pending_integration";
  }

  if (capability.interaction_mode === "write_optional") {
    return capability.can_write ? "enabled" : "not_enabled";
  }

  if (capability.interaction_mode === "download") {
    return capability.can_download_documents ? "available" : "not_enabled";
  }

  return "read_only";
}

export function derivePortalDatasetMessage(collection, emptyMessageKey) {
  if (!collection) {
    return null;
  }

  if (collection.source.availability_status === "pending_source_module") {
    return collection.source.message_key;
  }

  if (collection.items.length === 0) {
    return emptyMessageKey;
  }

  return collection.source.message_key;
}
