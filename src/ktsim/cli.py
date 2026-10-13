import argparse
import hashlib
import json
import logging
import subprocess
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

import yaml

from ktsim.calibrate import calibrate, check_plausibility
from ktsim.clean import clean_category
from ktsim.config import Calibration, CalibrationConfig, CellConfig, DGMConfig
from ktsim.io import find_input, load_movement, load_table, sha256, week_table
from ktsim.pilot import atomic_json, run_pilot
from ktsim.report import environment, make_report


def read_config(path):
    with Path(path).open() as stream:
        return yaml.safe_load(stream)


def calibration_main():
    parser = argparse.ArgumentParser(description="Calibrate three Dominick's pilot categories")
    parser.add_argument("--config", default="configs/calibration.yaml")
    parser.add_argument(
        "--categories", nargs="+", choices=["sna", "tna", "tti"], default=["sna", "tna", "tti"]
    )
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--stores", type=Path, default=Path("data/raw/stores.csv"))
    parser.add_argument("--week-decode", type=Path, default=Path("data/fixtures/week_decode.csv"))
    args = parser.parse_args()
    cfg = CalibrationConfig(**read_config(args.config))
    files, missing = {}, []
    for category in args.categories:
        for stem in ("w" + category, "upc" + category):
            try:
                files[stem] = find_input(args.data_dir, stem)
            except FileNotFoundError as error:
                missing.append(str(error))
    for path in (args.stores, args.week_decode):
        if not path.exists():
            missing.append(f"Missing {path}; run scripts/import_codebook.py first")
    if missing:
        parser.error("\n".join(missing))
    stores = load_table(args.stores)
    calendar = week_table(args.week_decode)
    output = args.data_dir / "calibration"
    output.mkdir(parents=True, exist_ok=True)
    log = ["# Calibration Log", "", "Exploratory cleaning rules; protocol review pending.", ""]
    checks_path = output / "checks.json"
    checks = json.loads(checks_path.read_text()) if checks_path.exists() else []
    checks = [check for check in checks if check["category"] not in args.categories]
    failures_path = output / "calibration_failures.json"
    failures = json.loads(failures_path.read_text()) if failures_path.exists() else {}
    log_path = output / "calibration_log.md"
    if log_path.exists():
        log = log_path.read_text().splitlines() + ["", "## Calibration invocation", ""]
    files.update(stores=args.stores, week_decode=args.week_decode)
    checksums = {str(path): sha256(path) for path in files.values()}
    for path, digest in checksums.items():
        log.append(f"- SHA-256 {path}: {digest}")
    atomic_json(checksums, output / "checksums.json")
    for category in args.categories:
        logging.info("Calibrating %s", category)
        try:
            clean = clean_category(
                load_movement(files["w" + category]),
                load_table(files["upc" + category]),
                stores,
                cfg,
            )
            holidays = [column for column in calendar if column.startswith("holiday_")]
            clean.frame = clean.frame.merge(
                calendar[["week", *holidays]], on="week", validate="many_to_one"
            )
            if clean.frame[holidays].isna().any().any():
                raise ValueError("Movement weeks outside the codebook")
            cal = calibrate(clean, cfg)
        except ValueError as error:
            failures[category] = str(error)
            log.extend(["", f"## {category}", f"BLOCKED: {error}"])
            log_path.write_text("\n".join(log) + "\n")
            atomic_json(failures, failures_path)
            logging.error("%s: %s", category, error)
            continue
        failures.pop(category, None)
        cal.save(output / f"calibration_{category}.json")
        cal_checks = check_plausibility(cal, cfg)
        checks.extend(dict(category=category, **asdict(check)) for check in cal_checks)
        log.extend(
            [
                "",
                f"## {category}",
                *clean.log,
                f"Focal UPC: {clean.focal_upc}; substituted: {clean.substituted_focal}",
            ]
        )
        for check in cal_checks:
            log.append(
                f"{check.name}: {check.value:.4f}; expected {check.expected}; "
                f"{'PASS' if check.passed else 'FAIL - author review required; no silent fallback'}"
            )
        (output / "calibration_log.md").write_text("\n".join(log) + "\n")
        atomic_json(checks, output / "checks.json")
        stores[stores.store.isin(cal.alpha_s)].to_csv(
            output / f"stores_{category}.csv", index=False
        )
        atomic_json(failures, failures_path)
    logging.info("Calibration outputs: %s", output)
    if any(category in failures for category in args.categories):
        raise SystemExit(
            "Calibration incomplete; see data/calibration/calibration_log.md. "
            "Author-approved protocol guidance is required; thresholds were not relaxed."
        )


def expand_cells(raw, dgm, selected, reps=None, estimators=None):
    cells = []
    for name in selected:
        entry = raw["cells"][name]
        base = dict(
            name=name,
            eta=dgm.eta_levels[entry["eta"]],
            kappa=dgm.kappa_levels[entry["kappa"]],
            phi=entry["phi"],
            delta=0.0,
            reps=reps or entry["reps"],
            estimators=estimators or entry.get("estimators", []),
            policies=entry.get("policies", []),
            data_only=entry.get("data_only", False),
        )
        if name == "P4":
            cells.extend(
                CellConfig(**base, pass_through=value) for value in entry["pass_through_grid"]
            )
        elif name == "P5":
            cells.extend(
                CellConfig(**base, multiplier=value) for value in entry["censoring_multipliers"]
            )
        elif isinstance(entry["delta"], list):
            for delta in entry["delta"]:
                values = dict(
                    base, delta=delta, policies=["greedy"] if delta == 0 else ["greedy_rps"]
                )
                cells.append(CellConfig(**values))
        else:
            cells.append(CellConfig(**dict(base, delta=entry["delta"])))
    return cells


def pilot_main():
    parser = argparse.ArgumentParser(description="Run known-truth pilot cells")
    parser.add_argument("--cells", nargs="+", default=["P0"])
    parser.add_argument("--n-jobs", type=int, default=1)
    parser.add_argument("--config", default="configs/pilot_cells.yaml")
    parser.add_argument("--dgm-config", default="configs/dgm_base.yaml")
    parser.add_argument("--estimator-config", default="configs/estimators.yaml")
    parser.add_argument("--calibration", type=Path)
    parser.add_argument("--stores", type=Path)
    parser.add_argument("--week-decode", type=Path, default=Path("data/fixtures/week_decode.csv"))
    parser.add_argument("--output-root", type=Path, default=Path("outputs/pilot"))
    parser.add_argument("--run-id")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--save-data", action="store_true")
    parser.add_argument("--synthetic", action="store_true")
    parser.add_argument("--reps", type=int)
    parser.add_argument("--cycles", type=int)
    parser.add_argument("--estimators", nargs="+", choices=["M1", "M2", "M3", "M4_plr", "M4_pliv"])
    args = parser.parse_args()
    if not args.synthetic and any(
        value is not None for value in (args.reps, args.cycles, args.estimators)
    ):
        parser.error("Smoke overrides (--reps/--cycles/--estimators) require --synthetic")
    if args.reps is not None and args.reps < 1 or args.cycles is not None and args.cycles < 1:
        parser.error("reps and cycles must be positive")
    if args.resume and not args.run_id:
        parser.error("--resume requires --run-id")
    if args.run_id and (Path(args.run_id).name != args.run_id or args.run_id in {".", ".."}):
        parser.error("run-id must be a directory name, not a path")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], text=True).strip())
    if dirty and not args.synthetic:
        parser.error("Working tree is dirty; commit reviewed code before running a real-data pilot")
    raw = read_config(args.config)
    selected = list(raw["cells"]) if args.cells == ["all"] else args.cells
    if any(name not in raw["cells"] for name in selected):
        parser.error("Unknown cell; expected P0-P5 or all")
    dgm = DGMConfig(**read_config(args.dgm_config))
    if args.cycles is not None:
        dgm.cycles = args.cycles
    est_cfg = read_config(args.estimator_config)
    checksums, checks = {}, []
    if args.synthetic:
        cal_path = Path("data/fixtures/calibration_synthetic.json")
        cal = Calibration.load(cal_path)
        dgm.store_zones = {store: 1 if store <= 4 else 2 for store in cal.alpha_s}
    else:
        cal_path = args.calibration or Path("data/calibration/calibration_tna.json")
        failures_path = cal_path.parent / "calibration_failures.json"
        if failures_path.exists() and "tna" in json.loads(failures_path.read_text()):
            parser.error(
                "Tuna calibration is blocked; resolve calibration_log.md before running the pilot"
            )
        if not cal_path.exists():
            parser.error("Tuna calibration missing; run scripts/run_calibration.py first")
        cal = Calibration.load(cal_path)
        store_path = args.stores or cal_path.parent / "stores_tna.csv"
        if not store_path.exists():
            parser.error(f"Missing {store_path}")
        stores = load_table(store_path)
        dgm.store_zones = dict(zip(stores.store.astype(int), stores.zone.astype(int)))
        dgm.calendar = week_table(args.week_decode)
        checks_path = cal_path.parent / "checks.json"
        if checks_path.exists():
            checks = json.loads(checks_path.read_text())
        checksums_path = cal_path.parent / "checksums.json"
        if checksums_path.exists():
            checksums = json.loads(checksums_path.read_text())
        else:
            parser.error("Calibration checksums.json is missing")
        checksums[str(store_path)] = sha256(store_path)
        checksums[str(args.week_decode)] = sha256(args.week_decode)
    checksums[str(cal_path)] = sha256(cal_path)
    cells = expand_cells(raw, dgm, selected, args.reps, args.estimators)
    effective = asdict(dgm)
    effective.pop("calendar")
    manifest = dict(
        commit=commit,
        dirty=dirty,
        synthetic=args.synthetic,
        master_seed=raw["master_seed"],
        cells=[asdict(cell) for cell in cells],
        dgm=effective,
        estimators=est_cfg,
        calibration=asdict(cal),
        checksums=checksums,
        calibration_checks=checks,
        environment=environment(),
        n_jobs=args.n_jobs,
        save_data=args.save_data,
        config_checksums={
            path: sha256(path) for path in (args.config, args.dgm_config, args.estimator_config)
        },
        source_checksums={
            str(path): sha256(path)
            for directory in ("src", "scripts")
            for path in sorted(Path(directory).rglob("*.py"))
        },
    )
    fingerprint = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()
    manifest["fingerprint"] = fingerprint
    run_id = args.run_id or datetime.now().strftime("%Y%m%d-%H%M-") + commit[:7]
    output = args.output_root / run_id
    run_pilot(
        cells,
        cal,
        dgm,
        est_cfg,
        raw["master_seed"],
        output,
        manifest,
        args.n_jobs,
        args.resume,
        args.save_data,
    )
    logging.info("Report: %s", make_report(output))


def report_main():
    parser = argparse.ArgumentParser(description="Render a pilot report from stored outputs")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output-root", type=Path, default=Path("outputs/pilot"))
    args = parser.parse_args()
    if Path(args.run_id).name != args.run_id or args.run_id in {".", ".."}:
        parser.error("run-id must be a directory name")
    logging.info("Report: %s", make_report(args.output_root / args.run_id))


def entry(main):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        main()
    except (ValueError, FileNotFoundError, FileExistsError) as error:
        raise SystemExit(str(error)) from error
