---
task_id: US-7-T2
story_id: US-7
story_title: "Customer master, contacts, addresses, and portal account linkage"
sprint: Sprint 03
status: ready
owner: "Frontend Lead / Backend Lead"
---

# Codex Prompt — US-7-T2

## Task title

**Create admin UI for customer list/detail, status control, and contact management**

## Objective

Deliver the first customer-management screens in the web admin so tenant administrators and allowed staff can search, create, edit, archive, and review customer records and their contacts using Vben Admin patterns.

## Source context

- Updated proposal: section 4 role model for tenant administrators and authorized tenant users; section 5.2 customer account and contact data; Appendix A customer file and contacts.
- Implementation specification: customer aggregate in section 4.3; customer package ownership in section 9; shared lifecycle and optimistic-lock conventions in section 2.
- Sprint reference: `docs/sprint/sprint-03-customer-management.md`.
- Cross-cutting rules: `AGENTS.md`.

## Dependencies

- `US-7-T1` must land first so the customer API contracts and persistence rules are stable.
- `US-3-T1`, `US-3-T3`, and `US-3-T4` should already provide the Vben shell, theme tokens, and DE/EN localization baseline.
- `US-5-T3` should provide RBAC-friendly route and action-guard patterns.

## Scope of work

- Build Vben Admin pages for customer list, create/edit/detail flows, status control, and contact management on top of the backend contracts from `US-7-T1`.
- Provide searchable and filterable customer list views with status, classification, ranking, branch/mandate defaults, primary contact summary, and archive-state visibility consistent with permissions.
- Create list/detail forms or tabbed pages for general customer data, addresses, contacts, and optional portal-link display/edit flows as allowed by the current API contracts.
- Implement create/edit/archive/reactivate actions with optimistic-lock handling, clear validation feedback, and confirmation UX for destructive or state-changing actions.
- Use DE-default / EN-secondary localization for route labels, menu labels, form labels, validation text, empty states, and action confirmations.
- Wire permission-based visibility for read/create/edit/activate-deactivate/export actions as appropriate for customer administration.
- Add frontend tests for key list/detail flows, permission guards, form validation, and localization rendering.

## Preferred file targets

- Vben Admin routes, menu registrations, page components, API client modules, and store/query hooks under the actual web-app path.
- Shared customer-form components for company data, addresses, and contact subforms.
- Locale resource files for German and English customer-management UI strings.
- Frontend tests close to the customer admin pages.

## Hard constraints

- Use Vben Admin conventions for list/detail pages, route guards, forms, drawers/modals, and reusable CRUD patterns; do not build an unrelated custom shell.
- Do not embed customer-auth or password-management flows in these admin pages; portal authentication belongs to `US-9-T1` and the IAM layer.
- Do not mix commercial settings into the core customer screens beyond obvious navigation handoff points; `US-8-*` owns commercial UI depth.
- Status changes, archive toggles, and customer edits must respect backend permission and optimistic-lock rules rather than relying on client-only assumptions.
- All user-facing strings introduced here must ship in German and English.

## Expected implementation outputs

- A usable customer-management admin UI with customer list/detail pages and contact maintenance.
- Permission-aware and localization-ready web pages aligned with the approved Vben Admin shell.
- Frontend tests or integration coverage for core CRUD and status flows.

## Non-goals

- Do not implement full import/export or vCard workflows here; that is `US-7-T3`.
- Do not implement the specialized commercial settings pages here; that is `US-8-T3` and `US-8-T4`.
- Do not implement customer portal read-only pages here; that is `US-9-*`.

## Verification checklist

- Authorized users can create, edit, archive, and search customers through the web UI.
- Contact add/edit/remove flows behave correctly and match backend validations.
- Permission guards hide or disable disallowed actions without replacing backend enforcement.
- German renders by default and English renders correctly when selected.
- Optimistic-lock and validation errors are surfaced clearly to users.

## Codex response format

- A short implementation plan before touching files.
- A concise list of files created or modified.
- A summary of key design decisions and assumptions.
- Verification evidence: build/lint/test commands and notable outputs.
- Open follow-ups or blockers that should be carried into the next task.

## Codex `/review` prompt

Use this after the implementation for **US-7-T2 — Create admin UI for customer list/detail, status control, and contact management** is finished.

```text
/review Please review the implementation for task US-7-T2 (Create admin UI for customer list/detail, status control, and contact management) against this prompt file and the current repository state.

Review goals:
- Confirm the implementation matches the objective, dependencies, hard constraints, expected outputs, non-goals, and verification checklist in `docs/prompts/US-7-T2.md`.
- Review only the files that are relevant to this task, but also flag any upstream or downstream contract drift caused by the changes.
- Identify correctness, data-model, API-contract, migration, authorization, localization, testing, and maintainability issues.

Task-specific review focus:
- Vben Admin integration is idiomatic and does not break the established shell, theme, or i18n rules.
- UI permissions and route guards align with backend contracts and do not create client-only security assumptions.
- Form handling preserves address/contact structure without duplicating backend business rules incorrectly.
- Localization coverage is complete for newly introduced customer-admin strings.

Required review output:
1. Blocking issues
2. Major issues
3. Minor issues
4. Nice-to-have improvements
5. Final verdict: `approved`, `approved with minor issues`, or `changes required`

Additional instructions:
- Be strict about tenant isolation, role scoping, auditability, DE default / EN secondary behavior, and traceability to US-7.
- Call out missing tests, weak assertions, incorrect acceptance coverage, schema drift, unsafe defaults, or assumptions that are not grounded in the proposal or implementation data model.
- If no real issue exists, say so clearly and do not invent problems.
```
