We still have the Vite resolve error:

[plugin:builtin:vite-resolve] "./route-cached" is not exported under the conditions ["module", "browser", "development", "import"] from package .../web/apps/web-antd/node_modules/@vben/layouts

Codex previously reported that the export was fixed, but the current repository state still shows that this is not true, or the dev server is resolving a stale package.json.

Important facts to verify:
1. In web/packages/effects/layouts/package.json, the exports field must include "./route-cached".
2. In web/apps/web-antd/node_modules/@vben/layouts/package.json, the exports field used by Vite must also include "./route-cached".
3. In web/packages/effects/layouts/src/index.ts, route-cached should be exported from the root if app code imports from @vben/layouts.
4. In web/packages/effects/layouts/src/route-cached/index.ts, all public route-cache APIs used by app code must be exported.

Current error means Vite is resolving an import like:
import { ... } from '@vben/layouts/route-cached';

but the resolved package.json does not expose that subpath.

Task:
Do a real filesystem-level diagnosis and fix.

Step 1 — Find all imports:
Run from repo root:
grep -R "@vben/layouts/route-cached" -n web/apps web/packages
grep -R "useRouteCacheSession\|useIsRouteCachePaneActive\|useRouteCacheScrollTarget\|RouteCachePane" -n web/apps web/packages

List every file that imports route-cache APIs.

Step 2 — Inspect the source package.json:
Print:
cat web/packages/effects/layouts/package.json

Confirm whether it contains:
"./route-cached": {
  "types": "./src/route-cached/index.ts",
  "default": "./src/route-cached/index.ts"
}

If it does not, add it.

Expected exports:
{
  ".": {
    "types": "./src/index.ts",
    "default": "./src/index.ts"
  },
  "./route-cached": {
    "types": "./src/route-cached/index.ts",
    "default": "./src/route-cached/index.ts"
  }
}

Step 3 — Inspect the resolved package used by Vite:
Run:
cat web/apps/web-antd/node_modules/@vben/layouts/package.json
readlink web/apps/web-antd/node_modules/@vben/layouts || true
realpath web/apps/web-antd/node_modules/@vben/layouts/package.json

This is critical. The browser error references:
web/apps/web-antd/node_modules/@vben/layouts/package.json

If this resolved package.json does not include "./route-cached", Vite will continue failing even if the source package.json was changed elsewhere.

Step 4 — If node_modules is stale:
Run from web root:
pnpm install

If still stale:
rm -rf web/apps/web-antd/node_modules/.vite
rm -rf web/node_modules/.vite
pnpm --filter @vben/web-antd dev

Do not delete lockfiles unless absolutely necessary.

Step 5 — Export public APIs:
Update:
web/packages/effects/layouts/src/route-cached/index.ts

It must export every public route-cache API used by web-antd, for example:
export { default as CachedRouteRenderer } from './cached-route-renderer.vue';
export { default as RouteCachedPage } from './route-cached-page.vue';
export { default as RouteCachedView } from './route-cached-view.vue';
export { default as RouteCachePane } from './route-cache-pane.vue';
export * from './route-cache-session';
export * from './route-cache-scroll';

Only export files that actually exist. If a listed file does not exist, either create it as intended by the tab-session implementation or remove imports that use it.

Step 6 — Root export:
Update:
web/packages/effects/layouts/src/index.ts

Add:
export * from './route-cached';

This is needed if any code imports route-cache APIs from '@vben/layouts'.

Step 7 — Fix import style:
Choose one public import style and make it consistent.

Preferred:
import { useIsRouteCachePaneActive } from '@vben/layouts/route-cached';

This requires the "./route-cached" subpath export.

Alternative:
import { useIsRouteCachePaneActive } from '@vben/layouts';

This requires root export from src/index.ts.

Do not import package internals using long relative paths from web-antd into web/packages/effects/layouts/src/...

Step 8 — Validate:
Run:
pnpm --filter @vben/web-antd dev

Then verify the old error is gone:
"./route-cached" is not exported

Also run the focused tests:
pnpm --dir web/packages/effects/layouts exec vitest run src/route-cached/route-cache-pane.test.ts src/route-cached/cached-route-renderer.test.ts src/route-cached/route-cache-scroll.test.ts src/route-cached/route-cached-view.test.ts
pnpm --dir web/apps/web-antd exec vitest run src/views/sicherplan/dashboard/index.test.ts src/router/routes/modules/sicherplan.test.ts src/views/sicherplan/admin-module-view.test.ts

Acceptance criteria:
- web/packages/effects/layouts/package.json exports "./route-cached".
- web/apps/web-antd/node_modules/@vben/layouts/package.json also exposes "./route-cached" or is a symlink to the updated source package.
- route-cached/index.ts exports all public route-cache APIs used by app code.
- src/index.ts exports './route-cached' if root imports are used.
- No import from @vben/layouts/route-cached fails.
- Dev server no longer shows the Vite resolve error.
- No backend/API changes.
- Tab-session behavior remains unchanged.