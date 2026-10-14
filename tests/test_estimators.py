import numpy as np

from ktsim.estimators.base import finalize, smearing_factor
from ktsim.policies import greedy_price


def test_extreme_and_positive_retained():
    for eta, extreme, positive in [(-12, True, False), (0.3, False, True)]:
        est = finalize(eta, predict=lambda x, p: np.exp(-p))
        assert est["eta_hat"] == eta
        assert est["extreme_estimate"] == extreme
        assert est["positive_slope"] == positive
        assert not est["numerical_failure"]
        assert greedy_price(est, [0, 1], np.array([2.4, 3.6])).shape == (2,)


def test_smearing_factor():
    assert abs(smearing_factor(np.zeros(10)) - 1) < 1e-12
    residuals = np.array([-0.3, 0.1, 0.2])
    assert abs(smearing_factor(residuals) - np.exp(residuals).mean()) < 1e-12
