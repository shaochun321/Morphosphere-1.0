#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 morphosphere_v2pp/scripts/run_evidence_reconstruction_v25.py
python3 morphosphere_v2pp/scripts/run_evidence_reconstruction_acceptance_v25.py
