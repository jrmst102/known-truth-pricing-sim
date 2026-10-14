from dataclasses import asdict
from pathlib import Path

import yaml

from ktsim.cli import expand_cells, protocol_version
from ktsim.config import DGMConfig


def test_baseline_and_grid():
    config = yaml.safe_load(Path("configs/dgm_base.yaml").read_text())
    dgm = DGMConfig(**config)
    raw = yaml.safe_load(Path("configs/scenarios.yaml").read_text())
    cells = expand_cells(raw, dgm, ["all"])
    assert len(cells) == 81
    assert {c.environment for c in cells} == {"sna", "tna", "tti"}
    assert {c.eta for c in cells} == {-0.8, -1.06, -2.5}
    assert {c.kappa for c in cells} == {-0.05, 0, 0.05}
    assert {c.phi for c in cells} == set(dgm.phi_levels)
    assert (dgm.history_weeks, dgm.cycles, dgm.rho_xi, dgm.xi_share) == (52, 104, 0.5, 0.5)
    assert dgm.cost_shifter["structure"] == "iid_store_week"
    assert dgm.sales_process == "latent" and dgm.shock_split == "design"
    assert dgm.reliability == {"tau": 0.02, "window": 26}
    assert dgm.feasible_band == {"lower": 0.8, "upper": 1.2}
    assert dgm.ladder_step == 0.05 and dgm.exploration == {"delta": 0.03, "decay_power": -0.25}
    assert raw["protocol_version"] == protocol_version() == "1.1"
    protocol = Path("docs/PROTOCOL_v1.1.md").read_text()
    spec = Path("docs/SPEC_v1.1.md").read_text()
    table = spec[spec.index("| Component |") : spec.index("\nEverything in this table")]
    assert table in protocol
    assert all(asdict(c)["sales_process"] == "latent" for c in cells)
    diagnostic = expand_cells(raw, dgm, ["all"], stage="diagnostic")
    assert sum(c.reps for c in diagnostic) == 93


def test_no_unreferenced_yaml_keys():
    source = "\n".join(p.read_text() for p in Path("src").rglob("*.py"))
    # Mapping labels (cells, categories, levels, named extensions) are data, not options.
    labels = {"cells", "extensions", "eta_levels", "kappa_levels", "stages"}

    def check(value, parent=""):
        if not isinstance(value, dict):
            return
        for key, child in value.items():
            if parent not in labels and key not in {"low", "med", "high", "none", "pos", "neg"}:
                assert key in source, f"Unread config key: {key}"
            check(child, key)

    for path in Path("configs").glob("*.yaml"):
        check(yaml.safe_load(path.read_text()))
