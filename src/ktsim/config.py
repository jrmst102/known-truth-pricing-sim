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
    diagnostics: dict = field(default_factory=dict)

    @property
    def resid_var(self):
        return self.diagnostics.get("resid_var", self.sigma_xi2 + self.sigma_eps2)

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
    cost_shifter: dict = field(
        default_factory=lambda: {"structure": "iid_store_week", "rho": 0.8, "sd": 0.05}
    )
    zone_drift: dict = field(default_factory=lambda: {"rho": 0.9})
    kappa_levels: dict = field(default_factory=lambda: {"none": 0.0, "pos": 0.05, "neg": -0.05})
    exploration: dict = field(default_factory=lambda: {"delta": 0.03, "decay_power": -0.25})
    censoring: dict = field(default_factory=lambda: {"multiplier": 1.5})
    history_weeks: int = 52
    cycles: int = 104
    rho_m: float = 0.0
    rho_xi: float = 0.5
    xi_share: float = 0.5
    shock_split: str = "design"
    sales_process: str = "latent"
    reliability: dict = field(default_factory=lambda: {"tau": 0.02, "window": 26})
    eta_levels: dict = field(default_factory=lambda: {"low": -0.8, "med": -1.06, "high": -2.5})
    phi_levels: list = field(default_factory=lambda: [0.0, 0.5, 1.0])
    store_zones: dict[int, int] = field(default_factory=dict)
    calendar: object = None

    def __post_init__(self):
        if self.cost_shifter["structure"] not in {"iid_store_week", "chainwide_ar1"}:
            raise ValueError("Unknown cost_shifter.structure")
        if self.shock_split not in {"design", "empirical"}:
            raise ValueError("Unknown shock_split")
        if self.sales_process not in {"latent", "censored"}:
            raise ValueError("Unknown sales_process")
        if not 0 <= self.xi_share <= 1 or not -1 < self.rho_xi < 1:
            raise ValueError("Invalid shock parameters")


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
    seed_offset: int = 0
    environment: str = "synthetic"
    sales_process: str | None = None
    cost_structure: str | None = None
    shock_split: str | None = None

    @property
    def label(self) -> str:
        if self.name == "P4":
            return f"P4:pass_through={self.pass_through:g}"
        if self.name == "P5":
            return f"P5:multiplier={self.multiplier:g}"
        return self.name
