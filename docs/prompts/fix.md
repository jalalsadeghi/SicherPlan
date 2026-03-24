Please inspect the SicherPlan web stage deployment path carefully and fix the current broken frontend deployment.

Confirmed symptoms:
- Public _app.config.js still points to https://mock-napi.vben.pro/api
- index.html references hashed assets such as:
  /jse/index-index-CFEY1UVh.js
  /js/src-BiuTFOay.js
  /js/utils-jy9g1xwR.js
  /js/src-Do5taltB.js
- Browser receives text/html instead of JavaScript for those module files
- This means the deployed dist is inconsistent and/or nginx is serving index.html as fallback for missing assets

Tasks:
1) Search the entire web tree for:
   mock-napi.vben.pro
   and remove or replace all real runtime usages with /api
2) Inspect the committed dist under:
   web/apps/web-antd/dist
   and ensure no file references mock-napi.vben.pro
3) Ensure index.html only references asset files that actually exist in dist
4) If the current dist is stale or inconsistent, regenerate it from the correct source build path
5) Update the stage nginx config so static assets return 404 when missing, instead of falling back to index.html
6) Add a CI safeguard that fails if:
   - mock-napi.vben.pro exists anywhere in web/apps/web-antd/dist
   - or index.html references missing assets
7) Summarize:
   - which source files contained the bad API URL
   - which dist files were inconsistent
   - which nginx rule caused MIME confusion
   - what was changed