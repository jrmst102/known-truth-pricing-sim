import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest


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
    subprocess.run(command, check=True, capture_output=True, text=True, timeout=60)
    output = tmp_path / "cli-smoke"
    first = pd.read_parquet(output / "estimates.parquet")
    subprocess.run(command + ["--resume"], check=True, capture_output=True, text=True, timeout=60)
    pd.testing.assert_frame_equal(first, pd.read_parquet(output / "estimates.parquet"))
    assert (output / "report.md").exists()
    import json

    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["stage"] == "validation"
    assert manifest["seed_child_index"] == 0
    assert manifest["protocol_version"] == "1.1"
    assert len(manifest["figures"]) == 5
    assert manifest["calibration_ids"]


def test_real_data_requires_clean_commit(tmp_path, monkeypatch, capsys):
    from ktsim import cli

    monkeypatch.setattr(
        sys, "argv", ["run_pilot.py", "--stage", "diagnostic", "--output-root", str(tmp_path)]
    )

    def git_output(command, **kwargs):
        if command == ["git", "rev-parse", "HEAD"]:
            return "a" * 40 + "\n"
        assert command == ["git", "status", "--porcelain"]
        return " M tracked-file.py\n"

    def forbidden(*args, **kwargs):
        pytest.fail("Dirty scientific run reached configuration or simulation")

    monkeypatch.setattr(cli.subprocess, "check_output", git_output)
    monkeypatch.setattr(cli, "read_config", forbidden)
    monkeypatch.setattr(cli, "run_pilot", forbidden)
    with pytest.raises(SystemExit) as result:
        cli.pilot_main()
    assert result.value.code == 2
    assert "Working tree is dirty" in capsys.readouterr().err
    assert not list(tmp_path.iterdir())


def test_committed_calendar():
    from ktsim.io import week_table

    weeks = week_table(Path("data/fixtures/week_decode.csv"))
    assert len(weeks) == 400
    assert weeks.holiday_easter.sum() == 8
    assert weeks.lent.sum() == 32
