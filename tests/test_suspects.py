from slabwise.suspects import flag


def _r(i, d, p, card="c1", g=10, ex=""):
    return dict(item_id=f"ebay:{i}", date=d, card=card, grade=g, price_usd=p, excluded=ex)


def test_far_sale_is_flagged_both_ways():
    rows = [_r(1, "2026-01-05", 1000), _r(2, "2026-01-20", 1100), _r(3, "2026-02-03", 950), _r(4, "2026-02-10", 1050),
            _r(5, "2026-02-12", 48), _r(6, "2026-02-14", 24000)]
    f = flag(rows)
    assert set(f) == {"ebay:5", "ebay:6"}
    assert f["ebay:5"]["ratio"] < 0.2 and f["ebay:6"]["ratio"] > 5


def test_a_card_that_really_rose_is_not_flagged():
    rows = [_r(i, f"20{18 + i // 4}-0{1 + i % 4}-10", 50 * 1.6 ** i) for i in range(16)]
    assert flag(rows) == {}


def test_grades_and_excluded_sales_stay_apart():
    rows = [_r(1, "2026-01-05", 1000), _r(2, "2026-01-06", 1000), _r(3, "2026-01-07", 1000),
            _r(4, "2026-01-08", 100, g=9), _r(5, "2026-01-09", 10, ex="lotto")]
    assert flag(rows) == {}
