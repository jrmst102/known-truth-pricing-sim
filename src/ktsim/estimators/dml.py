"""Within-store DML, grouped folds, store-cluster variance and cross-fitted prediction.

Cluster variance permits within-store dependence but does not model serial dynamics;
finite-panel inference is withheld until the author enables validated coverage.
Demand = exp(log prediction) * mean(exp(out-of-fold training residuals)).
"""

import hashlib
import json

import numpy as np
import statsmodels.api as sm
from doubleml import DoubleMLClusterData, DoubleMLPLIV, DoubleMLPLR
from sklearn.model_selection import GroupKFold

from ktsim.estimators.base import control_columns, finalize, smearing_factor
from ktsim.estimators.gbm import learner


class DML:
    def __init__(self, pliv=False):
        self.pliv = pliv
        self.name = "M4_pliv" if pliv else "M4_plr"

    def fit(self, df, cal, cfg):
        df = df.reset_index(drop=True)
        columns = [*control_columns(df), "week_of_year"]
        exog = df[columns].astype(float)
        raw = df.assign(
            treatment=df.price - cal.p_bar, instrument=df[cfg.get("instrument", "cost_shifter")]
        )
        means = raw.groupby("store")[["log_q", "treatment", "instrument"]].mean()
        transformed = raw[["log_q", "treatment", "instrument"]] - raw.groupby("store")[
            ["log_q", "treatment", "instrument"]
        ].transform("mean")
        data = exog.join(transformed).assign(store=df.store)
        dml_data = DoubleMLClusterData(
            data,
            "log_q",
            "treatment",
            cluster_cols="store",
            x_cols=columns,
            z_cols="instrument" if self.pliv else None,
        )
        params = cfg["nuisance_params"]
        common = dict(
            n_folds=cfg.get("n_folds", 5), draw_sample_splitting=False, score="partialling out"
        )
        if self.pliv:
            fit = DoubleMLPLIV(
                dml_data, ml_l=learner(params), ml_m=learner(params), ml_r=learner(params), **common
            )
        else:
            fit = DoubleMLPLR(dml_data, ml_l=learner(params), ml_m=learner(params), **common)
        splits = list(GroupKFold(common["n_folds"]).split(data, groups=df.store))
        cluster_splits = [
            ([df.store.iloc[a].unique()], [df.store.iloc[b].unique()]) for a, b in splits
        ]
        fit.set_sample_splitting(splits, [cluster_splits])
        fit.fit(n_jobs_cv=1, store_models=True)
        theta = float(fit.coef[0])
        interval = fit.confint().iloc[0].to_numpy() * cal.p_bar
        treatment_key = "ml_r" if self.pliv else "ml_m"
        out_y = fit.predictions["ml_l"][:, 0, 0]
        out_d = fit.predictions[treatment_key][:, 0, 0]
        residual = (
            transformed.log_q.to_numpy()
            - out_y
            - theta * (transformed.treatment.to_numpy() - out_d)
        )
        smear = smearing_factor(residual)

        def nuisance(key, inputs):
            return np.mean(
                [model.predict(inputs) for model in fit.models[key]["treatment"][0]], axis=0
            )

        def predict(frame, price):
            inputs = frame[columns].astype(float)
            # Restore the training-window store means for level forecasts.
            baseline = frame.store.map(means.log_q).to_numpy()
            centered_price = np.asarray(price) - cal.p_bar - frame.store.map(means.treatment)
            if frame.equals(df):
                yhat, dhat = out_y, out_d
            else:
                yhat, dhat = nuisance("ml_l", inputs), nuisance(treatment_key, inputs)
            return np.exp(baseline + yhat + theta * (centered_price - dhat)) * smear

        first_stage = None
        if self.pliv:
            zres = transformed.instrument.to_numpy() - fit.predictions["ml_m"][:, 0, 0]
            first = sm.OLS(transformed.treatment.to_numpy() - out_d, zres[:, None]).fit(
                cov_type="cluster", cov_kwds={"groups": df.store}
            )
            first_stage = float(first.tvalues[0] ** 2)
        result = finalize(
            theta * cal.p_bar,
            float(interval[0]),
            float(interval[1]),
            first_stage,
            predict,
            smearing=smear,
        )
        assignment = {
            int(store): fold
            for fold, (_, test) in enumerate(splits)
            for store in df.store.iloc[test].unique()
        }
        result.update(
            fold_assignment=assignment,
            fold_hash=hashlib.sha256(json.dumps(assignment, sort_keys=True).encode()).hexdigest(),
            nuisance_features=columns,
            variance_method="cluster:store",
            coverage_status=(
                "validated"
                if cfg.get("inference_validated", False)
                else "withheld: inference not validated"
            ),
        )
        return result
