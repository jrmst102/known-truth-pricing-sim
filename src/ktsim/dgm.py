"""Demand and deployment. Capacity uses current observed controls at reference price,
with expectation over shocks; it never uses realized shocks or candidate prices.
"""

import numpy as np
import pandas as pd


def controls(cal, dgm, stores, zones, t, promo, comp_index):
    frame = pd.DataFrame(
        {
            "store": stores,
            "zone": zones,
            "t": t,
            "promo": float(promo),
            "log_comp_index": float(comp_index),
            "week_of_year": (t - 1) % 52 + 1,
        }
    )
    for index in range(1, len(cal.season["g"]) + 1):
        week = cal.weeks[0] + t - 1
        frame[f"sin_{index}"] = np.sin(2 * np.pi * index * week / 52)
        frame[f"cos_{index}"] = np.cos(2 * np.pi * index * week / 52)
    for name in cal.holiday:
        value = 0.0
        if dgm.calendar is not None:
            week = cal.weeks[0] + t - 1
            lookup = dgm.calendar.set_index("week")
            if week not in lookup.index:
                raise ValueError("Simulation extends beyond authoritative calendar")
            value = float(lookup.loc[week, f"holiday_{name}"])
        frame[f"holiday_{name}"] = value
    return frame


def expected_log_demand(cal, dgm, x, price, eta):
    value = x.store.map(cal.alpha_s).to_numpy(dtype=float)
    value += cal.promo_effect * x.promo.to_numpy()
    value += dgm.cross_price_coef * x.log_comp_index.to_numpy()
    for index, (sine, cosine) in enumerate(zip(cal.season["g"], cal.season["h"]), 1):
        value += sine * x[f"sin_{index}"].to_numpy() + cosine * x[f"cos_{index}"].to_numpy()
    for name, coefficient in cal.holiday.items():
        value += coefficient * x[f"holiday_{name}"].to_numpy()
    return value - abs(eta) / cal.p_bar * (np.asarray(price) - cal.p_bar)


def capacity(cal, dgm, x, eta):
    from ktsim.rng import shock_parameters

    _, xi_var, eps_var = shock_parameters(cal, dgm)
    return dgm.censoring["multiplier"] * np.exp(
        expected_log_demand(cal, dgm, x, cal.p_bar, eta) + (xi_var + eps_var) / 2
    )


def draw_sales(cal, dgm, x, price, eta, xi, eps, censor, cap=None):
    sales = np.exp(expected_log_demand(cal, dgm, x, price, eta) + xi + eps)
    if censor:
        sales = np.minimum(sales, capacity(cal, dgm, x, eta) if cap is None else cap)
    return sales


def legacy_log_price(cal, dgm, t, zone, nu_zt, promo_t, depth_t):
    base = np.array([cal.mu_z[int(value)] for value in zone])
    return base + nu_zt + promo_t * np.log1p(-depth_t)


def deploy_price(base, cost, latent, assignment, delta, exploration, pass_through, kappa, ladder):
    """The only deployment path: adjust once, then project once (ties downward)."""
    from ktsim.oracle import project_price

    adjusted = np.asarray(base) * np.exp(
        pass_through * cost + kappa * latent + np.asarray(assignment) * delta * exploration
    )
    return project_price(adjusted, ladder)


def instruments(zone, cost, legacy=None):
    result = {"cost_shifter": np.asarray(cost)}
    if legacy is not None:  # explicitly requested extension only
        zone = np.asarray(zone)
        result["other_zone_price"] = np.array(
            [
                np.mean(np.asarray(legacy)[zone != value]) if np.any(zone != value) else np.nan
                for value in zone
            ]
        )
    return result


def kappa_scaled(level, sigma_xi):
    if sigma_xi == 0:
        if level == 0:
            return 0.0
        raise ValueError("Nonzero kappa requires positive latent demand variance")
    return level / sigma_xi
