import numpy as np


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


def project_price(prices, ladder):
    prices = np.asarray(prices)
    distance = np.abs(prices[..., None] - ladder)
    # The ascending ladder and first True resolve floating-point midpoint ties downward.
    nearest = distance.min(axis=-1, keepdims=True)
    return ladder[np.argmax(np.isclose(distance, nearest, rtol=0, atol=1e-12), axis=-1)]


def censored_mean(log_mean, variance, cap):
    """E[min(exp(N(mu, variance)), cap)] by lognormal partial expectation."""
    from scipy.special import ndtr

    mu, cap = np.broadcast_arrays(log_mean, cap)
    if variance == 0:
        return np.minimum(np.exp(mu), cap)
    sd = np.sqrt(variance)
    a = (np.log(cap) - mu) / sd
    return np.exp(mu + variance / 2) * ndtr(a - sd) + cap * ndtr(-a)


def expected_revenue(cal, dgm, frame, price, eta, cap=None):
    from ktsim.dgm import expected_log_demand
    from ktsim.rng import shock_parameters

    _, xi_var, eps_var = shock_parameters(cal, dgm)
    mean = expected_log_demand(cal, dgm, frame, price, eta)
    variance = xi_var + eps_var
    demand = np.exp(mean + variance / 2) if cap is None else censored_mean(mean, variance, cap)
    return np.asarray(price) * demand


def censored_oracle(cal, dgm, frame, eta, cap):
    """Observes controls and fixed capacity, never the realized latent state."""
    ladder = price_ladder(cal, dgm)
    revenue = np.column_stack(
        [expected_revenue(cal, dgm, frame, price, eta, cap) for price in ladder]
    )
    return ladder[np.argmax(revenue, axis=1)]
