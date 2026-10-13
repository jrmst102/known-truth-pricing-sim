import numpy as np
import statsmodels.api as sm
from linearmodels.iv import IV2SLS

from ktsim.estimators.base import design, finalize


class IV:
    def __init__(self, control_function=False):
        self.control_function = control_function
        self.name = "M3_cf" if control_function else "M3"

    def fit(self, df, cal, cfg):
        exog = design(df)
        columns = list(exog)
        treatment = (df.price - cal.p_bar).rename("price_centered")
        instrument = df[[cfg.get("instrument", "cost_shifter")]]
        iv_fit = IV2SLS(df.log_q, exog, treatment, instrument).fit(cov_type="robust")
        first_stage = float(iv_fit.first_stage.diagnostics.loc["price_centered", "f.stat"])
        if self.control_function:
            first_design = exog.join(instrument)
            first = sm.OLS(treatment, first_design).fit()
            full = exog.assign(price_centered=treatment, first_residual=first.resid)
            fit = sm.OLS(df.log_q, full).fit(cov_type="HC1")
            interval = fit.conf_int().loc["price_centered"] * cal.p_bar
        else:
            fit = iv_fit
            interval = fit.conf_int().loc["price_centered"] * cal.p_bar
        params = fit.params

        def predict(frame, price):
            baseline = design(frame, columns).to_numpy() @ params[columns].to_numpy()
            return np.exp(baseline + params.price_centered * (np.asarray(price) - cal.p_bar))

        return finalize(float(params.price_centered * cal.p_bar), float(interval.iloc[0]),
                        float(interval.iloc[1]), first_stage, predict)