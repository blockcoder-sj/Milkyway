#!/bin/sh
set -eu
umask 077

while true; do
    stamp=$(date -u +%Y%m%dT%H%M%SZ)
    plaintext="/tmp/quantclub_${stamp}.dump"
    temporary="/backups/.quantclub_${stamp}_$$.mwbak"
    destination="/backups/quantclub_${stamp}.mwbak"
    trap 'rm -f "$plaintext" "$temporary"' EXIT HUP INT TERM
    pg_dump --format=custom --no-owner --file="$plaintext"
    python /backup/encrypted_backup.py encrypt \
        --input "$plaintext" \
        --output "$temporary" \
        --public-key /run/secrets/backup-public.pem
    rm -f "$plaintext"
    mv --no-clobber "$temporary" "$destination"
    if [ -e "$temporary" ]; then
        echo "Backup destination already exists: $destination" >&2
        exit 1
    fi
    (cd /backups && sha256sum "$(basename "$destination")" > "$(basename "$destination").sha256")
    trap - EXIT HUP INT TERM
    find /backups -type f \( -name 'quantclub_*.mwbak' -o -name 'quantclub_*.mwbak.sha256' \) \
        -mtime +14 -delete
    sleep 21600
done
