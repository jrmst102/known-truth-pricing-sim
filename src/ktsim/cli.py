import argparse
import hashlib
import json
import logging
import re
import subprocess
from dataclasses import asdict, replace
from datetime import datetime
from itertools import product
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

from ktsim.calibrate import calibrate, check_plausibility
from ktsim.clean import clean_category
from ktsim.config import Calibration, CalibrationConfig, CellConfig, DGMConfig
from ktsim.coverage import audit_coverage, audit_markdown
from ktsim.io import find_input, load_movement, load_table, sha256, week_table
from ktsim.pilot import atomic_json, run_pilot
from ktsim.report import environment, make_report
from ktsim.rng import STAGES


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
            audit = audit_coverage(
                movement, load_table(files["upc" + category]), stores, cfg, calendar
            )
            atomic_json(audit, output / f"coverage_audit_{category}.json")
            (output / f"coverage_audit_{category}.md").write_text(audit_markdown(audit, category))
            window_path = output / "calibration_windows.json"
            windows = json.loads(window_path.read_text()) if window_path.exists() else {}
            if category in windows:
                low, high = windows[category]["week_range"]
                movement = movement[movement.week.between(low, high)]
                audit = audit_coverage(
                    movement, load_table(files["upc" + category]), stores, cfg, calendar
                )
                atomic_json(audit, output / f"coverage_audit_{category}_window.json")
                log.append(f"{category}: documented calibration window {low}–{high}")
            clean = clean_category(
                movement,
                load_table(files["upc" + category]),
                stores,
                cfg,
            )
            holidays = [column for column in calendar if column.startswith("holiday_")]
            clean.frame = clean.frame.merge(
                calendar[["week", *holidays]], on="week", how="left", validate="many_to_one"
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
        previous_path = output / f"calibration_{category}.json"
        if previous_path.exists():
            previous = json.loads(previous_path.read_text())
            historical = previous.get("diagnostics", {}).get("beta_reference_v1_0")
            if historical is not None:
                cal.diagnostics["beta_reference_v1_0"] = historical
            elif not previous.get("diagnostics"):
                cal.diagnostics["beta_reference_v1_0"] = previous["beta_reference"]
        cal.diagnostics["calibration_window"] = audit["week_range"]
        cal.diagnostics["elasticity_review"] = (
            "Code audit: natural log; unit price=price/qty; nonblank sale is promotion; "
            "competitor index is equal-weighted centered log unit price over eligible competing UPCs. "
            "External units/bundle interpretation remains pending; see docs/issues/elasticity-benchmark.md."
        )
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


def expand_cells(raw, dgm, selected, reps=None, estimators=None, stage="validation"):
    if "core" in raw:
        core = raw["core"]
        if set(core["phi"]) != set(dgm.phi_levels):
            raise ValueError("Scenario phi levels differ from the DGM baseline")
        cells = []
        stage_cfg = raw["stages"][stage]
        n_reps = stage_cfg.get("reps")
        if stage == "main":
            path = stage_cfg["decision_file"]
            if not path:
                raise ValueError("Main stage requires stages.main.decision_file from S3")
            decision = json.loads(Path(path).read_text())
            n_reps = decision["n_required"]["n_selected"]
            if not n_reps:
                raise ValueError("Pilot decision is incomplete")
        for env, eta, kappa, phi in product(
            core["environments"], core["eta"], core["kappa"], core["phi"]
        ):
            name = f"{env}:{eta}:{kappa}:{phi:g}"
            count = (
                stage_cfg.get("base_reps", n_reps)
                if (eta, kappa, phi) == ("med", "pos", 0.5)
                else n_reps
            )
            cells.append(
                CellConfig(
                    name,
                    dgm.eta_levels[eta],
                    dgm.kappa_levels[kappa],
                    phi,
                    dgm.exploration["delta"],
                    reps or count,
                    estimators or core["estimators"],
                    core["policies"],
                    environment=env,
                    references=core["references"],
                    pass_through=core["pass_through"],
                    rho_m=dgm.rho_m,
                    sales_process=dgm.sales_process,
                    cost_structure=dgm.cost_shifter["structure"],
                    shock_split=dgm.shock_split,
                    multiplier=dgm.censoring["multiplier"],
                )
            )
        available = {c.name: c for c in cells}
        for name, extension in raw["extensions"].items():
            base = available[extension["base"]]
            available[name] = replace(
                base, name=name, **{k: v for k, v in extension.items() if k != "base"}
            )
        if selected == ["all"]:
            return cells
        unknown = set(selected) - available.keys()
        if unknown:
            raise ValueError(f"Unknown cells: {sorted(unknown)}")
        return [available[name] for name in selected]
    cells = []
    for name in list(raw["cells"]) if selected == ["all"] else selected:
        entry = raw["cells"][name]
        base = dict(
            name=name,
            eta=dgm.eta_levels[entry["eta"]],
            kappa=dgm.kappa_levels[entry["kappa"]],
            phi=entry["phi"],
            delta=entry["delta"],
            reps=reps or entry["reps"],
            estimators=estimators or entry.get("estimators", []),
            policies=entry.get("policies", []),
            data_only=entry.get("data_only", False),
            environment=entry["environment"],
            rho_m=entry.get("rho_m", dgm.rho_m),
            sales_process=entry.get("sales_process", dgm.sales_process),
            cost_structure=dgm.cost_shifter["structure"],
            shock_split=dgm.shock_split,
        )
        if "pass_through_grid" in entry:
            cells.extend(CellConfig(**base, pass_through=v) for v in entry["pass_through_grid"])
        elif "censoring_multipliers" in entry:
            cells.extend(CellConfig(**base, multiplier=v) for v in entry["censoring_multipliers"])
        else:
            cells.append(CellConfig(**base))
    return cells


def protocol_version(path="docs/PROTOCOL_v1.1.md"):
    match = re.search(r"^Protocol version: ([^ ]+)", Path(path).read_text(), re.M)
    if not match:
        raise ValueError("Missing protocol version header")
    return match.group(1)


def pilot_main():
    parser = argparse.ArgumentParser(description="Run known-truth V1.1 stages")
    parser.add_argument("--cells", nargs="+", default=["all"])
    parser.add_argument("--stage", choices=list(STAGES), default="validation")
    parser.add_argument("--n-jobs", type=int, default=1)
    parser.add_argument("--config", default="configs/scenarios.yaml")
    parser.add_argument("--dgm-config", default="configs/dgm_base.yaml")
    parser.add_argument("--estimator-config", default="configs/estimators.yaml")
    parser.add_argument("--decisions-config", default="configs/decisions.yaml")
    parser.add_argument("--calibration", type=Path)
    parser.add_argument("--stores", type=Path)
    parser.add_argument("--week-decode", type=Path, default=Path("data/fixtures/week_decode.csv"))
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--run-id")
    for flag in ("resume", "save-data", "save-storeweek", "synthetic"):
        parser.add_argument("--" + flag, action="store_true")
    parser.add_argument("--reps", type=int)
    parser.add_argument("--cycles", type=int)
    parser.add_argument("--estimators", nargs="+", choices=["M1", "M2", "M3", "M4_plr", "M4_pliv"])
    args = parser.parse_args()
    if args.stage != "validation" and args.synthetic:
        parser.error("Synthetic calibration is available only for validation")
    if args.stage != "validation" and any(
        v is not None for v in (args.reps, args.cycles, args.estimators)
    ):
        parser.error("Smoke overrides require stage validation")
    if (args.reps is not None and args.reps < 1) or (args.cycles is not None and args.cycles < 1):
        parser.error("reps and cycles must be positive")
    if args.resume and not args.run_id:
        parser.error("--resume requires --run-id")
    if args.run_id and (Path(args.run_id).name != args.run_id or args.run_id in {".", ".."}):
        parser.error("run-id must be a directory name")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], text=True).strip())
    if dirty and args.stage != "validation":
        parser.error("Working tree is dirty; commit reviewed code before scientific runs")
    protocol = Path("docs/PROTOCOL_v1.1.md").read_text()
    if args.stage != "validation" and not re.search(r"^Author signature: \S", protocol, re.M):
        parser.error("Scientific stages require the author's protocol signature")
    if args.stage in {"pilot", "main"} and "Deliverables 1 and 2 accepted: yes" not in protocol:
        parser.error("Precision pilot and main require acceptance of Deliverables 1 and 2")
    raw = read_config(args.config)
    version = protocol_version()
    if raw["protocol_version"] != version:
        parser.error("Manifest protocol_version differs from protocol header")
    dgm = DGMConfig(**read_config(args.dgm_config))
    if args.cycles is not None:
        dgm.cycles = args.cycles
    est_cfg = read_config(args.estimator_config)
    cells = expand_cells(raw, dgm, args.cells, args.reps, args.estimators, args.stage)
    if args.stage != "validation" and args.cells != ["all"]:
        parser.error("Scientific stages require all core cells")
    if args.stage != "validation" and "core" not in raw:
        parser.error("Scientific stages require scenarios.yaml")
    calibrations, mechanisms, calibration_ids, checksums, audits = {}, {}, {}, {}, {}
    checks = []
    envs = sorted({c.environment for c in cells})
    if args.calibration and len(envs) != 1:
        parser.error("--calibration requires cells from exactly one environment")
    for env in envs:
        cal_path = (
            Path("data/fixtures/calibration_synthetic.json")
            if args.synthetic
            else (args.calibration or Path(f"data/calibration/calibration_{env}.json"))
        )
        if not cal_path.exists():
            parser.error(f"Missing calibration: {cal_path}")
        cal = Calibration.load(cal_path)
        current = replace(dgm)
        if args.synthetic:
            current.store_zones = {store: 1 if store <= 4 else 2 for store in cal.alpha_s}
        else:
            failures = cal_path.parent / "calibration_failures.json"
            if failures.exists() and env in json.loads(failures.read_text()):
                parser.error(f"Calibration {env} is blocked; resolve its coverage audit")
            store_path = args.stores or cal_path.parent / f"stores_{env}.csv"
            stores = load_table(store_path)
            current.store_zones = dict(zip(stores.store.astype(int), stores.zone.astype(int)))
            current.calendar = week_table(args.week_decode)
            checksums.update(json.loads((cal_path.parent / "checksums.json").read_text()))
            checksums[str(store_path)] = sha256(store_path)
            checksums[str(args.week_decode)] = sha256(args.week_decode)
            all_checks = json.loads((cal_path.parent / "checks.json").read_text())
            checks.extend(c for c in all_checks if c["category"] == env)
            audit_path = cal_path.parent / f"coverage_audit_{env}.json"
            audits[env] = json.loads(audit_path.read_text())
            for suffix in ("window",):
                window_audit = cal_path.parent / f"coverage_audit_{env}_{suffix}.json"
                if window_audit.exists():
                    audits[env][suffix] = json.loads(window_audit.read_text())
        calibrations[env], mechanisms[env] = cal, current
        calibration_ids[env] = sha256(cal_path)
        checksums[str(cal_path)] = sha256(cal_path)
    effective = {
        env: {k: v for k, v in asdict(cfg).items() if k != "calendar"}
        for env, cfg in mechanisms.items()
    }
    manifest = dict(
        commit=commit,
        dirty=dirty,
        synthetic=args.synthetic,
        protocol_version=version,
        spec_version=raw["spec_version"],
        stage=args.stage,
        seed_child_index=STAGES[args.stage],
        calibration_ids=calibration_ids,
        scenario_file_sha256=sha256(args.config),
        figures=[],
        master_seed=raw["master_seed"],
        cells=[asdict(c) for c in cells],
        dgm=effective,
        estimators=est_cfg,
        calibrations={env: asdict(c) for env, c in calibrations.items()},
        coverage_audits=audits,
        checksums=checksums,
        calibration_checks=checks,
        environment=environment(),
        n_jobs=args.n_jobs,
        save_data=args.save_data,
        save_storeweek=args.save_storeweek,
        decisions=read_config(args.decisions_config),
        config_checksums={
            path: sha256(path)
            for path in (
                args.config,
                args.dgm_config,
                args.estimator_config,
                args.decisions_config,
                "docs/PROTOCOL_v1.1.md",
            )
        },
        source_checksums={
            str(p): sha256(p)
            for directory in ("src", "scripts")
            for p in sorted(Path(directory).rglob("*.py"))
        },
    )
    frozen = dict(
        cells=[{k: v for k, v in asdict(c).items() if k != "reps"} for c in cells],
        dgm=effective,
        estimators=est_cfg,
        calibration_ids=calibration_ids,
        decisions=manifest["decisions"],
        protocol_version=version,
        source_checksums=manifest["source_checksums"],
    )
    manifest["scientific_settings_sha256"] = hashlib.sha256(
        json.dumps(frozen, sort_keys=True).encode()
    ).hexdigest()
    if args.stage == "main":
        decision = json.loads(Path(raw["stages"]["main"]["decision_file"]).read_text())
        if decision.get("scientific_settings_sha256") != manifest["scientific_settings_sha256"]:
            parser.error(
                "Scientific settings differ from S3; a protocol amendment and new pilot are required"
            )
    manifest["fingerprint"] = hashlib.sha256(
        json.dumps(manifest, sort_keys=True).encode()
    ).hexdigest()
    run_id = (
        args.run_id
        or datetime.now(ZoneInfo("America/New_York")).strftime("%Y%m%d-%H%M-") + commit[:7]
    )
    output = (args.output_root or Path("outputs") / args.stage) / run_id
    run_pilot(
        cells,
        calibrations,
        mechanisms,
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
