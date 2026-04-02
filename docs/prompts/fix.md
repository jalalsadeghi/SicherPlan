The previous change introduced an import-resolution error in web/apps/web-antd.

Current error
[plugin:vite:import-analysis] Failed to resolve import "@/sicherplan-legacy/components/SicherPlanLoadingOverlay.vue" from "src/sicherplan-legacy/views/CustomerAdminView.vue"

Root cause to verify first
In web/apps/web-antd/tsconfig.json, the alias mapping is:
- "#/*" -> "./src/*"
- "@/*" -> "./src/sicherplan-legacy/*"

That means an import like:
@/sicherplan-legacy/components/SicherPlanLoadingOverlay.vue
incorrectly resolves to:
src/sicherplan-legacy/sicherplan-legacy/components/...
So the import path is structurally wrong.

Also verify exact filename case on disk.
This repo is being run on Linux/WSL, so case must match exactly.
If the file is named SicherPlanLoadingOverlay.vue, every import must use the same exact casing.

Task
Fix the loading-overlay integration cleanly and make the project build again.

Required steps
1. Inspect the actual local file path that was created for the overlay component.
   Check whether the file exists in one of these locations:
   - web/apps/web-antd/src/sicherplan-legacy/components/SicherPlanLoadingOverlay.vue
   - web/apps/web-antd/src/components/SicherPlanLoadingOverlay.vue
   - or some differently cased variant

2. Normalize the component location and imports.
   Preferred target location:
   - web/apps/web-antd/src/sicherplan-legacy/components/SicherPlanLoadingOverlay.vue

   If you keep the file there, then the correct import from legacy views must be:
   - "@/components/SicherPlanLoadingOverlay.vue"

   because @ already points to src/sicherplan-legacy.

   Alternative acceptable fix:
   - use a relative import such as "../components/SicherPlanLoadingOverlay.vue"
   But prefer the alias form if it matches existing code style.

3. Fix all broken references consistently.
   At minimum inspect and fix:
   - web/apps/web-antd/src/sicherplan-legacy/views/CustomerAdminView.vue
   - web/apps/web-antd/src/sicherplan-legacy/views/EmployeeAdminView.vue
   - web/apps/web-antd/src/sicherplan-legacy/components/sicherplanLoadingOverlay.test.ts
   - any other file changed by the previous patch that imports this component

4. Verify the component filename casing and test filename casing.
   Use one naming convention consistently:
   - component file: SicherPlanLoadingOverlay.vue
   - test file may stay sicherplanLoadingOverlay.test.ts if desired, but imports must match the component file’s exact case

5. Do not change the functional behavior of the loading overlay unless needed for the fix.
   Keep the previously implemented behavior:
   - page/workspace-local translucent overlay
   - underlying form still visible
   - pointer interaction blocked while busy
   - aria-busy on the covered region
   - reuse existing loading flags already wired in EmployeeAdminView and CustomerAdminView

6. After fixing imports, run verification.
   Please run and report the result of:
   - a targeted build or vite check for web/apps/web-antd
   - the focused tests related to:
     - EmployeeAdminView
     - CustomerAdminView
     - SicherPlanLoadingOverlay
   - if a full build is too heavy, run the narrowest reliable command that proves the import issue is gone

7. Output format
   Before editing, briefly state:
   - actual overlay component path found on disk
   - incorrect imports found
   - corrected import strategy

   After editing, report:
   - changed files
   - exact corrected import strings
   - build/test result
   - whether any remaining alias inconsistencies were found