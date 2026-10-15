import re
from pathlib import Path

import yaml

from ktsim.cli import read_config, resolve_calibration
from ktsim.config import CalibrationConfig, DGMConfig
from ktsim.protocol import scenario_cells, validate_protocol


def test_config_baseline_and_protocol():
    raw = read_config("configs/scenarios.yaml")
    dgm = DGMConfig(**read_config("configs/dgm_base.yaml"))
    CalibrationConfig(**read_config("configs/calibration.yaml"))
    assert validate_protocol(raw) == "1.1"
    assert raw["environments"] == ["sna", "tna", "tti"]
    assert raw["eta"] == list(dgm.eta_levels)
    assert set(raw["kappa"]) == set(dgm.kappa_levels)
    assert raw["phi"] == dgm.phi_levels
    assert dgm.history_weeks == 52 and dgm.cycles == 104
    assert dgm.rho_xi == 0.5 and dgm.xi_share == 0.5 and dgm.shock_split == "design"
    assert dgm.sales_process == "latent"
    assert dgm.cost_shifter["structure"] == "iid_store_week"
    assert dgm.cost_shifter["sd"] == 0.05
    assert dgm.reliability == {"tau": 0.02, "window": 26}
    assert read_config("configs/decisions.yaml")["targets"] == {
        "elasticity": 0.02,
        "regret": 0.0025,
        "paired": 0.0025,
    }
    text = Path("docs/PROTOCOL_v1.1.md").read_text()
    spec = Path("docs/SPEC_v1.1.md").read_text()
    assert spec[spec.index("| Component |") : spec.index("\n\nEverything in this table")] in text
    assert len(scenario_cells(raw, dgm, "validation")) == 81
    assert resolve_calibration("sna").name == "calibration_sna.json"


def test_every_yaml_key_has_consumer():
    # Exclude declarations and documentation: each key must occur in executable source
    # as an attribute or literal (including dynamically used cell names/levels).
    source = "\n".join(
        p.read_text()
        for folder in ("src", "scripts")
        for p in Path(folder).rglob("*.py")
        if p.name != "config.py"
    )
    dynamic_keys = {
        "none",
        "pos",
        "neg",
        "low",
        "med",
        "high",
        "P0",
        "P1",
        "P2",
        "P3",
        "P4",
        "P5",
        "censored",
        "weak",
        "other_zone",
        "empirical",
        "chainwide",
        "promo_freq",
        "promo_depth",
        "resid_sd",
        "profit_mean",
        "beta_reference",
        "retained_stores_min",
    }

    def visit(value):
        if isinstance(value, dict):
            for key, child in value.items():
                assert key in dynamic_keys or re.search(r"\b" + re.escape(key) + r"\b", source), key
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    for path in Path("configs").glob("*.yaml"):
        visit(yaml.safe_load(path.read_text()))


def test_scientific_stage_acceptance_gates(tmp_path):
    import pytest

    raw = read_config("configs/scenarios.yaml")
    path = tmp_path / "protocol.md"
    path.write_text(
        "Protocol version: 1.1\nAuthor approval: APPROVED Author/date\n"
        "Deliverable 1 acceptance: PENDING\nDeliverable 2 acceptance: PENDING\n"
    )
    with pytest.raises(ValueError, match="Deliverable 1"):
        validate_protocol(raw, scientific=True, stage="diagnostic", path=path)
    path.write_text(
        path.read_text().replace(
            "Deliverable 1 acceptance: PENDING", "Deliverable 1 acceptance: ACCEPTED Author/date"
        )
    )
    assert validate_protocol(raw, scientific=True, stage="diagnostic", path=path) == "1.1"
    with pytest.raises(ValueError, match="Deliverable 2"):
        validate_protocol(raw, scientific=True, stage="pilot", path=path)


def test_unread_key_rejected(tmp_path):
    import pytest

    raw = read_config("configs/scenarios.yaml")
    raw["unused_setting"] = 42
    path = tmp_path / "scenarios.yaml"
    path.write_text(yaml.safe_dump(raw))
    with pytest.raises(ValueError, match="Unread configuration"):
        read_config(path)
