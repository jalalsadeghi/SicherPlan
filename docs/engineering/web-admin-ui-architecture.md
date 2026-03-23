# SicherPlan Web Admin UI Architecture

## Goal
SicherPlan uses Vben Admin as the shell, but the SicherPlan domain modules own the actual page composition. The navigation and page patterns should scale by business capability, not by a flat list of screens.

## Navigation grouping
- Dashboard
- Administration
  - Tenant & Core System
  - Platform Services
- People & Partners
  - Customers
  - Employees
  - Recruiting
  - Subcontractors
- Operations
  - Operations Master Data
  - Orders & Planning
  - Shift Planning
  - Staffing & Coverage
- Finance
  - Actual Release
  - Payroll
  - Billing
  - Subcontractor Invoice Checks
- Reporting
- Portals
- Public Forms

The grouped routes live in [sicherplan.ts](/home/jey/Projects/SicherPlan/web/apps/web-antd/src/router/routes/modules/sicherplan.ts). New admin modules should be added to the right business group first, not as a new first-level menu item.

## Reusable page pattern
Use these shared building blocks:
- `AdminPageShell`: standard hero/title/lead/actions shell for admin pages
- `AdminStatCard`: lightweight summary/status KPI card
- `RouteSectionView`: structural route node for grouped Vben navigation

Recommended composition:
1. `AdminPageShell`
2. optional `AdminStatCard` summary row
3. module working area using existing cards/panels
4. scoped empty/error/permission states

## Where to add new modules
- New internal backoffice features: add under the relevant `/admin/*` group in `sicherplan.ts`
- New portal features: add under the `Portal` route section
- New public forms: add under the `Public Forms` section

## Constraints
- Keep existing business URLs stable when possible
- Prefer grouping and shared scaffolding over page-specific visual hacks
- Keep German default and English secondary through i18n route labels and page copy
