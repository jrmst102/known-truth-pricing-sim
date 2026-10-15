from dataclasses import dataclass

import numpy as np
import pandas as pd
import statsmodels.api as sm

from ktsim.clean import CleanResult
from ktsim.config import Calibration, CalibrationConfig


@dataclass
class Check:
    name: str
    value: float
    passed: bool
    expected: object
    status: str = "pass"


def residual_components(frame: pd.DataFrame, cfg: CalibrationConfig, *, diagnostics=False):
    autocov = []
    for lag in (0, 1, 2):
        products = []
        for _, group in frame.groupby("store"):
            series = group.set_index("week").residual
            centered = series - series.mean()
            paired = pd.concat(
                [centered, centered.rename("lagged").set_axis(series.index + lag)], axis=1
            ).dropna()
            products.extend((paired.iloc[:, 0] * paired.iloc[:, 1]).tolist())
        autocov.append(float(np.mean(products)) if products else 0.0)
    variance, cov1, cov2 = autocov
    rho = np.clip(cov2 / cov1 if cov1 > 0 else cfg.rho_xi_bounds[0], *cfg.rho_xi_bounds)
    xi_var = np.clip(cov1 / rho, 0.0, max(0.0, cfg.xi_share_max * variance))
    result = (float(rho), float(xi_var), float(max(0.0, variance - xi_var)))
    if diagnostics:
        return (*result, dict(resid_var=variance, autocov_lag1=cov1, autocov_lag2=cov2))
    return result


def calibrate(clean: CleanResult, cfg: CalibrationConfig) -> Calibration:
    frame = clean.frame.copy()
    required = {"week", "log_q", "price", "promo", "zone", "profit"}
    if not required.issubset(frame):
        raise ValueError(f"Missing calibration fields: {sorted(required - set(frame))}")
    p_bar = float(frame.price.mean())
    if not np.isfinite(p_bar):
        raise ValueError("No valid observations for reference price")
    design = pd.DataFrame(
        {
            "price_centered": frame.price - p_bar,
            "promo": frame.promo,
            "log_comp_index": frame.log_comp_index,
        }
    )
    for harmonic in range(1, cfg.harmonics + 1):
        design[f"sin_{harmonic}"] = np.sin(2 * np.pi * harmonic * frame.week / 52)
        design[f"cos_{harmonic}"] = np.cos(2 * np.pi * harmonic * frame.week / 52)
    holidays = [column for column in frame if column.startswith("holiday_")]
    design = pd.concat(
        [
            design,
            frame[holidays],
            pd.get_dummies(frame.store.astype(int), prefix="store", dtype=float),
        ],
        axis=1,
    )
    fit = sm.OLS(frame.log_q, design.astype(float)).fit()
    frame["residual"] = fit.resid
    rho, xi_var, eps_var, empirical = residual_components(frame, cfg, diagnostics=True)
    regular = frame[frame.promo.eq(0)].copy()
    regular["log_price"] = np.log(regular.price)
    mu_z = regular.groupby("zone").log_price.mean()
    drift = regular.groupby(["zone", "week"]).log_price.mean()
    centered = drift - drift.index.get_level_values("zone").map(mu_z)
    depth = 1 - frame.loc[frame.promo.eq(1), "price"] / p_bar
    depth = depth[depth > 0]
    if depth.empty:
        raise ValueError("No positive promotion depths; author-approved fallback required")
    comp = clean.frame.groupby("week").log_comp_index.mean()
    return Calibration(
        alpha_s={store: float(fit.params[f"store_{store}"]) for store in clean.store_ids},
        season={
            "g": [float(fit.params[f"sin_{index}"]) for index in range(1, cfg.harmonics + 1)],
            "h": [float(fit.params[f"cos_{index}"]) for index in range(1, cfg.harmonics + 1)],
        },
        holiday={column.removeprefix("holiday_"): float(fit.params[column]) for column in holidays},
        promo_effect=float(fit.params.promo),
        rho_xi=rho,
        sigma_xi2=xi_var,
        sigma_eps2=eps_var,
        p_bar=p_bar,
        mu_z={int(zone): float(value) for zone, value in mu_z.items()},
        sigma_nu2=float(np.var(centered)),
        pi_promo=float(frame.promo.mean()),
        promo_depth={"mean": float(depth.mean()), "sd": float(depth.std(ddof=0))},
        sigma_comp=float(comp.std(ddof=0)),
        unit_cost=float((frame.price * (1 - frame.profit / 100)).mean()),
        price_dispersion={
            "sd_log_price": float(np.log(frame.price).std(ddof=0)),
            "n_distinct": int(frame.price.nunique()),
            "profit_mean": float(frame.profit.mean()),
            "resid_sd": float(np.sqrt(xi_var + eps_var)),
        },
        beta_reference=float(fit.params.price_centered * p_bar),
        n_stores=len(clean.store_ids),
        n_store_weeks=len(frame),
        zero_share=clean.zero_share,
        focal_upc=clean.focal_upc,
        weeks=[int(frame.week.min()), int(frame.week.max())],
        diagnostics=dict(
            **empirical,
            empirical_rho_xi=rho,
            empirical_sigma_xi2=xi_var,
            empirical_sigma_eps2=eps_var,
            beta_reference_review="pending: units, log base, promotion coding, "
            "and competing-index construction",
        ),
    )


def check_plausibility(cal: Calibration, cfg: CalibrationConfig) -> list[Check]:
    values = {
        "retained_stores_min": cal.n_stores,
        "promo_freq": cal.pi_promo,
        "promo_depth": cal.promo_depth["mean"],
        "beta_reference": cal.beta_reference,
        "resid_sd": cal.price_dispersion["resid_sd"],
        "profit_mean": cal.price_dispersion["profit_mean"],
    }
    result = []
    for name, bounds in cfg.plausibility.items():
        value = float(values[name])
        passed = (
            value >= bounds if isinstance(bounds, (int, float)) else bounds[0] <= value <= bounds[1]
        )
        status = "pass" if passed else ("flag" if name == "beta_reference" else "fail")
        result.append(Check(name, value, passed, bounds, status))
    return result
