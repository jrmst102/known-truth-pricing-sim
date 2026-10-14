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


@pytest.mark.parametrize("price,cap", [(2.5, 20), (3.0, 40), (3.5, 80)])
def test_censored_expected_revenue(price, cap):
    from ktsim.oracle import censored_mean

    rng = np.random.default_rng(123)
    mu, variance = np.log(35), 0.08
    draws = rng.normal(size=500000)
    # Antithetic integration reduces simulation noise without changing the target.
    revenue = (
        price
        * np.minimum(np.exp(mu + np.sqrt(variance) * np.concatenate([draws, -draws])), cap).mean()
    )
    exact = price * censored_mean(mu, variance, cap)
    assert abs(exact / revenue - 1) < 0.001
