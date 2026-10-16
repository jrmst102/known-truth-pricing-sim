"""Regression checks for pooling, reference applicability, and paired uncertainty."""
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ktsim.metrics import horizon_rmse, performance, replication_summary


def reporting_module():
    path = Path(__file__).parents[1] / "scripts/run_exploratory.py"
    spec = importlib.util.spec_from_file_location("exploratory_reporting", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_horizon_rmse_pools_squared_errors():
    # Two equal-sized weekly sets with RMSEs 3 and 4 have pooled RMSE sqrt(12.5).
    assert horizon_rmse([3, 4]) == np.sqrt(12.5)
    assert horizon_rmse([3, 4]) != 3.5
    assert np.isnan(horizon_rmse([np.nan]))


def test_reference_truth_is_not_an_estimate():
    rows = []
    for arm in ("M1:greedy", "legacy:legacy", "oracle:oracle"):
        for cycle in (1, 2):
            row = dict(cell="example", arm=arm, rep=0, cycle=cycle, week=cycle,
                       run_id="test", eta_hat=-1.06, eta_true=-1.06,
                       coverage_status="not applicable", ci_low=np.nan, ci_high=np.nan,
                       regret_dep_all=0.01, positive_slope=False, forecast_rmse=3 + (cycle == 2),
                       forecast_grid_rmse=3 + (cycle == 2), seconds=0, price_sd_26=0)
            for suffix in ("all", "model"):
                row.update({f"R_star_{suffix}": 100, f"R_dep_{suffix}": 99,
                            f"R_rec_{suffix}": 100})
            rows.append(row)
    frame = pd.DataFrame(rows)
    cfg = {"tau": 0.02, "window": 2}
    summary = replication_summary(frame, cfg).set_index("arm")
    assert summary.reliable_regret.eq(1).all()
    assert summary.loc["M1:greedy", "reliable"] == 1
    references = summary.loc[["legacy:legacy", "oracle:oracle"]]
    assert references[["terminal_error", "reliable", "reliable_sign", "positive_slope_rate"]].isna().all().all()
    perf = performance(frame, reliability=cfg)
    reference_perf = perf[perf.arm.str.startswith(("legacy:", "oracle:"))]
    assert reference_perf.n_estimated.eq(0).all()
    assert reference_perf.n_with_interval.eq(0).all()
    assert perf[perf.measure.eq("forecast_grid_rmse")].estimate.eq(np.sqrt(12.5)).all()
    frame.loc[frame.cycle.eq(2), "eta_hat"] = 0
    updated = replication_summary(frame, cfg).set_index("arm")
    assert updated.loc["M1:greedy", "reliable"] == 0
    assert updated.reliable_regret.eq(1).all()


def test_paired_mcse_uses_within_replication_differences():
    module = reporting_module()
    rows = []
    for rep, base in enumerate([0.1, 0.2, 0.3]):
        for arm in ("M1:greedy", "M1:greedy_rps", "M2:greedy", "M2:greedy_rps",
                    "M3:greedy", "M3:greedy_rps", "legacy:legacy"):
            # Large between-rep variation, but fixed model-minus-legacy differences.
            offset = 0 if arm == "legacy:legacy" else 0.01
            rows.append(dict(cell="example", environment="sna", kappa=0, rep=rep,
                             arm=arm, normalized_cumulative_deployed_regret=base + offset))
    rep = pd.DataFrame(rows)
    paired = module.paired_comparisons(rep)
    against_legacy = paired[paired.comparator_arm.eq("legacy:legacy")]
    assert len(paired) == 8
    assert paired.n_pairs.eq(3).all()
    assert np.allclose(against_legacy.mean_regret_difference_pp, 1)
    assert np.allclose(against_legacy.mcse_pp, 0, atol=1e-12)
    with pytest.raises(ValueError, match="Incomplete paired outcomes"):
        module.paired_comparisons(rep.drop(index=0))
