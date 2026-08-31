#!/bin/sh
set -eu

secret_file=${1:-deploy/.env}

if [ ! -f "$secret_file" ] || [ -L "$secret_file" ]; then
    echo "Secret environment file must be a regular non-symlink file" >&2
    exit 1
fi

if mode=$(stat -c '%a' -- "$secret_file" 2>/dev/null); then
    :
else
    mode=$(stat -f '%Lp' -- "$secret_file")
fi
if [ "$mode" != "600" ]; then
    echo "Secret environment file must have mode 0600" >&2
    exit 1
fi
