#!/bin/sh
# The official image may source non-executable init files. Keep shell options
# and temporary variables out of its entrypoint's environment.
(
set -eu

fingerprints=""
for variable in POSTGRES_PASSWORD APP_DB_PASSWORD PAPER_DB_PASSWORD BACKTEST_DB_PASSWORD SCHEDULER_DB_PASSWORD BACKUP_DB_PASSWORD AUTHORITY_DB_PASSWORD; do
    case "$variable" in
        POSTGRES_PASSWORD) value=${POSTGRES_PASSWORD:-} ;;
        APP_DB_PASSWORD) value=${APP_DB_PASSWORD:-} ;;
        PAPER_DB_PASSWORD) value=${PAPER_DB_PASSWORD:-} ;;
        BACKTEST_DB_PASSWORD) value=${BACKTEST_DB_PASSWORD:-} ;;
        SCHEDULER_DB_PASSWORD) value=${SCHEDULER_DB_PASSWORD:-} ;;
        BACKUP_DB_PASSWORD) value=${BACKUP_DB_PASSWORD:-} ;;
        AUTHORITY_DB_PASSWORD) value=${AUTHORITY_DB_PASSWORD:-} ;;
    esac
    if [ "${#value}" -lt 32 ]; then
        echo "$variable must contain at least 32 characters" >&2
        exit 1
    fi
    case "$value" in
        replace-with-*|REPLACE-WITH-*|change-me*|CHANGE-ME*|*not-configured)
            echo "$variable must not use a shipped placeholder" >&2
            exit 1
            ;;
    esac
    fingerprint=$(printf '%s' "$value" | sha256sum | cut -d ' ' -f 1)
    fingerprints="${fingerprints}${fingerprint}
"
done

unique_count=$(printf '%s' "$fingerprints" | sort -u | sed '/^$/d' | wc -l | tr -d ' ')
if [ "$unique_count" -ne 7 ]; then
    echo "Database role passwords must all be independent" >&2
    exit 1
fi

psql --set=ON_ERROR_STOP=1 \
    --set=app_password="$APP_DB_PASSWORD" \
    --set=paper_password="$PAPER_DB_PASSWORD" \
    --set=backtest_password="$BACKTEST_DB_PASSWORD" \
    --set=scheduler_password="$SCHEDULER_DB_PASSWORD" \
    --set=backup_password="$BACKUP_DB_PASSWORD" \
    --set=authority_password="$AUTHORITY_DB_PASSWORD" \
    --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<'SQL'
SELECT format('CREATE ROLE milkyway_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT PASSWORD %L', :'app_password')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'milkyway_app') \gexec
SELECT format('CREATE ROLE milkyway_paper LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT PASSWORD %L', :'paper_password')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'milkyway_paper') \gexec
SELECT format('CREATE ROLE milkyway_backtest LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT PASSWORD %L', :'backtest_password')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'milkyway_backtest') \gexec
SELECT format('CREATE ROLE milkyway_scheduler LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT PASSWORD %L', :'scheduler_password')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'milkyway_scheduler') \gexec
SELECT format('CREATE ROLE milkyway_backup LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT PASSWORD %L', :'backup_password')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'milkyway_backup') \gexec
SELECT format('CREATE ROLE milkyway_authority LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS PASSWORD %L', :'authority_password')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'milkyway_authority') \gexec
SQL
)
