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


def test_other_grader_with_a_grade_is_out():                # D306, protocol §66
    from slabwise.sources.auction_titles import other_grader
    assert other_grader("GASTLY TEMPORAL FORCES #177 TAG 10 RARER THAN A PSA 10")
    assert other_grader("Pikachu 2023 Crown Zenith #160 ACE 10 LIKE PSA 10")
    assert other_grader("Mega Charizard X EX SAR #110/080 Japanese Inferno X – Beckett 9.5 PSA10")
    assert other_grader("Gardevoir EX #233 ACE GEM MINT 10 (PSA 10 Equivalent)")
    assert not other_grader("2019 POKEMON JP DREAM LEAGUE TAG TEAM SOLGALEO & LUNALA GX 020/049 PSA 10")
    assert not other_grader('Latias & Latios GX SR[SM9 105/095](Expansion Pack "Tag Bolt")')
    assert not other_grader("2005 POKEMON EX UNSEEN FORCES #105 LUGIA EX-HOLO PSA 10")
