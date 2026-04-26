You are working in the SicherPlan repository.

Goal:
Fix the Flutter Mobile Calendar/Schedule screen so the calendar is always visible, even when the current employee has no released shifts in the current week, future weeks, or in the whole returned schedule list.

Current problem:
The current ScheduleScreen only renders the week/calendar UI when fetchReleasedSchedules returns at least one item. If the list is empty, it shows only the "Keine freigegebenen Schichten" HighlightCard and the user cannot browse the calendar. This is wrong. The calendar must always be visible, independent of whether shifts exist.

User expectation:
The Calendar/Schedule tab should behave like a real schedule calendar:
- Always show the week-based calendar view.
- Show seven days per week.
- Allow vertical scrolling through weeks.
- Days without shifts should still be visible.
- Days with shifts should show the shift entry.
- The user should be able to scroll up/down and look for shifts.
- Tapping a shift should still open the shift detail dialog.

Before coding:
1. Read and follow AGENTS.md.
2. Inspect the current implementation:
   - mobile/lib/features/schedule/schedule_screen.dart
   - mobile/test/schedule_screen_test.dart
   - mobile/lib/api/mobile_backend.dart
   - mobile/lib/l10n/app_localizations.dart
   - mobile/lib/navigation/app_shell.dart
3. Validate this proposal against the current code before changing it.
4. Do not change backend APIs unless you find a real blocker. This should be a mobile-only UI/test fix.

Business rules:
- This is the Employee/Guard self-service mobile schedule screen.
- The employee must only see their own released schedules from the existing employee-self-service endpoint.
- Do not expose tenant-wide planning data.
- Do not add admin, dispatcher, customer, subcontractor, HR-private, or payroll data.
- Keep role-scoped visibility and employee self-service boundaries intact.
- Use existing MobileBackendGateway.fetchReleasedSchedules and EmployeeReleasedScheduleItem.

Required UI change:
1. Remove the behavior where an empty schedule list replaces the calendar with only an empty HighlightCard.
2. Always render the schedule calendar/week list.
3. When schedules are empty, render a useful default calendar window, for example:
   - current week
   - several previous weeks
   - several following weeks
   A reasonable default is 4 previous weeks + current week + 12 future weeks.
4. When schedules are not empty, render a calendar range that includes:
   - the current week
   - all weeks containing returned schedules
   - several future weeks after the last schedule
   - optionally several previous weeks before the first schedule
5. The week list must be chronological and vertically scrollable.
6. Each week section should show a header similar to:
   "05 Jan – 11 Jan 2026"
7. Each week must show all seven days, Monday to Sunday.
8. Days without shifts must be visible and muted, with a short text such as "Keine Schicht" / "No shift".
9. Days with shifts must be visually highlighted and show shift cards/chips directly in the day row.
10. If multiple shifts exist on the same day, show all of them sorted by workStart.
11. Tapping a shift must open the existing shift detail dialog.
12. Do not require the user to tap a day first in order to see shifts.
13. Keep the event application card below the calendar and collapsed by default.
14. Keep the refresh button working.
15. Keep loading and error states, but do not let the empty state remove the calendar.
16. If fetchReleasedSchedules fails, show an error card and still keep the calendar shell visible if it is safe to do so.

Suggested implementation:
- In mobile/lib/features/schedule/schedule_screen.dart:
  - Replace the current `if (schedules.isEmpty) return HighlightCard(...)` branch.
  - Always build `sortedSchedules`, `schedulesByDay`, and `weekStarts`.
  - Refactor `_buildWeekStarts` so it does not depend on `schedules.first` and `schedules.last`.
  - Add a helper like:
    `_buildCalendarWeekStarts(List<EmployeeReleasedScheduleItem> schedules, {DateTime? anchorDate})`
  - Use DateTime.now() as anchorDate in production.
  - In tests, make the helper deterministic or inject a fixed anchor date if needed.
- Keep or refine existing private widgets:
  - _ScheduleWeekList
  - _ScheduleWeekSection
  - _ScheduleDayGroup
  - _ScheduleShiftCard
  - _ShiftDetailRow
- Use stable test keys:
  - schedule-week-list
  - schedule-week-section-YYYY-MM-DD
  - schedule-day-YYYY-MM-DD
  - schedule-day-empty-YYYY-MM-DD
  - schedule-shift-<assignmentId>
  - schedule-shift-dialog-<assignmentId>

Design guidance:
- The visual result should be closer to a simple mobile schedule list like the provided reference image:
  - a card for the week
  - rows for Mon/Tue/Wed/etc.
  - empty days muted
  - shift days highlighted
  - shift entries easy to tap
- Preserve the current SicherPlan visual language:
  - Material 3
  - existing theme colors/tokens
  - rounded cards
  - clear spacing
  - mobile-safe layout
- Do not add third-party calendar packages unless absolutely necessary.

Localization:
Add or adjust German and English labels where needed:
- Week / Woche
- No shift / Keine Schicht
- Shift details / Schichtdetails
- Today / Heute
- Close / Schließen
- Empty calendar hint, for example:
  DE: "Keine Schicht an diesem Tag"
  EN: "No shift on this day"

Tests:
Update mobile/test/schedule_screen_test.dart.

Required test coverage:
1. When fetchReleasedSchedules returns an empty list, the calendar week list is still rendered.
2. Empty schedule state should not replace the calendar.
3. Empty days are visible and show "Keine Schicht" or equivalent localized text.
4. The calendar renders the current/default week range even without shifts.
5. When schedules exist, days with shifts are highlighted and shift cards are visible.
6. Multiple shifts on one day are sorted by workStart.
7. Multiple weeks render in chronological order.
8. The user can scroll to a later week.
9. Tapping a shift opens the shift detail dialog.
10. Event application remains collapsed by default and below the calendar.
11. Existing confirm/decline flow still works.

Acceptance criteria:
- The Calendar/Schedule tab always displays a calendar.
- No-shift users still see weeks and days.
- Shift users see their shifts inside the relevant days.
- The calendar does not depend on `schedules.isEmpty`.
- No backend API changes are required.
- Employee self-service data boundaries remain intact.
- Flutter formatting, analyzer, and tests pass.

Run:
cd mobile
flutter format lib test
flutter analyze
flutter test

Final response:
- Explain what you changed.
- Explicitly confirm whether this was mobile-only.
- List changed files.
- List tests run and results.
- Mention any remaining limitations or follow-up tasks.