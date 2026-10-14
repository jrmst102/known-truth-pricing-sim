import subprocess
import sys
from pathlib import Path

import pandas as pd


def test_synthetic_cli_and_resume(tmp_path):
    command = [
        sys.executable,
        "scripts/run_pilot.py",
        "--cells",
        "sna:med:pos:phi=0.5",
        "--synthetic",
        "--reps",
        "1",
        "--cycles",
        "1",
        "--estimators",
        "M1",
        "--run-id",
        "cli-smoke",
        "--output-root",
        str(tmp_path),
    ]
    subprocess.run(command, check=True, capture_output=True, text=True)
    output = tmp_path / "cli-smoke"
    first = pd.read_parquet(output / "estimates.parquet")
    subprocess.run(command + ["--resume"], check=True, capture_output=True, text=True)
    pd.testing.assert_frame_equal(first, pd.read_parquet(output / "estimates.parquet"))
    assert (output / "report.md").exists()
    import json

    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["stage"] == "validation"
    assert manifest["seed_child_index"] == 0
    assert manifest["protocol_version"] == "1.1"
    assert len(manifest["figures"]) == 5
    assert manifest["calibration_ids"]


def test_real_data_requires_clean_commit(tmp_path):
    command = [sys.executable, "scripts/run_pilot.py", "--output-root", str(tmp_path)]
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode != 0
    assert "dirty" in result.stderr or "calibration" in result.stderr.lower()


def test_committed_calendar():
    from ktsim.io import week_table

    weeks = week_table(Path("data/fixtures/week_decode.csv"))
    assert len(weeks) == 400
    assert weeks.holiday_easter.sum() == 8
    assert weeks.lent.sum() == 32
