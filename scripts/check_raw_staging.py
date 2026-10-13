import subprocess
from pathlib import PurePosixPath

if __name__ == "__main__":
    staged = subprocess.check_output(["git", "diff", "--cached", "--name-only", "-z"])
    blocked = []
    for name in staged.decode().split("\0"):
        path = PurePosixPath(name)
        if (
            name.startswith("data/raw/")
            or name.startswith("data/")
            and path.suffix.lower() in {".zip", ".sas7bdat"}
        ):
            blocked.append(name)
    if blocked:
        raise SystemExit("Do not commit raw Kilts data:\n" + "\n".join(blocked))
