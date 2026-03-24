Please investigate and fix the SicherPlan web production artifact mismatch problem.

Problem:
- The deployed frontend index.html references hashed assets that do not exist in the final web container.
- Example:
  - index.html references /jse/index-index-_VBnAfr8.js and /js/env-CzAGrQv8.js
  - but those files are missing from /usr/share/nginx/html
- As a result, the browser gets 404 on startup assets and the app never bootstraps.

Context:
- Backend is healthy.
- The issue is in the frontend build/deploy artifact consistency.
- The deployed web app is the web-antd app.
- In the checked project copy, web/apps/web-antd/dist.zip contains different asset hashes than the deployed container, which suggests the deployed image is not built from a clean, matching artifact set.

Tasks:
1. Inspect the frontend build pipeline and Docker image build inputs.
2. Ensure the production image is built from one clean web-antd dist output only.
3. Add a verification step in the build/deploy process:
   - parse index.html
   - verify every referenced /js/... and /jse/... asset actually exists in the final image
4. Prevent mixed or stale assets from older builds.
5. Summarize:
   - root cause
   - touched files
   - exact build/deploy changes
   - verification command to run on the server after deployment

Important:
- Do not modify unrelated business logic.
- Focus on build artifact consistency and production image correctness.