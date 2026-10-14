"""Within-store, store-grouped DML with cluster-robust variance.

This is not a serial-dependence model; no time-cluster/HAC correction is added
beyond the store-cluster sandwich. Coverage claims stay withheld until the author
sets inference_validated after the dedicated Monte Carlo validation.
Demand = exp(log prediction) * Duan mean(exp(out-of-fold training residual)).
"""

import numpy as np
import pandas as pd
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
        columns = list(dict.fromkeys(columns))
        raw = pd.DataFrame(
            dict(
                log_q=df.log_q,
                treatment=df.price - cal.p_bar,
                instrument=df[cfg.get("instrument", "cost_shifter")],
            )
        )
        means = raw.groupby(df.store).mean()
        within = raw - raw.groupby(df.store).transform("mean")
        data = df[columns].astype(float).join(within).assign(store=df.store)
        dml_data = DoubleMLClusterData(
            data,
            "log_q",
            "treatment",
            cluster_cols="store",
            x_cols=columns,
            z_cols="instrument" if self.pliv else None,
        )
        n_folds = cfg.get("n_folds", 5)
        splits = list(GroupKFold(n_folds).split(data, groups=df.store))
        cluster_splits = [
            [
                ([np.unique(df.store.iloc[train])], [np.unique(df.store.iloc[test])])
                for train, test in splits
            ]
        ]
        params = cfg["nuisance_params"]
        common = dict(n_folds=n_folds, draw_sample_splitting=False, score="partialling out")
        if self.pliv:
            fit = DoubleMLPLIV(
                dml_data, ml_l=learner(params), ml_m=learner(params), ml_r=learner(params), **common
            )
        else:
            fit = DoubleMLPLR(dml_data, ml_l=learner(params), ml_m=learner(params), **common)
        fit.set_sample_splitting(splits, all_smpls_cluster=cluster_splits)
        fit.fit(n_jobs_cv=1, store_predictions=True, store_models=True)
        theta = float(fit.coef[0])
        interval = fit.confint().iloc[0].to_numpy() * cal.p_bar
        treatment_learner = "ml_r" if self.pliv else "ml_m"
        out_l = fit.predictions["ml_l"][:, 0, 0]
        out_d = fit.predictions[treatment_learner][:, 0, 0]
        group_y = df.store.map(means.log_q).to_numpy()
        group_d = df.store.map(means.treatment).to_numpy()
        fitted_log = group_y + out_l + theta * (raw.treatment.to_numpy() - group_d - out_d)
        smear = smearing_factor(df.log_q - fitted_log)
        folds = {}
        for fold, (_, test) in enumerate(splits):
            folds.update({int(store): fold for store in df.store.iloc[test].unique()})
        # Match training rows by stable store/time keys for out-of-fold predictions.
        train_index = pd.MultiIndex.from_frame(df[["store", "t"]])

        def nuisance(name, frame):
            models = fit.models[name]["treatment"][0]
            result = np.mean([model.predict(frame[columns]) for model in models], axis=0)
            positions = train_index.get_indexer(pd.MultiIndex.from_frame(frame[["store", "t"]]))
            seen = positions >= 0
            result[seen] = fit.predictions[name][positions[seen], 0, 0]
            return result

        def predict(frame, price):
            y_mean = frame.store.map(means.log_q).to_numpy()
            d_mean = frame.store.map(means.treatment).to_numpy()
            result = (
                y_mean
                + nuisance("ml_l", frame)
                + theta
                * (np.asarray(price) - cal.p_bar - d_mean - nuisance(treatment_learner, frame))
            )
            return np.exp(result) * smear

        first_stage = None
        if self.pliv:
            # Transformed first stage, instrument residualized by cross-fitted nuisance.
            z_resid = within.instrument.to_numpy() - fit.predictions["ml_m"][:, 0, 0]
            d_resid = within.treatment.to_numpy() - out_d
            first = sm.OLS(d_resid, z_resid[:, None]).fit(
                cov_type="cluster", cov_kwds={"groups": df.store}
            )
            first_stage = float(first.tvalues[0] ** 2)
        status = (
            "available"
            if cfg.get("inference_validated", False)
            else ("withheld: inference not validated")
        )
        result = finalize(
            theta * cal.p_bar,
            float(interval[0]),
            float(interval[1]),
            first_stage,
            predict,
            smearing=smear,
            coverage_status=status,
            fold_assignment=folds,
        )
        result["nuisance_features"] = columns
        result["cluster_variance"] = True
        return result
