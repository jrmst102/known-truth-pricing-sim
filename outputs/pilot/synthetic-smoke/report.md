# Known-Truth Pricing Pilot

Run: synthetic-smoke; commit: 2fb8d1dc72d9e8decddc1fe32dc9557fd83b868c; master seed: 20261013

**Status: exploratory implementation; protocol review and author sign-off pending.**
Synthetic fixture, not Dominick's results.

## Reproducibility
```json
{
  "commit": "2fb8d1dc72d9e8decddc1fe32dc9557fd83b868c",
  "dirty": true,
  "synthetic": true,
  "master_seed": 20261013,
  "cells": [
    {
      "name": "P0",
      "eta": -1.06,
      "kappa": 0.0,
      "phi": 0.0,
      "delta": 0.0,
      "reps": 2,
      "estimators": [
        "M1",
        "M3"
      ],
      "policies": [
        "greedy",
        "oracle"
      ],
      "pass_through": 0.2,
      "multiplier": 1.5,
      "rho_m": 0.0,
      "data_only": false
    },
    {
      "name": "P1",
      "eta": -1.06,
      "kappa": 0.05,
      "phi": 0.5,
      "delta": 0.0,
      "reps": 2,
      "estimators": [
        "M1",
        "M3"
      ],
      "policies": [
        "greedy"
      ],
      "pass_through": 0.2,
      "multiplier": 1.5,
      "rho_m": 0.0,
      "data_only": false
    },
    {
      "name": "P1",
      "eta": -1.06,
      "kappa": 0.05,
      "phi": 0.5,
      "delta": 0.03,
      "reps": 2,
      "estimators": [
        "M1",
        "M3"
      ],
      "policies": [
        "greedy_rps"
      ],
      "pass_through": 0.2,
      "multiplier": 1.5,
      "rho_m": 0.0,
      "data_only": false
    },
    {
      "name": "P2",
      "eta": -0.8,
      "kappa": 0.05,
      "phi": 0.5,
      "delta": 0.0,
      "reps": 2,
      "estimators": [
        "M1",
        "M3"
      ],
      "policies": [
        "greedy"
      ],
      "pass_through": 0.2,
      "multiplier": 1.5,
      "rho_m": 0.0,
      "data_only": false
    },
    {
      "name": "P3",
      "eta": -2.5,
      "kappa": 0.05,
      "phi": 0.5,
      "delta": 0.0,
      "reps": 2,
      "estimators": [
        "M1",
        "M3"
      ],
      "policies": [
        "greedy"
      ],
      "pass_through": 0.2,
      "multiplier": 1.5,
      "rho_m": 0.0,
      "data_only": false
    },
    {
      "name": "P4",
      "eta": -1.06,
      "kappa": 0.05,
      "phi": 0.0,
      "delta": 0.0,
      "reps": 2,
      "estimators": [
        "M1",
        "M3"
      ],
      "policies": [
        "legacy"
      ],
      "pass_through": 0.05,
      "multiplier": 1.5,
      "rho_m": 0.0,
      "data_only": false
    },
    {
      "name": "P4",
      "eta": -1.06,
      "kappa": 0.05,
      "phi": 0.0,
      "delta": 0.0,
      "reps": 2,
      "estimators": [
        "M1",
        "M3"
      ],
      "policies": [
        "legacy"
      ],
      "pass_through": 0.1,
      "multiplier": 1.5,
      "rho_m": 0.0,
      "data_only": false
    },
    {
      "name": "P4",
      "eta": -1.06,
      "kappa": 0.05,
      "phi": 0.0,
      "delta": 0.0,
      "reps": 2,
      "estimators": [
        "M1",
        "M3"
      ],
      "policies": [
        "legacy"
      ],
      "pass_through": 0.2,
      "multiplier": 1.5,
      "rho_m": 0.0,
      "data_only": false
    },
    {
      "name": "P4",
      "eta": -1.06,
      "kappa": 0.05,
      "phi": 0.0,
      "delta": 0.0,
      "reps": 2,
      "estimators": [
        "M1",
        "M3"
      ],
      "policies": [
        "legacy"
      ],
      "pass_through": 0.5,
      "multiplier": 1.5,
      "rho_m": 0.0,
      "data_only": false
    },
    {
      "name": "P4",
      "eta": -1.06,
      "kappa": 0.05,
      "phi": 0.0,
      "delta": 0.0,
      "reps": 2,
      "estimators": [
        "M1",
        "M3"
      ],
      "policies": [
        "legacy"
      ],
      "pass_through": 1.0,
      "multiplier": 1.5,
      "rho_m": 0.0,
      "data_only": false
    },
    {
      "name": "P5",
      "eta": -1.06,
      "kappa": 0.0,
      "phi": 0.0,
      "delta": 0.0,
      "reps": 2,
      "estimators": [
        "M1",
        "M3"
      ],
      "policies": [],
      "pass_through": 0.2,
      "multiplier": 1.25,
      "rho_m": 0.0,
      "data_only": true
    },
    {
      "name": "P5",
      "eta": -1.06,
      "kappa": 0.0,
      "phi": 0.0,
      "delta": 0.0,
      "reps": 2,
      "estimators": [
        "M1",
        "M3"
      ],
      "policies": [],
      "pass_through": 0.2,
      "multiplier": 1.5,
      "rho_m": 0.0,
      "data_only": true
    },
    {
      "name": "P5",
      "eta": -1.06,
      "kappa": 0.0,
      "phi": 0.0,
      "delta": 0.0,
      "reps": 2,
      "estimators": [
        "M1",
        "M3"
      ],
      "policies": [],
      "pass_through": 0.2,
      "multiplier": 2.0,
      "rho_m": 0.0,
      "data_only": true
    }
  ],
  "dgm": {
    "feasible_band": {
      "lower": 0.8,
      "upper": 1.2
    },
    "ladder_step": 0.05,
    "cross_price_coef": 0.2,
    "comp_index": {
      "rho": 0.8
    },
    "cost_shifter": {
      "rho": 0.8,
      "sd": 0.05
    },
    "zone_drift": {
      "rho": 0.9
    },
    "kappa_levels": {
      "none": 0.0,
      "pos": 0.05,
      "neg": -0.05
    },
    "exploration": {
      "delta_levels": [
        0.0,
        0.03
      ],
      "decay_power": -0.25,
      "two_point": true
    },
    "censoring": {
      "multiplier": 1.5
    },
    "history_weeks": 52,
    "cycles": 2,
    "rho_m_levels": [
      0.0,
      0.5
    ],
    "eta_levels": {
      "low": -0.8,
      "med": -1.06,
      "high": -2.5
    },
    "phi_levels": [
      0.0,
      0.5,
      1.0
    ],
    "store_zones": {
      "1": 1,
      "2": 1,
      "3": 1,
      "4": 1,
      "5": 2,
      "6": 2,
      "7": 2,
      "8": 2
    }
  },
  "estimators": {
    "M1_ols": {
      "robust_se": "HC1"
    },
    "M2_gbm": {
      "n_estimators": 500,
      "learning_rate": 0.05,
      "num_leaves": 31,
      "min_child_samples": 20,
      "fd_step": 0.01,
      "fd_window_weeks": 4
    },
    "M3_iv": {
      "instrument": "cost_shifter",
      "variants": [
        "tsls",
        "control_function"
      ],
      "report_first_stage_F": true
    },
    "M4_dml": {
      "n_folds": 5,
      "nuisance": "lightgbm",
      "nuisance_params": {
        "n_estimators": 500,
        "learning_rate": 0.05,
        "num_leaves": 31,
        "min_child_samples": 20
      },
      "variants": [
        "plr_controls",
        "pliv_cost_shifter"
      ]
    }
  },
  "calibration": {
    "alpha_s": {
      "1": 3.0,
      "2": 3.1,
      "3": 3.2,
      "4": 3.3,
      "5": 3.0,
      "6": 3.1,
      "7": 3.2,
      "8": 3.3
    },
    "season": {
      "g": [
        0.1,
        0.02
      ],
      "h": [
        0.05,
        0.01
      ]
    },
    "holiday": {},
    "promo_effect": 0.2,
    "rho_xi": 0.5,
    "sigma_xi2": 0.04,
    "sigma_eps2": 0.04,
    "p_bar": 3.0,
    "mu_z": {
      "1": 1.0986122886681098,
      "2": 1.1186122886681098
    },
    "sigma_nu2": 0.0025,
    "pi_promo": 0.15,
    "promo_depth": {
      "mean": 0.15,
      "sd": 0.02
    },
    "sigma_comp": 0.1,
    "unit_cost": 2.0,
    "price_dispersion": {
      "sd_log_price": 0.1,
      "n_distinct": 30,
      "profit_mean": 25.0,
      "resid_sd": 0.282842712474619
    },
    "beta_reference": -1.06,
    "n_stores": 8,
    "n_store_weeks": 416,
    "zero_share": 0.0,
    "focal_upc": 123,
    "weeks": [
      1,
      52
    ]
  },
  "checksums": {
    "data/fixtures/calibration_synthetic.json": "455f219dda55f750586bbeb07a27c4fe76b19c7c8e83537a86f5206067fe7073"
  },
  "calibration_checks": [],
  "environment": {
    "python": "3.11.11",
    "packages": {
      "ktsim": "0.1.0",
      "numpy": "2.2.3",
      "pandas": "2.2.3",
      "pyarrow": "19.0.1",
      "scipy": "1.15.2",
      "statsmodels": "0.14.4",
      "linearmodels": "6.1",
      "lightgbm": "4.6.0",
      "doubleml": "0.9.3",
      "scikit-learn": "1.5.2",
      "PyYAML": "6.0.2",
      "joblib": "1.4.2",
      "matplotlib": "3.10.1"
    },
    "cpu": "AMD EPYC 7763 64-Core Processor",
    "cores": 2,
    "ram_gib": 7.76
  },
  "n_jobs": 2,
  "save_data": true,
  "config_checksums": {
    "configs/pilot_cells.yaml": "a3a46f7c1acc538710966a5ac22460d6fd77a452cd82d76633b8e8859f7439a0",
    "configs/dgm_base.yaml": "aa4f2f6da77e5c15b0a76374aa29f70f8321a5e7ccd309d5816ee15cad72e7c9",
    "configs/estimators.yaml": "5ff2131d912b3960c497af881a8157c3b257e6828dc2dbf8f660d77776ccbac0"
  },
  "fingerprint": "921d6543911a856db137d2bc770f0c256b1d672f393024fb6c206bdffa764dbf"
}
```

## P0 correctness
| run_id | cell | arm | cycle_or_horizon | measure | estimate | mcse | n_reps |
| --- | --- | --- | --- | --- | --- | --- | --- |
| synthetic-smoke | P0 | M1:greedy | horizon | regret_rec | 2.183 | 0.906 | 2 |
| synthetic-smoke | P0 | M1:greedy | horizon | regret_dep | 1.237 | 0.754 | 2 |
| synthetic-smoke | P0 | M1:greedy | horizon | forecast_mape | 0.233 | 0.060 | 2 |
| synthetic-smoke | P0 | M1:greedy | horizon | censored_share | 0.031 | 0.031 | 2 |
| synthetic-smoke | P0 | M1:greedy | horizon | forecast_rmse | 5.774 | 1.014 | 2 |
| synthetic-smoke | P0 | M1:greedy | horizon | cumulative_regret | 2.473 | 1.508 | 2 |
| synthetic-smoke | P0 | M1:greedy | horizon | price_sd_26 | 0.074 | 0.009 | 2 |
| synthetic-smoke | P0 | M1:greedy | horizon | failure_share | 0.000 | 0.000 | 2 |
| synthetic-smoke | P0 | M1:greedy | horizon | seconds | 0.148 | 0.003 | 2 |
| synthetic-smoke | P0 | M1:oracle | horizon | regret_rec | 0.000 | 0.000 | 2 |
| synthetic-smoke | P0 | M1:oracle | horizon | regret_dep | 1.237 | 0.754 | 2 |
| synthetic-smoke | P0 | M1:oracle | horizon | forecast_mape | 0.233 | 0.060 | 2 |
| synthetic-smoke | P0 | M1:oracle | horizon | censored_share | 0.031 | 0.031 | 2 |
| synthetic-smoke | P0 | M1:oracle | horizon | forecast_rmse | 5.774 | 1.014 | 2 |
| synthetic-smoke | P0 | M1:oracle | horizon | cumulative_regret | 2.473 | 1.508 | 2 |
| synthetic-smoke | P0 | M1:oracle | horizon | price_sd_26 | 0.074 | 0.009 | 2 |
| synthetic-smoke | P0 | M1:oracle | horizon | failure_share | 0.000 | 0.000 | 2 |
| synthetic-smoke | P0 | M1:oracle | horizon | seconds | 0.032 | 0.001 | 2 |
| synthetic-smoke | P0 | M3:greedy | horizon | regret_rec | 2.183 | 0.906 | 2 |
| synthetic-smoke | P0 | M3:greedy | horizon | regret_dep | 1.237 | 0.754 | 2 |
| synthetic-smoke | P0 | M3:greedy | horizon | forecast_mape | 0.247 | 0.021 | 2 |
| synthetic-smoke | P0 | M3:greedy | horizon | censored_share | 0.031 | 0.031 | 2 |
| synthetic-smoke | P0 | M3:greedy | horizon | forecast_rmse | 6.522 | 0.204 | 2 |
| synthetic-smoke | P0 | M3:greedy | horizon | cumulative_regret | 2.473 | 1.508 | 2 |
| synthetic-smoke | P0 | M3:greedy | horizon | price_sd_26 | 0.074 | 0.009 | 2 |
| synthetic-smoke | P0 | M3:greedy | horizon | failure_share | 0.000 | 0.000 | 2 |
| synthetic-smoke | P0 | M3:greedy | horizon | seconds | 0.264 | 0.006 | 2 |
| synthetic-smoke | P0 | M3:oracle | horizon | regret_rec | 0.000 | 0.000 | 2 |
| synthetic-smoke | P0 | M3:oracle | horizon | regret_dep | 1.237 | 0.754 | 2 |
| synthetic-smoke | P0 | M3:oracle | horizon | forecast_mape | 0.247 | 0.021 | 2 |
| synthetic-smoke | P0 | M3:oracle | horizon | censored_share | 0.031 | 0.031 | 2 |
| synthetic-smoke | P0 | M3:oracle | horizon | forecast_rmse | 6.522 | 0.204 | 2 |
| synthetic-smoke | P0 | M3:oracle | horizon | cumulative_regret | 2.473 | 1.508 | 2 |
| synthetic-smoke | P0 | M3:oracle | horizon | price_sd_26 | 0.074 | 0.009 | 2 |
| synthetic-smoke | P0 | M3:oracle | horizon | failure_share | 0.000 | 0.000 | 2 |
| synthetic-smoke | P0 | M3:oracle | horizon | seconds | 0.132 | 0.000 | 2 |
| synthetic-smoke | P0 | M3_cf:greedy | horizon | regret_rec | 2.183 | 0.906 | 2 |
| synthetic-smoke | P0 | M3_cf:greedy | horizon | regret_dep | 1.237 | 0.754 | 2 |
| synthetic-smoke | P0 | M3_cf:greedy | horizon | forecast_mape | 0.247 | 0.021 | 2 |
| synthetic-smoke | P0 | M3_cf:greedy | horizon | censored_share | 0.031 | 0.031 | 2 |
| synthetic-smoke | P0 | M3_cf:greedy | horizon | forecast_rmse | 6.522 | 0.204 | 2 |
| synthetic-smoke | P0 | M3_cf:greedy | horizon | cumulative_regret | 2.473 | 1.508 | 2 |
| synthetic-smoke | P0 | M3_cf:greedy | horizon | price_sd_26 | 0.074 | 0.009 | 2 |
| synthetic-smoke | P0 | M3_cf:greedy | horizon | failure_share | 0.000 | 0.000 | 2 |
| synthetic-smoke | P0 | M3_cf:greedy | horizon | seconds | 0.242 | 0.002 | 2 |
| synthetic-smoke | P0 | M3_cf:oracle | horizon | regret_rec | 0.000 | 0.000 | 2 |
| synthetic-smoke | P0 | M3_cf:oracle | horizon | regret_dep | 1.237 | 0.754 | 2 |
| synthetic-smoke | P0 | M3_cf:oracle | horizon | forecast_mape | 0.247 | 0.021 | 2 |
| synthetic-smoke | P0 | M3_cf:oracle | horizon | censored_share | 0.031 | 0.031 | 2 |
| synthetic-smoke | P0 | M3_cf:oracle | horizon | forecast_rmse | 6.522 | 0.204 | 2 |
| synthetic-smoke | P0 | M3_cf:oracle | horizon | cumulative_regret | 2.473 | 1.508 | 2 |
| synthetic-smoke | P0 | M3_cf:oracle | horizon | price_sd_26 | 0.074 | 0.009 | 2 |
| synthetic-smoke | P0 | M3_cf:oracle | horizon | failure_share | 0.000 | 0.000 | 2 |
| synthetic-smoke | P0 | M3_cf:oracle | horizon | seconds | 0.142 | 0.001 | 2 |

P0 acceptance requires full reps/horizon, bias within two MCSEs, coverage >= 0.80, zero failures and zero oracle recommended-price regret.

## P1 decision
```json
{
  "n_sim": null,
  "required": null,
  "cap_exceeded": false,
  "inputs": [
    {
      "arm": "M1:greedy",
      "measure": "regret_rec",
      "sd": 0.0,
      "target": 0.25,
      "required": 0
    },
    {
      "arm": "M1:greedy_rps:delta=0.03",
      "measure": "regret_rec",
      "sd": 0.0,
      "target": 0.25,
      "required": 0
    },
    {
      "arm": "M3:greedy",
      "measure": "regret_rec",
      "sd": 1.8179335223504562,
      "target": 0.25,
      "required": 53
    },
    {
      "arm": "M3:greedy_rps:delta=0.03",
      "measure": "regret_rec",
      "sd": 1.937886780328754,
      "target": 0.25,
      "required": 61
    },
    {
      "arm": "M3_cf:greedy",
      "measure": "regret_rec",
      "sd": 1.8179335223504562,
      "target": 0.25,
      "required": 53
    },
    {
      "arm": "M3_cf:greedy_rps:delta=0.03",
      "measure": "regret_rec",
      "sd": 1.937886780328754,
      "target": 0.25,
      "required": 61
    }
  ],
  "reason": "P1 is incomplete; no n_sim decision"
}
```

| run_id | cell | arm | cycle_or_horizon | measure | estimate | mcse | n_reps |
| --- | --- | --- | --- | --- | --- | --- | --- |
| synthetic-smoke | P1 | M1:greedy | horizon | regret_rec | 3.090 | 0.000 | 2 |
| synthetic-smoke | P1 | M1:greedy | horizon | regret_dep | 2.038 | 0.196 | 2 |
| synthetic-smoke | P1 | M1:greedy | horizon | forecast_mape | 0.460 | 0.060 | 2 |
| synthetic-smoke | P1 | M1:greedy | horizon | censored_share | 0.031 | 0.031 | 2 |
| synthetic-smoke | P1 | M1:greedy | horizon | forecast_rmse | 9.991 | 1.638 | 2 |
| synthetic-smoke | P1 | M1:greedy | horizon | cumulative_regret | 4.076 | 0.393 | 2 |
| synthetic-smoke | P1 | M1:greedy | horizon | price_sd_26 | 0.086 | 0.001 | 2 |
| synthetic-smoke | P1 | M1:greedy | horizon | failure_share | 0.000 | 0.000 | 2 |
| synthetic-smoke | P1 | M1:greedy | horizon | seconds | 0.271 | 0.026 | 2 |
| synthetic-smoke | P1 | M1:greedy_rps:delta=0.03 | horizon | regret_rec | 3.090 | 0.000 | 2 |
| synthetic-smoke | P1 | M1:greedy_rps:delta=0.03 | horizon | regret_dep | 1.921 | 0.235 | 2 |
| synthetic-smoke | P1 | M1:greedy_rps:delta=0.03 | horizon | forecast_mape | 0.440 | 0.055 | 2 |
| synthetic-smoke | P1 | M1:greedy_rps:delta=0.03 | horizon | censored_share | 0.031 | 0.031 | 2 |
| synthetic-smoke | P1 | M1:greedy_rps:delta=0.03 | horizon | forecast_rmse | 9.557 | 1.565 | 2 |
| synthetic-smoke | P1 | M1:greedy_rps:delta=0.03 | horizon | cumulative_regret | 3.841 | 0.470 | 2 |
| synthetic-smoke | P1 | M1:greedy_rps:delta=0.03 | horizon | price_sd_26 | 0.085 | 0.002 | 2 |
| synthetic-smoke | P1 | M1:greedy_rps:delta=0.03 | horizon | failure_share | 0.000 | 0.000 | 2 |
| synthetic-smoke | P1 | M1:greedy_rps:delta=0.03 | horizon | seconds | 0.148 | 0.007 | 2 |
| synthetic-smoke | P1 | M3:greedy | horizon | regret_rec | 1.456 | 1.285 | 2 |
| synthetic-smoke | P1 | M3:greedy | horizon | regret_dep | 1.257 | 0.408 | 2 |
| synthetic-smoke | P1 | M3:greedy | horizon | forecast_mape | 0.248 | nan | 1 |
| synthetic-smoke | P1 | M3:greedy | horizon | censored_share | 0.031 | 0.031 | 2 |
| synthetic-smoke | P1 | M3:greedy | horizon | forecast_rmse | 5.514 | nan | 1 |
| synthetic-smoke | P1 | M3:greedy | horizon | cumulative_regret | 2.514 | 0.817 | 2 |
| synthetic-smoke | P1 | M3:greedy | horizon | price_sd_26 | 0.082 | 0.001 | 2 |
| synthetic-smoke | P1 | M3:greedy | horizon | failure_share | 0.500 | 0.500 | 2 |
| synthetic-smoke | P1 | M3:greedy | horizon | seconds | 0.262 | 0.088 | 2 |
| synthetic-smoke | P1 | M3:greedy_rps:delta=0.03 | horizon | regret_rec | 1.541 | 1.370 | 2 |
| synthetic-smoke | P1 | M3:greedy_rps:delta=0.03 | horizon | regret_dep | 1.222 | 0.378 | 2 |
| synthetic-smoke | P1 | M3:greedy_rps:delta=0.03 | horizon | forecast_mape | 0.249 | nan | 1 |
| synthetic-smoke | P1 | M3:greedy_rps:delta=0.03 | horizon | censored_share | 0.031 | 0.031 | 2 |
| synthetic-smoke | P1 | M3:greedy_rps:delta=0.03 | horizon | forecast_rmse | 5.524 | nan | 1 |
| synthetic-smoke | P1 | M3:greedy_rps:delta=0.03 | horizon | cumulative_regret | 2.444 | 0.756 | 2 |
| synthetic-smoke | P1 | M3:greedy_rps:delta=0.03 | horizon | price_sd_26 | 0.082 | 0.001 | 2 |
| synthetic-smoke | P1 | M3:greedy_rps:delta=0.03 | horizon | failure_share | 0.500 | 0.500 | 2 |
| synthetic-smoke | P1 | M3:greedy_rps:delta=0.03 | horizon | seconds | 0.187 | 0.055 | 2 |
| synthetic-smoke | P1 | M3_cf:greedy | horizon | regret_rec | 1.456 | 1.285 | 2 |
| synthetic-smoke | P1 | M3_cf:greedy | horizon | regret_dep | 1.257 | 0.408 | 2 |
| synthetic-smoke | P1 | M3_cf:greedy | horizon | forecast_mape | 0.248 | nan | 1 |
| synthetic-smoke | P1 | M3_cf:greedy | horizon | censored_share | 0.031 | 0.031 | 2 |
| synthetic-smoke | P1 | M3_cf:greedy | horizon | forecast_rmse | 5.514 | nan | 1 |
| synthetic-smoke | P1 | M3_cf:greedy | horizon | cumulative_regret | 2.514 | 0.817 | 2 |
| synthetic-smoke | P1 | M3_cf:greedy | horizon | price_sd_26 | 0.082 | 0.001 | 2 |
| synthetic-smoke | P1 | M3_cf:greedy | horizon | failure_share | 0.500 | 0.500 | 2 |
| synthetic-smoke | P1 | M3_cf:greedy | horizon | seconds | 0.194 | 0.048 | 2 |
| synthetic-smoke | P1 | M3_cf:greedy_rps:delta=0.03 | horizon | regret_rec | 1.541 | 1.370 | 2 |
| synthetic-smoke | P1 | M3_cf:greedy_rps:delta=0.03 | horizon | regret_dep | 1.222 | 0.378 | 2 |
| synthetic-smoke | P1 | M3_cf:greedy_rps:delta=0.03 | horizon | forecast_mape | 0.249 | nan | 1 |
| synthetic-smoke | P1 | M3_cf:greedy_rps:delta=0.03 | horizon | censored_share | 0.031 | 0.031 | 2 |
| synthetic-smoke | P1 | M3_cf:greedy_rps:delta=0.03 | horizon | forecast_rmse | 5.524 | nan | 1 |
| synthetic-smoke | P1 | M3_cf:greedy_rps:delta=0.03 | horizon | cumulative_regret | 2.444 | 0.756 | 2 |
| synthetic-smoke | P1 | M3_cf:greedy_rps:delta=0.03 | horizon | price_sd_26 | 0.082 | 0.001 | 2 |
| synthetic-smoke | P1 | M3_cf:greedy_rps:delta=0.03 | horizon | failure_share | 0.500 | 0.500 | 2 |
| synthetic-smoke | P1 | M3_cf:greedy_rps:delta=0.03 | horizon | seconds | 0.192 | 0.052 | 2 |

## P4 instrument
```json
{
  "weak": null,
  "strong": 1.0,
  "inputs": [
    {
      "pass_through": 0.05,
      "median_F": 0.0940166117700614
    },
    {
      "pass_through": 0.1,
      "median_F": 0.053002887292338645
    },
    {
      "pass_through": 0.2,
      "median_F": 1.2278017575233617
    },
    {
      "pass_through": 0.5,
      "median_F": 14.662445951135544
    },
    {
      "pass_through": 1.0,
      "median_F": 69.11327992942297
    }
  ]
}
```

Missing weak/strong choices mean the supplied grid does not qualify; do not substitute values.
## Bound cells
| cell | eta_true | p_star | oracle_at_bound |
| --- | --- | --- | --- |
| P0 | -1.060 | 2.850 | interior |
| P1 | -1.060 | 2.850 | interior |
| P2 | -0.800 | 3.600 | ceiling |
| P3 | -2.500 | 2.400 | floor |
| P4:pass_through=0.05 | -1.060 | 2.850 | interior |
| P4:pass_through=0.1 | -1.060 | 2.850 | interior |
| P4:pass_through=0.2 | -1.060 | 2.850 | interior |
| P4:pass_through=0.5 | -1.060 | 2.850 | interior |
| P4:pass_through=1 | -1.060 | 2.850 | interior |
| P5:multiplier=1.25 | -1.060 | 2.850 | interior |
| P5:multiplier=1.5 | -1.060 | 2.850 | interior |
| P5:multiplier=2 | -1.060 | 2.850 | interior |

## Compute plan
```json
{
  "projected_core_hours": null,
  "budget_hours": 150.0,
  "n_sim": null,
  "inputs": [
    {
      "arm": "M1:greedy",
      "mean_seconds": 0.2706452934994558
    },
    {
      "arm": "M1:greedy_rps:delta=0.03",
      "mean_seconds": 0.1481830090001494
    },
    {
      "arm": "M3:greedy",
      "mean_seconds": 0.2615150784995421
    },
    {
      "arm": "M3:greedy_rps:delta=0.03",
      "mean_seconds": 0.1871820420001313
    },
    {
      "arm": "M3_cf:greedy",
      "mean_seconds": 0.194044238499373
    },
    {
      "arm": "M3_cf:greedy_rps:delta=0.03",
      "mean_seconds": 0.19223344800047926
    }
  ],
  "ladder_step": "Insufficient P1 runtime"
}
```

Projection assumes 27 cells with the measured P1 arms. The actual protocol compute ladder and full-design arm weights were not supplied; no automatic protocol changes are made.
## Failures
| run_id | cell | arm | cycle_or_horizon | measure | estimate | mcse | n_reps | flag_gt_5_percent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| synthetic-smoke | P0 | M1:greedy | horizon | failure_share | 0.000 | 0.000 | 2 | False |
| synthetic-smoke | P0 | M1:oracle | horizon | failure_share | 0.000 | 0.000 | 2 | False |
| synthetic-smoke | P0 | M3:greedy | horizon | failure_share | 0.000 | 0.000 | 2 | False |
| synthetic-smoke | P0 | M3:oracle | horizon | failure_share | 0.000 | 0.000 | 2 | False |
| synthetic-smoke | P0 | M3_cf:greedy | horizon | failure_share | 0.000 | 0.000 | 2 | False |
| synthetic-smoke | P0 | M3_cf:oracle | horizon | failure_share | 0.000 | 0.000 | 2 | False |
| synthetic-smoke | P1 | M1:greedy | horizon | failure_share | 0.000 | 0.000 | 2 | False |
| synthetic-smoke | P1 | M1:greedy_rps:delta=0.03 | horizon | failure_share | 0.000 | 0.000 | 2 | False |
| synthetic-smoke | P1 | M3:greedy | horizon | failure_share | 0.500 | 0.500 | 2 | True |
| synthetic-smoke | P1 | M3:greedy_rps:delta=0.03 | horizon | failure_share | 0.500 | 0.500 | 2 | True |
| synthetic-smoke | P1 | M3_cf:greedy | horizon | failure_share | 0.500 | 0.500 | 2 | True |
| synthetic-smoke | P1 | M3_cf:greedy_rps:delta=0.03 | horizon | failure_share | 0.500 | 0.500 | 2 | True |
| synthetic-smoke | P2 | M1:greedy | horizon | failure_share | 0.000 | 0.000 | 2 | False |
| synthetic-smoke | P2 | M3:greedy | horizon | failure_share | 0.500 | 0.500 | 2 | True |
| synthetic-smoke | P2 | M3_cf:greedy | horizon | failure_share | 0.500 | 0.500 | 2 | True |
| synthetic-smoke | P3 | M1:greedy | horizon | failure_share | 0.000 | 0.000 | 2 | False |
| synthetic-smoke | P3 | M3:greedy | horizon | failure_share | 0.750 | 0.250 | 2 | True |
| synthetic-smoke | P3 | M3_cf:greedy | horizon | failure_share | 0.750 | 0.250 | 2 | True |
| synthetic-smoke | P4:pass_through=0.05 | M1:legacy | horizon | failure_share | 0.000 | 0.000 | 2 | False |
| synthetic-smoke | P4:pass_through=0.05 | M3:legacy | horizon | failure_share | 0.500 | 0.500 | 2 | True |
| synthetic-smoke | P4:pass_through=0.05 | M3_cf:legacy | horizon | failure_share | 0.500 | 0.500 | 2 | True |
| synthetic-smoke | P4:pass_through=0.1 | M1:legacy | horizon | failure_share | 0.000 | 0.000 | 2 | False |
| synthetic-smoke | P4:pass_through=0.1 | M3:legacy | horizon | failure_share | 0.500 | 0.500 | 2 | True |
| synthetic-smoke | P4:pass_through=0.1 | M3_cf:legacy | horizon | failure_share | 0.500 | 0.500 | 2 | True |
| synthetic-smoke | P4:pass_through=0.2 | M1:legacy | horizon | failure_share | 0.000 | 0.000 | 2 | False |
| synthetic-smoke | P4:pass_through=0.2 | M3:legacy | horizon | failure_share | 0.500 | 0.500 | 2 | True |
| synthetic-smoke | P4:pass_through=0.2 | M3_cf:legacy | horizon | failure_share | 0.500 | 0.500 | 2 | True |
| synthetic-smoke | P4:pass_through=0.5 | M1:legacy | horizon | failure_share | 0.000 | 0.000 | 2 | False |
| synthetic-smoke | P4:pass_through=0.5 | M3:legacy | horizon | failure_share | 0.000 | 0.000 | 2 | False |
| synthetic-smoke | P4:pass_through=0.5 | M3_cf:legacy | horizon | failure_share | 0.000 | 0.000 | 2 | False |
| synthetic-smoke | P4:pass_through=1 | M1:legacy | horizon | failure_share | 0.000 | 0.000 | 2 | False |
| synthetic-smoke | P4:pass_through=1 | M3:legacy | horizon | failure_share | 0.000 | 0.000 | 2 | False |
| synthetic-smoke | P4:pass_through=1 | M3_cf:legacy | horizon | failure_share | 0.000 | 0.000 | 2 | False |

## Censoring
Chosen multiplier: 1.5
| run_id | cell | arm | cycle_or_horizon | measure | estimate | mcse | n_reps |
| --- | --- | --- | --- | --- | --- | --- | --- |
| synthetic-smoke | P5:multiplier=1.25 | data:legacy | horizon | censored_share | 0.094 | 0.031 | 2 |
| synthetic-smoke | P5:multiplier=1.5 | data:legacy | horizon | censored_share | 0.031 | 0.031 | 2 |
| synthetic-smoke | P5:multiplier=2 | data:legacy | horizon | censored_share | 0.000 | 0.000 | 2 |

## Calibration
Not available for this run.

## Limitations
See CHANGELOG.md and docs/IMPLEMENTATION_NOTES.md for unresolved protocol rules.
Scientific replay excludes elapsed times and timestamps. CI and synthetic runs never use raw data.
## Diagnostics
![p0_elasticity](figures/p0_elasticity.png)
![p1_elasticity](figures/p1_elasticity.png)
![p1_forecast_bias](figures/p1_forecast_bias.png)
![p1_price_sd](figures/p1_price_sd.png)
![p4_first_stage](figures/p4_first_stage.png)
