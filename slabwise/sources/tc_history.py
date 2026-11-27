"""The long tcgcharts history (D80, D123, D345), kept in year shards so no file passes GitHub's 100 MB limit.

data/raw/tcgcharts/history.json.gz holds the sales up to 2023; history_<year>.json.gz one year each from 2024
(27 Nov 2026: the single file had reached 55 MB with half of the new cards still to come). Every reader goes
through paths()/load(); tc_history_merge.py writes them.
"""
import glob
import gzip
import json
import os

FIRST_YEAR_SHARD = 2024


def shard_name(sold_date):
    y = (sold_date or "")[:4]
    return "history.json.gz" if not y.isdigit() or int(y) < FIRST_YEAR_SHARD else f"history_{y}.json.gz"


def paths(tc_dir):
    p = os.path.join(tc_dir, "history.json.gz")
    return ([p] if os.path.exists(p) else []) + sorted(glob.glob(os.path.join(tc_dir, "history_[0-9][0-9][0-9][0-9].json.gz")))


def load(tc_dir):
    out = []
    for p in paths(tc_dir):
        out += json.load(gzip.open(p, "rt", encoding="utf-8"))
    return out
