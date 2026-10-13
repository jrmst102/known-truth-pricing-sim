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
    return 100 * (best - achieved) / best