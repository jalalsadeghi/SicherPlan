You are working in the public repository `jalalsadeghi/SicherPlan`.

Goal:
Fix and harden the `admin/planning-orders` page so that it matches the documented P-02 "Orders & Planning Records" scope and the existing planning API contract.

Primary files to inspect and modify:
- `web/apps/web-antd/src/router/routes/modules/sicherplan.ts`
- `web/apps/web-antd/src/views/sicherplan/module-registry.ts` (or the equivalent registry/wrapper file used by `AdminModuleView`)
- `web/apps/web-antd/src/sicherplan-legacy/views/PlanningOrdersAdminView.vue`
- `web/apps/web-antd/src/sicherplan-legacy/api/planningOrders.ts`
- any related composables/components under the planning feature used by the page

Documented target scope for P-02:
1. Customer orders / projects
2. Order release state
3. Order equipment lines
4. Order requirement lines
5. Order attachments (create + link)
6. Order commercial link
7. Planning records under the order
8. Planning-record release state
9. Planning-record attachments (create + link)
10. Planning-record commercial link
11. Planning-mode-aware editing so the user can create/use event, site, trade fair, or patrol planning records consistently with the documented planning model

Important constraints:
- Do NOT invent new backend endpoints.
- Use only the existing planning API surface already documented in OpenAPI.
- Keep the existing Vben / SicherPlan admin-shell patterns.
- Preserve tenant scoping, role scoping, and audit-friendly release actions.
- Do not change P-03 / P-04 behavior unless a shared planning helper must be fixed.

Tasks:
1. Verify route-to-view wiring
   - Confirm that `moduleKey: 'planning-orders'` resolves to `PlanningOrdersAdminView.vue`.
   - If the registry currently points to a placeholder or the wrong module, fix the mapping.
   - Keep the route path `/admin/planning-orders`.

2. Align access with the documented role matrix
   - Current code uses `tenant_admin`, `dispatcher`, `controller_qm`.
   - The documented P-02 page is intended for Tenant Administrator, Customer/Account Manager, and Operations Planner/Dispatcher.
   - Update authorities to align with the repository’s actual role model.
   - If there is no dedicated account-manager/commercial role implemented yet, use the nearest existing commercial role consistently and document the mapping in code comments.
   - If `controller_qm` must keep access, enforce read-only mode for that role instead of full CRUD.

3. Implement/complete the page as a master-detail workspace
   A. Left/list area
   - Filters for customer, order status/release state, planning mode, date window, and text search
   - Orders list
   - Planning-record list scoped to the selected order

   B. Order detail/editor area
   - Fields:
     - customer_id
     - title
     - requirement_type_id
     - service_category_code
     - security_concept_text
     - start_date
     - end_date
     - notes
     - release_state_code / release action
   - Separate CRUD sub-sections for:
     - equipment lines
     - requirement lines
     - attachments
     - commercial link summary

   C. Planning-record detail/editor area
   - Fields:
     - order_id
     - planning_mode_code
     - name
     - plan_start_at
     - plan_end_at
     - dispatcher_user_id
     - status_code
     - release_state_code / release action
   - Separate sub-sections for:
     - planning-record attachments
     - planning-record commercial link summary

4. Planning-mode-aware UI
   - Support the documented operational modes: `event`, `site`, `trade_fair`, `patrol`.
   - If the backend already carries mode-specific detail in the planning-record payload, render/edit those fields in a mode-aware detail panel.
   - If mode-specific detail is loaded through existing shared helpers, wire them in.
   - Do not fake unsupported persistence; if a mode-specific backend field truly does not exist, keep the field read-only/hidden and leave a concise inline technical note in code, not in the user UI.

5. API integration
   In `planningOrders.ts`, ensure the page supports the existing contract for:
   - orders list/create/get/update
   - order release-state
   - order equipment-lines list/create/update
   - order requirement-lines list/create/update
   - order attachments list/create/link
   - order commercial-link get
   - planning-records list/create/get/update
   - planning-record release-state
   - planning-record attachments list/create/link
   - planning-record commercial-link get

6. Validation and UX behavior
   - Validate required fields before submit.
   - Prevent invalid date windows (`start_date > end_date`, `plan_start_at >= plan_end_at`, etc.).
   - Make release actions explicit and separate from ordinary save actions.
   - Show inline loading/error states per sub-section so one failing child panel does not block the whole page.
   - Keep destructive or state-changing actions confirmable.
   - For read-only roles, disable or hide create/edit/release controls cleanly.

7. Tests
   Add or update tests that prove:
   - `/admin/planning-orders` resolves to the correct module
   - the correct roles can access the page
   - read-only roles cannot perform write actions
   - order and planning-record sections render independently
   - attachments / release-state / child-line sections are present
   - the API helper exposes the documented endpoint groups

8. Acceptance criteria
   The fix is complete only if:
   - the route is wired correctly
   - role access matches the intended page scope
   - the page exposes all documented P-02 sections
   - order-level and planning-record-level data are clearly separated
   - release-state and attachment workflows exist for both order and planning-record layers
   - the page is ready for realistic tenant-admin data entry without relying on informal notes as a substitute for structured fields

Output format:
- Provide a short summary of what was wrong
- List all changed files
- Explain any role-mapping decision
- Call out any remaining backend limitation explicitly