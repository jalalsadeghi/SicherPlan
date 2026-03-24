#!/bin/sh
set -eu

DIST_ROOT="${1:-/usr/share/nginx/html}"
INDEX_HTML="${DIST_ROOT}/index.html"

if [ ! -f "$INDEX_HTML" ]; then
  echo "Missing index.html at ${INDEX_HTML}" >&2
  exit 1
fi

refs=$(
  grep -Eo '(src|href)="/(js|jse)/[^"]+"' "$INDEX_HTML" \
    | sed -E 's/^(src|href)="\///; s/"$//'
)

if [ -z "$refs" ]; then
  echo "index.html does not reference any /js/ or /jse/ assets." >&2
  exit 1
fi

has_js=0
has_jse=0
missing=0

for ref in $refs; do
  case "$ref" in
    js/*)
      has_js=1
      ;;
    jse/*)
      has_jse=1
      ;;
  esac

  if [ ! -f "${DIST_ROOT}/${ref}" ]; then
    echo "Missing referenced asset: ${DIST_ROOT}/${ref}" >&2
    missing=1
  fi
done

if [ "$has_js" -ne 1 ] || [ "$has_jse" -ne 1 ]; then
  echo "index.html must reference both /js/... and /jse/... startup assets." >&2
  exit 1
fi

if [ "$missing" -ne 0 ]; then
  exit 1
fi
