"""D291: names and sets of the Japanese printings shown in English on the site.

A printing linked to an English card (D152) takes the English card's name. A printing only sold in Japan takes the
translation in data/ja_names_en.json (hand-checked), or else an automatic one from the species names (PokeAPI, D263)
with the usual prefixes and suffixes. The original Japanese name stays as a small caption under the English one.
"""
from __future__ import annotations

import json
import os
import re

_HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
_JA = re.compile(r"[぀-ヿ一-鿿]")
_SUFFIX = (("VSTAR", " VSTAR"), ("VMAX", " VMAX"), ("GX", "-GX"), ("EX", "-EX"), ("ex", " ex"), ("V", " V"))


def has_japanese(s) -> bool:
    return bool(_JA.search(s or ""))


def _load():
    t = json.load(open(os.path.join(_HERE, "ja_names_en.json"), encoding="utf-8"))
    sp = json.load(open(os.path.join(_HERE, "species_ja.json"), encoding="utf-8"))["names"]
    return t["cards"], t["sets"], t.get("words", {}), sp


_CARDS, _SETS, _WORDS, _SPECIES = _load()


def _species(s):
    s = s.strip()
    if s in _WORDS:
        return _WORDS[s]
    if s in _SPECIES:
        return _SPECIES[s].title().replace("'S", "'s")
    return None


def auto_name(n: str):
    """Automatic English name of a Japanese card name, or None when a part is not known."""
    s = n.strip()
    pre = ""
    if s.startswith("メガ"):
        pre, s = "Mega ", s[2:]
    suf = ""
    for k, v in _SUFFIX:
        if s.endswith(k):
            suf, s = v, s[: -len(k)]
            break
    xy = ""
    if pre and s[-1:] in ("X", "Y"):
        xy, s = " " + s[-1], s[:-1]
    if "の" in s:                                         # "ヒロシマのピカチュウ" -> "Hiroshima's Pikachu"
        owner, _, mon = s.rpartition("の")
        a, b = _species(owner) or _WORDS.get(owner), _species(mon)
        return f"{a}'s {b}{suf}" if a and b else None
    b = _species(s)
    return f"{pre}{b}{xy}{suf}" if b else None


def english(card: dict, en_names: dict):
    """(name, set, name_ja, set_ja, ja_only) for a Japanese printing of the catalogue (keys n, set, en, id)."""
    n, st = card.get("n") or "", card.get("set") or ""
    ja_only = not (card.get("en") and card["en"] in en_names)
    if not ja_only:
        name = en_names[card["en"]]
    else:
        name = _CARDS.get(card["id"]) or (auto_name(n) if has_japanese(n) else re.sub(r"\s*\(giapponese\)$", "", n)) or n
    set_en = _SETS.get(st, st)
    return name, set_en, (n if has_japanese(n) else None), (st if has_japanese(st) else None), ja_only
