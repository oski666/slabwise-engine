"""D345, 27 Nov 2026: the long history is written in year shards and read back whole."""
import gzip
import json
import os
import subprocess
import sys

from slabwise.sources import tc_history

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_merge_writes_year_shards_and_load_reads_them(tmp_path):
    rows = [{"card": "a", "tc_grade": 10, "sale_id": i, "sold_date": d, "price_cents": 100}
            for i, d in enumerate(["2021-01-01", "2023-05-01", "2024-02-01", "2025-03-01", "2026-06-01"])]
    json.dump(rows, gzip.open(tmp_path / "history.json.gz", "wt"))
    exp = tmp_path / "exp.json"
    json.dump([{"card": "a", "tc_grade": 10, "sale_id": 4, "sold_date": "2026-06-01", "price_cents": 150},
               {"card": "b", "tc_grade": 9, "sale_id": 9, "sold_date": "2025-07-01", "price_cents": 5}], open(exp, "w"))
    for _ in range(2):                                    # twice: the second run changes nothing
        subprocess.run([sys.executable, os.path.join(HERE, "scripts", "tc_history_merge.py"), str(exp),
                        str(tmp_path / "history.json.gz")], check=True, capture_output=True)
    names = [os.path.basename(p) for p in tc_history.paths(str(tmp_path))]
    assert names == ["history.json.gz", "history_2024.json.gz", "history_2025.json.gz", "history_2026.json.gz"]
    got = sorted((r["card"], r["sale_id"], r["price_cents"]) for r in tc_history.load(str(tmp_path)))
    assert got == [("a", 0, 100), ("a", 1, 100), ("a", 2, 100), ("a", 3, 100), ("a", 4, 150), ("b", 9, 5)]
    assert json.load(gzip.open(tmp_path / "history.json.gz", "rt"))[-1]["sold_date"] < "2024"
