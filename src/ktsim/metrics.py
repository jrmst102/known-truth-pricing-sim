import numpy as np
import pandas as pd


def finite(values):
    values = np.asarray(values, dtype=float)
    return values[np.isfinite(values)]


def mcse_mean(values):
    values = finite(values)
    return float(np.std(values, ddof=1) / np.sqrt(len(values))) if len(values) > 1 else np.nan


def mcse_bias(estimates, truth=0.0):
    return mcse_mean(np.asarray(estimates) - truth)


def mcse_empse(estimates):
    values = finite(estimates)
    return (
        float(np.std(values, ddof=1) / np.sqrt(2 * (len(values) - 1)))
        if len(values) > 1
        else np.nan
    )


def mcse_mse(estimates, truth=0.0):
    return mcse_mean((np.asarray(estimates) - truth) ** 2)


def mcse_coverage(covered):
    values = finite(covered)
    if not len(values):
        return np.nan
    rate = np.mean(values)
    return float(np.sqrt(rate * (1 - rate) / len(values)))


def replication_summary(estimates, reliability=None):
    reliability = reliability or {"tau": 0.02, "window": 26}
    rows = []
    for (cell, arm, rep), group in estimates.groupby(["cell", "arm", "rep"]):
        group = group.sort_values("cycle")
        row = dict(
            cell=cell,
            arm=arm,
            rep=rep,
            terminal_error=group.eta_hat.iloc[-1] - group.eta_true.iloc[-1],
        )
        for suffix in ("all", "model"):
            for kind in ("dep", "rec"):
                star = group[f"R_star_{suffix}"].sum(min_count=1)
                loss = (group[f"R_star_{suffix}"] - group[f"R_{kind}_{suffix}"]).sum(min_count=1)
                ending = "" if kind == "dep" else "_rec"
                row[f"cum_loss_{suffix}{ending}"] = loss
                row[f"norm_cum_regret_{suffix}{ending}"] = loss / star if star > 0 else np.nan
        last = group.tail(reliability["window"])
        complete = len(last) == reliability["window"]
        row["reliable_regret"] = (
            float(complete and last.regret_dep_all.le(reliability["tau"]).all())
            if complete
            else np.nan
        )
        row["reliable_sign"] = (
            float(complete and np.isfinite(last.eta_hat).all() and last.eta_hat.lt(0).all())
            if complete
            else np.nan
        )
        row["reliable"] = (
            float(row["reliable_regret"] == 1 and row["reliable_sign"] == 1) if complete else np.nan
        )
        for measure, column in (
            ("fallback_rate", "fallback_used"),
            ("extreme_rate", "extreme_estimate"),
            ("positive_slope_rate", "positive_slope"),
            ("failure_share", "numerical_failure"),
            ("forecast_mape", "forecast_mape"),
            ("censored_share", "censored_share"),
        ):
            row[measure] = group[column].mean()
        row["forecast_rmse"] = np.sqrt(np.mean(group.forecast_rmse**2))
        row["seconds"] = group.seconds.sum()
        row["price_sd_26"] = group.price_sd_26.iloc[-1]
        rows.append(row)
    return pd.DataFrame(rows)


def performance(estimates: pd.DataFrame, truth=None, *, reliability=None, stage="validation"):
    rows = []
    horizons = replication_summary(estimates, reliability)
    for (run_id, cell, arm), group in estimates.groupby(["run_id", "cell", "arm"], dropna=False):
        eta = group.eta_true.iloc[0] if truth is None else truth.get(cell, group.eta_true.iloc[0])
        status = group.coverage_status.iloc[0]

        def emit(checkpoint, measure, values, at, mcse=mcse_mean, transform=None):
            values = finite(values)
            n_total = len(at)
            n_estimated = int(np.isfinite(at.eta_hat).sum())
            n_interval = int(
                (np.isfinite(at.eta_hat) & np.isfinite(at.ci_low) & np.isfinite(at.ci_high)).sum()
            )
            estimate = (
                (np.mean(values) if transform is None else transform(values))
                if len(values)
                else np.nan
            )
            if measure == "coverage" and status.startswith("withheld"):
                estimate = np.nan
                values = np.array([])
            rows.append(
                dict(
                    run_id=run_id,
                    cell=cell,
                    arm=arm,
                    stage=stage,
                    cycle_or_horizon=checkpoint,
                    measure=measure,
                    estimate=float(estimate),
                    mcse=float(mcse(values)),
                    n_reps=len(values),
                    n_total=n_total,
                    n_estimated=n_estimated,
                    n_with_interval=n_interval,
                    coverage_status=status,
                )
            )

        if not arm.startswith(("oracle:", "legacy:", "data:")):
            for week in (78, 104, 156):
                at = group[group.week.eq(week)]
                if at.empty:
                    continue
                values = at.eta_hat.to_numpy(dtype=float)
                emit(week, "bias", values - eta, at)
                emit(
                    week,
                    "empirical_se",
                    values,
                    at,
                    mcse_empse,
                    lambda v: np.std(v, ddof=1) if len(v) > 1 else np.nan,
                )
                emit(
                    week,
                    "rmse",
                    values - eta,
                    at,
                    lambda v: mcse_mean(v**2) / (2 * np.sqrt(np.mean(v**2)))
                    if np.mean(v**2) > 0
                    else 0.0,
                    lambda v: np.sqrt(np.mean(v**2)),
                )
                valid = at[
                    np.isfinite(at.eta_hat) & np.isfinite(at.ci_low) & np.isfinite(at.ci_high)
                ]
                emit(
                    week,
                    "coverage",
                    (valid.ci_low <= eta) & (valid.ci_high >= eta),
                    at,
                    mcse_coverage,
                )
        horizon = horizons[horizons.cell.eq(cell) & horizons.arm.eq(arm)]
        final = group[group.cycle.eq(group.cycle.max())]
        for column in horizon.columns.difference(["cell", "arm", "rep", "terminal_error"]):
            emit("horizon", column, horizon[column], final)
    return pd.DataFrame(rows)
