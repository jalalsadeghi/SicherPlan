After implementing the sticky/floating Overview nav fix, perform or document this manual QA.

Manual QA:
1. Open:
   http://localhost:5173/admin/employees
2. Select an existing employee.
3. Click Overview.
4. Confirm left nav is visible next to Employee file section.
5. Scroll down slowly with the mouse wheel.
6. Confirm left nav stays visible in the viewport.
7. Scroll to the bottom sections, such as Groups or Documents.
8. Confirm left nav is still visible and usable.
9. Click Addresses link.
10. Confirm page scrolls to Addresses section.
11. Continue scrolling manually.
12. Confirm active link changes automatically based on the visible section.
13. Resize browser to tablet/mobile width.
14. Confirm nav does not cover content and remains usable.
15. Confirm visual style remains link-like with icons, not pill buttons.
16. Confirm Dashboard tab still works.
17. Confirm Create employee file mode still works.
18. Confirm no console errors.

If browser QA cannot be run:
- explicitly say manual QA was not run
- provide deterministic tests for structure, scrollIntoView, and IntersectionObserver.

Final report must include:
- whether CSS sticky worked or a fixed fallback was needed
- sticky top offset used
- root cause of the previous failure
- manual QA status.