"""Execution-only resume: verify original scientific inputs; preserve their manifest."""

import argparse
import hashlib
import json
import logging
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Set these before importing numerical libraries or spawning worker processes.
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

import pandas as pd

from ktsim.config import Calibration, CellConfig, DGMConfig
from ktsim.io import sha256, week_table
from ktsim.pilot import atomic_json, run_pilot
from ktsim.protocol import validate_protocol
from ktsim.report import environment, make_report

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "outputs/diagnostic/s2-diagnostic-20261014"


def prepare():
    manifest = json.loads((OUTPUT / "manifest.json").read_text())
    current = environment()
    if current["python"] != manifest["environment"]["python"]:
        raise ValueError("Install Python " + manifest["environment"]["python"])
    # Editable distribution metadata may differ; exact source hashes below govern
    # ktsim. All numerical/software dependency versions must remain unchanged.
    for package, expected in manifest["environment"]["packages"].items():
        if package != "ktsim" and current["packages"].get(package) != expected:
            raise ValueError(f"Package version changed: {package}; expected {expected}")
    frozen = {k: v for k, v in manifest.items() if k not in ("fingerprint", "execution_history")}
    frozen["figures"] = []
    # asdict originally serialized numeric store keys; restore their types for
    # the exact original sort_keys fingerprint, rather than string sorting.
    frozen["dgm"] = dict(frozen["dgm"])
    frozen["dgm"]["store_zones"] = {int(k): v for k, v in frozen["dgm"]["store_zones"].items()}
    frozen["calibration"] = {env: dict(cal) for env, cal in frozen["calibration"].items()}
    for cal in frozen["calibration"].values():
        for field in ("alpha_s", "mu_z"):
            cal[field] = {int(k): v for k, v in cal[field].items()}
    digest = hashlib.sha256(json.dumps(frozen, sort_keys=True).encode()).hexdigest()
    if digest != manifest["fingerprint"]:
        raise ValueError("Original manifest fingerprint is invalid")
    for group in ("config_checksums", "source_checksums"):
        for path, expected in manifest[group].items():
            if sha256(path) != expected:
                raise ValueError(f"Changed frozen input: {path}")
    # Raw movement archives are not read by S2. Verify every simulation input;
    # retain the original raw-archive provenance without rebuilding calibration.
    for path, expected in manifest["checksums"].items():
        if path.startswith("data/calibration/") or path == "data/fixtures/week_decode.csv":
            if sha256(path) != expected:
                raise ValueError(f"Changed simulation input: {path}")
    checks = json.loads(Path("data/calibration/checks.json").read_text())
    if checks != manifest["calibration_checks"]:
        raise ValueError("Calibration checks changed")
    calibrations = {}
    for env, expected in manifest["calibration"].items():
        path = Path(f"data/calibration/calibration_{env}.json")
        if json.loads(path.read_text()) != expected:
            raise ValueError(f"Calibration changed: {env}")
        audit = json.loads(Path(f"data/calibration/coverage_audit_{env}.json").read_text())
        window = Path(f"data/calibration/coverage_audit_{env}_window.json")
        if window.exists():
            audit["calibration_window_audit"] = json.loads(window.read_text())
        if audit != manifest["coverage_audits"][env]:
            raise ValueError(f"Coverage audit changed: {env}")
        calibrations[env] = Calibration.load(path)
    validate_protocol(manifest, scientific=True, stage="diagnostic")
    assert manifest["stage"] == "diagnostic" and not manifest["synthetic"] and not manifest["dirty"]
    dgm_raw = dict(manifest["dgm"])
    dgm_raw["store_zones"] = {int(k): v for k, v in dgm_raw["store_zones"].items()}
    dgm = DGMConfig(**dgm_raw)
    dgm.calendar = week_table(Path("data/fixtures/week_decode.csv"))
    cells = [CellConfig(**cell) for cell in manifest["cells"]]
    states = pd.read_parquet(OUTPUT / "states.parquet")
    for key in states.loc[states.status.eq("finished"), "key"]:
        for path in (
            OUTPUT / "replications" / f"{key}.parquet",
            OUTPUT / "replications" / f"{key}.state.json",
            OUTPUT / "storeweek" / f"{key}.parquet",
        ):
            if not path.exists():
                raise ValueError(f"Missing completed checkpoint: {path}")
    assert sum(c.reps for c in cells) == 96 and dgm.cycles == 104
    hashes = ROOT / "preserved_checkpoint_hashes.json"
    if hashes.exists():
        for path, expected in json.loads(hashes.read_text()).items():
            if sha256(OUTPUT / path) != expected:
                raise ValueError(f"Transferred checkpoint changed: {path}")
    print(f"Frozen inputs verified; {states.status.eq('finished').sum()}/96 complete", flush=True)
    return manifest, cells, calibrations, dgm


def stamp():
    return datetime.now(timezone.utc).isoformat()


def stop_child(child):
    if child.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(child.pid), "/T", "/F"], check=False)
    else:
        os.killpg(child.pid, signal.SIGTERM)
    try:
        child.wait(timeout=15)
    except subprocess.TimeoutExpired:
        if os.name != "nt":
            os.killpg(child.pid, signal.SIGKILL)
        else:
            child.kill()
        child.wait()


def main():
    parser = argparse.ArgumentParser(description="Resume the transferred S2 run on a local machine")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--execute", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.workers < 1:
        parser.error("workers must be positive")
    os.chdir(ROOT)
    manifest, cells, calibrations, dgm = prepare()
    history_path = OUTPUT / "execution_history.json"
    history = json.loads(history_path.read_text())
    if args.check_only:
        used = sum(item.get("worker_hours_upper_bound", 0) for item in history)
        print(
            f"Remaining worker-hour budget: {manifest['decisions_config']['budget_hours'] - used:.3f}; requested workers: {args.workers}"
        )
        return
    if args.execute:
        run_pilot(
            cells,
            calibrations,
            dgm,
            manifest["estimators"],
            manifest["master_seed"],
            OUTPUT,
            manifest,
            n_jobs=args.workers,
            resume=True,
            save_data=manifest["save_data"],
            save_storeweek=manifest["save_storeweek"],
        )
        return
    if history and "stopped_at" not in history[-1] and "finished_at" not in history[-1]:
        raise ValueError(
            "Previous execution is not recorded stopped; do not start duplicate workers"
        )
    budget = manifest["decisions_config"]["budget_hours"]
    used = sum(item.get("worker_hours_upper_bound", 0) for item in history)
    remaining = budget - used
    if remaining <= 0:
        raise ValueError(
            "Compute budget exhausted; further computation requires an explicit decision"
        )
    states = pd.read_parquet(OUTPUT / "states.parquet")
    if states.status.eq("finished").all():
        print("All replications already finished; no simulation launched.")
        print("Report:", make_report(OUTPUT))
        return
    current_commit = None
    if (ROOT / ".git").exists():
        current_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    attempt = dict(
        attempt=len(history) + 1,
        workers=args.workers,
        started_at=stamp(),
        status="running_local",
        environment=environment(),
        checkout_commit=current_commit,
        scientific_commit=manifest["commit"],
        launcher_sha256=sha256(__file__),
        budget_worker_hours=budget,
        remaining_wall_seconds=int(remaining * 3600 / args.workers),
        authorization="Author requested local continuation in VS Code",
    )
    history.append(attempt)
    atomic_json(history, history_path)
    options = (
        {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
        if os.name == "nt"
        else {"start_new_session": True}
    )
    child = None
    started = time.monotonic()
    code = 1
    try:
        child = subprocess.Popen(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "--execute",
                "--workers",
                str(args.workers),
            ],
            cwd=ROOT,
            **options,
        )
        code = child.wait(timeout=attempt["remaining_wall_seconds"])
        attempt["status"] = "finished" if code == 0 else "failed"
    except subprocess.TimeoutExpired:
        stop_child(child)
        attempt["status"] = "budget_stopped"
        code = 124
    except KeyboardInterrupt:
        if child is not None:
            stop_child(child)
        attempt["status"] = "stopped_by_user"
        code = 130
    finally:
        attempt.update(
            finished_at=stamp(),
            exit_code=code,
            worker_hours_upper_bound=(time.monotonic() - started) * args.workers / 3600,
        )
        atomic_json(history, history_path)
    if code == 0:
        saved = json.loads((OUTPUT / "manifest.json").read_text())
        saved["execution_history"] = history
        atomic_json(saved, OUTPUT / "manifest.json")
        print("Report:", make_report(OUTPUT))
    else:
        print(
            f"Run stopped ({attempt['status']}); finished checkpoints retained. Exit code {code}."
        )
    raise SystemExit(code)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    main()
