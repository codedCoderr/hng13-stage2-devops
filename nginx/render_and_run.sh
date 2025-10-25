#!/bin/sh
set -e

TEMPLATE=/etc/nginx/nginx.conf.template
OUT=/etc/nginx/nginx.conf

: "${ACTIVE_POOL:=blue}"    # default to blue if not set
# internal app port (same as PORT in .env)
PORT="${PORT:-3000}"

# Build upstream block depending on ACTIVE_POOL
# Primary has no 'backup' flag; backup server is marked backup.
if [ "$ACTIVE_POOL" = "green" ]; then
  UPSTREAM="
upstream backend {
    server app_green:${PORT} max_fails=1 fail_timeout=2s;
    server app_blue:${PORT} backup max_fails=1 fail_timeout=2s;
    keepalive 16;
}
"
else
  # default: blue active
  UPSTREAM="
upstream backend {
    server app_blue:${PORT} max_fails=1 fail_timeout=2s;
    server app_green:${PORT} backup max_fails=1 fail_timeout=2s;
    keepalive 16;
}
"
fi

# render
awk -v up="$UPSTREAM" '{ gsub("##__UPSTREAM_PLACEHOLDER__##", up); print }' "$TEMPLATE" > "$OUT"

echo "Rendered $OUT with ACTIVE_POOL=$ACTIVE_POOL (primary: ${ACTIVE_POOL})"
exec nginx -g "daemon off;"
