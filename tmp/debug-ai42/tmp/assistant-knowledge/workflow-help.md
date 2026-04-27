# Assistant Workflow Help

This generated source summarizes verified workflow seeds used by the assistant.

## Customer creation workflow (customer_create)

- linked_page_ids: C-01
- Customer creation starts in the Customers workspace: Prime customer master creation belongs to the Customers workspace inside the current tenant. [page C-01]

## Customer planning setup workflow (customer_plan_create)

- linked_page_ids: C-01, P-02, P-03
- Customer context is created or selected first: A customer context must exist before tenant staff can create planning records for that customer. [page C-01]
- Planning records and orders are prepared next: Customer-facing planning records and order setup continue in Orders & Planning Records. [page P-02]
- Detailed shift planning follows after the planning record exists: Detailed shift structure usually continues in Shift Planning after the customer planning record is ready. [page P-03]

## Employee creation workflow (employee_create)

- linked_page_ids: E-01
- Employees workspace owns employee creation: Operational employee master creation starts in the Employees workspace. [page E-01]
- Verified create action exists: The verified create action is registered as employees.create.open on the Employees workspace. [page E-01]

## Employee assignment workflow (employee_assign_to_shift_workflow)

- linked_page_ids: E-01, P-02, P-03, P-04, P-05
- Employee record must exist first: The employee must exist in the Employees workspace before staffing can assign that person to a shift. [page E-01]
- Order and planning record context is prepared first: Orders and planning records are managed in the Orders & Planning Records workspace. [page P-02]
- Shift structure is prepared in Shift Planning: Concrete shift planning lives in the Shift Planning workspace. [page P-03]
- Assignment happens in the Staffing Board: Employee-to-shift assignment is performed in the Staffing Board & Coverage workspace. [page P-04]
- Release and downstream outputs happen after staffing: Dispatch outputs and subcontractor release follow-up are handled in the dispatch and release workspace after staffing decisions are made. [page P-05]

## Order creation workflow (order_create)

- linked_page_ids: C-01, P-02, P-03, P-04
- Orders are created in planning order workspace: Customer orders and planning records are handled in the Orders & Planning Records workspace. [page P-02]
- Customer context is required: Order creation depends on an existing customer context and planning record ownership inside the current tenant. [page C-01]
- Orders lead into shift planning and staffing: After order setup, follow-up work usually continues in Shift Planning and Staffing Board pages. [page P-03]

## Contract or document registration workflow (contract_or_document_register)

- linked_page_ids: PS-01, C-01, P-02, S-01
- Contract handling is document-centered and context-dependent: The current repository does not verify one standalone contract module. Contract-like records are handled as documents or attachments linked to customer, planning, subcontractor, or other business context. [page PS-01]
- Platform Services is the safe shared document reference: Platform Services is the conservative shared workspace candidate for document create, versioning, and linkage when the exact contract subtype is still unclear. [page PS-01]
- Customer or order context may still be required: If the contract belongs to a customer relationship, customer history, or a planning record/order package, related context also lives in Customers or Orders & Planning Records. [page C-01]
- Subcontractor context may apply for partner agreements: If the question is about a subcontractor agreement, the subcontractor workspace is also a plausible context and should be clarified instead of guessed. [page S-01]

## Shift creation and release workflow (shift_create_or_release)

- linked_page_ids: P-03, P-04, P-05
- Shift setup lives in Shift Planning: Concrete shifts are created and edited in the Shift Planning workspace. [page P-03]
- Employee-app visibility depends on release and staffing state: Shift visibility for employee app depends on release state, staffing state, and downstream visibility checks. [page P-04]
- Dispatch outputs and releases are downstream: Dispatch outputs and release follow-up are managed in the dispatch and release workspace. [page P-05]
