#!/usr/bin/env bash
set -euo pipefail
python3 active/v35/scripts/check_v35.py --db outputs/m35.db
python3 active/v35H/scripts/check_v35H.py --db outputs/m35H.db
python3 active/v36/scripts/check_v36.py --db outputs/m36.db
python3 active/v361/scripts/check_v361.py --db outputs/m361.db
python3 active/v362/scripts/check_v362.py --db outputs/m362.db
python3 active/v363/scripts/check_v363.py --db outputs/m363.db
python3 active/v364/scripts/check_v364.py --db outputs/m364.db
python3 active/v365/scripts/check_v365.py --db outputs/m365.db
python3 active/v365_full_rebase/scripts/check_v365_full_rebase.py --db outputs/m365_full_rebase.db
