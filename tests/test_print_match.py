from PIL import Image, ImageDraw

from slabwise.print_match import ART_MAX, art_distance, same_print


def card(seed):
    im = Image.new("L", (300, 420), 128)
    d = ImageDraw.Draw(im)
    for k in range(12):
        x, y = (seed * 37 + k * 53) % 240, (seed * 71 + k * 29) % 200 + 30
        d.ellipse((x, y, x + 40 + k * 3, y + 30 + k * 2), fill=(seed * 40 + k * 17) % 256)
    return im


def test_same_and_different_art():
    a, b = card(1), card(1).resize((280, 392))
    assert art_distance(a, b) <= ART_MAX
    assert art_distance(a, card(5)) > ART_MAX


def test_other_pokemon_is_rejected():
    ok, why = same_print({"category": "Pokemon", "dexId": [251]}, {"category": "Pokemon", "dexId": [151]}, card(1), card(1))
    assert ok is False and why == "Pokémon diverso"
    ok, why = same_print({"category": "Trainer"}, {"category": "Pokemon", "dexId": [131]}, card(1), card(1))
    assert ok is False
    assert same_print({}, {"category": "Pokemon"}, None, card(1))[0] is None
