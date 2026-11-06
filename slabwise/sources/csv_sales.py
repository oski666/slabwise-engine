"""Load real sales from a CSV in the Slabwise schema (pillar P19).

Required columns: item_id, date (ISO), card, grade, price_usd, venue.
Optional: cert, is_lot, best_offer_hidden, excluded (a removal reason decided by the source, e.g. an unpaid
Fanatics lot, D46; the identity layer applies it and keeps the reason).
``card`` is the catalogue id of the exact printing (e.g. a TCGdex id such as
"swsh7-215" plus language/edition if relevant). Grades outside 7-10 are dropped.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..schema import GRADES


def _flag(raw, col):
    if col not in raw:
        return False
    return raw[col].astype(str).str.strip().str.lower().isin(["true", "1", "yes"]).to_numpy()


def load_sales_csv(path: str, start: str | None = None) -> tuple[pd.DataFrame, list[str]]:
    raw = pd.read_csv(path)
    need = {"item_id", "date", "card", "grade", "price_usd", "venue"}
    missing = need - set(raw.columns)
    if missing:
        raise ValueError(f"colonne mancanti: {sorted(missing)}")
    d = pd.to_datetime(raw["date"], utc=True, format="mixed")
    t0 = pd.Timestamp(start, tz="UTC") if start else d.min().normalize()
    cards = sorted(raw["card"].astype(str).unique())
    cid = {c: i for i, c in enumerate(cards)}
    out = pd.DataFrame({
        "item_id": raw["item_id"].astype(str),
        "day": (d - t0).dt.total_seconds() / 86400.0,
        "card": raw["card"].astype(str).map(cid),
        "grade": pd.to_numeric(raw["grade"], errors="coerce"),
        "cert": raw["cert"].astype(str).where(raw.get("cert", pd.Series(dtype=str)).notna(), None)
        if "cert" in raw else None,
        "venue": np.where(raw["venue"].str.lower().eq("ebay"), "ebay",
                          np.where(raw["venue"].str.lower().str.endswith("_fixed"), "fixed", "auction")),   # D51
        "price": pd.to_numeric(raw["price_usd"], errors="coerce"),
        "flag_lot": _flag(raw, "is_lot"),
        "flag_bo": _flag(raw, "best_offer_hidden"),
        "pre_reason": raw["excluded"].fillna("").astype(str) if "excluded" in raw else "",   # set by the source (D46)
    })
    out = out[out["grade"].isin(GRADES) & (out["price"] > 0) & (out["day"] >= 0)]
    out["grade"] = out["grade"].astype(int)
    out["week"] = (out["day"] // 7).astype(int)
    out = out.sort_values("day").reset_index(drop=True)
    out["sale_id"] = np.arange(len(out))
    return out, cards


PREFIX_ERA = (("ja:mystery-of-the-fossils", "wotc"),                       # D183: vintage Japanese set names before "ja:m"
              ("ja:sv", "sv"), ("ja:sm", "sm_swsh"), ("ja:xy", "sm_swsh"), ("ja:bw", "sm_swsh"),
              ("ja:m", "sv"), ("ja:s", "sm_swsh"),        # Japanese printings follow their English era
              ("base", "wotc"), ("gym", "wotc"), ("neo", "wotc"), ("swsh", "sm_swsh"), ("sm", "sm_swsh"),
              ("svp", "sv"), ("sv", "sv"), ("me", "sv"),
              # D117: older eras without their own pool join the nearest one; the R1/E2 gate of each card decides
              ("ecard", "wotc"), ("ex", "wotc"), ("pop", "wotc"), ("si", "wotc"),   # D150: POP Series, Southern Islands
               ("dp", "wotc"), ("pl", "wotc"), ("hgss", "wotc"), ("col", "wotc"),
              ("bw", "sm_swsh"), ("xy", "sm_swsh"), ("g1", "sm_swsh"), ("dc", "sm_swsh"), ("cel", "sm_swsh"))


def era_of(card: str, era_map: dict) -> str:
    """Era of a catalogue card: the map, else its base printing (edition suffix removed), else the id prefix."""
    if card in era_map:
        return era_map[card]
    base = card.split("/")[0]
    if base in era_map:
        return era_map[base]
    for pre, e in PREFIX_ERA:
        if card.startswith(pre):
            return e
    if card.startswith("ja:"):          # D183: other Japanese printings are older ones (Expansion Pack, Neo, e-series, PCG): like D117
        return "wotc"
    raise KeyError(f"era sconosciuta per {card}: aggiungila a era_map.json")
