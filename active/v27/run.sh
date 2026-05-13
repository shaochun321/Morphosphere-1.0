#!/usr/bin/env bash
set -euo pipefail
python3 scripts/check_v27.py
python3 scripts/query_v27.py --limit 3 >/dev/null
echo "m27 run: PASS"
