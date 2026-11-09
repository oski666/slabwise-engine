"""Eras of the market (D154, aligned with the public era indices of the hobby): the same groups for the site's tiles,
lists and indices. The set is still written on every card. Promo sets stay in the catalogue but out of the era and
general indices (is_promo)."""
import re

ERAS = ["Vintage", "Classica", "Di mezzo", "Moderna", "Spada e Scudo", "Scarlatto e Violetto"]   # D255: Contemporanea split
SERIES = [("basep", "Vintage"), ("base", "Vintage"), ("gym", "Vintage"), ("neo", "Vintage"), ("si", "Vintage"), ("bog", "Vintage"),
          ("ecard", "Classica"), ("ex", "Classica"), ("pop", "Classica"), ("np", "Classica"),
          ("dp", "Di mezzo"), ("pl", "Di mezzo"), ("hgss", "Di mezzo"), ("col", "Di mezzo"), ("bw", "Di mezzo"), ("ru1", "Di mezzo"),
          ("xy", "Moderna"), ("g1", "Moderna"), ("dc", "Moderna"), ("sm", "Moderna"),
          ("swsh", "Spada e Scudo"), ("cel", "Spada e Scudo"), ("sv", "Scarlatto e Violetto"), ("me", "Scarlatto e Violetto")]
# D211: Japanese printings follow the era of their English counterparts. Modern Japanese set codes are short codes
# (sv2a, m2a, s6a, sm11b, xy8, bw7); the vintage sets have names in our ids (expansion-pack, jungle, mystery-of-the-fossils,
# gold-silver-to-a-new-world, challenge-from-the-darkness...): Vintage. Until D211 every Japanese printing that was not
# "ja:sm" was labelled "Contemporanea", vintage ones included.
JA_SERIES = ((r"^ja:sv(?:\d|-p-)", "Scarlatto e Violetto"), (r"^ja:m(?:\d|-p-)", "Scarlatto e Violetto"), (r"^ja:s(?:\d|-p-)", "Spada e Scudo"),   # D255
             (r"^ja:sm(?:\d|-p-)", "Moderna"), (r"^ja:xy(?:\d|-p-)", "Moderna"), (r"^ja:bw(?:\d|-p-)", "Di mezzo"),
             (r"^ja:dp(?:\d|-p-)", "Di mezzo"))   # D231: the promo series (sv-p, m-p, s-p, sm-p, xy-p, bw-p, dp-p) too


def series_of(cid):
    if cid.startswith("ja:"):
        return next((lab for pat, lab in JA_SERIES if re.match(pat, cid)), "Vintage")
    return next((lab for pre, lab in SERIES if cid.startswith(pre)), "Altro")


is_promo = lambda cid: bool(re.match(r"^[a-z]+p-|^ja:[a-z]+-p-", cid.split("/")[0])) or cid.startswith("svp-")  # noqa: E731  Black Star Promos
