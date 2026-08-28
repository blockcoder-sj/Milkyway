#!/bin/sh
set -eu

while true; do
    stamp=$(date -u +%Y%m%dT%H%M%SZ)
    temporary="/backups/.quantclub_${stamp}.dump"
    destination="/backups/quantclub_${stamp}.dump"
    pg_dump --format=custom --no-owner --file="$temporary"
    mv "$temporary" "$destination"
    find /backups -type f -name 'quantclub_*.dump' -mtime +14 -delete
    sleep 21600
done
