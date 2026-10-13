from dataclasses import replace
from time import perf_counter

import numpy as np
import pandas as pd

from ktsim.dgm import (
    controls,
    deployed_log_price,
    draw_sales,
    expected_log_demand,
    instruments,
    kappa_scaled,
    legacy_log_price,
)
from ktsim.estimators import get_estimator
from ktsim.estimators.base import failed
from ktsim.oracle import bound_classification, oracle_price, price_ladder, regret
from ktsim.policies import greedy_price
from ktsim.rng import latent_demand


def run_replication(cell, rep, shocks, cal, dgm, est_cfg, *, save_data=False):
    dgm = replace(dgm, censoring={"multiplier": cell.multiplier})
    stores = np.array(sorted(cal.alpha_s))
    if set(stores) - set(dgm.store_zones):
        raise ValueError("Missing store-zone mapping; supply calibrated stores.csv")
    zones = np.array([dgm.store_zones[int(store)] for store in stores])
    zone_index = {zone: index for index, zone in enumerate(sorted(cal.mu_z))}
    xi = latent_demand(shocks, cal, cell.rho_m)
    scaling = kappa_scaled(cell.kappa, np.sqrt(cal.sigma_xi2))
    model_stores = np.zeros(len(stores), dtype=bool)
    model_stores[shocks.model_store_assignment[:int(cell.phi * len(stores))]] = True
    ladder = price_ladder(cal, dgm)
    best = oracle_price(cal, dgm, cell.eta)
    slope = abs(cell.eta) / cal.p_bar

    def context(t):
        index = t - 1
        frame = controls(cal, dgm, stores, zones, t, shocks.promo[index], shocks.comp_index[index])
        nu = np.array([shocks.nu[zone_index[zone], index] for zone in zones])
        legacy = legacy_log_price(cal, dgm, t, zones, shocks.cost[index], nu,
                                  shocks.promo[index], shocks.promo_depth[index], cell.pass_through)
        for name, values in instruments(cal, dgm, t, legacy, zones, shocks.cost[index]).items():
            frame[name] = values
        return frame, legacy

    def observed(frame, price, index, forecast=None):
        output = frame.copy()
        output["price"] = price
        output["p_bar"] = cal.p_bar
        output["realized"] = draw_sales(cal, dgm, frame, price, cell.eta, xi[:, index],
                                        shocks.eps[:, index], True)
        output["log_q"] = np.log(output.realized)
        output["forecast"] = np.nan if forecast is None else forecast
        uncensored = np.exp(expected_log_demand(cal, dgm, frame, price, cell.eta)
                            + xi[:, index] + shocks.eps[:, index])
        output["censored"] = uncensored > output.realized + 1e-10
        return output

    history = []
    for t in range(1, dgm.history_weeks + 1):
        frame, legacy = context(t)
        price = np.exp(legacy + scaling * xi[:, t - 1])
        history.append(observed(frame, price, t - 1))
    initial = pd.concat(history, ignore_index=True)
    estimator_names = list(cell.estimators)
    if "M3" in estimator_names:
        estimator_names.append("M3_cf")
    arms = [(estimator, policy) for estimator in estimator_names for policy in cell.policies]
    if cell.data_only:
        arms = [("data", "legacy")]
    rows, simulated = [], {}
    for estimator_name, policy in arms:
        data = initial.copy()
        previous = np.full(len(stores), cal.p_bar)
        previous_est = None
        arm = f"{estimator_name}:{policy}"
        if policy == "greedy_rps":
            arm += f":delta={cell.delta:g}"
        for cycle in range(1, dgm.cycles + 1):
            started = perf_counter()
            t = dgm.history_weeks + cycle
            index = t - 1
            frame, legacy = context(t)
            if cell.data_only:
                est = failed()
                est["failure_reason"] = None
                recommendation = np.exp(legacy)
            else:
                section = {"M1": "M1_ols", "M2": "M2_gbm", "M3": "M3_iv",
                           "M3_cf": "M3_iv", "M4_plr": "M4_dml", "M4_pliv": "M4_dml"}
                try:
                    est = get_estimator(estimator_name).fit(data, cal, est_cfg[section[estimator_name]])
                    if policy == "oracle":
                        recommendation = np.full(len(stores), best)
                    elif policy == "legacy":
                        recommendation = np.exp(legacy)
                    elif est["converged"]:
                        recommendation = greedy_price(est, frame, ladder)
                    else:
                        recommendation = previous.copy()
                except (ValueError, np.linalg.LinAlgError, RuntimeError, FloatingPointError) as error:
                    est = failed("nonfinite" if isinstance(error, FloatingPointError)
                                 else "nonconvergence")
                    recommendation = np.full(len(stores), best) if policy == "oracle" else previous.copy()
                if est["converged"]:
                    previous_est = est
            delta = cell.delta * cycle**dgm.exploration["decay_power"] if policy == "greedy_rps" else 0.
            deployed_log = deployed_log_price(np.log(recommendation), legacy, model_stores, scaling,
                                               xi[:, index], delta * model_stores, shocks.u[:, index])
            deployed = np.exp(deployed_log)
            forecast = None
            if previous_est is not None:
                forecast = previous_est["predict"](frame, deployed)
            next_week = observed(frame, deployed, index, forecast)
            data = pd.concat([data, next_week], ignore_index=True)
            trailing = data[data.t > t - 26]
            price_sd = float(trailing.assign(log_price=np.log(trailing.price))
                             .groupby("store").log_price.std(ddof=1).mean())
            if forecast is None:
                mape = rmse = np.nan
            else:
                mape = float(np.mean(np.abs(forecast - next_week.realized) / next_week.realized))
                rmse = float(np.sqrt(np.mean((forecast - next_week.realized)**2)))
            rows.append(dict(run_id="", cell=cell.label, rep=rep, arm=arm, cycle=cycle, week=t,
                             eta_true=cell.eta, p_star=best,
                             oracle_at_bound=bound_classification(best, ladder),
                             eta_hat=est["eta_hat"], ci_low=est["ci_low"], ci_high=est["ci_high"],
                             first_stage_F=est["first_stage_F"], converged=est["converged"],
                             failure_reason=est["failure_reason"], sign_flip=est["eta_hat"] > 0,
                             p_rec=float(np.mean(recommendation)),
                             p_dep_mean=float(np.mean(deployed[model_stores]))
                             if model_stores.any() else float(np.mean(deployed)),
                             regret_rec=float(np.mean(regret(recommendation, best, slope, cal.p_bar))),
                             regret_dep=float(np.mean(regret(deployed, best, slope, cal.p_bar))),
                             forecast_mape=mape, forecast_rmse=rmse, price_sd_26=price_sd,
                             censored_share=float(next_week.censored.mean()),
                             seconds=perf_counter() - started))
            previous = recommendation
        if save_data:
            simulated[arm] = data.to_dict("list")
    result = pd.DataFrame(rows)
    result.attrs["simulated_data"] = simulated
    return result