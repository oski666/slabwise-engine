"""Slabvalve counts (D225, D303): how many copies of each card and grade are on sale now.

Only numbers are kept, never the listings (eBay licence §8.1, DATA_SOURCES): for every card searched on every market
in a run, the count per grade, whether a search was cut at 200 results, and when it was read. The counts of the last
runs are merged, newest first, so a card counted in the rotation of the last 48 hours (D300) keeps its count, with
its own date, even when this run did not search it or the eBay step of this run failed.
"""
from datetime import datetime, timedelta, timezone

MAX_AGE_H = 48


def _ts(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def counts_from_listings(L):
    """{card: {"asof", "capped", "n": {grade: count}}} for the cards searched on every market in this run."""
    out = {}
    for cid, q in (L.get("queried") or {}).items():
        n = {}
        for r in L.get("listings") or []:
            if r["card"] == cid:
                n[str(r["grade"])] = n.get(str(r["grade"]), 0) + 1
        out[cid] = {"asof": L["asof"], "capped": bool(q.get("capped")), "n": n}
    return out


def merge(new, old, now=None, max_age_h=MAX_AGE_H):
    """Newest count per card; counts older than max_age_h hours are dropped."""
    now = now or datetime.now(timezone.utc)
    keep = {}
    for src in (old or {}, new or {}):
        for cid, e in src.items():
            if now - _ts(e["asof"]) > timedelta(hours=max_age_h):
                continue
            if cid not in keep or _ts(e["asof"]) >= _ts(keep[cid]["asof"]):
                keep[cid] = e
    return keep


def apply(R, counts):
    """Writes on_sale, on_sale_capped and on_sale_asof on every catalogue card that has a count (base prints only)."""
    newest = None
    for c in R["cards"]:
        e = counts.get(c["id"].split("/")[0]) if "/" not in c["id"] else None
        if e:
            c["on_sale"] = {str(g["grade"]): int(e["n"].get(str(g["grade"]), 0)) for g in c["grades"]}
            c["on_sale_capped"] = bool(e["capped"])
            c["on_sale_asof"] = e["asof"]
            newest = max(newest or e["asof"], e["asof"])
        else:
            for k in ("on_sale", "on_sale_capped", "on_sale_asof"):
                c.pop(k, None)
    R["on_sale_asof"] = newest
    return sum(1 for c in R["cards"] if c.get("on_sale"))
