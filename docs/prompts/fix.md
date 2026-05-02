/review Please review the implementation of the new customer order wizard "Demand groups" step.

Business requirement:
The customer order wizard should now have 7 steps. The new step `demand-groups` must appear after `series-exceptions`. After the user clicks "Generate Series & Continue" in `series-exceptions`, the wizard must generate the concrete shifts and move to `demand-groups`. In `demand-groups`, the user defines one or more demand-group templates once, and the system applies them to all generated shifts from the selected series/shift plan.

Review against:
- AGENTS.md
- docs/prompts/US-19-T1.md
- docs/prompts/US-19-T4.md
- current implementation data model rules
- existing planningStaffing API contracts
- existing customer wizard behavior

Focus areas:
1. Wizard correctness
   - exactly 7 steps
   - new step after series-exceptions
   - final-step logic now points to demand-groups
   - route restore works with `step=demand-groups`
   - direct access is blocked or redirected if required context is missing
2. Data correctness
   - demand groups are still normalized per concrete shift
   - no shadow demand-group model is created
   - applying to all generated shifts is correctly scoped by tenant + shift_plan_id + series_id/date window where available
3. Idempotency / duplicate safety
   - repeated submit does not blindly duplicate active demand groups
   - existing matching demand groups are skipped or updated according to documented behavior
4. UX
   - clear empty state if no generated shifts exist
   - clear apply summary after success
   - German default and English secondary labels exist
5. Security and scope
   - tenant scope is enforced
   - access token handling follows existing API patterns
   - no HR-private or partner-private data is exposed
6. Regression risk
   - existing six steps still work
   - staffing coverage page behavior remains unchanged
   - build/test commands pass

Required review output:
- Blocking issues
- Major issues
- Minor issues
- Nice-to-have improvements
- Final verdict: approved / approved with minor issues / changes required

Do not invent issues. If the implementation is sound, say so clearly.