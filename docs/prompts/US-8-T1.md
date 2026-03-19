---
task_id: US-8-T1
story_id: US-8
story_title: "Customer billing profile, rate cards, surcharge rules, and invoice parties"
sprint: Sprint 03
status: ready
owner: "Backend Lead / Finance Lead"
---

# Codex Prompt — US-8-T1

## Task title

**Implement customer billing profile, invoice parties, and payment/tax/bank fields**

## Objective

Create the CRM-owned commercial profile for each customer so finance-facing billing defaults, invoice-party routing, and payment/tax/bank data can be maintained centrally without duplicating commercial truth in the finance module.

## Source context

- Updated proposal: section 5.2 commercial and billing profile; Appendix A billing, e-invoicing, tax, banking, and terms data groups.
- Implementation specification: section 4.3 `crm.customer_billing_profile` and `crm.customer_invoice_party`; section 3 service ownership rule that CRM owns customer commercial settings while finance reads them.
- Sprint reference: `docs/sprint/sprint-03-customer-management.md`.
- Cross-cutting rules: `AGENTS.md`.

## Dependencies

- `US-7-T1` must already provide the customer aggregate and stable customer identifiers.
- `US-4-T1` should already provide lookup foundations used by invoice layout, shipping method, and related commercial codes.
- Finance readers are later consumers, but this task should not wait for finance tables to establish the CRM source of truth.

## Scope of work

- Create migrations, models, schemas, services, and APIs for `crm.customer_billing_profile` and `crm.customer_invoice_party`.
- Support one-to-one billing profiles per customer with invoice email, payment terms, tax number, VAT ID, tax-exempt flag, bank details, and related contract/billing fields that belong in the commercial profile.
- Support one or more alternative invoice parties per customer, including company/contact name, linked address, invoice email where needed, invoice layout override, and a single default invoice party.
- Implement tenant-safe validation for the one-profile-per-customer rule, one-default-invoice-party rule, required-field combinations, and optimistic-lock handling where the repo uses `version_no`.
- Expose backend contracts that later finance services can consume read-only when generating invoices or dispatch decisions.
- Preserve clean seams for advanced invoice-layout, e-invoice, Leitweg, dispatch, and dunning logic that will deepen in `US-8-T4`.
- Add tests covering CRUD, default selection, address linkage, and finance-read contract stability.

## Preferred file targets

- Alembic migration(s) for the CRM commercial-profile tables.
- `modules/customers/` or equivalent commercial-profile models, schemas, services, routers, and tests.
- Shared address integration only where necessary for invoice-party address linkage.

## Hard constraints

- CRM remains the write owner of customer commercial settings; finance may read but must not redefine this truth here.
- Do not implement invoice generation or accounts-receivable workflows in this task.
- Keep tax and bank data protected by least-privilege backend access rules and audit seams.
- Do not collapse alternative invoice parties into a loose JSON blob; preserve normalized invoice-party rows.
- Advanced e-invoice, Leitweg, dispatch, and dunning behavior should remain a clean extension seam for `US-8-T4`, not a half-implemented side path.

## Expected implementation outputs

- Normalized CRM billing-profile and invoice-party persistence with stable APIs.
- Validated payment/tax/bank and invoice-party data contracts ready for later finance consumption.
- Automated tests covering profile ownership, invoice-party defaults, and address linkage.

## Non-goals

- Do not implement rate cards or surcharge rules here; that is `US-8-T2`.
- Do not build the admin UI here; that is `US-8-T3`.
- Do not implement real invoice dispatch or dunning execution here; that is outside Sprint 3 and beyond `US-8-T4` configuration support.

## Verification checklist

- Each customer can hold exactly one billing profile and multiple invoice parties with only one default invoice party.
- Payment/tax/bank fields persist and validate correctly without leaking across tenants.
- Invoice-party addresses link through `common.address` instead of duplicating postal truth.
- Finance-facing read contracts can obtain the commercial profile without mutating it.

## Codex response format

- A short implementation plan before touching files.
- A concise list of files created or modified.
- A summary of key design decisions and assumptions.
- Verification evidence: build/lint/test commands and notable outputs.
- Open follow-ups or blockers that should be carried into the next task.

## Codex `/review` prompt

Use this after the implementation for **US-8-T1 — Implement customer billing profile, invoice parties, and payment/tax/bank fields** is finished.

```text
/review Please review the implementation for task US-8-T1 (Implement customer billing profile, invoice parties, and payment/tax/bank fields) against this prompt file and the current repository state.

Review goals:
- Confirm the implementation matches the objective, dependencies, hard constraints, expected outputs, non-goals, and verification checklist in `docs/prompts/US-8-T1.md`.
- Review only the files that are relevant to this task, but also flag any upstream or downstream contract drift caused by the changes.
- Identify correctness, data-model, API-contract, migration, authorization, localization, testing, and maintainability issues.

Task-specific review focus:
- CRM retains ownership of commercial settings and finance-facing contracts are read-only and stable.
- Invoice-party normalization and default-selection rules are correct and migration-safe.
- Sensitive tax/bank data is protected appropriately and not overexposed in generic list APIs.
- The design leaves a clean seam for `US-8-T4` instead of entangling advanced dispatch/e-invoice logic prematurely.

Required review output:
1. Blocking issues
2. Major issues
3. Minor issues
4. Nice-to-have improvements
5. Final verdict: `approved`, `approved with minor issues`, or `changes required`

Additional instructions:
- Be strict about tenant isolation, role scoping, auditability, DE default / EN secondary behavior, and traceability to US-8.
- Call out missing tests, weak assertions, incorrect acceptance coverage, schema drift, unsafe defaults, or assumptions that are not grounded in the proposal or implementation data model.
- If no real issue exists, say so clearly and do not invent problems.
```
