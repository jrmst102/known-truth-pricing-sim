from dataclasses import dataclass

import numpy as np
import pandas as pd

from ktsim.config import CalibrationConfig


@dataclass
class CleanResult:
    frame: pd.DataFrame
    focal_upc: int
    store_ids: list[int]
    zero_share: float
    substituted_focal: bool
    log: list[str]


def clean_category(
    movement: pd.DataFrame,
    upc: pd.DataFrame,
    stores: pd.DataFrame,
    cfg: CalibrationConfig,
    *,
    week_range=None,
) -> CleanResult:
    frame = movement.copy()
    log = []

    def retain(mask, rule):
        nonlocal frame
        before = len(frame)
        frame = frame.loc[mask].copy()
        log.append(f"{rule}: {before} -> {len(frame)}")

    retain(frame.ok.eq(1), "1 OK == 1")
    retain(frame.price.gt(0) & frame.qty.gt(0) & frame.move.ge(0), "2 valid price/qty/move")
    if not {"store", "zone", "price_tier"}.issubset(stores):
        raise ValueError(
            "Store metadata requires store, zone, price_tier; use the codebook importer"
        )
    metadata = stores.dropna(subset=["zone", "price_tier"])
    retain(
        frame.store.isin(metadata.store) & frame.upc.isin(upc.upc), "3 known UPC and zoned store"
    )
    for column in ("store", "upc", "week"):
        if frame[column].isna().any() or not np.equal(frame[column], np.floor(frame[column])).all():
            raise ValueError(f"Invalid noninteger identifiers in {column}")
        frame[column] = frame[column].astype(int)
    if frame.duplicated(["store", "upc", "week"]).any():
        raise ValueError("Duplicate store-UPC-week observations")
    if frame.empty:
        raise ValueError("No valid movement rows")
    low, high = week_range or (int(frame.week.min()), int(frame.week.max()))
    if not frame.week.between(low, high).all():
        raise ValueError("Movement rows outside the selected calibration window")
    n_weeks = high - low + 1
    coverage = frame.groupby("store").week.nunique() / n_weeks
    threshold = cfg.store_coverage_min
    minimum = cfg.plausibility.get("retained_stores_min", 40)
    if (coverage >= threshold).sum() < minimum:
        threshold = cfg.store_coverage_fallback
        log.append(f"Store coverage fallback: {threshold}")
    retain(frame.store.isin(coverage[coverage >= threshold].index), "4 store coverage")
    if frame.empty:
        raise ValueError("No stores satisfy coverage threshold")
    log.append(
        f"Coverage denominator: weeks {low}-{high}; "
        f"span {n_weeks}; retained stores {frame.store.nunique()}"
    )
    n_retained = frame.store.nunique()
    presence = frame.groupby("upc").size() / (n_retained * n_weeks)
    sales = frame.groupby("upc").move.sum().sort_values(ascending=False, kind="stable")
    initial = int(sales.index[0])
    eligible = presence[presence >= cfg.upc_coverage_min].index
    retain(frame.upc.isin(eligible), "5 UPC coverage")
    if frame.empty:
        raise ValueError(
            f"No UPC satisfies coverage threshold {cfg.upc_coverage_min:.0%}; "
            f"best UPC coverage {presence.max():.1%}, {n_retained} stores, "
            f"{n_weeks} weeks. No automatic threshold change."
        )
    candidates = [int(code) for code in sales.index if code in eligible]
    focal = None
    zero_share = np.nan
    for code in candidates:
        subset = frame[frame.upc.eq(code)]
        zero_share = float(subset.move.eq(0).mean())
        if zero_share <= cfg.zero_share_max:
            focal = code
            break
    if focal is None:
        raise ValueError("All eligible focal UPCs exceed zero_share_max")
    competing = frame[frame.upc.ne(focal)].copy()
    if competing.empty:
        raise ValueError("No competing UPC remains for the competing-price index")
    competing["log_unit_price"] = np.log(competing.price / competing.qty)
    competing["centered"] = competing.log_unit_price - competing.groupby(
        "upc"
    ).log_unit_price.transform("mean")
    comp_index = competing.groupby("week").centered.mean()
    retain(frame.upc.eq(focal), "6 focal UPC selection and zero-share substitution")
    log.append(
        f"Focal UPC rows before zero removal: {len(frame)}; "
        f"expected {frame.store.nunique() * n_weeks}"
    )
    frame["log_comp_index"] = frame.week.map(comp_index)
    if frame.log_comp_index.isna().any():
        raise ValueError("Missing competitor index weeks; author-approved fallback required")
    frame = frame.merge(metadata, on="store", validate="many_to_one")
    frame["price"] = frame.price / frame.qty
    frame["q"] = frame.move
    retain(frame.q.gt(0), "7 remove zero sales before log regression")
    frame["log_q"] = np.log(frame.q)
    frame["promo"] = frame.sale.fillna("").astype(str).str.strip().ne("").astype(float)
    return CleanResult(
        frame.sort_values(["store", "week"]).reset_index(drop=True),
        focal,
        sorted(int(store) for store in frame.store.unique()),
        zero_share,
        focal != initial,
        log,
    )
