import numpy as np
import pandas as pd

from ktsim.decisions import choose_n_sim, choose_pass_through
from ktsim.metrics import mcse_bias, mcse_coverage, mcse_empse, mcse_mean, mcse_mse


def test_hand_computed_mcse():
    values = np.array([1.0, 2.0, 3.0])
    assert np.isclose(mcse_mean(values), 1 / np.sqrt(3))
    assert np.isclose(mcse_bias(values, 2), 1 / np.sqrt(3))
    assert np.isclose(mcse_empse(values), 0.5)
    assert np.isclose(mcse_mse(values, 2), 1 / 3)
    assert np.isclose(mcse_coverage([1, 0, 1, 0]), 0.25)
    assert np.isnan(mcse_mean([1]))


def test_n_sim_and_cap():
    perf = pd.DataFrame(
        [
            dict(arm="M1:greedy", measure="bias", cycle_or_horizon="156", mcse=0.1, n_reps=100),
            dict(
                arm="M1:greedy",
                measure="regret_rec",
                cycle_or_horizon="horizon",
                mcse=0.01,
                n_reps=100,
            ),
        ]
    )
    result = choose_n_sim(perf)
    assert result.required == 2500
    assert result.n_sim == 2000
    assert result.cap_exceeded
    perf.iloc[0, perf.columns.get_loc("cycle_or_horizon")] = "78"
    assert choose_n_sim(perf).n_sim is None


def test_pass_through():
    frame = pd.DataFrame(
        {
            "cell": ["P4:pass_through=0.1", "P4:pass_through=1"],
            "arm": ["M3:legacy"] * 2,
            "cycle": [104] * 2,
            "first_stage_F": [10.0, 60.0],
        }
    )
    result = choose_pass_through(frame)
    assert result.weak == 0.1
    assert result.strong == 1


def test_revenue_weighted_regret_example():
    import json
    from pathlib import Path

    from ktsim.metrics import revenue_summary

    example = json.loads(Path("tests/fixtures/regret_example.json").read_text())
    stars, deployed = np.array(example["R_star"]), np.array(example["R_dep"])
    weekly = (stars - deployed).sum(axis=1) / stars.sum(axis=1)
    np.testing.assert_allclose(weekly, example["weekly_regret"], atol=1e-12)
    frame = pd.DataFrame({"R_star_all": stars.sum(axis=1), "R_dep_all": deployed.sum(axis=1)})
    result = revenue_summary(frame)
    assert abs(result["cum_loss"] - example["cum_loss"]) < 1e-12
    assert abs(result["norm_cum_regret"] - example["normalized"]) < 1e-12


def test_reliability_joint_criterion():
    from ktsim.metrics import reliability

    frame = pd.DataFrame({"cycle": range(1, 27), "regret_dep_all": 0.01, "eta_hat": -1.0})
    assert reliability(frame)["reliable"]
    frame.loc[3, "eta_hat"] = np.nan
    assert reliability(frame) == dict(reliable=False, reliable_regret=True, reliable_sign=False)
    frame.loc[4, "regret_dep_all"] = 0.021
    assert not reliability(frame)["reliable_regret"]


def test_failure_denominators_and_withheld_coverage():
    from ktsim.config import Calibration, CellConfig, DGMConfig
    from ktsim.loop import run_replication
    from ktsim.metrics import performance
    from ktsim.rng import draw_shocks, replication_streams

    cal = Calibration.load("data/fixtures/calibration_synthetic.json")
    dgm = DGMConfig(cycles=1, store_zones={s: 1 if s <= 4 else 2 for s in cal.alpha_s})
    cell = CellConfig("case", -1.06, 0, 0.5, 0, 1, ["M1"], ["greedy"])
    shocks = draw_shocks(replication_streams(4, 1)[0], cal.n_stores, 53, cal, dgm)
    result = run_replication(cell, 0, shocks, cal, dgm, {"M1_ols": {}})
    result.attrs.clear()
    copies = []
    for rep, eta in enumerate([-1.0, np.nan, -12.0]):
        row = result.copy()
        row["rep"], row["cycle"], row["eta_hat"] = rep, 104, eta
        row["ci_low"], row["ci_high"] = (-1.2, -0.8) if rep == 0 else (np.nan, np.nan)
        row["arm"], row["coverage_status"] = "M4_plr:greedy", "withheld: inference not validated"
        copies.append(row)
    perf = performance(pd.concat(copies))
    assert perf.n_total.eq(3).all()
    assert perf.n_estimated.eq(2).all()
    assert perf.n_with_interval.eq(1).all()
    assert perf[perf.measure.eq("coverage")].estimate.isna().all()
    assert np.isclose(perf[perf.measure.eq("bias")].estimate.iloc[0], (-1 - 12) / 2 + 1.06)


def test_n_required_includes_all_cells_and_paired_differences():
    from ktsim.decisions import choose_n_required

    cfg = dict(
        targets=dict(elasticity=0.02, regret=0.0025, paired_regret=0.0025),
        floor=1,
        cap=2000,
        budget_hours=150,
    )
    records = []
    for cell in ["sna", "tti"]:
        for arm in ["M1:greedy", "M3:greedy"]:
            for measure, checkpoint, mcse in [
                ("bias", "104", 0.1 if cell == "tti" else 0.01),
                ("norm_cum_regret_all", "horizon", 0.001),
            ]:
                records.append(
                    dict(
                        cell=cell,
                        arm=arm,
                        measure=measure,
                        cycle_or_horizon=checkpoint,
                        mcse=mcse,
                        n_reps=100,
                    )
                )
    reps = pd.DataFrame(
        [
            dict(cell="sna", arm=arm, rep=rep, norm_cum_regret_all=value)
            for rep in range(3)
            for arm, value in [("M1:greedy", 0.01 * rep), ("M3:greedy", 0.02 * rep)]
        ]
    )
    result = choose_n_required(pd.DataFrame(records), cfg, reps)
    assert result["N_required"] == 2500
    assert result["bounding"]["cell"] == "tti"
    assert result["n_selected"] == 2000 and result["shortfall"]
    assert result["paired"][0]["required"] == 16
