import numpy as np
from doubleml import DoubleMLData, DoubleMLPLIV, DoubleMLPLR
from sklearn.model_selection import KFold

from ktsim.estimators.base import design, finalize
from ktsim.estimators.gbm import learner
from ktsim.estimators.iv import IV


class DML:
    def __init__(self, pliv=False):
        self.pliv = pliv
        self.name = "M4_pliv" if pliv else "M4_plr"

    def fit(self, df, cal, cfg):
        exog = design(df)
        columns = list(exog)
        data = exog.assign(
            log_q=df.log_q, treatment=df.price - cal.p_bar, instrument=df.cost_shifter
        )
        dml_data = DoubleMLData(
            data, "log_q", "treatment", x_cols=columns, z_cols="instrument" if self.pliv else None
        )
        params = cfg["nuisance_params"]
        common = dict(n_folds=cfg.get("n_folds", 5), draw_sample_splitting=False)
        if self.pliv:
            fit = DoubleMLPLIV(
                dml_data, ml_l=learner(params), ml_m=learner(params), ml_r=learner(params), **common
            )
        else:
            fit = DoubleMLPLR(dml_data, ml_l=learner(params), ml_m=learner(params), **common)
        splits = list(KFold(common["n_folds"], shuffle=True, random_state=20261013).split(data))
        fit.set_sample_splitting(splits)
        fit.fit(n_jobs_cv=1)
        theta = float(fit.coef[0])
        interval = fit.confint().iloc[0].to_numpy() * cal.p_bar
        outcome = learner(params).fit(exog, df.log_q)
        treatment = learner(params).fit(exog, df.price - cal.p_bar)

        def predict(frame, price):
            inputs = design(frame, columns)
            result = outcome.predict(inputs) + theta * (
                np.asarray(price) - cal.p_bar - treatment.predict(inputs)
            )
            return np.exp(result)

        first_stage = IV().fit(df, cal, {}).get("first_stage_F") if self.pliv else None
        return finalize(
            theta * cal.p_bar, float(interval[0]), float(interval[1]), first_stage, predict
        )
