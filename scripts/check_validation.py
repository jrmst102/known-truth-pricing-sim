import argparse
import json

from ktsim.validation import check_run

parser = argparse.ArgumentParser(description="Write V1.1 mechanical acceptance evidence")
parser.add_argument("run_directory")
args = parser.parse_args()
checks = check_run(args.run_directory)
print(json.dumps(checks, indent=2))
if any(value is False for value in checks["acceptance"].values()):
    raise SystemExit("Mechanical acceptance checks failed")
