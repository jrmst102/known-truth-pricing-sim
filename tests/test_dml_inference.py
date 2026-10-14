"""Explicit opt-in validation; passing never changes the author's inference flag."""

import os

import numpy as np
import pandas as pd
import pytest

from ktsim.estimators.dml import DML
from ktsim.rng import ar1


@pytest.mark.slow
@pytest.mark.skipif(os.environ.get("RUN_DML_INFERENCE") != "1", reason="opt-in 200-draw study")
@pytest.mark.parametrize("pliv", [False, True])
def test_cluster_interval_coverage(cal, pliv):
    params = dict(n_estimators=20, learning_rate=0.05, num_leaves=8, min_child_samples=20)
    cfg = dict(nuisance_params=params, n_folds=5, inference_validated=False)
    covered = 0
    n_stores, weeks = 40, 52
    for seed in range(200):
        rng = np.random.default_rng(9000 + seed)
        store = np.repeat(np.arange(n_stores), weeks)
        t = np.tile(np.arange(1, weeks + 1), n_stores)
        promo = rng.binomial(1, 0.2, len(store))
        comp = rng.normal(0, 0.1, len(store))
        z = rng.normal(0, 1, len(store))
        price = cal.p_bar + 0.2 * z + rng.normal(0, 0.2, len(store))
        latent = ar1(rng.normal(size=(n_stores, weeks)), 0.5, 0.2).ravel()
        outcome = (
            np.repeat(rng.normal(3, 0.5, n_stores), weeks)
            - 1.06 / cal.p_bar * (price - cal.p_bar)
            + 0.2 * promo
            + 0.2 * comp
            + latent
            + rng.normal(0, 0.2, len(store))
        )
        frame = pd.DataFrame(
            dict(
                store=store,
                t=t,
                week_of_year=t,
                promo=promo,
                log_comp_index=comp,
                cost_shifter=z,
                price=price,
                log_q=outcome,
            )
        )
        result = DML(pliv=pliv).fit(frame, cal, cfg)
        assert np.isfinite(result["eta_hat"])
        covered += result["ci_low"] <= -1.06 <= result["ci_high"]
    rate = covered / 200
    assert 0.90 <= rate <= 0.99, rate
