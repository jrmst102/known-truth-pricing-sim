import pandas as pd

from ktsim.clean import clean_category
from ktsim.config import CalibrationConfig
from ktsim.io import load_movement


def test_clean_rules():
    frame = load_movement("data/fixtures/movement_small.csv")
    frame["store"] = frame.store.astype(float)
    stores = pd.DataFrame({"store": [1, 2, 3], "zone": [1, 2, 1], "price_tier": ["L"] * 3})
    result = clean_category(
        frame,
        pd.DataFrame({"upc": [123, 456, 999]}),
        stores,
        CalibrationConfig(plausibility={"retained_stores_min": 2}),
    )
    assert result.store_ids == [1, 2]
    assert result.focal_upc == 456
    assert len(result.frame) == 8
    assert result.substituted_focal
    assert result.zero_share == 0
    assert result.frame.store.dtype.kind == "i"
    assert all(str(index) in " ".join(result.log) for index in range(1, 8))
    assert "1 OK == 1: 21 -> 20" in result.log
    assert "2 valid price/qty/move: 20 -> 19" in result.log
    assert "3 known UPC and zoned store: 19 -> 18" in result.log
    assert "4 store coverage: 18 -> 17" in result.log
    assert "5 UPC coverage: 17 -> 16" in result.log


def test_coverage_audit_numbers():
    from ktsim.coverage import audit_coverage

    frame = load_movement("data/fixtures/movement_small.csv")
    stores = pd.DataFrame({"store": [1, 2, 3], "zone": [1, 2, 1], "price_tier": ["L"] * 3})
    audit = audit_coverage(
        frame,
        pd.DataFrame({"upc": [123, 456, 999]}),
        stores,
        CalibrationConfig(plausibility={"retained_stores_min": 2}),
    )
    assert audit["calendar_span"] == 4
    assert audit["n_retained_stores"] == 2
    for row in audit["top_upcs"]:
        assert row["expected_rows"] == 8
        assert sum(row["missing_by_cause"].values()) + row["rows_present"] == 8
        assert row["coverage"] == row["rows_present"] / 8
    assert [x["rows"] for x in audit["store_steps"]] == [21, 20, 19, 18, 17]
