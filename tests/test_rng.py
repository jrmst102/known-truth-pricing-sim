import numpy as np
import pandas as pd

from ktsim.rng import (
    assign_model_stores,
    draw_shocks,
    latent_demand,
    replication_streams,
)


def test_cost_shifter_independence(cal, dgm):
    shocks = draw_shocks(replication_streams(1, 1)[0], 10, 10000, cal, dgm)
    cost = shocks.cost.ravel()
    for other in (shocks.omega, shocks.eps, shocks.u):
        assert abs(np.corrcoef(cost, other.ravel())[0, 1]) < 0.02
    assert abs(np.corrcoef(shocks.cost[:, 1:].ravel(), shocks.cost[:, :-1].ravel())[0, 1]) < 0.02


def test_zone_stratified_assignment():
    frame = pd.read_csv("data/calibration/stores_tti.csv").sort_values("store")
    permutation = np.random.default_rng(12).permutation(len(frame))
    model = assign_model_stores(permutation, frame.zone, 0.5)
    assert model.sum() == round(0.5 * len(frame))
    for zone in frame.zone.unique():
        mask = frame.zone.eq(zone)
        assert abs(model[mask].sum() - 0.5 * mask.sum()) <= 1


def test_design_shock_split(cal, dgm):
    # Empirical calibration deliberately disagrees with the design.
    cal.rho_xi = 0.9
    cal.sigma_xi2, cal.sigma_eps2 = 0.07, 0.01
    shocks = draw_shocks(replication_streams(1, 1)[0], 4, 100000, cal, dgm)
    xi = latent_demand(shocks, cal, 0, dgm)
    assert abs(np.corrcoef(xi[:, 1:].ravel(), xi[:, :-1].ravel())[0, 1] - 0.5) < 0.02
    assert abs(np.var(xi) / (0.5 * cal.resid_var) - 1) < 0.02
    assert abs(np.var(shocks.eps) / (0.5 * cal.resid_var) - 1) < 0.02
