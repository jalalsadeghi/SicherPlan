After implementing the left-side navigation for the "Order scope & documents" step, perform or document this manual QA.

Manual QA:
1. Open:
   /admin/customers/order-workspace?customer_id=<id>&step=order-scope-documents
   or reach this step normally.
2. Confirm the three section links appear on the left:
   - Equipment
   - Requirements
   - Order documents
3. Confirm the three section cards appear on the right.
4. Click Equipment.
5. Confirm scroll goes to Equipment section.
6. Click Requirements.
7. Confirm scroll goes to Requirements section.
8. Click Order documents.
9. Confirm scroll goes to Order documents section.
10. Scroll manually with mouse wheel.
11. Confirm the left nav remains visible/sticky.
12. Confirm the active link changes automatically based on the visible section.
13. Confirm the forms in all three sections still work:
   - add/save equipment line
   - add/save requirement line
   - document actions still visible
14. Confirm Next and Previous still work.
15. Confirm no console errors.

If browser QA cannot be run:
- explicitly say manual QA was not run
- provide deterministic tests using scrollIntoView and IntersectionObserver mocks.

Final report must include:
- manual QA status
- whether the Employees Overview sticky-nav pattern was reused directly
- any responsive limitation
- confirmation that no business logic in the three sections was changed