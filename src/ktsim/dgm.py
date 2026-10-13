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


def draw_sales(cal, dgm, x, price, eta, xi, eps, censor):
    mean = expected_log_demand(cal, dgm, x, price, eta)
    sales = np.exp(mean + xi + eps)
    if censor:
        sales = np.minimum(sales, dgm.censoring["multiplier"] * np.exp(mean))
    return sales


def legacy_log_price(cal, dgm, t, zone, cost_t, nu_zt, promo_t, depth_t, pass_through=0.2):
    base = np.array([cal.mu_z[int(value)] for value in zone])
    return base + pass_through * cost_t + nu_zt + promo_t * np.log1p(-depth_t)


def deployed_log_price(rec_log_price, legacy_log_price, D_s, kappa_scaled, xi_st, delta_t, u_st):
    return np.where(D_s, rec_log_price, legacy_log_price) + kappa_scaled * xi_st + delta_t * u_st


def instruments(cal, dgm, t, legacy_log_price_all_stores, zone, cost_t=0.0):
    prices = np.asarray(legacy_log_price_all_stores)
    other = np.array(
        [
            np.mean(prices[np.asarray(zone) != value])
            if np.any(np.asarray(zone) != value)
            else np.nan
            for value in zone
        ]
    )
    return {"cost_shifter": np.full(len(zone), cost_t), "other_zone_price": other}


def kappa_scaled(level, sigma_xi):
    if sigma_xi == 0:
        if level == 0:
            return 0.0
        raise ValueError("Nonzero kappa requires positive latent demand variance")
    return level / sigma_xi
