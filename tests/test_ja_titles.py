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


def test_d233_promo_number_without_name():
    entry = ("poncho\\-wearing pikachu|poncho\\W*(?:wearing\\W*)? pikachu", 207, -1, "\\bxy\\W*(?:black\\W*star\\W*)?promo|\\bxy\\W?p\\b")
    at.JA_CATALOGUE["ja:xy-p-207"] = entry
    try:
        assert at.match_title("2013 Pokemon ポンチョを着たピカチュウ XY Promos #207/XY-P PSA 10")[0] == "ja:xy-p-207"
        assert at.match_title("2013 Pokemon ポンチョを着たピカチュウ XY Promos #208/XY-P PSA 10")[0] is None   # another number
        assert at.match_title("2013 Pokemon ポンチョを着たピカチュウ XY Promos #207/SM-P PSA 10")[0] is None   # another promo series
    finally:
        at.JA_CATALOGUE.pop("ja:xy-p-207", None)


def test_d235_english_fixes():
    assert at.match_title("2019 POKEMON SM BLACK STAR PROMO #SM162 PIKACHU-HOLO PSA 10")[0] == "smp-SM162"
    assert at.match_title("CHARIZARD EX (2023) POKEMON S&V 151 - 199/165 (SPECIAL ILLUSTRATION RARE) PSA 8")[0] == "sv03.5-199"
    assert at.match_title("2025 Pokemon Mega Evolutions Mega Lucario EX #188/132 PSA MINT 9")[0] == "me01-188"
    assert at.match_title("Pokemon XY Evolutions Charizard 11/108 PSA 10")[0] is None          # the XY reprint stays out
    assert at.match_title("Pokemon 151 Mew ex Metal Promo 205/165 PSA 10")[0] is None          # the metal card stays out
    assert at.match_title("Pokemon lot (3) Charizard 4/102 PSA 10")[0] is None


def test_d236_bare_number():
    assert at.match_title("Pokemon 1999 Mewtwo 10 Holo Base Set PSA 10")[0] == "base1-10"
    assert at.match_title("2021 Pokemon Evolving Skies 215 Umbreon VMAX Alternate Art Secret Rare PSA 10")[0] == "swsh7-215"
    assert at.match_title("POKEMON BASE SET MEWTWO HOLO PSA 10 VINTAGE 1999")[0] is None      # the grade is not the number


def test_d238_d239_japanese_setcode_bare_korean():
    assert at.match_title("PSA 10 Charizard ex SAR 349/190 SV4a Shiny Treasure ex Pokemon Card")[0] == "ja:sv4a-349"
    assert at.match_title("Bulbasaur 166/165 PSA 10 Sv2a Card 151 Pokemon Card Game")[0] != "ja:sv2a-166"   # SV2a does not count
    assert at.match_title("1996 Pokemon Japanese Basic 6 Charizard-Holo - PSA NM 7")[0] == "ja:expansion-pack-6"
    assert at.match_title("2025 POKEMON MEGA DREAM - M2A KR #199/193 PSYDUCK ART RARE PSA 10")[0] is None   # Korean

