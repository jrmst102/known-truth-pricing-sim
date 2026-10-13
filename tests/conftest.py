from pathlib import Path

import pytest

from ktsim.config import Calibration, DGMConfig


@pytest.fixture
def cal():
    return Calibration.load(Path(__file__).parents[1] / "data/fixtures/calibration_synthetic.json")


@pytest.fixture
def dgm():
    return DGMConfig(store_zones={store: 1 if store <= 4 else 2 for store in range(1, 9)})