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
    import numpy as np
    by = defaultdict(list)
    for r in rows:
        if r.get("excluded"):
            continue
        try:
            p = float(r["price_usd"])
            g = int(float(r["grade"]))
            d = _d(r["date"]).toordinal()
        except (TypeError, ValueError, KeyError):
            continue
        if p > 0:
            by[(r["card"], g)].append((d, p, r["item_id"]))
    out = {}
    span = WEEKS * 7
    for sales in by.values():
        if len(sales) <= MIN_OTHERS:
            continue
        sales.sort()
        days = np.array([x[0] for x in sales])
        prices = np.array([x[1] for x in sales])
        lo = np.searchsorted(days, days - span, side="left")
        hi = np.searchsorted(days, days + span, side="right")
        for k in range(len(sales)):
            m = hi[k] - lo[k] - 1
            if m < MIN_OTHERS:
                continue
            others = np.sort(np.concatenate([prices[lo[k]:k], prices[k + 1:hi[k]]]))
            ref = float(others[m // 2]) if m % 2 else math.sqrt(others[m // 2 - 1] * others[m // 2])
            ratio = sales[k][1] / ref
            if ratio > RATIO or ratio < 1 / RATIO:
                out[sales[k][2]] = dict(ref=round(ref, 2), n=int(m), ratio=round(ratio, 3))
    return out
