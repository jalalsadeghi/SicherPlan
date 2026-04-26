Review the Mobile Calendar/Schedule implementation you just changed.

Focus on:
1. Does the screen really use vertical week-by-week scrolling instead of the previous month grid?
2. Are all released shifts visible directly under their day?
3. Does tapping a shift open a dialog box, not a bottom sheet?
4. Does the dialog show all available EmployeeReleasedScheduleItem details without inventing backend fields?
5. Are employee self-service data boundaries preserved?
6. Are confirm/decline, documents, route copy, and calendar export still working where they existed before?
7. Are German and English localization labels clean and not hardcoded unnecessarily?
8. Are tests updated instead of weakened?
9. Are there any regressions in event applications, empty state, loading state, or error state?

Run:
cd mobile
flutter format lib test
flutter analyze
flutter test

If you find problems, fix them in the smallest safe change. Do not change backend code unless there is a proven blocker.