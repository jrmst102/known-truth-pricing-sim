from dataclasses import dataclass

import numpy as np


@dataclass
class NSimDecision:
    n_sim: int | None
    required: int | None
    cap_exceeded: bool
    inputs: list[dict]
    reason: str


@dataclass
class PassThroughDecision:
    weak: float | None
    strong: float | None
    inputs: list[dict]


@dataclass
class ComputePlan:
    projected_core_hours: float | None
    budget_hours: float
    n_sim: int | None
    inputs: list[dict]
    ladder_step: str


def choose_n_sim(perf_P1, bias_target=0.02, regret_target_pp=0.25, floor=500, cap=2000):
    inputs = []
    for _, row in perf_P1.iterrows():
        final_bias = row.measure == "bias" and str(row.cycle_or_horizon) == "156"
        horizon_regret = row.measure == "regret_rec" and str(row.cycle_or_horizon) == "horizon"
        if not (final_bias or horizon_regret) or not np.isfinite(row.mcse):
            continue
        sd = float(row.mcse * np.sqrt(row.n_reps))
        target = bias_target if final_bias else regret_target_pp
        inputs.append(
            dict(
                arm=row.arm,
                measure=row.measure,
                sd=sd,
                target=target,
                required=int(np.ceil((sd / target) ** 2)),
            )
        )
    if not inputs:
        return NSimDecision(
            None, None, False, [], "P1 final-week bias and horizon regret are required"
        )
    measures = {item["measure"] for item in inputs}
    if measures != {"bias", "regret_rec"}:
        return NSimDecision(None, None, False, inputs, "P1 is incomplete; no n_sim decision")
    required = max(floor, max(item["required"] for item in inputs))
    return NSimDecision(
        min(cap, required),
        required,
        required > cap,
        inputs,
        "Ceiling of max (SD / target)^2, bounded by floor and cap; protocol review pending",
    )


def choose_pass_through(perf_P4):
    inputs = []
    if not perf_P4.empty:
        frame = perf_P4[perf_P4.arm.str.startswith("M3:")]
        for cell, group in frame.groupby("cell"):
            value = float(cell.split("=")[-1])
            final = group[group.cycle.eq(group.cycle.max())]
            median = float(final.first_stage_F.median())
            inputs.append(dict(pass_through=value, median_F=median))
    weak = [row for row in inputs if 8 <= row["median_F"] <= 12]
    strong = [row for row in inputs if row["median_F"] >= 50]
    return PassThroughDecision(
        min(weak, key=lambda row: abs(row["median_F"] - 10))["pass_through"] if weak else None,
        min(strong, key=lambda row: row["pass_through"])["pass_through"] if strong else None,
        inputs,
    )


def compute_projection(runtime, n_sim, budget_hours=150.0):
    inputs = []
    if not runtime.empty:
        baseline = runtime[runtime.cell.eq("P1")]
        for arm, group in baseline.groupby("arm"):
            inputs.append(dict(arm=arm, mean_seconds=float(group.seconds.mean())))
    hours = (
        None
        if n_sim is None or not inputs
        else 27 * n_sim * sum(row["mean_seconds"] for row in inputs) / 3600
    )
    step = (
        "none"
        if hours is not None and hours <= budget_hours
        else (
            "Await author-provided protocol compute ladder"
            if hours is not None
            else "Insufficient P1 runtime"
        )
    )
    return ComputePlan(hours, budget_hours, n_sim, inputs, step)


def censoring_multiplier(summary_P5):
    if summary_P5.empty:
        return None
    means = summary_P5.groupby("cell").censored_share.mean()
    closest = (means - 0.05).abs().idxmin()
    return float(closest.split("=")[-1])
