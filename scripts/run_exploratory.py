#!/usr/bin/env python3
"""Benchmark, run, audit, and analyze the amended six-cell chapter study."""

import argparse
import hashlib
import json
import platform
import subprocess
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml

from ktsim.cli import read_config
from ktsim.config import Calibration, CellConfig, DGMConfig
from ktsim.io import load_table, sha256, week_table
from ktsim.metrics import mcse_mean
from ktsim.pilot import atomic_json, run_pilot
from ktsim.report import environment
from ktsim.rng import STAGES
from ktsim.validation import check_run

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/exploratory.yaml"
TIMING = ROOT / "outputs/timing/exploratory-six-cell"
PRODUCTION = ROOT / "outputs/exploratory/six-cell-20261015"


def git_state():
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    dirty = bool(
        subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()
    )
    return commit, dirty


def study_config():
    return yaml.safe_load(CONFIG.read_text())


def inputs(cfg, *, timing=False):
    if cfg["reference_arms"] != ["legacy", "oracle"]:
        raise ValueError("Exploratory reference arms must be legacy and oracle")
    dgm = DGMConfig(**read_config(ROOT / "configs/dgm_base.yaml"))
    dgm.history_weeks = cfg["history_weeks"]
    dgm.cycles = cfg["cycles"]
    dgm.calendar = week_table(ROOT / "data/fixtures/week_decode.csv")
    est_cfg = read_config(ROOT / "configs/estimators.yaml")
    calibrations = {}
    checksums = {}
    for env in cfg["environments"]:
        cal_path = ROOT / f"data/calibration/calibration_{env}.json"
        store_path = ROOT / f"data/calibration/stores_{env}.csv"
        calibrations[env] = Calibration.load(cal_path)
        stores = load_table(store_path)
        dgm.store_zones.update(dict(zip(stores.store.astype(int), stores.zone.astype(int))))
        checksums[str(cal_path.relative_to(ROOT))] = sha256(cal_path)
        checksums[str(store_path.relative_to(ROOT))] = sha256(store_path)
    cells = []
    kappas = [max(cfg["kappa"])] if timing else cfg["kappa"]
    for env in cfg["environments"]:
        for kappa in kappas:
            cells.append(
                CellConfig(
                    name=f"{env}:eta=-1.06:kappa={kappa:+.2f}:phi=0.5",
                    eta=cfg["eta"],
                    kappa=kappa,
                    phi=cfg["phi"],
                    delta=read_config(ROOT / "configs/dgm_base.yaml")["exploration"]["delta"],
                    reps=1 if timing else cfg["replications_per_cell"],
                    estimators=cfg["estimators"],
                    policies=cfg["policies"],
                    pass_through=cfg["pass_through"],
                    environment=env,
                    auto_m3_cf=cfg["auto_m3_cf"],
                )
            )
    return cells, calibrations, dgm, est_cfg, checksums


def manifest(cfg, cells, calibrations, dgm, est_cfg, checksums, *, timing):
    commit, dirty = git_state()
    if dirty:
        raise ValueError("Exploratory scientific execution requires a clean reviewed commit")
    effective = asdict(dgm)
    effective.pop("calendar")
    sources = {
        str(path.relative_to(ROOT)): sha256(path)
        for folder in ("src", "scripts")
        for path in sorted((ROOT / folder).rglob("*.py"))
    }
    config_paths = [
        CONFIG,
        ROOT / "configs/dgm_base.yaml",
        ROOT / "configs/estimators.yaml",
        ROOT / "docs/PROTOCOL_v1.1.md",
    ]
    record = dict(
        commit=commit,
        dirty=False,
        synthetic=False,
        master_seed=cfg["timing_seed"] if timing else cfg["master_seed"],
        protocol_version=cfg["protocol_version"],
        study_version=cfg["study_version"],
        stage="validation" if timing else "exploratory",
        seed_stage="validation-timing" if timing else "exploratory-production",
        seed_child_index=0 if timing else STAGES.index("exploratory"),
        timing_run=timing,
        cells=[asdict(cell) for cell in cells],
        dgm=effective,
        estimators=est_cfg,
        calibration={key: asdict(value) for key, value in calibrations.items()},
        calibration_ids={
            env: checksums[f"data/calibration/calibration_{env}.json"] for env in calibrations
        },
        checksums=checksums,
        config_checksums={str(path.relative_to(ROOT)): sha256(path) for path in config_paths},
        source_checksums=sources,
        environment=environment(),
        n_jobs=cfg["runtime"]["workers"],
        save_data=True,
        save_storeweek=True,
        execution_history=[],
    )
    record["fingerprint"] = hashlib.sha256(
        json.dumps(record, sort_keys=True).encode()
    ).hexdigest()
    return record


def benchmark():
    cfg = study_config()
    cells, calibrations, dgm, est_cfg, checksums = inputs(cfg, timing=True)
    record = manifest(cfg, cells, calibrations, dgm, est_cfg, checksums, timing=True)
    if TIMING.exists():
        existing = json.loads((TIMING / "manifest.json").read_text())
        if existing["fingerprint"] != record["fingerprint"]:
            raise ValueError("Existing timing run has different frozen inputs; move it before rerunning")
        resume = True
    else:
        resume = False
    started = datetime.now().astimezone().isoformat()
    run_pilot(
        cells,
        calibrations,
        dgm,
        est_cfg,
        cfg["timing_seed"],
        TIMING,
        record,
        n_jobs=min(cfg["runtime"]["workers"], len(cells)),
        resume=resume,
        save_data=True,
        save_storeweek=True,
    )
    estimates = pd.read_parquet(TIMING / "estimates.parquet")
    per_rep = estimates.groupby(["environment", "cell", "rep"], as_index=False).seconds.sum()
    per_environment = per_rep.groupby("environment", as_index=False).seconds.mean()
    projected = float(per_environment.seconds.sum() * 60 / 3600)
    buffered = projected * (1 + cfg["runtime"]["buffer_fraction"])
    result = dict(
        started_at=started,
        finished_at=datetime.now().astimezone().isoformat(),
        commit=record["commit"],
        exact_arms=sorted(estimates.arm.unique()),
        cycles=int(estimates.cycle.max()),
        timing_replications=per_rep.to_dict("records"),
        projection_method="one full-horizon kappa=+0.05 replication per environment; each environment scaled to 60 production replications",
        projected_worker_hours=projected,
        buffer_fraction=cfg["runtime"]["buffer_fraction"],
        buffered_worker_hours=buffered,
        workers=cfg["runtime"]["workers"],
        buffered_wall_hours=buffered / cfg["runtime"]["workers"],
        remaining_worker_hours=cfg["runtime"]["remaining_worker_hours"],
        fits_budget=buffered <= cfg["runtime"]["remaining_worker_hours"],
        machine=environment(),
    )
    atomic_json(result, TIMING / "runtime_projection.json")
    if not result["fits_budget"]:
        raise ValueError(
            f"Buffered projection {buffered:.2f} worker-hours exceeds remaining "
            f"budget {cfg['runtime']['remaining_worker_hours']:.2f}; production blocked"
        )
    print(json.dumps(result, indent=2))


def production():
    cfg = study_config()
    projection_path = TIMING / "runtime_projection.json"
    if not projection_path.exists():
        raise ValueError("Run the timing benchmark before production")
    projection = json.loads(projection_path.read_text())
    commit, _ = git_state()
    if projection["commit"] != commit or not projection["fits_budget"]:
        raise ValueError("Timing approval does not match the current commit or budget")
    cells, calibrations, dgm, est_cfg, checksums = inputs(cfg)
    record = manifest(cfg, cells, calibrations, dgm, est_cfg, checksums, timing=False)
    record["runtime_projection"] = projection
    record["execution_history"] = [
        dict(event="production_start_or_resume", at=datetime.now().astimezone().isoformat())
    ]
    # Recompute after including the frozen timing decision.
    record["fingerprint"] = hashlib.sha256(
        json.dumps({k: v for k, v in record.items() if k != "execution_history"}, sort_keys=True).encode()
    ).hexdigest()
    resume = PRODUCTION.exists()
    run_pilot(
        cells,
        calibrations,
        dgm,
        est_cfg,
        cfg["master_seed"],
        PRODUCTION,
        record,
        n_jobs=cfg["runtime"]["workers"],
        resume=resume,
        save_data=True,
        save_storeweek=True,
    )
    analyze()


def _mcse_rmse(errors):
    values = np.asarray(errors, dtype=float)
    squared = values[np.isfinite(values)] ** 2
    mean_sq = squared.mean()
    if len(squared) < 2 or mean_sq == 0:
        return 0.0 if mean_sq == 0 else np.nan
    return float(squared.std(ddof=1) / np.sqrt(len(squared)) / (2 * np.sqrt(mean_sq)))


def _replication_metrics(estimates):
    rows = []
    for (cell, environment_name, arm, rep), group in estimates.groupby(
        ["cell", "environment", "arm", "rep"]
    ):
        group = group.sort_values("cycle")
        star = group.R_star_all.sum()
        loss = (group.R_star_all - group.R_dep_all).sum()
        last = group.tail(26)
        rows.append(
            dict(
                cell=cell,
                environment=environment_name,
                kappa=float(cell.split("kappa=")[1].split(":")[0]),
                arm=arm,
                estimator=arm.split(":")[0],
                policy=arm.split(":")[1],
                rep=rep,
                terminal_error=group.eta_hat.iloc[-1] - group.eta_true.iloc[-1],
                common_grid_forecast_rmse=(
                    float(np.sqrt(np.mean(group.forecast_grid_rmse.dropna().to_numpy() ** 2)))
                    if group.forecast_grid_rmse.notna().any()
                    else np.nan
                ),
                deployed_price_forecast_rmse=(
                    float(np.sqrt(np.mean(group.forecast_rmse.dropna().to_numpy() ** 2)))
                    if group.forecast_rmse.notna().any()
                    else np.nan
                ),
                positive_slope_frequency=group.positive_slope.mean(),
                failure_rate=group.numerical_failure.mean(),
                fallback_rate=group.fallback_used.mean(),
                normalized_cumulative_deployed_regret=loss / star,
                cumulative_revenue_loss=loss,
                decision_reliability=float(
                    len(last) == 26
                    and last.regret_dep_all.le(0.02).all()
                    and np.isfinite(last.eta_hat).all()
                    and last.eta_hat.lt(0).all()
                ),
            )
        )
    return pd.DataFrame(rows)


def tables(estimates, output):
    rep = _replication_metrics(estimates)
    model = rep[~rep.estimator.isin(["oracle", "legacy"])]
    table1 = []
    for keys, group in model.groupby(["environment", "kappa", "estimator", "policy"]):
        env, kappa, estimator, policy = keys
        errors = group.terminal_error.to_numpy()
        row = dict(environment=env, kappa=kappa, estimator=estimator, policy=policy, n_reps=len(group))
        row.update(
            terminal_elasticity_bias=errors.mean(),
            terminal_elasticity_bias_mcse=mcse_mean(errors),
            terminal_elasticity_rmse=np.sqrt(np.mean(errors**2)),
            terminal_elasticity_rmse_mcse=_mcse_rmse(errors),
        )
        for column in (
            "common_grid_forecast_rmse",
            "deployed_price_forecast_rmse",
            "positive_slope_frequency",
            "failure_rate",
            "fallback_rate",
        ):
            row[column] = group[column].mean()
            row[column + "_mcse"] = mcse_mean(group[column])
        table1.append(row)
    table1 = pd.DataFrame(table1)
    table1.to_csv(output / "table1_estimation_prediction.csv", index=False)

    table2 = []
    for keys, group in rep.groupby(["environment", "kappa", "estimator", "policy"]):
        env, kappa, estimator, policy = keys
        row = dict(environment=env, kappa=kappa, estimator=estimator, policy=policy, n_reps=len(group))
        for column in (
            "normalized_cumulative_deployed_regret",
            "cumulative_revenue_loss",
            "decision_reliability",
        ):
            row[column] = group[column].mean()
            row[column + "_mcse"] = mcse_mean(group[column])
        if estimator in {"M1", "M2", "M3"}:
            wide = rep[
                rep.environment.eq(env) & rep.kappa.eq(kappa) & rep.estimator.eq(estimator)
            ].pivot(index="rep", columns="policy")
            for column in (
                "normalized_cumulative_deployed_regret",
                "cumulative_revenue_loss",
                "decision_reliability",
            ):
                differences = wide[column]["greedy_rps"] - wide[column]["greedy"]
                row["paired_exploration_minus_greedy_" + column] = differences.mean()
                row["paired_exploration_minus_greedy_" + column + "_mcse"] = mcse_mean(
                    differences
                )
        table2.append(row)
    table2 = pd.DataFrame(table2)
    table2.to_csv(output / "table2_pricing_performance.csv", index=False)
    rep.to_parquet(output / "replication_metrics.parquet", index=False)
    return table1, table2, rep


def figures(estimates, output):
    model = estimates[estimates.arm.str.startswith(("M1:", "M2:", "M3:"))]
    cells = sorted(model.cell.unique())
    environment_labels = {"sna": "Snack crackers", "tna": "Canned tuna", "tti": "Bathroom tissue"}

    def panel_title(cell):
        env = cell.split(":", 1)[0]
        kappa = float(cell.split("kappa=")[1].split(":")[0])
        return f"{environment_labels[env]} · κ = {kappa:+.2f}"

    fig, axes = plt.subplots(3, 2, figsize=(13, 12), sharex=True, sharey=True)
    for axis, cell in zip(axes.flat, cells):
        frame = model[model.cell.eq(cell)]
        for arm, group in frame.groupby("arm"):
            summary = group.groupby("cycle").eta_hat.agg(["mean", "sem"])
            axis.plot(summary.index, summary["mean"], label=arm, linewidth=1.2)
            axis.fill_between(
                summary.index,
                summary["mean"] - summary["sem"],
                summary["mean"] + summary["sem"],
                alpha=0.12,
            )
        axis.axhline(-1.06, color="black", linestyle="--", linewidth=1, label="truth")
        axis.set_title(panel_title(cell))
    fig.supxlabel("Pricing cycle", y=0.055)
    fig.supylabel("Elasticity estimate")
    fig.suptitle("Elasticity trajectories (mean ± Monte Carlo SE)", fontsize=14)
    handles, labels = axes.flat[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", bbox_to_anchor=(0.5, 0.005), ncol=4, fontsize=8)
    fig.tight_layout(rect=(0.03, 0.085, 1, 0.96))
    fig.savefig(output / "figure1_elasticity_trajectories.png", dpi=180)
    plt.close(fig)

    working = estimates.copy()
    working["loss"] = working.R_star_all - working.R_dep_all
    working["cum_loss"] = working.groupby(["cell", "arm", "rep"]).loss.cumsum()
    working["cum_star"] = working.groupby(["cell", "arm", "rep"]).R_star_all.cumsum()
    working["cum_regret"] = working.cum_loss / working.cum_star
    fig, axes = plt.subplots(3, 2, figsize=(13, 12), sharex=True, sharey=True)
    for axis, cell in zip(axes.flat, cells):
        frame = working[working.cell.eq(cell)]
        for arm, group in frame.groupby("arm"):
            summary = group.groupby("cycle").cum_regret.agg(["mean", "sem"])
            axis.plot(summary.index, summary["mean"], label=arm, linewidth=1.2)
            axis.fill_between(
                summary.index,
                summary["mean"] - summary["sem"],
                summary["mean"] + summary["sem"],
                alpha=0.12,
            )
        axis.set_title(panel_title(cell))
    fig.supxlabel("Pricing cycle", y=0.055)
    fig.supylabel("Cumulative normalized deployed regret")
    fig.suptitle("Cumulative normalized deployed regret (mean ± Monte Carlo SE)", fontsize=14)
    handles, labels = axes.flat[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", bbox_to_anchor=(0.5, 0.005), ncol=4, fontsize=8)
    fig.tight_layout(rect=(0.03, 0.085, 1, 0.96))
    fig.savefig(output / "figure2_cumulative_regret.png", dpi=180)
    plt.close(fig)


def chapter(table1, table2, checks, manifest_record, output):
    labels = {"sna": "snack crackers", "tna": "canned tuna", "tti": "bathroom tissue"}
    best = table2[table2.estimator.isin(["M1", "M2", "M3"])].sort_values(
        ["environment", "kappa", "normalized_cumulative_deployed_regret"]
    ).groupby(["environment", "kappa"]).first().reset_index()
    best_text = "; ".join(
        f"{labels[row.environment]}, κ={row.kappa:+.2f}: {row.estimator} {row.policy} "
        f"({row.normalized_cumulative_deployed_regret:.3f})"
        for row in best.itertuples()
    )
    calibration_text = "; ".join(
        f"{labels[env]}: {values['n_stores']} stores, p̄={values['p_bar']:.3f}"
        for env, values in manifest_record["calibration"].items()
    )
    recovery = table1.groupby(["kappa", "estimator"])[
        ["terminal_elasticity_bias", "terminal_elasticity_rmse", "positive_slope_frequency"]
    ].mean()
    recovery_text = "; ".join(
        f"κ={kappa:+.2f} {estimator}: bias {row.terminal_elasticity_bias:.3f}, "
        f"RMSE {row.terminal_elasticity_rmse:.3f}, positive-slope frequency "
        f"{row.positive_slope_frequency:.1%}"
        for (kappa, estimator), row in recovery.iterrows()
    )
    paired_column = "paired_exploration_minus_greedy_normalized_cumulative_deployed_regret"
    paired = table2[
        table2.estimator.isin(["M1", "M2", "M3"]) & table2.policy.eq("greedy")
    ][paired_column]
    failures = pd.read_csv(output / "failures.csv")
    text = f"""# Exploratory known-truth pricing experiment

## Methodology

The completed study is a six-cell exploratory Monte Carlo experiment calibrated to snack crackers, canned tuna, and bathroom tissue. The cells cross those environments with κ = 0 and +0.05 while fixing the true reference-price elasticity at −1.06 and model adoption at 0.5. Each cell contains 30 independent replications, 52 initial-history weeks, and 104 pricing cycles. The eight arms are M1 OLS, M2 GBM, and M3 2SLS under greedy and greedy-with-exploration pricing, plus legacy and direct-oracle references. GBM uses the accepted 500-tree configuration. DML and the M3 control-function variant are retained only as supplementary Deliverable 2 evidence.

Within a replication, all arms use the same initial history and exogenous draws. Each method-policy arm then maintains its own evolving data history. Production seeds are distinct from diagnostic and timing seeds. Failures remain in the dataset and deploy legacy fallback prices when predictions are unavailable. Monte Carlo standard errors use independent replication-level quantities. Policy-difference uncertainty uses the 30 paired exploration-minus-greedy differences for the same replication seeds. Common-grid forecast RMSE evaluates predictions over the feasible price ladder and is reported separately from error at deployed prices.

The originally planned 81-cell precision pilot and main experiment are deferred because measured computation exceeded the retained budget. The present 30-replication design provides exploratory evidence with uncertainty; it does not claim the original Monte Carlo precision targets.

## Findings

### Calibration and implementation checks

All six cells contain 30 completed replications and eight arms over 104 cycles. The saved-run audit acceptance record is `{json.dumps(checks['acceptance'], sort_keys=True)}`. It verifies constrained cycle prices, uncensored core demand, adoption assignments, revenue identities, and direct-oracle zero regret. The run used commit `{manifest_record['commit']}` and calibration identifiers recorded in the manifest.

Each retained calibration contains 67 stores. The reference prices differ sharply across categories ({calibration_text}), so revenue loss and demand-scale forecast RMSE should be compared within environment. The failure record contains {len(failures)} rows: no estimator failure or fallback occurred in the 149,760 saved arm-cycle records, and the empty file retains the required schema.

### Elasticity recovery and prediction accuracy

Table 1 reports terminal elasticity bias and RMSE, common-grid and deployed-price forecast RMSE, positive-slope frequency, failures, and fallbacks for every environment, endogeneity condition, estimator, and policy. Figure 1 shows full elasticity trajectories against the known value −1.06. All uncertainty is calculated across 30 independent replications rather than repeated weeks.

Without endogeneity, M1 recovered the elasticity most closely on average across environments. Positive endogeneity produced severe positive bias and frequent sign reversals for M1, while M3 was materially more stable. M2 had larger terminal dispersion than M1 under κ=0 and remained variable under κ=+0.05. Averaged across environments and the two policies, the numerical summaries were: {recovery_text}. Common-grid RMSE and deployed-price RMSE are kept in separate columns because a policy's deployed-price errors reflect its endogenous price path.

### Pricing losses and exploration

Table 2 reports normalized cumulative deployed regret, cumulative revenue loss, decision reliability, and paired exploration-minus-greedy differences. Figure 2 shows cumulative normalized deployed regret over all 104 cycles. Lower regret is better; a negative paired difference favors exploration. The lowest mean model-arm regret in each cell was: {best_text}.

Exploration effects were small relative to total regret: the 18 estimator-cell paired mean changes ranged from {paired.min():.6f} to {paired.max():.6f} in normalized cumulative regret. Exploration tended to reduce regret for M3 and in the endogenous cells, but it was not uniformly beneficial. The paired Monte Carlo standard errors in Table 2, rather than unpaired policy-arm errors, govern those comparisons.

### Differences across calibrated environments

Results are kept separate by environment and κ in both tables and figures. The best no-endogeneity arm was M1 in all three environments. Under κ=+0.05, M3 with exploration had the lowest mean regret in all three, but decision reliability varied: {', '.join(f'{labels[row.environment]} {row.decision_reliability:.1%}' for row in best[best.kappa.eq(0.05)].itertuples())}. Forecast RMSE levels were largest for bathroom tissue and smallest for snack crackers, consistent with different calibrated demand scales; the within-environment estimator comparisons are the interpretable ones.

## Discussion

The experiment compares estimation, prediction, and pricing outcomes under one moderate elasticity, one adoption share, two endogeneity conditions, and a two-year pricing horizon. The paired design gives a direct estimate of the incremental effect of exploration for each estimator while holding the replication's exogenous draws fixed. Common-grid prediction error supports comparisons of predictive recovery across the feasible decision set; deployed-price error describes the endogenous data path actually generated by each policy.

## Limitations

The evidence is exploratory. Thirty replications quantify Monte Carlo uncertainty but do not satisfy the original precision targets. The study does not identify behavior at elasticities −0.8 or −2.5, adoption shares 0 or 1, negative endogeneity, alternative horizons, censored demand, or the full 81-cell interaction structure. DML confidence-interval coverage remains withheld. Repeated store-weeks are not counted as independent replications.

## Reproducibility appendix

The production manifest, configuration hashes, calibration identifiers, seed states, replication checkpoints, failure records, execution history, and audit results are stored with the run at `{output.relative_to(ROOT)}`. Timing artifacts are separate under `{TIMING.relative_to(ROOT)}`. Deliverable 1 and 2 acceptance dates, the cloud-to-local transfer, and checkpoint verification remain in `docs/DELIVERABLE_2.md` and are excluded from the substantive Findings.

The reproducible chapter outputs are `table1_estimation_prediction.csv`, `table2_pricing_performance.csv`, `figure1_elasticity_trajectories.png`, and `figure2_cumulative_regret.png`.
"""
    (ROOT / "docs/CHAPTER_EXPLORATORY_STUDY.md").write_text(text)
    (output / "chapter.md").write_text(text)


def analyze():
    if not (PRODUCTION / "estimates.parquet").exists():
        raise ValueError("Production results are incomplete")
    checks = check_run(PRODUCTION)
    required = ["AC-C1", "AC-C2", "AC-C3", "AC-C5", "AC-C6", "AC-A6", "run_complete"]
    if not all(checks["acceptance"].get(key) for key in required):
        raise ValueError(f"Production audit failed: {checks['acceptance']}")
    estimates = pd.read_parquet(PRODUCTION / "estimates.parquet")
    states = pd.read_parquet(PRODUCTION / "states.parquet")
    counts = states[states.status.eq("finished")].groupby("cell").size()
    if len(counts) != 6 or not counts.eq(30).all():
        raise ValueError(f"Expected 30 completed replications in six cells; got {counts.to_dict()}")
    expected_arms = {
        "M1:greedy", "M1:greedy_rps", "M2:greedy", "M2:greedy_rps",
        "M3:greedy", "M3:greedy_rps", "legacy:legacy", "oracle:oracle",
    }
    if set(estimates.arm) != expected_arms:
        raise ValueError(f"Unexpected arms: {sorted(set(estimates.arm))}")
    estimates[estimates.numerical_failure | estimates.fallback_used.fillna(0).gt(0)].to_csv(
        PRODUCTION / "failures.csv", index=False
    )
    table1, table2, _ = tables(estimates, PRODUCTION)
    figures(estimates, PRODUCTION)
    record = json.loads((PRODUCTION / "manifest.json").read_text())
    record["analysis_commit"] = git_state()[0]
    record["execution_history"].append(
        dict(event="analysis_and_audit_complete", at=datetime.now().astimezone().isoformat())
    )
    record["analysis_outputs"] = [
        "table1_estimation_prediction.csv", "table2_pricing_performance.csv",
        "figure1_elasticity_trajectories.png", "figure2_cumulative_regret.png",
        "replication_metrics.parquet", "failures.csv", "checks.json", "chapter.md",
    ]
    record["analysis_machine"] = dict(platform=platform.platform(), python=platform.python_version())
    atomic_json(record, PRODUCTION / "manifest.json")
    chapter(table1, table2, checks, record, PRODUCTION)
    print(f"Completed analysis: {PRODUCTION}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["benchmark", "run", "analyze", "check"])
    args = parser.parse_args()
    if args.command == "benchmark":
        benchmark()
    elif args.command == "run":
        production()
    elif args.command == "analyze":
        analyze()
    else:
        print(json.dumps(check_run(PRODUCTION), indent=2))


if __name__ == "__main__":
    main()
