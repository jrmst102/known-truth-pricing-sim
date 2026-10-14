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


def revenue_summary(frame, suffix="all", kind="dep"):
    star = frame[f"R_star_{suffix}"].sum(min_count=1)
    loss = (frame[f"R_star_{suffix}"] - frame[f"R_{kind}_{suffix}"]).sum(min_count=1)
    return {"cum_loss": loss, "norm_cum_regret": loss / star}


def reliability(frame, tau=0.02, window=26):
    last = frame.sort_values("cycle").tail(window)
    complete = len(last) == window and last.cycle.nunique() == window
    regret = complete and bool((last.regret_dep_all <= tau).all())
    sign = complete and bool((np.isfinite(last.eta_hat) & (last.eta_hat < 0)).all())
    return dict(reliable_regret=regret, reliable_sign=sign, reliable=regret and sign)


def replication_measures(estimates, reliability_cfg=None):
    cfg = reliability_cfg or {"tau": 0.02, "window": 26}
    rows = []
    for (cell, arm, rep), group in estimates.groupby(["cell", "arm", "rep"]):
        final = group.sort_values("cycle").iloc[-1]
        row = dict(
            cell=cell,
            arm=arm,
            rep=rep,
            terminal_cycle=int(final.cycle),
            terminal_error=final.eta_hat - final.eta_true,
        )
        for suffix in ("all", "model"):
            for kind in ("dep", "rec"):
                measures = revenue_summary(group, suffix, kind)
                for name, value in measures.items():
                    row[f"{name}{'_rec' if kind == 'rec' else ''}_{suffix}"] = value
        row.update(reliability(group, **cfg))
        for source, target in [
            ("fallback_used", "fallback_rate"),
            ("extreme_estimate", "extreme_rate"),
            ("positive_slope", "positive_slope_rate"),
            ("numerical_failure", "failure_share"),
            ("censored_share", "censored_share"),
            ("forecast_mape", "forecast_mape"),
        ]:
            row[target] = group[source].mean()
        row["forecast_rmse"] = np.sqrt(np.mean(group.forecast_rmse**2))
        row["seconds"] = group.seconds.sum()
        rows.append(row)
    return pd.DataFrame(rows)


def performance(
    estimates: pd.DataFrame, truth: dict | None = None, *, stage="validation", reliability_cfg=None
) -> pd.DataFrame:
    rows = []
    rep_measures = replication_measures(estimates, reliability_cfg)
    for (run_id, cell, arm), group in estimates.groupby(["run_id", "cell", "arm"], dropna=False):
        eta = group.eta_true.iloc[0] if truth is None else truth.get(cell, group.eta_true.iloc[0])
        status = (
            "withheld: inference not validated"
            if arm.startswith("M4") and group.coverage_status.str.startswith("withheld").any()
            else "available"
        )
        at = group[group.cycle.eq(group.cycle.max())]

        def emit(checkpoint, measure, values, mcse=mcse_mean, transform=None):
            values = finite(values)
            n_estimated = int(np.isfinite(at.eta_hat).sum())
            intervals = (
                np.isfinite(at.eta_hat)
                & np.isfinite(at.ci_low.astype(float))
                & np.isfinite(at.ci_high.astype(float))
            )
            value = (
                (np.mean(values) if transform is None else transform(values))
                if len(values)
                else np.nan
            )
            withheld = measure == "coverage" and status.startswith("withheld")
            rows.append(
                dict(
                    run_id=run_id,
                    cell=cell,
                    arm=arm,
                    stage=stage,
                    cycle_or_horizon=checkpoint,
                    measure=measure,
                    estimate=np.nan if withheld else float(value),
                    mcse=np.nan if withheld or not len(values) else float(mcse(values)),
                    n_reps=len(values),
                    n_total=len(at),
                    n_estimated=n_estimated,
                    n_with_interval=int(intervals.sum()),
                    coverage_status=status,
                    denominator="n_with_interval"
                    if measure == "coverage"
                    else "n_estimated"
                    if measure in {"bias", "empirical_se", "rmse"}
                    else "n_total",
                )
            )

        for cycle in (26, 52, 104):
            at = group[group.cycle.eq(cycle)]
            if at.empty:
                continue
            values = at.eta_hat.to_numpy(dtype=float)
            emit(cycle, "bias", values - eta)
            emit(
                cycle,
                "empirical_se",
                values,
                mcse_empse,
                lambda v: np.std(v, ddof=1) if len(v) > 1 else np.nan,
            )
            emit(
                cycle,
                "rmse",
                values - eta,
                lambda v: mcse_mean(v**2) / (2 * np.sqrt(np.mean(v**2))) if np.mean(v**2) else 0,
                lambda v: np.sqrt(np.mean(v**2)),
            )
            valid = at[
                np.isfinite(at.eta_hat)
                & np.isfinite(at.ci_low.astype(float))
                & np.isfinite(at.ci_high.astype(float))
            ]
            emit(cycle, "coverage", (valid.ci_low <= eta) & (valid.ci_high >= eta), mcse_coverage)
        at = group[group.cycle.eq(group.cycle.max())]
        reps = rep_measures[rep_measures.cell.eq(cell) & rep_measures.arm.eq(arm)]
        for column in reps.columns.difference(["cell", "arm", "rep", "terminal_cycle"]):
            emit("horizon", column, reps[column])
    return pd.DataFrame(rows)
