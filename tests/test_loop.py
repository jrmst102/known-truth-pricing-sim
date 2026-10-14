import numpy as np
import pandas as pd

from ktsim.config import CellConfig
from ktsim.estimators.base import failed
from ktsim.loop import run_replication
from ktsim.rng import draw_shocks, replication_streams


def test_legacy_fallback(cal, dgm, monkeypatch):
    class NoPrediction:
        def fit(self, *args):
            return failed()

    monkeypatch.setattr("ktsim.loop.get_estimator", lambda name: NoPrediction())
    dgm.cycles = 2
    cell = CellConfig("check", -1.06, 0.05, 1, 0, 1, ["M1"], ["greedy", "legacy"])
    shocks = draw_shocks(replication_streams(14, 1)[0], cal.n_stores, 54, cal, dgm)
    result = run_replication(cell, 0, shocks, cal, dgm, {"M1_ols": {}}, save_data=True)
    greedy = pd.DataFrame(result.attrs["simulated_data"]["M1:greedy"])
    legacy = pd.DataFrame(result.attrs["simulated_data"]["M1:legacy"])
    np.testing.assert_array_equal(greedy.price, legacy.price)
    assert greedy[greedy.cycle > 0].fallback_used.all()
    assert result[result.arm.eq("M1:greedy")].fallback_used.eq(1).all()
    assert result.R_dep_all.gt(0).all()


def test_partial_predictions_fall_back_per_store(cal, dgm, monkeypatch):
    from ktsim.estimators.base import finalize

    class PartialPrediction:
        def fit(self, *args):
            def predict(frame, price):
                return np.where(frame.store.to_numpy() == 1, np.nan, np.exp(-0.1 * price))

            return finalize(-0.3, predict=predict)

    monkeypatch.setattr("ktsim.loop.get_estimator", lambda name: PartialPrediction())
    dgm.cycles = 1
    cell = CellConfig("case", -1.06, 0.05, 1, 0, 1, ["M1"], ["greedy"])
    shocks = draw_shocks(replication_streams(14, 1)[0], cal.n_stores, 53, cal, dgm)
    result = run_replication(cell, 0, shocks, cal, dgm, {"M1_ols": {}}, save_storeweek=True)
    audit = result.attrs["storeweek"]
    assert audit.fallback_used.sum() == 1
    assert result.fallback_used.iloc[0] == 1 / cal.n_stores


def test_failed_dml_still_withholds_coverage(cal, dgm, monkeypatch):
    class NoFit:
        def fit(self, *args):
            raise ValueError("planted DML failure")

    monkeypatch.setattr("ktsim.loop.get_estimator", lambda name: NoFit())
    dgm.cycles = 1
    cell = CellConfig("case", -1.06, 0.05, 1, 0, 1, ["M4_plr"], ["greedy"])
    shocks = draw_shocks(replication_streams(14, 1)[0], cal.n_stores, 53, cal, dgm)
    result = run_replication(cell, 0, shocks, cal, dgm, {"M4_dml": {"inference_validated": False}})
    assert result.coverage_status.str.startswith("withheld").all()
