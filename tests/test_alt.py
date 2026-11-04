"""Alt sold rows (D64): marketplace and eBay id from what the public page shows."""
import importlib.util
import os

import pytest

pytest.importorskip("playwright")
spec = importlib.util.spec_from_file_location("alt_sold", os.path.join(os.path.dirname(__file__), "..", "scripts", "alt_sold.py"))
alt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(alt)


def test_source_and_ebay_id():
    ebay = {"image": "https://alt-images.b-cdn.net/external/ebay/ccg/20260805T155714/227447304612.jpg?height=540", "logo": "eBay.png"}
    fan = {"image": "https://alt-images.b-cdn.net/external/pwcc_fixed_price/20261027T020000/BOV2_44-0.jpg", "logo": "Fanatics%20Collect.png"}
    assert alt.source_of(ebay) == "ebay" and alt.ebay_id(ebay) == "227447304612"
    assert alt.source_of(fan) == "fanatics" and alt.ebay_id(fan) is None
    assert set(alt.QUERY) >= {"base1-4", "swsh7-215", "ja:sv2a-201"}
