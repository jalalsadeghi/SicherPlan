---
task_id: US-8-T4
story_id: US-8
story_title: "Customer billing profile, rate cards, surcharge rules, and invoice parties"
sprint: Sprint 03
status: ready
owner: "Backend Lead / Frontend Lead / Finance Lead"
---

# Codex Prompt — US-8-T4

## Task title

**Support invoice layout, e-invoice, Leitweg, dispatch, and dunning configuration**

## Objective

Complete the advanced customer invoice-configuration layer so invoice layout choices, e-invoice readiness, dispatch controls, and dunning-policy settings are represented explicitly and can feed later finance delivery flows without schema rework.

## Source context

- Updated proposal: section 5.2 commercial and billing profile; Appendix A billing and e-invoicing data group including invoice layouts, e-invoice toggle, Leitweg ID, dispatch control, and dunning overview.
- Implementation specification: section 4.3 `crm.customer_billing_profile` fields for `e_invoice_enabled`, `leitweg_id`, `invoice_layout_code`, `shipping_method_code`, and `dunning_policy_code`; lookup ownership rules in section 4.1.
- Sprint reference: `docs/sprint/sprint-03-customer-management.md`.
- Cross-cutting rules: `AGENTS.md`.

## Dependencies

- `US-8-T1` should already persist the base billing profile and invoice-party structures.
- `US-8-T3` should already provide the commercial-settings UI scaffolding.
- `US-6-T2` and `US-6-T4` provide future communication/integration seams that dispatch-related configuration must remain compatible with.

## Scope of work

- Implement the specialized configuration behavior, validation rules, and UI/API support for invoice layout selection, e-invoice enablement, Leitweg-style routing fields, dispatch/shipping methods, and dunning-policy settings.
- Use lookup-backed or otherwise controlled dictionaries for invoice layouts, shipping methods, and dunning policies rather than uncontrolled free text where the spec already points to code-backed values.
- Define required-field combinations and validation behavior for configuration states such as e-invoice enabled versus standard email/postal dispatch modes, without overcommitting to provider-specific execution details too early.
- Ensure invoice-party and billing-profile data interact cleanly with dispatch preferences and default layout choices.
- Add tests that prove configuration combinations validate correctly and remain consumable by later finance, communication, and integration workflows.
- If the repository already exposes finance-read DTOs, extend them in a backward-compatible way so advanced invoice configuration is visible without rewriting contracts later.

## Preferred file targets

- Customer commercial-profile services and schemas under `modules/customers/` or equivalent.
- Lookup integration under shared core helpers where needed for layout/shipping/dunning codes.
- Vben Admin commercial-settings pages/components that present the new configuration fields and validations.
- Backend and frontend tests for configuration combinations.

## Hard constraints

- This task is about configuration, validation, and stable contracts; do not implement full invoice dispatch execution or dunning runs here.
- Do not hardcode provider-specific transport logic into the CRM customer module.
- Configuration must remain readable by later finance and communication modules without creating hidden cross-module writes.
- Avoid shallow free-text fields for options that should be lookup- or code-backed according to the implementation spec.
- Do not make customer-commercial configuration dependent on operational planning data.

## Expected implementation outputs

- Advanced invoice-configuration support for layouts, e-invoice readiness, dispatch preferences, and dunning policies.
- Backward-compatible API/UI contracts that later finance workflows can consume.
- Validation coverage for realistic commercial-configuration combinations.

## Non-goals

- Do not generate, send, or collect invoices here.
- Do not implement jurisdiction-specific finance engines beyond the configuration fields already grounded in the proposal/spec.
- Do not bypass the shared communication/integration backbones for future dispatch paths.

## Verification checklist

- Invoice-configuration fields persist cleanly and validate required combinations.
- Lookup-backed codes for layout/shipping/dunning remain stable and tenant-safe.
- Advanced invoice configuration is visible through stable read contracts without breaking earlier consumers.
- UI and API behavior stay aligned for layout/e-invoice/dispatch/dunning configuration.

## Codex response format

- A short implementation plan before touching files.
- A concise list of files created or modified.
- A summary of key design decisions and assumptions.
- Verification evidence: build/lint/test commands and notable outputs.
- Open follow-ups or blockers that should be carried into the next task.

## Codex `/review` prompt

Use this after the implementation for **US-8-T4 — Support invoice layout, e-invoice, Leitweg, dispatch, and dunning configuration** is finished.

```text
/review Please review the implementation for task US-8-T4 (Support invoice layout, e-invoice, Leitweg, dispatch, and dunning configuration) against this prompt file and the current repository state.

Review goals:
- Confirm the implementation matches the objective, dependencies, hard constraints, expected outputs, non-goals, and verification checklist in `docs/prompts/US-8-T4.md`.
- Review only the files that are relevant to this task, but also flag any upstream or downstream contract drift caused by the changes.
- Identify correctness, data-model, API-contract, migration, authorization, localization, testing, and maintainability issues.

Task-specific review focus:
- Advanced invoice configuration is represented explicitly and compatibly with future finance/communication flows.
- Validation logic is strong enough to prevent incomplete or contradictory dispatch/e-invoice settings.
- Lookup/code usage is controlled and maintainable rather than free-form and brittle.
- The task stops at configuration and contracts instead of smuggling later finance execution into Sprint 3.

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
