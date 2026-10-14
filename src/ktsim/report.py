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
from ktsim.metrics import replication_summary


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
    measures = [
        ("eta_hat", "elasticity"),
        ("regret_dep_all", "deployed_regret"),
        ("forecast_mape", "forecast_error"),
        ("fallback_used", "fallback"),
        ("first_stage_F", "first_stage"),
    ]
    for column, filename in measures:
        fig, axis = plt.subplots(figsize=(9, 5))
        for arm, group in estimates.groupby("arm"):
            values = group.groupby("cycle")[column].mean()
            axis.plot(values.index, values.values, label=arm)
        axis.set(xlabel="Cycle", ylabel=column)
        axis.legend(fontsize=6)
        fig.tight_layout()
        fig.savefig(directory / f"{filename}.png", dpi=150)
        plt.close(fig)


def display_performance(frame):
    frame = frame.copy()
    percentage = frame.measure.str.startswith(("norm_cum_regret", "reliable")) | (
        frame.measure.isin(
            [
                "coverage",
                "fallback_rate",
                "extreme_rate",
                "positive_slope_rate",
                "failure_share",
                "forecast_mape",
                "censored_share",
            ]
        )
    )
    frame.loc[percentage, ["estimate", "mcse"]] *= 100
    frame["unit"] = percentage.map({True: "%", False: "native"})
    withheld = frame.measure.eq("coverage") & frame.coverage_status.str.startswith("withheld")
    frame["estimate"] = frame.estimate.astype(object)
    frame.loc[withheld, "estimate"] = "withheld"
    return frame


def make_report(output):
    output = Path(output)
    manifest = json.loads((output / "manifest.json").read_text())
    estimates = pd.read_parquet(output / "estimates.parquet")
    perf = pd.read_csv(output / "performance.csv")
    stage = manifest.get("stage", "validation")
    reliability = manifest.get("dgm", {}).get("reliability", {"tau": 0.02, "window": 26})
    summaries = replication_summary(estimates, reliability)
    config = manifest.get("decisions_config")
    if config is None:
        import yaml

        config = yaml.safe_load(Path("configs/decisions.yaml").read_text())
    decisions = {}
    if stage == "pilot":
        cells = manifest.get("cells", [])
        expected_arms = {
            f"{name}:{policy}"
            for cell in cells
            for name in cell["estimators"]
            for policy in cell["policies"]
        }
        if any("M3" in cell["estimators"] for cell in cells):
            expected_arms.update("M3_cf:" + policy for cell in cells for policy in cell["policies"])
        decisions = choose_n_required(
            summaries,
            config,
            expected_cells={cell["name"] for cell in cells},
            expected_arms=expected_arms,
        )
        decisions["scientific_fingerprint"] = manifest.get("scientific_fingerprint")
        seconds = summaries.groupby(["cell", "arm"]).seconds.mean().sum()
        n_sim = decisions.get("n_sim")
        decisions["projected_core_hours"] = None if n_sim is None else seconds * n_sim / 3600
        decisions["budget_shortfall_hours"] = (
            None
            if n_sim is None
            else max(0.0, decisions["projected_core_hours"] - config["budget_hours"])
        )

    def section(title, measures):
        selected = perf[perf.measure.isin(measures)]
        return [f"## {title}", table(display_performance(selected)), ""]

    calibration_rows = []
    calibrations = manifest.get("calibration", {})
    if "p_bar" in calibrations:  # development fixtures from older direct callers
        calibrations = {"fixture": calibrations}
    for name, calibration in calibrations.items():
        diagnostic = calibration.get("diagnostics", {})
        calibration_rows.append(
            dict(
                environment=name,
                p_bar=calibration["p_bar"],
                beta_reference=calibration["beta_reference"],
                original_beta_reference=diagnostic.get("previous_beta_reference"),
                original_p_bar=diagnostic.get("previous_p_bar"),
                investigation=diagnostic.get("beta_reference_review", "not applicable"),
            )
        )
    lines = [
        "# Known-Truth Pricing Simulation",
        "",
        f"Run: {output.name}; commit: {manifest['commit']}; stage: {stage}; "
        f"protocol: {manifest.get('protocol_version', 'unversioned')}",
        "",
        "Synthetic fixture, not Dominick's results."
        if manifest["synthetic"]
        else "Empirically calibrated development validation."
        if stage == "validation"
        else "Empirically calibrated scientific stage.",
        "",
        "Author protocol approval remains governed by docs/PROTOCOL_v1.1.md.",
        "",
        "## Provenance",
        "```json",
        json.dumps(manifest, indent=2),
        "```",
        "",
        "## Calibration and coverage audit",
        table(pd.DataFrame(calibration_rows)),
        table(pd.DataFrame(manifest.get("calibration_checks", []))),
        "```json",
        json.dumps(manifest.get("coverage_audits", {}), indent=2),
        "```",
        "Benchmark beta_reference is a descriptive review flag, not an exclusion criterion. "
        "Investigation: units, log base, promotions and competing-index construction remain pending.",
        "",
    ]
    lines += section("Elasticity and denominators", ["bias", "empirical_se", "rmse", "coverage"])
    lines += section(
        "Revenue-weighted regret and fallback rates",
        [
            "cum_loss_all",
            "cum_loss_model",
            "cum_loss_all_rec",
            "cum_loss_model_rec",
            "norm_cum_regret_all",
            "norm_cum_regret_model",
            "norm_cum_regret_all_rec",
            "norm_cum_regret_model_rec",
            "fallback_rate",
            "extreme_rate",
            "positive_slope_rate",
        ],
    )
    reliability_rows = perf[perf.measure.isin(["reliable_regret", "reliable_sign", "reliable"])]
    reliability_table = reliability_rows.pivot(
        index=["cell", "arm"], columns="measure", values="estimate"
    ).reset_index()
    for column in ("reliable_regret", "reliable_sign", "reliable"):
        if column in reliability_table:
            reliability_table[column] *= 100
    lines += ["## Reliability (%)", table(reliability_table), ""]
    lines += section("Forecast accuracy", ["forecast_mape", "forecast_rmse"])
    lines += section(
        "Failures and denominators",
        ["failure_share", "fallback_rate", "extreme_rate", "positive_slope_rate"],
    )
    lines += section("Runtime", ["seconds"])
    if stage == "pilot":
        lines += [
            "## N_required decision and paired comparisons",
            "```json",
            json.dumps(decisions, indent=2),
            "```",
            "",
        ]
    lines += [
        "## Interpretation",
        "Ratios are stored as fractions and shown as percentages here. "
        "Bias/SE/RMSE use finite estimates; coverage uses available intervals, with M4 "
        "coverage withheld unless inference_validated is explicitly set by the author. "
        "Short runs do not establish reliability or statistical acceptance.",
        "",
    ]
    figures(estimates, output / "figures")
    manifest["figures"] = [
        str(path.relative_to(output)) for path in sorted((output / "figures").glob("*.png"))
    ]
    lines += ["## Figures"]
    for path in manifest["figures"]:
        lines.append(f"![{Path(path).stem}]({path})")
        if Path(path).stem == "deployed_regret":
            lines += [
                "Fallback rates (%) for the regret figure:",
                table(display_performance(perf[perf.measure.eq("fallback_rate")])),
            ]
    (output / "report.md").write_text("\n".join(lines) + "\n")
    # Derived fields do not alter the fingerprint of the frozen inputs used for resume.
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (output / "decisions.json").write_text(json.dumps(decisions, indent=2) + "\n")
    return output / "report.md"
