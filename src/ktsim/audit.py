"""Coverage eligibility audits; aggregate counts only, never redistribute movement data."""

import numpy as np
import pandas as pd


def coverage_audit(movement, upc, stores, cfg, calendar=None):
    counts = []
    frame = movement.copy()
    duplicates = int(frame.duplicated(["upc", "store", "week"]).sum())

    def retain(mask, rule):
        nonlocal frame
        before = frame.store.nunique()
        frame = frame.loc[mask].copy()
        counts.append(
            dict(
                rule=rule,
                stores_before=int(before),
                stores_after=int(frame.store.nunique()),
                rows_after=len(frame),
            )
        )

    retain(frame.ok.eq(1), "OK == 1")
    retain(frame.price.gt(0) & frame.qty.gt(0) & frame.move.ge(0), "valid price/qty/move")
    metadata = stores.dropna(subset=["zone", "price_tier"])
    retain(frame.store.isin(metadata.store) & frame.upc.isin(upc.upc), "known UPC and zoned store")
    if frame.empty:
        raise ValueError("No rows available for coverage audit")
    start, end = int(frame.week.min()), int(frame.week.max())
    span = end - start + 1
    coverage = frame.groupby("store").week.nunique() / span
    threshold = cfg.store_coverage_min
    if (coverage >= threshold).sum() < cfg.plausibility.get("retained_stores_min", 40):
        threshold = cfg.store_coverage_fallback
    retain(frame.store.isin(coverage[coverage >= threshold].index), "store coverage")
    store_ids = sorted(int(v) for v in frame.store.unique())
    if not store_ids:
        raise ValueError("No retained stores for coverage audit")
    grid = pd.MultiIndex.from_product([store_ids, range(start, end + 1)], names=["store", "week"])
    raw = movement[movement.store.isin(store_ids) & movement.week.between(start, end)]
    present = grid.isin(pd.MultiIndex.from_frame(raw[["store", "week"]]))
    top = frame.groupby("upc").move.sum().sort_values(ascending=False, kind="stable").head(10)
    rows = []
    for code, volume in top.items():
        raw_upc = raw[raw.upc.eq(code)]
        exists = grid.isin(pd.MultiIndex.from_frame(raw_upc[["store", "week"]]))
        ok_rows = raw_upc[raw_upc.ok.eq(1)]
        ok = grid.isin(pd.MultiIndex.from_frame(ok_rows[["store", "week"]]))
        valid = ok_rows[ok_rows.price.gt(0) & ok_rows.qty.gt(0) & ok_rows.move.ge(0)]
        good = grid.isin(pd.MultiIndex.from_frame(valid[["store", "week"]]))
        rows.append(
            dict(
                upc=int(code),
                volume=float(volume),
                rows_present=int(good.sum()),
                expected_rows=len(grid),
                coverage=float(good.mean()),
                missing_store_absent=int((~present).sum()),
                missing_upc_absent=int((present & ~exists).sum()),
                dropped_ok=int((exists & ~ok).sum()),
                dropped_price_qty_move=int((ok & ~good).sum()),
            )
        )
    alignment = dict(week_min=start, week_max=end, all_weeks_in_calendar=None)
    if calendar is not None:
        alignment.update(
            all_weeks_in_calendar=bool(movement.week.isin(calendar.week).all()),
            start_date=str(calendar.set_index("week").loc[start, "date"]),
            end_date=str(calendar.set_index("week").loc[end, "date"]),
            date_basis="week joined to authoritative codebook calendar; "
            "movement supplies week IDs, not independent dates",
        )
    return dict(
        week_range=[start, end],
        calendar_span=span,
        equals_399_weeks=span == 399,
        retained_stores=len(store_ids),
        store_ids=store_ids,
        store_coverage_threshold=threshold,
        retained_after_rules=counts,
        duplicate_rows=duplicates,
        date_alignment=alignment,
        top_upcs=rows,
        best_coverage=float(frame.groupby("upc").size().max() / len(grid)),
        threshold=cfg.upc_coverage_min,
    )


def candidate_window(movement, upc, stores, cfg, minimum_weeks=156, minimum_stores=40):
    """Search longest windows first; reapply store coverage within each window.

    A returned candidate is a proposal, not authorization to change the sample.
    UPC eligibility and competitor availability must still pass clean_category.
    """
    frame = movement[
        movement.ok.eq(1)
        & movement.price.gt(0)
        & movement.qty.gt(0)
        & movement.move.ge(0)
        & movement.upc.isin(upc.upc)
        & movement.store.isin(stores.dropna(subset=["zone", "price_tier"]).store)
    ]
    start, end = int(frame.week.min()), int(frame.week.max())
    ids = sorted(frame.store.unique())
    week_ids = list(range(start, end + 1))
    active = (
        pd.crosstab(frame.store, frame.week)
        .reindex(index=ids, columns=week_ids, fill_value=0)
        .to_numpy()
        > 0
    ).astype(int)
    activity = np.pad(active.cumsum(axis=1), ((0, 0), (1, 0)))
    top = frame.groupby("upc").move.sum().sort_values(ascending=False, kind="stable")
    matrices = []
    for code in top.index:
        subset = frame[frame.upc.eq(code)]
        a = (
            pd.crosstab(subset.store, subset.week)
            .reindex(index=ids, columns=week_ids, fill_value=0)
            .to_numpy()
        )
        matrices.append(np.pad((a > 0).cumsum(axis=1), ((0, 0), (1, 0))))
    matrices = np.asarray(matrices)
    from ktsim.clean import clean_category

    for length in range(len(week_ids), minimum_weeks - 1, -1):
        for left in range(len(week_ids) - length + 1):
            right = left + length
            store_coverage = (activity[:, right] - activity[:, left]) / length
            threshold = cfg.store_coverage_min
            if (store_coverage >= threshold).sum() < minimum_stores:
                threshold = cfg.store_coverage_fallback
            keep = store_coverage >= threshold
            if keep.sum() < minimum_stores:
                continue
            ratios = (matrices[:, keep, right] - matrices[:, keep, left]).sum(axis=1) / (
                keep.sum() * length
            )
            if (ratios >= cfg.upc_coverage_min).sum() < 2:
                continue
            lo, hi = start + left, start + right - 1
            try:
                clean = clean_category(movement[movement.week.between(lo, hi)], upc, stores, cfg)
            except ValueError:
                continue
            if len(clean.store_ids) < minimum_stores:
                continue
            code = clean.focal_upc
            return dict(
                week_range=[lo, hi],
                weeks=length,
                n_stores=len(clean.store_ids),
                upc=int(code),
                coverage=float(ratios[list(top.index).index(code)]),
                status="candidate; author sample review pending",
                competing_index_validated=True,
            )
    return None


def audit_markdown(audit, category):
    import json

    def table(records):
        if not records:
            return "No rows.\n"
        columns = list(records[0])
        return (
            "\n".join(
                [
                    "| " + " | ".join(columns) + " |",
                    "| " + " | ".join(["---"] * len(columns)) + " |",
                ]
                + [
                    "| " + " | ".join(str(record.get(key, "")) for key in columns) + " |"
                    for record in records
                ]
            )
            + "\n"
        )

    return (
        f"# Coverage audit: {category}\n\n"
        f"Metadata scope: {audit.get('metadata_scope', 'unspecified')}; "
        f"source: {audit.get('metadata_source', 'unspecified')}.\n\n"
        f"Calendar span: {audit['calendar_span']}; week range: {audit['week_range']}; "
        f"retained stores: {audit['retained_stores']}; duplicate rows: {audit['duplicate_rows']}.\n\n"
        f"Best coverage: {audit['best_coverage']:.6%}; threshold: {audit['threshold']:.0%}.\n\n"
        "## Store retention\n\n" + table(audit["retained_after_rules"]) + "\n"
        "## Top ten UPCs and missing-record causes\n\n" + table(audit["top_upcs"]) + "\n"
        "## Date alignment\n\n```json\n"
        + json.dumps(audit["date_alignment"], indent=2)
        + "\n```\n\n## Window proposal\n\n```json\n"
        + json.dumps(audit.get("candidate_window"), indent=2)
        + "\n```\n\n"
        "A proposal does not change the sample or authorize a scientific run.\n"
    )
