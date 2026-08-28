#!/bin/sh
set -eu

if [ "$#" -ne 1 ]; then
    echo "Usage: RESTORE_CONFIRM=quantclub /restore.sh /backups/file.dump" >&2
    exit 2
fi
if [ "${RESTORE_CONFIRM:-}" != "quantclub" ]; then
    echo "Restore replaces the current database. Set RESTORE_CONFIRM=quantclub to continue." >&2
    exit 2
fi

backup=$1
case "$backup" in
    /backups/quantclub_*.dump) ;;
    *) echo "Refusing unexpected backup path: $backup" >&2; exit 2 ;;
esac
if [ ! -f "$backup" ]; then
    echo "Backup does not exist: $backup" >&2
    exit 2
fi

pg_restore --clean --if-exists --no-owner --exit-on-error --dbname="$POSTGRES_DB" "$backup"
echo "Restore completed from $backup"
