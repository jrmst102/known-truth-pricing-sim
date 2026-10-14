import argparse
import json
from pathlib import Path

from ktsim.audit import audit_markdown, candidate_window, coverage_audit
from ktsim.clean import clean_category
from ktsim.cli import read_config
from ktsim.config import CalibrationConfig
from ktsim.io import find_input, load_movement, load_table, sha256, week_table


def main():
    parser = argparse.ArgumentParser(
        description="Audit coverage without changing eligibility rules"
    )
    parser.add_argument("--category", choices=["sna", "tna", "tti"], required=True)
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--stores", type=Path, default=Path("data/raw/stores.csv"))
    parser.add_argument("--search-window", action="store_true")
    args = parser.parse_args()
    movement = load_movement(find_input(args.data_dir, "w" + args.category))
    upc = load_table(find_input(args.data_dir, "upc" + args.category))
    stores = load_table(args.stores)
    cfg = CalibrationConfig(**read_config("configs/calibration.yaml"))
    audit = coverage_audit(movement, upc, stores, cfg, week_table())
    audit["category"] = args.category
    audit["input_checksums"] = {
        str(path): sha256(path)
        for path in (
            find_input(args.data_dir, "w" + args.category),
            find_input(args.data_dir, "upc" + args.category),
            args.stores,
        )
    }
    audit["metadata_source"] = str(args.stores)
    audit["metadata_scope"] = (
        "retained-store table" if "calibration" in args.stores.parts else "full store metadata"
    )
    if args.search_window:
        audit["candidate_window"] = candidate_window(movement, upc, stores, cfg)
        candidate = audit["candidate_window"]
        if candidate:
            lo, hi = candidate["week_range"]
            try:
                clean = clean_category(movement[movement.week.between(lo, hi)], upc, stores, cfg)
                candidate["clean_validation"] = dict(
                    focal_upc=clean.focal_upc,
                    n_stores=len(clean.store_ids),
                    n_rows=len(clean.frame),
                )
            except ValueError as error:
                candidate["clean_validation_error"] = str(error)
    out = args.data_dir / "calibration" / f"coverage_audit_{args.category}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(audit, indent=2) + "\n")
    out.with_suffix(".md").write_text(audit_markdown(audit, args.category))
    print(out)


if __name__ == "__main__":
    main()
