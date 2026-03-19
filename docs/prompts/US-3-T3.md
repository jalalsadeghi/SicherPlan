---
task_id: US-3-T3
story_id: US-3
story_title: "Vben Admin shell, Prokit mobile shell, theme tokens, and localization"
sprint: Sprint 01
status: ready
owner: "Frontend Lead / Mobile Lead"
---

# Codex Prompt — US-3-T3

## Task title

**Implement theme tokens using light rgb(40,170,170) and dark rgb(35,200,205) across web/mobile**

## Objective

Create a shared theme baseline for web and mobile so SicherPlan has a consistent, professional visual system from Sprint 1 onward.

## Source context

- Cross-cutting rules: `AGENTS.md` (exact light/dark primary colors, DE/EN rule, Vben/Prokit references).
- Sprint reference: `docs/sprint/sprint-01-inception-and-setup.md`.
- Brand assets from prior context: `Main-Logo-site.png` and `app_icon.png`.

## Dependencies

- `US-3-T1` web shell should exist.
- `US-3-T2` mobile shell should exist.

## Scope of work

- Define theme tokens for web and mobile with a shared naming approach, even if the implementations are framework-specific.
- Use the exact required primary colors: light mode `rgb(40,170,170)` and dark mode `rgb(35,200,205)`.
- Add light/dark theme switching in the web shell and mobile shell, or at minimum the internal wiring and a demonstrable toggle where the frameworks permit it in Sprint 1.
- Create supporting semantic colors (success, warning, danger, surface, border, text) conservatively so the primary colors stay visually coherent with the SicherPlan brand assets.
- Document the token choices so later feature work does not drift into inconsistent styling.

## Preferred file targets

- Web theme/token files under the actual web app structure
- Flutter theme/token files under the actual mobile app structure
- `docs/ux/theme-tokens.md`

## Hard constraints

- Use the exact primary color values provided by the user; do not approximate them.
- Do not introduce a competing brand palette that obscures the required colors.
- Keep theme definitions maintainable and framework-native rather than scattering ad hoc hex/rgb values throughout components.
- Preserve readability and contrast in both light and dark modes.

## Expected implementation outputs

- Consistent light/dark theme definitions for web and mobile.
- A clear theme-token document or equivalent in-repo explanation.
- A demonstrable theme switch or wiring that later modules can reuse.

## Non-goals

- Do not redesign layout structure or navigation here.
- Do not overbuild a full design system beyond the needed Sprint 1 baseline.
- Do not postpone token centralization by sprinkling raw colors through many files.

## Verification checklist

- Both web and mobile use the required primary colors.
- Theme values are centralized and easy to reuse.
- Light and dark themes render legibly in the current shells.
- Documentation explains how later UI work should consume the tokens.

## Codex response format

- A short implementation plan before touching files.
- A concise list of files created or modified.
- A summary of key design decisions and assumptions.
- Verification evidence: build/lint/test commands and notable outputs.
- Open follow-ups or blockers that should be carried into the next task.
