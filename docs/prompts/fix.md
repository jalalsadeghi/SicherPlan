You are working in the SicherPlan repository.

Goal
----
In the Planning admin page, make the checkpoint `Latitude` and `Longitude` fields render in the same row.

Primary file
------------
- `web/apps/web-antd/src/sicherplan-legacy/views/PlanningOpsAdminView.vue`

Problem
-------
The checkpoint forms currently use the shared 6-column detail grid, but the current field spans cause `Longitude` to wrap to the next line.
This is visible in the child checkpoint form under selected `Patrol routes`, and the same layout pattern should be made consistent in the create-mode checkpoint form too.

What to change
--------------
Update the checkpoint form layout in BOTH places inside `PlanningOpsAdminView.vue`:

1. The create-mode checkpoint block:
   `editorEntityKey === 'patrol_checkpoint'`

2. The child checkpoint form under:
   `entityKey === 'patrol_route' && selectedRecord && !isCreatingRecord`

Make these layout changes:

- Keep:
  - `Sequence` and `Checkpoint code` on one row
- Make:
  - `Label` full width
- Put:
  - `Latitude` and `Longitude` on the same row
- Keep:
  - `Pick on map` on its own full-width row below them
- Then keep the remaining fields below:
  - `Scan type`
  - `Expected token value`
  - `Minimum dwell (sec)`
  - `Notes`

Recommended implementation
--------------------------
Use the existing grid utility classes already present in this file.

For both checkpoint form blocks:
- Change the `Label` field from half-width to full-width (`field-stack--wide`)
- Change both `Latitude` and `Longitude` fields from third-width to half-width (`field-stack--half`)
- Keep the map action wrapper as full-width

Example target structure order:
- Sequence -> `field-stack--third`
- Checkpoint code -> `field-stack--third`
- Label -> `field-stack--wide`
- Latitude -> `field-stack--half`
- Longitude -> `field-stack--half`
- Pick on map -> full width
- Scan type -> `field-stack--half`
- Expected token value -> `field-stack--half`
- Minimum dwell (sec) -> `field-stack--half`
- Notes -> `field-stack--wide`

Constraints
-----------
- Do not change backend code.
- Do not change the shared grid system globally unless necessary.
- Keep the existing responsive mobile behavior.
- Apply the same layout logic to both checkpoint forms for consistency.

Acceptance criteria
-------------------
- In the patrol-route checkpoint form, `Latitude` and `Longitude` are on the same row.
- In checkpoint create-mode, the same alignment is used.
- `Pick on map` remains directly below the coordinate row.
- No regression in the rest of the Planning admin form.

After coding
------------
Provide a short summary of:
- which template lines/blocks were updated
- which field-span classes were changed
- whether both checkpoint forms were aligned consistently