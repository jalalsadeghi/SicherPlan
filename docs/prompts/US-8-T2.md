---
task_id: US-8-T2
story_id: US-8
story_title: "Customer billing profile, rate cards, surcharge rules, and invoice parties"
sprint: Sprint 03
status: ready
owner: "Backend Lead / Finance Lead"
---

# Codex Prompt — US-8-T2

## Task title

**Implement rate cards, rate lines, surcharge rules, and effective-date validation**

## Objective

Build the customer-commercial pricing backbone so SicherPlan can maintain customer-specific rates, pricing dimensions, and surcharge logic over time without overlapping validity windows or hidden duplication in finance.

## Source context

- Updated proposal: section 5.2 commercial and billing profile; Appendix A commercial rules including general rates, function-based rates, surcharge masks, and separate invoice-item support expectations.
- Implementation specification: section 4.3 `crm.customer_rate_card`, `crm.customer_rate_line`, and `crm.customer_surcharge_rule`; section 6 validation guidance; section 3 ownership rule that CRM owns customer commercial settings.
- Sprint reference: `docs/sprint/sprint-03-customer-management.md`.
- Cross-cutting rules: `AGENTS.md`.

## Dependencies

- `US-7-T1` must already provide stable customer ownership and identifiers.
- `US-8-T1` should already establish the commercial-profile context for each customer.
- Be aware that `hr.function_type` and `hr.qualification_type` are introduced later; do not create an incompatible shortcut if those catalogs are not yet present in the repo.

## Scope of work

- Create migrations, models, schemas, services, and APIs for customer rate cards, rate lines, and surcharge rules.
- Support versioned rate cards with `effective_from` / `effective_to`, rate kind, currency, and notes, and prevent overlapping active windows through service validation or a database exclusion strategy that matches repo conventions.
- Support rate lines keyed by pricing dimensions such as function, qualification, planning mode, billing unit, and unit price, with stable uniqueness rules per effective card.
- Support surcharge rules with surcharge type, effective dates, weekday/time masks, region scope, and percentage/fixed amount fields appropriate to the normalized schema.
- Implement pricing validation and lookup/query helpers that later finance logic can consume without moving commercial ownership out of CRM.
- If the later HR catalogs are not yet available in the repository, keep `function_type_id` and `qualification_type_id` nullable or behind a migration-safe seam; do not invent shadow catalogs that will conflict with Sprint 4.
- Add tests for overlapping-window validation, dimension uniqueness, currency/rule validation, and finance-read contract expectations.

## Preferred file targets

- Alembic migration(s) for CRM commercial-rate tables.
- `modules/customers/` or equivalent pricing-domain models, schemas, services, routers, and tests.
- Shared pricing or validation helpers only if they do not break CRM ownership.

## Hard constraints

- Customer commercial rules must remain CRM-owned even though finance will consume them later.
- Do not create a second commercial rule source of truth inside finance or planning.
- Overlapping effective windows for the same active rate-card scope must be prevented deterministically.
- Do not introduce incompatible temporary function/qualification catalogs just to satisfy early references before HR catalogs land.
- Keep money and quantity types aligned with the implementation spec's numeric conventions.
- Avoid vague JSON-only pricing rules when the normalized schema already defines concrete columns.

## Expected implementation outputs

- A versioned customer-pricing model with rate cards, rate lines, and surcharge rules.
- Deterministic effective-date and pricing-dimension validation.
- Stable read/query contracts for later finance pricing resolution.

## Non-goals

- Do not build the customer commercial UI here; that is `US-8-T3`.
- Do not implement invoice layout, Leitweg, dispatch, or dunning configuration here beyond preserving compatibility with `US-8-T4`.
- Do not implement invoice calculation or billing document generation here.

## Verification checklist

- Rate cards cannot overlap incorrectly for the same customer and scope.
- Rate-line uniqueness is enforced for the chosen pricing-dimension tuple.
- Surcharge rules validate date/time masks and amount combinations correctly.
- The implementation does not create future migration debt around function/qualification references.

## Codex response format

- A short implementation plan before touching files.
- A concise list of files created or modified.
- A summary of key design decisions and assumptions.
- Verification evidence: build/lint/test commands and notable outputs.
- Open follow-ups or blockers that should be carried into the next task.

## Codex `/review` prompt

Use this after the implementation for **US-8-T2 — Implement rate cards, rate lines, surcharge rules, and effective-date validation** is finished.

```text
/review Please review the implementation for task US-8-T2 (Implement rate cards, rate lines, surcharge rules, and effective-date validation) against this prompt file and the current repository state.

Review goals:
- Confirm the implementation matches the objective, dependencies, hard constraints, expected outputs, non-goals, and verification checklist in `docs/prompts/US-8-T2.md`.
- Review only the files that are relevant to this task, but also flag any upstream or downstream contract drift caused by the changes.
- Identify correctness, data-model, API-contract, migration, authorization, localization, testing, and maintainability issues.

Task-specific review focus:
- Effective-date and overlap handling are deterministic, test-covered, and realistic for production pricing maintenance.
- CRM remains the single source of customer commercial truth and later finance consumption is read-oriented.
- Function/qualification references are handled in a migration-safe way despite later HR-catalog delivery.
- Pricing rules are normalized and maintainable instead of hidden in opaque JSON blobs.

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
