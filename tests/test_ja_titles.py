"""D214 (protocol §38): Japanese titles that write the set code of our id, or a hyphen before the suffix."""
from slabwise.sources import auction_titles as at


def test_d214_set_code_and_hyphen():
    at.NEW_JA_RULES = True
    assert at.match_japanese("2023 Pokemon Sv2a Japanese Art Rare #168 Charmander PSA 10 GEM MINT")[0] == "ja:sv2a-168"
    assert at.match_japanese("2023 Pokemon SV2a JP Mew Ex ULTRA RARE PSA 10 #208 JP")[0] == "ja:sv2a-208"
    # the number stays required: same set code, another number
    assert at.match_japanese("2023 Pokemon Sv2a Japanese Art Rare #169 Charmander PSA 10")[0] is None
    # a code inside another word is not the set ("sv2ab" is not "sv2a")
    assert at.match_japanese("2023 Pokemon Sv2ab Japanese Art Rare #168 Charmander PSA 10")[0] is None


def test_d214_rules_off_as_before():
    at.NEW_JA_RULES = False
    try:
        assert at.match_japanese("2023 Pokemon Sv2a Japanese Art Rare #168 Charmander PSA 10 GEM MINT")[0] is None
    finally:
        at.NEW_JA_RULES = True


def test_d221_qualified_grades_excluded():
    assert at.match_title("2022 Pokemon Giratina V Alt Art Lost Origin 186/196 PSA 9 (OC) MINT")[1].startswith("esclusa")
    assert at.match_title("2013 POKEMON B&W PLASMA STORM #136 CHARIZARD PSA 9 OC")[1].startswith("esclusa")
    assert at.match_title("2013 POKEMON B&W PLASMA STORM #136 CHARIZARD PSA 9 MINT")[1] is None or not at.match_title("2013 POKEMON B&W PLASMA STORM #136 CHARIZARD PSA 9 MINT")[1].startswith("esclusa")


def test_d231_promo_numbers():
    import importlib
    import sys
    sys.path.insert(0, "scripts")
    cr = importlib.import_module("card_requests")
    at.NEW_JA_PROMO = True
    at.JA_CATALOGUE["ja:xy-p-207"] = tuple(cr.ja_entry("Poncho-wearing Pikachu", None, "207", None, "XY Promos"))
    at.JA_CATALOGUE["ja:xy-p-230"] = tuple(cr.ja_entry("Poncho-wearing Pikachu", None, "230", None, "XY Promos"))
    try:
        assert at.match_title("PSA 10 Poncho Wearing Pikachu Mega Charizard X 207/XY-P Japanese Pokemon Promo")[0] == "ja:xy-p-207"
        assert at.match_title("2016 Pokemon Japanese XY Promo Full Art Rayquaza Poncho Wearing Pikachu #230 PSA 10 GEM MINT")[0] == "ja:xy-p-230"
        assert at.match_title("PSA 10 Poncho Wearing Pikachu 231/XY-P Promo Japanese Pokemon Card")[0] is None   # not in the catalogue
    finally:
        at.JA_CATALOGUE.pop("ja:xy-p-207", None)
        at.JA_CATALOGUE.pop("ja:xy-p-230", None)
