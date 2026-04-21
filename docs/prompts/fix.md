After implementing Dashboard photo upload and removing Profile photo tab, perform or document this manual QA.

Manual QA:
1. Open:
   http://localhost:5173/admin/employees
2. Select an existing employee, e.g. P-2000 Markus Neumann.
3. Confirm Dashboard tab is active.
4. Confirm the text "Employee dashboard" is gone.
5. Confirm the employee photo/avatar is visible in the Dashboard hero.
6. Confirm the Profile photo tab is no longer visible.
7. Click the photo.
8. Confirm an image file picker opens.
9. Select a valid image.
10. Confirm:
    - only the photo/avatar area shows upload progress.
    - the whole page is not dimmed.
    - the dashboard does not disappear.
    - after upload, the new photo is shown.
11. Select another image and confirm photo changes.
12. Test an employee without photo:
    - placeholder/initials are visible.
    - clicking placeholder opens file picker.
    - upload works.
13. Test a role without photo management permission if available:
    - photo is visible.
    - upload is disabled/not allowed.
14. Click Create employee file.
15. Confirm only Overview tab is visible.
16. Save a new employee if practical.
17. Confirm Dashboard appears only after employee exists.
18. Confirm all other tabs still work:
    - Overview
    - App access
    - Qualifications
    - Credentials
    - Availability
    - Private profile
    - Addresses
    - Absences
    - Notes
    - Groups
    - Documents
19. Confirm Dashboard assignment contexts and calendar still work.
20. Confirm no console errors.

If browser QA cannot be run:
- explicitly say manual QA was not run
- provide deterministic tests covering the same behavior.

Final report must include:
- manual QA status
- whether photo upload was implemented parent-owned or component-owned
- whether old Profile photo panel code was removed or only hidden
- any remaining limitation.