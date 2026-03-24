Please fix the remaining duplicate /api production URL bug in SicherPlan web-antd.

Current confirmed behavior:
- The correct backend route exists:
  /api/core/admin/tenants
- Direct browser access to that route returns invalid_access_token, which confirms the route exists but requires auth.
- However, the deployed frontend still sends:
  /api/api/core/admin/tenants
- That wrong URL returns 404.
- Therefore the remaining problem is still in the built frontend production URL construction.

Tasks:
1. Inspect the legacy web client URL construction for Core Admin and shared API helpers.
2. Confirm whether client paths already include "/api/...".
3. Ensure production apiBaseUrl does not prepend another "/api" on top of those paths.
4. Keep localhost development unchanged.
5. Verify the final production bundle no longer contains requests to /api/api/...
6. Summarize:
   - touched files
   - exact production env value
   - exact development env value
   - rebuild/redeploy steps
   - cache invalidation steps

Important:
- Do not change backend routes.
- Do not break localhost.
- Fix the frontend production bundle only.