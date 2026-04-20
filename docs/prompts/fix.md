Perform a final UX parity check between:
1. Customer New Plan wizard Step 8 "Series & exceptions"
2. admin/planning-shifts "New series" modal

Focus specifically on weekday selection.

Checklist:
1. Both surfaces must use the same weekday order:
   Mon Tue Wed Thu Fri Sat Sun
2. Both surfaces must map index 0 to Monday and index 6 to Sunday.
3. Both surfaces must use the same mask semantics:
   1111100 = Monday-Friday
4. Both surfaces must show chip buttons for weekly recurrence.
5. Both surfaces must not require typing weekday_mask manually.
6. Both surfaces must clear or ignore weekday_mask for daily recurrence.
7. Customer New Plan wizard must remain visually consistent with its own design system:
   - same spacing as surrounding form
   - responsive layout
   - accessible focus state
   - no horizontal overflow
8. The change must not affect:
   - Shift Plan selection
   - Series save/generation
   - Exception creation
   - Draft persistence
   - Route synchronization
   - Backend payload shape

If any mismatch exists, fix it.

Final response must include:
- whether UX parity is achieved
- any intentional differences and why
- screenshots are not required, but mention the exact selectors/classes used.