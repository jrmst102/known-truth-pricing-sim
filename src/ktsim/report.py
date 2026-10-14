import json
import os
import platform
from importlib.metadata import version
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from ktsim.decisions import choose_n_required
from ktsim.pilot import atomic_json


def environment():
    packages = [
        "ktsim",
        "numpy",
        "pandas",
        "pyarrow",
        "scipy",
        "statsmodels",
        "linearmodels",
        "lightgbm",
        "doubleml",
        "scikit-learn",
        "PyYAML",
        "joblib",
        "matplotlib",
    ]
    model = platform.processor()
    cpuinfo = Path("/proc/cpuinfo")
    if cpuinfo.exists():
        model = next(
            (
                line.split(":", 1)[1].strip()
                for line in cpuinfo.read_text().splitlines()
                if line.startswith("model name")
            ),
            model,
        )
    ram = os.sysconf("SC_PHYS_PAGES") * os.sysconf("SC_PAGE_SIZE") / 1024**3
    return dict(
        python=platform.python_version(),
        packages={name: version(name) for name in packages},
        cpu=model,
        cores=os.cpu_count(),
        ram_gib=round(ram, 2),
    )


def table(frame):
    if frame.empty:
        return "Not available for this run.\n"
    headers = list(frame)
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for values in frame.itertuples(index=False, name=None):
        measure = values[headers.index("measure")] if "measure" in headers else ""
        precision = (
            2 if measure in {"coverage", "regret_rec", "regret_dep", "cumulative_regret"} else 3
        )
        formatted = [
            f"{value:.{precision}f}" if isinstance(value, float) else str(value) for value in values
        ]
        lines.append("| " + " | ".join(formatted) + " |")
    return "\n".join(lines) + "\n"


def figures(estimates, directory):
    directory.mkdir(exist_ok=True)
    for measure, label in [
        ("eta_error", "Elasticity error"),
        ("regret_dep_all", "Deployed weekly regret (%)"),
        ("price_sd_26", "Within-store log-price SD, trailing 26 weeks"),
    ]:
        frame = estimates.assign(eta_error=estimates.eta_hat - estimates.eta_true)
        fig, axis = plt.subplots(figsize=(9, 5))
        for arm, group in frame.groupby("arm"):
            values = group.groupby("cycle")[measure].median()
            if measure == "regret_dep_all":
                values = 100 * values
            axis.plot(values.index, values.values, label=arm)
        axis.set(xlabel="Cycle", ylabel=label)
        axis.legend(fontsize=6, ncol=2)
        fig.tight_layout()
        fig.savefig(directory / f"{measure}.png", dpi=150)
        plt.close(fig)
    p0 = estimates[estimates.cell.eq("P0") & estimates.cycle.eq(estimates.cycle.max())]
    if not p0.empty:
        fig, axis = plt.subplots(figsize=(9, 5))
        for arm, group in p0.groupby("arm"):
            axis.hist(group.eta_hat.dropna(), bins=15, alpha=0.4, label=arm)
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
                quantiles = group.groupby("cycle")[measure].quantile([0.1, 0.5, 0.9]).unstack()
                axis.plot(quantiles.index, quantiles[0.5], label=arm)
                axis.fill_between(quantiles.index, quantiles[0.1], quantiles[0.9], alpha=0.1)
            axis.set(xlabel="Cycle", ylabel=measure)
            axis.legend(fontsize=6)
            fig.tight_layout()
            fig.savefig(directory / f"{filename}.png", dpi=150)
            plt.close(fig)
        fig, axis = plt.subplots(figsize=(7, 5))
        for arm, group in p1.groupby("arm"):
            final = group[group.cycle.eq(group.cycle.max())]
            axis.scatter(
                final.eta_hat.mean() - final.eta_true.iloc[0], group.forecast_mape.mean(), label=arm
            )
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
        axis.axhspan(8, 12, alpha=0.2)
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
    stage = manifest.get("stage", "validation")
    display = perf.copy()
    fraction = display.measure.str.contains("regret|rate|reliable|coverage|share|mape", regex=True)
    display.loc[fraction, ["estimate", "mcse"]] *= 100
    display["units"] = fraction.map({True: "%", False: "native"})
    coverage = display.measure.eq("coverage") & display.coverage_status.str.startswith("withheld")
    display["estimate"] = display.estimate.astype(object)
    display.loc[coverage, "estimate"] = "withheld"

    # Counts are retained even when every fit or interval is missing.
    def section(measures):
        return table(display[display.measure.isin(measures)])

    lines = [
        "# Known-Truth Pricing V1.1",
        "",
        f"Run: {output.name}; commit: {manifest['commit']}; master seed: {manifest['master_seed']}",
        f"Protocol: {manifest.get('protocol_version', '1.1')}; stage: {stage}; "
        f"seed child: {manifest.get('seed_child_index', 0)}",
        "",
        "Synthetic fixture — development validation, not empirical results."
        if manifest["synthetic"]
        else "Empirical calibration; "
        + (
            "mechanical validation, not scientific results."
            if stage == "validation"
            else "scientific run."
        ),
        "",
        "## Calibration and coverage audit",
        table(pd.DataFrame(manifest.get("calibration_checks", []))),
    ]
    for env, cal in manifest.get("calibrations", {}).items():
        lines += [
            f"### {env}",
            f"Reference price: {cal['p_bar']}; stores: {cal['n_stores']}; "
            f"weeks: {cal['weeks']}; observational elasticity: {cal['beta_reference']}.",
            f"Elasticity review: {cal.get('diagnostics', {}).get('elasticity_review', 'pending')}.",
        ]
        audit = manifest.get("coverage_audits", {}).get(env)
        if audit:
            lines += [
                f"Coverage denominator: {audit['calendar_span']} weeks × {audit['n_retained_stores']} stores; "
                f"range: {audit['week_range']}.",
                table(pd.DataFrame(audit["top_upcs"])),
                f"Best coverage across all UPCs: {audit.get('best_upc', 'not recorded')}",
            ]
            if "window" in audit:
                window = audit["window"]
                lines += [
                    f"Step 2 calibration window: {window['week_range']}; {window['calendar_span']} weeks; "
                    f"{window['n_retained_stores']} stores. Full-span audit retained above.",
                    table(pd.DataFrame(window["top_upcs"])),
                ]
    lines += [
        "## Elasticity estimates and denominators",
        section(["bias", "empirical_se", "rmse", "coverage"]),
        "Bias, empirical SE and RMSE use n_estimated; coverage uses n_with_interval. "
        "M4 coverage is withheld until inference validation and author activation.",
        "## Regret and fallback rates",
        section(
            [
                "norm_cum_regret_all",
                "norm_cum_regret_model",
                "norm_cum_regret_rec_all",
                "norm_cum_regret_rec_model",
                "cum_loss_all",
                "cum_loss_model",
                "cum_loss_rec_all",
                "cum_loss_rec_model",
                "fallback_rate",
                "extreme_rate",
                "positive_slope_rate",
            ]
        ),
        "Regret fractions are converted to percentages here. Cumulative loss is in dollars. "
        "Fallback revenue remains included in every policy comparison.",
        "## Decision reliability",
        section(["reliable", "reliable_regret", "reliable_sign"]),
        "## Forecast accuracy",
        section(["forecast_mape", "forecast_rmse"]),
        "## Failures and denominators",
        section(["failure_share", "fallback_rate", "extreme_rate", "positive_slope_rate"]),
        "## Runtime",
        table(runtime),
    ]
    decisions = {}
    if stage == "pilot":
        reps = pd.read_csv(output / "replication_metrics.csv")
        decision = choose_n_required(perf, manifest["decisions"], reps)
        decisions["n_required"] = decision
        decisions["scientific_settings_sha256"] = manifest.get("scientific_settings_sha256")
        lines += [
            "## Main-experiment replication decision",
            "```json",
            json.dumps(decision, indent=2),
            "```",
        ]
        if decision["shortfall"]:
            lines += [
                "**Precision shortfall at the configured compute cap; achieved MCSEs are listed above.**"
            ]
        if decision["n_selected"]:
            hours = (
                runtime.groupby(["cell", "arm"]).seconds.mean().sum()
                * decision["n_selected"]
                / 3600
            )
            decisions["projected_core_hours"] = float(hours)
            lines += [f"Projected core hours: {hours:.2f}; budget: {decision['budget_hours']}."]
    figures(estimates, output / "figures")
    manifest["figures"] = [
        str(p.relative_to(output)) for p in sorted((output / "figures").glob("*.png"))
    ]
    lines += ["## Provenance", "```json", json.dumps(manifest, indent=2), "```", "## Diagnostics"]
    lines += [f"![{Path(p).stem}]({p})" for p in manifest["figures"]]
    (output / "report.md").write_text("\n".join(lines) + "\n")
    atomic_json(decisions, output / "decisions.json")
    atomic_json(manifest, output / "manifest.json")
    return output / "report.md"
