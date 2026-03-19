#!/usr/bin/env bash
set -euo pipefail

test -f web/.env.example
test -f web/src/config/env.ts

grep -q '^VITE_SP_ENV=' web/.env.example
grep -q '^VITE_SP_API_BASE_URL=' web/.env.example
grep -q 'export const webAppConfig' web/src/config/env.ts
grep -q 'defaultLocale' web/src/config/env.ts
grep -q 'darkPrimary' web/src/config/env.ts
