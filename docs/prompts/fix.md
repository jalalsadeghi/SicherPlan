Please fix the production API base/path duplication bug in SicherPlan web-antd without breaking localhost development.

Problem:
- On the deployed domain, Core Admin requests are going to:
  /api/api/core/admin/tenants
- Backend logs confirm:
  GET /api/api/core/admin/tenants -> 404
- The correct route should be:
  /api/core/admin/tenants
- Authentication works, so the backend is up. The issue is frontend URL construction in production.

Likely cause:
- apiBaseUrl in production is set to "/api"
- legacy API paths in sicherplan-legacy still already start with "/api/..."
- final URL becomes "/api/api/..."

Tasks:
1. Inspect:
   - web/apps/web-antd/src/sicherplan-legacy/config/env.ts
   - web/apps/web-antd/src/sicherplan-legacy/api/coreAdmin.ts
   - any related legacy API clients using fetch(`${webAppConfig.apiBaseUrl}${path}`)
2. Make production URL construction consistent so "/api" is not duplicated.
3. Keep localhost dev unchanged:
   - local dev should still work with http://localhost:8000
4. Prefer the minimal, low-risk fix:
   - either keep legacy paths as "/api/..." and ensure production apiBaseUrl does NOT include "/api"
   - or add a safe URL join/normalization helper that prevents duplicate "/api"
5. Do not break auth or other legacy API modules.
6. Document the exact required values for:
   - VITE_SP_API_BASE_URL in development
   - VITE_SP_API_BASE_URL in production
7. Summarize:
   - touched files
   - exact fix
   - rebuild/redeploy requirement
   - cache invalidation note

Important:
- Do not break localhost.
- Keep the fix minimal.
- Do not redesign unrelated routing.