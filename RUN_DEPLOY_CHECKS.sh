#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
echo "[Morphosphere v36.6 pass5] deploy check root: $ROOT"
echo "[1/5] v36.5 full-rebase lineage check"
python3 active/v365_full_rebase/scripts/check_v365_full_rebase.py --db outputs/m365_full_rebase.db
echo "[2/5] core DB integrity"
./RUN_CORE_DB_INTEGRITY.sh
echo "[3/5] pass3 checks"
./RUN_V366_PASS3_CHECKS.sh
echo "[4/5] pass5 checks"
./RUN_V366_PASS5_CHECKS.sh
echo "[5/5] module status preview"
./RUN_PASS5_MODULE_STATUS.sh | sed -n '1,40p'
echo "[Morphosphere v36.6 pass5] PASS"

if [ -x ./RUN_V366_PASS6_CHECKS.sh ]; then ./RUN_V366_PASS6_CHECKS.sh; fi

if [ -x ./RUN_V366_PASS7_CHECKS.sh ]; then ./RUN_V366_PASS7_CHECKS.sh; fi

echo '[PASS8] running boundary alignment checks'
./RUN_V366_PASS8_CHECKS.sh
