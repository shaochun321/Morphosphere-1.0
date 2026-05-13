"""Morphosphere diagnostic CLI.

Examples:
  python -m morphosphere.cli run diagnostic --calibration_profile basic_physics_v1
  python -m morphosphere.cli run validation --db outputs/morphosphere_state_separation_v01_output_database.db
  python -m morphosphere.cli run state-separation --db outputs/morphosphere_state_separation_v01_output_database.db
  python -m morphosphere.cli validate v852 --db outputs/morphosphere_state_separation_v01_output_database.db
  python -m morphosphere.cli validate v853 --db outputs/morphosphere_state_separation_v01_output_database.db
  python -m morphosphere.cli validate state-separation --db outputs/morphosphere_state_separation_v01_output_database.db
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
    run.add_argument("target", choices=["diagnostic", "validation", "state-separation"])
    run.add_argument("--db", default="outputs/morphosphere_state_separation_v01_output_database.db")
    run.add_argument("--config", default="configs/v853_validation.json")
    run.add_argument("--calibration_profile", default="basic_physics_v1", choices=["diagnostic_event_channel_v1", "basic_physics_v1"])
    run.add_argument("--physics_seed", default="8531")
    run.add_argument("--no_reset", action="store_true")

    val = sub.add_parser("validate")
    val.add_argument("target", choices=["v852", "v853", "state-separation"])
    val.add_argument("--db", default="outputs/morphosphere_state_separation_v01_output_database.db")

    args = p.parse_args(argv)
    if args.cmd == "run" and args.target == "diagnostic":
        return run_cmd([
            "run_v85_diagnostic.py",
            "--db", args.db,
            "--calibration_profile", args.calibration_profile,
            "--execution_mode", "diagnostic_full",
            "--scientific_use_allowed", "false",
            "--physics_seed", str(args.physics_seed),
        ])
    if args.cmd == "run" and args.target == "validation":
        return run_cmd(["run_v853_validation.py", "--db", args.db, "--config", args.config])
    if args.cmd == "run" and args.target == "state-separation":
        cmd = ["scripts/run_state_separation_core.py", "--db", args.db]
        if args.no_reset:
            cmd.append("--no-reset")
        return run_cmd(cmd)
    if args.cmd == "validate" and args.target == "v852":
        return run_cmd(["scripts/run_acceptance_sql.py", args.db])
    if args.cmd == "validate" and args.target == "v853":
        return run_cmd(["scripts/run_v853_behavioral_acceptance.py", args.db])
    if args.cmd == "validate" and args.target == "state-separation":
        return run_cmd(["scripts/run_state_separation_acceptance.py", args.db])
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
