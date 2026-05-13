#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
if [ "${RUN_EXAMPLES:-0}" = "1" ]; then
  echo "[optional] RUN_EXAMPLES.sh"
  ./RUN_EXAMPLES.sh
fi
if [ "${RUN_FULL_BRIDGE:-0}" = "1" ]; then
  echo "[optional] RUN_FULL_BRIDGE_CHECKS.sh"
  ./RUN_FULL_BRIDGE_CHECKS.sh
fi
if [ "${RUN_FULL_DB_INTEGRITY:-0}" = "1" ]; then
  echo "[optional] full DB integrity"
  RUN_FULL_DB_INTEGRITY=1 ./RUN_CORE_DB_INTEGRITY.sh
fi
