FROM postgres:16-trixie@sha256:f1c3376c26f2609ab9f29f71f824103fe2fcd8ee0346485cb6122a4f93df6f94 AS pgtools
FROM python:3.11-slim-trixie@sha256:1042b61448fef4ba92d16a8c7eb4996d027568ce64792a7877fd88511e0af7c6

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY deploy/debian.sources /tmp/debian.sources
RUN rm -f /etc/apt/sources.list /etc/apt/sources.list.d/* \
    && mv /tmp/debian.sources /etc/apt/sources.list.d/debian.sources \
    && apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends libgomp1=14.2.0-19 \
        libpq5=17.11-0+deb13u1 liblz4-1=1.10.0-4 libzstd1=1.5.7+dfsg-1 \
        zlib1g=1:1.3.dfsg+really1.3.1-1+b1 libxxhash0=0.8.3-2 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 app \
    && useradd --uid 10001 --gid app --create-home app

# Match the server major version: pg_restore 17 emits settings rejected by PG16.
COPY --from=pgtools /usr/lib/postgresql/16/bin/pg_dump /usr/local/bin/pg_dump
COPY --from=pgtools /usr/lib/postgresql/16/bin/pg_restore /usr/local/bin/pg_restore
RUN pg_dump --version && pg_restore --version

WORKDIR /app
COPY requirements.lock ./
RUN pip install --require-hashes --only-binary=:all: -r requirements.lock \
    && pip uninstall -y setuptools wheel

COPY --chown=app:app . .
RUN mkdir -p /app/runtime /app/backups /app/data_cache \
    && chown -R app:app /app/runtime /app/backups /app/data_cache

USER app
EXPOSE 8000
CMD ["uvicorn", "cloud_app.main:app", "--host", "127.0.0.1", "--port", "8000", "--workers", "1"]
