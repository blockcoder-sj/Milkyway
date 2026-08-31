#!/bin/sh
set -eu

umask 077
stamp=$(date -u +%Y%m%dT%H%M%SZ)
temporary="/backups/.quantclub_pre_kms_${stamp}.dump"
backup_name="quantclub_pre_kms_${stamp}.dump"
destination="/backups/${backup_name}"

trap 'rm -f "$temporary"' EXIT HUP INT TERM

pg_dump --format=custom --no-owner --file="$temporary"
mv "$temporary" "$destination"
trap - EXIT HUP INT TERM
(cd /backups && sha256sum "$backup_name" > "${backup_name}.sha256")
(cd /backups && sha256sum -c "${backup_name}.sha256")
pg_restore --list "$destination" >/dev/null

echo "Verified pre-migration backup: $destination"
