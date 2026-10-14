from dataclasses import replace

import numpy as np

from ktsim.config import CellConfig
from ktsim.dgm import deploy_price
from ktsim.loop import run_replication
from ktsim.oracle import price_ladder, project_price
from ktsim.rng import draw_shocks, replication_streams


def test_ladder_after_adjustments(cal, dgm):
    dgm.cycles = 2
    ladder = price_ladder(cal, dgm)
    np.testing.assert_array_equal(
        project_price((ladder[:-1] + ladder[1:]) / 2, ladder), ladder[:-1]
    )
    cell = CellConfig("check", -1.06, 0.05, 0.5, 0.03, 1, ["M1"], ["greedy_rps"], references=True)
    shocks = draw_shocks(replication_streams(42, 1)[0], cal.n_stores, 54, cal, dgm)
    result = run_replication(cell, 0, shocks, cal, dgm, {"M1_ols": {}}, save_data=True)
    for data in result.attrs["simulated_data"].values():
        assert np.isin(data["price"], ladder).all()
        assert not any(data["censored"])
    for prices in result.deployed_prices:
        assert np.isin(prices, ladder).all()


def test_exploration_inert_at_phi_zero(cal, dgm):
    dgm.cycles = 2
    cell = CellConfig("check", -1.06, 0.05, 0, 0.03, 1, ["M1"], ["greedy_rps"])
    shocks = draw_shocks(replication_streams(42, 1)[0], cal.n_stores, 54, cal, dgm)
    first = run_replication(cell, 0, shocks, cal, dgm, {"M1_ols": {}})
    second = run_replication(replace(cell, delta=0), 0, shocks, cal, dgm, {"M1_ols": {}})
    assert first.deployed_prices.tolist() == second.deployed_prices.tolist()
    assert first.regret_dep_model.isna().all()


def test_cost_shifter_relevance(cal, dgm):
    rng = np.random.default_rng(71)
    z = rng.normal(0, 0.05, 100_000)
    ladder = price_ladder(cal, dgm)
    for phi in (0, 1):
        price = deploy_price(
            np.full(len(z), cal.p_bar), ladder, z, 0.2, 0, 0, np.full(len(z), phi, bool), 0, 0
        )
        slope = np.cov(np.log(price), z)[0, 1] / np.var(z, ddof=1)
        assert abs(slope / 0.2 - 1) < 0.1


def test_oracle_zero_regret_and_adjusted_regret(cal, dgm):
    dgm.cycles = 2
    cell = CellConfig("oracle_check", -1.06, 0, 1, 0, 1, [], [], references=True, pass_through=0)
    shocks = draw_shocks(replication_streams(124, 1)[0], cal.n_stores, 54, cal, dgm)
    for kappa in (0, 0.05):
        result = run_replication(replace(cell, kappa=kappa), 0, shocks, cal, dgm, {})
        oracle = result[result.arm.eq("oracle:oracle")]
        assert oracle.regret_rec_all.eq(0).all()
        assert oracle.regret_dep_all.ge(0).all()
        if kappa == 0:
            assert oracle.regret_dep_all.eq(0).all()
