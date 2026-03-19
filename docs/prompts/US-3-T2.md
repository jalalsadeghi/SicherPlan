---
task_id: US-3-T2
story_id: US-3
story_title: "Vben Admin shell, Prokit mobile shell, theme tokens, and localization"
sprint: Sprint 01
status: ready
owner: "Mobile Lead"
---

# Codex Prompt — US-3-T2

## Task title

**Bootstrap Flutter mobile shell from Prokit reference and define app navigation**

## Objective

Create the first mobile shell for employee and field workflows using Flutter with Prokit-style navigation and screen composition as the interaction reference.

## Source context

- Updated proposal: employee app and self-service; planning/field/time-capture scope; technical architecture and deliverables.
- Cross-cutting rules: `AGENTS.md` (Flutter + Prokit reference, mobile rules, DE/EN rule, theme rule, scoped operational data).
- Sprint reference: `docs/sprint/sprint-01-inception-and-setup.md`.
- Brand asset provided in prior context: `app_icon.png`.

## Dependencies

- `US-2-T1` should define repository/workspace structure first.
- `US-2-T2` should provide baseline config/environment patterns for the mobile app.

## Scope of work

- Bootstrap or adapt a Flutter app shell using Prokit Flutter as the interaction/reference baseline, without blindly copying a template into the product.
- Define mobile navigation for the early employee/field experience with placeholder screens such as home, schedule, information feed, time capture, patrol/watchbook access, and profile/settings.
- Create a route/session structure that can later support employee, field supervisor, and restricted field-execution permissions.
- Add app branding assets, including the provided app icon, and keep the shell ready for later theme/i18n implementation.
- Keep the architecture ready for offline-capable features that will arrive in later sprints.

## Preferred file targets

- Flutter app bootstrap files under the actual mobile app path
- Navigation/router configuration, shell screens, and placeholder feature folders
- Asset registration for `app_icon.png`
- A short mobile-shell note under `docs/ux/` or `docs/engineering/` if needed

## Hard constraints

- Use Prokit as a reference for navigation and screen composition, not as a substitute for actual product requirements.
- Do not implement business logic-heavy field or schedule flows here; create shell and navigation only.
- Keep the app structure ready for offline field workflows and scoped operational data.
- Do not hardcode English-only strings or colors that will later conflict with the approved theme/i18n rules.

## Expected implementation outputs

- A runnable Flutter app shell.
- A stable navigation model for employee and field-oriented flows.
- Brand asset wiring for the mobile app icon and shell identity.

## Non-goals

- Do not implement final theme tokens here; that belongs to `US-3-T3`.
- Do not implement full localization here; that belongs to `US-3-T4`.
- Do not build complete schedule, time-capture, or patrol features yet.

## Verification checklist

- The Flutter app runs successfully in development mode.
- Navigation between placeholder screens works.
- The app icon/branding asset is wired correctly.
- The code structure leaves a clean path for later feature modules and offline flows.

## Codex response format

- A short implementation plan before touching files.
- A concise list of files created or modified.
- A summary of key design decisions and assumptions.
- Verification evidence: build/lint/test commands and notable outputs.
- Open follow-ups or blockers that should be carried into the next task.
