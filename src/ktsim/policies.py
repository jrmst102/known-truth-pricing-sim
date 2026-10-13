import numpy as np


def greedy_price(est, x_t, ladder):
    revenues = np.column_stack(
        [price * est["predict"](x_t, np.full(len(x_t), price)) for price in ladder]
    )
    if not np.isfinite(revenues).all():
        raise FloatingPointError("Nonfinite demand predictions")
    return ladder[np.argmax(revenues, axis=1)]


def add_random_price_shock(log_price, delta, t, u_t, decay_power):
    if t < 1:
        raise ValueError("Exploration cycle starts at 1")
    return log_price + delta * t**decay_power * u_t
