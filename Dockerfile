FROM python:3.11-slim-trixie@sha256:1042b61448fef4ba92d16a8c7eb4996d027568ce64792a7877fd88511e0af7c6

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 app \
    && useradd --uid 10001 --gid app --create-home app

WORKDIR /app
COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip uninstall -y setuptools wheel

COPY --chown=app:app . .
RUN mkdir -p /app/runtime /app/backups /app/data_cache \
    && chown -R app:app /app/runtime /app/backups /app/data_cache

USER app
EXPOSE 8000
CMD ["uvicorn", "cloud_app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
