/review

Please review the Employee Overview side-navigation isolation fix.

Check:
1. Does each employee detail tab have isolated Overview section refs?
2. Does selectOverviewSection avoid document.getElementById/document.querySelector/global selectors?
3. Are duplicated static ids no longer used as scroll targets?
4. Do hidden cached employee tabs ignore scroll/observer updates?
5. Can Markus Neumann stay on Addresses while Emir Kaya stays on Notes?
6. Do Emir and Sarah side links work while Markus is still open?
7. Does switching top employee tabs preserve each employee’s own Overview scroll/active section?
8. Does closing one employee tab no longer affect whether other employee tabs’ side links work?
9. Are the Employees list tab and employee detail top-tab behavior unchanged?
10. Are Customers tabs unaffected?
11. Are domCached/keepAlive, route authority, moduleKey, sidebar structure, and pageKey behavior unchanged?
12. Were backend/API files untouched?
13. What tests were added or updated and what commands were run?

Please report:
- exact root cause
- files changed
- implementation summary
- tests added/updated
- commands run
- remaining risks