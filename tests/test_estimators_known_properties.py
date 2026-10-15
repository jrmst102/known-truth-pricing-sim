import numpy as np
import pandas as pd
import pytest

from ktsim.dgm import controls, expected_log_demand
from ktsim.estimators import get_estimator


@pytest.fixture
def observable_data(cal, dgm):
    rng = np.random.default_rng(345)
    frames = []
    for t in range(1, 251):
        stores = np.array(sorted(cal.alpha_s))
        frame = controls(
            cal,
            dgm,
            stores,
            [dgm.store_zones[store] for store in stores],
            t,
            rng.binomial(1, 0.15),
            rng.normal(0, 0.1),
        )
        frame["cost_shifter"] = rng.normal(0, 0.1)
        frame["price"] = cal.p_bar + 2 * frame.cost_shifter + rng.normal(0, 0.03, len(stores))
        frame["log_q"] = expected_log_demand(cal, dgm, frame, frame.price, -1.06) + rng.normal(
            0, 0.1, len(stores)
        )
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


@pytest.mark.parametrize("name", ["M1", "M3", "M3_cf"])
def test_known_property(name, observable_data, cal):
    est = get_estimator(name).fit(observable_data, cal, {})
    assert est["converged"]
    se = (est["ci_high"] - est["ci_low"]) / 3.92
    assert abs(est["eta_hat"] + 1.06) < 2 * se
    if name != "M1":
        assert est["first_stage_F"] > 50


@pytest.mark.parametrize("name", ["M2", "M4_plr", "M4_pliv"])
def test_ml_fits_observable_data(name, observable_data, cal):
    params = {"n_estimators": 30, "learning_rate": 0.05, "num_leaves": 10, "min_child_samples": 20}
    cfg = dict(params, nuisance_params=params, n_folds=2, fd_window_weeks=4, fd_step=0.01)
    est = get_estimator(name).fit(observable_data, cal, cfg)
    assert est["converged"]
    assert est["eta_hat"] <= 0
    forecast = est["predict"](observable_data.iloc[:8], np.full(8, cal.p_bar))
    assert np.isfinite(forecast).all()
    assert (forecast > 0).all()
