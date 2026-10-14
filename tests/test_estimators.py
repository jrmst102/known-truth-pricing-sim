import numpy as np
import pandas as pd

from ktsim.estimators.base import finalize, smearing_factor
from ktsim.policies import greedy_price


def test_extreme_and_positive_retained():
    for eta in (-12, 0.3):
        result = finalize(eta, predict=lambda frame, price: np.exp(eta * price))
        assert result["eta_hat"] == eta
        assert result["extreme_estimate"] == (eta == -12)
        assert result["positive_slope"] == (eta > 0)
        assert not result["numerical_failure"]
        recommendation = greedy_price(result, pd.DataFrame({"store": [1]}), np.array([1.0, 2.0]))
        assert recommendation[0] == (1 if eta < 0 else 2)
    assert finalize(-12, predict=None)["predictions_unavailable"]


def test_smearing_factor():
    assert abs(smearing_factor(np.zeros(100)) - 1) < 1e-12
    residuals = np.array([-0.4, 0.1, 0.3])
    assert smearing_factor(residuals) == np.exp(residuals).mean()
