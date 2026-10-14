"""Check saved-run mechanics without starting a simulation."""

import argparse
import json

from ktsim.validation import check_run


def main():
    parser = argparse.ArgumentParser(description="Write v1.1 saved-run validation evidence")
    parser.add_argument("run_directory")
    parser.add_argument("--full-horizon", action="store_true")
    args = parser.parse_args()
    checks = check_run(args.run_directory, require_full_horizon=args.full_horizon)
    print(json.dumps(checks, indent=2))
    if any(value is False for value in checks["acceptance"].values()):
        raise SystemExit("Mechanical acceptance checks failed")


if __name__ == "__main__":
    main()
