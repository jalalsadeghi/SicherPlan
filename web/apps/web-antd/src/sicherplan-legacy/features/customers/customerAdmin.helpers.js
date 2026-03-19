export const CUSTOMER_PERMISSION_MATRIX = {
  platform_admin: ["customers.customer.read", "customers.customer.write"],
  tenant_admin: ["customers.customer.read", "customers.customer.write"],
  dispatcher: [],
  accounting: ["customers.customer.read"],
  controller_qm: [],
  customer_user: [],
  subcontractor_user: [],
};

export function hasCustomerPermission(role, permissionKey) {
  return (CUSTOMER_PERMISSION_MATRIX[role] ?? []).includes(permissionKey);
}

export function deriveCustomerActionState(role, selectedCustomer) {
  const canRead = hasCustomerPermission(role, "customers.customer.read");
  const canWrite = hasCustomerPermission(role, "customers.customer.write");
  const customerStatus = selectedCustomer?.status ?? "active";
  const archivedAt = selectedCustomer?.archived_at ?? null;

  return {
    canRead,
    canCreate: canWrite,
    canEdit: canWrite && !!selectedCustomer,
    canManageContacts: canWrite && !!selectedCustomer,
    canManageAddresses: canWrite && !!selectedCustomer,
    canDeactivate: canWrite && customerStatus === "active" && !archivedAt,
    canReactivate: canWrite && customerStatus === "inactive" && !archivedAt,
    canArchive: canWrite && !!selectedCustomer && !archivedAt,
  };
}

export function buildLifecyclePayload(customer, nextStatus) {
  const archivedAt = nextStatus === "archived" ? new Date().toISOString() : null;

  return {
    status: nextStatus,
    archived_at: archivedAt,
    version_no: customer.version_no,
  };
}

export function formatPrimaryContactSummary(customer) {
  const primaryContact = customer?.contacts?.find((contact) => contact.is_primary_contact);
  if (!primaryContact) {
    return "";
  }

  return [primaryContact.full_name, primaryContact.email].filter(Boolean).join(" · ");
}

export function mapCustomerApiMessage(messageKey) {
  const messageMap = {
    "errors.iam.auth.invalid_access_token": "customerAdmin.feedback.authRequired",
    "errors.iam.authorization.permission_denied": "customerAdmin.feedback.permissionDenied",
    "errors.iam.authorization.scope_denied": "customerAdmin.feedback.permissionDenied",
    "errors.customers.customer.not_found": "customerAdmin.feedback.notFound",
    "errors.customers.contact.not_found": "customerAdmin.feedback.notFound",
    "errors.customers.customer_address.not_found": "customerAdmin.feedback.notFound",
    "errors.customers.history_entry.not_found": "customerAdmin.feedback.notFound",
    "errors.customers.employee_block.not_found": "customerAdmin.feedback.notFound",
    "errors.customers.customer.duplicate_number": "customerAdmin.feedback.duplicateNumber",
    "errors.customers.customer.stale_version": "customerAdmin.feedback.staleVersion",
    "errors.customers.contact.stale_version": "customerAdmin.feedback.staleVersion",
    "errors.customers.address_link.stale_version": "customerAdmin.feedback.staleVersion",
    "errors.customers.employee_block.stale_version": "customerAdmin.feedback.staleVersion",
    "errors.customers.contact.duplicate_email": "customerAdmin.feedback.duplicateEmail",
    "errors.customers.contact.primary_conflict": "customerAdmin.feedback.primaryConflict",
    "errors.customers.customer_address.default_conflict": "customerAdmin.feedback.defaultAddressConflict",
    "errors.customers.contact.invalid_user_scope": "customerAdmin.feedback.invalidPortalUser",
  };

  return messageMap[messageKey] ?? "customerAdmin.feedback.error";
}
