from dataclasses import replace

from ktsim.config import CellConfig
from ktsim.estimators.dml import DML
from ktsim.loop import run_replication
from ktsim.metrics import performance
from ktsim.rng import draw_shocks, replication_streams


def test_grouped_folds_and_features(cal, dgm):
    params = dict(n_estimators=10, learning_rate=0.05, num_leaves=10, min_child_samples=10)
    cfg = dict(nuisance_params=params, n_folds=5, inference_validated=False)
    shocks = draw_shocks(replication_streams(42, 1)[0], cal.n_stores, 53, cal, dgm)
    cell = CellConfig("base", -1.06, 0.05, 0.5, 0.03, 1, ["M4_pliv"], ["greedy"])
    result = run_replication(
        cell, 0, shocks, cal, replace(dgm, cycles=1), {"M4_dml": cfg}, save_data=True
    )
    import pandas as pd

    frame = pd.DataFrame(result.attrs["simulated_data"]["M4_pliv:greedy"])
    est = DML(pliv=True).fit(frame, cal, cfg)
    assert est["cluster_variance"]
    assert "store" not in est["nuisance_features"]
    assert len(est["fold_assignment"]) == cal.n_stores
    assert set(est["fold_assignment"].values()) == set(range(5))
    assert est["coverage_status"] == "withheld: inference not validated"
    records = result.attrs["fold_records"]
    assert records[0]["assignment"]
    # Even checkpoint output with intervals must withhold nominal coverage.
    result["week"] = 78
    perf = performance(result)
    m4 = perf[perf.arm.str.startswith("M4")]
    assert m4.coverage_status.str.startswith("withheld").all()
    assert m4[m4.measure.eq("coverage")].estimate.isna().all()
