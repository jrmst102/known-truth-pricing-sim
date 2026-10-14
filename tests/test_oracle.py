import numpy as np
import pytest

from ktsim.oracle import bound_classification, oracle_price, price_ladder, regret


@pytest.mark.parametrize("eta,bound", [(-0.8, "ceiling"), (-1.06, "interior"), (-2.5, "floor")])
def test_oracle(cal, dgm, eta, bound):
    ladder = price_ladder(cal, dgm)
    best = oracle_price(cal, dgm, eta)
    brute = ladder[np.argmax(ladder * np.exp(-abs(eta) / cal.p_bar * (ladder - cal.p_bar)))]
    assert best == brute
    assert bound_classification(best, ladder) == bound
    loss = regret(ladder, best, abs(eta) / cal.p_bar, cal.p_bar)
    assert np.isclose(loss[ladder == best], 0)
    assert np.all(loss[ladder != best] > 0)


def test_censored_expected_revenue():
    from ktsim.oracle import censored_lognormal_mean

    rng = np.random.default_rng(104)
    # Antithetic integration reduces Monte Carlo noise without changing the target.
    draws = rng.normal(size=500_000)
    shocks = np.r_[draws, -draws]
    for price, cap in [(2.0, 10.0), (3.0, 25.0), (4.0, 80.0)]:
        mu, variance = 3 - 0.35 * (price - 3), 0.25
        mc = price * np.minimum(np.exp(mu + np.sqrt(variance) * shocks), cap).mean()
        exact = price * censored_lognormal_mean(mu, variance, cap)
        assert abs(mc / exact - 1) < 0.001
