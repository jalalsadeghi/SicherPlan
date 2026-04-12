You are working in the SicherPlan monorepo on the latest main branch.

Task:
Fix the admin/planning bug where the "Notes" field for Planning Setup -> Requirement types is saved by the user but does not come back when reopening the record in Edit mode.

Context already observed:
- In `web/apps/web-antd/src/sicherplan-legacy/views/PlanningOpsAdminView.vue`, the Requirement Type editor uses `draft.notes` for the Notes textarea.
- The same view hydrates edit state via `syncDraft(record)` and reads `record.notes`.
- The same view sends `notes` in the base payload used for create/update.
- In `web/apps/web-antd/src/sicherplan-legacy/api/planningAdmin.ts`, the frontend detail type already expects `notes?: string | null`.
- In backend planning schemas, RequirementType currently uses `description` instead of `notes`, while sibling planning setup entities use `notes`.
- This strongly suggests a frontend/backend contract mismatch for `requirement_type`.

Your job:
1. Verify the actual root cause by tracing the full round-trip for `requirement_type`:
   - frontend form
   - frontend API typing/client
   - backend router
   - backend schemas
   - service layer
   - repository/model mapping
   - any serializer/read-model layer
   - import/export/template helpers
2. Apply the fix in the most correct and minimal-safe way.
3. Prefer the canonical API contract `notes` for requirement_type, to match the UI and sibling planning entities.
4. Preserve backward compatibility where reasonable:
   - If legacy payloads or stored data still use `description`, accept/map them safely during the transition.
   - Do not lose existing persisted values.
5. Update any import/export/template/header logic for requirement_type so it is consistent with the final contract.
   - If import currently uses `description`, support legacy aliasing if practical, but standardize outward-facing behavior to `notes`.
6. Add or update tests to prove the fix.

Files to inspect first:
- `web/apps/web-antd/src/sicherplan-legacy/views/PlanningOpsAdminView.vue`
- `web/apps/web-antd/src/sicherplan-legacy/api/planningAdmin.ts`
- `web/apps/web-antd/src/features/planning/*` or legacy helper files related to planning admin/import templates
- `backend/app/modules/planning/schemas.py`
- `backend/app/modules/planning/router*.py`
- `backend/app/modules/planning/service*.py`
- `backend/app/modules/planning/repository*.py`
- `backend/app/modules/planning/models*.py`
- relevant tests under backend and web if present

Acceptance criteria:
- When a user creates a Requirement Type and fills Notes, the value is persisted.
- When the same Requirement Type is reopened in Edit mode, the Notes textarea is populated with the saved value.
- Updating Notes persists the new value and shows it again on the next Edit open.
- Existing legacy values stored under `description` are not lost.
- No regression for other Planning Setup entities.
- Import/export/template behavior for requirement_type is consistent with the final chosen contract.

Implementation guidance:
- Do not patch only the textarea binding.
- Fix the contract mismatch at the correct layer(s).
- If the DB column is still `description`, decide whether:
  a) API/model mapping to `notes` is enough, or
  b) a migration/rename is required.
  Choose the safest option and explain why.
- Keep changes scoped to this bug unless a nearby inconsistency must be corrected to complete the fix.

Validation required:
After implementing, explicitly validate whether the original hypothesis (“frontend expects `notes`, backend uses `description` for requirement_type”) was correct.
If it was not fully correct, explain the true root cause and what you changed instead.

Please return:
1. Root-cause summary
2. Files changed
3. Why the chosen fix is correct
4. Tests added/updated
5. Any compatibility notes or migration notes