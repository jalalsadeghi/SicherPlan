You are working in the SicherPlan monorepo.

Goal:
Improve the P-02 Orders & Planning Records document tabs so uploaded documents are no longer passive rows.
Implement a usable document interaction flow for both:
- Order documents
- Planning record documents

Source of truth:
1) web/apps/web-antd/src/sicherplan-legacy/views/PlanningOrdersAdminView.vue
2) web/apps/web-antd/src/sicherplan-legacy/api/planningOrders.ts
3) Uploaded/openapi-backed behavior already documented in the project:
   - platform docs support document get/version/download/link
4) Keep existing permission model and current page structure intact.

Important current problem:
In the documents tabs, document rows are rendered as plain divs (`planning-orders-doc-row`) with no click handler, no selected state, and no actions.
Users can upload/link documents, and list rows are shown, but they cannot inspect or download them from P-02.

Required implementation:
1. In PlanningOrdersAdminView.vue:
   - Make document rows interactive for both order and planning-record document lists.
   - Replace passive `div.planning-orders-doc-row` rows with clickable/selectable buttons, similar to other list rows in the page.
   - Add selected state for:
     - selectedOrderDocumentId
     - selectedPlanningDocumentId
   - When a document row is clicked, show a detail/action panel below the list in the same tab.
   - In that panel show at minimum:
     - document title
     - document id
     - current version number
     - status
     - source label if available
   - Add actions:
     - Download current version
     - Copy document ID
     - Clear selection
   - Show empty-state text if no document is selected.

2. In web/apps/web-antd/src/sicherplan-legacy/api/planningOrders.ts:
   - Add a typed helper to download the current document version through the platform docs API:
     GET /api/platform/tenants/{tenant_id}/documents/{document_id}/versions/{version_no}/download
   - Implement this as a blob download helper, not JSON.
   - Also add a helper to fetch document metadata if needed only when strictly necessary.
   - Reuse existing PlanningDocumentRead shape where possible.

3. In PlanningOrdersAdminView.vue:
   - Wire the new download action to the new API helper.
   - Use the selected row’s `current_version_no`.
   - Trigger a browser download with a safe fallback filename derived from document title.
   - Show feedback toast on success/failure using the existing feedback pattern.

4. Styling:
   - Keep styling aligned with existing planning page UI.
   - Selected document rows should visibly match the existing selected list-row behavior.
   - Do not introduce a new page or modal unless absolutely necessary.
   - Keep layout responsive.

5. Permissions:
   - Respect current `actionState.canManageOrderDocs` / `actionState.canManagePlanningDocs` for upload/link flows.
   - Reading/downloading should follow existing readable scope; do not loosen authorization.
   - Do not invent new roles or permission keys.

Non-goals for this task:
- Do NOT implement delete/unlink unless already supported by existing API.
- Do NOT implement metadata edit/update label unless already supported by existing API.
- Do NOT redesign the whole P-02 page.
- Do NOT touch unrelated modules.

Optional enhancement if low-risk:
- Render current version and status directly in each row subtitle.
- Add a very small “Download” inline action on the selected document only.

Acceptance criteria:
1. Clicking an order document row visibly selects it.
2. Clicking a planning-record document row visibly selects it.
3. A detail/action area appears after selection.
4. Download current version works for both order and planning-record documents.
5. No regression in upload/link flows.
6. No TypeScript/Vue compile errors.
7. Keep code clean and localized to the planning orders feature.

Deliverables:
- Updated PlanningOrdersAdminView.vue
- Updated planningOrders.ts
- Any minimal supporting types/utilities required
- Brief summary of what changed and any limitations still remaining