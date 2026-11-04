"""Eras of the market (D154, aligned with the public era indices of the hobby): the same groups for the site's tiles,
lists and indices. The set is still written on every card. Promo sets stay in the catalogue but out of the era and
general indices (is_promo)."""
import re

ERAS = ["Vintage", "Classica", "Di mezzo", "Moderna", "Contemporanea"]
SERIES = [("basep", "Vintage"), ("base", "Vintage"), ("gym", "Vintage"), ("neo", "Vintage"), ("si", "Vintage"),
          ("ecard", "Classica"), ("ex", "Classica"), ("pop", "Classica"),
          ("dp", "Di mezzo"), ("pl", "Di mezzo"), ("hgss", "Di mezzo"), ("col", "Di mezzo"), ("bw", "Di mezzo"),
          ("xy", "Moderna"), ("g1", "Moderna"), ("dc", "Moderna"), ("sm", "Moderna"),
          ("swsh", "Contemporanea"), ("cel", "Contemporanea"), ("sv", "Contemporanea"), ("me", "Contemporanea")]
JA_SERIES = {"ja:s": "Contemporanea", "ja:m": "Contemporanea", "ja:sm": "Moderna"}
series_of = lambda cid: (next((lab for pre, lab in sorted(JA_SERIES.items(), key=lambda t: -len(t[0])) if cid.startswith(pre)), "Contemporanea")  # noqa: E731
                         if cid.startswith("ja:") else next((lab for pre, lab in SERIES if cid.startswith(pre)), "Altro"))
is_promo = lambda cid: bool(re.match(r"^[a-z]+p-", cid.split("/")[0])) or cid.startswith("svp-")  # noqa: E731  Black Star Promos
