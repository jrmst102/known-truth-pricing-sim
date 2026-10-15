from dataclasses import replace
from time import perf_counter

import numpy as np
import pandas as pd

from ktsim.dgm import (
    capacity,
    controls,
    deploy_price,
    draw_sales,
    expected_log_demand,
    instruments,
    kappa_scaled,
    legacy_log_price,
)
from ktsim.estimators import get_estimator
from ktsim.estimators.base import failed, finalize
from ktsim.oracle import (
    bound_classification,
    censored_oracle,
    expected_revenue,
    oracle_price,
    price_ladder,
)
from ktsim.rng import assign_model_stores, latent_demand, shock_parameters


def cell_dgm(cell, dgm):
    return replace(
        dgm,
        censoring={"multiplier": cell.multiplier},
        sales_process=cell.sales_process or dgm.sales_process,
        cost_shifter=dict(
            dgm.cost_shifter, structure=cell.cost_structure or dgm.cost_shifter["structure"]
        ),
        shock_split=cell.shock_split or dgm.shock_split,
    )


def revenue_totals(star, deployed, recommended, assignment):
    result = {}
    for name, mask in (("all", np.ones(len(star), dtype=bool)), ("model", assignment)):
        for field, values in (("R_star", star), ("R_dep", deployed), ("R_rec", recommended)):
            result[f"{field}_{name}"] = float(np.sum(values[mask])) if mask.any() else np.nan
        for kind in ("dep", "rec"):
            total = result[f"R_star_{name}"]
            result[f"regret_{kind}_{name}"] = (
                (total - result[f"R_{kind}_{name}"]) / total if total > 0 else np.nan
            )
    return result


def run_replication(cell, rep, shocks, cal, dgm, est_cfg, *, save_data=False, save_storeweek=False):
    dgm = cell_dgm(cell, dgm)
    stores = np.array(sorted(cal.alpha_s))
    if set(stores) - set(dgm.store_zones):
        raise ValueError("Missing store-zone mapping; supply calibrated stores.csv")
    zones = np.array([dgm.store_zones[int(store)] for store in stores])
    zone_index = {zone: index for index, zone in enumerate(sorted(cal.mu_z))}
    xi = latent_demand(shocks, cal, cell.rho_m, dgm)
    scaling = kappa_scaled(cell.kappa, np.sqrt(shock_parameters(cal, dgm)[1]))
    model = assign_model_stores(shocks.model_store_assignment, zones, cell.phi)
    ladder = price_ladder(cal, dgm)
    best_latent = oracle_price(cal, dgm, cell.eta)
    sections = {
        "M1": "M1_ols",
        "M2": "M2_gbm",
        "M3": "M3_iv",
        "M3_cf": "M3_iv",
        "M4_plr": "M4_dml",
        "M4_pliv": "M4_dml",
    }
    use_other = any(
        est_cfg.get(section, {}).get("instrument") == "other_zone_price"
        for section in ("M3_iv", "M4_dml")
    )

    def context(t):
        index = t - 1
        frame = controls(cal, dgm, stores, zones, t, shocks.promo[index], shocks.comp_index[index])
        nu = np.array([shocks.nu[zone_index[zone], index] for zone in zones])
        legacy = np.exp(
            legacy_log_price(cal, dgm, t, zones, nu, shocks.promo[index], shocks.promo_depth[index])
        )
        for name, values in instruments(
            zones, shocks.cost[:, index], np.log(legacy) if use_other else None
        ).items():
            frame[name] = values
        cap = capacity(cal, dgm, frame, cell.eta) if dgm.sales_process == "censored" else None
        return frame, legacy, cap

    def observed(frame, price, index, cap, forecast=None):
        output = frame.copy()
        output["price"] = price
        output["p_bar"] = cal.p_bar
        output["realized"] = draw_sales(
            cal,
            dgm,
            frame,
            price,
            cell.eta,
            xi[:, index],
            shocks.eps[:, index],
            cap is not None,
            cap,
        )
        output["log_q"] = np.log(output.realized)
        output["forecast"] = np.nan if forecast is None else forecast
        output["censored"] = (
            False
            if cap is None
            else (
                np.exp(
                    expected_log_demand(cal, dgm, frame, price, cell.eta)
                    + xi[:, index]
                    + shocks.eps[:, index]
                )
                > cap
            )
        )
        output["model_assigned"] = model
        output["fallback_used"] = False
        return output

    history = []
    for t in range(1, dgm.history_weeks + 1):
        frame, legacy, cap = context(t)
        price = deploy_price(
            legacy,
            shocks.cost[:, t - 1],
            xi[:, t - 1],
            False,
            0,
            0,
            cell.pass_through,
            scaling,
            ladder,
        )
        history.append(observed(frame, price, t - 1, cap))
    initial = pd.concat(history, ignore_index=True)
    names = list(cell.estimators)
    if "M3" in names and cell.auto_m3_cf:
        names.append("M3_cf")
    arms = [
        (name, policy)
        for name in names
        for policy in cell.policies
        if policy not in {"oracle", "legacy"}
    ]
    arms.extend([("oracle", "oracle"), ("legacy", "legacy")])
    if cell.data_only:
        arms = [("data", "legacy")]
    rows, simulated, audits, fold_records = [], {}, [], []
    for name, policy in arms:
        data = initial.copy()
        arm = f"{name}:{policy}"
        for cycle in range(1, dgm.cycles + 1):
            started = perf_counter()
            t = dgm.history_weeks + cycle
            index = t - 1
            frame, legacy, cap = context(t)
            best = (
                np.full(len(stores), best_latent)
                if cap is None
                else (censored_oracle(cal, dgm, frame, cell.eta, cap))
            )
            fallback = np.zeros(len(stores), dtype=bool)
            forecast = None
            forecast_grid_rmse = np.nan
            if policy in {"oracle", "legacy"}:
                est = finalize(cell.eta, coverage_status="not applicable")
                est["predictions_unavailable"] = False
                recommendation = best if policy == "oracle" else legacy
            else:
                try:
                    est = get_estimator(name).fit(data, cal, est_cfg[sections[name]])
                except (ValueError, np.linalg.LinAlgError, RuntimeError, FloatingPointError):
                    est = failed()
                if name.startswith("M4"):
                    if not est_cfg["M4_dml"].get("inference_validated", False):
                        est["coverage_status"] = "withheld: inference not validated"
                    fold_records.append(
                        dict(arm=arm, cycle=cycle, assignment=est["fold_assignment"])
                    )
                recommendation = legacy.copy()
                unavailable = np.ones(len(stores), dtype=bool)
                if est["predict"] is not None:
                    try:
                        predictions = np.column_stack(
                            [est["predict"](frame, np.full(len(stores), price)) for price in ladder]
                        )
                        truth_grid = np.column_stack(
                            [
                                expected_revenue(
                                    cal,
                                    dgm,
                                    frame,
                                    np.full(len(stores), price),
                                    cell.eta,
                                    cap,
                                )
                                / price
                                for price in ladder
                            ]
                        )
                        forecast_grid_rmse = float(
                            np.sqrt(np.mean((predictions - truth_grid) ** 2))
                        )
                        usable = np.isfinite(predictions).all(axis=1) & (predictions > 0).all(
                            axis=1
                        )
                        recommendation[usable] = ladder[
                            np.argmax(predictions[usable] * ladder, axis=1)
                        ]
                        unavailable = ~usable
                    except (ValueError, RuntimeError, FloatingPointError):
                        pass
                est["predictions_unavailable"] = bool(unavailable.any())
                fallback = unavailable & model
            delta = (
                cell.delta * cycle ** (dgm.exploration["decay_power"])
                if policy == "greedy_rps"
                else 0.0
            )
            # Reference oracle deploys directly to make zero-regret checks possible when
            # adjustments are zero; legacy remains the base for unassigned stores.
            base = np.where(model, recommendation, legacy)
            if policy == "oracle":
                base = best
            deployed = deploy_price(
                base,
                shocks.cost[:, index],
                xi[:, index],
                model,
                delta,
                shocks.u[:, index],
                cell.pass_through,
                scaling,
                ladder,
            )
            if policy in {"oracle", "legacy"}:
                forecast = expected_revenue(cal, dgm, frame, deployed, cell.eta, cap) / deployed
            elif est["predict"] is not None:
                try:
                    forecast = est["predict"](frame, deployed)
                except (ValueError, RuntimeError, FloatingPointError):
                    forecast = None
            next_week = observed(frame, deployed, index, cap, forecast)
            next_week["fallback_used"] = fallback
            star = expected_revenue(cal, dgm, frame, best, cell.eta, cap)
            dep = expected_revenue(cal, dgm, frame, deployed, cell.eta, cap)
            rec = expected_revenue(cal, dgm, frame, recommendation, cell.eta, cap)
            totals = revenue_totals(star, dep, rec, model)
            if save_storeweek:
                audits.append(
                    next_week.assign(
                        arm=arm,
                        cycle=cycle,
                        rep=rep,
                        cell=cell.label,
                        environment=cell.environment,
                        p_rec=recommendation,
                        p_star=best,
                        R_star=star,
                        R_dep=dep,
                        R_rec=rec,
                    )
                )
            data = pd.concat([data, next_week], ignore_index=True)
            trailing = data[data.t > t - dgm.reliability["window"]]
            price_sd = float(
                trailing.assign(log_price=np.log(trailing.price))
                .groupby("store")
                .log_price.std(ddof=1)
                .mean()
            )
            errors = None if forecast is None else forecast - next_week.realized.to_numpy()
            rows.append(
                dict(
                    run_id="",
                    cell=cell.label,
                    environment=cell.environment,
                    rep=rep,
                    arm=arm,
                    cycle=cycle,
                    week=t,
                    eta_true=cell.eta,
                    p_star=float(np.mean(best)),
                    oracle_at_bound=(
                        bound_classification(float(best[0]), ladder)
                        if np.unique(best).size == 1
                        else "mixed"
                    ),
                    **{
                        key: est[key]
                        for key in (
                            "eta_hat",
                            "ci_low",
                            "ci_high",
                            "first_stage_F",
                            "converged",
                            "failure_reason",
                            "numerical_failure",
                            "predictions_unavailable",
                            "extreme_estimate",
                            "positive_slope",
                            "smearing_factor",
                            "coverage_status",
                        )
                    },
                    model_share_realized=float(model.mean()),
                    n_model_stores=int(model.sum()),
                    fallback_used=float(fallback.sum() / model.sum()) if model.any() else np.nan,
                    p_rec=float(np.mean(recommendation)),
                    p_dep_mean=float(np.mean(deployed)),
                    **totals,
                    forecast_mape=float(np.mean(np.abs(errors) / next_week.realized))
                    if errors is not None
                    else np.nan,
                    forecast_rmse=float(np.sqrt(np.mean(errors**2)))
                    if errors is not None
                    else np.nan,
                    forecast_grid_rmse=forecast_grid_rmse,
                    price_sd_26=price_sd,
                    censored_share=float(next_week.censored.mean()),
                    sales_process=dgm.sales_process,
                    cost_structure=dgm.cost_shifter["structure"],
                    shock_split=dgm.shock_split,
                    seconds=perf_counter() - started,
                )
            )
        if save_data:
            simulated[arm] = data.to_dict("list")
    result = pd.DataFrame(rows)
    result.attrs["simulated_data"] = simulated
    result.attrs["storeweek"] = pd.concat(audits, ignore_index=True) if audits else pd.DataFrame()
    result.attrs["assignment"] = model.tolist()
    result.attrs["fold_records"] = fold_records
    return result
