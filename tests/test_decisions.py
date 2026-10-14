import numpy as np
import pandas as pd

from ktsim.cli import read_config
from ktsim.decisions import choose_n_required


def test_precision_bound_and_paired():
    frame = pd.DataFrame(
        [
            dict(
                cell="base",
                arm=arm,
                rep=rep,
                terminal_error=rep * 0.01,
                norm_cum_regret_all=rep * 0.01 + offset,
            )
            for arm, offset in [("M1:greedy", 0), ("M3:greedy", 0.005), ("M1:greedy_rps", -0.01)]
            for rep in range(10)
        ]
    )
    cfg = read_config("configs/decisions.yaml")
    result = choose_n_required(frame, cfg)
    expected = int(
        np.ceil((frame[frame.arm.eq("M1:greedy")].norm_cum_regret_all.std(ddof=1) / 0.0025) ** 2)
    )
    assert result["N_required"] == expected
    assert result["bounding"]["measure"] == "norm_cum_regret_all"
    assert all(row["required"] <= 1 for row in result["paired"])
    cfg["cap"] = 10
    result = choose_n_required(frame, cfg)
    assert result["cap_exceeded"]
    assert result["bounding"]["target_shortfall_at_cap"] > 0
