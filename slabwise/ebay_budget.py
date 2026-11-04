"""Which catalogue cards get their eBay listings checked (D135, replaces the room cap of D118).

eBay allows 5,000 calls a day and each English card searched costs a few calls per run, so only the first N English
cards of the catalogue, in the order they entered it, are searched; the others (and every Japanese printing, whose
listings are not searched yet) enter the catalogue anyway, with deals_off on the site. Prices are not affected:
they come from completed sales.
"""
LIMITS = (("2026-11-09", 70), ("9999-12-31", 300))    # (last day, cards) — 300 once the hourly measurement ends


def limit(today: str) -> int:
    return next(n for last, n in LIMITS if today <= last)


def monitored(cards, today: str) -> set:
    """cards: the English catalogue in file order (prototype/data/cards.json)."""
    return {c["id"] for c in cards[:limit(today)]}
