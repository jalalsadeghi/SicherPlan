/review

Please review the embedded Customer Orders workspace refactor.

Check:
1. Does clicking New order inside Customer detail > Orders stay on /admin/customers?
2. Does it keep customer_id, tab=orders, and pageKey=customers:detail:<customerId>?
3. Does it avoid opening the separate Order workspace top tab?
4. Does the embedded order workspace render inside the Orders tab?
5. Does Edit order also open inside the Orders tab?
6. Does Cancel/Back return to the Orders list inside the same tab?
7. Does Save/Complete refresh the order list and keep the user in the same Customer tab?
8. Is the legacy /admin/customers/order-workspace route still compatible?
9. Did we avoid backend/API changes?
10. Are Dashboard and Overview tabs unaffected?
11. Is Customer Overview side navigation unaffected?
12. Are customer list tab and customer detail pageKey behavior unchanged?
13. Which tests were added/updated and what commands were run?

Please report:
- root cause of the confusing navigation
- files changed
- implementation summary
- route/query behavior before and after
- test results
- remaining risks