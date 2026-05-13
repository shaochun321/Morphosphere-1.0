#!/usr/bin/env bash
set -euo pipefail
python3 scripts/query_v366_pass8.py summary
python3 scripts/query_v366_pass8.py placement
python3 scripts/query_v366_pass8.py external
