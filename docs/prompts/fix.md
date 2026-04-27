Review the Employees workspace changes.

Check:
1. Address history is moved into a dialog and no longer clutters the Overview page.
2. Reset password is moved into a dialog and still calls the correct API.
3. Detach access is in the same action row as Update linked access and Reset password, aligned to the right.
4. Diagnostics are moved into a dialog and still show all readiness checks.
5. Tall portrait employee photos in the list stay inside the avatar container without distortion or overflow.
6. The detail/dashboard photo display was not broken.
7. Clicking the sidebar Employees item while already inside an employee detail returns to the employee list.
8. The Back to employee list button still works.
9. No backend API or permission scope was changed.
10. Tests were added or updated instead of weakened.

Run the relevant web tests, lint, and typecheck. Fix any regression with the smallest safe change.