import test from "node:test";
import assert from "node:assert/strict";

import {
  buildCommercialConfirmationKey,
  deriveCustomerCommercialActionState,
  hasCustomerCommercialPermission,
  mapCustomerCommercialApiMessage,
  resolveBillingProfileFeedbackError,
  resolveBillingProfileApiError,
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

test("commercial api message mapping and active-change confirmation are stable", () => {
  assert.equal(
    mapCustomerCommercialApiMessage("errors.customers.rate_card.overlap"),
    "customerAdmin.feedback.rateCardOverlap",
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
