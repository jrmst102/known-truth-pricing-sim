"""Run the author-approved, time-bounded replacement for S2 diagnostics."""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from ktsim.config import Calibration, CellConfig, DGMConfig
from ktsim.io import sha256, week_table
from ktsim.pilot import run_pilot
from ktsim.report import environment, make_report

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "outputs/diagnostic/s2-diagnostic-20261014"
OUTPUT = ROOT / "outputs/diagnostic/s2-reduced-20261015"


def table(frame: pd.DataFrame) -> str:
    columns = list(frame)
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for row in frame.itertuples(index=False, name=None):
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def add_preserved_evidence(report: Path) -> None:
    states = pd.read_parquet(SOURCE / "states.parquet")
    keys = states.loc[states.status.eq("finished"), "key"].tolist()
    frames = [pd.read_parquet(SOURCE / "replications" / f"{key}.parquet") for key in keys]
    estimates = pd.concat(frames, ignore_index=True)
    by_arm = (
        estimates.groupby("arm")
        .agg(
            failure_rate=("numerical_failure", "mean"),
            fallback_rate=("fallback_used", "mean"),
            positive_slope_rate=("positive_slope", "mean"),
            runtime_minutes=("seconds", lambda values: values.sum() / len(keys) / 60),
        )
        .reset_index()
    )
    for column in ("failure_rate", "fallback_rate", "positive_slope_rate"):
        by_arm[column] = (100 * by_arm[column]).round(2)
    by_arm["runtime_minutes"] = by_arm.runtime_minutes.round(1)
    scope = [
        "## Author-approved reduced scope",
        "",
        "This report combines two explicitly different evidence sets:",
        "",
        "- 14 preserved SNA replications from the original run, each with 104 cycles and all 14 arms.",
        "- One TNA and one TTI `med, pos, phi=0.5` replication, each with 52 cycles and all 14 arms.",
        "",
        "The reduced diagnostic exercises every estimator and policy in all three retained environments, "
        "but it does not establish 81-cell coverage or 104-cycle behavior in TNA and TTI. "
        "It provides operational diagnostics only and does not constitute author acceptance.",
        "",
        "## Preserved 104-cycle SNA evidence",
        "",
        f"Completed replications: {len(keys)}; distinct cells: {estimates.cell.nunique()}.",
        "",
        table(by_arm),
        "",
    ]
    text = report.read_text()
    marker = "## Provenance"
    report.write_text(text.replace(marker, "\n".join(scope) + marker, 1))


def main() -> None:
    if OUTPUT.exists():
        raise FileExistsError(f"Reduced run already exists: {OUTPUT}")
    if subprocess.check_output(["git", "status", "--porcelain"], text=True).strip():
        raise ValueError("Reduced scientific run requires a clean reviewed commit")
    original = json.loads((SOURCE / "manifest.json").read_text())
    selected = [
        CellConfig(**raw)
        for raw in original["cells"]
        if raw["environment"] in {"tna", "tti"}
        and raw["eta"] == -1.06
        and raw["kappa"] == 0.05
        and raw["phi"] == 0.5
        and "base-extra" not in raw["name"]
    ]
    if len(selected) != 2:
        raise ValueError("Expected exactly one representative TNA and TTI cell")
    dgm_raw = dict(original["dgm"])
    dgm_raw["cycles"] = 52
    dgm_raw["store_zones"] = {int(key): value for key, value in dgm_raw["store_zones"].items()}
    dgm = DGMConfig(**dgm_raw)
    dgm.calendar = week_table(ROOT / "data/fixtures/week_decode.csv")
    calibrations = {
        name: Calibration.load(ROOT / f"data/calibration/calibration_{name}.json")
        for name in ("tna", "tti")
    }
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    source_checksums = {
        str(path.relative_to(ROOT)): sha256(path)
        for directory in ("src", "scripts")
        for path in sorted((ROOT / directory).rglob("*.py"))
    }
    manifest = dict(original)
    manifest.update(
        commit=commit,
        cells=[asdict(cell) for cell in selected],
        dgm={key: value for key, value in asdict(dgm).items() if key != "calendar"},
        calibration={name: asdict(cal) for name, cal in calibrations.items()},
        calibration_ids={
            name: sha256(ROOT / f"data/calibration/calibration_{name}.json")
            for name in calibrations
        },
        environment=environment(),
        n_jobs=2,
        figures=[],
        source_checksums=source_checksums,
        save_data=False,
        save_storeweek=True,
        reduced_scope={
            "authorized_by": "Jose Mendoza",
            "authorized_at": "2026-10-15",
            "reason": "Author requested completion within one to two hours",
            "preserved_sna_replications": 14,
            "preserved_sna_cycles": 104,
            "new_environments": ["tna", "tti"],
            "new_cell": "med:pos:phi=0.5",
            "new_reps_per_environment": 1,
            "new_cycles": 52,
            "limitations": [
                "Not all 81 core cells are diagnosed",
                "TNA and TTI do not cover the 104-cycle horizon",
                "One replication per added environment does not estimate Monte Carlo variability",
            ],
        },
        started_at=datetime.now(timezone.utc).isoformat(),
    )
    manifest.pop("execution_history", None)
    manifest.pop("fingerprint", None)
    manifest["fingerprint"] = hashlib.sha256(
        json.dumps(manifest, sort_keys=True).encode()
    ).hexdigest()
    run_pilot(
        selected,
        calibrations,
        dgm,
        original["estimators"],
        original["master_seed"],
        OUTPUT,
        manifest,
        n_jobs=2,
        save_data=False,
        save_storeweek=True,
    )
    report = make_report(OUTPUT)
    add_preserved_evidence(report)
    print(f"Reduced diagnostic report: {report}", flush=True)


if __name__ == "__main__":
    main()
