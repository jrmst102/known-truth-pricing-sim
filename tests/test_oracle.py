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
