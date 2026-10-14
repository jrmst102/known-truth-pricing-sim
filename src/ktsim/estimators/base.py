from typing import Callable, Protocol, TypedDict

import numpy as np
import pandas as pd

from ktsim.config import Calibration


class Estimate(TypedDict):
    eta_hat: float
    ci_low: float | None
    ci_high: float | None
    first_stage_F: float | None
    numerical_failure: bool
    predictions_unavailable: bool
    extreme_estimate: bool
    positive_slope: bool
    smearing_factor: float
    converged: bool
    failure_reason: str | None
    predict: Callable[[pd.DataFrame, np.ndarray], np.ndarray] | None


class Estimator(Protocol):
    name: str

    def fit(self, df: pd.DataFrame, cal: Calibration, cfg: dict) -> Estimate: ...


def control_columns(frame):
    return [
        column
        for column in frame
        if column in {"promo", "log_comp_index"} or column.startswith(("holiday_", "sin_", "cos_"))
    ]


def design(frame, columns=None):
    result = pd.concat(
        [
            frame[control_columns(frame)].astype(float),
            pd.get_dummies(frame.store.astype(int), prefix="store", dtype=float),
        ],
        axis=1,
    )
    if columns is None:
        result = result.loc[:, result.ne(0).any()]
    else:
        result = result.reindex(columns=columns, fill_value=0.0)
    return result


def smearing_factor(residuals):
    return float(np.mean(np.exp(np.asarray(residuals))))


def finalize(eta, low=None, high=None, first_stage=None, predict=None, smearing=1.0):
    finite = bool(np.isfinite(eta))
    interval = finite and all(v is not None and np.isfinite(v) for v in (low, high))
    return Estimate(
        eta_hat=float(eta) if finite else np.nan,
        ci_low=float(low) if interval else None,
        ci_high=float(high) if interval else None,
        first_stage_F=first_stage,
        converged=finite,
        failure_reason=None if finite else "nonfinite",
        predict=predict,
        numerical_failure=not finite,
        predictions_unavailable=predict is None,
        extreme_estimate=finite and abs(eta) > 10,
        positive_slope=finite and eta > 0,
        smearing_factor=smearing,
    )


def failed(reason="nonconvergence"):
    result = finalize(np.nan, smearing=np.nan)
    result["failure_reason"] = reason
    return result
