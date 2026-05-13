#!/usr/bin/env bash
set -euo pipefail
if [ "$#" -ne 1 ]; then
  echo "Usage: $0 /path/to/Morphosphere_tree" >&2
  exit 2
fi
TARGET="$1"
mkdir -p "$TARGET/active" "$TARGET/outputs" "$TARGET/runtime_store" "$TARGET/docs"
cp -R active/v364 "$TARGET/active/"
cp outputs/m364.db "$TARGET/outputs/"
mkdir -p "$TARGET/runtime_store/v364"
cp -R runtime_store/v364/. "$TARGET/runtime_store/v364/"
cp -R docs/. "$TARGET/docs/"
echo "Applied v36.4 bridge overlay to $TARGET"
