#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$ROOT/external_data/ctc"
cat "$ROOT"/../ms25_src.part* > "$ROOT/external_data/ctc/Fluo-N2DH-GOWT1.zip"
python3 - <<'PY'
import hashlib, pathlib
p=pathlib.Path('external_data/ctc/Fluo-N2DH-GOWT1.zip')
h=hashlib.sha256(p.read_bytes()).hexdigest()
print(h)
assert h=='1a7bd9a7d1d10c4122c7782427b437246fb69cc3322a975485c04e206f64fc2c'
PY
