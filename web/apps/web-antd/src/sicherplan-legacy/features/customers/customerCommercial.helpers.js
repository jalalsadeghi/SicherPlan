const CUSTOMER_COMMERCIAL_PERMISSION_MATRIX = {
  platform_admin: ["customers.billing.read", "customers.billing.write"],
  tenant_admin: ["customers.billing.read", "customers.billing.write"],
  dispatcher: [],
  accounting: ["customers.billing.read"],
  controller_qm: [],
  customer_user: [],
  subcontractor_user: [],
};

export function hasCustomerCommercialPermission(role, permissionKey) {
  return (CUSTOMER_COMMERCIAL_PERMISSION_MATRIX[role] ?? []).includes(permissionKey);
}

export function deriveCustomerCommercialActionState(role) {
  const canReadCommercial = hasCustomerCommercialPermission(role, "customers.billing.read");
  const canWriteCommercial = hasCustomerCommercialPermission(role, "customers.billing.write");

  return {
    canReadCommercial,
    canWriteCommercial,
    canManageBillingProfile: canWriteCommercial,
    canManageInvoiceParties: canWriteCommercial,
    canManageRateCards: canWriteCommercial,
    canManageRateLines: canWriteCommercial,
    canManageSurchargeRules: canWriteCommercial,
  };
}

export function validateBillingProfileDraft(draft) {
  if (draft.invoice_email && !draft.invoice_email.includes("@")) {
    return "customerAdmin.feedback.invalidInvoiceEmail";
  }
  if (draft.payment_terms_days !== "" && Number(draft.payment_terms_days) < 0) {
    return "customerAdmin.feedback.invalidPaymentTerms";
  }
  if (draft.tax_exempt && !`${draft.tax_exemption_reason ?? ""}`.trim()) {
    return "customerAdmin.feedback.taxExemptionReasonRequired";
  }
  if (!draft.tax_exempt && `${draft.tax_exemption_reason ?? ""}`.trim()) {
    return "customerAdmin.feedback.taxExemptionReasonForbidden";
  }
  const hasBankData = [draft.bank_account_holder, draft.bank_iban, draft.bank_bic, draft.bank_name].some(
    (value) => `${value ?? ""}`.trim(),
  );
  if (hasBankData && !`${draft.bank_account_holder ?? ""}`.trim()) {
    return "customerAdmin.feedback.bankAccountHolderRequired";
  }
  if (hasBankData && !`${draft.bank_iban ?? ""}`.trim()) {
    return "customerAdmin.feedback.bankIbanRequired";
  }
  const shippingMethodCode = `${draft.shipping_method_code ?? ""}`.trim();
  if (draft.e_invoice_enabled && shippingMethodCode && shippingMethodCode !== "e_invoice") {
    return "customerAdmin.feedback.eInvoiceDispatchMismatch";
  }
  if (shippingMethodCode === "e_invoice" && !draft.e_invoice_enabled) {
    return "customerAdmin.feedback.eInvoiceRequired";
  }
  if (shippingMethodCode === "e_invoice" && !`${draft.leitweg_id ?? ""}`.trim()) {
    return "customerAdmin.feedback.leitwegRequired";
  }
  if (!draft.e_invoice_enabled && `${draft.leitweg_id ?? ""}`.trim()) {
    return "customerAdmin.feedback.leitwegForbidden";
  }
  if (shippingMethodCode === "email_pdf" && !`${draft.invoice_email ?? ""}`.trim()) {
    return "customerAdmin.feedback.dispatchEmailRequired";
  }
  if (shippingMethodCode === "e_invoice" && `${draft.invoice_layout_code ?? ""}`.trim() === "compact") {
    return "customerAdmin.feedback.invoiceLayoutIncompatible";
  }
  return null;
}

export function validateRateCardDraft(draft) {
  if (!`${draft.rate_kind ?? ""}`.trim()) {
    return "customerAdmin.feedback.rateKindRequired";
  }
  if (!/^[A-Za-z]{3}$/.test(`${draft.currency_code ?? ""}`.trim())) {
    return "customerAdmin.feedback.invalidCurrency";
  }
  if (!`${draft.effective_from ?? ""}`.trim()) {
    return "customerAdmin.feedback.rateCardEffectiveFromRequired";
  }
  if (draft.effective_to && draft.effective_to < draft.effective_from) {
    return "customerAdmin.feedback.invalidEffectiveWindow";
  }
  return null;
}

export function validateRateLineDraft(draft) {
  if (!`${draft.line_kind ?? ""}`.trim()) {
    return "customerAdmin.feedback.rateLineKindRequired";
  }
  if (!`${draft.billing_unit ?? ""}`.trim()) {
    return "customerAdmin.feedback.invalidBillingUnit";
  }
  const unitPrice = Number(draft.unit_price);
  if (!Number.isFinite(unitPrice) || unitPrice < 0) {
    return "customerAdmin.feedback.invalidUnitPrice";
  }
  if (`${draft.minimum_quantity ?? ""}`.trim()) {
    const minQty = Number(draft.minimum_quantity);
    if (!Number.isFinite(minQty) || minQty < 0) {
      return "customerAdmin.feedback.invalidMinimumQuantity";
    }
  }
  return null;
}

export function validateSurchargeRuleDraft(draft) {
  if (!`${draft.surcharge_type ?? ""}`.trim()) {
    return "customerAdmin.feedback.surchargeTypeRequired";
  }
  if (!`${draft.effective_from ?? ""}`.trim()) {
    return "customerAdmin.feedback.surchargeEffectiveFromRequired";
  }
  if (draft.effective_to && draft.effective_to < draft.effective_from) {
    return "customerAdmin.feedback.invalidEffectiveWindow";
  }
  if (draft.weekday_mask && !/^[01]{7}$/.test(draft.weekday_mask)) {
    return "customerAdmin.feedback.invalidWeekdayMask";
  }
  const hasTimeFrom = draft.time_from_minute !== "" && draft.time_from_minute !== null && draft.time_from_minute !== undefined;
  const hasTimeTo = draft.time_to_minute !== "" && draft.time_to_minute !== null && draft.time_to_minute !== undefined;
  if (hasTimeFrom !== hasTimeTo) {
    return "customerAdmin.feedback.invalidTimeRange";
  }
  if (hasTimeFrom && hasTimeTo && Number(draft.time_to_minute) <= Number(draft.time_from_minute)) {
    return "customerAdmin.feedback.invalidTimeRange";
  }
  const hasPercent = `${draft.percent_value ?? ""}`.trim() !== "";
  const hasFixed = `${draft.fixed_amount ?? ""}`.trim() !== "";
  if (hasPercent === hasFixed) {
    return "customerAdmin.feedback.invalidAmountCombination";
  }
  if (hasFixed && !/^[A-Za-z]{3}$/.test(`${draft.currency_code ?? ""}`.trim())) {
    return "customerAdmin.feedback.invalidCurrency";
  }
  if (!hasFixed && `${draft.currency_code ?? ""}`.trim()) {
    return "customerAdmin.feedback.invalidCurrency";
  }
  return null;
}

export function buildCommercialConfirmationKey(kind, active) {
  if (!active) {
    return null;
  }
  const map = {
    billingProfile: "customerAdmin.confirm.activeCommercialChange",
    invoiceParty: "customerAdmin.confirm.defaultInvoicePartyChange",
    rateCard: "customerAdmin.confirm.activeCommercialChange",
    rateLine: "customerAdmin.confirm.activeCommercialChange",
    surchargeRule: "customerAdmin.confirm.activeCommercialChange",
  };
  return map[kind] ?? null;
}

export function mapCustomerCommercialApiMessage(messageKey) {
  const messageMap = {
    "errors.customers.billing_profile.invalid_invoice_email": "customerAdmin.feedback.invalidInvoiceEmail",
    "errors.customers.billing_profile.invalid_payment_terms": "customerAdmin.feedback.invalidPaymentTerms",
    "errors.customers.billing_profile.tax_exemption_reason_required": "customerAdmin.feedback.taxExemptionReasonRequired",
    "errors.customers.billing_profile.tax_exemption_reason_forbidden": "customerAdmin.feedback.taxExemptionReasonForbidden",
    "errors.customers.billing_profile.bank_account_holder_required": "customerAdmin.feedback.bankAccountHolderRequired",
    "errors.customers.billing_profile.bank_iban_required": "customerAdmin.feedback.bankIbanRequired",
    "errors.customers.billing_profile.e_invoice_required": "customerAdmin.feedback.eInvoiceRequired",
    "errors.customers.billing_profile.e_invoice_dispatch_mismatch": "customerAdmin.feedback.eInvoiceDispatchMismatch",
    "errors.customers.billing_profile.leitweg_required": "customerAdmin.feedback.leitwegRequired",
    "errors.customers.billing_profile.leitweg_forbidden": "customerAdmin.feedback.leitwegForbidden",
    "errors.customers.billing_profile.dispatch_email_required": "customerAdmin.feedback.dispatchEmailRequired",
    "errors.customers.billing_profile.invoice_layout_incompatible": "customerAdmin.feedback.invoiceLayoutIncompatible",
    "errors.customers.billing_profile.stale_version": "customerAdmin.feedback.staleVersion",
    "errors.customers.invoice_party.default_conflict": "customerAdmin.feedback.defaultInvoicePartyConflict",
    "errors.customers.invoice_party.invalid_invoice_email": "customerAdmin.feedback.invalidInvoiceEmail",
    "errors.customers.invoice_party.stale_version": "customerAdmin.feedback.staleVersion",
    "errors.customers.rate_card.overlap": "customerAdmin.feedback.rateCardOverlap",
    "errors.customers.rate_card.invalid_currency": "customerAdmin.feedback.invalidCurrency",
    "errors.customers.rate_card.invalid_window": "customerAdmin.feedback.invalidEffectiveWindow",
    "errors.customers.rate_card.stale_version": "customerAdmin.feedback.staleVersion",
    "errors.customers.rate_line.duplicate_dimension": "customerAdmin.feedback.duplicateRateDimension",
    "errors.customers.rate_line.invalid_billing_unit": "customerAdmin.feedback.invalidBillingUnit",
    "errors.customers.rate_line.invalid_unit_price": "customerAdmin.feedback.invalidUnitPrice",
    "errors.customers.rate_line.invalid_minimum_quantity": "customerAdmin.feedback.invalidMinimumQuantity",
    "errors.customers.rate_line.stale_version": "customerAdmin.feedback.staleVersion",
    "errors.customers.surcharge_rule.invalid_window": "customerAdmin.feedback.invalidEffectiveWindow",
    "errors.customers.surcharge_rule.invalid_weekday_mask": "customerAdmin.feedback.invalidWeekdayMask",
    "errors.customers.surcharge_rule.invalid_time_range": "customerAdmin.feedback.invalidTimeRange",
    "errors.customers.surcharge_rule.invalid_amount_combination": "customerAdmin.feedback.invalidAmountCombination",
    "errors.customers.surcharge_rule.invalid_currency": "customerAdmin.feedback.invalidCurrency",
    "errors.customers.surcharge_rule.outside_rate_card_window": "customerAdmin.feedback.surchargeOutsideRateCardWindow",
    "errors.customers.surcharge_rule.stale_version": "customerAdmin.feedback.staleVersion",
  };

  return messageMap[messageKey] ?? "customerAdmin.feedback.error";
}

const BILLING_PROFILE_ERROR_CONFIG = [
  {
    apiMessageKey: "errors.customers.billing_profile.invalid_invoice_email",
    feedbackMessageKey: "customerAdmin.feedback.invalidInvoiceEmail",
    fields: ["invoice_email"],
  },
  {
    apiMessageKey: "errors.customers.billing_profile.invalid_payment_terms",
    feedbackMessageKey: "customerAdmin.feedback.invalidPaymentTerms",
    fields: ["payment_terms_days"],
  },
  {
    apiMessageKey: "errors.customers.billing_profile.tax_exemption_reason_required",
    feedbackMessageKey: "customerAdmin.feedback.taxExemptionReasonRequired",
    fields: ["tax_exempt", "tax_exemption_reason"],
  },
  {
    apiMessageKey: "errors.customers.billing_profile.tax_exemption_reason_forbidden",
    feedbackMessageKey: "customerAdmin.feedback.taxExemptionReasonForbidden",
    fields: ["tax_exempt", "tax_exemption_reason"],
  },
  {
    apiMessageKey: "errors.customers.billing_profile.bank_account_holder_required",
    feedbackMessageKey: "customerAdmin.feedback.bankAccountHolderRequired",
    fields: ["bank_account_holder", "bank_iban", "bank_bic", "bank_name"],
  },
  {
    apiMessageKey: "errors.customers.billing_profile.bank_iban_required",
    feedbackMessageKey: "customerAdmin.feedback.bankIbanRequired",
    fields: ["bank_iban", "bank_account_holder", "bank_bic", "bank_name"],
  },
  {
    apiMessageKey: "errors.customers.billing_profile.e_invoice_required",
    feedbackMessageKey: "customerAdmin.feedback.eInvoiceRequired",
    fields: ["shipping_method_code", "e_invoice_enabled"],
  },
  {
    apiMessageKey: "errors.customers.billing_profile.e_invoice_dispatch_mismatch",
    feedbackMessageKey: "customerAdmin.feedback.eInvoiceDispatchMismatch",
    fields: ["shipping_method_code", "e_invoice_enabled"],
  },
  {
    apiMessageKey: "errors.customers.billing_profile.leitweg_required",
    feedbackMessageKey: "customerAdmin.feedback.leitwegRequired",
    fields: ["leitweg_id", "shipping_method_code", "e_invoice_enabled"],
  },
  {
    apiMessageKey: "errors.customers.billing_profile.leitweg_forbidden",
    feedbackMessageKey: "customerAdmin.feedback.leitwegForbidden",
    fields: ["leitweg_id", "shipping_method_code", "e_invoice_enabled"],
  },
  {
    apiMessageKey: "errors.customers.billing_profile.dispatch_email_required",
    feedbackMessageKey: "customerAdmin.feedback.dispatchEmailRequired",
    fields: ["invoice_email", "shipping_method_code"],
  },
  {
    apiMessageKey: "errors.customers.billing_profile.invoice_layout_incompatible",
    feedbackMessageKey: "customerAdmin.feedback.invoiceLayoutIncompatible",
    fields: ["invoice_layout_code", "shipping_method_code", "e_invoice_enabled"],
  },
];

export function resolveBillingProfileApiError(messageKey, details = {}, errorCode = "") {
  if (messageKey === "errors.customers.lookup.not_found") {
    const lookupErrorMap = {
      "customers.validation.billing_profile_invoice_layout": {
        messageKey: "customerAdmin.feedback.invoiceLayoutUnavailable",
        fields: ["invoice_layout_code"],
      },
      "customers.validation.billing_profile_shipping_method": {
        messageKey: "customerAdmin.feedback.shippingMethodUnavailable",
        fields: ["shipping_method_code"],
      },
      "customers.validation.billing_profile_dunning_policy": {
        messageKey: "customerAdmin.feedback.dunningPolicyUnavailable",
        fields: ["dunning_policy_code"],
      },
    };
    const lookupResolution = lookupErrorMap[errorCode];
    if (lookupResolution) {
      return {
        isKnown: true,
        summaryTitleKey: "customerAdmin.feedback.billingProfileSaveFailedTitle",
        summaryBodyKey: "customerAdmin.feedback.billingProfileSaveFailedSummary",
        primaryMessageKey: lookupResolution.messageKey,
        fields: lookupResolution.fields,
        details,
      };
    }
  }
  const resolved = BILLING_PROFILE_ERROR_CONFIG.find((entry) => entry.apiMessageKey === messageKey);
  if (resolved) {
    return {
      isKnown: true,
      summaryTitleKey: "customerAdmin.feedback.billingProfileSaveFailedTitle",
      summaryBodyKey: "customerAdmin.feedback.billingProfileSaveFailedSummary",
      primaryMessageKey: resolved.feedbackMessageKey,
      fields: resolved.fields,
      details,
    };
  }

  return {
    isKnown: false,
    summaryTitleKey: "customerAdmin.feedback.billingProfileSaveFailedTitle",
    summaryBodyKey: "customerAdmin.feedback.billingProfileUnexpected",
    primaryMessageKey: null,
    fields: [],
    details,
  };
}

export function resolveBillingProfileFeedbackError(messageKey) {
  const resolved = BILLING_PROFILE_ERROR_CONFIG.find((entry) => entry.feedbackMessageKey === messageKey);
  if (resolved) {
    return {
      isKnown: true,
      summaryTitleKey: "customerAdmin.feedback.billingProfileSaveFailedTitle",
      summaryBodyKey: "customerAdmin.feedback.billingProfileSaveFailedSummary",
      primaryMessageKey: resolved.feedbackMessageKey,
      fields: resolved.fields,
    };
  }
  return {
    isKnown: false,
    summaryTitleKey: "customerAdmin.feedback.billingProfileSaveFailedTitle",
    summaryBodyKey: "customerAdmin.feedback.billingProfileUnexpected",
    primaryMessageKey: null,
    fields: [],
  };
}

export function resolveInvoicePartyApiError(messageKey, details = {}, errorCode = "") {
  if (messageKey === "errors.customers.lookup.not_found" && errorCode === "customers.validation.invoice_party_layout_lookup") {
    return {
      isKnown: true,
      summaryTitleKey: "customerAdmin.feedback.invoicePartySaveFailedTitle",
      summaryBodyKey: "customerAdmin.feedback.invoicePartySaveFailedSummary",
      primaryMessageKey: "customerAdmin.feedback.invoiceLayoutUnavailable",
      fields: ["invoice_layout_lookup_id"],
      details,
    };
  }
  const directMap = {
    "errors.customers.invoice_party.invalid_layout_format": "customerAdmin.feedback.invoicePartyInvalidInvoiceLayout",
    "errors.customers.lookup.invalid_domain": "customerAdmin.feedback.invoicePartyInvalidInvoiceLayout",
    "errors.customers.lookup.scope_mismatch": "customerAdmin.feedback.invoicePartyInvalidInvoiceLayout",
  };
  const resolvedMessage = directMap[messageKey];
  if (resolvedMessage) {
    return {
      isKnown: true,
      summaryTitleKey: "customerAdmin.feedback.invoicePartySaveFailedTitle",
      summaryBodyKey: "customerAdmin.feedback.invoicePartySaveFailedSummary",
      primaryMessageKey: resolvedMessage,
      fields: ["invoice_layout_lookup_id"],
      details,
    };
  }
  return {
    isKnown: false,
    summaryTitleKey: "customerAdmin.feedback.invoicePartySaveFailedTitle",
    summaryBodyKey: "customerAdmin.feedback.invoicePartyUnexpected",
    primaryMessageKey: null,
    fields: [],
    details,
  };
}
