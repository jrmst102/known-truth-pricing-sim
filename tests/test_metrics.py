import numpy as np
import pandas as pd

from ktsim.decisions import choose_n_sim, choose_pass_through
from ktsim.metrics import mcse_bias, mcse_coverage, mcse_empse, mcse_mean, mcse_mse


def test_hand_computed_mcse():
    values = np.array([1., 2., 3.])
    assert np.isclose(mcse_mean(values), 1 / np.sqrt(3))
    assert np.isclose(mcse_bias(values, 2), 1 / np.sqrt(3))
    assert np.isclose(mcse_empse(values), .5)
    assert np.isclose(mcse_mse(values, 2), 1 / 3)
    assert np.isclose(mcse_coverage([1, 0, 1, 0]), .25)
    assert np.isnan(mcse_mean([1]))


def test_n_sim_and_cap():
    perf = pd.DataFrame([dict(arm="M1:greedy", measure="bias", cycle_or_horizon="156",
                              mcse=.1, n_reps=100),
                         dict(arm="M1:greedy", measure="regret_rec", cycle_or_horizon="horizon",
                              mcse=.01, n_reps=100)])
    result = choose_n_sim(perf)
    assert result.required == 2500
    assert result.n_sim == 2000
    assert result.cap_exceeded
    perf.iloc[0, perf.columns.get_loc("cycle_or_horizon")] = "78"
    assert choose_n_sim(perf).n_sim is None


def test_pass_through():
    frame = pd.DataFrame({"cell": ["P4:pass_through=0.1", "P4:pass_through=1"],
                          "arm": ["M3:legacy"] * 2, "cycle": [104] * 2, "first_stage_F": [10., 60.]})
    result = choose_pass_through(frame)
    assert result.weak == .1
    assert result.strong == 1