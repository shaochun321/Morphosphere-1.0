#!/usr/bin/env bash
set -euo pipefail
python3 scripts/query_v366_pass12.py --db outputs/v366/m366_build_pass12_execution.db stress
