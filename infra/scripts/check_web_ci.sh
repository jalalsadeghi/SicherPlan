#!/usr/bin/env bash
set -euo pipefail

test -f web/Dockerfile.stage
test -f web/scripts/deploy/Dockerfile
test -f web/scripts/deploy/verify-dist-assets.sh
test -f web/nginx.stage.conf
test -f web/apps/web-antd/.env.production
test -f web/apps/web-antd/dist/index.html

grep -q 'COPY web/apps/web-antd/dist /usr/share/nginx/html' web/Dockerfile.stage
grep -q 'COPY --from=builder /app/apps/web-antd/dist /usr/share/nginx/html' web/scripts/deploy/Dockerfile
grep -q 'RUN rm -rf /app/apps/web-antd/dist' web/scripts/deploy/Dockerfile
grep -q 'RUN rm -rf /usr/share/nginx/html/\*' web/scripts/deploy/Dockerfile
grep -q '/usr/local/bin/verify-web-dist /usr/share/nginx/html' web/scripts/deploy/Dockerfile
grep -q 'Current stage frontend image expects committed dist assets' web/Dockerfile.stage
grep -q 'proxy_pass http://backend:8000/api/' web/nginx.stage.conf
grep -q 'location = /_app.config.js' web/nginx.stage.conf
grep -q 'location ^~ /js/' web/nginx.stage.conf
grep -q 'location ^~ /jse/' web/nginx.stage.conf
grep -q 'try_files \$uri \$uri/ /index.html;' web/nginx.stage.conf
grep -q '^VITE_SP_ENV=staging$' web/apps/web-antd/.env.production
grep -q '^VITE_SP_API_BASE_URL=$' web/apps/web-antd/.env.production
grep -Fq 'function resolveApiBaseUrl' web/apps/web-antd/src/sicherplan-legacy/config/env.ts
grep -Fq 'replace(/\/api\/?$/, "")' web/apps/web-antd/src/sicherplan-legacy/config/env.ts
grep -Fq 'return env === "development" ? "http://localhost:8000" : ""' web/apps/web-antd/src/sicherplan-legacy/config/env.ts

if rg -n 'mock-napi\.vben\.pro' web/apps/web-antd/dist; then
  echo "web/apps/web-antd/dist still contains mock-napi.vben.pro runtime references." >&2
  exit 1
fi

if rg -n '/api/api/' web/apps/web-antd/dist; then
  echo "web/apps/web-antd/dist still contains duplicated /api/api/ paths." >&2
  exit 1
fi

python3 - <<'PY'
from pathlib import Path
import re
import sys

dist_root = Path("web/apps/web-antd/dist")
index_html = (dist_root / "index.html").read_text(encoding="utf-8")
refs = re.findall(r'(?:src|href)="(/[^"]+)"', index_html)
missing = []
has_js = False
has_jse = False
for ref in refs:
    if ref.startswith("http"):
        continue
    rel = ref.lstrip("/").split("?", 1)[0]
    if rel.startswith("js/"):
        has_js = True
    if rel.startswith("jse/"):
        has_jse = True
    if not (dist_root / rel).exists():
        missing.append(ref)

if missing:
    print("index.html references missing dist assets:", file=sys.stderr)
    for ref in missing:
        print(f"  - {ref}", file=sys.stderr)
    raise SystemExit(1)

if not has_js or not has_jse:
    print("index.html is missing expected js/ or jse/ bundle references.", file=sys.stderr)
    raise SystemExit(1)
PY

bash web/scripts/deploy/verify-dist-assets.sh web/apps/web-antd/dist
