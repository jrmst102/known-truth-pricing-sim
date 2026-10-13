import json
import os
import platform
from dataclasses import asdict
from importlib.metadata import version
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from ktsim.decisions import (
    censoring_multiplier,
    choose_n_sim,
    choose_pass_through,
    compute_projection,
)


def environment():
    packages = ["ktsim", "numpy", "pandas", "pyarrow", "scipy", "statsmodels", "linearmodels",
                "lightgbm", "doubleml", "scikit-learn", "PyYAML", "joblib", "matplotlib"]
    model = platform.processor()
    cpuinfo = Path("/proc/cpuinfo")
    if cpuinfo.exists():
        model = next((line.split(":", 1)[1].strip() for line in cpuinfo.read_text().splitlines()
                      if line.startswith("model name")), model)
    ram = os.sysconf("SC_PHYS_PAGES") * os.sysconf("SC_PAGE_SIZE") / 1024**3
    return dict(python=platform.python_version(), packages={name: version(name) for name in packages},
                cpu=model, cores=os.cpu_count(), ram_gib=round(ram, 2))


def table(frame):
    if frame.empty:
        return "Not available for this run.\n"
    headers = list(frame)
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for values in frame.itertuples(index=False, name=None):
        measure = values[headers.index("measure")] if "measure" in headers else ""
        precision = 2 if measure in {"coverage", "regret_rec", "regret_dep", "cumulative_regret"} else 3
        formatted = [f"{value:.{precision}f}" if isinstance(value, float) else str(value) for value in values]
        lines.append("| " + " | ".join(formatted) + " |")
    return "\n".join(lines) + "\n"


def figures(estimates, directory):
    directory.mkdir(exist_ok=True)
    p0 = estimates[estimates.cell.eq("P0") & estimates.cycle.eq(estimates.cycle.max())]
    if not p0.empty:
        fig, axis = plt.subplots(figsize=(9, 5))
        for arm, group in p0.groupby("arm"):
            axis.hist(group.eta_hat.dropna(), bins=15, alpha=.4, label=arm)
        axis.axvline(p0.eta_true.iloc[0], color="black", linestyle="--")
        axis.set(xlabel="Estimated elasticity", ylabel="Replications")
        axis.legend(fontsize=7)
        fig.tight_layout()
        fig.savefig(directory / "p0_elasticity.png", dpi=150)
        plt.close(fig)
    p1 = estimates[estimates.cell.eq("P1")]
    if not p1.empty:
        for measure, filename in [("eta_hat", "p1_elasticity"), ("price_sd_26", "p1_price_sd")]:
            fig, axis = plt.subplots(figsize=(9, 5))
            for arm, group in p1.groupby("arm"):
                quantiles = group.groupby("cycle")[measure].quantile([.1, .5, .9]).unstack()
                axis.plot(quantiles.index, quantiles[.5], label=arm)
                axis.fill_between(quantiles.index, quantiles[.1], quantiles[.9], alpha=.1)
            axis.set(xlabel="Cycle", ylabel=measure)
            axis.legend(fontsize=6)
            fig.tight_layout()
            fig.savefig(directory / f"{filename}.png", dpi=150)
            plt.close(fig)
        fig, axis = plt.subplots(figsize=(7, 5))
        for arm, group in p1.groupby("arm"):
            final = group[group.cycle.eq(group.cycle.max())]
            axis.scatter(final.eta_hat.mean() - final.eta_true.iloc[0], group.forecast_mape.mean(), label=arm)
        axis.set(xlabel="Elasticity bias", ylabel="Forecast MAPE")
        axis.legend(fontsize=6)
        fig.tight_layout()
        fig.savefig(directory / "p1_forecast_bias.png", dpi=150)
        plt.close(fig)
    p4 = estimates[estimates.cell.str.startswith("P4:") & estimates.arm.eq("M3:legacy")]
    if not p4.empty:
        fig, axis = plt.subplots(figsize=(7, 5))
        values = p4[p4.cycle.eq(p4.cycle.max())].groupby("cell").first_stage_F.median()
        axis.plot([float(label.split("=")[-1]) for label in values.index], values.values, "o-")
        axis.axhspan(8, 12, alpha=.2)
        axis.axhline(50, color="black", linestyle="--")
        axis.set(xlabel="Pass-through", ylabel="Median first-stage statistic")
        fig.tight_layout()
        fig.savefig(directory / "p4_first_stage.png", dpi=150)
        plt.close(fig)


def make_report(output):
    output = Path(output)
    manifest = json.loads((output / "manifest.json").read_text())
    estimates = pd.read_parquet(output / "estimates.parquet")
    perf = pd.read_csv(output / "performance.csv")
    runtime = pd.read_csv(output / "runtime.csv")
    n_sim = choose_n_sim(perf[perf.cell.eq("P1")])
    passthrough = choose_pass_through(estimates[estimates.cell.str.startswith("P4:")])
    compute = compute_projection(runtime, n_sim.n_sim)
    p5 = estimates[estimates.cell.str.startswith("P5:")]
    decisions = dict(n_sim=asdict(n_sim), pass_through=asdict(passthrough),
                     compute=asdict(compute), censoring_multiplier=censoring_multiplier(p5))
    lines = ["# Known-Truth Pricing Pilot", "",
             f"Run: {output.name}; commit: {manifest['commit']}; master seed: {manifest['master_seed']}",
             "", "**Status: exploratory implementation; protocol review and author sign-off pending.**",
             "Synthetic fixture, not Dominick's results." if manifest["synthetic"] else "Real-data calibration.",
             "", "## Reproducibility", "```json", json.dumps(manifest, indent=2), "```", "",
             "## P0 correctness", table(perf[perf.cell.eq("P0")]),
             "P0 acceptance requires full reps/horizon, bias within two MCSEs, coverage >= 0.80, "
             "zero failures and zero oracle recommended-price regret.", "",
             "## P1 decision", "```json", json.dumps(asdict(n_sim), indent=2), "```", "",
             table(perf[perf.cell.eq("P1")]), "## P4 instrument", "```json",
             json.dumps(asdict(passthrough), indent=2), "```", "",
             "Missing weak/strong choices mean the supplied grid does not qualify; do not substitute values.",
             "## Bound cells", table(estimates[["cell", "eta_true", "p_star", "oracle_at_bound"]].drop_duplicates()),
             "## Compute plan", "```json", json.dumps(asdict(compute), indent=2), "```", "",
             "Projection assumes 27 cells with the measured P1 arms. The actual protocol compute ladder "
             "and full-design arm weights were not supplied; no automatic protocol changes are made.",
             "## Failures"]
    failures = perf[(perf.measure.eq("failure_share")) & perf.cycle_or_horizon.eq("horizon")].copy()
    failures["flag_gt_5_percent"] = failures.estimate > .05
    lines += [table(failures), "## Censoring", f"Chosen multiplier: {decisions['censoring_multiplier']}",
              table(perf[perf.cell.str.startswith("P5:") & perf.measure.eq("censored_share")]),
              "## Calibration", table(pd.DataFrame(manifest.get("calibration_checks", []))),
              "## Limitations", "See CHANGELOG.md and docs/IMPLEMENTATION_NOTES.md for unresolved protocol rules.",
              "Scientific replay excludes elapsed times and timestamps. CI and synthetic runs never use raw data.",
              "## Diagnostics"]
    figures(estimates, output / "figures")
    lines += [f"![{path.stem}](figures/{path.name})" for path in sorted((output / "figures").glob("*.png"))]
    (output / "report.md").write_text("\n".join(lines) + "\n")
    (output / "decisions.json").write_text(json.dumps(decisions, indent=2) + "\n")
    return output / "report.md"