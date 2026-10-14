import numpy as np


def greedy_price(est, x_t, ladder, *, return_unavailable=False):
    revenues = np.column_stack(
        [price * est["predict"](x_t, np.full(len(x_t), price)) for price in ladder]
    )
    unavailable = ~np.isfinite(revenues).all(axis=1)
    if unavailable.any() and not return_unavailable:
        raise FloatingPointError("Nonfinite demand predictions")
    recommendation = ladder[np.argmax(np.where(np.isfinite(revenues), revenues, -np.inf), axis=1)]
    return (recommendation, unavailable) if return_unavailable else recommendation
