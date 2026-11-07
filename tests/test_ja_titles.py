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
