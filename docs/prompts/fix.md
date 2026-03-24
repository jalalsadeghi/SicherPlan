Please fix the SicherPlan web production Docker image so the deployed frontend includes the correct built assets.

Problem:
- The deployed domain serves /index.html, but the JS bundles referenced by index.html are missing.
- Browser errors show 404s for files like:
  - /jse/index-index-*.js
  - /js/env-*.js
- Inside the running web container, /usr/share/nginx/html currently contains index.html but not the referenced bundle files.
- This means the production web image is copying the wrong build output or an incomplete build output.

Relevant file:
- web/scripts/deploy/Dockerfile

Important code fact:
- The current production stage copies:
  COPY --from=builder /app/playground/dist /usr/share/nginx/html
- But the deployed app is the SicherPlan web-antd application, not the playground app.
- The correct built output likely lives under:
  /app/apps/web-antd/dist

Tasks:
1. Inspect the monorepo build outputs after the build step.
2. Confirm which app is the actual deployed SicherPlan frontend.
3. Update the Dockerfile production COPY step so it copies the correct dist directory for the deployed app.
4. Verify that the final nginx image contains:
   - /usr/share/nginx/html/index.html
   - /usr/share/nginx/html/jse/...
   - /usr/share/nginx/html/js/...
5. Do not break local development.
6. Summarize:
   - touched files
   - exact path changes
   - rebuild/redeploy steps
   - cache purge note for browser/CDN

Important:
- Keep the fix minimal.
- Do not redesign nginx unless necessary.
- Focus on the production image contents.