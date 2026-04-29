export const CUSTOMER_PERMISSION_MATRIX = {
  platform_admin: ["customers.customer.read", "customers.customer.write"],
  tenant_admin: [
    "customers.customer.read",
    "customers.customer.write",
    "customers.portal_access.read",
    "customers.portal_access.write",
  ],
  dispatcher: ["customers.customer.read"],
  accounting: ["customers.customer.read"],
  controller_qm: ["customers.customer.read"],
  customer_user: [],
  subcontractor_user: [],
};

export const CUSTOMER_DETAIL_TAB_ORDER = [
  "dashboard",
  "overview",
  "contact_access",
  "commercial",
  "orders",
  "history",
  "employee_blocks",
];

const CUSTOMER_DETAIL_TAB_ALIASES = {
  addresses: "contact_access",
  contacts: "contact_access",
  plans: "orders",
  portal: "contact_access",
};

export const CUSTOMER_COMMERCIAL_TAB_ORDER = [
  "billing_profile",
  "invoice_parties",
  "pricing_rules",
];

export const CUSTOMER_PRICING_RULES_TAB_ORDER = [
  "rate_cards",
  "rate_lines",
  "surcharges",
];

export const CUSTOMER_OVERVIEW_SECTION_ORDER = [
  "master_data",
  "contacts",
  "addresses",
  "portal_access",
  "billing_profile",
  "invoice_parties",
  "rate_cards",
  "rate_lines",
  "surcharges",
  "orders",
  "history",
  "employee_blocks",
];

const CUSTOMER_OVERVIEW_SECTION_LABEL_KEYS = {
  addresses: "customerAdmin.contactAccess.addressesTitle",
  billing_profile: "customerAdmin.commercial.billingTitle",
  contacts: "customerAdmin.contactAccess.contactsTitle",
  employee_blocks: "customerAdmin.tabs.employeeBlocks",
  history: "customerAdmin.tabs.history",
  invoice_parties: "customerAdmin.commercial.invoiceTitle",
  master_data: "customerAdmin.tabs.overview",
  orders: "customerAdmin.tabs.orders",
  portal_access: "customerAdmin.contactAccess.portalTitle",
  rate_cards: "customerAdmin.commercial.rateCardsTitle",
  rate_lines: "customerAdmin.commercial.rateLinesTitle",
  surcharges: "customerAdmin.commercial.surchargesTitle",
};

const CUSTOMER_OVERVIEW_SECTION_ICONS = {
  addresses: "lucide:map-pin",
  billing_profile: "lucide:receipt-text",
  commercial: "lucide:badge-euro",
  contacts: "lucide:contact-round",
  contacts_access: "lucide:users-round",
  employee_blocks: "lucide:user-round-x",
  history: "lucide:history",
  invoice_parties: "lucide:file-text",
  master_data: "lucide:layout-dashboard",
  orders: "lucide:clipboard-list",
  portal_access: "lucide:key-round",
  pricing_rules: "lucide:calculator",
  rate_cards: "lucide:badge-cent",
  rate_lines: "lucide:list",
  surcharges: "lucide:percent",
};

const CUSTOMER_OVERVIEW_SECTION_TEST_IDS = {
  addresses: "customer-overview-nav-addresses",
  billing_profile: "customer-overview-nav-billing-profile",
  contacts: "customer-overview-nav-contacts",
  employee_blocks: "customer-overview-nav-employee-blocks",
  history: "customer-overview-nav-history",
  invoice_parties: "customer-overview-nav-invoice-parties",
  master_data: "customer-overview-nav-master-data",
  orders: "customer-overview-nav-orders",
  portal_access: "customer-overview-nav-portal-access",
  rate_cards: "customer-overview-nav-rate-cards",
  rate_lines: "customer-overview-nav-rate-lines",
  surcharges: "customer-overview-nav-surcharges",
};

const CUSTOMER_ROUTE_TAB_TO_OVERVIEW_SECTION = {
  addresses: "addresses",
  commercial: "billing_profile",
  contact_access: "contacts",
  contacts: "contacts",
  dashboard: "master_data",
  employee_blocks: "employee_blocks",
  history: "history",
  orders: "orders",
  overview: "master_data",
  plans: "orders",
  portal: "portal_access",
  rate_cards: "rate_cards",
  rate_lines: "rate_lines",
  surcharges: "surcharges",
};

export function hasCustomerPermission(role, permissionKey) {
  return (CUSTOMER_PERMISSION_MATRIX[role] ?? []).includes(permissionKey);
}

export function resolveCustomerAdminSectionVisibility({ effectiveRole, embedded = false }) {
  const isTenantAdminEmbedded = embedded && effectiveRole === "tenant_admin";

  return {
    showGovernanceHero: !isTenantAdminEmbedded,
  };
}

export function resolveCustomerAdminSessionScope({
  effectiveRole,
  effectiveTenantScopeId,
}) {
  const tenantScopeId = typeof effectiveTenantScopeId === "string" ? effectiveTenantScopeId.trim() : "";
  if (effectiveRole === "tenant_admin" || effectiveRole === "dispatcher" || effectiveRole === "accounting" || effectiveRole === "controller_qm") {
    return {
      tenantScopeId,
    };
  }

  return {
    tenantScopeId,
  };
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

export function formatCustomerReferenceOptionLabel(record) {
  if (!record) {
    return "";
  }

  if ("name" in record && record.name) {
    return record.name;
  }

  if ("label" in record && record.label) {
    return record.label;
  }

  return record.code ?? "";
}

export function formatCustomerReferenceDisplayLabel(record) {
  if (!record) {
    return "";
  }

  if ("name" in record && record.name) {
    return [record.code, record.name].filter(Boolean).join(" - ");
  }

  return [record.code, record.label].filter(Boolean).join(" - ");
}

export function filterCustomerMandatesByBranch(mandates, branchId) {
  const normalizedBranchId = typeof branchId === "string" ? branchId.trim() : "";
  if (!normalizedBranchId) {
    return [...(mandates ?? [])];
  }
  return (mandates ?? []).filter((mandate) => mandate.branch_id === normalizedBranchId);
}

export function buildCustomerReferenceMaps(referenceData) {
  const buildMap = (items) => new Map((items ?? []).map((item) => [item.id, formatCustomerReferenceDisplayLabel(item)]));

  return {
    legalForms: buildMap(referenceData?.legal_forms),
    classifications: buildMap(referenceData?.classifications),
    rankings: buildMap(referenceData?.rankings),
    customerStatuses: buildMap(referenceData?.customer_statuses),
    branches: buildMap(referenceData?.branches),
    mandates: buildMap(referenceData?.mandates),
  };
}

export function buildCustomerDraftPayload(draft, { allowedBranchIds = null, allowedMandateIds = null } = {}) {
  const emptyToNull = (value) => {
    if (typeof value !== "string") {
      return value ?? null;
    }
    const trimmed = value.trim();
    return trimmed.length > 0 ? trimmed : null;
  };
  const normalizeReference = (value, allowedIds) => {
    const normalized = emptyToNull(value);
    if (normalized == null) {
      return null;
    }
    if (Array.isArray(allowedIds)) {
      return allowedIds.includes(normalized) ? normalized : null;
    }
    return normalized;
  };

  return {
    tenant_id: draft.tenant_id,
    customer_number: draft.customer_number.trim(),
    name: draft.name.trim(),
    status: emptyToNull(draft.status) ?? "active",
    legal_name: emptyToNull(draft.legal_name),
    external_ref: emptyToNull(draft.external_ref),
    legal_form_lookup_id: emptyToNull(draft.legal_form_lookup_id),
    classification_lookup_id: emptyToNull(draft.classification_lookup_id),
    ranking_lookup_id: emptyToNull(draft.ranking_lookup_id),
    customer_status_lookup_id: emptyToNull(draft.customer_status_lookup_id),
    default_branch_id: normalizeReference(draft.default_branch_id, allowedBranchIds),
    default_mandate_id: normalizeReference(draft.default_mandate_id, allowedMandateIds),
    notes: emptyToNull(draft.notes),
  };
}

export function resolveCustomerCancelSelection(previousSelectedCustomer) {
  return previousSelectedCustomer
    ? { isCreatingCustomer: false, selectedCustomerId: previousSelectedCustomer.id, selectedCustomer: previousSelectedCustomer }
    : { isCreatingCustomer: false, selectedCustomerId: "", selectedCustomer: null };
}

export function buildCustomerDetailTabs({ canReadCommercial, canReadOrders, hasSelectedCustomer, isCreatingCustomer }) {
  if (isCreatingCustomer) {
    return ["overview"];
  }

  if (!hasSelectedCustomer) {
    return [];
  }

  return CUSTOMER_DETAIL_TAB_ORDER.filter((tabId) => {
    if (tabId === "commercial") {
      return !!canReadCommercial;
    }
    if (tabId === "orders") {
      return !!canReadOrders;
    }
    return true;
  });
}

export function buildCustomerOverviewSections({
  canReadCommercial,
  canReadOrders,
  canSeeEmployeeBlocks,
  canSeeHistory,
  hasRateCards,
  isCreatingCustomer,
  selectedCustomer,
} = {}) {
  const hasSelectedCustomer = !!selectedCustomer;
  const showDetailSections = hasSelectedCustomer && !isCreatingCustomer;

  const overviewSection = {
    children: [
      {
        groupId: "overview",
        icon: CUSTOMER_OVERVIEW_SECTION_ICONS.master_data,
        id: "master_data",
        labelKey: CUSTOMER_OVERVIEW_SECTION_LABEL_KEYS.master_data,
        testId: CUSTOMER_OVERVIEW_SECTION_TEST_IDS.master_data,
        visible: true,
      },
    ],
    icon: CUSTOMER_OVERVIEW_SECTION_ICONS.master_data,
    id: "overview",
    labelKey: "customerAdmin.tabs.overview",
    visible: true,
  };

  const contactsAccessGroup = {
    children: [
      {
        groupId: "contacts_access",
        icon: CUSTOMER_OVERVIEW_SECTION_ICONS.contacts,
        id: "contacts",
        labelKey: CUSTOMER_OVERVIEW_SECTION_LABEL_KEYS.contacts,
        testId: CUSTOMER_OVERVIEW_SECTION_TEST_IDS.contacts,
        visible: showDetailSections,
      },
      {
        groupId: "contacts_access",
        icon: CUSTOMER_OVERVIEW_SECTION_ICONS.addresses,
        id: "addresses",
        labelKey: CUSTOMER_OVERVIEW_SECTION_LABEL_KEYS.addresses,
        testId: CUSTOMER_OVERVIEW_SECTION_TEST_IDS.addresses,
        visible: showDetailSections,
      },
      {
        groupId: "contacts_access",
        icon: CUSTOMER_OVERVIEW_SECTION_ICONS.portal_access,
        id: "portal_access",
        labelKey: CUSTOMER_OVERVIEW_SECTION_LABEL_KEYS.portal_access,
        testId: CUSTOMER_OVERVIEW_SECTION_TEST_IDS.portal_access,
        visible: showDetailSections,
      },
    ],
    icon: CUSTOMER_OVERVIEW_SECTION_ICONS.contacts_access,
    id: "contacts_access",
    labelKey: "customerAdmin.tabs.contactAccess",
    visible: showDetailSections,
  };

  const commercialGroup = {
    children: [
      {
        groupId: "commercial",
        icon: CUSTOMER_OVERVIEW_SECTION_ICONS.billing_profile,
        id: "billing_profile",
        labelKey: CUSTOMER_OVERVIEW_SECTION_LABEL_KEYS.billing_profile,
        testId: CUSTOMER_OVERVIEW_SECTION_TEST_IDS.billing_profile,
        visible: showDetailSections && !!canReadCommercial,
      },
      {
        groupId: "commercial",
        icon: CUSTOMER_OVERVIEW_SECTION_ICONS.invoice_parties,
        id: "invoice_parties",
        labelKey: CUSTOMER_OVERVIEW_SECTION_LABEL_KEYS.invoice_parties,
        testId: CUSTOMER_OVERVIEW_SECTION_TEST_IDS.invoice_parties,
        visible: showDetailSections && !!canReadCommercial,
      },
      {
        children: [
          {
            groupId: "pricing_rules",
            icon: CUSTOMER_OVERVIEW_SECTION_ICONS.rate_cards,
            id: "rate_cards",
            labelKey: CUSTOMER_OVERVIEW_SECTION_LABEL_KEYS.rate_cards,
            testId: CUSTOMER_OVERVIEW_SECTION_TEST_IDS.rate_cards,
            visible: showDetailSections && !!canReadCommercial,
          },
          {
            groupId: "pricing_rules",
            icon: CUSTOMER_OVERVIEW_SECTION_ICONS.rate_lines,
            id: "rate_lines",
            labelKey: CUSTOMER_OVERVIEW_SECTION_LABEL_KEYS.rate_lines,
            testId: CUSTOMER_OVERVIEW_SECTION_TEST_IDS.rate_lines,
            visible: showDetailSections && !!canReadCommercial && !!hasRateCards,
          },
          {
            groupId: "pricing_rules",
            icon: CUSTOMER_OVERVIEW_SECTION_ICONS.surcharges,
            id: "surcharges",
            labelKey: CUSTOMER_OVERVIEW_SECTION_LABEL_KEYS.surcharges,
            testId: CUSTOMER_OVERVIEW_SECTION_TEST_IDS.surcharges,
            visible: showDetailSections && !!canReadCommercial && !!hasRateCards,
          },
        ],
        icon: CUSTOMER_OVERVIEW_SECTION_ICONS.pricing_rules,
        id: "pricing_rules",
        labelKey: "customerAdmin.commercial.tabs.pricingRules",
        visible: showDetailSections && !!canReadCommercial,
      },
    ],
    icon: CUSTOMER_OVERVIEW_SECTION_ICONS.commercial,
    id: "commercial",
    labelKey: "customerAdmin.tabs.commercial",
    visible: showDetailSections && !!canReadCommercial,
  };

  const standaloneSections = [
    {
      icon: CUSTOMER_OVERVIEW_SECTION_ICONS.orders,
      id: "orders",
      labelKey: CUSTOMER_OVERVIEW_SECTION_LABEL_KEYS.orders,
      testId: CUSTOMER_OVERVIEW_SECTION_TEST_IDS.orders,
      visible: showDetailSections && !!canReadOrders,
    },
    {
      icon: CUSTOMER_OVERVIEW_SECTION_ICONS.history,
      id: "history",
      labelKey: CUSTOMER_OVERVIEW_SECTION_LABEL_KEYS.history,
      testId: CUSTOMER_OVERVIEW_SECTION_TEST_IDS.history,
      visible: showDetailSections && !!canSeeHistory,
    },
    {
      icon: CUSTOMER_OVERVIEW_SECTION_ICONS.employee_blocks,
      id: "employee_blocks",
      labelKey: CUSTOMER_OVERVIEW_SECTION_LABEL_KEYS.employee_blocks,
      testId: CUSTOMER_OVERVIEW_SECTION_TEST_IDS.employee_blocks,
      visible: showDetailSections && !!canSeeEmployeeBlocks,
    },
  ];

  return [overviewSection, contactsAccessGroup, commercialGroup, ...standaloneSections];
}

export function normalizeCustomerDetailTab(activeTab, options) {
  const tabs = buildCustomerDetailTabs(options);
  if (!tabs.length) {
    return "";
  }

  const normalizedTab = CUSTOMER_DETAIL_TAB_ALIASES[activeTab] ?? activeTab;

  return tabs.includes(normalizedTab) ? normalizedTab : (options?.isCreatingCustomer ? "overview" : "dashboard");
}

export function resolveCustomerOverviewSectionId(activeTab, { hasRateCards } = {}) {
  const normalizedTab = CUSTOMER_ROUTE_TAB_TO_OVERVIEW_SECTION[activeTab] ? activeTab : (CUSTOMER_DETAIL_TAB_ALIASES[activeTab] ?? activeTab);
  const rawSectionId = CUSTOMER_ROUTE_TAB_TO_OVERVIEW_SECTION[normalizedTab] ?? "master_data";
  if ((rawSectionId === "rate_lines" || rawSectionId === "surcharges") && !hasRateCards) {
    return "rate_cards";
  }
  return rawSectionId;
}

export function normalizeCustomerCommercialTab(activeTab) {
  return CUSTOMER_COMMERCIAL_TAB_ORDER.includes(activeTab) ? activeTab : "billing_profile";
}

export function buildCustomerPricingRulesTabs({ hasRateCards }) {
  return hasRateCards ? [...CUSTOMER_PRICING_RULES_TAB_ORDER] : ["rate_cards"];
}

export function normalizeCustomerPricingRulesTab(activeTab, { hasRateCards }) {
  const tabs = buildCustomerPricingRulesTabs({ hasRateCards });
  return tabs.includes(activeTab) ? activeTab : "rate_cards";
}

export function resolveCustomerSelectedRateCardId(activeRateCardId, rateCards) {
  if ((rateCards ?? []).some((row) => row.id === activeRateCardId)) {
    return activeRateCardId;
  }
  return rateCards?.[0]?.id ?? "";
}

export function resolveCustomerAdminRouteContext(query) {
  const normalizeValue = (value) => (typeof value === "string" ? value.trim() : "");
  const detailTab = normalizeValue(query?.tab);

  return {
    customerId: normalizeValue(query?.customer_id),
    detailTab,
  };
}

export function buildCustomerCommercialLocation(customerId = "") {
  const query = { tab: "commercial" };
  if (customerId) {
    query.customer_id = customerId;
  }
  return {
    path: "/admin/customers",
    query,
  };
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
    "errors.customers.customer.invalid_initial_status": "customerAdmin.feedback.invalidInitialStatus",
    "errors.customers.customer.invalid_branch_scope": "customerAdmin.feedback.invalidBranchScope",
    "errors.customers.customer.invalid_mandate_scope": "customerAdmin.feedback.invalidMandateScope",
    "errors.customers.customer.mandate_branch_mismatch": "customerAdmin.feedback.mandateBranchMismatch",
    "errors.customers.contact.stale_version": "customerAdmin.feedback.staleVersion",
    "errors.customers.address_link.stale_version": "customerAdmin.feedback.staleVersion",
    "errors.customers.employee_block.stale_version": "customerAdmin.feedback.staleVersion",
    "errors.customers.contact.duplicate_email": "customerAdmin.feedback.duplicateEmail",
    "errors.customers.contact.primary_conflict": "customerAdmin.feedback.primaryConflict",
    "errors.customers.customer_address.default_conflict": "customerAdmin.feedback.defaultAddressConflict",
    "errors.customers.contact.invalid_user_id_format": "customerAdmin.feedback.invalidPortalUserFormat",
    "errors.customers.contact.invalid_user_scope": "customerAdmin.feedback.invalidPortalUser",
    "errors.customers.portal_access.contact_already_linked": "customerAdmin.feedback.portalAccessAlreadyLinked",
    "errors.customers.portal_access.contact_customer_mismatch": "customerAdmin.feedback.portalAccessContactMismatch",
    "errors.customers.portal.contact_inactive": "customerAdmin.feedback.portalAccessContactInactive",
    "errors.customers.portal.customer_inactive": "customerAdmin.feedback.portalAccessCustomerInactive",
  };

  return messageMap[messageKey] ?? "customerAdmin.feedback.error";
}
