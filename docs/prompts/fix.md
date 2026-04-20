After implementing the fix, perform or document this exact manual QA scenario.

Do not mark the task complete with tests only unless you explicitly state you cannot run the browser and provide the deterministic equivalent test.

Manual browser QA scenario:
1. Start backend and frontend.
2. Open:
   http://localhost:5173/admin/customers/new-plan?customer_id=84bad50d-209c-491e-b86b-13c7788c7620&order_id=7eb5cee5-92ab-442b-8433-b9d8b94949e2&step=shift-plan&planning_entity_id=cf297d3f-e149-4448-86b6-f6cb70f6da58&planning_entity_type=site&planning_mode_code=site&planning_record_id=1606e67d-dc16-4724-8640-843c02e4f16d
3. Select existing ShiftPlan:
   8ced3d43-8c8b-42eb-b713-518204ffe0ad
4. Confirm selected summary appears.
5. Click Next.
6. Confirm:
   - UI shows Step 8 "Series & exceptions"
   - URL has step=series-exceptions
   - URL has shift_plan_id=8ced3d43-8c8b-42eb-b713-518204ffe0ad
   - backend may show GET /shift-plans/{id}/series 200
   - after all requests finish, UI is still Step 8
   - it does not bounce back to Shift plan
7. If there are no series rows, the Series form must still appear.
8. Select or create a shift template and complete the series fields.
9. Do not generate shifts yet unless the test requires it.

Also test:
- refresh page on Step 8 URL with shift_plan_id
- direct invalid Step 8 URL without shift_plan_id
- click Previous from Step 8 back to Step 7
- then click Next again

Final report must include:
- whether manual QA passed
- if not, exact browser console trace and backend log around the rollback
- exact route before and after clicking Next
- exact rendered data-step-id before and after clicking Next