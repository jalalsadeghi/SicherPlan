---
task_id: US-8-T3
story_id: US-8
story_title: "Customer billing profile, rate cards, surcharge rules, and invoice parties"
sprint: Sprint 03
status: ready
owner: "Frontend Lead / Backend Lead / Finance Lead"
---

# Codex Prompt — US-8-T3

## Task title

**Build commercial settings UI with validation and finance read contracts**

## Objective

Provide Vben Admin commercial-settings pages so tenant administrators and accounting users can maintain customer billing profiles, invoice parties, rate cards, and surcharge rules through clear, validated workflows that finance can trust.

## Source context

- Updated proposal: section 4 role model including tenant accounting; section 5.2 commercial and billing profile; Appendix A billing/e-invoicing/commercial rules.
- Implementation specification: section 4.3 customer commercial tables; section 3 ownership rule that CRM owns customer commercial settings and finance reads them; section 2 shared lifecycle/version conventions.
- Sprint reference: `docs/sprint/sprint-03-customer-management.md`.
- Cross-cutting rules: `AGENTS.md`.

## Dependencies

- `US-8-T1` and `US-8-T2` must land first so backend contracts are stable.
- `US-7-T2` should already provide the customer-admin shell and navigation entry points.
- `US-3-T1`, `US-3-T3`, and `US-3-T4` should already provide Vben shell, theme, and localization baselines.

## Scope of work

- Build customer commercial-settings UI pages or tabs for billing profile, invoice parties, rate cards, and surcharge rules using Vben Admin patterns.
- Provide permission-aware create/edit/list flows for tenant administrators and accounting-oriented users, with clear separation between read-only versus editable views.
- Implement validated forms and table/grid editing for effective-date windows, default invoice parties, tax/bank/payment terms, and surcharge/rate structures.
- Support optimistic-lock or stale-data handling, user-friendly validation errors, and explicit confirmation UX for risky changes to active commercial settings.
- Expose or consume stable finance-read contracts so later finance modules can resolve customer commercial rules without screen-scraping or ad hoc APIs.
- Ensure all added UI strings, help text, and validation messages ship in German and English.
- Add frontend tests for permission guards, validation flows, localization, and core commercial-editing scenarios.

## Preferred file targets

- Vben Admin customer-commercial pages, route/menu extensions, API clients, and shared form/grid components.
- Locale resource files for German and English commercial-setting strings.
- Frontend tests around customer commercial settings.

## Hard constraints

- Use Vben Admin conventions; do not introduce a disconnected finance-only UI shell for customer commercial settings.
- Do not let the UI bypass backend version or permission checks for commercial data.
- Tax and bank fields should not be exposed broadly to roles that only need operational customer context.
- Do not implement invoice generation or dispatch execution in the UI here; this task is about configuration and stable read contracts.
- All newly introduced user-facing text must follow the DE-default / EN-secondary rule.

## Expected implementation outputs

- A commercial-settings admin UI for customer billing profiles, invoice parties, rates, and surcharge rules.
- Finance-readable API/client contracts suitable for later billing workflows.
- Frontend validation and permission coverage for commercial settings.

## Non-goals

- Do not implement the advanced e-invoice/dispatch/dunning configuration depth here beyond obvious navigation and data-field compatibility; that is `US-8-T4`.
- Do not implement customer portal pages here.
- Do not compute invoices, receivables, or revenue reports here.

## Verification checklist

- Authorized users can maintain customer commercial settings through the web UI.
- Permission guards and field visibility behave correctly for operational versus accounting-oriented roles.
- Validation catches overlapping effective windows, bad defaults, and missing required commercial fields.
- German is default and English renders correctly for all new commercial UI strings.

## Codex response format

- A short implementation plan before touching files.
- A concise list of files created or modified.
- A summary of key design decisions and assumptions.
- Verification evidence: build/lint/test commands and notable outputs.
- Open follow-ups or blockers that should be carried into the next task.

## Codex `/review` prompt

Use this after the implementation for **US-8-T3 — Build commercial settings UI with validation and finance read contracts** is finished.

```text
/review Please review the implementation for task US-8-T3 (Build commercial settings UI with validation and finance read contracts) against this prompt file and the current repository state.

Review goals:
- Confirm the implementation matches the objective, dependencies, hard constraints, expected outputs, non-goals, and verification checklist in `docs/prompts/US-8-T3.md`.
- Review only the files that are relevant to this task, but also flag any upstream or downstream contract drift caused by the changes.
- Identify correctness, data-model, API-contract, migration, authorization, localization, testing, and maintainability issues.

Task-specific review focus:
- Commercial UI flows match backend contracts cleanly and do not introduce duplicate business logic or hidden write paths.
- Sensitive finance-related fields are not overexposed to roles that should only see operational customer data.
- Vben Admin integration, localization, and validation UX are consistent with the existing shell and platform rules.
- Finance-read contracts remain stable and explicit.

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
