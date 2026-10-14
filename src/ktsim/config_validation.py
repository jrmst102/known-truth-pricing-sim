"""Reject unused/unknown configuration keys instead of silently ignoring them."""

from dataclasses import fields

from ktsim.config import CalibrationConfig, DGMConfig

TREE_KEYS = {"n_estimators", "learning_rate", "num_leaves", "min_child_samples"}


def keys(mapping, allowed, label):
    unknown = set(mapping) - set(allowed)
    if unknown:
        raise ValueError(f"Unread configuration keys in {label}: {sorted(unknown)}")


def validate_config(raw):
    if "feasible_band" in raw:
        keys(raw, {field.name for field in fields(DGMConfig)} - {"store_zones", "calendar"}, "DGM")
        nested = {
            "feasible_band": {"lower", "upper"},
            "comp_index": {"rho"},
            "cost_shifter": {"structure", "rho", "sd"},
            "zone_drift": {"rho"},
            "exploration": {"delta", "decay_power"},
            "censoring": {"multiplier"},
            "reliability": {"tau", "window"},
        }
        for name, allowed in nested.items():
            keys(raw[name], allowed, name)
    elif "store_coverage_min" in raw:
        keys(raw, {field.name for field in fields(CalibrationConfig)}, "calibration")
        keys(
            raw["plausibility"],
            {
                "retained_stores_min",
                "promo_freq",
                "promo_depth",
                "resid_sd",
                "profit_mean",
                "beta_reference",
            },
            "plausibility",
        )
    elif "M1_ols" in raw:
        allowed = {
            "M1_ols": {"robust_se"},
            "M2_gbm": TREE_KEYS | {"fd_step", "fd_window_weeks"},
            "M3_iv": {"instrument"},
            "M4_dml": {"n_folds", "instrument", "nuisance_params", "inference_validated"},
        }
        keys(raw, allowed, "estimators")
        for name, fields_allowed in allowed.items():
            keys(raw[name], fields_allowed, name)
        keys(raw["M4_dml"]["nuisance_params"], TREE_KEYS, "nuisance_params")
    elif "targets" in raw:
        keys(raw, {"targets", "floor", "cap", "budget_hours"}, "decisions")
        keys(raw["targets"], {"elasticity", "regret", "paired"}, "targets")
    elif "environments" in raw:
        keys(
            raw,
            {
                "protocol_version",
                "spec_version",
                "master_seed",
                "environments",
                "eta",
                "kappa",
                "phi",
                "estimators",
                "policies",
                "pass_through",
                "stages",
                "extensions",
            },
            "scenarios",
        )
        keys(raw["stages"], {"validation", "diagnostic", "pilot", "main"}, "stages")
        for stage, definition in raw["stages"].items():
            keys(
                definition,
                {"reps", "base_extra_reps"} if stage == "diagnostic" else {"reps"},
                f"stages.{stage}",
            )
        for name, definition in raw["extensions"].items():
            keys(
                definition,
                {
                    "base",
                    "sales_process",
                    "pass_through",
                    "instrument",
                    "shock_split",
                    "cost_structure",
                },
                f"extensions.{name}",
            )
            if len(definition) != 2 or "base" not in definition:
                raise ValueError("Each extension must vary one factor from a named base")
    else:
        raise ValueError("Unrecognized configuration schema")
    return raw
