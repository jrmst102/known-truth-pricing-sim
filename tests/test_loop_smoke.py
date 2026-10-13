from time import perf_counter

import numpy as np
import pandas as pd
import pytest

from ktsim.config import CellConfig
from ktsim.loop import run_replication
from ktsim.rng import draw_shocks, replication_streams


@pytest.mark.slow
def test_two_replications(cal, dgm):
    started = perf_counter()
    cell = CellConfig("P0", -1.06, 0., 0., 0., 2, ["M1", "M3"], ["greedy", "oracle"])
    for rep, ss in enumerate(replication_streams(42, 2)):
        shocks = draw_shocks(ss, cal.n_stores, dgm.history_weeks + dgm.cycles, cal, dgm)
        result = run_replication(cell, rep, shocks, cal, dgm, {"M1_ols": {}, "M3_iv": {}}, save_data=True)
        assert len(result) == 6 * dgm.cycles
        assert result.loc[result.arm.str.startswith("M1:"), "converged"].all()
        assert result.failure_reason.notna().equals(~result.converged)
        assert set(result.failure_reason.dropna()) <= {"nonconvergence", "nonfinite", "abs_eta_gt_10"}
        assert (result[result.arm.str.endswith(":oracle")].regret_rec == 0).all()
        assert result.oracle_at_bound.eq("interior").all()
        assert {"forecast", "realized"}.issubset(result.attrs["simulated_data"]["M1:greedy"])
        assert {78, 104, 156}.issubset(result.week.unique())
    assert perf_counter() - started < 300


def test_replay(cal, dgm):
    dgm.cycles = 2
    cell = CellConfig("P1", -1.06, .05, .5, .03, 1, ["M1"], ["greedy_rps"])
    ss = replication_streams(42, 1)[0]
    outputs = []
    for _ in range(2):
        replay_ss = np.random.SeedSequence(ss.entropy, spawn_key=ss.spawn_key)
        shocks = draw_shocks(replay_ss, cal.n_stores, 54, cal, dgm)
        result = run_replication(cell, 0, shocks, cal, dgm, {"M1_ols": {}})
        result.attrs.clear()
        outputs.append(result.drop(columns=["seconds"]))
    pd.testing.assert_frame_equal(*outputs, check_exact=True)


def test_ml_loop(cal, dgm):
    dgm.cycles = 1
    cell = CellConfig("P0", -1.06, 0., 0., 0., 1, ["M2", "M4_plr", "M4_pliv"], ["greedy"])
    params = {"n_estimators": 10, "learning_rate": .05, "num_leaves": 10, "min_child_samples": 10}
    cfg = {"M2_gbm": dict(params, fd_step=.01, fd_window_weeks=4),
           "M4_dml": dict(nuisance_params=params, n_folds=2)}
    shocks = draw_shocks(replication_streams(42, 1)[0], cal.n_stores, 53, cal, dgm)
    result = run_replication(cell, 0, shocks, cal, dgm, cfg)
    assert len(result) == 3
    assert result.converged.all()
    assert np.isfinite(result.forecast_mape).all()


def test_failed_fit_carries_recommendation(cal, dgm, monkeypatch):
    from ktsim.estimators.ols import OLS

    class FailSecondFit:
        count = 0

        def fit(self, frame, calibration, cfg):
            self.count += 1
            if self.count == 2:
                raise ValueError("Planted fitting failure")
            return OLS().fit(frame, calibration, cfg)

    forced = FailSecondFit()
    monkeypatch.setattr("ktsim.loop.get_estimator", lambda name: forced)
    dgm.cycles = 2
    cell = CellConfig("P1", -1.06, .05, .5, 0., 1, ["M1"], ["greedy"])
    shocks = draw_shocks(replication_streams(42, 1)[0], cal.n_stores, 54, cal, dgm)
    result = run_replication(cell, 0, shocks, cal, dgm, {"M1_ols": {}})
    assert result.converged.tolist() == [True, False]
    assert result.failure_reason.iloc[1] == "nonconvergence"
    assert result.p_rec.iloc[0] == result.p_rec.iloc[1]