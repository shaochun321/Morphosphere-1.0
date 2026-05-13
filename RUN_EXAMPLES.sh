#!/usr/bin/env bash
set -euo pipefail
python3 active/v365_full_rebase/scripts/check_v365_full_rebase.py --db outputs/m365_full_rebase.db
python3 active/v365_full_rebase/scripts/query_v365_full_rebase.py --db outputs/m365_full_rebase.db --table components --limit 10
python3 active/v365_full_rebase/scripts/query_v365_full_rebase.py --db outputs/m365_full_rebase.db --table coverage --limit 25
