"""Suspect sales (D274, D275, protocol §61): a sale whose price is far from the other sales of the same atom.

Rule registered before the code: a sale is suspect when its price is more than RATIO times above or below the median
of the other sales of the same card x grade within WEEKS weeks before and after it, with at least MIN_OTHERS of them.
The window around the sale keeps cards that really rose (or fell) over the years from being flagged. Suspect sales
are only proposed: they leave the value only once Oscar confirms them in the exception register.
"""
from __future__ import annotations

import math
from collections import defaultdict
from datetime import date

RATIO = 5.0
WEEKS = 26
MIN_OTHERS = 3


def _d(s: str) -> date:
    return date.fromisoformat(str(s)[:10])


def flag(rows):
    """rows: dicts with item_id, date, card, grade, price_usd (excluded rows are skipped).
    Returns {item_id: dict(ref=median of the others, n=how many, ratio=price/ref)} for the suspect sales."""
    by = defaultdict(list)
    for r in rows:
        if r.get("excluded"):
            continue
        try:
            p = float(r["price_usd"])
        except (TypeError, ValueError):
            continue
        if p > 0:
            by[(r["card"], int(float(r["grade"])))].append((_d(r["date"]), p, r["item_id"]))
    out = {}
    span = WEEKS * 7
    for sales in by.values():
        if len(sales) <= MIN_OTHERS:
            continue
        sales.sort()
        for k, (d, p, iid) in enumerate(sales):
            others = sorted(q for j, (d2, q, _) in enumerate(sales) if j != k and abs((d2 - d).days) <= span)
            if len(others) < MIN_OTHERS:
                continue
            m = len(others)
            ref = others[m // 2] if m % 2 else math.sqrt(others[m // 2 - 1] * others[m // 2])
            ratio = p / ref
            if ratio > RATIO or ratio < 1 / RATIO:
                out[iid] = dict(ref=round(ref, 2), n=m, ratio=round(ratio, 3))
    return out
