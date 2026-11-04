"""Identity layer (pillar P4): decide *what* was sold before looking at price.

Steps, in order:
1. duplicates: same marketplace item id, or same cert within 3 days at the same price;
2. cert verification: the cert decides the real card and grade; a cert pointing to a
   printing outside the catalogue, or to a grade outside scope, removes the record;
3. listing type: detected lots, Best Offer recorded at asking price.
0. (before all) reasons decided by the source: unpaid, pending or vanished Fanatics lots (D46).

Every removed record keeps a reason. Nothing here looks at whether a price is
"plausible": that is the model's job (P6, P8).

``cert_lookup`` stands in for the PSA public API: it maps a cert to (card, grade).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .schema import GRADES


def sim_cert_lookup(sales: pd.DataFrame):
    """Cert registry built from simulation truth (what the PSA API would answer)."""
    reg = {}
    for cert, card, grade in zip(sales["cert"], sales["t_card"], sales["t_grade"]):
        if cert is not None and isinstance(cert, str):
            reg[cert] = (int(card), int(grade))
    return reg.get


def identity_layer(sales: pd.DataFrame, cert_lookup=None, verify_certs=True,
                   dedup_cross_feed=True, keyword_filters=True) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (clean, removed). ``removed`` has a ``reason`` column."""
    s = sales.sort_values("day").copy()
    s["reason"] = ""
    if "pre_reason" in s:                     # decided by the source, e.g. unpaid Fanatics lot (D46)
        s["reason"] = s["pre_reason"].fillna("").astype(str)
        s = s.drop(columns="pre_reason")

    dup_item = s.duplicated("item_id", keep="first")
    s.loc[dup_item, "reason"] = "duplicato (stesso annuncio)"

    if dedup_cross_feed:
        has = s["cert"].notna() & (s["reason"] == "")
        last = {}
        for idx, cert, day, price in zip(s.index[has], s.loc[has, "cert"], s.loc[has, "day"], s.loc[has, "price"]):
            prev = last.get(cert)
            if prev is not None and day - prev[0] <= 3 and abs(price / prev[1] - 1) < 0.02:
                s.at[idx, "reason"] = "duplicato (stesso cert, altra fonte)"
            else:
                last[cert] = (day, price)

    if verify_certs and cert_lookup is not None:
        has = s["cert"].notna() & (s["reason"] == "")
        for idx, cert in zip(s.index[has], s.loc[has, "cert"]):
            hit = cert_lookup(cert)
            if hit is None:
                continue
            card, grade = hit
            if card < 0:
                s.at[idx, "reason"] = "cert: stampa diversa dal catalogo"
            elif grade not in GRADES:
                s.at[idx, "reason"] = "cert: voto fuori perimetro"
            else:
                s.at[idx, "card"] = card
                s.at[idx, "grade"] = grade
                s.at[idx, "cert_ok"] = True

    if keyword_filters:
        s.loc[(s["reason"] == "") & s["flag_lot"], "reason"] = "lotto di più carte"
        s.loc[(s["reason"] == "") & s["flag_bo"], "reason"] = "Best Offer senza prezzo accettato"

    if "cert_ok" not in s:
        s["cert_ok"] = False
    s["cert_ok"] = s["cert_ok"].fillna(False).astype(bool)
    clean = s[s["reason"] == ""].drop(columns="reason")
    removed = s[s["reason"] != ""]
    return clean.reset_index(drop=True), removed.reset_index(drop=True)
