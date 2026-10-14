"""Evaluate the specification's second eligibility step; never relax coverage."""

import argparse
from pathlib import Path

from ktsim.clean import clean_category
from ktsim.cli import read_config
from ktsim.config import CalibrationConfig
from ktsim.coverage import candidate_windows
from ktsim.io import find_input, load_movement, load_table
from ktsim.pilot import atomic_json

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--category", choices=["sna", "tna", "tti"], required=True)
args = parser.parse_args()
root = Path("data")
cfg = CalibrationConfig(**read_config("configs/calibration.yaml"))
movement = load_movement(find_input(root, "w" + args.category))
upc = load_table(find_input(root, "upc" + args.category))
stores = load_table(root / "raw/stores.csv")
attempts = []
for low, high in candidate_windows(movement, upc, stores, cfg):
    try:
        clean = clean_category(movement[movement.week.between(low, high)], upc, stores, cfg)
        if len(clean.store_ids) < 40:
            raise ValueError("Fewer than 40 retained stores")
    except ValueError as error:
        attempts.append(dict(week_range=[low, high], reason=str(error)))
        continue
    result = dict(
        week_range=[low, high],
        length=high - low + 1,
        n_stores=len(clean.store_ids),
        focal_upc=clean.focal_upc,
        log=clean.log,
        rule="Longest candidate under full-file retained-store screening, earliest start ties; all cleaning rules and store retention rechecked inside the candidate window. Not a proof of the global longest window under changing store sets.",
        prior_rejected=attempts,
    )
    break
else:
    result = dict(eligible=False, prior_rejected=attempts)
atomic_json(result, root / "calibration" / f"window_evaluation_{args.category}.json")
print(result)
