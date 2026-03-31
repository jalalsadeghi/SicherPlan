You are working in the latest SicherPlan repository.

Problem:
The current Employees admin page is too limited compared to the documented target employee file.
In the current implementation, the Employees overview form only supports a narrow operational subset:
personnel_no, first_name, last_name, preferred_name, work_email, work_phone, mobile_phone,
default_branch_id, default_mandate_id, hire_date, termination_date, user_id, notes.

But the intended employee file should also support at least:
- status (editable in the detail form)
- birth_date
- place_of_birth
- nationality_country_code (or birth_country_code equivalent in current naming)
- employment_type_code
- target_weekly_hours
- target_monthly_hours

Important implementation findings:
- The employees module is wired through:
  web/apps/web-antd/src/views/sicherplan/module-registry.ts
  -> EmployeeAdminView.vue
- Current UI file:
  web/apps/web-antd/src/sicherplan-legacy/views/EmployeeAdminView.vue
- Current frontend API contract:
  web/apps/web-antd/src/sicherplan-legacy/api/employeeAdmin.ts
- Current frontend helpers:
  web/apps/web-antd/src/sicherplan-legacy/features/employees/employeeAdmin.helpers.js
- Current backend employee schemas:
  backend/app/modules/employees/schemas.py
- Current backend employee models:
  backend/app/modules/employees/models.py

Current root cause:
1) birth_date / place_of_birth / nationality_country_code are modeled in EmployeePrivateProfile, but there is no dedicated UI/editor wired for them.
2) employment_type_code / target_weekly_hours / target_monthly_hours are not implemented in the current hr.employee backend model/schema/UI at all.
3) status exists in list/filter/badge behavior, but is not editable in the employee detail form.

Task:
Implement a proper full-stack fix so that the Employees module supports these missing fields in a clean, role-safe, production-ready way.

Requirements:
1. Preserve the current master-detail Employees page and current tabs.
2. Add an editable status field to the detail form.
3. Add support for:
   - birth_date
   - place_of_birth
   - nationality_country_code
   in a dedicated Private Profile section/tab, visible only to roles with private read/write permissions.
4. Extend hr.employee with:
   - employment_type_code
   - target_weekly_hours
   - target_monthly_hours
   including:
   - SQLAlchemy model changes
   - Pydantic schema changes
   - Alembic migration
   - service/repository updates
   - API serialization
5. Wire these fields into the Employees admin frontend so they can be:
   - loaded
   - edited
   - saved
   - displayed consistently
6. Update import/export support if the current employee CSV template is meant to represent the employee file.
   At minimum, extend the CSV template and import/export mapping for:
   - status
   - employment_type_code
   - target_weekly_hours
   - target_monthly_hours
7. Do not expose private-profile fields to roles that lack employees.private.read / employees.private.write.
8. Keep backward compatibility for existing records where these new values are null.

Files to inspect and update:
Frontend:
- web/apps/web-antd/src/sicherplan-legacy/views/EmployeeAdminView.vue
- web/apps/web-antd/src/sicherplan-legacy/api/employeeAdmin.ts
- web/apps/web-antd/src/sicherplan-legacy/features/employees/employeeAdmin.helpers.js
- related i18n/messages files for field labels and feedback
- related layout/helper tests

Backend:
- backend/app/modules/employees/models.py
- backend/app/modules/employees/schemas.py
- backend/app/modules/employees/service.py
- backend/app/modules/employees/ops_service.py
- backend/app/modules/employees/router or API endpoint files if needed
- new alembic migration

Testing:
Add or update tests for:
- frontend layout/rendering of the new fields/tabs
- payload builder/helper coverage
- backend create/update/read behavior
- permission behavior for private-profile visibility
- migration compatibility for existing rows

Acceptance criteria:
- In Employees detail, status is editable.
- Employment type and target hours are visible and editable.
- Birth date, birth place, and nationality country code are visible/editable in a private-profile UI section for authorized roles.
- Data persists correctly through API and database.
- Existing employee records continue to load without errors.
- No unauthorized private field leakage.
- Tests pass.

Before changing code, first summarize:
- impacted files
- data model changes
- API contract changes
- permission implications
Then implement.