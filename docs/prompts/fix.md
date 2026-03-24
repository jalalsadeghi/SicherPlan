Please fix the duplicate /api production URL bug in SicherPlan web-antd without breaking localhost development.

Problem:
- In production, Core Admin requests are sent to:
  /api/api/core/admin/tenants
- The correct URL should be:
  /api/core/admin/tenants
- Backend returns 404 because the current route is wrong.
- Browser confirms the failing request comes from the built frontend chunk:
  coreAdmin-*.js
- Backend health is fine; this is a frontend production URL construction bug.

Tasks:
1. Inspect:
   - web/apps/web-antd/src/sicherplan-legacy/config/env.ts
   - web/apps/web-antd/src/sicherplan-legacy/api/coreAdmin.ts
   - any shared fetch/http helper used by the legacy SicherPlan API layer
2. Find where apiBaseUrl is joined with paths that already begin with /api/.
3. Apply the minimal fix so production no longer generates /api/api/...
4. Keep localhost dev unchanged:
   - local dev should still use http://localhost:8000
5. Ensure production config does NOT require VITE_SP_API_BASE_URL=/api if paths already include /api.
6. Summarize:
   - touched files
   - exact logic change
   - required production env value
   - required dev env value
   - rebuild/redeploy steps

Important:
- Do not redesign unrelated routing.
- Do not break local dev.
- Keep the fix minimal and production-safe.