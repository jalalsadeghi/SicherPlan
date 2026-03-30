import test from "node:test";
import assert from "node:assert/strict";

import {
  applySurchargeAmountMode,
  buildCommercialConfirmationKey,
  buildWeekdayMask,
  COMMON_CURRENCY_OPTIONS,
  deriveCustomerCommercialActionState,
  hasCustomerCommercialPermission,
  mapCustomerCommercialApiMessage,
  minutesToTimeInput,
  normalizeOptionalScalar,
  normalizeRateLinePayloadDraft,
  parseWeekdayMask,
  RATE_LINE_BILLING_UNIT_OPTIONS,
  RATE_LINE_KIND_OPTIONS,
  RATE_LINE_PLANNING_MODE_OPTIONS,
  resolveBillingProfileFeedbackError,
  resolveBillingProfileApiError,
  resolveInvoicePartyApiError,
  resolveSurchargeAmountMode,
  SURCHARGE_TYPE_OPTIONS,
  timeInputToMinutes,
  validateSurchargeRuleAgainstRateCardWindow,
  validateBillingProfileDraft,
  validateRateCardDraft,
  validateRateLineDraft,
  validateSurchargeRuleDraft,
} from "./customerCommercial.helpers.js";

test("accounting has commercial read but not commercial write", () => {
  assert.equal(hasCustomerCommercialPermission("accounting", "customers.billing.read"), true);
  assert.equal(hasCustomerCommercialPermission("accounting", "customers.billing.write"), false);
  assert.equal(deriveCustomerCommercialActionState("tenant_admin").canManageRateCards, true);
  assert.equal(deriveCustomerCommercialActionState("accounting").canManageRateCards, false);
});

test("billing-profile validation enforces tax and bank combinations", () => {
  assert.equal(
    validateBillingProfileDraft({
      invoice_email: "bad",
      payment_terms_days: "",
      tax_exempt: false,
      tax_exemption_reason: "",
      bank_account_holder: "",
      bank_iban: "",
      bank_bic: "",
      bank_name: "",
    }),
    "customerAdmin.feedback.invalidInvoiceEmail",
  );
  assert.equal(
    validateBillingProfileDraft({
      invoice_email: "",
      payment_terms_days: "",
      tax_exempt: true,
      tax_exemption_reason: "",
      e_invoice_enabled: false,
      leitweg_id: "",
      invoice_layout_code: "",
      shipping_method_code: "",
      bank_account_holder: "",
      bank_iban: "",
      bank_bic: "",
      bank_name: "",
    }),
    "customerAdmin.feedback.taxExemptionReasonRequired",
  );
});

test("billing-profile validation enforces advanced invoice configuration combinations", () => {
  assert.equal(
    validateBillingProfileDraft({
      invoice_email: "",
      payment_terms_days: "",
      tax_exempt: false,
      tax_exemption_reason: "",
      e_invoice_enabled: true,
      leitweg_id: "",
      invoice_layout_code: "standard",
      shipping_method_code: "email_pdf",
      bank_account_holder: "",
      bank_iban: "",
      bank_bic: "",
      bank_name: "",
    }),
    "customerAdmin.feedback.eInvoiceDispatchMismatch",
  );
  assert.equal(
    validateBillingProfileDraft({
      invoice_email: "",
      payment_terms_days: "",
      tax_exempt: false,
      tax_exemption_reason: "",
      e_invoice_enabled: true,
      leitweg_id: "",
      invoice_layout_code: "standard",
      shipping_method_code: "e_invoice",
      bank_account_holder: "",
      bank_iban: "",
      bank_bic: "",
      bank_name: "",
    }),
    "customerAdmin.feedback.leitwegRequired",
  );
});

test("rate-card and rate-line validation catches missing fields and invalid values", () => {
  assert.equal(
    validateRateCardDraft({ rate_kind: "", currency_code: "EU", effective_from: "", effective_to: "" }),
    "customerAdmin.feedback.rateKindRequired",
  );
  assert.equal(
    validateRateLineDraft({ line_kind: "base", billing_unit: "hour", unit_price: "-1", minimum_quantity: "" }),
    "customerAdmin.feedback.invalidUnitPrice",
  );
});

test("optional scalar normalization is safe for strings, numbers, and empty values", () => {
  assert.equal(normalizeOptionalScalar("  demo  "), "demo");
  assert.equal(normalizeOptionalScalar(4), "4");
  assert.equal(normalizeOptionalScalar(0), "0");
  assert.equal(normalizeOptionalScalar("   "), null);
  assert.equal(normalizeOptionalScalar(""), null);
  assert.equal(normalizeOptionalScalar(null), null);
  assert.equal(normalizeOptionalScalar(undefined), null);
});

test("rate-line payload normalization accepts numeric minimum quantity without throwing", () => {
  assert.deepEqual(
    normalizeRateLinePayloadDraft(
      {
        line_kind: "function",
        function_type_id: "",
        qualification_type_id: null,
        planning_mode_code: " patrol ",
        billing_unit: "hour",
        unit_price: 19.5,
        minimum_quantity: 4,
        sort_order: 120,
        notes: "  Important  ",
      },
      { tenantId: "tenant-1", rateCardId: "rate-card-1" },
    ),
    {
      tenant_id: "tenant-1",
      rate_card_id: "rate-card-1",
      line_kind: "function",
      function_type_id: null,
      qualification_type_id: null,
      planning_mode_code: "patrol",
      billing_unit: "hour",
      unit_price: "19.5",
      minimum_quantity: "4",
      sort_order: 120,
      notes: "Important",
    },
  );
  assert.deepEqual(
    normalizeRateLinePayloadDraft(
      {
        line_kind: "base",
        function_type_id: "",
        qualification_type_id: "",
        planning_mode_code: "",
        billing_unit: "flat",
        unit_price: "25.00",
        minimum_quantity: "",
        sort_order: "",
        notes: "",
      },
      { tenantId: "tenant-1", rateCardId: "rate-card-1" },
    ),
    {
      tenant_id: "tenant-1",
      rate_card_id: "rate-card-1",
      line_kind: "base",
      function_type_id: null,
      qualification_type_id: null,
      planning_mode_code: null,
      billing_unit: "flat",
      unit_price: "25.00",
      minimum_quantity: null,
      sort_order: 0,
      notes: null,
    },
  );
});

test("pricing rule option constants expose guided select values", () => {
  assert.deepEqual(
    RATE_LINE_KIND_OPTIONS.map((option) => option.value),
    ["base", "function", "qualification", "planning_mode"],
  );
  assert.deepEqual(
    RATE_LINE_BILLING_UNIT_OPTIONS.map((option) => option.value),
    ["hour", "day", "flat"],
  );
  assert.deepEqual(
    RATE_LINE_PLANNING_MODE_OPTIONS.map((option) => option.value),
    ["event", "site", "trade_fair", "patrol"],
  );
  assert.deepEqual(
    SURCHARGE_TYPE_OPTIONS.map((option) => option.value),
    ["night", "weekend", "holiday", "regional"],
  );
  assert.equal(COMMON_CURRENCY_OPTIONS[0]?.value, "EUR");
});

test("surcharge validation enforces mask, ranges, and amount rules", () => {
  assert.equal(
    validateSurchargeRuleDraft({
      surcharge_type: "night",
      effective_from: "2026-01-01",
      effective_to: "2026-01-02",
      weekday_mask: "11x1111",
      time_from_minute: "",
      time_to_minute: "",
      percent_value: "25",
      fixed_amount: "",
      currency_code: "",
    }),
    "customerAdmin.feedback.invalidWeekdayMask",
  );
  assert.equal(
    validateSurchargeRuleDraft({
      surcharge_type: "night",
      effective_from: "2026-01-01",
      effective_to: "",
      weekday_mask: "1111111",
      time_from_minute: 1200,
      time_to_minute: 1000,
      percent_value: "25",
      fixed_amount: "",
      currency_code: "",
    }),
    "customerAdmin.feedback.invalidTimeRange",
  );
});

test("surcharge validation mirrors rate-card date window rules", () => {
  const boundedRateCard = {
    effective_from: "2026-01-01",
    effective_to: "2026-12-31",
  };
  assert.equal(
    validateSurchargeRuleAgainstRateCardWindow(boundedRateCard, {
      effective_from: "2025-12-31",
      effective_to: "2026-12-31",
    }),
    "customerAdmin.feedback.surchargeOutsideRateCardWindow",
  );
  assert.equal(
    validateSurchargeRuleAgainstRateCardWindow(boundedRateCard, {
      effective_from: "2026-01-01",
      effective_to: "",
    }),
    "customerAdmin.feedback.surchargeEffectiveToRequiredForRateCard",
  );
  assert.equal(
    validateSurchargeRuleAgainstRateCardWindow(boundedRateCard, {
      effective_from: "2026-01-01",
      effective_to: "2027-01-01",
    }),
    "customerAdmin.feedback.surchargeOutsideRateCardWindow",
  );
  assert.equal(
    validateSurchargeRuleAgainstRateCardWindow(boundedRateCard, {
      effective_from: "2026-03-01",
      effective_to: "2026-02-01",
    }),
    "customerAdmin.feedback.invalidEffectiveWindow",
  );
  assert.equal(
    validateSurchargeRuleAgainstRateCardWindow(
      { effective_from: "2026-01-01", effective_to: "" },
      {
        effective_from: "2026-03-01",
        effective_to: "",
      },
    ),
    null,
  );
});

test("weekday mask conversion stays compatible with backend bitmask format", () => {
  assert.deepEqual(parseWeekdayMask("1010101"), ["mon", "wed", "fri", "sun"]);
  assert.equal(buildWeekdayMask(["mon", "wed", "fri", "sun"]), "1010101");
  assert.equal(buildWeekdayMask([]), "");
});

test("surcharge time conversion maps HH:mm controls to backend minute integers", () => {
  assert.equal(minutesToTimeInput(0), "00:00");
  assert.equal(minutesToTimeInput(75), "01:15");
  assert.equal(minutesToTimeInput(1440), "23:59");
  assert.equal(timeInputToMinutes("00:00"), 0);
  assert.equal(timeInputToMinutes("13:45"), 825);
  assert.equal(timeInputToMinutes(""), null);
});

test("surcharge amount mode helper keeps percent and fixed modes exclusive", () => {
  assert.equal(resolveSurchargeAmountMode({ percent_value: "25", fixed_amount: "", currency_code: "" }), "percent");
  assert.equal(resolveSurchargeAmountMode({ percent_value: "", fixed_amount: "12.50", currency_code: "eur" }), "fixed");
  assert.deepEqual(
    applySurchargeAmountMode("percent", { percent_value: "25", fixed_amount: "12.50", currency_code: "eur" }, "EUR"),
    {
      percent_value: "25",
      fixed_amount: "",
      currency_code: "",
    },
  );
  assert.deepEqual(
    applySurchargeAmountMode("fixed", { percent_value: "25", fixed_amount: "", currency_code: "" }, "EUR"),
    {
      percent_value: "",
      fixed_amount: "",
      currency_code: "EUR",
    },
  );
});

test("commercial api message mapping and active-change confirmation are stable", () => {
  assert.equal(
    mapCustomerCommercialApiMessage("errors.customers.rate_card.overlap"),
    "customerAdmin.feedback.rateCardOverlap",
  );
  assert.equal(
    mapCustomerCommercialApiMessage("errors.customers.rate_line.invalid_function_type"),
    "customerAdmin.feedback.invalidFunctionType",
  );
  assert.equal(
    mapCustomerCommercialApiMessage("errors.customers.rate_line.invalid_qualification_type"),
    "customerAdmin.feedback.invalidQualificationType",
  );
  assert.equal(buildCommercialConfirmationKey("rateCard", true), "customerAdmin.confirm.activeCommercialChange");
  assert.equal(buildCommercialConfirmationKey("rateCard", false), null);
});

test("billing-profile api errors resolve to field-aware frontend guidance", () => {
  assert.deepEqual(
    resolveBillingProfileApiError("errors.customers.billing_profile.dispatch_email_required"),
    {
      isKnown: true,
      summaryTitleKey: "customerAdmin.feedback.billingProfileSaveFailedTitle",
      summaryBodyKey: "customerAdmin.feedback.billingProfileSaveFailedSummary",
      primaryMessageKey: "customerAdmin.feedback.dispatchEmailRequired",
      fields: ["invoice_email", "shipping_method_code"],
      details: {},
    },
  );
  assert.deepEqual(
    resolveBillingProfileApiError("errors.customers.billing_profile.leitweg_required"),
    {
      isKnown: true,
      summaryTitleKey: "customerAdmin.feedback.billingProfileSaveFailedTitle",
      summaryBodyKey: "customerAdmin.feedback.billingProfileSaveFailedSummary",
      primaryMessageKey: "customerAdmin.feedback.leitwegRequired",
      fields: ["leitweg_id", "shipping_method_code", "e_invoice_enabled"],
      details: {},
    },
  );
  assert.deepEqual(
    resolveBillingProfileApiError(
      "errors.customers.lookup.not_found",
      {},
      "customers.validation.billing_profile_shipping_method",
    ),
    {
      isKnown: true,
      summaryTitleKey: "customerAdmin.feedback.billingProfileSaveFailedTitle",
      summaryBodyKey: "customerAdmin.feedback.billingProfileSaveFailedSummary",
      primaryMessageKey: "customerAdmin.feedback.shippingMethodUnavailable",
      fields: ["shipping_method_code"],
      details: {},
    },
  );
  assert.deepEqual(
    resolveBillingProfileApiError("errors.customers.billing_profile.unknown_rule"),
    {
      isKnown: false,
      summaryTitleKey: "customerAdmin.feedback.billingProfileSaveFailedTitle",
      summaryBodyKey: "customerAdmin.feedback.billingProfileUnexpected",
      primaryMessageKey: null,
      fields: [],
      details: {},
    },
  );
});

test("billing-profile client validation messages resolve to the same field guidance", () => {
  assert.deepEqual(
    resolveBillingProfileFeedbackError("customerAdmin.feedback.eInvoiceDispatchMismatch"),
    {
      isKnown: true,
      summaryTitleKey: "customerAdmin.feedback.billingProfileSaveFailedTitle",
      summaryBodyKey: "customerAdmin.feedback.billingProfileSaveFailedSummary",
      primaryMessageKey: "customerAdmin.feedback.eInvoiceDispatchMismatch",
      fields: ["shipping_method_code", "e_invoice_enabled"],
    },
  );
  assert.deepEqual(
    resolveBillingProfileFeedbackError("customerAdmin.feedback.unknown"),
    {
      isKnown: false,
      summaryTitleKey: "customerAdmin.feedback.billingProfileSaveFailedTitle",
      summaryBodyKey: "customerAdmin.feedback.billingProfileUnexpected",
      primaryMessageKey: null,
      fields: [],
    },
  );
});

test("invoice-party invoice-layout API errors resolve to field-level guidance", () => {
  assert.deepEqual(
    resolveInvoicePartyApiError("errors.customers.invoice_party.invalid_layout_format"),
    {
      isKnown: true,
      summaryTitleKey: "customerAdmin.feedback.invoicePartySaveFailedTitle",
      summaryBodyKey: "customerAdmin.feedback.invoicePartySaveFailedSummary",
      primaryMessageKey: "customerAdmin.feedback.invoicePartyInvalidInvoiceLayout",
      fields: ["invoice_layout_lookup_id"],
      details: {},
    },
  );
  assert.deepEqual(
    resolveInvoicePartyApiError("errors.customers.lookup.not_found", {}, "customers.validation.invoice_party_layout_lookup"),
    {
      isKnown: true,
      summaryTitleKey: "customerAdmin.feedback.invoicePartySaveFailedTitle",
      summaryBodyKey: "customerAdmin.feedback.invoicePartySaveFailedSummary",
      primaryMessageKey: "customerAdmin.feedback.invoiceLayoutUnavailable",
      fields: ["invoice_layout_lookup_id"],
      details: {},
    },
  );
});
