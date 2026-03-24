Please fix the production API base configuration for the SicherPlan web frontend so Core Admin no longer calls localhost.

Context:
- Project: SicherPlan
- Frontend app: web/apps/web-antd
- Current production symptom:
  - Core Admin shows:
    "The core administration page could not complete the action."
  - Browser network shows requests like:
    OPTIONS http://localhost:8000/api/core/admin/tenants -> 400
  - Authentication works correctly against:
    https://secur.lumina-core.de/api/auth/me
- Conclusion:
  - The deployed frontend bundle is using the localhost fallback API base instead of the production server API base.

Relevant code:
- web/apps/web-antd/src/sicherplan-legacy/config/env.ts
- current fallback:
  VITE_SP_API_BASE_URL ?? "http://localhost:8000"

Tasks:
1. Inspect the production build configuration for web/apps/web-antd
2. Ensure production never falls back to localhost:8000
3. Make production use the correct API base:
   - preferably same-origin if supported by deployment
   - otherwise the explicit production API origin
4. Keep localhost:8000 only for local development
5. Verify all Core Admin API calls use the corrected base URL
6. Summarize:
   - touched files
   - required env vars
   - exact build/redeploy steps
   - any cache/CDN invalidation needed after deployment

Important:
- Do not redesign unrelated app logic
- Keep the fix minimal and deployment-focused