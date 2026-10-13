from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class CalibrationConfig:
    store_coverage_min: float = 0.8
    store_coverage_fallback: float = 0.7
    upc_coverage_min: float = 0.9
    zero_share_max: float = 0.1
    harmonics: int = 2
    rho_xi_bounds: list[float] = field(default_factory=lambda: [0.2, 0.9])
    xi_share_max: float = 0.9
    plausibility: dict = field(default_factory=dict)


@dataclass
class Calibration:
    alpha_s: dict[int, float]
    season: dict[str, list[float]]
    holiday: dict[str, float]
    promo_effect: float
    rho_xi: float
    sigma_xi2: float
    sigma_eps2: float
    p_bar: float
    mu_z: dict[int, float]
    sigma_nu2: float
    pi_promo: float
    promo_depth: dict[str, float]
    sigma_comp: float
    unit_cost: float
    price_dispersion: dict
    beta_reference: float
    n_stores: int
    n_store_weeks: int
    zero_share: float
    focal_upc: int
    weeks: list[int]

    @classmethod
    def load(cls, path: str | Path) -> Calibration:
        data = json.loads(Path(path).read_text())
        for key in ("alpha_s", "mu_z"):
            data[key] = {int(store): value for store, value in data[key].items()}
        return cls(**data)

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(asdict(self), indent=2, allow_nan=False) + "\n")


@dataclass
class DGMConfig:
    feasible_band: dict = field(default_factory=lambda: {"lower": 0.8, "upper": 1.2})
    ladder_step: float = 0.05
    cross_price_coef: float = 0.2
    comp_index: dict = field(default_factory=lambda: {"rho": 0.8})
    cost_shifter: dict = field(default_factory=lambda: {"rho": 0.8, "sd": 0.05})
    zone_drift: dict = field(default_factory=lambda: {"rho": 0.9})
    kappa_levels: dict = field(default_factory=lambda: {"none": 0.0, "pos": 0.05, "neg": -0.05})
    exploration: dict = field(default_factory=lambda: {"decay_power": -0.25})
    censoring: dict = field(default_factory=lambda: {"multiplier": 1.5})
    history_weeks: int = 52
    cycles: int = 104
    rho_m_levels: list = field(default_factory=lambda: [0.0, 0.5])
    eta_levels: dict = field(default_factory=lambda: {"low": -0.8, "med": -1.06, "high": -2.5})
    phi_levels: list = field(default_factory=lambda: [0.0, 0.5, 1.0])
    store_zones: dict[int, int] = field(default_factory=dict)
    calendar: object = None


@dataclass
class CellConfig:
    name: str
    eta: float
    kappa: float
    phi: float
    delta: float
    reps: int
    estimators: list[str] = field(default_factory=list)
    policies: list[str] = field(default_factory=list)
    pass_through: float = 0.2
    multiplier: float = 1.5
    rho_m: float = 0.0
    data_only: bool = False

    @property
    def label(self) -> str:
        if self.name == "P4":
            return f"P4:pass_through={self.pass_through:g}"
        if self.name == "P5":
            return f"P5:multiplier={self.multiplier:g}"
        return self.name
