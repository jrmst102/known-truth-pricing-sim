from dataclasses import replace
from time import perf_counter

import numpy as np
import pandas as pd

from ktsim.dgm import (
    capacity_at_reference,
    controls,
    deploy_price,
    draw_sales,
    instruments,
    kappa_scaled,
    legacy_log_price,
)
from ktsim.estimators import get_estimator
from ktsim.estimators.base import failed, finalize
from ktsim.oracle import (
    bound_classification,
    censored_oracle_price,
    expected_revenue,
    oracle_price,
    price_ladder,
    project_price,
)
from ktsim.policies import greedy_price
from ktsim.rng import assign_model_stores, latent_demand, mechanism_calibration


def cell_mechanism(dgm, cell):
    return replace(
        dgm,
        censoring={"multiplier": cell.multiplier},
        cost_shifter=dict(dgm.cost_shifter, structure=cell.cost_structure),
        shock_split=cell.shock_split,
        sales_process=cell.sales_process,
    )


def run_replication(cell, rep, shocks, cal, dgm, est_cfg, *, save_data=False, save_storeweek=False):
    dgm = cell_mechanism(dgm, cell)
    cal = mechanism_calibration(cal, dgm)
    stores = np.array(sorted(cal.alpha_s))
    if set(stores) - set(dgm.store_zones):
        raise ValueError("Missing store-zone mapping; supply calibrated stores.csv")
    zones = np.array([dgm.store_zones[int(store)] for store in stores])
    zone_index = {zone: index for index, zone in enumerate(sorted(cal.mu_z))}
    xi = latent_demand(shocks, cal, cell.rho_m)
    scaling = kappa_scaled(cell.kappa, np.sqrt(cal.sigma_xi2))
    model = assign_model_stores(shocks.model_store_assignment, zones, cell.phi)
    ladder = price_ladder(cal, dgm)
    censored = cell.sales_process == "censored"
    if cell.sales_process not in {"latent", "censored"}:
        raise ValueError("Unknown sales_process")

    def context(t):
        i = t - 1
        frame = controls(cal, dgm, stores, zones, t, shocks.promo[i], shocks.comp_index[i])
        nu = np.array([shocks.nu[zone_index[z], i] for z in zones])
        legacy = legacy_log_price(cal, dgm, t, zones, nu, shocks.promo[i], shocks.promo_depth[i])
        for name, values in instruments(
            cal,
            dgm,
            t,
            legacy,
            zones,
            shocks.cost[:, i],
            other_zone=cell.instrument == "other_zone_price",
        ).items():
            frame[name] = values
        cap = capacity_at_reference(cal, dgm, frame, cell.eta) if censored else None
        return frame, np.exp(legacy), cap

    def observed(frame, price, i, cap, forecast=None):
        out = frame.copy()
        out["price"], out["p_bar"] = price, cal.p_bar
        latent = draw_sales(cal, dgm, frame, price, cell.eta, xi[:, i], shocks.eps[:, i])
        out["realized"] = np.minimum(latent, cap) if censored else latent
        out["log_q"] = np.log(out.realized)
        out["forecast"] = np.nan if forecast is None else forecast
        out["censored"] = latent > out.realized
        out["model_assigned"] = model
        out["fallback_used"] = False
        out["cycle"] = max(0, i + 1 - dgm.history_weeks)
        return out

    history = []
    for t in range(1, dgm.history_weeks + 1):
        frame, legacy, cap = context(t)
        price = deploy_price(
            legacy,
            ladder,
            shocks.cost[:, t - 1],
            cell.pass_through,
            scaling,
            xi[:, t - 1],
            np.zeros(len(stores), bool),
            0,
            shocks.u[:, t - 1],
        )
        history.append(observed(frame, price, t - 1, cap))
    initial = pd.concat(history, ignore_index=True)
    names = list(cell.estimators)
    if "M3" in names:
        names.append("M3_cf")
    arms = [(name, policy) for name in names for policy in cell.policies]
    if cell.references:
        arms += [("oracle", "oracle"), ("legacy", "legacy")]
    if cell.data_only:
        arms = [("data", "legacy")]
    rows, simulated, audit, fold_hashes = [], {}, [], set()
    for name, policy in arms:
        data = initial.copy()
        arm = f"{name}:{policy}"
        for cycle in range(1, dgm.cycles + 1):
            started = perf_counter()
            t = dgm.history_weeks + cycle
            i = t - 1
            frame, legacy, cap = context(t)
            best = (
                censored_oracle_price(cal, dgm, frame, cell.eta, cap)
                if censored
                else np.full(len(stores), oracle_price(cal, dgm, cell.eta))
            )
            fallback = np.zeros(len(stores), bool)
            if name in {"data", "oracle", "legacy"}:
                est = finalize(cell.eta, predict=None)
                est["predictions_unavailable"] = False
            else:
                section = {
                    "M1": "M1_ols",
                    "M2": "M2_gbm",
                    "M3": "M3_iv",
                    "M3_cf": "M3_iv",
                    "M4_plr": "M4_dml",
                    "M4_pliv": "M4_dml",
                }[name]
                cfg = dict(est_cfg[section])
                if cell.instrument != "cost_shifter":
                    cfg["instrument"] = cell.instrument
                try:
                    est = get_estimator(name).fit(data, cal, cfg)
                except (ValueError, np.linalg.LinAlgError, RuntimeError, FloatingPointError):
                    est = failed()
            if name.startswith("M4"):
                est["coverage_status"] = (
                    "validated"
                    if est_cfg["M4_dml"].get("inference_validated", False)
                    else "withheld: inference not validated"
                )
            if policy == "oracle":
                recommendation = best.copy()
            elif policy == "legacy":
                recommendation = project_price(legacy, ladder)
            elif est["predict"] is None:
                recommendation = project_price(legacy, ladder)
                fallback = model.copy()
            else:
                try:
                    recommendation, unavailable = greedy_price(
                        est, frame, ladder, return_unavailable=True
                    )
                    if unavailable.any():
                        est["predictions_unavailable"] = True
                        recommendation[unavailable] = project_price(legacy[unavailable], ladder)
                        fallback = model & unavailable
                except (ValueError, FloatingPointError, RuntimeError, OverflowError):
                    est["predictions_unavailable"] = True
                    recommendation = project_price(legacy, ladder)
                    fallback = model.copy()
            # Reference arms apply their recommendation chainwide; estimator arms use D_s.
            base = np.where(model, recommendation, legacy)
            if policy in {"oracle", "legacy"}:
                base = best.copy() if policy == "oracle" else legacy.copy()
            base[fallback] = legacy[fallback]
            delta = (
                cell.delta * cycle ** dgm.exploration["decay_power"]
                if policy == "greedy_rps"
                else 0
            )
            deployed = deploy_price(
                base,
                ladder,
                shocks.cost[:, i],
                cell.pass_through,
                scaling,
                xi[:, i],
                model,
                delta,
                shocks.u[:, i],
            )
            forecast = None
            if est["predict"] is not None and not est["predictions_unavailable"]:
                try:
                    forecast = np.asarray(est["predict"](frame, deployed))
                    if not np.isfinite(forecast).all():
                        forecast = None
                except (ValueError, FloatingPointError, RuntimeError, OverflowError):
                    forecast = None
            next_week = observed(frame, deployed, i, cap, forecast)
            next_week["fallback_used"] = fallback
            next_week["base_price"] = base
            next_week["recommended_price"] = recommendation
            revenue = {
                kind: expected_revenue(cal, dgm, frame, price, cell.eta, cap)
                for kind, price in [("star", best), ("dep", deployed), ("rec", recommendation)]
            }
            for kind, values in revenue.items():
                next_week[f"R_{kind}"] = values
            data = pd.concat([data, next_week], ignore_index=True)
            trailing = data[data.t > t - 26]
            price_sd = (
                trailing.assign(log_price=np.log(trailing.price))
                .groupby("store")
                .log_price.std()
                .mean()
            )
            mape = rmse = np.nan
            if forecast is not None:
                mape = float(np.mean(np.abs(forecast - next_week.realized) / next_week.realized))
                rmse = float(np.sqrt(np.mean((forecast - next_week.realized) ** 2)))
            row = dict(
                run_id="",
                cell=cell.label,
                environment=cell.environment,
                rep=rep,
                arm=arm,
                cycle=cycle,
                week=t,
                eta_true=cell.eta,
                p_star=float(best.mean()),
                oracle_at_bound=bound_classification(best[0], ladder),
                eta_hat=est["eta_hat"],
                ci_low=est["ci_low"],
                ci_high=est["ci_high"],
                first_stage_F=est["first_stage_F"],
                converged=est["converged"],
                failure_reason=est["failure_reason"],
                p_rec=float(recommendation.mean()),
                p_dep_mean=float(deployed.mean()),
                deployed_prices=deployed.tolist(),
                model_share_realized=float(model.mean()),
                n_model_stores=int(model.sum()),
                fallback_used=float(fallback[model].mean()) if model.any() else 0.0,
                smearing_factor=est["smearing_factor"],
                sales_process=cell.sales_process,
                cost_structure=cell.cost_structure,
                shock_split=cell.shock_split,
                coverage_status=est.get("coverage_status", "available"),
                forecast_mape=mape,
                forecast_rmse=rmse,
                price_sd_26=float(price_sd),
                censored_share=float(next_week.censored.mean()),
                seconds=perf_counter() - started,
            )
            for flag in (
                "numerical_failure",
                "predictions_unavailable",
                "extreme_estimate",
                "positive_slope",
            ):
                row[flag] = est[flag]
            if est.get("fold_hash"):
                fold_hashes.add(est["fold_hash"])
            for label, mask in [("all", np.ones(len(stores), bool)), ("model", model)]:
                for kind, values in revenue.items():
                    row[f"R_{kind}_{label}"] = float(values[mask].sum()) if mask.any() else np.nan
                for kind in ("dep", "rec"):
                    row[f"regret_{kind}_{label}"] = (
                        row[f"R_star_{label}"] - row[f"R_{kind}_{label}"]
                    ) / row[f"R_star_{label}"]
            rows.append(row)
            if save_storeweek:
                audit.append(next_week.assign(arm=arm, cell=cell.label, rep=rep))
        if save_data:
            simulated[arm] = data.to_dict("list")
    result = pd.DataFrame(rows)
    result.attrs.update(
        simulated_data=simulated,
        storeweek=pd.concat(audit, ignore_index=True) if audit else None,
        model_assignment=dict(zip(stores.tolist(), model.tolist())),
        dml_fold_hashes=sorted(fold_hashes),
    )
    return result
