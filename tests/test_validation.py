import json
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest
import yaml

from ktsim.validation import check_run


@pytest.fixture(scope="module")
def saved_run(tmp_path_factory):
    root = tmp_path_factory.mktemp("saved-run-validation")
    estimators = yaml.safe_load(Path("configs/estimators.yaml").read_text())
    estimators["M4_dml"]["nuisance_params"]["n_estimators"] = 5
    config = root / "small-estimators.yaml"
    config.write_text(yaml.safe_dump(estimators))
    subprocess.run(
        [
            sys.executable,
            "scripts/run_pilot.py",
            "--synthetic",
            "--stage",
            "validation",
            "--cells",
            "sna:med:none:phi=0",
            "sna:med:pos:phi=0.5",
            "--cycles",
            "1",
            "--reps",
            "1",
            "--estimators",
            "M1",
            "M4_plr",
            "--estimator-config",
            str(config),
            "--save-data",
            "--save-storeweek",
            "--run-id",
            "short-run",
            "--output-root",
            str(root),
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    )
    return root / "short-run"


def test_current_schema_and_both_commands(saved_run):
    checks = check_run(saved_run)
    assert all(value is not False for value in checks["acceptance"].values())
    assert checks["cycles"] == 1 and checks["complete"]
    assert checks["dml_folds_recorded"] and checks["dml_coverage_withheld"]
    result = subprocess.run(
        [sys.executable, "scripts/check_validation.py", str(saved_run)],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert json.loads(result.stdout)["revenue_balanced"]
    result = subprocess.run(
        [
            sys.executable,
            "scripts/validate_v11.py",
            "--check-only",
            "--run-id",
            saved_run.name,
            "--output-root",
            str(saved_run.parent),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0
    assert "full_horizon" in result.stderr
    assert not (saved_run.parent / "short-run-estimators.yaml").exists()


@pytest.mark.parametrize("corruption", ["price", "fold_hash", "missing_audits", "missing_cycle"])
def test_corrupted_artifacts_fail(saved_run, tmp_path, corruption):
    target = tmp_path / "run"
    shutil.copytree(saved_run, target)
    if corruption == "price":
        path = target / "storeweek.parquet"
        frame = pd.read_parquet(path)
        frame.loc[0, "price"] += 0.001
        frame.to_parquet(path, index=False)
        key = "AC-C1"
    elif corruption == "fold_hash":
        path = target / "states.parquet"
        frame = pd.read_parquet(path)
        frame.loc[0, "dml_fold_assignment_hash"] = "wrong"
        frame.to_parquet(path, index=False)
        key = "AC-A7"
    elif corruption == "missing_cycle":
        path = target / "estimates.parquet"
        pd.read_parquet(path).iloc[1:].to_parquet(path, index=False)
        key = "run_complete"
    else:
        (target / "storeweek.parquet").unlink()
        shutil.rmtree(target / "simulated")
        key = "AC-C1"
    checks = check_run(target)
    assert checks["acceptance"][key] is False
