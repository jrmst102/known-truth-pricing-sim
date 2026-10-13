from dataclasses import dataclass

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


def replication_streams(master_seed: int, n_reps: int) -> list[np.random.SeedSequence]:
    return np.random.SeedSequence(master_seed).spawn(n_reps)


def ar1(innovations, rho, sd):
    result = np.empty_like(innovations, dtype=float)
    result[..., 0] = sd * innovations[..., 0]
    for index in range(1, innovations.shape[-1]):
        result[..., index] = (
            rho * result[..., index - 1] + sd * np.sqrt(1 - rho**2) * innovations[..., index]
        )
    return result


def draw_shocks(ss, n_stores, n_weeks, cal, dgm) -> ShockArrays:
    rng = np.random.Generator(np.random.PCG64(ss))
    return ShockArrays(
        omega=rng.standard_normal((n_stores, n_weeks)),
        eps=rng.normal(0, np.sqrt(cal.sigma_eps2), (n_stores, n_weeks)),
        u=rng.choice([-1.0, 1.0], (n_stores, n_weeks)),
        cost=ar1(rng.standard_normal(n_weeks), dgm.cost_shifter["rho"], dgm.cost_shifter["sd"]),
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
