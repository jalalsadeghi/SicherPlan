After implementing the calendar fixes, perform or document this exact manual QA.

Manual QA:
1. Open http://localhost:5173/admin/customers.
2. Select a customer with calendar entries, for example RheinForum Köln.
3. Scroll to the Customer calendar.
4. Confirm current month calendar is visible.
5. Click Next.
6. Confirm:
   - calendar card does not disappear
   - month label changes immediately
   - loading indicator is subtle and does not replace the whole calendar
   - after data loads, entries appear if available
7. Click Previous.
8. Confirm the same no-flicker behavior.
9. In a day that has both shift and order counts, confirm:
   - ORD appears before SH
   - ORD and SH are on the same row
10. Navigate to a month with no entries.
11. Confirm:
   - calendar grid still shows the month
   - summary chips show 0 values
   - no empty-state message appears below the calendar
12. Simulate or observe an API error if practical.
13. Confirm actual calendar error still appears.

If browser QA cannot be run:
- explicitly say manual QA was not run
- provide deterministic test coverage for the same cases

Do not mark the task complete with tests that only check API calls. The visible UX must be covered.