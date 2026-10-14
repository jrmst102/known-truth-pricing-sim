"""Record eligibility denominators and mutually exclusive missing-row causes."""

import numpy as np
import pandas as pd


def audit_coverage(movement, upc, stores, cfg, calendar=None):
    keys = ["upc", "store", "week"]
    duplicates = movement[movement.duplicated(keys, keep=False)][keys].drop_duplicates()
    frame = movement
    steps = [{"rule": "raw", "stores": int(frame.store.nunique()), "rows": len(frame)}]
    for rule, mask in [
        ("OK == 1", frame.ok.eq(1)),
    ]:
        frame = frame[mask]
        steps.append(dict(rule=rule, stores=int(frame.store.nunique()), rows=len(frame)))
    frame = frame[frame.price.gt(0) & frame.qty.gt(0) & frame.move.ge(0)]
    steps.append(
        dict(rule="valid price/qty/move", stores=int(frame.store.nunique()), rows=len(frame))
    )
    metadata = stores.dropna(subset=["zone", "price_tier"])
    frame = frame[frame.store.isin(metadata.store) & frame.upc.isin(upc.upc)]
    steps.append(
        dict(rule="known UPC and zoned store", stores=int(frame.store.nunique()), rows=len(frame))
    )
    if frame.empty:
        raise ValueError("No valid movement rows")
    low, high = int(frame.week.min()), int(frame.week.max())
    span = high - low + 1
    coverage = frame.groupby("store").week.nunique() / span
    threshold = cfg.store_coverage_min
    if sum(coverage >= threshold) < cfg.plausibility.get("retained_stores_min", 40):
        threshold = cfg.store_coverage_fallback
    retained = coverage[coverage >= threshold].index
    frame = frame[frame.store.isin(retained)]
    steps.append(dict(rule="store coverage", stores=len(retained), rows=len(frame)))
    expected = len(retained) * span
    grid = pd.MultiIndex.from_product([retained, range(low, high + 1)], names=["store", "week"])
    raw = movement[movement.store.isin(retained) & movement.week.between(low, high)]
    present = pd.MultiIndex.from_frame(raw[["store", "week"]].drop_duplicates())
    rows = []
    sales = frame.groupby("upc").move.sum().sort_values(ascending=False, kind="stable")
    counts = frame.groupby("upc").size()
    best_code = counts.idxmax()
    codes = list(sales.head(10).index)
    if best_code not in codes:
        codes.append(best_code)
    for code in codes:
        item = raw[raw.upc.eq(code)]
        raw_idx = pd.MultiIndex.from_frame(item[["store", "week"]].drop_duplicates())
        ok = item[item.ok.eq(1)]
        ok_idx = pd.MultiIndex.from_frame(ok[["store", "week"]].drop_duplicates())
        valid = frame[frame.upc.eq(code)]
        valid_idx = pd.MultiIndex.from_frame(valid[["store", "week"]].drop_duplicates())
        rows.append(
            dict(
                upc=int(code),
                volume=float(sales.loc[code]),
                rows_present=len(valid_idx),
                expected_rows=expected,
                coverage=len(valid_idx) / expected,
                missing_by_cause=dict(
                    store_absent=len(grid.difference(present)),
                    upc_absent=len(grid.intersection(present).difference(raw_idx)),
                    ok_zero=len(grid.intersection(raw_idx).difference(ok_idx)),
                    price_qty_rule=len(grid.intersection(ok_idx).difference(valid_idx)),
                ),
            )
        )
    alignment = {}
    if calendar is not None:
        alignment = dict(
            missing_weeks=sorted(set(range(low, high + 1)) - set(calendar.week)),
            first=calendar[calendar.week.eq(low)].astype(str).to_dict("records"),
            last=calendar[calendar.week.eq(high)].astype(str).to_dict("records"),
        )
    return dict(
        week_range=[low, high],
        calendar_span=span,
        equals_399=span == 399,
        store_coverage_threshold=threshold,
        store_steps=steps,
        n_retained_stores=len(retained),
        retained_stores=sorted(map(int, retained)),
        top_upcs=rows[:10],
        best_upc=next(row for row in rows if row["upc"] == best_code),
        duplicates=duplicates.astype(int).to_dict("records"),
        date_alignment=alignment,
    )


def candidate_windows(movement, upc, stores, cfg, min_weeks=156):
    """Enumerate longest eligible spans without changing the 90% UPC threshold.

    Candidate ranking uses full-file retained stores; each candidate must subsequently
    pass the complete cleaning rules on its own window (including competitor coverage).
    """
    audit = audit_coverage(movement, upc, stores, cfg)
    valid = movement[
        movement.store.isin(audit["retained_stores"])
        & movement.ok.eq(1)
        & movement.price.gt(0)
        & movement.qty.gt(0)
        & movement.move.ge(0)
    ]
    low, high = audit["week_range"]
    counts = (
        valid.groupby(["upc", "week"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=range(low, high + 1), fill_value=0)
        .to_numpy()
    )
    cumulative = np.pad(np.cumsum(counts, axis=1), ((0, 0), (1, 0)))
    for length in range(high - low + 1, min_weeks - 1, -1):
        totals = cumulative[:, length:] - cumulative[:, :-length]
        eligible = (totals >= cfg.upc_coverage_min * audit["n_retained_stores"] * length).any(
            axis=0
        )
        for start in np.flatnonzero(eligible):
            yield [int(low + start), int(low + start + length - 1)]


def audit_markdown(audit, category):
    lines = [
        f"# Coverage audit: {category}",
        "",
        f"Calendar range: {audit['week_range']}; "
        f"span {audit['calendar_span']} weeks; equals 399: {audit['equals_399']}.",
        f"Retained stores: {audit['n_retained_stores']}. Duplicates: {len(audit['duplicates'])}.",
        "",
        "| UPC | Rows present | Expected | Coverage | Missing by cause |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in audit["top_upcs"]:
        lines.append(
            f"| {row['upc']} | {row['rows_present']} | {row['expected_rows']} | "
            f"{row['coverage']:.6f} | {row['missing_by_cause']} |"
        )
    lines += [
        "",
        f"Best coverage across every UPC: {audit['best_upc']}",
        "",
        f"Store rules: {audit['store_steps']}",
        "",
        f"Date alignment: {audit['date_alignment']}",
    ]
    return "\n".join(lines) + "\n"
