"""Auction-house sales (Goldin, Fanatics Collect via Apify actors) -> sales CSV schema.

Each record is matched to one catalogue printing from its title, or dropped with a
reason. Rules are deliberately strict: an unmatched sale costs little, a sale matched
to the wrong card poisons a whole series. Seller and buyer names are never kept.

Card key: the catalogue id, plus "/1st" or "/shadowless" for Wizards-era editions
(different printings, different prices). Only English cards, only PSA 7-10 single
cards (no lots, packs, signed or altered cards, reprints).
"""
from __future__ import annotations

import re

# catalogue id -> (name regex, set regex or None, card number, allowed years)
CATALOGUE = {
    "base1-4": (r"(?<!dark )(?<!mega )charizard(?! ex| v| gx| vmax)", r"base|game|holo", 4, (1999, 2000)),
    "base1-2": (r"blastoise(?! ex| v)", r"base|game|holo", 2, (1999, 2000)),
    "base1-15": (r"venusaur(?! ex| v)", r"base|game|holo", 15, (1999, 2000)),
    "base1-10": (r"mewtwo(?! ex| v)", r"base|game|holo", 10, (1999, 2000)),
    "base1-3": (r"chansey", r"base|game|holo", 3, (1999, 2000)),
    "base1-1": (r"alakazam(?! ex| v)", r"base|game|holo", 1, (1999, 2000)),
    "base1-8": (r"machamp", r"base|game|holo", 8, (1999, 2000)),
    "base1-58": (r"pikachu", r"base|game", 58, (1999, 2000)),
    "base2-11": (r"snorlax", r"jungle", 11, (1999, 2000)),
    "base3-5": (r"gengar", r"fossil", 5, (1999, 2000)),
    "base3-4": (r"dragonite", r"fossil", 4, (1999, 2000)),
    "base5-4": (r"dark charizard", r"rocket", 4, (2000,)),
    "neo1-9": (r"lugia", r"neo genesis", 9, (2000, 2001)),
    "neo3-14": (r"suicune", r"neo revelation", 14, (2001,)),
    "gym2-1": (r"blaine'?s arcanine", r"gym challenge", 1, (2000,)),
    "gym2-13": (r"misty'?s gyarados", r"gym challenge", 13, (2000,)),
    "sv03.5-199": (r"charizard ex", r"151", 199, (2023,)),
    "sv03.5-205": (r"mew ex", r"151", 205, (2023,)),
    "sv04.5-232": (r"mew ex", r"paldean fates", 232, (2024,)),
    "swsh7-215": (r"umbreon vmax", r"evolving skies", 215, (2021,)),
    "svp-085": (r"pikachu.*grey felt hat|grey felt hat.*pikachu", None, 85, (2023, 2024)),
    "me02-125": (r"mega charizard x ex", r"phantasmal flames", 125, (2025,)),
    "sv03.5-168": (r"charmander", r"151", 168, (2023,)),
}
WOTC = ("base", "neo", "gym")

def card_no(no):
    """A card number as the matcher compares it: 65 for "065", "sv49" for "SV49" (Hidden Fates shiny vault), "tg05"."""
    no = str(no).strip().lower()
    m = re.fullmatch(r"([a-z]*)0*(\d+)", no)
    if not m:
        return -1
    return int(m.group(2)) if not m.group(1) else m.group(1) + m.group(2)


# D102: cards added from visitors' requests (scripts/add_cards.py) live in data/catalogue_extra.json
import json as _json
import os as _os
_EXTRA = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..", "data", "catalogue_extra.json")
if _os.path.exists(_EXTRA):
    for _k, (_name, _setre, _no, _yrs) in _json.load(open(_EXTRA)).items():
        CATALOGUE.setdefault(_k, (_name, _setre, card_no(_no), tuple(_yrs)))

EN_FIX = _os.environ.get("SLABWISE_EN_FIX", "1") == "1"   # D235 (protocol §45 passed)
EN_BARE = _os.environ.get("SLABWISE_EN_BARE", "1") == "1"  # D236 (protocol §46 passed)
_NOT_NUM = re.compile(r"\b(?:psa|gem\W*(?:mt|mint)|mint|nm\W*mt|grade[ds]?|pop(?:ulation)?)\W*\d+(?:\.5)?|\b(?:199\d|20[0-2]\d)\b")
_BARE = re.compile(r"(?<![\w/#.,])0*(\d{1,3})(?![\w/%.,])")


def en_exclude(fix):
        return re.compile(
        r"japanese|korean|chinese|german|french|italian|spanish|portuguese|dutch|indonesian|thai"
        r"|\b(?:ita|italiano|italiana|ger|deu|deutsch|fr|fra|francais|français|esp|español|espanol|kor|chn|ptbr)\b"   # D160: short language tags ("Holo ITA")
        r"|\b(?:tedesc[oaie]|francese|spagnol[oaie]|portoghese|olandese|corean[oa]|cinese|polacc[oa]|deutsche[nr]?|franz[öo]sisch|spanisch|italienisch"
        r"|koreanisch|chinesisch|allemand|anglais|italien|espagnol|alem[aá]n|franc[eé]s|coreano|chino)\b"   # D187: language words in Italian, German, French, Spanish
        r"|\blot\b|collection \(|" + (r"\((?!(?:199\d|20[0-2]\d)\))\d+\)" if fix else r"\(\d+\)") + r"|\bset of\b|complete set|sealed|unopened|booster|\bpack\b|" + (r"(?<!elite trainer )\bbox\b" if fix else r"\bbox\b") + r""
        r"|jumbo|oversize|celebrations|classic collection|" + (r"(?<!prismatic )(?<!mega )evolutions" if fix else r"(?<!prismatic )evolutions") + r"|expedition|base set 2|base set ii\b|base ii\b|legendary collection"
        r"|signed|sketch|autograph|psa/dna|authentic|\bauto\b|topps|sticker|bandai|metal|\bgold\b(?! star)|staff|prerelease"
        r"|stamp|\berror\b|misprint|miscut|no set symbol|no symbol|\bproof\b|test print|\bdeck\b|reverse|cosmos|trainer kit|\bbgs\b|\bcgc\b|\bsgc\b"
        r"|\bpsa\s*(?:10|[1-9](?:\.5)?)\s*\(?\s*(?:oc|mk|st|pd|mc)\b")   # D221: qualified grades (off-centre, marks, stain...) are not the grade


EXCLUDE = en_exclude(EN_FIX)
NUM = re.compile(r"#\s*0*(\d+)|\b0*(\d+)\s*/\s*\d+")
NUM_PREFIX = re.compile(r"\b(sv|tg|gg|rc|sh|sl|h|hgss|dp|bw|xy|sm|swsh)\s*0*(\d+)\b")     # SV49/SV94, TG05/TG30, GG44/GG70; D150: H9/H32 (Skyridge, Aquapolis), SL10 (Call of Legends); D153: promo numbers HGSS03, DP38, BW54, XY121, SM60, SWSH050

SPLIT = {"firered": r"fire\W?red", "leafgreen": r"leaf\W?green", "heartgold": r"heart\W?gold", "soulsilver": r"soul\W?silver"}
STOP = ("the", "of", "and")


def set_re(name):
    """Title regex for a set name (D153). Small words are optional ("Call Legends" and "Call of Legends"), compound
    words may be split ("Fire Red"), FireRed & LeafGreen and HeartGold & SoulSilver also go by FRLG and HGSS; a Black
    Star Promos set only needs "promo", since its numbers (HGSS03, DP38) already name the set."""
    low = (name or "").lower().replace("é", "e")
    if "black star promo" in low:
        return r"\bpromo"
    words = re.findall(r"[a-z0-9]+", low)
    parts = [SPLIT.get(w, re.escape(w)) for w in words if w not in STOP]
    if not parts:
        return None
    rx = r"\b" + r"\W*(?:(?:of|the|and)\W*)?".join(parts) + r"\b"
    if "firered" in words and "leafgreen" in words:
        rx = rf"(?:{rx}|\bfrlg\b)"
    if "heartgold" in words and "soulsilver" in words:
        rx = rf"(?:{rx}|\bhgss\b)"
    return rx
YEAR = re.compile(r"\b(199\d|20[0-2]\d)\b")


# Japanese printings (D28: separate catalogue cards). key -> (name regex EN|JP, card number, set size, set regex or None)
# Verified on TCGdex (ja) by number and illustrator, except s6a-095 (not on TCGdex; known numbering).
JA_CATALOGUE = {
    # (name, number, set total, set name in English titles such as Fanatics' "... Japanese ... 151 ... #201")
    "ja:sv2a-201": (r"charizard ex|リザードンex|リザードン ex", 201, 165, r"\b151\b"),
    "ja:sv2a-208": (r"mew ex|ミュウex|ミュウ ex", 208, 165, r"\b151\b"),
    "ja:sv2a-168": (r"charmander|ヒトカゲ", 168, 165, r"\b151\b"),
    "ja:sv4a-347": (r"mew ex|ミュウex|ミュウ ex", 347, 190, r"shiny treasure"),
    "ja:s6a-095": (r"umbreon vmax|ブラッキーvmax|ブラッキー vmax", 95, 69, r"eevee heroes"),
    "ja:m2-110": (r"mega charizard x ex|メガリザードンxex|メガリザードンx ex", 110, 80, r"inferno x|\bm2\b"),
}
# D134: Japanese counterparts added from the candidate queue (scripts/add_batch.py) live in data/catalogue_ja_extra.json
_JA_EXTRA = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..", "data", "catalogue_ja_extra.json")
if _os.path.exists(_JA_EXTRA):
    for _k, (_name, _no, _tot, _setre) in _json.load(open(_JA_EXTRA, encoding="utf-8")).items():
        JA_CATALOGUE.setdefault(_k, (_name, _no, _tot, _setre))
JP_CHARS = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff]")
JA_SPECIES = _os.environ.get("SLABWISE_JA_SPECIES", "0") == "1"   # D237 (protocol §47)
_SPECIES_FILE = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..", "data", "species_ja.json")
_SPECIES = _json.load(open(_SPECIES_FILE, encoding="utf-8"))["names"] if _os.path.exists(_SPECIES_FILE) else {}
_SPECIES_RE = re.compile("|".join(re.escape(k) for k in sorted(_SPECIES, key=len, reverse=True))) if _SPECIES else None


def _species_en(t):
    """D237: "リザードンex" -> "リザードン charizard ex", "メガリザードン" -> "メガ mega リザードン charizard"."""
    t = _SPECIES_RE.sub(lambda m: f" {m.group(0)} {_SPECIES[m.group(0)]} ", t)
    return " ".join(t.replace("メガ", " メガ mega ").split())


JA_PROMO_NONAME = _os.environ.get("SLABWISE_JA_PROMO_NONAME", "1") == "1"   # D233 (protocol §43 passed)
JA_PROMO_OWN = _os.environ.get("SLABWISE_JA_PROMO_OWN", "1") == "1"         # D234 (protocol §44 passed)
_JA_PROMO_FULL = re.compile(r"(?<![\d/])\b0*(\d{1,3})\s*/\s*(xy|sm|swsh|sv|bw|dp|s|m)\W?p\b")
_JA_PROMO_KEY = re.compile(r"^ja:([a-z]+)-p-0*(\d+)$")
NEW_JA_BOX = _os.environ.get("SLABWISE_JA_BOX", "1") == "1"   # D232 (protocol §42 passed); "0" = before it
# D232: "box" that is part of the card's name ("Special Box", "Stamp Box", "Gift Box"...) is not a sealed box
_BOX_NEW = r"(?<!special\W)(?<!stamp\W)(?<!gift\W)(?<!premium\W)(?<!collection\W)(?<!golden\W)box"


JA_KOR = _os.environ.get("SLABWISE_JA_KOR", "1") == "1"   # D239 (protocol §50 passed)


def ja_exclude(new_box, kor=None):
    kor = JA_KOR if kor is None else kor
    return re.compile(
        (r"(?<![a-z0-9])(?:kor|kr)(?![a-z0-9])|" if kor else "") + r"\blot\b|\(\d+\)|まとめ|セット売り|未開封|" + (_BOX_NEW if new_box else "box") + r"|ボックス|(?<!拡張)パック|(?<!expansion )\bpack\b|sealed|signed|サイン|proxy|プロキシ|"
        r"\bbgs\b|\bcgc\b|\bsgc\b|\bars\b|korean|chinese|韓国|中国|簡体|繁体"
        r"|no\W*rarity|マークなし"                   # D158/D166: No Rarity is a variant of its own, not the regular printing
        r"|\bpsa\s*(?:10|[1-9](?:\.5)?)\s*\(?\s*(?:oc|mk|st|pd|mc)\b")   # D221: qualified grades are not the grade


JA_EXCLUDE = ja_exclude(NEW_JA_BOX)
NUM_TOT = re.compile(r"0*(\d+)\s*/\s*0*(\d+)")


JA_SETCODE = _os.environ.get("SLABWISE_JA_SETCODE", "1") == "1"   # D238 a (protocol §48b passed)
JA_BARE = _os.environ.get("SLABWISE_JA_BARE", "1") == "1"         # D238 b (protocol §49 passed)
_JA_CODES = None


def _ja_codes():
    global _JA_CODES
    if _JA_CODES is None:
        codes = {k[3:].rsplit("-", 1)[0] for k in JA_CATALOGUE}
        codes = sorted(c for c in codes if re.fullmatch(r"[a-z]{1,4}\d{1,2}[a-z]|m\d", c) and c != "sv2a")   # §48b: not SV2a
        _JA_CODES = re.compile(r"(?<![a-z0-9])(?:" + "|".join(map(re.escape, codes)) + r")(?![a-z0-9])") if codes else re.compile(r"(?!x)x")
    return _JA_CODES


def is_japanese(title: str) -> bool:
    t = title.lower()
    return bool(JP_CHARS.search(title) or re.search(r"\bjapanese\b|\bjpn\b|\bjp\b|japan", t))


# D214 (protocol §38): the set is also recognised from the code of our id ("ja:m3-086" -> "m3", "ja:sv-p-288" -> "sv-p")
# and from the Japanese set name of our page (prototype/data/cards_ja.json); not the codes of named (vintage) sets.
_JA_PAGES = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..", "prototype", "data", "cards_ja.json")
_JA_SETNAME = {}
if _os.path.exists(_JA_PAGES):
    _JA_SETNAME = {_c["id"]: (_c.get("set") or "").lower() for _c in _json.load(open(_JA_PAGES, encoding="utf-8"))}
_SETX = {}


def _set_extra(key):
    if key not in _SETX:
        code = key[3:].rsplit("-", 1)[0].lower()
        alts = [r"(?<![a-z0-9])" + re.escape(code) + r"(?![a-z0-9])"] if re.fullmatch(r"[a-z]{1,4}\d{0,2}[a-z]?(?:-p)?", code) else []
        name = _JA_SETNAME.get(key) or ""
        if JP_CHARS.search(name) and len(name) >= 3:              # Japanese words have no word boundaries
            alts.append(re.escape(name))
        _SETX[key] = "|".join(alts) or None
    return _SETX[key]


def _set_ok(key, setre, t):
    x = _set_extra(key) if NEW_JA_RULES else None
    return bool((setre and re.search(setre, t)) or (x and re.search(x, t)))


NEW_JA_RULES = _os.environ.get("SLABWISE_JA_RULES", "1") == "1"   # noqa: E501
NEW_JA_PROMO = _os.environ.get("SLABWISE_JA_PROMO", "1") == "1"   # D231 (protocol §41 passed); "0" = the matcher before it
_JA_PROMO_NO = re.compile(r"(?<![\d/])\b0*(\d{1,3})\s*/\s*(?:xy|sm|swsh|sv|bw|dp|s|m)\W?p\b")   # D214: "0" gives the matcher before §38 (for the test)


def match_japanese(title: str):
    t = " ".join(title.lower().split())
    if NEW_JA_RULES:                                      # D214: "mewtwo-gx" is "mewtwo gx"; "aqua's" is "aquas"
        t = re.sub(r"-(gx|ex|vmax|vstar|v)\b", r" \1", t).replace("'", "").replace("’", "")
    if JA_EXCLUDE.search(t):
        return None, "esclusa (lotto, sigillato, firmata, altro grader...)"
    if JA_SPECIES and _SPECIES_RE is not None:
        t = _species_en(t)
    pairs = {(int(a), int(b)) for a, b in NUM_TOT.findall(t)}
    nums = {int(x) for x in re.findall(r"#\s*0*(\d+)", t)} | {int(x) for x in re.findall(r"\bno\.?\s*0*(\d+)\b", t)}   # D158: vintage "No. 006"
    nums |= {a for a, _ in pairs}                         # D168: "088/087" with the set named also counts as the number
    nums |= {int(x) for x in re.findall(r"(?<![\d/])\b0\d{2}\b(?!\s*/)", t)}   # D168: vintage labels "Base Set Japanese 003"
    if NEW_JA_PROMO:                                      # D231: a promo number written "207/XY-P", "013/SM-P", "227/S-P"
        nums |= {int(x) for x in _JA_PROMO_NO.findall(t)}
    if JA_BARE and not pairs and not re.search(r"#\s*\d|\bno\.?\s*\d", t) and not _JA_PROMO_NO.search(t):   # D238 b (protocol §49)
        nums |= {int(x) for x in _BARE.findall(_NOT_NUM.sub(" ", t))}
    hits = [k for k, (name, no, tot, setre) in JA_CATALOGUE.items() if re.search(name.replace("'", "") if NEW_JA_RULES else name, t)
            and ((no, tot) in pairs or (no in nums and _set_ok(k, setre, t)))]
    if JA_PROMO_NONAME and not hits:                      # D233 (protocol §43): "ポンチョを着たピカチュウ #207/XY-P" is 207/XY-P
        promo = {(int(n), c) for n, c in _JA_PROMO_FULL.findall(t)}
        hits = [k for k in JA_CATALOGUE if (m := _JA_PROMO_KEY.match(k)) and (int(m.group(2)), m.group(1)) in promo]
        own = {JA_CATALOGUE[k][0] for k in hits}
        if hits and any(nm not in own and re.search(nm.replace("'", ""), t)
                        and not (JA_PROMO_OWN and any(re.search(nm.replace("'", ""), o.replace("\\", "")) for o in own))
                        for nm, _, _, _ in JA_CATALOGUE.values()):
            return None, "ambigua"                        # another card of the catalogue is named in the title
    if len(hits) != 1:
        return None, "nessuna carta giapponese del catalogo" if not hits else "ambigua"
    return hits[0], None


NEW_EN_RULES = _os.environ.get("SLABWISE_EN_RULES", "0") == "1"   # D216 (protocol §39): failed T3, off; "1" to test again
_SEP = r"\W*(?:(?:of|the|and)\W*)?"
_SUBSETS = [_SEP.join(w) + r"\b" for w in (("shiny", "vault"), ("galarian", "gallery"), ("trainer", "gallery"), ("radiant", "collection"))]
_PARENT = {}
_PROMO_SPAN = {"xy": (2013, 2016), "sm": (2017, 2020), "swsh": (2019, 2023), "bw": (2011, 2013), "hgss": (2010, 2011),
               "dp": (2007, 2009), "sv": (2023, 2026)}   # D235 (3)
_PROMO_START = {"xy": 2013, "sm": 2017, "swsh": 2019, "bw": 2011, "hgss": 2010, "dp": 2007, "sv": 2023}   # D216 (5): PSA's year for a series' promos
_HYPH = re.compile(r"\\-(?=(?:gx|ex|vmax|vstar|v)\b)")


def _parent_set(setre):
    """D216: "Crown Zenith Galarian Gallery" also as "Crown Zenith" (the GG/SV/TG/RC number already names the subset)."""
    if setre not in _PARENT:
        _PARENT[setre] = next((setre[:-len(_SEP + x)] + r"\b" for x in _SUBSETS if setre.endswith(_SEP + x)), None)
    return _PARENT[setre]


def match_title(title: str):
    """Return (card_key, None) or (None, reason). Japanese titles go to the Japanese catalogue."""
    if is_japanese(title):
        return match_japanese(title)
    if JA_SETCODE and _ja_codes().search(title.lower()):   # D238 a (protocol §48b): only when no English card takes it
        en = _match_english(title)
        return en if en[0] else match_japanese(title)
    return _match_english(title)


def _match_english(title: str):
    t = " ".join(title.lower().replace("’", "'").split())
    if EN_FIX:                                            # D235 (1): "Mega Evolutions" is the set Mega Evolution
        t = re.sub(r"\bmega\W*evolutions\b", "mega evolution", t)
    if EXCLUDE.search(t):
        return None, "esclusa (lingua, lotto, sigillato, firmata, ristampa...)"
    if NEW_EN_RULES:                                      # D216: "charizard-gx" is "charizard gx"
        t = re.sub(r"-(gx|ex|vmax|vstar|v)\b", r" \1", t)
    years = {int(y) for y in YEAR.findall(t)}
    nums = {int(a or b) for a, b in NUM.findall(t)} | {p + n for p, n in NUM_PREFIX.findall(t)}
    if EN_BARE and not NUM.search(t):                      # D236 (protocol §46): "Base Set 10 Mewtwo Holo PSA 7"
        nums |= {int(x) for x in _BARE.findall(_NOT_NUM.sub(" ", t))}
    hits = []
    for cid, (name, setre, no, yrs) in CATALOGUE.items():
        if not re.search(_HYPH.sub(" ", name) if NEW_EN_RULES else name, t):
            continue
        if setre and not re.search(setre, t):
            par = _parent_set(setre) if NEW_EN_RULES and isinstance(no, str) else None
            if not (par and re.search(par, t)):
                continue
        if EN_FIX and years and isinstance(no, str) and setre == r"\bpromo" and (sp := _PROMO_SPAN.get(re.match(r"[a-z]+", no).group(0))):
            yrs = range(sp[0], sp[1] + 1)                 # D235 (3): a promo of a series is valid in every year of the series
        if years and not years & set(yrs) and not (NEW_EN_RULES and setre == r"\bpromo" and isinstance(no, str)
                                                   and years & {_PROMO_START.get(re.match(r"[a-z]+", no).group(0))}):
            continue
        if not nums or no not in nums:
            # D216: a promo number with its prefix ("swsh75") also as the bare number when the prefix is a word of the title
            pm = re.fullmatch(r"(swsh|sm|xy|bw|dp|hgss)(\d+)", no) if NEW_EN_RULES and isinstance(no, str) and setre == r"\bpromo" else None
            if not (pm and int(pm.group(2)) in nums and re.search(rf"\b{pm.group(1)}\b", t)):
                continue
        hits.append(cid)
    if len(hits) != 1:
        return None, "nessuna carta del catalogo" if not hits else "ambigua"
    cid = hits[0]
    if cid.startswith(WOTC):
        if re.search(r"1st ed|first ed|1\s*[°ºa]\s*ed|prima ed|\b1\.\s*ed|erste ed|1(?:re|ère)\s*[ée]d", t):   # D187: 1st edition in Italian, German, French
            cid += "/1st"
        elif "shadowless" in t:
            cid += "/shadowless"
    return refine_variant(cid, t)


def refine_variant(cid, title):
    """Printings that PSA and tcgcharts keep apart (D81): Pikachu's cheeks, Machamp's 1st edition shadowless."""
    t = (title or "").lower()
    if cid in ("base1-58/1st", "base1-58/shadowless"):
        if "red cheek" in t:
            return cid + "-red", None
        if "yellow cheek" in t:
            return cid + "-yellow", None
        return None, "variante ambigua"
    if cid == "base1-8/1st" and "shadowless" in t:
        return "base1-8/1st-shadowless", None
    return cid, None


def to_rows(records, venue):
    """Apify actor records -> (rows for the sales CSV, Counter of drop reasons)."""
    from collections import Counter
    rows, why = [], Counter()
    for r in records:
        grader = (r.get("grader") or "").upper()
        grade = r.get("grade_numeric")
        price = r.get("final_price_with_premium") or r.get("final_sale_price")
        date = r.get("sold_at") or r.get("auction_end_date")
        status = str(r.get("listing_status") or "").lower()
        if "sold" not in status:
            why["non venduta"] += 1
            continue
        if grader != "PSA" or grade is None or int(grade) not in (7, 8, 9, 10) or float(grade) != int(grade):
            why["non PSA 7-10"] += 1
            continue
        if not price or not date:
            why["prezzo o data mancanti"] += 1
            continue
        card, reason = match_title(r.get("title") or "")
        if not card:
            why[reason] += 1
            continue
        cert = r.get("certification_number") or None
        rows.append({"item_id": f"{venue}:{r['lot_id']}", "date": date, "card": card, "grade": int(grade),
                     "price_usd": float(price), "venue": venue, "cert": cert,
                     "title": r.get("title")})
        why["tenuta"] += 1
    return rows, why


GRADE_IN_TITLE = re.compile(
    r"\bpsa\s*(?:gem\s*-?\s*mi?n?t|gem\s*mt|mint|nm\s*-?\s*mt|nm|ex\s*-?\s*mt|ex)?\s*\+?\s*(10|[1-9](?:\.5)?)\b")


def grade_from_title(title: str):
    """PSA grade stated in an eBay title, or None if absent or ambiguous (two grades = lot)."""
    t = title.lower()
    found = {float(x) for x in GRADE_IN_TITLE.findall(t)}
    return int(found.pop()) if len(found) == 1 and float(int(min(found))) == min(found) else None


def ebay_rows(records, site="ebay.com"):
    """eBay sold records (Apify caffein.dev/ebay-sold-listings) -> (sales CSV rows, drop reasons).
    Price = sold price without shipping (schema). Best Offer accepted: eBay shows the asking
    price, not the accepted one, so the row is flagged (the model treats it as an upper bound)."""
    from collections import Counter
    rows, why = [], Counter()
    for r in records:
        if (r.get("soldCurrency") or "USD") != "USD":
            why["valuta non USD"] += 1
            continue
        title = r.get("title") or ""
        if re.search(r"\b(cgc|bgs|sgc|beckett|tag)\b", title.lower()):
            why["altro grader"] += 1
            continue
        grade = grade_from_title(title)
        if grade not in (7, 8, 9, 10):
            why["non PSA 7-10"] += 1
            continue
        card, reason = match_title(title)
        if not card:
            why[reason] += 1
            continue
        try:
            price = float(str(r.get("soldPrice")).replace(",", ""))
        except ValueError:
            why["prezzo mancante"] += 1
            continue
        rows.append({"item_id": f"ebay:{r['itemId']}", "date": r.get("endedAt"), "card": card, "grade": grade,
                     "price_usd": price, "venue": "ebay", "cert": None,
                     "best_offer_hidden": bool(r.get("isBestOfferAccepted")), "title": title})
        why["tenuta"] += 1
    return rows, why
