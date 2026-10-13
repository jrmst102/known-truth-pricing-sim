from __future__ import annotations

import hashlib
import io
import zipfile
from pathlib import Path

import pandas as pd


def load_table(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as archive:
            names = [name for name in archive.namelist()
                     if Path(name).suffix.lower() in {".csv", ".sas7bdat"}]
            if len(names) != 1:
                raise ValueError(f"{path}: expected exactly one CSV or SAS dataset")
            with archive.open(names[0]) as stream:
                if names[0].lower().endswith(".csv"):
                    frame = pd.read_csv(stream, low_memory=False)
                else:
                    frame = pd.read_sas(io.BytesIO(stream.read()), format="sas7bdat",
                                        encoding="latin1")
    elif path.suffix.lower() == ".sas7bdat":
        frame = pd.read_sas(path, encoding="latin1")
    else:
        frame = pd.read_csv(path, low_memory=False)
    frame.columns = frame.columns.str.strip().str.lower()
    return frame.loc[:, ~frame.columns.str.endswith("_hex")]


def load_movement(path: str | Path) -> pd.DataFrame:
    frame = load_table(path)
    required = {"upc", "store", "week", "move", "price", "qty", "profit", "sale", "ok"}
    missing = required - set(frame)
    if missing:
        raise ValueError(f"{path}: missing movement columns {sorted(missing)}")
    return frame


def sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def find_input(root: Path, stem: str) -> Path:
    for directory in (root / "raw", root):
        for suffix in (".csv", ".zip", ".sas7bdat"):
            path = directory / (stem + suffix)
            if path.exists():
                return path
    raise FileNotFoundError(f"Missing {stem}.csv (or .zip/.sas7bdat) in {root / 'raw'} or {root}")


def week_table(path: str | Path = "data/fixtures/week_decode.csv") -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError("Authoritative week_decode.csv is required; dates are not guessed")
    frame = pd.read_csv(path, parse_dates=["date"])
    if frame.week.tolist() != list(range(1, 401)):
        raise ValueError("week_decode.csv must contain weeks 1 through 400 in order")
    return frame