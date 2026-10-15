"""Validate current saved-run artifacts; never infer acceptance from absent data."""

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

from ktsim.config import Calibration, CellConfig, DGMConfig
from ktsim.dgm import deploy_price
from ktsim.loop import run_replication
from ktsim.oracle import censored_mean, price_ladder
from ktsim.pilot import atomic_json
from ktsim.rng import assign_model_stores, draw_shocks, replication_streams


def _arms(cell):
    names = list(cell.estimators)
    if "M3" in names and cell.auto_m3_cf:
        names.append("M3_cf")
    if cell.data_only:
        return {"data:legacy"}
    return {
        f"{name}:{policy}"
        for name in names
        for policy in cell.policies
        if policy not in {"oracle", "legacy"}
    } | {"oracle:oracle", "legacy:legacy"}


def _reference_checks():
    cal = Calibration.load("data/fixtures/calibration_synthetic.json")
    cfg = DGMConfig(store_zones={store: 1 if store <= 4 else 2 for store in cal.alpha_s})
    z = np.random.default_rng(12).normal(0, 0.05, 100000)
    coefficients = {}
    for phi in (0, 1):
        price = deploy_price(
            base=cal.p_bar,
            cost=z,
            latent=0,
            assignment=bool(phi),
            delta=0,
            exploration=0,
            pass_through=0.2,
            kappa=0,
            ladder=price_ladder(cal, cfg),
        )
        coefficients[str(phi)] = float(np.cov(z, np.log(price))[0, 1] / np.var(z, ddof=1))
    normals = np.random.default_rng(104).normal(size=500000)
    draws = np.r_[normals, -normals]
    errors = []
    for price, cap in [(2.0, 10.0), (3.0, 25.0), (4.0, 80.0)]:
        mu = 3 - 0.35 * (price - 3)
        exact = price * censored_mean(mu, 0.25, cap)
        monte_carlo = price * np.minimum(np.exp(mu + 0.5 * draws), cap).mean()
        errors.append(float(abs(monte_carlo / exact - 1)))
    cell = CellConfig("direct-oracle", -1.06, 0, 1, 0, 1, [], [], pass_through=0)
    shocks = draw_shocks(replication_streams(42, 1)[0], cal.n_stores, 54, cal, cfg)
    direct = run_replication(cell, 0, shocks, cal, replace(cfg, cycles=2), {})
    zero = direct[direct.arm.eq("oracle:oracle")]
    stores = pd.read_csv("data/calibration/stores_tti.csv")
    zones = stores.zone.to_numpy()
    assignment = assign_model_stores(np.random.default_rng(2).permutation(len(zones)), zones, 0.5)
    balance = assignment.sum() == round(0.5 * len(zones)) and all(
        abs(assignment[zones == zone].sum() - 0.5 * sum(zones == zone)) <= 1
        for zone in np.unique(zones)
    )
    return dict(
        cost_coefficients=coefficients,
        cost_relevance_within_ten_percent=all(
            abs(v / 0.2 - 1) < 0.1 for v in coefficients.values()
        ),
        censored_oracle_mc_relative_errors=errors,
        censored_oracle_mc_pass=max(errors) < 0.001,
        direct_oracle_regret_zero=bool(zero.regret_dep_all.eq(0).all()),
        tti_zone_balance=bool(balance),
    )


def check_run(output, *, require_full_horizon=False):
    """Check the shared DGM, per-environment calibration, state sidecars and store-week schema.

    Short runs can pass mechanical checks but cannot pass the full-horizon gate.
    Optional audit outputs that are missing are reported as unverified, not passed.
    """
    output = Path(output)
    manifest = json.loads((output / "manifest.json").read_text())
    estimates = pd.read_parquet(output / "estimates.parquet")
    states = pd.read_parquet(output / "states.parquet")
    perf = pd.read_csv(output / "performance.csv")
    if estimates.empty or states.empty or perf.empty:
        raise ValueError("Validation requires nonempty estimates, states and performance")
    if not {"calibration", "dgm", "cells"} <= manifest.keys():
        raise ValueError("Manifest must contain calibration, dgm and cells in the current schema")
    calibrations = {}
    for env, raw in manifest["calibration"].items():
        calibrations[env] = Calibration(
            **dict(
                raw,
                alpha_s={int(k): v for k, v in raw["alpha_s"].items()},
                mu_z={int(k): v for k, v in raw["mu_z"].items()},
            )
        )
    dgm = DGMConfig(
        **dict(
            manifest["dgm"],
            store_zones={int(k): v for k, v in manifest["dgm"]["store_zones"].items()},
        )
    )
    cells = {cell.label: cell for cell in (CellConfig(**raw) for raw in manifest["cells"])}
    expected = {
        (label, rep, arm, cycle)
        for label, cell in cells.items()
        for rep in range(cell.reps)
        for arm in _arms(cell)
        for cycle in range(1, dgm.cycles + 1)
    }
    index = ["cell", "rep", "arm", "cycle"]
    recorded = estimates.set_index(index)
    complete = recorded.index.is_unique and set(recorded.index) == expected
    simulated_paths = sorted((output / "simulated").glob("*.parquet"))
    simulated = (
        pd.concat([pd.read_parquet(path) for path in simulated_paths], ignore_index=True)
        if simulated_paths
        else pd.DataFrame()
    )
    sw_path = output / "storeweek.parquet"
    storeweek = pd.read_parquet(sw_path) if sw_path.exists() else pd.DataFrame()
    on_ladder = not (simulated.empty and storeweek.empty)
    history = not simulated.empty
    expected_groups = {key[:3] for key in expected}
    if not simulated.empty:
        groups = simulated.groupby(["cell", "rep", "arm"])
        history &= set(groups.groups) == expected_groups
        for (label, _, _), frame in groups:
            cal = calibrations[cells[label].environment]
            before = frame[frame.t <= dgm.history_weeks]
            history &= (
                len(before) == cal.n_stores * dgm.history_weeks
                and not before.duplicated(["store", "t"]).any()
                and set(before.store) == set(cal.alpha_s)
                and set(before.t) == set(range(1, dgm.history_weeks + 1))
            )
    for frame in (simulated, storeweek):
        if frame.empty:
            continue
        for label, group in frame.groupby("cell"):
            on_ladder &= np.isin(
                group.price, price_ladder(calibrations[cells[label].environment], dgm)
            ).all()
    cycle_prices = False
    if not storeweek.empty:
        groups = storeweek.groupby(index)
        cycle_prices = set(groups.groups) == expected and all(
            len(frame) == calibrations[cells[label].environment].n_stores
            and not frame.store.duplicated().any()
            for (label, _, _, _), frame in groups
        )
    adoption = not states.empty and not states.duplicated(["cell", "rep"]).any()
    expected_states = {(label, rep) for label, cell in cells.items() for rep in range(cell.reps)}
    adoption &= set(zip(states.cell, states.rep)) == expected_states
    folds = True
    for row in states.to_dict("records"):
        cell = cells[row["cell"]]
        cal = calibrations[cell.environment]
        ids = np.array(sorted(cal.alpha_s))
        zones = np.array([dgm.store_zones[int(store)] for store in ids])
        assignment = np.asarray(json.loads(row["model_store_assignment"]), dtype=bool)
        group = estimates[estimates.cell.eq(row["cell"]) & estimates.rep.eq(row["rep"])]
        valid = len(assignment) == len(ids)
        if valid:
            valid = (
                assignment.sum() == round(cell.phi * len(ids))
                and group.n_model_stores.eq(assignment.sum()).all()
                and np.allclose(group.model_share_realized, assignment.mean())
                and all(
                    abs(assignment[zones == zone].sum() - cell.phi * sum(zones == zone)) <= 1
                    for zone in np.unique(zones)
                )
            )
        adoption &= valid and row["status"] == "finished"
        sidecar_path = output / "replications" / f"{row['key']}.state.json"
        if not sidecar_path.exists():
            folds = False
            continue
        saved = json.loads(sidecar_path.read_text())
        adoption &= saved["model_store_assignment"] == assignment.tolist()
        records = saved["dml_fold_records"]
        # Writer hashes Python dictionaries whose store IDs are integers.
        normalized = [
            dict(record, assignment={int(k): v for k, v in record["assignment"].items()})
            for record in records
        ]
        digest = hashlib.sha256(json.dumps(normalized, sort_keys=True).encode()).hexdigest()
        folds &= digest == saved["dml_fold_assignment_hash"] == row["dml_fold_assignment_hash"]
        success = group[group.arm.str.startswith("M4") & ~group.numerical_failure]
        assignments = {(record["arm"], record["cycle"]): record["assignment"] for record in records}
        for fitted in success.itertuples():
            mapping = assignments.get((fitted.arm, fitted.cycle), {})
            folds &= set(map(int, mapping)) == set(ids) and set(mapping.values()) == set(
                range(manifest["estimators"]["M4_dml"].get("n_folds", 5))
            )
    revenue = False
    if not storeweek.empty and set(storeweek.groupby(index).groups) == set(recorded.index):
        revenue = True
        for suffix, frame in [("all", storeweek), ("model", storeweek[storeweek.model_assigned])]:
            sums = frame.groupby(index)[["R_star", "R_dep", "R_rec"]].sum().reindex(recorded.index)
            for column in sums:
                revenue &= np.allclose(
                    sums[column],
                    recorded[column + "_" + suffix],
                    rtol=1e-12,
                    atol=1e-12,
                    equal_nan=True,
                )
            star = recorded["R_star_" + suffix]
            for kind in ("dep", "rec"):
                fraction = (star - recorded["R_" + kind + "_" + suffix]) / star
                revenue &= np.allclose(
                    fraction,
                    recorded["regret_" + kind + "_" + suffix],
                    rtol=1e-12,
                    atol=1e-12,
                    equal_nan=True,
                )
    exploration = None
    if not storeweek.empty:
        comparisons = []
        for label, cell in cells.items():
            if cell.phi != 0 or not {"greedy", "greedy_rps"} <= set(cell.policies):
                continue
            names = list(cell.estimators) + (
                ["M3_cf"] if "M3" in cell.estimators and cell.auto_m3_cf else []
            )
            for rep in range(cell.reps):
                frame = storeweek[storeweek.cell.eq(label) & storeweek.rep.eq(rep)]
                for name in names:
                    a = frame[frame.arm.eq(name + ":greedy")].sort_values(["cycle", "store"])
                    b = frame[frame.arm.eq(name + ":greedy_rps")].sort_values(["cycle", "store"])
                    comparisons.append(not a.empty and np.array_equal(a.price, b.price))
        if comparisons:
            exploration = bool(all(comparisons))
    core = estimates[estimates.sales_process.eq("latent")]
    no_censor = bool(core.censored_share.eq(0).all()) if len(core) else None
    if no_censor and not simulated.empty:
        latent_cells = {
            label
            for label, cell in cells.items()
            if (cell.sales_process or dgm.sales_process) == "latent"
        }
        no_censor = bool(not simulated[simulated.cell.isin(latent_cells)].censored.any())
    oracle = estimates[estimates.arm.eq("oracle:oracle")]
    oracle_ok = bool(
        len(oracle) and oracle.regret_rec_all.eq(0).all() and oracle.regret_dep_all.ge(-1e-12).all()
    )
    m4 = perf[perf.arm.str.startswith("M4")]
    withheld = bool(len(m4) and m4.coverage_status.str.startswith("withheld").all())
    allowed_coverage = (
        manifest.get("estimators", {}).get("M4_dml", {}).get("inference_validated", False)
    )
    coverage_ok = bool(
        len(m4) and (withheld if not allowed_coverage else m4.coverage_status.eq("available").all())
    )
    denominator = bool(
        (perf.n_total > 0).all()
        and (perf.n_estimated >= 0).all()
        and (perf.n_with_interval >= 0).all()
        and (perf.n_estimated <= perf.n_total).all()
        and (perf.n_with_interval <= perf.n_estimated).all()
    )
    references = _reference_checks()
    checks = dict(
        run_id=output.name,
        synthetic=manifest["synthetic"],
        stage=manifest["stage"],
        fingerprint=manifest["fingerprint"],
        cycles=dgm.cycles,
        replications=min(cell.reps for cell in cells.values()),
        cells=len(cells),
        arms=sorted(estimates.arm.unique()),
        complete=bool(complete),
        deployed_prices_on_ladder=bool(on_ladder),
        history_checked=bool(history),
        exploration_inert_at_phi_zero=exploration,
        cycle_prices_checked=bool(cycle_prices),
        adoption_recorded=bool(adoption),
        revenue_balanced=bool(revenue),
        core_censored_share_zero=no_censor,
        denominators_valid=denominator,
        dml_folds_recorded=bool(folds) if len(m4) else None,
        dml_coverage_withheld=withheld if len(m4) else None,
        **references,
    )
    checks["acceptance"] = {
        "AC-C1": bool(on_ladder and history and cycle_prices and exploration is not False),
        "AC-C2": references["cost_relevance_within_ten_percent"],
        "AC-C3": bool(adoption and references["tti_zone_balance"]),
        "AC-C5": bool(no_censor and references["censored_oracle_mc_pass"]) if len(core) else None,
        "AC-C6": bool(revenue and oracle_ok and references["direct_oracle_regret_zero"]),
        "AC-A6": denominator,
        "AC-A7": bool(folds and coverage_ok) if len(m4) else None,
        "run_complete": bool(complete),
    }
    if require_full_horizon:
        required_arms = {
            f"{name}:{policy}"
            for name in ("M1", "M2", "M3", "M3_cf", "M4_plr", "M4_pliv")
            for policy in ("greedy", "greedy_rps")
        } | {"oracle:oracle", "legacy:legacy"}
        checks["acceptance"]["full_horizon"] = bool(
            complete
            and dgm.cycles == 104
            and exploration is True
            and all(cell.reps >= 2 and _arms(cell) == required_arms for cell in cells.values())
            and {cell.phi for cell in cells.values()} >= {0, 0.5, 1}
        )
    checks["scope"] = (
        "Saved-run mechanical checks, not scientific or author acceptance. "
        "Planted failure, smearing, grouped-fold and hand-regret tests are separate."
    )
    atomic_json(checks, output / "checks.json")
    return checks
