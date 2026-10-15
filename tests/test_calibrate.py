import numpy as np
import pandas as pd

from ktsim.calibrate import calibrate, residual_components
from ktsim.clean import CleanResult
from ktsim.config import CalibrationConfig
from ktsim.rng import ar1


def test_variance_decomposition():
    rng = np.random.default_rng(12)
    latent = ar1(rng.normal(size=(10, 10000)), 0.6, 0.4)
    residual = latent + rng.normal(0, 0.2, latent.shape)
    frame = pd.DataFrame(
        {
            "store": np.repeat(np.arange(10), 10000),
            "week": np.tile(np.arange(10000), 10),
            "residual": residual.ravel(),
        }
    )
    rho, xi, eps = residual_components(frame, CalibrationConfig())
    assert abs(rho - 0.6) < 0.03
    assert abs(xi - 0.16) < 0.01
    assert abs(eps - 0.04) < 0.01


def test_variance_clipping():
    frame = pd.DataFrame(
        {"store": [1] * 4, "week": [1, 2, 3, 4], "residual": [1.0, -1.0, 1.0, -1.0]}
    )
    rho, xi, eps = residual_components(frame, CalibrationConfig())
    assert 0.2 <= rho <= 0.9
    assert 0 <= xi <= 0.9
    assert eps >= 0


def test_calibration_float_ids_serializes(tmp_path):
    rng = np.random.default_rng(12)
    weeks = np.tile(np.arange(1, 101), 2)
    promo = rng.binomial(1, 0.2, 200)
    price = 3.0 - 0.5 * promo + rng.normal(0, 0.1, 200)
    frame = pd.DataFrame(
        {
            "store": np.repeat([1.0, 2.0], 100),
            "zone": np.repeat([1, 2], 100),
            "week": weeks,
            "promo": promo,
            "price": price,
            "log_comp_index": rng.normal(0, 0.1, 200),
            "profit": 25.0,
            "log_q": 3.0 - 0.35 * (price - 3.0) + 0.2 * promo + rng.normal(0, 0.2, 200),
        }
    )
    clean = CleanResult(frame, 123, [1, 2], 0.0, False, [])
    cal = calibrate(clean, CalibrationConfig())
    cal.save(tmp_path / "calibration.json")
    assert set(cal.alpha_s) == {1, 2}
    assert cal.beta_reference < 0


def test_reference_price_mean():
    from ktsim.clean import clean_category
    from ktsim.io import load_movement

    frame = load_movement("data/fixtures/movement_small.csv")
    stores = pd.DataFrame({"store": [1, 2, 3], "zone": [1, 2, 1], "price_tier": ["L"] * 3})
    cfg = CalibrationConfig(plausibility={"retained_stores_min": 2})
    clean = clean_category(frame, pd.DataFrame({"upc": [123, 456, 999]}), stores, cfg)
    result = calibrate(clean, cfg)
    assert result.p_bar == clean.frame.price.mean()
    assert result.diagnostics["resid_var"] >= 0


def test_beta_reference_is_review_flag(cal):
    from ktsim.calibrate import check_plausibility

    cal.beta_reference = -3.16
    result = check_plausibility(
        cal, CalibrationConfig(plausibility={"beta_reference": [-2.59, -0.79]})
    )
    assert result[0].status == "flag"
