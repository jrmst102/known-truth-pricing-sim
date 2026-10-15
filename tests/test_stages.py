import numpy as np
import pytest

from ktsim.cli import read_config
from ktsim.protocol import scenario_cells, validate_protocol
from ktsim.rng import replication_streams


def test_stage_seed_separation(dgm):
    values = [
        replication_streams(42, 2, stage)[0].generate_state(8)
        for stage in ("validation", "diagnostic", "pilot", "main")
    ]
    for i, first in enumerate(values):
        for second in values[i + 1 :]:
            assert not np.array_equal(first, second)
    raw = read_config("configs/scenarios.yaml")
    assert len(scenario_cells(raw, dgm, "pilot")) == 81
    diagnostic = scenario_cells(raw, dgm, "diagnostic")
    assert len(diagnostic) == 84
    assert all(cell.seed_offset == 1 for cell in diagnostic if ":base-extra" in cell.name)
    raw["environments"] = ["sna", "tti"]
    assert len(scenario_cells(raw, dgm, "pilot")) == 54
    with pytest.raises(ValueError, match="requires"):
        scenario_cells(raw, dgm, "main")
    raw["protocol_version"] = "1.0"
    with pytest.raises(ValueError, match="mismatch"):
        validate_protocol(raw)


def test_extensions_keep_one_named_base(dgm):
    from ktsim.protocol import extension_cell

    raw = read_config("configs/scenarios.yaml")
    for stage in ("validation", "diagnostic", "pilot", "main"):
        cells, instrument = extension_cell(raw, dgm, "other_zone", stage, n_required=150)
        assert len(cells) == 1
        assert instrument == "other_zone_price"
        assert cells[0].name == "sna:med:pos:phi=0.5:extension=other_zone"
