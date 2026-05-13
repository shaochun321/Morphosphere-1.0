#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 -S morphosphere_v2pp/scripts/validate_full_core_v18.py outputs/morphosphere_full_core_v18_output_database.db
