import numpy as np
import pandas as pd


def finite(values):
    values = np.asarray(values, dtype=float)
    return values[np.isfinite(values)]


def mcse_mean(values):
    values = finite(values)
    return float(np.std(values, ddof=1) / np.sqrt(len(values))) if len(values) > 1 else np.nan


def mcse_bias(estimates, truth=0.):
    return mcse_mean(np.asarray(estimates) - truth)


def mcse_empse(estimates):
    values = finite(estimates)
    return float(np.std(values, ddof=1) / np.sqrt(2 * (len(values) - 1))) if len(values) > 1 else np.nan


def mcse_mse(estimates, truth=0.):
    return mcse_mean((np.asarray(estimates) - truth)**2)


def mcse_coverage(covered):
    values = finite(covered)
    if not len(values):
        return np.nan
    rate = np.mean(values)
    return float(np.sqrt(rate * (1 - rate) / len(values)))


def performance(estimates: pd.DataFrame, truth: dict | None = None) -> pd.DataFrame:
    rows = []
    for (run_id, cell, arm), group in estimates.groupby(["run_id", "cell", "arm"], dropna=False):
        eta = group.eta_true.iloc[0] if truth is None else truth.get(cell, group.eta_true.iloc[0])

        def emit(checkpoint, measure, values, mcse=mcse_mean, transform=None):
            values = finite(values)
            if not len(values):
                return
            estimate = np.mean(values) if transform is None else transform(values)
            rows.append(dict(run_id=run_id, cell=cell, arm=arm, cycle_or_horizon=checkpoint,
                             measure=measure, estimate=float(estimate), mcse=float(mcse(values)),
                             n_reps=len(values)))

        if not arm.startswith("data:"):
            for week in (78, 104, 156):
                at = group[group.week.eq(week)]
                if at.empty:
                    continue
                values = at.eta_hat.to_numpy(dtype=float)
                emit(week, "bias", values - eta)
                emit(week, "empirical_se", values, mcse_empse,
                     lambda values: np.std(values, ddof=1) if len(values) > 1 else np.nan)
                errors = values - eta
                emit(week, "rmse", errors,
                     lambda errors: mcse_mean(errors**2) / (2 * np.sqrt(np.mean(errors**2)))
                     if np.mean(errors**2) > 0 else 0., lambda errors: np.sqrt(np.mean(errors**2)))
                valid = at[at.ci_low.notna() & at.ci_high.notna()]
                emit(week, "coverage", (valid.ci_low <= eta) & (valid.ci_high >= eta), mcse_coverage)
                emit(week, "sign_flip", at.loc[at.converged, "sign_flip"], mcse_coverage)
                emit(week, "failure_share", ~at.converged, mcse_coverage)
        by_rep = group.groupby("rep")
        for column in ("regret_rec", "regret_dep", "forecast_mape", "censored_share"):
            emit("horizon", column, by_rep[column].mean())
        emit("horizon", "forecast_rmse", by_rep.forecast_rmse.apply(
            lambda values: np.sqrt(np.mean(values**2))))
        emit("horizon", "cumulative_regret", by_rep.regret_dep.sum())
        final = group[group.cycle.eq(group.cycle.max())]
        emit("horizon", "price_sd_26", final.price_sd_26)
        if not arm.startswith("data:"):
            emit("horizon", "failure_share", by_rep.converged.apply(lambda values: (~values).mean()))
            last = group[group.cycle > group.cycle.max() - 26]
            if group.cycle.max() >= 26:
                emit("horizon", "decision_reliability", last.groupby("rep").regret_rec.apply(
                    lambda values: bool((values <= 2.).all())), mcse_coverage)
        emit("horizon", "seconds", by_rep.seconds.sum())
    return pd.DataFrame(rows, columns=["run_id", "cell", "arm", "cycle_or_horizon", "measure",
                                       "estimate", "mcse", "n_reps"])