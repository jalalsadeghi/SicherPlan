Review the Credentials maintenance change in admin/employees.

Check:
1. Existing credentials have Edit and Archive/Revoke actions.
2. Edit opens a dialog and only exposes fields supported by the backend update schema.
3. Save uses PATCH/updateEmployeeCredential and includes version_no.
4. Archive/Revoke uses PATCH/updateEmployeeCredential, not DELETE.
5. No hard-delete endpoint or frontend delete behavior was introduced.
6. Issue badge output still works.
7. The UI remains compact and consistent with the Employees Overview page.
8. Archived/revoked credentials are visually clear or removed from the active list according to existing backend list behavior.
9. Tenant scope and employee scope are unchanged.
10. Tests were added or updated and are meaningful.

Run the relevant web tests, lint, and typecheck. Fix any regression with the smallest safe change.