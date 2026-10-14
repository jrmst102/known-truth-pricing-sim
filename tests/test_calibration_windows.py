import json
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest

from ktsim.audit import coverage_audit
from ktsim.calibration_windows import load_calibration_windows
from ktsim.clean import clean_category
from ktsim.config import CalibrationConfig
from ktsim.io import load_movement, sha256


def test_explicit_denominator_includes_missing_boundary_week():
    frame = load_movement("data/fixtures/movement_small.csv")
    upcs = pd.DataFrame({"upc": [123, 456, 999]})
    stores = pd.DataFrame({"store": [1, 2, 3], "zone": [1, 2, 1], "price_tier": ["L"] * 3})
    cfg = CalibrationConfig(plausibility={"retained_stores_min": 2})
    audit = coverage_audit(frame, upcs, stores, cfg, week_range=[1, 5])
    assert audit["calendar_span"] == 5
    assert audit["top_upcs"][0]["expected_rows"] == 10
    with pytest.raises(ValueError, match="coverage threshold"):
        clean_category(frame, upcs, stores, cfg, week_range=[1, 5])


@pytest.mark.parametrize(
    "window",
    [
        dict(week_range=[1, 155]),
        dict(week_range=[341, 1]),
        dict(week_range=[True, 341]),
        dict(week_range=[1, 341], length=340),
    ],
)
def test_invalid_window_rejected(tmp_path, window):
    path = tmp_path / "windows.json"
    path.write_text(json.dumps({"tna": window}))
    with pytest.raises(ValueError):
        load_calibration_windows(path)


def test_cli_applies_window_and_preserves_full_audit(tmp_path):
    # Synthetic category: two UPCs cover 330 weeks; a third spans the tail.
    # Full-sample UPC coverage fails, but the explicitly selected window passes.
    rng = np.random.default_rng(31)
    rows = []
    for store in range(1, 41):
        for week in range(1, 400):
            promo = week % 7 == 0
            for upc in [1, 2] if week <= 330 else [3] if week >= 342 else []:
                price = (
                    3 - 0.3 * promo + rng.normal(0, 0.05)
                    if upc == 1
                    else 2 + rng.normal(0, 0.03)
                    if upc == 2
                    else 1000
                )
                move = (
                    np.exp(4 - 0.35 * (price - 3) + 0.2 * promo + rng.normal(0, 0.1))
                    if upc == 1
                    else 2
                )
                rows.append(
                    dict(
                        store=store,
                        week=week,
                        upc=upc,
                        price=price,
                        qty=1,
                        move=move,
                        profit=25,
                        sale="S" if promo else "",
                        ok=1,
                    )
                )
    movement = pd.DataFrame(rows)
    movement.to_csv(tmp_path / "wtna.csv", index=False)
    pd.DataFrame({"upc": [1, 2, 3]}).to_csv(tmp_path / "upctna.csv", index=False)
    stores = tmp_path / "stores.csv"
    pd.DataFrame({"store": range(1, 41), "zone": [1, 2] * 20, "price_tier": ["L"] * 40}).to_csv(
        stores, index=False
    )
    out = tmp_path / "calibration"
    out.mkdir()
    windows = out / "calibration_windows.json"
    windows.write_text(json.dumps({"tna": {"week_range": [1, 341], "length": 341}}))
    (out / "calibration_failures.json").write_text(json.dumps({"tna": "old full-span failure"}))
    command = [
        sys.executable,
        "scripts/run_calibration.py",
        "--categories",
        "tna",
        "--data-dir",
        str(tmp_path),
        "--stores",
        str(stores),
    ]
    subprocess.run(command, check=True, capture_output=True, text=True, timeout=60)
    full = json.loads((out / "coverage_audit_tna.json").read_text())
    selected = json.loads((out / "coverage_audit_tna_window.json").read_text())
    cal = json.loads((out / "calibration_tna.json").read_text())
    assert full["week_range"] == [1, 399] and full["best_coverage"] < 0.9
    assert selected["week_range"] == [1, 341] and selected["calendar_span"] == 341
    assert selected["best_coverage"] >= 0.9
    assert cal["n_stores"] == 40 and cal["weeks"] == [1, 330]
    assert cal["diagnostics"]["calibration_window"]["week_range"] == [1, 341]
    assert cal["p_bar"] == pytest.approx(movement[movement.upc.eq(1)].price.mean())
    assert json.loads((out / "calibration_failures.json").read_text()) == {}
    assert json.loads((out / "checksums.json").read_text())[str(windows)] == sha256(windows)
    subprocess.run(command, check=True, capture_output=True, text=True, timeout=60)
    repeated = json.loads((out / "calibration_tna.json").read_text())
    assert repeated["p_bar"] == cal["p_bar"] and repeated["n_store_weeks"] == cal["n_store_weeks"]
    assert "weeks 1-341" in (out / "calibration_log.md").read_text()
