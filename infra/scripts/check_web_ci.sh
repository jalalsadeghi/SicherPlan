#!/usr/bin/env bash
set -euo pipefail

test -f web/Dockerfile.stage
test -f web/nginx.stage.conf
test -f web/apps/web-antd/dist/index.html

# The current stage image serves committed dist directly, so the smoke check should
# validate the exact inputs that Docker stage deployment depends on right now.
grep -q 'COPY web/apps/web-antd/dist /usr/share/nginx/html' web/Dockerfile.stage
grep -q 'Stage web image requires committed web/apps/web-antd/dist/index.html' web/Dockerfile.stage
grep -q 'proxy_pass http://backend:8000/api/' web/nginx.stage.conf
grep -q 'try_files \$uri \$uri/ /index.html;' web/nginx.stage.conf
