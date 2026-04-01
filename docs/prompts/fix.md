You are working in the latest SicherPlan repository.

Bug to fix:
The Employees admin page now loads readiness tabs (qualifications, credentials, availability, absences), but the page throws a generic frontend error after loading or saving an employee.

Observed backend log:
- GET /api/employees/tenants/{tenant_id}/employees/{employee_id} -> 200
- GET /api/employees/tenants/{tenant_id}/employees/{employee_id}/notes -> 200
- GET /api/employees/tenants/{tenant_id}/employees/{employee_id}/documents -> 200
- GET /api/employees/tenants/{tenant_id}/employees/{employee_id}/photo -> 200
- GET /api/employees/tenants/{tenant_id}/employees/availability-rules?employee_id=... -> 422
- GET /api/employees/tenants/{tenant_id}/employees/qualifications?employee_id=... -> 422
- GET /api/employees/tenants/{tenant_id}/employees/credentials?employee_id=... -> 422
- GET /api/employees/tenants/{tenant_id}/employees/absences?employee_id=... -> 422

Root cause:
In backend/app/modules/employees/router.py, the dynamic route
    @router.get("/{employee_id}")
is declared before several fixed collection routes like:
    /availability-rules
    /qualifications
    /credentials
    /absences
and likely similar one-segment collection routes.

Because FastAPI/Starlette routing is order-sensitive, requests such as:
    /employees/availability-rules
are being matched against:
    /employees/{employee_id}
so "availability-rules" is parsed as employee_id and fails UUID validation, causing HTTP 422.

Task:
Fix the backend routing bug cleanly and add regression coverage.

Required changes:
1. In backend/app/modules/employees/router.py
   reorder routes so all fixed collection/static routes are declared BEFORE any dynamic
   /{employee_id}
   route and before any other conflicting one-segment dynamic route.
2. Specifically ensure these list/create/update families are not shadowed:
   - /availability-rules
   - /absences
   - /leave-balances
   - /event-applications
   - /time-accounts
   - /allowances
   - /advances
   - /credentials
   - /qualifications
   and any other static collection route under the same prefix.
3. Preserve existing endpoint paths. Do NOT redesign the API.
4. Add backend regression tests proving that these routes resolve correctly and return 200/201 instead of 422 due to path shadowing.
5. If there are existing API tests for employee routes, extend them. Otherwise add focused route-resolution regression tests in backend/tests/modules/employees/.
6. Keep the new employee readiness UI unchanged unless a tiny frontend hardening improvement is needed.

Optional but recommended frontend hardening:
If one secondary readiness request fails, do not collapse the whole employee page into a generic “Action failed” state.
Instead:
- keep the main employee record visible
- show tab-level feedback for the failing readiness area
But only do this if it is a small, contained change.

Files to inspect:
- backend/app/modules/employees/router.py
- backend/tests/modules/employees/*
- possibly frontend files only if needed for small error-isolation improvement:
  - web/apps/web-antd/src/sicherplan-legacy/views/EmployeeAdminView.vue
  - web/apps/web-antd/src/sicherplan-legacy/api/employeeAdmin.ts

Acceptance criteria:
- Loading an employee no longer triggers 422 for readiness list endpoints
- Saving a new employee no longer surfaces the generic error caused by those failing GETs
- The following endpoints resolve correctly:
  /availability-rules
  /qualifications
  /credentials
  /absences
- Existing employee detail endpoints still work
- Regression tests pass

Before coding:
First summarize:
- which routes are shadowed
- the exact route-order fix
- the tests you will add
Then implement.