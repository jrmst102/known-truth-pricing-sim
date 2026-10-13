import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor

from ktsim.estimators.base import control_columns, finalize


def learner(params):
    return LGBMRegressor(
        **params,
        verbosity=-1,
        n_jobs=1,
        random_state=20261013,
        deterministic=True,
        force_col_wise=True,
    )


class GBM:
    name = "M2"

    def fit(self, df, cal, cfg):
        columns = ["price", "week_of_year", "store", *control_columns(df)]
        categories = sorted(df.store.unique())

        def features(frame, price):
            inputs = frame.assign(price=price)[columns].copy()
            inputs["store"] = pd.Categorical(inputs.store, categories=categories)
            return inputs

        params = {
            key: cfg[key]
            for key in ("n_estimators", "learning_rate", "num_leaves", "min_child_samples")
        }
        model = learner(params)
        model.fit(features(df, df.price), df.log_q, categorical_feature=["store"])
        last = df[df.t > df.t.max() - cfg.get("fd_window_weeks", 4)]
        step = cfg.get("fd_step", 0.01)
        upper = model.predict(features(last, cal.p_bar * (1 + step)))
        lower = model.predict(features(last, cal.p_bar * (1 - step)))
        eta = float(np.mean(upper - lower) / (np.log1p(step) - np.log1p(-step)))

        def predict(frame, price):
            return np.exp(model.predict(features(frame, price)))

        return finalize(eta, predict=predict)
