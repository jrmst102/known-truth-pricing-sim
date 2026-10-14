from dataclasses import replace

import numpy as np

from ktsim.config import CellConfig
from ktsim.estimators.base import finalize
from ktsim.loop import run_replication
from ktsim.rng import draw_shocks, replication_streams


def test_legacy_fallback(cal, dgm, monkeypatch):
    class Missing:
        def fit(self, *args):
            return finalize(-1, predict=None)

    monkeypatch.setattr("ktsim.loop.get_estimator", lambda name: Missing())
    cell = CellConfig("base", -1.06, 0.05, 1, 0, 1, ["M1"], ["greedy"])
    shocks = draw_shocks(replication_streams(42, 1)[0], cal.n_stores, 53, cal, dgm)
    result = run_replication(
        cell, 0, shocks, cal, replace(dgm, cycles=1), {"M1_ols": {}}, save_storeweek=True
    )
    model = result[result.arm.eq("M1:greedy")].iloc[0]
    legacy = result[result.arm.eq("legacy:legacy")].iloc[0]
    assert model.fallback_used == 1
    assert model.predictions_unavailable
    assert model.R_dep_all == legacy.R_dep_all
    frame = result.attrs["storeweek"]
    assert frame[frame.arm.eq("M1:greedy")].fallback_used.all()


def test_oracle_regret_and_empty_model_set(cal, dgm):
    for kappa in (0, 0.05):
        cell = CellConfig("base", -1.06, kappa, 0, 0, 1, [], [], pass_through=0)
        shocks = draw_shocks(replication_streams(42, 1)[0], cal.n_stores, 54, cal, dgm)
        result = run_replication(
            cell, 0, shocks, cal, replace(dgm, cycles=2), {}, save_storeweek=True
        )
        oracle = result[result.arm.eq("oracle:oracle")]
        assert oracle.regret_rec_all.eq(0).all()
        assert oracle.regret_dep_model.isna().all()
        if kappa == 0:
            assert oracle.regret_dep_all.eq(0).all()
        else:
            assert oracle.regret_dep_all.ge(0).all()
        assert np.isfinite(oracle.R_star_all).all()
