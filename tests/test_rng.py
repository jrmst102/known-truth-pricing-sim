import numpy as np
import pandas as pd

from ktsim.rng import (
    assign_model_stores,
    draw_shocks,
    latent_demand,
    mechanism_calibration,
    replication_streams,
)


def test_cost_shifter_independence(cal, dgm):
    shocks = draw_shocks(replication_streams(987, 1)[0], 10, 10000, cal, dgm)
    for values in (shocks.omega, shocks.eps, shocks.u):
        assert abs(np.corrcoef(shocks.cost.ravel(), values.ravel())[0, 1]) < 0.02
    assert abs(np.corrcoef(shocks.cost[:, 1:].ravel(), shocks.cost[:, :-1].ravel())[0, 1]) < 0.02


def test_zone_stratified_assignment():
    stores = pd.read_csv("data/calibration/stores_tti.csv")
    zones = stores.zone.to_numpy()
    assignment = assign_model_stores(np.random.default_rng(2).permutation(len(zones)), zones, 0.5)
    assert assignment.sum() == round(0.5 * len(zones))
    for zone in np.unique(zones):
        assert abs(assignment[zones == zone].sum() - 0.5 * sum(zones == zone)) <= 1


def test_design_shock_split(cal, dgm):
    effective = mechanism_calibration(cal, dgm)
    shocks = draw_shocks(replication_streams(88, 1)[0], 8, 100000, cal, dgm)
    xi = latent_demand(shocks, effective, 0)
    assert abs(np.corrcoef(xi[:, 1:].ravel(), xi[:, :-1].ravel())[0, 1] - 0.5) < 0.02
    variance = 0.5 * (cal.sigma_xi2 + cal.sigma_eps2)
    assert abs(np.var(xi) / variance - 1) < 0.02
