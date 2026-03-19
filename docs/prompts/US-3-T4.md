---
task_id: US-3-T4
story_id: US-3
story_title: "Vben Admin shell, Prokit mobile shell, theme tokens, and localization"
sprint: Sprint 01
status: ready
owner: "Frontend Lead / Backend Lead / Mobile Lead"
---

# Codex Prompt — US-3-T4

## Task title

**Implement DE/EN i18n resource structure and shared localization rules for UI and API messages**

## Objective

Create a localization baseline that enforces German as the default language and English as the secondary language across web, mobile, and API-facing message contracts.

## Source context

- Updated proposal: target user groups and access model; communication backbone; employee app / customer / subcontractor portal intent; technical architecture.
- Cross-cutting rules: `AGENTS.md` (German default, English secondary, no hardcoded mixed-language strings).
- Sprint reference: `docs/sprint/sprint-01-inception-and-setup.md`.

## Dependencies

- `US-3-T1` and `US-3-T2` should provide the web/mobile shell entry points.
- `US-2-T4` should inform API error/message structure where relevant.

## Scope of work

- Implement localization resource structures for the web and mobile apps using idiomatic framework patterns.
- Define how backend/API validation and error messages should be represented so clients can render localized text consistently; prefer stable keys/codes over one-off inline message strings.
- Set German as the default locale and English as the secondary locale in the current shells.
- Translate the shell-level strings, route labels, menu items, auth placeholders, and common validation or empty-state messages needed for Sprint 1.
- Document localization rules for future work: key naming, fallback behavior, interpolation, date/number formatting, and when messages belong in backend versus frontend/mobile resources.

## Preferred file targets

- Web locale resource files (for example `de-DE` and `en-US` resources)
- Flutter localization resources (for example ARB or equivalent resource files)
- Backend message-key / localization helper files if the API project exists
- `docs/ux/localization-rules.md`

## Hard constraints

- German must be the default locale.
- English must exist as the secondary locale for all user-facing strings introduced in Sprint 1.
- Do not leave hardcoded user-visible strings in shell components if a localization resource structure exists.
- Keep localization strategy compatible with notifications, documents, and API validation messages that will come later.

## Expected implementation outputs

- A working DE/EN localization baseline for web and mobile shells.
- A documented localization rule set for future tasks.
- A consistent approach for API/client message localization.

## Non-goals

- Do not translate the entire future product scope; only create the baseline and cover Sprint 1 shell/UI text.
- Do not implement every notification or document template now.
- Do not invent locale variants beyond what the project currently needs.

## Verification checklist

- German is the default at runtime.
- English can be selected and renders the shell correctly.
- Shell strings and common validation text use resource keys rather than hardcoded literals.
- Documentation explains how later tasks must add DE and EN content together.

## Codex response format

- A short implementation plan before touching files.
- A concise list of files created or modified.
- A summary of key design decisions and assumptions.
- Verification evidence: build/lint/test commands and notable outputs.
- Open follow-ups or blockers that should be carried into the next task.

## Codex `/review` prompt

Use this after the implementation for **US-3-T4 — Implement DE/EN i18n resource structure and shared localization rules for UI and API messages** is finished.

```text
/review Please review the implementation for task US-3-T4 (Implement DE/EN i18n resource structure and shared localization rules for UI and API messages) against this prompt file and the current repository state.

Review goals:
- Confirm the implementation matches the objective, dependencies, hard constraints, expected outputs, non-goals, and verification checklist in `docs/prompts/US-3-T4.md`.
- Review only the files that are relevant to this task, but also flag any upstream or downstream contract drift caused by the changes.
- Identify correctness, data-model, API-contract, migration, authorization, localization, testing, and maintainability issues.

Task-specific review focus:
- CI/CD and automation changes are minimal, reproducible, and do not weaken quality gates.
- German default and English secondary language handling is present wherever user-facing text changes.

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
