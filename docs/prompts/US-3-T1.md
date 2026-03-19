---
task_id: US-3-T1
story_id: US-3
story_title: "Vben Admin shell, Prokit mobile shell, theme tokens, and localization"
sprint: Sprint 01
status: ready
owner: "Frontend Lead"
---

# Codex Prompt — US-3-T1

## Task title

**Bootstrap Vben Admin workspace and role-aware navigation shell**

## Objective

Create the first usable web shell for SicherPlan using Vben Admin conventions, with role-aware navigation, clear module placeholders, and branding that matches the approved platform direction.

## Source context

- Updated proposal: target user groups and access model; technical architecture; deliverables for the web platform.
- Cross-cutting rules: `AGENTS.md` (Vben Admin reference, DE/EN rule, theme rule, portal/privacy rule).
- Sprint reference: `docs/sprint/sprint-01-inception-and-setup.md`.
- Brand assets provided in prior context: `Main-Logo-site.png`.

## Dependencies

- `US-2-T1` should define repository/workspace structure first.
- `US-2-T2` should provide environment/config handling for the web app.

## Scope of work

- Bootstrap or adapt the web client as a Vben Admin-based workspace rather than a generic blank Vue app.
- Create base layouts for authenticated admin/tenant users and portal-style external users if the repo structure allows it, even if the portal routes are placeholders for now.
- Implement role-aware navigation/menu configuration for the primary roles in the proposal: platform admin, tenant admin, dispatcher/operator, accounting, controller/QM, customer user, and subcontractor user.
- Create placeholder route groups for the major modules so later CRUD/features land into a stable shell: dashboard, core settings, customers, employees, subcontractors, planning, field execution, finance, reporting, and platform services.
- Apply SicherPlan branding with the provided logo asset and keep the shell ready for later theme/i18n wiring.

## Preferred file targets

- Web workspace bootstrapping/config files under the actual web app path
- Router, layout, auth-store, and menu configuration files
- Brand asset placement for `Main-Logo-site.png`
- A short web-shell note under `docs/ux/` or `docs/engineering/` if the shell structure needs explanation

## Hard constraints

- Use Vben Admin patterns as the reference shell; do not build an unrelated custom admin framework.
- Do not implement business CRUD screens in depth here; keep placeholder pages light but structurally correct.
- Navigation and route guards must be compatible with later RBAC enforcement from IAM work.
- German must remain the default language once i18n wiring is added; do not hardcode English-only shell text.

## Expected implementation outputs

- A runnable web shell with authentication/role placeholder plumbing.
- A stable, role-aware route/menu registry ready for later modules.
- Basic SicherPlan branding in the shell.

## Non-goals

- Do not implement full localization here; that belongs to `US-3-T4`.
- Do not implement the final theme token system here; that belongs to `US-3-T3`.
- Do not build business module forms, lists, or reports yet.

## Verification checklist

- The web app starts successfully and shows the new shell.
- Role-aware navigation can be demonstrated with mock or provisional role data.
- Placeholder module routes exist and are organized consistently.
- The brand logo is applied cleanly without breaking the shell layout.

## Codex response format

- A short implementation plan before touching files.
- A concise list of files created or modified.
- A summary of key design decisions and assumptions.
- Verification evidence: build/lint/test commands and notable outputs.
- Open follow-ups or blockers that should be carried into the next task.

## Codex `/review` prompt

Use this after the implementation for **US-3-T1 — Bootstrap Vben Admin workspace and role-aware navigation shell** is finished.

```text
/review Please review the implementation for task US-3-T1 (Bootstrap Vben Admin workspace and role-aware navigation shell) against this prompt file and the current repository state.

Review goals:
- Confirm the implementation matches the objective, dependencies, hard constraints, expected outputs, non-goals, and verification checklist in `docs/prompts/US-3-T1.md`.
- Review only the files that are relevant to this task, but also flag any upstream or downstream contract drift caused by the changes.
- Identify correctness, data-model, API-contract, migration, authorization, localization, testing, and maintainability issues.

Task-specific review focus:
- Tenant isolation, scoping, and data ownership boundaries are enforced.
- Role-based visibility and authorization rules match the prompt and service boundaries.
- Vben Admin integration follows the agreed shell, navigation, theme, and i18n conventions.

Required review output:
1. Blocking issues
2. Major issues
3. Minor issues
4. Nice-to-have improvements
5. Final verdict: `approved`, `approved with minor issues`, or `changes required`

Additional instructions:
- Be strict about tenant isolation, role scoping, auditability, DE default / EN secondary behavior, and traceability to US-3.
- Call out missing tests, weak assertions, incorrect acceptance coverage, schema drift, or assumptions that are not grounded in the proposal or implementation data model.
- If no real issue exists, say so clearly and do not invent problems.
```
