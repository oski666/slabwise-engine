import re

from slabwise.sources import auction_titles as at


def test_set_re_short_words_compounds_promos():
    cases = [("Call of Legends", "2011 pokemon call of legends holo lugia #sl7", True),
             ("Call of Legends", "2011 pokemon call legends lugia sl7", True),
             ("FireRed & LeafGreen", "2004 pokemon ex fire red leaf green charizard ex 105/112", True),
             ("FireRed & LeafGreen", "frlg charizard ex 105/112", True),
             ("HGSS Black Star Promos", "2010 heartgold soulsilver promo pikachu #hgss03", True),
             ("Champion's Path", "champions path charizard vmax 74/73", True),
             ("Call of Legends", "pokemon legends awakened", False)]
    for name, title, ok in cases:
        assert bool(re.search(at.set_re(name), title)) is ok, (name, title)


def test_promo_numbers():
    key = "test-promo"
    at.CATALOGUE[key] = ("testmon", at.set_re("HGSS Black Star Promos"), at.card_no("HGSS99"), (2010, 2011))
    try:
        assert at.match_title("2010 Pokemon HeartGold & SoulSilver Promo Holo Testmon #HGSS99 PSA 10 GEM MINT")[0] == key
    finally:
        at.CATALOGUE.pop(key)
