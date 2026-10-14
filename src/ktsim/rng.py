from dataclasses import dataclass

import numpy as np

STAGES = ("validation", "diagnostic", "pilot", "main")


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


def replication_streams(master_seed: int, n_reps: int, stage="validation"):
    child = np.random.SeedSequence(master_seed).spawn(4)[STAGES.index(stage)]
    return child.spawn(n_reps)


def ar1(innovations, rho, sd):
    result = np.empty_like(innovations, dtype=float)
    result[..., 0] = sd * innovations[..., 0]
    for index in range(1, innovations.shape[-1]):
        result[..., index] = (
            rho * result[..., index - 1] + sd * np.sqrt(1 - rho**2) * innovations[..., index]
        )
    return result


def shock_parameters(cal, dgm):
    if dgm.shock_split == "design":
        return dgm.rho_xi, dgm.xi_share * cal.resid_var, (1 - dgm.xi_share) * cal.resid_var
    return cal.rho_xi, cal.sigma_xi2, cal.sigma_eps2


def draw_shocks(ss, n_stores, n_weeks, cal, dgm) -> ShockArrays:
    rng = np.random.Generator(np.random.PCG64(ss))
    _, _, eps_var = shock_parameters(cal, dgm)
    # Draw a full cost matrix in either mode to preserve other random streams.
    omega = rng.standard_normal((n_stores, n_weeks))
    eps = rng.normal(0, np.sqrt(eps_var), (n_stores, n_weeks))
    u = rng.choice([-1.0, 1.0], (n_stores, n_weeks))
    cost_innovations = rng.standard_normal((n_stores, n_weeks))
    if dgm.cost_shifter["structure"] == "iid_store_week":
        cost = cost_innovations * dgm.cost_shifter["sd"]
    else:
        chain = ar1(cost_innovations[0], dgm.cost_shifter["rho"], dgm.cost_shifter["sd"])
        cost = np.broadcast_to(chain, (n_stores, n_weeks)).copy()
    return ShockArrays(
        omega=omega,
        eps=eps,
        u=u,
        cost=cost,
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


def assign_model_stores(permutation, zones, phi):
    """Round within zones, then adjust the largest zone to the rounded chain target."""
    if not 0 <= phi <= 1:
        raise ValueError("phi must be in [0, 1]")
    zones = np.asarray(zones)
    result = np.zeros(len(zones), dtype=bool)
    unique, counts = np.unique(zones, return_counts=True)
    for zone, count in zip(unique, counts):
        order = permutation[zones[permutation] == zone]
        result[order[: round(phi * count)]] = True
    difference = round(phi * len(zones)) - int(result.sum())
    # Distribute any residual across largest zones while keeping each within one store.
    for zone in unique[np.argsort(-counts, kind="stable")]:
        if difference == 0:
            break
        order = permutation[zones[permutation] == zone]
        candidates = order[~result[order]] if difference > 0 else order[result[order]][::-1]
        for index in candidates:
            proposed = int(result[zones == zone].sum()) + (1 if difference > 0 else -1)
            if abs(proposed - phi * len(order)) > 1:
                break
            result[index] = difference > 0
            difference += -1 if difference > 0 else 1
            if difference == 0:
                break
    if difference:
        raise ValueError("Could not balance assignment")
    return result


def latent_demand(shocks, cal, rho_m, dgm=None):
    if not 0 <= rho_m <= 1:
        raise ValueError("rho_m must be in [0, 1]")
    rho, xi_var = (cal.rho_xi, cal.sigma_xi2) if dgm is None else shock_parameters(cal, dgm)[:2]
    innovations = np.sqrt(1 - rho_m) * shocks.omega + np.sqrt(rho_m) * shocks.common_shock[None, :]
    return ar1(innovations, rho, np.sqrt(xi_var))
