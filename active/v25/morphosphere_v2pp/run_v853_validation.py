#!/usr/bin/env python3
"""Run Morphosphere v8.5.3 validation perturbations on the local v8.5 diagnostic DB."""
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from morphosphere.validation.v853 import main

if __name__ == "__main__":
    raise SystemExit(main())
