"""Opt-in inference validation; passing never changes the author's coverage flag."""

import os

import pytest
from test_dml import panel

from ktsim.estimators.dml import DML


@pytest.mark.slow
@pytest.mark.skipif(
    os.environ.get("KTSIM_VALIDATE_INFERENCE") != "1",
    reason="Set KTSIM_VALIDATE_INFERENCE=1 for the 200-draw validation",
)
def test_clustered_inference_coverage(cal):
    cfg = dict(n_folds=5, nuisance_params=dict(n_estimators=30, min_child_samples=30))
    counts = {False: 0, True: 0}
    for seed in range(200):
        frame = panel(cal, seed=1000 + seed, n_stores=50, weeks=104)
        for pliv in counts:
            result = DML(pliv).fit(frame, cal, cfg)
            assert result["converged"]
            counts[pliv] += result["ci_low"] <= -0.4 * cal.p_bar <= result["ci_high"]
    for count in counts.values():
        assert 0.90 <= count / 200 <= 0.99
