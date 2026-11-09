"""D183: every catalogue card, English or Japanese, has an engine era (else the site build stops)."""
import json
import os

from slabwise.sources.csv_sales import era_of

ROOT = os.path.join(os.path.dirname(__file__), "..")


def test_every_catalogue_card_has_an_era():
    era_map = json.load(open(os.path.join(ROOT, "data", "raw", "era_map.json")))
    cards = json.load(open(os.path.join(ROOT, "prototype", "data", "cards.json")))
    ja = json.load(open(os.path.join(ROOT, "prototype", "data", "cards_ja.json")))
    for c in cards + ja:
        assert era_of(c["id"], era_map) in {"wotc", "sm_swsh", "sv"}
    assert era_of("ja:mystery-of-the-fossils-146", era_map) == "wotc"
    assert era_of("ja:m2a-240", era_map) == "sv"
    assert era_of("ja:sm9-103", era_map) == "sm_swsh"


def test_d211_japanese_site_eras():
    from slabwise.series import series_of
    assert series_of("ja:expansion-pack-6") == "Vintage"
    assert series_of("ja:mystery-of-the-fossils-146") == "Vintage"
    assert series_of("ja:m2-110") == "Scarlatto e Violetto"    # D255
    assert series_of("ja:sv2a-201") == "Scarlatto e Violetto"
    assert series_of("ja:s6a-095") == "Spada e Scudo"
    assert series_of("swsh7-215") == "Spada e Scudo" and series_of("cel25-4") == "Spada e Scudo"
    assert series_of("sv03.5-199") == "Scarlatto e Violetto" and series_of("me02-130") == "Scarlatto e Violetto"
    assert series_of("ja:sm9-103") == "Moderna"


def test_d217_old_sets_have_an_era():
    from slabwise.series import series_of
    assert era_of("np-39", {}) == era_of("ru1-7", {}) == era_of("bog-8", {}) == "wotc"
    assert (series_of("np-39"), series_of("bog-8"), series_of("ru1-7")) == ("Classica", "Vintage", "Di mezzo")
