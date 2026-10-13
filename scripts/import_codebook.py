import argparse
import re
from pathlib import Path

import pandas as pd
from pypdf import PdfReader

from ktsim.io import sha256

EASTER = {1990: "1990-04-15", 1991: "1991-03-31", 1992: "1992-04-19", 1993: "1993-04-11",
          1994: "1994-04-03", 1995: "1995-04-16", 1996: "1996-04-07", 1997: "1997-03-30"}


def import_codebook(path, stores_path, weeks_path):
    text = "\n".join(page.extract_text() for page in PdfReader(path).pages)
    rows = re.findall(r"^\s*(\d{1,3})\s+(\d{2}/\d{2}/\d{2})\s+(\d{2}/\d{2}/\d{2})([^\n]*)",
                      text, flags=re.MULTILINE)
    weeks = pd.DataFrame(rows, columns=["week", "date", "end", "special_event"])
    weeks["week"] = weeks.week.astype(int)
    weeks = weeks[weeks.week <= 400].sort_values("week")
    if weeks.week.tolist() != list(range(1, 401)):
        raise ValueError("Could not extract all 400 codebook weeks")
    weeks["date"] = pd.to_datetime(weeks.date, format="%m/%d/%y")
    weeks["end"] = pd.to_datetime(weeks.end, format="%m/%d/%y")
    weeks["special_event"] = weeks.special_event.str.strip()
    weeks["lent"] = False
    weeks["holiday_easter"] = 0
    for date in EASTER.values():
        date = pd.Timestamp(date)
        mask = weeks.date.le(date) & weeks.end.ge(date)
        if mask.any():
            easter_week = int(weeks.loc[mask, "week"].iloc[0])
            weeks.loc[mask, "holiday_easter"] = 1
            weeks.loc[weeks.week.between(easter_week - 4, easter_week - 1), "lent"] = True
    weeks["holiday_lent"] = weeks.lent.astype(int)
    for event in weeks.special_event.unique():
        if event and event.lower() != "easter":
            name = re.sub(r"[^a-z0-9]+", "_", event.lower()).strip("_")
            weeks[f"holiday_{name}"] = weeks.special_event.eq(event).astype(int)
    section = text.rsplit("Part 6: Dominick", 1)[1].split("Part 7:")[0]
    store_rows = re.findall(r"^\s*(\d{1,3})\s+(.+?)\s+(High|Medium|Low|CubFighter|Cub-Fighter)\s+(\d{1,2})\b",
                            section, flags=re.MULTILINE)
    stores = pd.DataFrame(store_rows, columns=["store", "city", "price_tier", "zone"])
    if len(stores) < 40 or stores.store.duplicated().any():
        raise ValueError("Store metadata extraction failed")
    stores[["store", "zone"]] = stores[["store", "zone"]].astype(int)
    for target in (stores_path, weeks_path):
        target.parent.mkdir(parents=True, exist_ok=True)
    stores.to_csv(stores_path, index=False)
    weeks.to_csv(weeks_path, index=False, date_format="%Y-%m-%d")
    weeks_path.with_suffix(".source.txt").write_text(
        f"Kilts Center Dominick's data manual; SHA-256 {sha256(path)}\n"
        "Week start/end and special-event fields extracted verbatim. Lent and Easter use actual Easter dates.\n")
    print(f"Imported {len(stores)} zoned stores and {len(weeks)} weeks; review before calibration.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import factual store/week tables from the public Kilts PDF")
    parser.add_argument("--manual", type=Path, required=True)
    parser.add_argument("--stores", type=Path, default=Path("data/raw/stores.csv"))
    parser.add_argument("--weeks", type=Path, default=Path("data/fixtures/week_decode.csv"))
    args = parser.parse_args()
    import_codebook(args.manual, args.stores, args.weeks)