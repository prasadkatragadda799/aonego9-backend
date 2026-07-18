#!/usr/bin/env bash
set -euo pipefail

: "${PORT:=10000}"

echo "[entrypoint] Baking PORT=${PORT} into nginx.conf"
envsubst '${PORT}' < /etc/nginx/templates/nginx.conf.template > /etc/nginx/nginx.conf

echo "[entrypoint] Running database migrations"
cd /app
alembic upgrade head

echo "[entrypoint] Starting nginx + backend via supervisord"
exec supervisord -c /etc/supervisor/supervisord.conf
