"""D347: the stories of the week for the reels (docs/specs/2026-11-reel-scene.md)."""
from slabwise import stories as S


def _c(cid, name, set_, lang="en", en=None, value=100, pop=1000, sales90=20, ch30=0.0, hist=None, sales=None):
    g = dict(grade=10, value=value, lo=value * .9, hi=value * 1.1, sales90=sales90, pop=pop, ch30=ch30, history=hist or [])
    return dict(id=cid, name=name, set=set_, lang=lang, en=en, en_same=True if en else None, grades=[g], sales=sales or [])


def test_twin_gap_finds_the_cheaper_japanese_and_says_it_in_euros():
    cards = [_c("e1", "Magikarp", "Paldea Evolved", value=3500, pop=4000),
             _c("ja:j1", "Magikarp", "Triplet Beat", lang="ja", en="e1", value=200, pop=60000)]
    st = S.twin_gap(cards, 0.9)
    assert len(st) == 1 and st[0]["kind"] == "twin" and not st[0]["ja_more"]
    assert "3.150\u00a0€" in st[0]["numbers"] and "180\u00a0€" in st[0]["numbers"]
    assert [x["t"] for x in st[0]["scenes"]] == ["statement", "vs", "bars", "statement", "question"]


def test_twin_gap_skips_promos_and_absurd_gaps():
    cards = [_c("e1", "Pikachu", "SM Black Star Promos", value=3000), _c("ja:j1", "Pikachu", "X", lang="ja", en="e1", value=50),
             _c("e2", "Eevee", "Set", value=10000), _c("ja:j2", "Eevee", "Y", lang="ja", en="e2", value=100)]
    assert S.twin_gap(cards, 1) == []


def test_era_share_uses_italian_numbers():
    st = S.era_share(dict(eras={"Classica": dict(start=0.138, y1=0.036, now=0.018), "Scarlatto e Violetto": dict(start=0.54, y1=0.6, now=0.71)}))
    assert st and "Una su 56" in st[0]["hook"] and "il 13,8%" in st[0]["numbers"] and "l'1" not in st[0]["numbers"]


def test_week_stories_at_most_six_two_per_kind_no_card_twice():
    cards = []
    for i in range(5):
        cards += [_c(f"e{i}", f"Card{i}", "Set", value=1000 * (i + 3), pop=1000), _c(f"ja:j{i}", f"Card{i}", "SetJ", lang="ja", en=f"e{i}", value=400, pop=20000)]
    st = S.week_stories(cards, None, {}, 1, "2026-11-23")
    assert len(st) == 2 and all(s["kind"] == "twin" for s in st)
    assert len({c for s in st for c in s["cards"]}) == 4
