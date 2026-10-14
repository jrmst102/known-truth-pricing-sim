"""Reproducible full-horizon mechanical acceptance on synthetic calibration.

Small learners reduce validation cost; their effective parameters are saved. This
is not a diagnostic/precision/scientific run and cannot approve the protocol.
"""

import argparse
import subprocess
import sys
from pathlib import Path

import yaml

from ktsim.cli import read_config
from ktsim.validation import check_run


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output-root", type=Path, default=Path("outputs/validation"))
    parser.add_argument("--n-jobs", type=int, default=2)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    est = read_config("configs/estimators.yaml")
    small = dict(n_estimators=10, learning_rate=0.05, num_leaves=10, min_child_samples=10)
    est["M2_gbm"].update(small)
    est["M4_dml"]["nuisance_params"] = small
    config = args.output_root / f"{args.run_id}-estimators.yaml"
    if not args.check_only:
        content = yaml.safe_dump(est, sort_keys=False)
        if config.exists() and config.read_text() != content:
            raise SystemExit("Existing validation config differs; choose a new run ID")
        if not config.exists():
            config.write_text(content)
    command = [
        sys.executable,
        "scripts/run_pilot.py",
        "--synthetic",
        "--stage",
        "validation",
        "--cells",
        "sna:med:none:phi=0",
        "sna:med:pos:phi=0.5",
        "sna:med:pos:phi=1",
        "--reps",
        "2",
        "--cycles",
        "104",
        "--estimator-config",
        str(config),
        "--n-jobs",
        str(args.n_jobs),
        "--save-data",
        "--save-storeweek",
        "--run-id",
        args.run_id,
        "--output-root",
        str(args.output_root),
    ]
    if args.resume:
        command.append("--resume")
    if not args.check_only:
        subprocess.run(command, check=True)
    output = args.output_root / args.run_id
    checks = check_run(output, require_full_horizon=True)
    failed = [name for name, passed in checks["acceptance"].items() if passed is False]
    if failed:
        raise SystemExit(f"Acceptance failed: {', '.join(failed)}; see {output / 'checks.json'}")
    print(output / "checks.json")


if __name__ == "__main__":
    main()
