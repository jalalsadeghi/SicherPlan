You are working in the SicherPlan repository.

Repository:
https://github.com/jalalsadeghi/SicherPlan

Current local state:
- Dependencies are now installed.
- Node is v22.22.2 through nvm.
- The repository `.nvmrc` expects Node 22.x.
- `pnpm build` starts and many packages build successfully.
- The previous missing dependency error (`cross-env: not found`) is no longer the main issue.
- The previous Vite missing module error may have been caused by incomplete node_modules, but now the current blocking problem is different.

Current build error summary:

`pnpm build` runs root turbo build.
Several packages build successfully, including `@vben/web-antdv-next`.

Warnings appear during `@vben/web-antdv-next` build:

Big integer literals are not available in the configured target environment.

But `@vben/web-antdv-next` finishes successfully with:

✓ built in 1m 12s

The final failure is:

ERROR @vben/web-antd#build: command (/home/jey/Projects/SicherPlan/web/apps/web-antd) /home/jey/.nvm/versions/node/v22.22.2/bin/pnpm run build exited (1)

Tasks: 13 successful, 18 total
Failed: @vben/web-antd#build

Important interpretation to validate:
The BigInt warnings from `@vben/web-antdv-next` are probably not the root cause because that package completes successfully. The real failure is inside the main app package `@vben/web-antd`, but the root turbo output does not show the complete error.

Repository facts:
- `web/package.json` root build script runs `cross-env NODE_OPTIONS=--max-old-space-size=8192 turbo build`.
- `web/package.json` also has `build:antd`.
- `web/apps/web-antd/package.json` has build script: `pnpm vite build --mode production`.
- `web/apps/web-antd/vite.config.ts` defines alias `@` to `./src/sicherplan-legacy` and proxies only `/api` to `http://localhost:8000`.

Task:
1. Do not change product/business code yet.
2. Do not change backend APIs, tenant logic, customer/planning domain logic, or database logic.
3. First isolate the real `@vben/web-antd` build error.
4. Run:
   - `cd ~/Projects/SicherPlan/web`
   - `node -v`
   - `pnpm -v`
   - `pnpm -F @vben/web-antd run build 2>&1 | tee /tmp/web-antd-build.log`
   - `tail -n 160 /tmp/web-antd-build.log`
5. If the direct package build still hides the error, run:
   - `pnpm turbo build --filter=@vben/web-antd --force --output-logs=full 2>&1 | tee /tmp/web-antd-turbo-build.log`
   - `tail -n 200 /tmp/web-antd-turbo-build.log`
6. Identify the first real error line inside `@vben/web-antd`.
7. Classify the failure:
   - dependency/tooling issue
   - TypeScript/typecheck issue
   - Vite/Rollup build issue
   - unresolved import or alias issue
   - asset/path issue
   - app-specific SicherPlan customization issue under `src/sicherplan-legacy`
8. Only after identifying the exact root cause, propose the smallest possible fix.
9. If a fix is needed:
   - keep the changes narrowly scoped to `@vben/web-antd`
   - preserve Vben Admin conventions
   - preserve SicherPlan theme/i18n rules
   - avoid unrelated formatting or refactoring
10. Run verification after the fix:
   - `pnpm -F @vben/web-antd run build`
   - if that passes, `pnpm build`
11. Report:
   - root cause
   - evidence
   - exact file(s) changed
   - whether product code was touched
   - verification result
   - any remaining warnings, especially BigInt warnings, and whether they are blocking or non-blocking

Output format:
- Root cause
- Evidence from logs
- Files inspected
- Files changed
- Verification commands
- Result
- Remaining risk