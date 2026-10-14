"""Mechanical acceptance evidence from a saved validation run and deterministic checks."""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from ktsim.config import Calibration, DGMConfig
from ktsim.dgm import deploy_price
from ktsim.oracle import censored_lognormal_mean, price_ladder
from ktsim.rng import assign_model_stores


def check_run(output):
    output = Path(output)
    manifest = json.loads((output / "manifest.json").read_text())
    estimates = pd.read_parquet(output / "estimates.parquet")
    states = pd.read_parquet(output / "states.parquet")
    perf = pd.read_csv(output / "performance.csv")
    on_ladder, adoption, no_censor = True, True, True
    for env, group in estimates.groupby("environment"):
        raw = manifest["calibrations"][env]
        cal = Calibration(
            **dict(
                raw,
                alpha_s={int(k): v for k, v in raw["alpha_s"].items()},
                mu_z={int(k): v for k, v in raw["mu_z"].items()},
            )
        )
        cfg = DGMConfig(**manifest["dgm"][env])
        ladder = price_ladder(cal, cfg)
        on_ladder &= all(np.isin(prices, ladder).all() for prices in group.deployed_prices)
        no_censor &= bool(group[group.sales_process.eq("latent")].censored_share.eq(0).all())
        adoption &= bool(
            (group.model_share_realized * cal.n_stores - group.n_model_stores).abs().lt(1e-10).all()
        )
    history_checked = False
    for path in (output / "simulated").glob("*.parquet"):
        data = pd.read_parquet(path)
        env = next(c["environment"] for c in manifest["cells"] if c["name"] == data.cell.iloc[0])
        raw = manifest["calibrations"][env]
        cal = Calibration(**raw)
        ladder = price_ladder(cal, DGMConfig(**manifest["dgm"][env]))
        on_ladder &= bool(np.isin(data.price, ladder).all())
        history_checked = True
    assignments = bool(states.model_assignment.notna().all())
    grouped_folds = (
        bool(states.dml_fold_hashes.map(lambda value: bool(json.loads(value))).all())
        if estimates.arm.str.startswith("M4").any()
        else None
    )
    m4 = perf[perf.arm.str.startswith("M4")]
    withheld = bool(m4.coverage_status.str.startswith("withheld").all()) if len(m4) else None
    oracle = estimates[estimates.arm.eq("oracle:oracle")]
    oracle_rec = bool(oracle.regret_rec_all.eq(0).all()) if len(oracle) else None
    checks = dict(
        deployed_prices_on_ladder=bool(on_ladder),
        history_checked=history_checked,
        adoption_recorded=adoption,
        assignment_vectors_recorded=assignments,
        core_censored_share_zero=no_censor,
        oracle_recommended_regret_zero=oracle_rec,
        denominators_valid=bool(
            ((perf.n_estimated <= perf.n_total) & (perf.n_with_interval <= perf.n_estimated)).all()
        ),
        dml_folds_recorded=grouped_folds,
        dml_coverage_withheld=withheld,
        cycles=int(estimates.cycle.max()),
        replications=int(estimates.rep.nunique()),
        arms=sorted(estimates.arm.unique()),
        synthetic=manifest["synthetic"],
        stage=manifest["stage"],
        fingerprint=manifest["fingerprint"],
    )
    # Non-saturated pass-through check uses a reference price with a sufficiently fine ladder.
    fixture = Calibration.load("data/fixtures/calibration_synthetic.json")
    cfg = DGMConfig()
    z = np.random.default_rng(71).normal(0, 0.05, 100_000)
    coefficients = {}
    for phi in (0, 1):
        p = deploy_price(fixture.p_bar, price_ladder(fixture, cfg), z, 0.2, 0, 0, phi, 0, 0)
        coefficients[str(phi)] = float(np.cov(np.log(p), z)[0, 1] / np.var(z, ddof=1))
    checks["cost_coefficients"] = coefficients
    checks["cost_relevance_within_ten_percent"] = all(
        abs(c / 0.2 - 1) < 0.1 for c in coefficients.values()
    )
    normals = np.random.default_rng(104).normal(size=500_000)
    draws = np.r_[normals, -normals]
    errors = []
    for p, cap in [(2.0, 10.0), (3.0, 25.0), (4.0, 80.0)]:
        mu = 3 - 0.35 * (p - 3)
        exact = p * censored_lognormal_mean(mu, 0.25, cap)
        mc = p * np.minimum(np.exp(mu + 0.5 * draws), cap).mean()
        errors.append(float(abs(mc / exact - 1)))
    checks["censored_oracle_mc_relative_errors"] = errors
    checks["censored_oracle_mc_pass"] = max(errors) < 0.001
    # Exercise the calibrated tissue store set without reading raw movement data.
    stores = pd.read_csv("data/calibration/stores_tti.csv")
    zones = stores.zone.to_numpy()
    assignment = assign_model_stores(np.random.default_rng(2).permutation(len(zones)), zones, 0.5)
    checks["tti_zone_balance"] = bool(
        assignment.sum() == round(0.5 * len(zones))
        and all(
            abs(assignment[zones == zone].sum() - 0.5 * sum(zones == zone)) <= 1
            for zone in np.unique(zones)
        )
    )
    checks["acceptance"] = {
        "AC-C1": bool(on_ladder and history_checked),
        "AC-C2": checks["cost_relevance_within_ten_percent"],
        "AC-C3": bool(adoption and assignments and checks["tti_zone_balance"]),
        "AC-C5": bool(no_censor and checks["censored_oracle_mc_pass"]),
        "AC-C6": oracle_rec,
        "AC-A6": checks["denominators_valid"],
        "AC-A7": bool(grouped_folds and withheld) if grouped_folds is not None else None,
    }
    checks["scope"] = (
        "Saved-run mechanical checks; companion unit tests supply planted failures, hand regret, exploration and grouped-fold assertions. Author protocol signature and S2 acceptance are separate."
    )
    (output / "checks.json").write_text(json.dumps(checks, indent=2) + "\n")
    return checks
