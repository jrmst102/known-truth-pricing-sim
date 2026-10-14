import numpy as np
import pandas as pd

from ktsim.metrics import mcse_bias, mcse_coverage, mcse_empse, mcse_mean, mcse_mse


def test_hand_computed_mcse():
    values = np.array([1.0, 2.0, 3.0])
    assert np.isclose(mcse_mean(values), 1 / np.sqrt(3))
    assert np.isclose(mcse_bias(values, 2), 1 / np.sqrt(3))
    assert np.isclose(mcse_empse(values), 0.5)
    assert np.isclose(mcse_mse(values, 2), 1 / 3)
    assert np.isclose(mcse_coverage([1, 0, 1, 0]), 0.25)
    assert np.isnan(mcse_mean([1]))


def test_revenue_weighted_regret_example():
    import json
    from pathlib import Path

    from ktsim.loop import revenue_totals
    from ktsim.metrics import replication_summary

    fixture = json.loads(Path("tests/fixtures/regret_example.json").read_text())
    rows = []
    for week, (star, dep, rec) in enumerate(zip(fixture["star"], fixture["dep"], fixture["rec"])):
        totals = revenue_totals(
            np.array(star), np.array(dep), np.array(rec), np.array(fixture["model"])
        )
        assert abs(totals["regret_dep_all"] - fixture["weekly_regret_all"][week]) < 1e-12
        rows.append(
            dict(
                cell="base",
                arm="M1:greedy",
                rep=0,
                cycle=week + 1,
                eta_hat=-1,
                eta_true=-1,
                fallback_used=0,
                extreme_estimate=False,
                positive_slope=False,
                numerical_failure=False,
                forecast_mape=0,
                forecast_rmse=0,
                censored_share=0,
                seconds=0,
                price_sd_26=0,
                **totals,
            )
        )
    row = replication_summary(pd.DataFrame(rows), {"tau": 0.02, "window": 2}).iloc[0]
    assert abs(row.cum_loss_all - 150) < 1e-12
    assert abs(row.norm_cum_regret_all - 0.1) < 1e-12
    assert abs(row.norm_cum_regret_model - 80 / 1150) < 1e-12
    assert row.norm_cum_regret_all_rec == 0


def test_reliability_joint_criterion(cal, dgm):
    from dataclasses import replace

    from ktsim.config import CellConfig
    from ktsim.loop import run_replication
    from ktsim.metrics import performance, replication_summary
    from ktsim.rng import draw_shocks, replication_streams

    dgm = replace(dgm, cycles=2)
    cell = CellConfig("base", -1.06, 0, 0.5, 0, 1, ["M1"], ["greedy"])
    shocks = draw_shocks(replication_streams(42, 1)[0], cal.n_stores, 54, cal, dgm)
    result = run_replication(cell, 0, shocks, cal, dgm, {"M1_ols": {}})
    result["regret_dep_all"] = 0.01
    result["eta_hat"] = -1.0
    cfg = {"tau": 0.02, "window": 2}
    assert replication_summary(result, cfg).reliable.eq(1).all()
    result.loc[result.cycle.eq(2), "eta_hat"] = np.nan
    summary = replication_summary(result, cfg)
    assert summary.reliable_regret.eq(1).all()
    assert summary.reliable_sign.eq(0).all()
    assert summary.reliable.eq(0).all()
    perf = performance(result, reliability=cfg)
    assert (perf.n_estimated <= perf.n_total).all()
    assert (perf.n_with_interval <= perf.n_estimated).all()
