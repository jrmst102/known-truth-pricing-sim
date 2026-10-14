"""Demand predictions use exp(log prediction) times mean(exp(training residual))."""

import numpy as np
import statsmodels.api as sm

from ktsim.estimators.base import design, finalize, smearing_factor


class OLS:
    name = "M1"

    def fit(self, df, cal, cfg):
        exog = design(df)
        controls = list(exog)
        exog["price_centered"] = df.price - cal.p_bar
        fit = sm.OLS(df.log_q, exog).fit(cov_type=cfg.get("robust_se", "HC1"))
        coefficient = fit.params.price_centered
        interval = fit.conf_int().loc["price_centered"] * cal.p_bar

        smear = smearing_factor(fit.resid)

        def predict(frame, price):
            inputs = design(frame, controls)
            inputs["price_centered"] = np.asarray(price) - cal.p_bar
            return np.exp(fit.predict(inputs)) * smear

        return finalize(
            coefficient * cal.p_bar,
            float(interval.iloc[0]),
            float(interval.iloc[1]),
            predict=predict,
            smearing=smear,
        )
