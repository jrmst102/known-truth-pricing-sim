# Known-Truth Pricing Pilot

Run: synthetic-demo; commit: a64c6d99902b52cbee2184d90340d775ab559cc7; master seed: 20261013

**Status: exploratory implementation; protocol review and author sign-off pending.**
Synthetic fixture, not Dominick's results.

## Reproducibility
```json
{
  "commit": "a64c6d99902b52cbee2184d90340d775ab559cc7",
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
        "M2",
        "M3",
        "M4_plr",
        "M4_pliv"
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
        "M2",
        "M3",
        "M4_plr",
        "M4_pliv"
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
        "M2",
        "M3",
        "M4_plr",
        "M4_pliv"
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
      "estimators": [],
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
      "estimators": [],
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
      "estimators": [],
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
  "source_checksums": {
    "src/ktsim/__init__.py": "68602e3d99b8d7e9f0931e84eb8495511adbb4dabb1aa2a238b9047ab19b946b",
    "src/ktsim/calibrate.py": "3d86c9ec1117c724f13c6b84e8394b17de94ed7ed95a26ac0602af83240cf726",
    "src/ktsim/clean.py": "b3365301e0b01fb4d89d9ab27e4a47df8eceafd008bd3b472fbc21955feab5f6",
    "src/ktsim/cli.py": "04ec78df3986fccfe8d88316c0cb6bf97a3d5ab5467699aaaec86451bdef9d3f",
    "src/ktsim/config.py": "33f5ba8e3904fe038010f7ec38078ad74e017ec0b5fef89f97186850bdcbee7b",
    "src/ktsim/decisions.py": "70e5bab365fdeb7c47872d66491f5fd1f0cc4e8e336c1106e8faa894a5110fd5",
    "src/ktsim/dgm.py": "b7e7eb2129b4aa6d0286756d600c36e844e69cb2efd5b1d660da50d757643316",
    "src/ktsim/estimators/__init__.py": "d57f97eb8587f88f33854fc72763a0e6fe65cd1d48136985471c1100fe3fc903",
    "src/ktsim/estimators/base.py": "58520cd47df28aca46053708a4bbf773369c6be3bc912e4624e987f868ae9970",
    "src/ktsim/estimators/dml.py": "bc74032bb8db63d2608be0f57f836823643648bae71d44fcbb105d901097df95",
    "src/ktsim/estimators/gbm.py": "8796c659ce18c1ad6f34480f7bf9738cfee0240abf47c3ee750f39d777bb03e8",
    "src/ktsim/estimators/iv.py": "bb5f22cf473956025d466364315a9d33b7080d94c133cb8e640944721faf26cc",
    "src/ktsim/estimators/ols.py": "f6cb8b471919445e984d7283880e89cd603f2a0de9163eeb32817ce1b53cc06b",
    "src/ktsim/io.py": "1784d0637aa233c7c3bb18ec0aee2d0a2fc38e425e28f212418f55630ecd5501",
    "src/ktsim/loop.py": "45e588b53111ff2d2a192a27795e8e799afd75e7e7376faf934b23aedeb01f81",
    "src/ktsim/metrics.py": "3b3597cf3c1b33b623fddb5c0809739d4554c0c04e83e9339ecec87fb251ac42",
    "src/ktsim/oracle.py": "8543ee8fe93faa209d216f9b8d120a9910fb68cc4e831b3246192926ea39c479",
    "src/ktsim/pilot.py": "7d20b4e407280aaec335f4afa7f32c8da03202dccbd63cf317a5a51c2e93b85c",
    "src/ktsim/policies.py": "45567e016432d081198cb981e6eae603c0575f8ee101d8e71e9218d75de9d6a0",
    "src/ktsim/report.py": "a4932bf5d7010b04966e67d77fb1e7c690116a3909be678dedec52eb48c98036",
    "src/ktsim/rng.py": "7379286358831ff4b0ff48bf85d3f40ebdf7c8a89fd7ac832a59a287229a89c6",
    "scripts/check_raw_staging.py": "6719c5efed1244a24da9ae4fb87e53321a0e737ab3784ea1d872dc0584af42eb",
    "scripts/import_codebook.py": "80c11ba359cb6943f1bd085b4233aa828e5b2de29b556cb2d46800b290589d1b",
    "scripts/make_report.py": "52ea2d2f467d06c6006b828d86c0386d52e7e007d6f55f64efbb04d223102dad",
    "scripts/run_calibration.py": "68f486cb7c8f4094ef4d4bfd4344cd93b4d1fc34640d0ee5ee35ae03af8841f3",
    "scripts/run_pilot.py": "ccce631cfe33842f2d81fa3fe14149c261c03310fa3914b05c7f3055684cac0e"
  },
  "fingerprint": "699aff0dc0bc8e4da7e9d92401194775b8bcadf63e438d42b2ca4b1201a582e1"
}
```

## P0 correctness
| run_id | cell | arm | cycle_or_horizon | measure | estimate | mcse | n_reps |
| --- | --- | --- | --- | --- | --- | --- | --- |
| synthetic-demo | P0 | M1:greedy | horizon | regret_rec | 2.18 | 0.91 | 2 |
| synthetic-demo | P0 | M1:greedy | horizon | regret_dep | 1.24 | 0.75 | 2 |
| synthetic-demo | P0 | M1:greedy | horizon | forecast_mape | 0.233 | 0.060 | 2 |
| synthetic-demo | P0 | M1:greedy | horizon | censored_share | 0.031 | 0.031 | 2 |
| synthetic-demo | P0 | M1:greedy | horizon | forecast_rmse | 5.774 | 1.014 | 2 |
| synthetic-demo | P0 | M1:greedy | horizon | cumulative_regret | 2.47 | 1.51 | 2 |
| synthetic-demo | P0 | M1:greedy | horizon | price_sd_26 | 0.074 | 0.009 | 2 |
| synthetic-demo | P0 | M1:greedy | horizon | failure_share | 0.000 | 0.000 | 2 |
| synthetic-demo | P0 | M1:greedy | horizon | seconds | 0.220 | 0.044 | 2 |
| synthetic-demo | P0 | M1:oracle | horizon | regret_rec | 0.00 | 0.00 | 2 |
| synthetic-demo | P0 | M1:oracle | horizon | regret_dep | 1.24 | 0.75 | 2 |
| synthetic-demo | P0 | M1:oracle | horizon | forecast_mape | 0.233 | 0.060 | 2 |
| synthetic-demo | P0 | M1:oracle | horizon | censored_share | 0.031 | 0.031 | 2 |
| synthetic-demo | P0 | M1:oracle | horizon | forecast_rmse | 5.774 | 1.014 | 2 |
| synthetic-demo | P0 | M1:oracle | horizon | cumulative_regret | 2.47 | 1.51 | 2 |
| synthetic-demo | P0 | M1:oracle | horizon | price_sd_26 | 0.074 | 0.009 | 2 |
| synthetic-demo | P0 | M1:oracle | horizon | failure_share | 0.000 | 0.000 | 2 |
| synthetic-demo | P0 | M1:oracle | horizon | seconds | 0.049 | 0.021 | 2 |
| synthetic-demo | P0 | M2:greedy | horizon | regret_rec | 1.25 | 0.88 | 2 |
| synthetic-demo | P0 | M2:greedy | horizon | regret_dep | 1.24 | 0.75 | 2 |
| synthetic-demo | P0 | M2:greedy | horizon | forecast_mape | 0.259 | 0.063 | 2 |
| synthetic-demo | P0 | M2:greedy | horizon | censored_share | 0.031 | 0.031 | 2 |
| synthetic-demo | P0 | M2:greedy | horizon | forecast_rmse | 6.848 | 1.192 | 2 |
| synthetic-demo | P0 | M2:greedy | horizon | cumulative_regret | 2.47 | 1.51 | 2 |
| synthetic-demo | P0 | M2:greedy | horizon | price_sd_26 | 0.074 | 0.009 | 2 |
| synthetic-demo | P0 | M2:greedy | horizon | failure_share | 0.000 | 0.000 | 2 |
| synthetic-demo | P0 | M2:greedy | horizon | seconds | 0.638 | 0.022 | 2 |
| synthetic-demo | P0 | M2:oracle | horizon | regret_rec | 0.00 | 0.00 | 2 |
| synthetic-demo | P0 | M2:oracle | horizon | regret_dep | 1.24 | 0.75 | 2 |
| synthetic-demo | P0 | M2:oracle | horizon | forecast_mape | 0.259 | 0.063 | 2 |
| synthetic-demo | P0 | M2:oracle | horizon | censored_share | 0.031 | 0.031 | 2 |
| synthetic-demo | P0 | M2:oracle | horizon | forecast_rmse | 6.848 | 1.192 | 2 |
| synthetic-demo | P0 | M2:oracle | horizon | cumulative_regret | 2.47 | 1.51 | 2 |
| synthetic-demo | P0 | M2:oracle | horizon | price_sd_26 | 0.074 | 0.009 | 2 |
| synthetic-demo | P0 | M2:oracle | horizon | failure_share | 0.000 | 0.000 | 2 |
| synthetic-demo | P0 | M2:oracle | horizon | seconds | 0.385 | 0.004 | 2 |
| synthetic-demo | P0 | M3:greedy | horizon | regret_rec | 2.18 | 0.91 | 2 |
| synthetic-demo | P0 | M3:greedy | horizon | regret_dep | 1.24 | 0.75 | 2 |
| synthetic-demo | P0 | M3:greedy | horizon | forecast_mape | 0.247 | 0.021 | 2 |
| synthetic-demo | P0 | M3:greedy | horizon | censored_share | 0.031 | 0.031 | 2 |
| synthetic-demo | P0 | M3:greedy | horizon | forecast_rmse | 6.522 | 0.204 | 2 |
| synthetic-demo | P0 | M3:greedy | horizon | cumulative_regret | 2.47 | 1.51 | 2 |
| synthetic-demo | P0 | M3:greedy | horizon | price_sd_26 | 0.074 | 0.009 | 2 |
| synthetic-demo | P0 | M3:greedy | horizon | failure_share | 0.000 | 0.000 | 2 |
| synthetic-demo | P0 | M3:greedy | horizon | seconds | 0.294 | 0.042 | 2 |
| synthetic-demo | P0 | M3:oracle | horizon | regret_rec | 0.00 | 0.00 | 2 |
| synthetic-demo | P0 | M3:oracle | horizon | regret_dep | 1.24 | 0.75 | 2 |
| synthetic-demo | P0 | M3:oracle | horizon | forecast_mape | 0.247 | 0.021 | 2 |
| synthetic-demo | P0 | M3:oracle | horizon | censored_share | 0.031 | 0.031 | 2 |
| synthetic-demo | P0 | M3:oracle | horizon | forecast_rmse | 6.522 | 0.204 | 2 |
| synthetic-demo | P0 | M3:oracle | horizon | cumulative_regret | 2.47 | 1.51 | 2 |
| synthetic-demo | P0 | M3:oracle | horizon | price_sd_26 | 0.074 | 0.009 | 2 |
| synthetic-demo | P0 | M3:oracle | horizon | failure_share | 0.000 | 0.000 | 2 |
| synthetic-demo | P0 | M3:oracle | horizon | seconds | 0.150 | 0.009 | 2 |
| synthetic-demo | P0 | M3_cf:greedy | horizon | regret_rec | 2.18 | 0.91 | 2 |
| synthetic-demo | P0 | M3_cf:greedy | horizon | regret_dep | 1.24 | 0.75 | 2 |
| synthetic-demo | P0 | M3_cf:greedy | horizon | forecast_mape | 0.247 | 0.021 | 2 |
| synthetic-demo | P0 | M3_cf:greedy | horizon | censored_share | 0.031 | 0.031 | 2 |
| synthetic-demo | P0 | M3_cf:greedy | horizon | forecast_rmse | 6.522 | 0.204 | 2 |
| synthetic-demo | P0 | M3_cf:greedy | horizon | cumulative_regret | 2.47 | 1.51 | 2 |
| synthetic-demo | P0 | M3_cf:greedy | horizon | price_sd_26 | 0.074 | 0.009 | 2 |
| synthetic-demo | P0 | M3_cf:greedy | horizon | failure_share | 0.000 | 0.000 | 2 |
| synthetic-demo | P0 | M3_cf:greedy | horizon | seconds | 0.270 | 0.003 | 2 |
| synthetic-demo | P0 | M3_cf:oracle | horizon | regret_rec | 0.00 | 0.00 | 2 |
| synthetic-demo | P0 | M3_cf:oracle | horizon | regret_dep | 1.24 | 0.75 | 2 |
| synthetic-demo | P0 | M3_cf:oracle | horizon | forecast_mape | 0.247 | 0.021 | 2 |
| synthetic-demo | P0 | M3_cf:oracle | horizon | censored_share | 0.031 | 0.031 | 2 |
| synthetic-demo | P0 | M3_cf:oracle | horizon | forecast_rmse | 6.522 | 0.204 | 2 |
| synthetic-demo | P0 | M3_cf:oracle | horizon | cumulative_regret | 2.47 | 1.51 | 2 |
| synthetic-demo | P0 | M3_cf:oracle | horizon | price_sd_26 | 0.074 | 0.009 | 2 |
| synthetic-demo | P0 | M3_cf:oracle | horizon | failure_share | 0.000 | 0.000 | 2 |
| synthetic-demo | P0 | M3_cf:oracle | horizon | seconds | 0.167 | 0.017 | 2 |
| synthetic-demo | P0 | M4_pliv:greedy | horizon | regret_rec | 3.09 | 0.00 | 2 |
| synthetic-demo | P0 | M4_pliv:greedy | horizon | regret_dep | 1.24 | 0.75 | 2 |
| synthetic-demo | P0 | M4_pliv:greedy | horizon | forecast_mape | 0.560 | 0.113 | 2 |
| synthetic-demo | P0 | M4_pliv:greedy | horizon | censored_share | 0.031 | 0.031 | 2 |
| synthetic-demo | P0 | M4_pliv:greedy | horizon | forecast_rmse | 15.532 | 6.093 | 2 |
| synthetic-demo | P0 | M4_pliv:greedy | horizon | cumulative_regret | 2.47 | 1.51 | 2 |
| synthetic-demo | P0 | M4_pliv:greedy | horizon | price_sd_26 | 0.074 | 0.009 | 2 |
| synthetic-demo | P0 | M4_pliv:greedy | horizon | failure_share | 0.250 | 0.250 | 2 |
| synthetic-demo | P0 | M4_pliv:greedy | horizon | seconds | 5.068 | 0.089 | 2 |
| synthetic-demo | P0 | M4_pliv:oracle | horizon | regret_rec | 0.00 | 0.00 | 2 |
| synthetic-demo | P0 | M4_pliv:oracle | horizon | regret_dep | 1.24 | 0.75 | 2 |
| synthetic-demo | P0 | M4_pliv:oracle | horizon | forecast_mape | 0.560 | 0.113 | 2 |
| synthetic-demo | P0 | M4_pliv:oracle | horizon | censored_share | 0.031 | 0.031 | 2 |
| synthetic-demo | P0 | M4_pliv:oracle | horizon | forecast_rmse | 15.532 | 6.093 | 2 |
| synthetic-demo | P0 | M4_pliv:oracle | horizon | cumulative_regret | 2.47 | 1.51 | 2 |
| synthetic-demo | P0 | M4_pliv:oracle | horizon | price_sd_26 | 0.074 | 0.009 | 2 |
| synthetic-demo | P0 | M4_pliv:oracle | horizon | failure_share | 0.250 | 0.250 | 2 |
| synthetic-demo | P0 | M4_pliv:oracle | horizon | seconds | 4.733 | 0.021 | 2 |
| synthetic-demo | P0 | M4_plr:greedy | horizon | regret_rec | 1.78 | 0.51 | 2 |
| synthetic-demo | P0 | M4_plr:greedy | horizon | regret_dep | 1.24 | 0.75 | 2 |
| synthetic-demo | P0 | M4_plr:greedy | horizon | forecast_mape | 0.273 | 0.015 | 2 |
| synthetic-demo | P0 | M4_plr:greedy | horizon | censored_share | 0.031 | 0.031 | 2 |
| synthetic-demo | P0 | M4_plr:greedy | horizon | forecast_rmse | 7.512 | 0.168 | 2 |
| synthetic-demo | P0 | M4_plr:greedy | horizon | cumulative_regret | 2.47 | 1.51 | 2 |
| synthetic-demo | P0 | M4_plr:greedy | horizon | price_sd_26 | 0.074 | 0.009 | 2 |
| synthetic-demo | P0 | M4_plr:greedy | horizon | failure_share | 0.000 | 0.000 | 2 |
| synthetic-demo | P0 | M4_plr:greedy | horizon | seconds | 3.742 | 0.127 | 2 |
| synthetic-demo | P0 | M4_plr:oracle | horizon | regret_rec | 0.00 | 0.00 | 2 |
| synthetic-demo | P0 | M4_plr:oracle | horizon | regret_dep | 1.24 | 0.75 | 2 |
| synthetic-demo | P0 | M4_plr:oracle | horizon | forecast_mape | 0.273 | 0.015 | 2 |
| synthetic-demo | P0 | M4_plr:oracle | horizon | censored_share | 0.031 | 0.031 | 2 |
| synthetic-demo | P0 | M4_plr:oracle | horizon | forecast_rmse | 7.512 | 0.168 | 2 |
| synthetic-demo | P0 | M4_plr:oracle | horizon | cumulative_regret | 2.47 | 1.51 | 2 |
| synthetic-demo | P0 | M4_plr:oracle | horizon | price_sd_26 | 0.074 | 0.009 | 2 |
| synthetic-demo | P0 | M4_plr:oracle | horizon | failure_share | 0.000 | 0.000 | 2 |
| synthetic-demo | P0 | M4_plr:oracle | horizon | seconds | 3.324 | 0.001 | 2 |

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
      "arm": "M2:greedy",
      "measure": "regret_rec",
      "sd": 0.300704942069742,
      "target": 0.25,
      "required": 2
    },
    {
      "arm": "M2:greedy_rps:delta=0.03",
      "measure": "regret_rec",
      "sd": 0.4428795397767855,
      "target": 0.25,
      "required": 4
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
    },
    {
      "arm": "M4_pliv:greedy",
      "measure": "regret_rec",
      "sd": 0.6409817788781725,
      "target": 0.25,
      "required": 7
    },
    {
      "arm": "M4_pliv:greedy_rps:delta=0.03",
      "measure": "regret_rec",
      "sd": 0.6409817788781725,
      "target": 0.25,
      "required": 7
    },
    {
      "arm": "M4_plr:greedy",
      "measure": "regret_rec",
      "sd": 0.0,
      "target": 0.25,
      "required": 0
    },
    {
      "arm": "M4_plr:greedy_rps:delta=0.03",
      "measure": "regret_rec",
      "sd": 0.0,
      "target": 0.25,
      "required": 0
    }
  ],
  "reason": "P1 is incomplete; no n_sim decision"
}
```

| run_id | cell | arm | cycle_or_horizon | measure | estimate | mcse | n_reps |
| --- | --- | --- | --- | --- | --- | --- | --- |
| synthetic-demo | P1 | M1:greedy | horizon | regret_rec | 3.09 | 0.00 | 2 |
| synthetic-demo | P1 | M1:greedy | horizon | regret_dep | 2.04 | 0.20 | 2 |
| synthetic-demo | P1 | M1:greedy | horizon | forecast_mape | 0.460 | 0.060 | 2 |
| synthetic-demo | P1 | M1:greedy | horizon | censored_share | 0.031 | 0.031 | 2 |
| synthetic-demo | P1 | M1:greedy | horizon | forecast_rmse | 9.991 | 1.638 | 2 |
| synthetic-demo | P1 | M1:greedy | horizon | cumulative_regret | 4.08 | 0.39 | 2 |
| synthetic-demo | P1 | M1:greedy | horizon | price_sd_26 | 0.086 | 0.001 | 2 |
| synthetic-demo | P1 | M1:greedy | horizon | failure_share | 0.000 | 0.000 | 2 |
| synthetic-demo | P1 | M1:greedy | horizon | seconds | 0.154 | 0.001 | 2 |
| synthetic-demo | P1 | M1:greedy_rps:delta=0.03 | horizon | regret_rec | 3.09 | 0.00 | 2 |
| synthetic-demo | P1 | M1:greedy_rps:delta=0.03 | horizon | regret_dep | 1.92 | 0.24 | 2 |
| synthetic-demo | P1 | M1:greedy_rps:delta=0.03 | horizon | forecast_mape | 0.440 | 0.055 | 2 |
| synthetic-demo | P1 | M1:greedy_rps:delta=0.03 | horizon | censored_share | 0.031 | 0.031 | 2 |
| synthetic-demo | P1 | M1:greedy_rps:delta=0.03 | horizon | forecast_rmse | 9.557 | 1.565 | 2 |
| synthetic-demo | P1 | M1:greedy_rps:delta=0.03 | horizon | cumulative_regret | 3.84 | 0.47 | 2 |
| synthetic-demo | P1 | M1:greedy_rps:delta=0.03 | horizon | price_sd_26 | 0.085 | 0.002 | 2 |
| synthetic-demo | P1 | M1:greedy_rps:delta=0.03 | horizon | failure_share | 0.000 | 0.000 | 2 |
| synthetic-demo | P1 | M1:greedy_rps:delta=0.03 | horizon | seconds | 0.160 | 0.009 | 2 |
| synthetic-demo | P1 | M2:greedy | horizon | regret_rec | 2.75 | 0.21 | 2 |
| synthetic-demo | P1 | M2:greedy | horizon | regret_dep | 1.91 | 0.06 | 2 |
| synthetic-demo | P1 | M2:greedy | horizon | forecast_mape | 0.362 | 0.054 | 2 |
| synthetic-demo | P1 | M2:greedy | horizon | censored_share | 0.031 | 0.031 | 2 |
| synthetic-demo | P1 | M2:greedy | horizon | forecast_rmse | 8.294 | 1.380 | 2 |
| synthetic-demo | P1 | M2:greedy | horizon | cumulative_regret | 3.81 | 0.13 | 2 |
| synthetic-demo | P1 | M2:greedy | horizon | price_sd_26 | 0.085 | 0.001 | 2 |
| synthetic-demo | P1 | M2:greedy | horizon | failure_share | 0.000 | 0.000 | 2 |
| synthetic-demo | P1 | M2:greedy | horizon | seconds | 0.624 | 0.001 | 2 |
| synthetic-demo | P1 | M2:greedy_rps:delta=0.03 | horizon | regret_rec | 2.78 | 0.31 | 2 |
| synthetic-demo | P1 | M2:greedy_rps:delta=0.03 | horizon | regret_dep | 1.78 | 0.10 | 2 |
| synthetic-demo | P1 | M2:greedy_rps:delta=0.03 | horizon | forecast_mape | 0.351 | 0.059 | 2 |
| synthetic-demo | P1 | M2:greedy_rps:delta=0.03 | horizon | censored_share | 0.031 | 0.031 | 2 |
| synthetic-demo | P1 | M2:greedy_rps:delta=0.03 | horizon | forecast_rmse | 8.104 | 1.470 | 2 |
| synthetic-demo | P1 | M2:greedy_rps:delta=0.03 | horizon | cumulative_regret | 3.57 | 0.20 | 2 |
| synthetic-demo | P1 | M2:greedy_rps:delta=0.03 | horizon | price_sd_26 | 0.084 | 0.001 | 2 |
| synthetic-demo | P1 | M2:greedy_rps:delta=0.03 | horizon | failure_share | 0.000 | 0.000 | 2 |
| synthetic-demo | P1 | M2:greedy_rps:delta=0.03 | horizon | seconds | 0.662 | 0.029 | 2 |
| synthetic-demo | P1 | M3:greedy | horizon | regret_rec | 1.46 | 1.29 | 2 |
| synthetic-demo | P1 | M3:greedy | horizon | regret_dep | 1.26 | 0.41 | 2 |
| synthetic-demo | P1 | M3:greedy | horizon | forecast_mape | 0.248 | nan | 1 |
| synthetic-demo | P1 | M3:greedy | horizon | censored_share | 0.031 | 0.031 | 2 |
| synthetic-demo | P1 | M3:greedy | horizon | forecast_rmse | 5.514 | nan | 1 |
| synthetic-demo | P1 | M3:greedy | horizon | cumulative_regret | 2.51 | 0.82 | 2 |
| synthetic-demo | P1 | M3:greedy | horizon | price_sd_26 | 0.082 | 0.001 | 2 |
| synthetic-demo | P1 | M3:greedy | horizon | failure_share | 0.500 | 0.500 | 2 |
| synthetic-demo | P1 | M3:greedy | horizon | seconds | 0.172 | 0.050 | 2 |
| synthetic-demo | P1 | M3:greedy_rps:delta=0.03 | horizon | regret_rec | 1.54 | 1.37 | 2 |
| synthetic-demo | P1 | M3:greedy_rps:delta=0.03 | horizon | regret_dep | 1.22 | 0.38 | 2 |
| synthetic-demo | P1 | M3:greedy_rps:delta=0.03 | horizon | forecast_mape | 0.249 | nan | 1 |
| synthetic-demo | P1 | M3:greedy_rps:delta=0.03 | horizon | censored_share | 0.031 | 0.031 | 2 |
| synthetic-demo | P1 | M3:greedy_rps:delta=0.03 | horizon | forecast_rmse | 5.524 | nan | 1 |
| synthetic-demo | P1 | M3:greedy_rps:delta=0.03 | horizon | cumulative_regret | 2.44 | 0.76 | 2 |
| synthetic-demo | P1 | M3:greedy_rps:delta=0.03 | horizon | price_sd_26 | 0.082 | 0.001 | 2 |
| synthetic-demo | P1 | M3:greedy_rps:delta=0.03 | horizon | failure_share | 0.500 | 0.500 | 2 |
| synthetic-demo | P1 | M3:greedy_rps:delta=0.03 | horizon | seconds | 0.180 | 0.055 | 2 |
| synthetic-demo | P1 | M3_cf:greedy | horizon | regret_rec | 1.46 | 1.29 | 2 |
| synthetic-demo | P1 | M3_cf:greedy | horizon | regret_dep | 1.26 | 0.41 | 2 |
| synthetic-demo | P1 | M3_cf:greedy | horizon | forecast_mape | 0.248 | nan | 1 |
| synthetic-demo | P1 | M3_cf:greedy | horizon | censored_share | 0.031 | 0.031 | 2 |
| synthetic-demo | P1 | M3_cf:greedy | horizon | forecast_rmse | 5.514 | nan | 1 |
| synthetic-demo | P1 | M3_cf:greedy | horizon | cumulative_regret | 2.51 | 0.82 | 2 |
| synthetic-demo | P1 | M3_cf:greedy | horizon | price_sd_26 | 0.082 | 0.001 | 2 |
| synthetic-demo | P1 | M3_cf:greedy | horizon | failure_share | 0.500 | 0.500 | 2 |
| synthetic-demo | P1 | M3_cf:greedy | horizon | seconds | 0.188 | 0.051 | 2 |
| synthetic-demo | P1 | M3_cf:greedy_rps:delta=0.03 | horizon | regret_rec | 1.54 | 1.37 | 2 |
| synthetic-demo | P1 | M3_cf:greedy_rps:delta=0.03 | horizon | regret_dep | 1.22 | 0.38 | 2 |
| synthetic-demo | P1 | M3_cf:greedy_rps:delta=0.03 | horizon | forecast_mape | 0.249 | nan | 1 |
| synthetic-demo | P1 | M3_cf:greedy_rps:delta=0.03 | horizon | censored_share | 0.031 | 0.031 | 2 |
| synthetic-demo | P1 | M3_cf:greedy_rps:delta=0.03 | horizon | forecast_rmse | 5.524 | nan | 1 |
| synthetic-demo | P1 | M3_cf:greedy_rps:delta=0.03 | horizon | cumulative_regret | 2.44 | 0.76 | 2 |
| synthetic-demo | P1 | M3_cf:greedy_rps:delta=0.03 | horizon | price_sd_26 | 0.082 | 0.001 | 2 |
| synthetic-demo | P1 | M3_cf:greedy_rps:delta=0.03 | horizon | failure_share | 0.500 | 0.500 | 2 |
| synthetic-demo | P1 | M3_cf:greedy_rps:delta=0.03 | horizon | seconds | 0.236 | 0.064 | 2 |
| synthetic-demo | P1 | M4_pliv:greedy | horizon | regret_rec | 2.64 | 0.45 | 2 |
| synthetic-demo | P1 | M4_pliv:greedy | horizon | regret_dep | 1.82 | 0.02 | 2 |
| synthetic-demo | P1 | M4_pliv:greedy | horizon | forecast_mape | 1.656 | 0.343 | 2 |
| synthetic-demo | P1 | M4_pliv:greedy | horizon | censored_share | 0.031 | 0.031 | 2 |
| synthetic-demo | P1 | M4_pliv:greedy | horizon | forecast_rmse | 52.103 | 1.785 | 2 |
| synthetic-demo | P1 | M4_pliv:greedy | horizon | cumulative_regret | 3.64 | 0.04 | 2 |
| synthetic-demo | P1 | M4_pliv:greedy | horizon | price_sd_26 | 0.087 | 0.003 | 2 |
| synthetic-demo | P1 | M4_pliv:greedy | horizon | failure_share | 0.000 | 0.000 | 2 |
| synthetic-demo | P1 | M4_pliv:greedy | horizon | seconds | 4.993 | 0.057 | 2 |
| synthetic-demo | P1 | M4_pliv:greedy_rps:delta=0.03 | horizon | regret_rec | 2.64 | 0.45 | 2 |
| synthetic-demo | P1 | M4_pliv:greedy_rps:delta=0.03 | horizon | regret_dep | 1.78 | 0.10 | 2 |
| synthetic-demo | P1 | M4_pliv:greedy_rps:delta=0.03 | horizon | forecast_mape | 2.195 | 1.006 | 2 |
| synthetic-demo | P1 | M4_pliv:greedy_rps:delta=0.03 | horizon | censored_share | 0.031 | 0.031 | 2 |
| synthetic-demo | P1 | M4_pliv:greedy_rps:delta=0.03 | horizon | forecast_rmse | 74.529 | 24.627 | 2 |
| synthetic-demo | P1 | M4_pliv:greedy_rps:delta=0.03 | horizon | cumulative_regret | 3.56 | 0.19 | 2 |
| synthetic-demo | P1 | M4_pliv:greedy_rps:delta=0.03 | horizon | price_sd_26 | 0.087 | 0.004 | 2 |
| synthetic-demo | P1 | M4_pliv:greedy_rps:delta=0.03 | horizon | failure_share | 0.000 | 0.000 | 2 |
| synthetic-demo | P1 | M4_pliv:greedy_rps:delta=0.03 | horizon | seconds | 4.968 | 0.012 | 2 |
| synthetic-demo | P1 | M4_plr:greedy | horizon | regret_rec | 3.09 | 0.00 | 2 |
| synthetic-demo | P1 | M4_plr:greedy | horizon | regret_dep | 2.04 | 0.20 | 2 |
| synthetic-demo | P1 | M4_plr:greedy | horizon | forecast_mape | 0.474 | 0.065 | 2 |
| synthetic-demo | P1 | M4_plr:greedy | horizon | censored_share | 0.031 | 0.031 | 2 |
| synthetic-demo | P1 | M4_plr:greedy | horizon | forecast_rmse | 11.851 | 2.612 | 2 |
| synthetic-demo | P1 | M4_plr:greedy | horizon | cumulative_regret | 4.08 | 0.39 | 2 |
| synthetic-demo | P1 | M4_plr:greedy | horizon | price_sd_26 | 0.086 | 0.001 | 2 |
| synthetic-demo | P1 | M4_plr:greedy | horizon | failure_share | 0.000 | 0.000 | 2 |
| synthetic-demo | P1 | M4_plr:greedy | horizon | seconds | 3.766 | 0.045 | 2 |
| synthetic-demo | P1 | M4_plr:greedy_rps:delta=0.03 | horizon | regret_rec | 3.09 | 0.00 | 2 |
| synthetic-demo | P1 | M4_plr:greedy_rps:delta=0.03 | horizon | regret_dep | 1.92 | 0.24 | 2 |
| synthetic-demo | P1 | M4_plr:greedy_rps:delta=0.03 | horizon | forecast_mape | 0.449 | 0.057 | 2 |
| synthetic-demo | P1 | M4_plr:greedy_rps:delta=0.03 | horizon | censored_share | 0.031 | 0.031 | 2 |
| synthetic-demo | P1 | M4_plr:greedy_rps:delta=0.03 | horizon | forecast_rmse | 11.305 | 2.542 | 2 |
| synthetic-demo | P1 | M4_plr:greedy_rps:delta=0.03 | horizon | cumulative_regret | 3.84 | 0.47 | 2 |
| synthetic-demo | P1 | M4_plr:greedy_rps:delta=0.03 | horizon | price_sd_26 | 0.085 | 0.002 | 2 |
| synthetic-demo | P1 | M4_plr:greedy_rps:delta=0.03 | horizon | failure_share | 0.000 | 0.000 | 2 |
| synthetic-demo | P1 | M4_plr:greedy_rps:delta=0.03 | horizon | seconds | 3.741 | 0.004 | 2 |

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
      "mean_seconds": 0.15426648900029244
    },
    {
      "arm": "M1:greedy_rps:delta=0.03",
      "mean_seconds": 0.1603362640007617
    },
    {
      "arm": "M2:greedy",
      "mean_seconds": 0.6239672224992319
    },
    {
      "arm": "M2:greedy_rps:delta=0.03",
      "mean_seconds": 0.6622116574999382
    },
    {
      "arm": "M3:greedy",
      "mean_seconds": 0.17192595249889558
    },
    {
      "arm": "M3:greedy_rps:delta=0.03",
      "mean_seconds": 0.1803178659993136
    },
    {
      "arm": "M3_cf:greedy",
      "mean_seconds": 0.18766776199936425
    },
    {
      "arm": "M3_cf:greedy_rps:delta=0.03",
      "mean_seconds": 0.23583731400049146
    },
    {
      "arm": "M4_pliv:greedy",
      "mean_seconds": 4.992635593500381
    },
    {
      "arm": "M4_pliv:greedy_rps:delta=0.03",
      "mean_seconds": 4.967971829000817
    },
    {
      "arm": "M4_plr:greedy",
      "mean_seconds": 3.7656848245005676
    },
    {
      "arm": "M4_plr:greedy_rps:delta=0.03",
      "mean_seconds": 3.7414958899998965
    }
  ],
  "ladder_step": "Insufficient P1 runtime"
}
```

Projection assumes 27 cells with the measured P1 arms. The actual protocol compute ladder and full-design arm weights were not supplied; no automatic protocol changes are made.
## Failures
| run_id | cell | arm | cycle_or_horizon | measure | estimate | mcse | n_reps | flag_gt_5_percent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| synthetic-demo | P0 | M1:greedy | horizon | failure_share | 0.000 | 0.000 | 2 | False |
| synthetic-demo | P0 | M1:oracle | horizon | failure_share | 0.000 | 0.000 | 2 | False |
| synthetic-demo | P0 | M2:greedy | horizon | failure_share | 0.000 | 0.000 | 2 | False |
| synthetic-demo | P0 | M2:oracle | horizon | failure_share | 0.000 | 0.000 | 2 | False |
| synthetic-demo | P0 | M3:greedy | horizon | failure_share | 0.000 | 0.000 | 2 | False |
| synthetic-demo | P0 | M3:oracle | horizon | failure_share | 0.000 | 0.000 | 2 | False |
| synthetic-demo | P0 | M3_cf:greedy | horizon | failure_share | 0.000 | 0.000 | 2 | False |
| synthetic-demo | P0 | M3_cf:oracle | horizon | failure_share | 0.000 | 0.000 | 2 | False |
| synthetic-demo | P0 | M4_pliv:greedy | horizon | failure_share | 0.250 | 0.250 | 2 | True |
| synthetic-demo | P0 | M4_pliv:oracle | horizon | failure_share | 0.250 | 0.250 | 2 | True |
| synthetic-demo | P0 | M4_plr:greedy | horizon | failure_share | 0.000 | 0.000 | 2 | False |
| synthetic-demo | P0 | M4_plr:oracle | horizon | failure_share | 0.000 | 0.000 | 2 | False |
| synthetic-demo | P1 | M1:greedy | horizon | failure_share | 0.000 | 0.000 | 2 | False |
| synthetic-demo | P1 | M1:greedy_rps:delta=0.03 | horizon | failure_share | 0.000 | 0.000 | 2 | False |
| synthetic-demo | P1 | M2:greedy | horizon | failure_share | 0.000 | 0.000 | 2 | False |
| synthetic-demo | P1 | M2:greedy_rps:delta=0.03 | horizon | failure_share | 0.000 | 0.000 | 2 | False |
| synthetic-demo | P1 | M3:greedy | horizon | failure_share | 0.500 | 0.500 | 2 | True |
| synthetic-demo | P1 | M3:greedy_rps:delta=0.03 | horizon | failure_share | 0.500 | 0.500 | 2 | True |
| synthetic-demo | P1 | M3_cf:greedy | horizon | failure_share | 0.500 | 0.500 | 2 | True |
| synthetic-demo | P1 | M3_cf:greedy_rps:delta=0.03 | horizon | failure_share | 0.500 | 0.500 | 2 | True |
| synthetic-demo | P1 | M4_pliv:greedy | horizon | failure_share | 0.000 | 0.000 | 2 | False |
| synthetic-demo | P1 | M4_pliv:greedy_rps:delta=0.03 | horizon | failure_share | 0.000 | 0.000 | 2 | False |
| synthetic-demo | P1 | M4_plr:greedy | horizon | failure_share | 0.000 | 0.000 | 2 | False |
| synthetic-demo | P1 | M4_plr:greedy_rps:delta=0.03 | horizon | failure_share | 0.000 | 0.000 | 2 | False |
| synthetic-demo | P2 | M1:greedy | horizon | failure_share | 0.000 | 0.000 | 2 | False |
| synthetic-demo | P2 | M3:greedy | horizon | failure_share | 0.500 | 0.500 | 2 | True |
| synthetic-demo | P2 | M3_cf:greedy | horizon | failure_share | 0.500 | 0.500 | 2 | True |
| synthetic-demo | P3 | M1:greedy | horizon | failure_share | 0.000 | 0.000 | 2 | False |
| synthetic-demo | P3 | M3:greedy | horizon | failure_share | 0.750 | 0.250 | 2 | True |
| synthetic-demo | P3 | M3_cf:greedy | horizon | failure_share | 0.750 | 0.250 | 2 | True |
| synthetic-demo | P4:pass_through=0.05 | M3:legacy | horizon | failure_share | 0.500 | 0.500 | 2 | True |
| synthetic-demo | P4:pass_through=0.05 | M3_cf:legacy | horizon | failure_share | 0.500 | 0.500 | 2 | True |
| synthetic-demo | P4:pass_through=0.1 | M3:legacy | horizon | failure_share | 0.500 | 0.500 | 2 | True |
| synthetic-demo | P4:pass_through=0.1 | M3_cf:legacy | horizon | failure_share | 0.500 | 0.500 | 2 | True |
| synthetic-demo | P4:pass_through=0.2 | M3:legacy | horizon | failure_share | 0.500 | 0.500 | 2 | True |
| synthetic-demo | P4:pass_through=0.2 | M3_cf:legacy | horizon | failure_share | 0.500 | 0.500 | 2 | True |
| synthetic-demo | P4:pass_through=0.5 | M3:legacy | horizon | failure_share | 0.000 | 0.000 | 2 | False |
| synthetic-demo | P4:pass_through=0.5 | M3_cf:legacy | horizon | failure_share | 0.000 | 0.000 | 2 | False |
| synthetic-demo | P4:pass_through=1 | M3:legacy | horizon | failure_share | 0.000 | 0.000 | 2 | False |
| synthetic-demo | P4:pass_through=1 | M3_cf:legacy | horizon | failure_share | 0.000 | 0.000 | 2 | False |

## Censoring
Chosen multiplier: 1.5
| run_id | cell | arm | cycle_or_horizon | measure | estimate | mcse | n_reps |
| --- | --- | --- | --- | --- | --- | --- | --- |
| synthetic-demo | P5:multiplier=1.25 | data:legacy | horizon | censored_share | 0.094 | 0.031 | 2 |
| synthetic-demo | P5:multiplier=1.5 | data:legacy | horizon | censored_share | 0.031 | 0.031 | 2 |
| synthetic-demo | P5:multiplier=2 | data:legacy | horizon | censored_share | 0.000 | 0.000 | 2 |

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
