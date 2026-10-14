from dataclasses import dataclass, replace

import numpy as np


@dataclass
class ShockArrays:
    omega: np.ndarray
    eps: np.ndarray
    u: np.ndarray
    cost: np.ndarray
    nu: np.ndarray
    promo: np.ndarray
    promo_depth: np.ndarray
    comp_index: np.ndarray
    common_shock: np.ndarray
    model_store_assignment: np.ndarray


STAGES = {"validation": 0, "diagnostic": 1, "pilot": 2, "main": 3}


def replication_streams(
    master_seed: int, n_reps: int, stage="validation"
) -> list[np.random.SeedSequence]:
    return np.random.SeedSequence(master_seed).spawn(4)[STAGES[stage]].spawn(n_reps)


def ar1(innovations, rho, sd):
    result = np.empty_like(innovations, dtype=float)
    result[..., 0] = sd * innovations[..., 0]
    for index in range(1, innovations.shape[-1]):
        result[..., index] = (
            rho * result[..., index - 1] + sd * np.sqrt(1 - rho**2) * innovations[..., index]
        )
    return result


def draw_shocks(ss, n_stores, n_weeks, cal, dgm) -> ShockArrays:
    if dgm.cost_shifter["structure"] not in {"iid_store_week", "chainwide_ar1"}:
        raise ValueError("Unknown cost_shifter structure")
    cal = mechanism_calibration(cal, dgm)
    rng = np.random.Generator(np.random.PCG64(ss))
    return ShockArrays(
        omega=rng.standard_normal((n_stores, n_weeks)),
        eps=rng.normal(0, np.sqrt(cal.sigma_eps2), (n_stores, n_weeks)),
        u=rng.choice([-1.0, 1.0], (n_stores, n_weeks)),
        cost=(
            rng.normal(0, dgm.cost_shifter["sd"], (n_stores, n_weeks))
            if dgm.cost_shifter["structure"] == "iid_store_week"
            else np.broadcast_to(
                ar1(rng.standard_normal(n_weeks), dgm.cost_shifter["rho"], dgm.cost_shifter["sd"]),
                (n_stores, n_weeks),
            ).copy()
        ),
        nu=ar1(
            rng.standard_normal((len(cal.mu_z), n_weeks)),
            dgm.zone_drift["rho"],
            np.sqrt(cal.sigma_nu2),
        ),
        promo=rng.binomial(1, cal.pi_promo, n_weeks),
        promo_depth=np.clip(
            rng.normal(cal.promo_depth["mean"], cal.promo_depth["sd"], n_weeks), 0.0, 0.95
        ),
        comp_index=ar1(rng.standard_normal(n_weeks), dgm.comp_index["rho"], cal.sigma_comp),
        common_shock=rng.standard_normal(n_weeks),
        model_store_assignment=rng.permutation(n_stores),
    )


def latent_demand(shocks, cal, rho_m):
    if not 0 <= rho_m <= 1:
        raise ValueError("rho_m must be in [0, 1]")
    innovations = np.sqrt(1 - rho_m) * shocks.omega + np.sqrt(rho_m) * shocks.common_shock[None, :]
    return ar1(innovations, cal.rho_xi, np.sqrt(cal.sigma_xi2))


def mechanism_calibration(cal, dgm):
    if dgm.shock_split == "empirical":
        diag = cal.diagnostics
        return replace(
            cal,
            rho_xi=diag.get("empirical_rho_xi", cal.rho_xi),
            sigma_xi2=diag.get("empirical_sigma_xi2", cal.sigma_xi2),
            sigma_eps2=diag.get("empirical_sigma_eps2", cal.sigma_eps2),
        )
    if dgm.shock_split != "design":
        raise ValueError("Unknown shock_split")
    variance = cal.diagnostics.get("resid_var", cal.sigma_xi2 + cal.sigma_eps2)
    return replace(
        cal,
        rho_xi=dgm.rho_xi,
        sigma_xi2=dgm.xi_share * variance,
        sigma_eps2=(1 - dgm.xi_share) * variance,
    )


def assign_model_stores(permutation, zones, phi):
    """Stratify once using shared random ranks, then balance the chain total."""
    zones = np.asarray(zones)
    if not 0 <= phi <= 1:
        raise ValueError("phi must be in [0, 1]")
    assigned = np.zeros(len(zones), dtype=bool)
    groups = sorted(np.unique(zones), key=lambda z: (-sum(zones == z), z))
    for zone in groups:
        candidates = permutation[zones[permutation] == zone]
        assigned[candidates[: round(phi * len(candidates))]] = True
    difference = round(phi * len(zones)) - assigned.sum()
    # Distribute corrections from the largest zone while preserving a one-store bound.
    for zone in groups:
        if difference == 0:
            break
        candidates = permutation[
            (zones[permutation] == zone) & (assigned[permutation] == (difference < 0))
        ]
        for index in candidates:
            change = 1 if difference > 0 else -1
            if abs(assigned[zones == zone].sum() + change - phi * sum(zones == zone)) > 1:
                break
            assigned[index] = difference > 0
            difference -= change
            if difference == 0:
                break
    if difference:
        raise ValueError("Cannot balance zone assignment")
    return assigned
