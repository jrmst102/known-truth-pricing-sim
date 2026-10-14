import numpy as np


def greedy_price(est, x_t, ladder):
    revenues = np.column_stack(
        [price * est["predict"](x_t, np.full(len(x_t), price)) for price in ladder]
    )
    if not np.isfinite(revenues).all():
        raise FloatingPointError("Nonfinite demand predictions")
    return ladder[np.argmax(revenues, axis=1)]
