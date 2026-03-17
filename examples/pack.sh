#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

EXCLUDE_ARGS=(
    -x "*.DS_Store"
    -x "*/.DS_Store"
    -x "*/__pycache__/*"
    -x "__pycache__/*"
    -x "*.pyc"
    -x "*.pyo"
    -x "*.pyd"
    -x ".git/*"
    -x "*.egg-info/*"
)

packed=0
for dir in */; do
    dir="${dir%/}"
    [[ -d "$dir" ]] || continue
    [[ -f "$dir/__init__.py" || -f "$dir/plugin.py" ]] || continue

    archive="${dir}.zip"
    echo "Packing $dir → $archive"
    rm -f "$archive"
    zip -r "$archive" "$dir" "${EXCLUDE_ARGS[@]}" > /dev/null

    packed=$((packed + 1))
done

echo "Done — $packed archive(s) created."
