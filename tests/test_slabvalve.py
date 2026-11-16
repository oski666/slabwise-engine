from datetime import datetime, timezone

from slabwise import slabvalve

NOW = datetime(2026, 11, 16, 18, 0, tzinfo=timezone.utc)


def test_counts_only_for_cards_searched_on_every_market():
    L = {"asof": "2026-11-16T17:00:00Z",
         "listings": [{"card": "base1-4", "grade": 10}, {"card": "base1-4", "grade": 10}, {"card": "base1-4", "grade": 9},
                      {"card": "base1-2", "grade": 8}],
         "queried": {"base1-4": {"markets": 4, "capped": True}}}
    c = slabvalve.counts_from_listings(L)
    assert set(c) == {"base1-4"}
    assert c["base1-4"]["n"] == {"10": 2, "9": 1} and c["base1-4"]["capped"]


def test_merge_keeps_newest_and_drops_old():
    old = {"a": {"asof": "2026-11-15T12:00:00Z", "capped": False, "n": {"10": 1}},
           "b": {"asof": "2026-11-14T12:00:00Z", "capped": False, "n": {"10": 9}}}      # older than 48 hours
    new = {"a": {"asof": "2026-11-16T17:00:00Z", "capped": False, "n": {"10": 3}}}
    m = slabvalve.merge(new, old, now=NOW)
    assert set(m) == {"a"} and m["a"]["n"] == {"10": 3}
    assert slabvalve.merge({}, old, now=NOW)["a"]["n"] == {"10": 1}          # a failed run keeps the last counts


def test_apply_sets_zero_for_grades_without_listings_and_skips_variants():
    R = {"cards": [{"id": "a", "grades": [{"grade": 10}, {"grade": 9}]},
                   {"id": "a/1st", "grades": [{"grade": 10}]},
                   {"id": "z", "grades": [{"grade": 10}], "on_sale": {"10": 5}}]}
    counts = {"a": {"asof": "2026-11-16T17:00:00Z", "capped": False, "n": {"10": 3}}}
    assert slabvalve.apply(R, counts) == 1
    a, v, z = R["cards"]
    assert a["on_sale"] == {"10": 3, "9": 0} and a["on_sale_asof"] == "2026-11-16T17:00:00Z"
    assert "on_sale" not in v and "on_sale" not in z
    assert R["on_sale_asof"] == "2026-11-16T17:00:00Z"
