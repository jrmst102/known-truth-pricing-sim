from ktsim.estimators.dml import DML
from ktsim.estimators.gbm import GBM
from ktsim.estimators.iv import IV
from ktsim.estimators.ols import OLS


def get_estimator(name):
    if name == "M1":
        return OLS()
    if name == "M2":
        return GBM()
    if name in {"M3", "M3_cf"}:
        return IV(control_function=name == "M3_cf")
    if name in {"M4_plr", "M4_pliv"}:
        return DML(pliv=name == "M4_pliv")
    raise ValueError(f"Unknown estimator: {name}")
