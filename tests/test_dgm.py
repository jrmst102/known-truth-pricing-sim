import numpy as np

from ktsim.dgm import controls, draw_sales, expected_log_demand, kappa_scaled
from ktsim.rng import draw_shocks, latent_demand, replication_streams


def test_elasticity_and_censoring(cal, dgm):
    stores = np.array(list(cal.alpha_s))
    x = controls(cal, dgm, stores, [dgm.store_zones[store] for store in stores], 1, 0, 0)
    step = 1e-5
    upper = expected_log_demand(cal, dgm, x, cal.p_bar * np.exp(step), -1.06)
    lower = expected_log_demand(cal, dgm, x, cal.p_bar * np.exp(-step), -1.06)
    np.testing.assert_allclose((upper - lower) / (2 * step), -1.06)
    mean = expected_log_demand(cal, dgm, x, cal.p_bar, -1.06)
    sales = draw_sales(cal, dgm, x, cal.p_bar, -1.06, 5, 0, True)
    np.testing.assert_allclose(sales, 1.5 * np.exp(mean))
    assert np.isclose(kappa_scaled(0.05, 0.2) * 0.2, 0.05)


def test_replay_and_common_variance(cal, dgm):
    ss = replication_streams(42, 1)[0]
    first = draw_shocks(ss, 8, 10000, cal, dgm)
    second = draw_shocks(ss, 8, 10000, cal, dgm)
    np.testing.assert_array_equal(first.omega, second.omega)
    xi = latent_demand(first, cal, 0.5)
    assert abs(np.var(xi) - cal.sigma_xi2) < 0.003
    assert abs(np.corrcoef(xi)[0, 1] - 0.5) < 0.04
