"""Oracles observe current controls and pre-set capacity, never realized shocks."""

import numpy as np
from scipy.special import ndtr

from ktsim.dgm import expected_log_demand


def price_ladder(cal, dgm) -> np.ndarray:
    lower = cal.p_bar * dgm.feasible_band["lower"]
    upper = cal.p_bar * dgm.feasible_band["upper"]
    start = np.ceil((lower - 1e-10) / dgm.ladder_step)
    end = np.floor((upper + 1e-10) / dgm.ladder_step)
    ladder = np.round(np.arange(start, end + 1) * dgm.ladder_step, 10)
    if len(ladder) == 0:
        raise ValueError("Feasible price band contains no ladder points")
    return ladder


def oracle_price(cal, dgm, eta) -> float:
    ladder = price_ladder(cal, dgm)
    slope = abs(eta) / cal.p_bar
    return float(ladder[np.argmax(ladder * np.exp(-slope * (ladder - cal.p_bar)))])


def bound_classification(price, ladder) -> str:
    if np.isclose(price, ladder[-1]):
        return "ceiling"
    if np.isclose(price, ladder[0]):
        return "floor"
    return "interior"


def regret(p_rec, p_star, b, p_bar) -> np.ndarray:
    best = p_star * np.exp(-b * (p_star - p_bar))
    achieved = np.asarray(p_rec) * np.exp(-b * (np.asarray(p_rec) - p_bar))
    return (best - achieved) / best


def project_price(price, ladder):
    """Nearest feasible price; numerical midpoint ties resolve downward."""
    prices = np.asarray(price)
    upper = np.clip(np.searchsorted(ladder, prices), 0, len(ladder) - 1)
    lower = np.maximum(upper - 1, 0)
    midpoint = (ladder[lower] + ladder[upper]) / 2
    return ladder[np.where(prices <= midpoint + 1e-12, lower, upper)]


def censored_lognormal_mean(mu, variance, cap):
    mu, cap = np.broadcast_arrays(mu, cap)
    if np.any(cap <= 0) or variance < 0:
        raise ValueError("Capacity must be positive and variance nonnegative")
    if variance == 0:
        return np.minimum(np.exp(mu), cap)
    sd = np.sqrt(variance)
    a = (np.log(cap) - mu) / sd
    return np.exp(mu + variance / 2) * ndtr(a - sd) + cap * ndtr(-a)


def expected_revenue(cal, dgm, frame, price, eta, capacity=None):
    mu = expected_log_demand(cal, dgm, frame, price, eta)
    variance = cal.sigma_xi2 + cal.sigma_eps2
    demand = (
        np.exp(mu + variance / 2)
        if capacity is None
        else censored_lognormal_mean(mu, variance, capacity)
    )
    return np.asarray(price) * demand


def censored_oracle_price(cal, dgm, frame, eta, capacity):
    ladder = price_ladder(cal, dgm)
    revenues = np.column_stack(
        [expected_revenue(cal, dgm, frame, p, eta, capacity) for p in ladder]
    )
    return ladder[np.argmax(revenues, axis=1)]
