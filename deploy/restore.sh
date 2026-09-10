#!/bin/sh
set -eu

if [ "$#" -ne 1 ]; then
    echo "Usage: RESTORE_CONFIRM=quantclub /restore.sh /backups/file.mwbak" >&2
    exit 2
fi
if [ "${RESTORE_CONFIRM:-}" != "quantclub" ]; then
    echo "Restore replaces the current database. Set RESTORE_CONFIRM=quantclub to continue." >&2
    exit 2
fi

backup=$1
case "$backup" in
    /backups/quantclub_*.mwbak) ;;
    *) echo "Refusing unexpected backup path: $backup" >&2; exit 2 ;;
esac
if [ ! -f "$backup" ]; then
    echo "Backup does not exist: $backup" >&2
    exit 2
fi

case "${PGUSER:-}" in
    milkyway_backup|milkyway_app|milkyway_paper|milkyway_backtest|milkyway_scheduler)
        echo "Restore requires a maintenance-only owner/restore identity" >&2
        exit 2
        ;;
esac

checksum="${backup}.sha256"
if [ ! -f "$checksum" ]; then
    echo "Encrypted backup checksum is missing" >&2
    exit 2
fi
(cd /backups && sha256sum -c "$(basename "$checksum")")

plaintext="/tmp/restore_$$.dump"
trap 'rm -f "$plaintext"' EXIT HUP INT TERM
python /backup/encrypted_backup.py decrypt \
    --input "$backup" \
    --output "$plaintext" \
    --private-key /run/secrets/backup-private.pem
pg_restore --list "$plaintext" >/dev/null
pg_restore --clean --if-exists --no-owner --exit-on-error --dbname="$PGDATABASE" "$plaintext"
echo "Restore completed from $backup"
