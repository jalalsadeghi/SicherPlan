Please fix the exact production API base URL bug in SicherPlan web-antd.

Root cause already identified:
- In web/apps/web-antd/.env.production:
  - VITE_SP_ENV=staging
  - VITE_SP_API_BASE_URL=
- In web/apps/web-antd/src/sicherplan-legacy/config/env.ts:
  - resolveApiBaseUrl() returns "/api" when env is staging and VITE_SP_API_BASE_URL is empty
- Legacy SicherPlan API paths already start with "/api/..."
- Therefore production builds currently generate:
  /api + /api/core/admin/tenants
  => /api/api/core/admin/tenants

Required fix:
1. Update resolveApiBaseUrl() so that when:
   - env !== development
   - and VITE_SP_API_BASE_URL is empty
   it returns an empty string instead of "/api"
2. Keep localhost development unchanged:
   - development fallback must remain http://localhost:8000
3. Do not change backend routes.
4. Do not redesign unrelated routing or auth logic.
5. Summarize:
   - touched files
   - exact logic change
   - expected production request after rebuild
   - rebuild/redeploy steps

Expected result after rebuild:
- production requests should become:
  /api/core/admin/tenants
- not:
  /api/api/core/admin/tenants