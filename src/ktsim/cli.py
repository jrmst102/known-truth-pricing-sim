import argparse
import hashlib
import json
import logging
import subprocess
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

import yaml

from ktsim.audit import coverage_audit
from ktsim.calibrate import calibrate, check_plausibility
from ktsim.calibration_windows import load_calibration_windows
from ktsim.clean import clean_category
from ktsim.config import Calibration, CalibrationConfig, DGMConfig
from ktsim.config_validation import validate_config
from ktsim.io import find_input, load_movement, load_table, sha256, week_table
from ktsim.pilot import atomic_json, run_pilot
from ktsim.protocol import (
    PROTOCOL_VERSION,
    SPEC_VERSION,
    extension_cell,
    scenario_cells,
    validate_protocol,
)
from ktsim.report import environment, make_report
from ktsim.rng import STAGES


def read_config(path):
    with Path(path).open() as stream:
        return validate_config(yaml.safe_load(stream))


def calibration_main():
    parser = argparse.ArgumentParser(description="Calibrate three Dominick's pilot categories")
    parser.add_argument("--config", default="configs/calibration.yaml")
    parser.add_argument(
        "--categories", nargs="+", choices=["sna", "tna", "tti"], default=["sna", "tna", "tti"]
    )
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--stores", type=Path, default=Path("data/raw/stores.csv"))
    parser.add_argument(
        "--windows",
        type=Path,
        help="Window JSON; defaults to <data-dir>/calibration/calibration_windows.json",
    )
    parser.add_argument("--week-decode", type=Path, default=Path("data/fixtures/week_decode.csv"))
    args = parser.parse_args()
    cfg = CalibrationConfig(**read_config(args.config))
    windows_path = args.windows or args.data_dir / "calibration/calibration_windows.json"
    if args.windows is not None and not windows_path.exists():
        parser.error(f"Missing calibration window configuration: {windows_path}")
    windows = load_calibration_windows(windows_path)
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
    if windows_path.exists():
        files["calibration_windows"] = windows_path
    checksums_path = output / "checksums.json"
    checksums = json.loads(checksums_path.read_text()) if checksums_path.exists() else {}
    checksums.update({str(path): sha256(path) for path in files.values()})
    for path, digest in checksums.items():
        log.append(f"- SHA-256 {path}: {digest}")
    atomic_json(checksums, output / "checksums.json")
    for category in args.categories:
        logging.info("Calibrating %s", category)
        try:
            movement = load_movement(files["w" + category])
            upc = load_table(files["upc" + category])
            audit_metadata = dict(
                metadata_source=str(args.stores),
                metadata_sha256=sha256(args.stores),
                metadata_scope="retained-store table"
                if "calibration" in args.stores.parts
                else "full store metadata",
                input_checksums={
                    str(path): checksums[str(path)]
                    for path in (files["w" + category], files["upc" + category], args.stores)
                },
            )
            # Preserve the full-span eligibility audit before applying an approved window.
            audit = coverage_audit(movement, upc, stores, cfg, calendar)
            audit.update(audit_metadata)
            atomic_json(audit, output / f"coverage_audit_{category}.json")
            window = windows.get(category)
            bounds = window["week_range"] if window else None
            if window:
                movement = movement[movement.week.between(*bounds)].copy()
                if movement.empty:
                    raise ValueError(f"No movement rows in approved window {bounds}")
                log.append(
                    f"{category}: applying approved calibration window {bounds}; "
                    f"configuration SHA-256 {sha256(windows_path)}"
                )
                window_audit = coverage_audit(
                    movement, upc, stores, cfg, calendar, week_range=bounds
                )
                window_audit.update(audit_metadata)
                window_audit["calibration_window"] = window
                atomic_json(window_audit, output / f"coverage_audit_{category}_window.json")
            clean = clean_category(movement, upc, stores, cfg, week_range=bounds)
            if window and len(clean.store_ids) < max(
                40, cfg.plausibility.get("retained_stores_min", 40)
            ):
                raise ValueError(
                    "Approved calibration window retains fewer than the required stores"
                )
            holidays = [column for column in calendar if column.startswith("holiday_")]
            clean.frame = clean.frame.merge(
                calendar[["week", *holidays]], on="week", validate="many_to_one"
            )
            if clean.frame[holidays].isna().any().any():
                raise ValueError("Movement weeks outside the codebook")
            cal = calibrate(clean, cfg)
            if window:
                cal.diagnostics["calibration_window"] = dict(
                    week_range=bounds,
                    length=bounds[1] - bounds[0] + 1,
                    configuration_path=str(windows_path),
                    configuration_sha256=sha256(windows_path),
                    observed_week_range=cal.weeks,
                )
            previous_calibration = output / f"calibration_{category}.json"
            if previous_calibration.exists():
                previous = Calibration.load(previous_calibration)
                cal.diagnostics["previous_beta_reference"] = previous.diagnostics.get(
                    "previous_beta_reference", previous.beta_reference
                )
                cal.diagnostics["previous_p_bar"] = previous.diagnostics.get(
                    "previous_p_bar", previous.p_bar
                )
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
                f"{check.status.upper()}"
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


def resolve_calibration(environment, root=Path("data/calibration")):
    failures = root / "calibration_failures.json"
    if failures.exists() and environment in json.loads(failures.read_text()):
        raise ValueError(
            f"{environment} calibration blocked; review coverage audit and calibration log"
        )
    path = root / f"calibration_{environment}.json"
    if not path.exists():
        raise ValueError(f"Missing calibration: {path}")
    return path


def pilot_main():
    parser = argparse.ArgumentParser(description="Run protocol v1.1 simulation stages")
    parser.add_argument("--cells", nargs="+", default=["all"])
    parser.add_argument("--stage", choices=STAGES, default="validation")
    parser.add_argument("--extension")
    parser.add_argument("--n-jobs", type=int, default=1)
    parser.add_argument("--config", default="configs/scenarios.yaml")
    parser.add_argument("--dgm-config", default="configs/dgm_base.yaml")
    parser.add_argument("--estimator-config", default="configs/estimators.yaml")
    parser.add_argument("--decision-config", default="configs/decisions.yaml")
    parser.add_argument("--decision", type=Path)
    parser.add_argument("--calibration-dir", type=Path, default=Path("data/calibration"))
    parser.add_argument("--week-decode", type=Path, default=Path("data/fixtures/week_decode.csv"))
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--run-id")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--save-data", action="store_true")
    parser.add_argument("--save-storeweek", action="store_true")
    parser.add_argument("--synthetic", action="store_true")
    parser.add_argument("--reps", type=int)
    parser.add_argument("--cycles", type=int)
    parser.add_argument("--estimators", nargs="+", choices=["M1", "M2", "M3", "M4_plr", "M4_pliv"])
    args = parser.parse_args()
    scientific = args.stage != "validation"
    if args.synthetic and scientific:
        parser.error("Synthetic fixtures are restricted to validation, not scientific stages")
    if scientific and any(value is not None for value in (args.reps, args.cycles, args.estimators)):
        parser.error("Scientific stages cannot use smoke overrides")
    if (args.reps is not None and args.reps < 1) or (args.cycles is not None and args.cycles < 1):
        parser.error("reps and cycles must be positive")
    if args.resume and not args.run_id:
        parser.error("--resume requires --run-id")
    if args.run_id and (Path(args.run_id).name != args.run_id or args.run_id in {".", ".."}):
        parser.error("run-id must be a directory name, not a path")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], text=True).strip())
    if dirty and scientific:
        parser.error("Working tree is dirty; scientific stages require a reviewed clean commit")
    raw = read_config(args.config)
    try:
        version_raw = (
            raw
            if "protocol_version" in raw
            else dict(protocol_version=PROTOCOL_VERSION, spec_version=SPEC_VERSION)
        )
        validate_protocol(version_raw, scientific=scientific, stage=args.stage)
    except ValueError as error:
        parser.error(str(error))
    dgm = DGMConfig(**read_config(args.dgm_config))
    if args.cycles is not None:
        dgm.cycles = args.cycles
    est_cfg = read_config(args.estimator_config)
    decisions_config = read_config(args.decision_config)
    decision = json.loads(args.decision.read_text()) if args.decision else {}
    if args.stage == "main" and (not decision.get("approved") or not decision.get("n_sim")):
        parser.error("Main requires an explicitly approved pilot decision")
    if args.extension:
        cells, instrument = extension_cell(
            raw, dgm, args.extension, args.stage, args.reps, args.estimators, decision.get("n_sim")
        )
        est_cfg["M3_iv"]["instrument"] = instrument
        est_cfg["M4_dml"]["instrument"] = instrument
    else:
        cells = scenario_cells(
            raw,
            dgm,
            args.stage,
            None if args.cells == ["all"] else args.cells,
            args.reps,
            args.estimators,
            decision.get("n_sim"),
        )
    if not cells:
        parser.error("No matching scenario cells")
    if scientific and args.cells != ["all"]:
        parser.error("Scientific stages require every retained core cell")
    checksums, checks, audits, calibrations = {}, [], {}, {}
    for env in sorted({cell.environment for cell in cells}):
        if args.synthetic:
            path = Path("data/fixtures/calibration_synthetic.json")
            cal = Calibration.load(path)
            dgm.store_zones.update({store: 1 if store <= 4 else 2 for store in cal.alpha_s})
        else:
            try:
                path = resolve_calibration(env, args.calibration_dir)
            except ValueError as error:
                parser.error(str(error))
            cal = Calibration.load(path)
            store_path = args.calibration_dir / f"stores_{env}.csv"
            stores = load_table(store_path)
            dgm.store_zones.update(dict(zip(stores.store.astype(int), stores.zone.astype(int))))
            checksums[str(store_path)] = sha256(store_path)
            audit_path = args.calibration_dir / f"coverage_audit_{env}.json"
            if not audit_path.exists():
                parser.error(f"Missing coverage audit: {audit_path}")
            audits[env] = json.loads(audit_path.read_text())
            window_audit_path = args.calibration_dir / f"coverage_audit_{env}_window.json"
            if window_audit_path.exists():
                audits[env]["calibration_window_audit"] = json.loads(window_audit_path.read_text())
                checksums[str(window_audit_path)] = sha256(window_audit_path)
        calibrations[env] = cal
        checksums[str(path)] = sha256(path)
    if not args.synthetic:
        dgm.calendar = week_table(args.week_decode)
        checksums[str(args.week_decode)] = sha256(args.week_decode)
        check_path = args.calibration_dir / "checks.json"
        checks = json.loads(check_path.read_text()) if check_path.exists() else []
        raw_checksums = args.calibration_dir / "checksums.json"
        if not raw_checksums.exists():
            parser.error("Calibration checksums.json is missing")
        checksums.update(json.loads(raw_checksums.read_text()))
    effective = asdict(dgm)
    effective.pop("calendar")
    config_checksums = {
        path: sha256(path)
        for path in (args.config, args.dgm_config, args.estimator_config, args.decision_config)
    }
    source_checksums = {
        str(path): sha256(path)
        for directory in ("src", "scripts")
        for path in sorted(Path(directory).rglob("*.py"))
    }
    frozen = dict(
        configs=config_checksums,
        sources=source_checksums,
        calibrations=checksums,
        extension=args.extension,
        effective_estimators=est_cfg,
    )
    frozen_hash = hashlib.sha256(json.dumps(frozen, sort_keys=True).encode()).hexdigest()
    if args.stage == "main" and decision.get("scientific_fingerprint") != frozen_hash:
        parser.error("Settings changed since the precision pilot; protocol amendment required")
    manifest = dict(
        commit=commit,
        dirty=dirty,
        synthetic=args.synthetic,
        master_seed=raw["master_seed"],
        protocol_version=PROTOCOL_VERSION,
        spec_version=SPEC_VERSION,
        stage=args.stage,
        seed_child_index=STAGES.index(args.stage),
        cells=[asdict(cell) for cell in cells],
        dgm=effective,
        estimators=est_cfg,
        calibration={k: asdict(v) for k, v in calibrations.items()},
        calibration_ids={
            env: sha256(Path("data/fixtures/calibration_synthetic.json"))
            if args.synthetic
            else sha256(args.calibration_dir / f"calibration_{env}.json")
            for env in calibrations
        },
        scenario_file_sha256=sha256(args.config),
        figures=[],
        checksums=checksums,
        calibration_checks=checks,
        coverage_audits=audits,
        environment=environment(),
        n_jobs=args.n_jobs,
        save_data=args.save_data,
        save_storeweek=args.save_storeweek,
        config_checksums=config_checksums,
        source_checksums=source_checksums,
        decisions_config=decisions_config,
        scientific_fingerprint=frozen_hash,
    )
    manifest["fingerprint"] = hashlib.sha256(
        json.dumps(manifest, sort_keys=True).encode()
    ).hexdigest()
    run_id = args.run_id or datetime.now().strftime("%Y%m%d-%H%M-") + commit[:7]
    output = (args.output_root or Path("outputs") / args.stage) / run_id
    run_pilot(
        cells,
        calibrations,
        dgm,
        est_cfg,
        raw["master_seed"],
        output,
        manifest,
        args.n_jobs,
        args.resume,
        args.save_data,
        args.save_storeweek,
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
