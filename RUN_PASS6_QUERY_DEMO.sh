#!/usr/bin/env bash
set -euo pipefail
DB="outputs/v366/m366_build_pass6.db"
echo '--- Pass6 status ---'; python3 scripts/query_v366_lineage.py --db "$DB" status
echo '--- Pass6 health ---'; python3 scripts/query_v366_lineage.py --db "$DB" health
echo '--- Pass6 samples ---'; python3 scripts/query_v366_lineage.py --db "$DB" samples --limit 3
