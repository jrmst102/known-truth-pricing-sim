import numpy as np
import pandas as pd

from ktsim.calibrate import calibrate, residual_components
from ktsim.clean import CleanResult
from ktsim.config import CalibrationConfig
from ktsim.rng import ar1


def test_variance_decomposition():
    rng = np.random.default_rng(12)
    latent = ar1(rng.normal(size=(10, 10000)), .6, .4)
    residual = latent + rng.normal(0, .2, latent.shape)
    frame = pd.DataFrame({"store": np.repeat(np.arange(10), 10000),
                          "week": np.tile(np.arange(10000), 10), "residual": residual.ravel()})
    rho, xi, eps = residual_components(frame, CalibrationConfig())
    assert abs(rho - .6) < .03
    assert abs(xi - .16) < .01
    assert abs(eps - .04) < .01


def test_variance_clipping():
    frame = pd.DataFrame({"store": [1] * 4, "week": [1, 2, 3, 4],
                          "residual": [1., -1., 1., -1.]})
    rho, xi, eps = residual_components(frame, CalibrationConfig())
    assert .2 <= rho <= .9
    assert 0 <= xi <= .9
    assert eps >= 0


def test_calibration_float_ids_serializes(tmp_path):
    rng = np.random.default_rng(12)
    weeks = np.tile(np.arange(1, 101), 2)
    promo = rng.binomial(1, .2, 200)
    price = 3. - .5 * promo + rng.normal(0, .1, 200)
    frame = pd.DataFrame({"store": np.repeat([1., 2.], 100), "zone": np.repeat([1, 2], 100),
                          "week": weeks, "promo": promo, "price": price,
                          "log_comp_index": rng.normal(0, .1, 200), "profit": 25.,
                          "log_q": 3. - .35 * (price - 3.) + .2 * promo + rng.normal(0, .2, 200)})
    clean = CleanResult(frame, 123, [1, 2], 0., False, [])
    cal = calibrate(clean, CalibrationConfig())
    cal.save(tmp_path / "calibration.json")
    assert set(cal.alpha_s) == {1, 2}
    assert cal.beta_reference < 0