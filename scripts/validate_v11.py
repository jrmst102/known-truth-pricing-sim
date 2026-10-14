"""Reproducible full-horizon mechanical acceptance on synthetic calibration.

Small learners reduce validation cost; their effective parameters are saved. This
is not a diagnostic/precision/scientific run and cannot approve the protocol.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from ktsim.cli import read_config
from ktsim.config import Calibration, CellConfig, DGMConfig
from ktsim.dgm import deploy_price
from ktsim.loop import run_replication
from ktsim.oracle import price_ladder
from ktsim.rng import draw_shocks, replication_streams


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
    estimates = pd.read_parquet(output / "estimates.parquet")
    storeweek = pd.read_parquet(output / "storeweek.parquet")
    cal = Calibration.load("data/fixtures/calibration_synthetic.json")
    dgm = DGMConfig(**read_config("configs/dgm_base.yaml"))
    ladder = price_ladder(cal, dgm)
    on_ladder = all(
        np.isin(pd.read_parquet(path).price, ladder).all()
        for path in (output / "simulated").glob("*.parquet")
    )
    rng = np.random.default_rng(12)
    z = rng.normal(0, 0.05, 100000)
    deployed = deploy_price(np.full(len(z), cal.p_bar), z, 0, True, 0, 0, 0.2, 0, ladder)
    coefficient = float(np.cov(z, np.log(deployed))[0, 1] / np.var(z, ddof=1))
    m4 = estimates[estimates.arm.str.startswith("M4")]
    performance = pd.read_csv(output / "performance.csv")
    denominators = (performance.n_estimated <= performance.n_total).all() and (
        performance.n_with_interval <= performance.n_estimated
    ).all()
    grouped = storeweek.groupby(["cell", "rep", "arm", "cycle"])[["R_star", "R_dep", "R_rec"]].sum()
    recorded = estimates.set_index(["cell", "rep", "arm", "cycle"])
    balance = all(
        np.allclose(
            grouped[column], recorded.loc[grouped.index, column + "_all"], rtol=1e-12, atol=1e-12
        )
        for column in grouped
    )
    phi0 = storeweek[storeweek.cell.eq("sna:med:none:phi=0")]
    inert = True
    for rep in (0, 1):
        frame = phi0[phi0.rep.eq(rep)]
        for name in ("M1", "M2", "M3", "M3_cf", "M4_plr", "M4_pliv"):
            a = frame[frame.arm.eq(name + ":greedy")].sort_values(["cycle", "store"]).price
            b = frame[frame.arm.eq(name + ":greedy_rps")].sort_values(["cycle", "store"]).price
            inert &= np.array_equal(a.to_numpy(), b.to_numpy())
    oracle = estimates[estimates.arm.eq("oracle:oracle")]
    dgm.store_zones = {store: 1 if store <= 4 else 2 for store in cal.alpha_s}
    from dataclasses import replace

    direct_cell = CellConfig("direct-oracle", -1.06, 0, 1, 0, 1, [], [], pass_through=0)
    shocks = draw_shocks(replication_streams(42, 1)[0], cal.n_stores, 54, cal, dgm)
    direct = run_replication(direct_cell, 0, shocks, cal, replace(dgm, cycles=2), {})
    zero = direct[direct.arm.eq("oracle:oracle")]
    model_null = estimates[estimates.cell.eq("sna:med:none:phi=0")].regret_dep_model.isna().all()
    counts = estimates.groupby(["cell", "rep", "arm"]).cycle.agg(["count", "max"])
    checks = dict(
        kind="synthetic mechanical validation; author acceptance pending",
        run_id=args.run_id,
        horizon=104,
        replications=2,
        cells=3,
        arms=sorted(estimates.arm.unique().tolist()),
        AC_C1=bool(on_ladder and inert),
        AC_C2=dict(passed=abs(coefficient / 0.2 - 1) < 0.1, coefficient=coefficient, target=0.2),
        AC_C3=bool(
            estimates.model_share_realized.notna().all() and estimates.n_model_stores.notna().all()
        ),
        AC_C5=bool(estimates.censored_share.eq(0).all()),
        AC_C6=bool(
            balance
            and model_null
            and zero.regret_dep_all.eq(0).all()
            and oracle.regret_rec_all.eq(0).all()
            and oracle.regret_dep_all.ge(0).all()
        ),
        AC_A6=bool(denominators),
        AC_A7=bool(m4.coverage_status.str.startswith("withheld").all()),
        complete=bool(counts["count"].eq(104).all() and counts["max"].eq(104).all()),
        checks_requiring_separate_unit_tests=[
            "censored oracle MC integration",
            "extreme and positive estimates",
            "legacy fallback",
            "zone assignment",
            "hand-worked regret",
            "configuration consistency",
            "grouped folds",
        ],
        outstanding=[
            "author protocol sign-off",
            "full-metadata tuna audit",
            "retained empirical environment acceptance",
        ],
    )
    path = output / "checks.json"
    path.write_text(json.dumps(checks, indent=2) + "\n")
    for key in ("AC_C1", "AC_C3", "AC_C5", "AC_C6", "AC_A6", "AC_A7", "complete"):
        if not checks[key]:
            raise SystemExit(f"Acceptance failed: {key}; see {path}")
    if not checks["AC_C2"]["passed"]:
        raise SystemExit(f"Acceptance failed: AC_C2; see {path}")
    print(path)


if __name__ == "__main__":
    main()
