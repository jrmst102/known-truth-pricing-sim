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

from ktsim.config import Calibration, CellConfig, DGMConfig
from ktsim.io import load_table, sha256, week_table
from ktsim.metrics import mcse_mean, performance, replication_summary
from ktsim.report import environment
from ktsim.rng import STAGES

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
    from ktsim.cli import read_config
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
    from ktsim.pilot import atomic_json, run_pilot
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
    from ktsim.pilot import run_pilot
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
    # Use the same definitions as performance.csv; reference truth placeholders
    # are not estimates and cannot satisfy an estimated-sign criterion.
    rep = replication_summary(estimates).rename(columns={
        "forecast_grid_rmse": "common_grid_forecast_rmse",
        "forecast_rmse": "deployed_price_forecast_rmse",
        "positive_slope_rate": "positive_slope_frequency",
        "failure_share": "failure_rate",
        "norm_cum_regret_all": "normalized_cumulative_deployed_regret",
        "cum_loss_all": "cumulative_revenue_loss",
        "reliable": "decision_reliability",
        "reliable_regret": "regret_reliability",
    })
    metadata = estimates[["cell", "environment"]].drop_duplicates()
    rep = rep.merge(metadata, on="cell", validate="many_to_one")
    rep["kappa"] = rep.cell.str.extract(r"kappa=([^:]+)")[0].astype(float)
    rep["estimator"] = rep.arm.str.split(":").str[0]
    rep["policy"] = rep.arm.str.split(":").str[1]
    return rep[[
        "cell", "environment", "kappa", "arm", "estimator", "policy", "rep",
        "terminal_error", "common_grid_forecast_rmse", "deployed_price_forecast_rmse",
        "positive_slope_frequency", "failure_rate", "fallback_rate",
        "normalized_cumulative_deployed_regret", "cumulative_revenue_loss",
        "decision_reliability", "regret_reliability",
    ]]


def paired_comparisons(rep):
    """Within-cell differences, paired by replication, in percentage points."""
    rows = []
    for (cell, env, kappa), group in rep.groupby(["cell", "environment", "kappa"]):
        wide = group.pivot(index="rep", columns="arm",
                           values="normalized_cumulative_deployed_regret")
        model_arms = sorted(a for a in wide if a.startswith(("M1:", "M2:", "M3:")))
        contrasts = [(arm, "legacy:legacy") for arm in model_arms]
        contrasts += [(f"M3:{policy}", f"M1:{policy}")
                      for policy in ("greedy", "greedy_rps")]
        for treatment, comparator in contrasts:
            paired = wide[[treatment, comparator]]
            if paired.isna().any().any():
                raise ValueError(f"Incomplete paired outcomes: {cell}, {treatment}, {comparator}")
            differences = 100 * (paired[treatment] - paired[comparator])
            rows.append(dict(
                cell=cell, environment=env, kappa=kappa,
                treatment_arm=treatment, comparator_arm=comparator,
                n_pairs=len(differences),
                mean_regret_difference_pp=differences.mean(),
                mcse_pp=mcse_mean(differences),
            ))
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
            "regret_reliability",
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
    paired_comparisons(rep).to_csv(output / "table3_paired_comparisons.csv", index=False)
    rep.to_parquet(output / "replication_metrics.parquet", index=False)
    return table1, table2, rep


ARM_LABELS = {
    "M1:greedy": "OLS: greedy", "M1:greedy_rps": "OLS: exploration",
    "M2:greedy": "GBM: greedy", "M2:greedy_rps": "GBM: exploration",
    "M3:greedy": "IV: greedy", "M3:greedy_rps": "IV: exploration",
    "legacy:legacy": "Legacy",
    "oracle:oracle": "Oracle recommendation + deployment adjustments",
}


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
            axis.plot(summary.index, summary["mean"], label=ARM_LABELS[arm], linewidth=1.2,
                      linestyle="--" if arm.endswith("greedy_rps") else "-")
            axis.fill_between(
                summary.index,
                summary["mean"] - summary["sem"],
                summary["mean"] + summary["sem"],
                alpha=0.12,
            )
        axis.axhline(-1.06, color="black", linestyle="--", linewidth=1, label="True reference-price elasticity")
        axis.set_title(panel_title(cell))
    fig.supxlabel("Pricing cycle", y=0.055)
    fig.supylabel("Elasticity estimate")
    fig.suptitle("Elasticity trajectories (mean ± Monte Carlo SE)", fontsize=14)
    handles, labels = axes.flat[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", bbox_to_anchor=(0.5, 0.005), ncol=4, fontsize=8)
    fig.tight_layout(rect=(0.03, 0.085, 1, 0.96))
    fig.savefig(output / "figure1_elasticity_trajectories.png", dpi=180)
    plt.close(fig)

    working = estimates.sort_values(["cell", "arm", "rep", "cycle"]).copy()
    working["loss"] = working.R_star_all - working.R_dep_all
    working["cum_loss"] = working.groupby(["cell", "arm", "rep"]).loss.cumsum()
    working["cum_star"] = working.groupby(["cell", "arm", "rep"]).R_star_all.cumsum()
    working["cum_regret"] = 100 * working.cum_loss / working.cum_star
    fig, axes = plt.subplots(3, 2, figsize=(13, 12), sharex=True, sharey=True)
    for axis, cell in zip(axes.flat, cells):
        frame = working[working.cell.eq(cell)]
        for arm, group in frame.groupby("arm"):
            summary = group.groupby("cycle").cum_regret.agg(["mean", "sem"])
            axis.plot(summary.index, summary["mean"], label=ARM_LABELS[arm], linewidth=1.2,
                      linestyle="--" if arm.endswith("greedy_rps") else "-")
            axis.fill_between(
                summary.index,
                summary["mean"] - summary["sem"],
                summary["mean"] + summary["sem"],
                alpha=0.12,
            )
        axis.axhline(0, color="black", linestyle=":", linewidth=1,
                     label="Constrained oracle benchmark")
        axis.set_title(panel_title(cell))
    fig.supxlabel("Pricing cycle", y=0.055)
    fig.supylabel("Cumulative normalized deployed regret (%)")
    fig.suptitle("Cumulative normalized deployed regret (mean ± Monte Carlo SE)", fontsize=14)
    handles, labels = axes.flat[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", bbox_to_anchor=(0.5, 0.005), ncol=3, fontsize=8)
    fig.tight_layout(rect=(0.03, 0.105, 1, 0.96))
    fig.savefig(output / "figure2_cumulative_regret.png", dpi=180)
    plt.close(fig)


def chapter(table1, table2, checks, manifest_record, output):
    labels = {"sna": "Snack crackers", "tna": "Canned tuna", "tti": "Bathroom tissue"}
    paired = pd.read_csv(output / "table3_paired_comparisons.csv")
    selected = paired[
        (paired.kappa.eq(0) & paired.treatment_arm.eq("M1:greedy")
         & paired.comparator_arm.eq("legacy:legacy"))
        | (paired.kappa.eq(0.05) & paired.treatment_arm.eq("M3:greedy")
           & paired.comparator_arm.eq("M1:greedy"))
        | (paired.kappa.eq(0.05) & paired.treatment_arm.eq("M3:greedy_rps")
           & paired.comparator_arm.eq("legacy:legacy"))
    ].sort_values(["kappa", "treatment_arm", "environment"])
    paired_rows = "\n".join(
        f"| {labels[r.environment]} | {r.kappa:.2f} | {ARM_LABELS[r.treatment_arm]} minus "
        f"{ARM_LABELS[r.comparator_arm]} | {r.mean_regret_difference_pp:+.4f} | {r.mcse_pp:.4f} |"
        for r in selected.itertuples()
    )
    endogenous = table2[table2.kappa.eq(0.05)]
    regret_rows = []
    for env in labels:
        g = endogenous[endogenous.environment.eq(env)]
        def value(estimator, policy, column):
            return g.loc[g.estimator.eq(estimator) & g.policy.eq(policy), column].iloc[0]
        regret_rows.append(
            f"| {labels[env]} | {100 * value('M1', 'greedy', 'normalized_cumulative_deployed_regret'):.3f} | "
            f"{100 * value('M3', 'greedy_rps', 'normalized_cumulative_deployed_regret'):.3f} | "
            f"{100 * value('legacy', 'legacy', 'normalized_cumulative_deployed_regret'):.3f} | "
            f"{100 * value('M3', 'greedy_rps', 'decision_reliability'):.1f} |"
        )
    regret_rows = "\n".join(regret_rows)
    exploration = table2[table2.estimator.isin(["M1", "M2", "M3"]) & table2.policy.eq("greedy")][
        "paired_exploration_minus_greedy_normalized_cumulative_deployed_regret"
    ] * 100
    tuna = table1[table1.environment.eq("tna") & table1.kappa.eq(0.05) & table1.policy.eq("greedy")]
    grid_ols = tuna.loc[tuna.estimator.eq("M1"), "common_grid_forecast_rmse"].iloc[0]
    grid_iv = tuna.loc[tuna.estimator.eq("M3"), "common_grid_forecast_rmse"].iloc[0]
    text = f"""# Exploratory known-truth pricing experiment

## Methodology

The completed study is a six-cell exploratory Monte Carlo experiment calibrated to snack crackers, canned tuna, and bathroom tissue. It crosses these environments with κ = 0 and 0.05, holding the true reference-price elasticity at −1.06 and model adoption at 0.5. Each cell contains 30 independent replications, 52 initial-history weeks, and 104 pricing cycles. Each calibrated environment contains 67 stores. The eight arms are M1 OLS, M2 GBM, and M3 IV (2SLS), each under greedy and greedy-with-exploration pricing, plus legacy and an oracle-recommendation reference. GBM uses the accepted 500-tree configuration. DML and the M3 control-function variant remain supplementary diagnostic evidence and are not part of this experiment.

Within a cell and replication, arms share initial history and exogenous draws, then maintain their own evolving data histories. Production seeds differ from diagnostic and timing seeds. Failures remain in the dataset, with legacy fallback prices used when predictions are unavailable. The original 81-cell precision pilot and main experiment are deferred; this reduced study does not claim their precision targets or factorial coverage.

### Outcome definitions and uncertainty

**Elasticity recovery.** Terminal error is the final-cycle estimate minus −1.06. Bias is its mean across replications; terminal elasticity RMSE is the square root of mean squared terminal error across replications. For GBM, the reported elasticity is a local finite contrast in predicted log demand between prices 1% below and 1% above the reference price, divided by the corresponding log-price difference and averaged over recent observed contexts. It is a local response summary, not a globally constant GBM coefficient. Positive-slope frequency is the share of cycles with an estimate strictly above zero; a zero estimate does not count as positive but also does not meet the negative-sign reliability criterion. Legacy and oracle reference arms do not estimate elasticity, so recovery, estimated-sign outcomes, and joint decision reliability are not applicable to them.

**Forecast accuracy.** Common-grid RMSE evaluates predicted demand against known expected demand at every feasible ladder price using common current observable contexts across arms. Deployed-price RMSE evaluates predictions against realized sales at the prices actually deployed and therefore reflects both the policy's price path and realized demand noise. Within each replication, horizon RMSE is the square root of the mean of the 104 squared weekly RMSE values. Weekly evaluation sets are equally sized. The tables then report the mean and Monte Carlo standard error (MCSE) of these replication-level horizon RMSEs. This definition is used in both Table 1 and `performance.csv`; it is not the arithmetic mean of weekly RMSEs. Demand-scale RMSE levels should be compared within a calibrated environment.

**Pricing performance.** For each replication, normalized cumulative deployed regret is total expected revenue loss relative to the constrained oracle divided by total constrained-oracle expected revenue, summed over all stores and 104 cycles. Thus, it is revenue weighted rather than an unweighted average of weekly regret ratios. Cumulative revenue loss is the numerator of this ratio. CSV regret levels are fractions; the chapter and Figure 2 express levels as percentages and paired regret differences as percentage points. Lower regret is better.

**Reliability.** Model decision reliability is the fraction of replications in which every one of the final 26 cycles has deployed regret at most 2% and a finite, strictly negative estimated elasticity. Regret-only reliability omits the estimated-sign requirement and is reported separately for all arms, including references. Neither measure is an elasticity confidence-interval coverage rate.

**Oracle references.** The constrained oracle benchmark chooses the feasible ladder price maximizing known expected revenue and defines the regret denominator and zero-regret baseline. The simulated oracle-recommendation arm passes its optimal recommendation through the implementation's deployment adjustments, including cost pass-through and the managerial component. Its deployed prices can therefore depart from the optimum and incur positive regret. The saved direct-oracle zero-regret check is a separate controlled validation condition, not evidence that the adjusted oracle arm must have zero deployed regret in every production cell.

**Monte Carlo uncertainty and pairing.** MCSEs are calculated from independent replication-level outcomes, not from repeated store-weeks. A paired comparison subtracts the comparator's outcome from the treatment's outcome within the same cell and replication, then reports the mean difference and its sample standard deviation divided by √30. This applies to exploration versus greedy pricing, fitted-model arms versus legacy, and IV versus OLS under the same pricing policy. A negative paired regret difference favors the first-named arm. Figures show mean ± one MCSE, not 95% confidence intervals. Terminal elasticity RMSE uses a delta-method MCSE. All comparisons are exploratory; no multiple-comparison-adjusted significance claims are made.

## Findings

### Completed runs and implementation checks

All six cells completed 30 replications with eight arms and 104 pricing cycles, yielding 149,760 arm-cycle records. The saved mechanical audit passed all applicable checks, including feasible ladder prices, uncensored core demand, adoption assignments, and revenue identities. No numerical failure or fallback was recorded. These checks support implementation integrity; they do not establish estimator accuracy or economic superiority.

### Elasticity recovery and prediction

Table 1 reports recovery and prediction outcomes separately for each environment, endogeneity condition, estimator, and policy. Figure 1 shows the estimated trajectories against the known reference-price elasticity. Under κ = 0, greedy OLS terminal biases were approximately −0.006, −0.012, and −0.013 for snack crackers, canned tuna, and bathroom tissue, with RMSEs of 0.062, 0.100, and 0.075. OLS therefore recovered the reference elasticity closely in these exogenous cells.

Under κ = 0.05, greedy OLS terminal biases increased to approximately 1.344, 1.241, and 1.549, respectively. Mean terminal estimates consequently became positive despite the negative known elasticity. Corresponding IV biases were approximately 0.254, 0.452, and 0.338. IV substantially reduced OLS bias in these cells, but it did not eliminate it.

GBM's reported local contrast was zero at the terminal cycle in all 30 canned-tuna replications under both endogeneity conditions and both pricing policies. Its terminal bias and RMSE there were consequently 1.06. This result is consistent with locally flat tree predictions over the narrow ±1% interval. It does not establish that GBM learned no price response elsewhere on the feasible ladder.

Prediction accuracy and pricing performance did not yield interchangeable conclusions. For endogenous canned tuna, common-grid RMSE under greedy pricing was {grid_ols:.3f} for OLS and {grid_iv:.3f} for IV, while IV reduced normalized cumulative regret relative to OLS by approximately 0.363 percentage points. These numerically similar RMSE means do not establish formal predictive equivalence. They show why forecast accuracy and decision outcomes must be reported separately.

### Pricing performance and verified paired comparisons

Table 2 reports regret, revenue loss, joint model decision reliability, and regret-only reliability. Table 3 reports all 48 within-cell paired contrasts: six model arms versus legacy and IV versus OLS under each of the two policies in each cell. The selected comparisons below summarize the principal findings; each uses 30 paired replications.

| Environment | κ | Paired contrast | Mean regret difference (percentage points) | Paired MCSE (percentage points) |
|---|---:|---|---:|---:|
{paired_rows}

Without endogeneity, greedy OLS reduced mean regret relative to legacy in all three environments. Under endogeneity, greedy IV reduced mean regret relative to greedy OLS in every environment. Nevertheless, every fitted-model arm had higher mean regret than legacy in each endogenous cell. IV with exploration had the lowest mean regret among the fitted-model arms there, but this within-model ranking does not make it the best available pricing policy overall.

| Environment, κ = 0.05 | OLS greedy regret (%) | IV exploration regret (%) | Legacy regret (%) | IV exploration joint reliability (%) |
|---|---:|---:|---:|---:|
{regret_rows}

Joint model reliability varied substantially across environments even for the lowest-regret fitted-model arm. The separate regret-only column in Table 2 permits pricing-threshold comparisons with reference policies without treating their stored truth placeholders as estimated elasticities.

### Exploration and environmental variation

Across the 18 estimator-cell comparisons, mean exploration-minus-greedy regret differences ranged from {exploration.min():.4f} to {exploration.max():+.4f} percentage points. Exploration reduced mean regret in all six IV cells and all nine endogenous estimator-cell comparisons, but it was not uniformly beneficial across the experiment. These effects were small relative to the regret levels. Their precision is given by the paired MCSEs in Table 2; small magnitude should not be confused with an absence of statistical precision.

Results remain stratified by environment and κ. Differences in demand scales, price ladders, and calibration parameters make within-environment comparisons the interpretable basis for estimator and policy assessment. The canned-tuna local GBM result and variation in IV reliability also caution against treating a cross-environment average as a universal ranking.

## Discussion

The exploratory evidence separates three objectives: recovering the known reference-price elasticity, predicting demand, and choosing prices with low revenue loss. OLS performed well in the exogenous cells but became strongly biased under endogeneity. IV improved both elasticity recovery and regret relative to OLS under endogeneity, yet legacy pricing retained lower mean regret than all fitted-model arms in those cells. A more accurate estimator relative to another fitted method therefore did not, in this design, guarantee improvement over the operational reference policy. Exploration produced modest, condition-dependent changes over the 104-cycle horizon.

## Limitations

These conclusions apply to three calibrations, one reference elasticity, one adoption share, two endogeneity conditions, and the specified learner and policy settings. Thirty replications permit MCSE reporting but do not establish the originally planned precision targets or a general estimator ranking. The experiment does not cover other elasticities, adoption shares, negative endogeneity, alternative horizons, censored demand, or the full 81-cell interaction structure. GBM's local contrast is sensitive to the chosen price interval. Observed zero failures, or empirical reliability of 0% or 100%, do not establish corresponding population probabilities, even when a plug-in MCSE is zero. DML inference and M4 confidence-interval coverage remain withheld pending separate validation. No confirmatory hypothesis-testing or generalization beyond this design is claimed.

## Reproducibility appendix

Production used commit `{manifest_record['commit']}`. The original manifest, configurations, calibration identifiers, seeds, checkpoints, runtime records, and saved mechanical audit remain under `{output.relative_to(ROOT)}`. The audit acceptance record is `{json.dumps(checks['acceptance'], sort_keys=True)}`. The direct-oracle validation has the restricted interpretation described above. Timing artifacts remain separate under `{TIMING.relative_to(ROOT)}`.

Reporting revisions regenerate derived summaries and figures from saved estimates without rerunning simulations. `reporting_revision.json` records the source checksums, reporting-source hashes, environment, and output hashes. Original production and analysis provenance remains in the manifest. Run `PYTHONPATH=src python scripts/run_exploratory.py report` to regenerate reporting from the saved artifacts; this command reuses the saved audit and does not rerun simulation-based validation. The `analyze` command additionally performs the full audit in the project's supported environment.

Publication files are `table1_estimation_prediction.csv`, `table2_pricing_performance.csv`, `table3_paired_comparisons.csv`, `figure1_elasticity_trajectories.png`, `figure2_cumulative_regret.png`, and `replication_metrics.parquet`. In Figure 1, the dashed horizontal line is the true reference elasticity. In Figure 2, the dotted zero line is the constrained oracle benchmark and the separately labeled oracle-recommendation curve includes deployment adjustments. Shaded bands show one MCSE across replications. CSV blanks in reference-arm recovery and joint-reliability fields mean not applicable.
"""
    (ROOT / "docs/CHAPTER_EXPLORATORY_STUDY.md").write_text(text)
    (output / "chapter.md").write_text(text)


def analyze(*, reporting_only=False):
    if not (PRODUCTION / "estimates.parquet").exists():
        raise ValueError("Production results are incomplete")
    if reporting_only:
        checks = json.loads((PRODUCTION / "checks.json").read_text())
    else:
        from ktsim.validation import check_run
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
    if estimates.duplicated(["cell", "arm", "rep", "cycle"]).any():
        raise ValueError("Duplicate arm-cycle observations")
    cycle_sets = estimates.groupby(["cell", "arm", "rep"]).cycle.agg(set)
    if len(cycle_sets) != 6 * 30 * 8 or not cycle_sets.map(lambda x: x == set(range(1, 105))).all():
        raise ValueError("Expected 104 cycles for every cell, arm, and replication")
    table1, table2, _ = tables(estimates, PRODUCTION)
    performance(estimates, stage="exploratory").to_csv(PRODUCTION / "performance.csv", index=False)
    figures(estimates, PRODUCTION)
    record = json.loads((PRODUCTION / "manifest.json").read_text())
    # Preserve original run/analysis provenance; record reporting-only changes separately.
    chapter(table1, table2, checks, record, PRODUCTION)
    outputs = [
        "table1_estimation_prediction.csv", "table2_pricing_performance.csv",
        "table3_paired_comparisons.csv", "figure1_elasticity_trajectories.png",
        "figure2_cumulative_regret.png", "replication_metrics.parquet", "performance.csv", "chapter.md",
    ]
    revision = dict(
        reporting_version="1.2", generated_at=datetime.now().astimezone().isoformat(),
        base_commit=git_state()[0], working_tree_dirty=git_state()[1],
        simulation_rerun=False,
        audit="reused saved checks.json" if reporting_only else "full audit rerun",
        source_sha256={name: sha256(PRODUCTION / name) for name in
                       ("estimates.parquet", "states.parquet", "checks.json", "manifest.json")},
        reporting_source_sha256={name: sha256(ROOT / name) for name in
                                 ("scripts/run_exploratory.py", "src/ktsim/metrics.py")},
        output_sha256={name: sha256(PRODUCTION / name) for name in outputs},
        environment=dict(platform=platform.platform(), python=platform.python_version(),
                         numpy=np.__version__, pandas=pd.__version__),
        definitions=dict(horizon_rmse="sqrt(mean(weekly_rmse ** 2))",
                         reference_joint_reliability="not applicable",
                         reference_regret_reliability="last 26 cycles each at most 2% regret",
                         paired_difference="treatment minus comparator, percentage points",
                         paired_mcse="sample SD of paired differences / sqrt(n_pairs)"),
    )
    (PRODUCTION / "reporting_revision.json").write_text(json.dumps(revision, indent=2) + "\n")
    print(f"Completed analysis: {PRODUCTION}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["benchmark", "run", "analyze", "report", "check"])
    args = parser.parse_args()
    if args.command == "benchmark":
        benchmark()
    elif args.command == "run":
        production()
    elif args.command == "analyze":
        analyze()
    elif args.command == "report":
        analyze(reporting_only=True)
    else:
        from ktsim.validation import check_run
        print(json.dumps(check_run(PRODUCTION), indent=2))


if __name__ == "__main__":
    main()
