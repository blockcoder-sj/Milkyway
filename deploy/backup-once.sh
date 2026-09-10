#!/bin/sh
set -eu

umask 077
stamp=$(date -u +%Y%m%dT%H%M%SZ)
plaintext="/tmp/quantclub_pre_migration_${stamp}.dump"
temporary="/backups/.quantclub_pre_migration_${stamp}_$$.mwbak"
backup_name="quantclub_pre_migration_${stamp}.mwbak"
destination="/backups/${backup_name}"

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
trap - EXIT HUP INT TERM
(cd /backups && sha256sum "$backup_name" > "${backup_name}.sha256")
(cd /backups && sha256sum -c "${backup_name}.sha256")

echo "Created authenticated encrypted pre-migration backup: $destination"
