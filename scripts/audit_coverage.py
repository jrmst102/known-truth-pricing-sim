"""Audit raw category coverage before changing any calibration sample."""

import argparse
from pathlib import Path

from ktsim.cli import read_config
from ktsim.config import CalibrationConfig
from ktsim.coverage import audit_coverage, audit_markdown
from ktsim.io import find_input, load_movement, load_table, week_table
from ktsim.pilot import atomic_json

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--category", choices=["sna", "tna", "tti"], required=True)
parser.add_argument("--data-dir", type=Path, default=Path("data"))
args = parser.parse_args()
root = args.data_dir
cfg = CalibrationConfig(**read_config("configs/calibration.yaml"))
audit = audit_coverage(
    load_movement(find_input(root, "w" + args.category)),
    load_table(find_input(root, "upc" + args.category)),
    load_table(root / "raw/stores.csv"),
    cfg,
    week_table(root / "fixtures/week_decode.csv"),
)
output = root / "calibration"
output.mkdir(exist_ok=True)
atomic_json(audit, output / f"coverage_audit_{args.category}.json")
(output / f"coverage_audit_{args.category}.md").write_text(audit_markdown(audit, args.category))
