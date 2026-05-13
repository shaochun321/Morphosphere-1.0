#!/usr/bin/env bash
set -euo pipefail
DB="outputs/v366/m366_build_pass11_parallel.db"
python3 scripts/query_v366_pass11_parallel.py --db "$DB" summary
python3 scripts/query_v366_pass11_parallel.py --db "$DB" lanes
