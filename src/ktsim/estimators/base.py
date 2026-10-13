from typing import Callable, Protocol, TypedDict

import numpy as np
import pandas as pd

from ktsim.config import Calibration


class Estimate(TypedDict):
    eta_hat: float
    ci_low: float | None
    ci_high: float | None
    first_stage_F: float | None
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


def finalize(eta, low=None, high=None, first_stage=None, predict=None):
    failure = None
    if not np.isfinite(eta) or any(
        value is not None and not np.isfinite(value) for value in (low, high)
    ):
        failure = "nonfinite"
    elif abs(eta) > 10:
        failure = "abs_eta_gt_10"
    return Estimate(
        eta_hat=float(eta) if failure is None else np.nan,
        ci_low=low if failure is None else None,
        ci_high=high if failure is None else None,
        first_stage_F=first_stage,
        converged=failure is None,
        failure_reason=failure,
        predict=predict if failure is None else None,
    )


def failed(reason="nonconvergence"):
    return Estimate(
        eta_hat=np.nan,
        ci_low=None,
        ci_high=None,
        first_stage_F=None,
        converged=False,
        failure_reason=reason,
        predict=None,
    )
