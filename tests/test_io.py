import zipfile

import pandas as pd
import pytest

from ktsim.io import load_movement, load_table, sha256


def test_movement_csv_and_zip(tmp_path):
    csv = tmp_path / "movement.csv"
    csv.write_text("STORE,UPC,WEEK,MOVE,QTY,PRICE,SALE,PROFIT,OK,PRICE_HEX\n"
                   "2,123,1,10,1,2.5,,20,1,ABCD\n")
    zipped = tmp_path / "movement.zip"
    with zipfile.ZipFile(zipped, "w") as archive:
        archive.write(csv, csv.name)
    frame = load_movement(csv)
    pd.testing.assert_frame_equal(frame, load_movement(zipped))
    assert "price_hex" not in frame
    assert frame.price.iloc[0] == 2.5
    assert len(sha256(csv)) == 64


def test_rejects_missing_columns(tmp_path):
    csv = tmp_path / "bad.csv"
    csv.write_text("STORE,UPC\n2,123\n")
    with pytest.raises(ValueError, match="missing movement columns"):
        load_movement(csv)


def test_ambiguous_zip(tmp_path):
    zipped = tmp_path / "ambiguous.zip"
    with zipfile.ZipFile(zipped, "w") as archive:
        archive.writestr("a.csv", "a\n1")
        archive.writestr("b.csv", "b\n2")
    with pytest.raises(ValueError, match="exactly one"):
        load_table(zipped)