# Web Shell Notes

## Task anchor

- Task: `US-3-T1`

## What was established

- A Vue 3 + Vite web workspace with Pinia and Vue Router under `web/`
- Role-aware route and menu registries for the initial internal and portal roles
- Separate admin and portal layouts that share shell rules but keep navigation intent clear
- DE-default / EN-secondary localization wiring for shell labels, menus, route placeholders, and header controls
- Placeholder module routes for:
  - dashboard
  - core settings
  - platform services
  - customers
  - employees
  - subcontractors
  - planning
  - field execution
  - finance
  - reporting

## Role model used in the shell

- `platform_admin`
- `tenant_admin`
- `dispatcher`
- `accounting`
- `controller_qm`
- `customer_user`
- `subcontractor_user`

These are provisional UI-facing role IDs for shell/routing behavior. Later IAM work should either confirm them or map them cleanly without changing the basic shell structure.

## Branding note

The prompt referenced `Main-Logo-site.png`, but that asset does not exist in the current repository state. The shell therefore uses a text/SVG-like SicherPlan mark for now. Once the real logo asset is provided, it should replace the temporary brand mark inside `BrandPanel.vue`.

## Why the shell is still intentionally light

- No business CRUD screens are implemented yet.
- The shell now has a DE/EN resource structure, but later modules still need to consume it consistently.
- Theme tokens are now centralized by `US-3-T3`, but later modules still need to consume them consistently.
- Route guards are role-aware and router-based, but not yet backed by real IAM responses.

This keeps the shell structurally correct without pretending Sprint 2+ module work already exists.
