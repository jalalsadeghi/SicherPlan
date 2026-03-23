# SicherPlan Admin UI Foundation

## Purpose

The admin frontend now uses the Vben shell as the primary product frame and treats the legacy SicherPlan module screens as embedded workspaces during the migration phase.

## Structure

- `web/apps/web-antd/src/components/sicherplan/`
  Shared page-building blocks for intro sections, stats, split layouts, section headers, and empty states.
- `web/apps/web-antd/src/views/sicherplan/dashboard/index.vue`
  Product dashboard entry that replaces the generic demo-style landing view.
- `web/apps/web-antd/src/views/sicherplan/admin-module-view.vue`
  Reusable wrapper that gives each module a consistent intro, summary cards, quick links, and workspace section.
- `web/apps/web-antd/src/views/sicherplan/module-registry.ts`
  Config-driven mapping from route metadata to module descriptions, badges, quick links, and the embedded legacy workspace component.

## Navigation Model

The left navigation is grouped for mixed navigation mode:

- Dashboard
- Administration
- Customers
- Workforce
- Operations
- Billing & Payroll
- Reporting
- Portals
- Public Forms

This keeps top-level scanning short while the sidebar holds the module leaves for the active business area.

## Page Pattern

Every wrapped admin module follows the same composition:

1. Product intro with title, summary, and key badges
2. Summary stat row
3. Split overview with module intent and delivery guardrails
4. Embedded workspace card for the existing operational screen

This pattern keeps upcoming feature work consistent while avoiding a risky full rewrite of the existing admin forms and tables.

## Adding A New Module

1. Add the module route and set `meta.moduleKey`.
2. Register the module in `src/views/sicherplan/module-registry.ts`.
3. Add DE and EN locale entries under `sicherplan.ui.modules.*` and any related navigation keys.
4. Point the registry entry to the module workspace component.

## Migration Note

The current wrapper approach is intentionally transitional. It centralizes shell quality and information architecture now, while allowing future sprints to replace individual legacy workspaces with native Vben-first screens incrementally.
