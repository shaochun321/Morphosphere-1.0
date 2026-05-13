"""Minimal Morphosphere diagnostic CLI.

Examples:
  python -m morphosphere.cli run diagnostic
  python -m morphosphere.cli run validation
  python -m morphosphere.cli validate v852
  python -m morphosphere.cli validate v853
"""
from __future__ import annotations
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run_cmd(args: list[str]) -> int:
    return subprocess.call([sys.executable, *args], cwd=str(ROOT))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="morphosphere")
    sub = p.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run")
    run.add_argument("target", choices=["diagnostic", "validation"])
    val = sub.add_parser("validate")
    val.add_argument("target", choices=["v852", "v853"])
    args = p.parse_args(argv)
    if args.cmd == "run" and args.target == "diagnostic":
        return run_cmd(["run_v85_diagnostic.py"])
    if args.cmd == "run" and args.target == "validation":
        return run_cmd(["run_v853_validation.py"])
    if args.cmd == "validate" and args.target == "v852":
        return run_cmd(["scripts/run_acceptance_sql.py", "v85_full_diagnostic_run.db"])
    if args.cmd == "validate" and args.target == "v853":
        return run_cmd(["scripts/run_v853_behavioral_acceptance.py", "v85_full_diagnostic_run.db"])
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
