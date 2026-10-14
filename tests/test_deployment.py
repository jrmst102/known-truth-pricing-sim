from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from ktsim.config import CellConfig
from ktsim.dgm import deploy_price
from ktsim.loop import run_replication
from ktsim.oracle import price_ladder, project_price
from ktsim.rng import draw_shocks, replication_streams


def run(cal, dgm, phi=0.5, delta=0.03):
    cell = CellConfig("base", -1.06, 0.05, phi, delta, 1, ["M1"], ["greedy_rps"])
    shocks = draw_shocks(replication_streams(42, 1)[0], cal.n_stores, 54, cal, dgm)
    return run_replication(
        cell,
        0,
        shocks,
        cal,
        replace(dgm, cycles=2),
        {"M1_ols": {}},
        save_data=True,
        save_storeweek=True,
    )


def test_ladder_after_adjustments(cal, dgm):
    ladder = price_ladder(cal, dgm)
    np.testing.assert_array_equal(
        project_price((ladder[:-1] + ladder[1:]) / 2, ladder), ladder[:-1]
    )
    result = run(cal, dgm)
    for values in result.attrs["simulated_data"].values():
        frame = pd.DataFrame(values)
        assert np.isin(frame.price, ladder).all()
        assert not frame.censored.any()
    assert result.censored_share.eq(0).all()


def test_exploration_inert_at_phi_zero(cal, dgm):
    a, b = run(cal, dgm, 0, 0), run(cal, dgm, 0, 0.03)
    # Compare the two policies as well as explicit exploration levels.
    cell = CellConfig("base", -1.06, 0.05, 0, 0, 1, ["M1"], ["greedy"])
    shocks = draw_shocks(replication_streams(42, 1)[0], cal.n_stores, 54, cal, dgm)
    c = run_replication(
        cell, 0, shocks, cal, replace(dgm, cycles=2), {"M1_ols": {}}, save_data=True
    )
    np.testing.assert_array_equal(
        a.attrs["simulated_data"]["M1:greedy_rps"]["price"],
        b.attrs["simulated_data"]["M1:greedy_rps"]["price"],
    )
    np.testing.assert_array_equal(
        c.attrs["simulated_data"]["M1:greedy"]["price"],
        b.attrs["simulated_data"]["M1:greedy_rps"]["price"],
    )


@pytest.mark.parametrize("phi", [0, 1])
def test_cost_shifter_relevance(cal, dgm, phi):
    rng = np.random.default_rng(12)
    z = rng.normal(0, 0.05, 100000)
    price = deploy_price(np.full(len(z), 3.0), z, 0, phi, 0, 0, 0.2, 0, price_ladder(cal, dgm))
    coefficient = np.cov(z, np.log(price))[0, 1] / np.var(z, ddof=1)
    assert abs(coefficient / 0.2 - 1) < 0.1
