FROM python:3.11-slim

# nginx        — reverse proxy in front of the app (this is what the user asked for)
# supervisor   — runs nginx + gunicorn as sibling processes in one container
# gettext-base — provides envsubst, used to bake Render's $PORT into nginx.conf at boot
# libpq5       — runtime lib for psycopg2 (asyncpg is pure-Python, no separate lib needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    supervisor \
    gettext-base \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY docker/nginx.conf.template /etc/nginx/templates/nginx.conf.template
COPY docker/supervisord.conf /etc/supervisor/supervisord.conf
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Render sets $PORT at runtime; this is just documentation for `docker run` locally.
EXPOSE 10000

ENTRYPOINT ["/entrypoint.sh"]
