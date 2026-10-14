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


def choose_n_required(perf_pilot, cfg, replication_data=None):
    """Use fraction-scale regret and every cell/arm; expose caps and paired Ns."""
    inputs, missing = [], []
    for (cell, arm), group in perf_pilot.groupby(["cell", "arm"]):
        if not arm.startswith(("M1:", "M2:", "M3:", "M4_")):
            continue
        for measure, checkpoint, target in [
            ("bias", "104", cfg["targets"]["elasticity"]),
            ("norm_cum_regret_all", "horizon", cfg["targets"]["regret"]),
        ]:
            selected = group[
                group.measure.eq(measure) & group.cycle_or_horizon.astype(str).eq(checkpoint)
            ]
            if selected.empty or not np.isfinite(selected.mcse.iloc[0]):
                missing.append(dict(cell=cell, arm=arm, measure=measure))
                continue
            row = selected.iloc[0]
            sd = float(row.mcse * np.sqrt(row.n_reps))
            inputs.append(
                dict(
                    cell=cell,
                    arm=arm,
                    measure=measure,
                    sd=sd,
                    target=target,
                    required=int(np.ceil((sd / target) ** 2)),
                )
            )
    paired = []
    if replication_data is not None:
        for cell, group in replication_data.groupby("cell"):
            pivot = group.pivot(index="rep", columns="arm", values="norm_cum_regret_all")
            comparisons = []
            for policy in ("greedy", "greedy_rps"):
                comparisons += [(f"{name}:{policy}", f"M1:{policy}") for name in ("M3", "M4_pliv")]
            comparisons += [
                (f"{name}:greedy_rps", f"{name}:greedy")
                for name in ("M1", "M2", "M3", "M4_plr", "M4_pliv")
            ]
            for left, right in comparisons:
                if left not in pivot or right not in pivot:
                    continue
                difference = (pivot[left] - pivot[right]).dropna()
                if len(difference) < 2:
                    continue
                sd = float(difference.std(ddof=1))
                target = cfg["targets"]["paired_regret"]
                paired.append(
                    dict(
                        cell=cell,
                        comparison=f"{left} vs {right}",
                        n_pairs=len(difference),
                        sd=sd,
                        required=int(np.ceil((sd / target) ** 2)),
                    )
                )
    bound = max(inputs, key=lambda row: row["required"]) if inputs else None
    required = max(cfg["floor"], bound["required"]) if bound and not missing else None
    selected = min(required, cfg["cap"]) if required is not None else None
    return dict(
        N_required=required,
        n_selected=selected,
        bounding=bound,
        inputs=inputs,
        missing=missing,
        paired=paired,
        targets=cfg["targets"],
        floor=cfg["floor"],
        cap=cfg["cap"],
        budget_hours=cfg["budget_hours"],
        shortfall=bool(required is not None and required > cfg["cap"]),
        achieved_mcse_at_cap=[
            dict(
                cell=r["cell"],
                arm=r["arm"],
                measure=r["measure"],
                mcse=r["sd"] / np.sqrt(cfg["cap"]),
            )
            for r in inputs
        ],
    )
