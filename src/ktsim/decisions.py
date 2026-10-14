import numpy as np


def choose_n_required(perf_pilot, config, *, expected_cells=None, expected_arms=None):
    """Use replication-level terminal errors and normalized deployed regret.

    Paired comparisons use within-replication differences, never independent-arm SEs.
    Targets and the explicit floor/cap/budget are supplied by decisions.yaml.
    """
    targets = config["targets"]
    if config["cap"] < 1 or config["floor"] < 0 or config["budget_hours"] <= 0:
        raise ValueError("Invalid explicit compute limits")
    if any(value <= 0 for value in targets.values()):
        raise ValueError("Precision targets must be positive")
    inputs, paired, incomplete = [], [], []
    if expected_cells is not None and expected_arms is not None:
        available = set(zip(perf_pilot.cell, perf_pilot.arm))
        for cell in expected_cells:
            for arm in expected_arms:
                if (cell, arm) not in available:
                    incomplete.append(dict(cell=cell, arm=arm, reason="missing planned arm"))
    for (cell, arm), group in perf_pilot.groupby(["cell", "arm"]):
        if arm.startswith(("oracle:", "legacy:", "data:")):
            continue
        for measure, target in [
            ("terminal_error", targets["elasticity"]),
            ("norm_cum_regret_all", targets["regret"]),
        ]:
            values = group[measure].to_numpy(dtype=float)
            values = values[np.isfinite(values)]
            if len(values) < 2:
                incomplete.append(dict(cell=cell, arm=arm, measure=measure))
                continue
            sd = float(np.std(values, ddof=1))
            inputs.append(
                dict(
                    cell=cell,
                    arm=arm,
                    measure=measure,
                    sd=sd,
                    n_total=len(group),
                    n_estimated=len(values),
                    target=target,
                    required=int(np.ceil((sd / target) ** 2)),
                )
            )
    for cell, group in perf_pilot.groupby("cell"):
        arms = set(group.arm)
        comparisons = []
        for policy in ("greedy", "greedy_rps"):
            comparisons.extend(
                [(f"M3:{policy}", f"M1:{policy}"), (f"M4_pliv:{policy}", f"M1:{policy}")]
            )
        estimators = {arm.split(":")[0] for arm in arms}
        comparisons.extend(
            (f"{est}:greedy_rps", f"{est}:greedy")
            for est in estimators
            if est not in {"oracle", "legacy", "data"}
        )
        for left, right in comparisons:
            if left not in arms or right not in arms:
                continue
            a = group[group.arm.eq(left)].set_index("rep").norm_cum_regret_all
            b = group[group.arm.eq(right)].set_index("rep").norm_cum_regret_all
            difference = (a - b).dropna()
            if len(difference) < 2:
                incomplete.append(dict(cell=cell, comparison=f"{left} minus {right}"))
                continue
            sd = float(difference.std(ddof=1))
            paired.append(
                dict(
                    cell=cell,
                    comparison=f"{left} minus {right}",
                    sd=sd,
                    n_paired=len(difference),
                    target=targets["paired"],
                    required=int(np.ceil((sd / targets["paired"]) ** 2)),
                )
            )
    if not inputs or incomplete:
        return dict(
            N_required=None,
            n_sim=None,
            reason="Incomplete pilot",
            inputs=inputs,
            paired=paired,
            incomplete=incomplete,
            config=config,
        )
    bounding = max(inputs, key=lambda row: row["required"])
    required = max(config["floor"], bounding["required"])
    n_sim = min(config["cap"], required)
    for row in inputs + paired:
        row["achieved_mcse_at_cap"] = row["sd"] / np.sqrt(config["cap"])
        row["target_shortfall_at_cap"] = max(0.0, row["achieved_mcse_at_cap"] - row["target"])
    return dict(
        N_required=required,
        n_sim=n_sim,
        bounding=bounding,
        cap_exceeded=required > config["cap"],
        inputs=inputs,
        paired=paired,
        config=config,
        approved=False,
    )
