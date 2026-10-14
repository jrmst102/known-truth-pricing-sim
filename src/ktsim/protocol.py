"""Protocol validation and explicit scientific scenario expansion."""

import re
from itertools import product
from pathlib import Path

from ktsim.config import CellConfig

PROTOCOL_VERSION = "1.1"
SPEC_VERSION = "1.1"


def validate_protocol(raw, *, scientific=False, stage=None, path="docs/PROTOCOL_v1.1.md"):
    text = Path(path).read_text()
    match = re.search(r"^Protocol version: ([0-9.]+)", text, re.MULTILINE)
    if (
        not match
        or match.group(1) != raw["protocol_version"]
        or (raw["protocol_version"] != PROTOCOL_VERSION or raw["spec_version"] != SPEC_VERSION)
    ):
        raise ValueError("Protocol/spec version mismatch")
    if scientific and not re.search(r"^Author approval: APPROVED .+", text, re.MULTILINE):
        raise ValueError("Author sign-off pending in docs/PROTOCOL_v1.1.md; scientific run blocked")
    if scientific:
        required = ["Deliverable 1"]
        if stage in {"pilot", "main"}:
            required.append("Deliverable 2")
        for deliverable in required:
            if not re.search(r"^" + deliverable + r" acceptance: ACCEPTED .+", text, re.MULTILINE):
                raise ValueError(f"{deliverable} acceptance pending; scientific run blocked")
    return match.group(1)


def scenario_cells(raw, dgm, stage, selected=None, reps=None, estimators=None, n_required=None):
    if raw["phi"] != dgm.phi_levels:
        raise ValueError("Scenario phi levels drift from DGM baseline")
    definitions = raw["stages"][stage]
    count = reps if reps is not None else definitions["reps"]
    if stage == "main" and count is None:
        count = n_required
    if count is None:
        raise ValueError("Main stage requires the accepted pilot n_required decision")
    cells = []
    for env, eta, kappa, phi in product(raw["environments"], raw["eta"], raw["kappa"], raw["phi"]):
        name = f"{env}:{eta}:{kappa}:phi={phi:g}"
        if selected is not None and name not in selected:
            continue
        cells.append(
            CellConfig(
                name,
                dgm.eta_levels[eta],
                dgm.kappa_levels[kappa],
                phi,
                dgm.exploration["delta"],
                count,
                estimators or raw["estimators"],
                raw["policies"],
                pass_through=raw["pass_through"],
                environment=env,
                rho_m=dgm.rho_m,
            )
        )
        if stage == "diagnostic" and eta == "med" and kappa == "pos" and phi == 0.5:
            cells.append(
                CellConfig(
                    name + ":base-extra",
                    dgm.eta_levels[eta],
                    dgm.kappa_levels[kappa],
                    phi,
                    dgm.exploration["delta"],
                    definitions["base_extra_reps"],
                    estimators or raw["estimators"],
                    raw["policies"],
                    pass_through=raw["pass_through"],
                    environment=env,
                    rho_m=dgm.rho_m,
                    seed_offset=count,
                )
            )
    return cells


def extension_cell(raw, dgm, extension, stage, reps=None, estimators=None, n_required=None):
    definition = dict(raw["extensions"][extension])
    base = definition.pop("base")
    instrument = definition.pop("instrument", "cost_shifter")
    cells = [
        cell
        for cell in scenario_cells(raw, dgm, stage, [base], reps, estimators, n_required)
        if cell.name == base
    ]
    if len(cells) != 1:
        raise ValueError("Extension must reference exactly one base cell")
    cell = cells[0]
    cell.name += ":extension=" + extension
    for key, value in definition.items():
        if key not in {"sales_process", "pass_through", "shock_split", "cost_structure"}:
            raise ValueError(f"Unknown extension key {key}")
        setattr(cell, key, value)
    return [cell], instrument
