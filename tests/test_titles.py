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


def test_d187_other_languages_and_editions():
    from slabwise.sources.auction_titles import match_title
    assert match_title("Pokemon Flamara Holo Flareon tedesco 3/64 Jungle PSA 9 come nuovo")[0] is None
    assert match_title("Pokemon Mewtwo GX Mewtwo Shining Legends 2017 78/73 PSA 8 tedesco scintillante")[0] is None
    assert match_title("1999 POKEMON JUNGLE 1° EDIZIONE #3 FLAREON-HOLO PSA 9")[0] == "base2-3/1st"
    assert match_title("1999 Pokemon Jungle Flareon Holo 3/64 PSA 9")[0] == "base2-3"
