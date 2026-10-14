import numpy as np
import pandas as pd

from ktsim.estimators.dml import DML


def panel(cal, seed=47, n_stores=12, weeks=70):
    rng = np.random.default_rng(seed)
    stores = np.repeat(np.arange(n_stores), weeks)
    t = np.tile(np.arange(weeks), n_stores)
    z = rng.normal(size=len(t))
    price = cal.p_bar + 0.15 * z + rng.normal(0, 0.1, len(t))
    promo = rng.binomial(1, 0.2, len(t))
    from ktsim.rng import ar1

    xi = ar1(rng.normal(size=(n_stores, weeks)), 0.5, 0.15).ravel()
    return pd.DataFrame(
        dict(
            store=stores,
            t=t,
            week_of_year=t % 52 + 1,
            promo=promo,
            log_comp_index=rng.normal(0, 0.1, len(t)),
            cost_shifter=z,
            price=price,
            log_q=3 + stores * 0.1 - 0.4 * (price - cal.p_bar) + 0.2 * promo + xi,
        )
    )


def test_grouped_folds_and_features(cal):
    frame = panel(cal)
    cfg = dict(n_folds=5, nuisance_params=dict(n_estimators=10, min_child_samples=15))
    for pliv in (False, True):
        result = DML(pliv).fit(frame, cal, cfg)
        assert result["converged"]
        assert set(result["fold_assignment"]) == set(frame.store)
        assert len(set(result["fold_assignment"].values())) == 5
        assert "store" not in result["nuisance_features"]
        assert result["variance_method"] == "cluster:store"
        assert result["coverage_status"] == "withheld: inference not validated"
        assert len(result["fold_hash"]) == 64
        assert np.isfinite(result["predict"](frame, frame.price)).all()
