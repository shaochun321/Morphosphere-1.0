#!/usr/bin/env bash
set -euo pipefail
DB="outputs/v366/m366_build_pass7.db"
echo '--- Pass7 status ---'
python3 scripts/query_v366_lineage_pass7.py --db "$DB" status
echo '--- Pass7 directness debt ---'
python3 scripts/query_v366_lineage_pass7.py --db "$DB" debt | head -80
echo '--- Pass7 contracts ---'
python3 scripts/query_v366_lineage_pass7.py --db "$DB" contracts | head -80
echo '--- Pass7 plan ---'
python3 scripts/query_v366_lineage_pass7.py --db "$DB" plan | head -80
