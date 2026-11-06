import numpy as np
import pandas as pd

from slabwise.backtest import run
from slabwise.identity import identity_layer, sim_cert_lookup
from slabwise.model import LatentValueModel, LVMParams
from slabwise.sim import SimConfig, simulate

SMALL = dict(n_cards=40, weeks=60)


def test_simulator_is_deterministic():
    a = simulate(SimConfig(seed=7, **SMALL)).sales
    b = simulate(SimConfig(seed=7, **SMALL)).sales
    pd.testing.assert_frame_equal(a, b)


def test_no_look_ahead():
    """P11: estimates up to week 40 must not change when later sales change."""
    m = simulate(SimConfig(seed=3, **SMALL))
    r1 = run(m, "A", LVMParams(), weeks=60)
    late = m.sales["week"] > 40
    m.sales.loc[late, "price"] *= 3.0
    r2 = run(m, "A", LVMParams(), weeks=60)
    for n in r1.names:
        np.testing.assert_allclose(r1.est[n][:41], r2.est[n][:41], equal_nan=True, err_msg=n)


def test_identity_removes_duplicates_and_bad_certs():
    m = simulate(SimConfig(seed=2, **SMALL))
    clean, removed = identity_layer(m.sales, sim_cert_lookup(m.sales))
    assert not clean["item_id"].duplicated().any()
    assert (removed["t_kind"] == "genuine").mean() < 0.02
    assert set(removed["reason"]) <= {
        "duplicato (stesso annuncio)", "duplicato (stesso cert, altra fonte)",
        "cert: stampa diversa dal catalogo", "cert: voto fuori perimetro",
        "lotto di più carte", "Best Offer senza prezzo accettato"}


def test_model_recovers_value_and_rejects_fakes():
    """One card, flat market: genuine sales around 1000 $, plus cheap fakes."""
    rng = np.random.default_rng(0)
    rows = []
    for w in range(30):
        rows.append(dict(card=0, grade=10, day=w * 7 + 1, price=1000 * np.exp(rng.normal(0, 0.08)),
                         venue="ebay", cert=f"k{w}", cert_ok=True))
        if w > 20:
            rows.append(dict(card=0, grade=10, day=w * 7 + 2, price=30.0, venue="ebay", cert=None, cert_ok=False))
    df = pd.DataFrame(rows)
    df["week"] = (df["day"] // 7).astype(int)
    m = LatentValueModel(1, np.array([0]), 1, LVMParams())
    for w in range(30):
        m.ingest(w, df[df["week"] == w])
    mean, sd = m.estimates_with_sd(29)
    assert abs(np.exp(mean[0, 0]) / 1000 - 1) < 0.08
    pg = m.sale_posteriors(0)
    prices = np.array([o["y"] for o in m.obs[0]])
    assert pg[prices < np.log(100)].max() < 0.05      # fakes judged non-genuine
    assert np.isfinite(mean[0, 1]) and sd[0, 1] > sd[0, 0]   # grade 9 borrowed, less certain


def test_auction_title_matching():
    from slabwise.sources.auction_titles import match_title
    assert match_title("1999 Pokemon Base Set Holo Charizard #4 PSA 9 MINT")[0] == "base1-4"
    assert match_title("1999 Pokemon Base Set Shadowless Holo Charizard #4 PSA 9")[0] == "base1-4/shadowless"
    assert match_title("1999 Pokemon Base Set First Edition Holofoil #8 Machamp - PSA NM 7")[0] == "base1-8/1st"
    assert match_title("1999 Pokemon Base Set Shadowless Red Cheeks Pikachu #58 PSA 10 GEM MINT")[0] == "base1-58/shadowless-red"
    assert match_title("1999 Pokemon Base Set Shadowless #58 Pikachu PSA 9")[0] is None
    assert match_title("1999 Pokemon Base Set 1st Edition Shadowless Machamp #8 PSA 9")[0] == "base1-8/1st-shadowless"
    assert match_title("2000 Pokemon Rocket Rare Holofoil #4 Dark Charizard - PSA NM 7")[0] == "base5-4"
    assert match_title("2023 Pokemon Scarlet & Violet Promo Van Gogh Pikachu With Grey Felt Hat #85 PSA 9")[0] == "svp-085"
    for bad in ("2000 Pokemon Base Set II Holofoil #3 Chansey - PSA NM-MT 8",
                "2021 Pokemon Celebrations Classic Collection Base Set #4 Charizard - PSA GEM MT 10",
                "1996 Pokemon Japanese Base Set Holo #6 Charizard - PSA GEM MT 10",
                "1999 Pokemon Base Set E3 Stamp Red Cheeks #58 Pikachu - PSA MINT 9",
                "1999 Pokemon Base Set Unopened Charizard Foil Pack (11 Cards) - PSA NM-MT 8"):
        assert not (match_title(bad)[0] or "ja:").startswith(("base", "neo", "sv", "swsh", "ex", "gym")), bad   # D158: a Japanese title may match the Japanese printing


def test_language_gaps_v12():
    """Protocol section 5, L1 and L2: language gaps are recovered and help sparse languages."""
    import numpy as np
    from slabwise.identity import identity_layer
    from slabwise.model import LatentValueModel
    from slabwise.sim import SimConfig, simulate
    from slabwise.schema import GRADE_INDEX
    m = simulate(SimConfig(seed=7, n_cards=60, weeks=104, contamination=0.0, flood=False, langs=4))
    clean, _ = identity_layer(m.sales, None, verify_certs=False)
    C, NL = 60, 4
    shared = LatentValueModel(C, m.era_obs, 5)
    separate = LatentValueModel(C * (NL + 1), np.tile(m.era_obs, NL + 1), 5)
    sep = clean.copy()
    sep["card"] = sep["card"] + C * sep["lang"]
    sep["lang"] = 0
    gs, gp = dict(tuple(clean.groupby("week"))), dict(tuple(sep.groupby("week")))
    for w in range(104):
        shared.ingest(w, gs.get(w, clean.iloc[:0]))
        separate.ingest(w, gp.get(w, sep.iloc[:0]))
    # L1: shared gap of each language within 0.10 of the truth (mean over cards)
    assert np.all(np.abs(shared.mu_lang[:NL] - m.lang_gap.mean(axis=0)) < 0.10), (shared.mu_lang[:NL], m.lang_gap.mean(0))
    # L2: lower error on non-English atoms that have at least one sale
    sold = clean[clean["lang"] > 0].groupby(["card", "lang", "grade"]).size().index
    e_sh, e_sep = [], []
    est_sep = separate.estimates(103)
    for c, l, g in sold:
        gi = GRADE_INDEX[int(g)]
        truth = m.value[c, gi, 103] + m.lang_gap[c, l - 1]
        mean, _ = shared.estimates_lang(103, l)
        if np.isfinite(mean[c, gi]) and np.isfinite(est_sep[c + C * l, gi]):
            e_sh.append(abs(mean[c, gi] - truth))
            e_sep.append(abs(est_sep[c + C * l, gi] - truth))
    print("L1", np.round(shared.mu_lang[:NL], 3), np.round(m.lang_gap.mean(0), 3), "L2", np.median(e_sh), np.median(e_sep), len(e_sh))
    assert np.median(e_sh) < np.median(e_sep), (np.median(e_sh), np.median(e_sep))


def test_character_package(tmp_path):
    """character.json is the only source of the character; poses may be inline SVG or image files."""
    import json
    import shutil
    import sys
    from PIL import Image
    sys.path.insert(0, "prototype/character")
    from load import POSES, load
    real = load("prototype/character/slabby")
    assert all(f'id="slabby-{p}"' in real["svg"] for p in POSES) and "--sb-main" in real["css"]
    d = tmp_path / "alt"
    shutil.copytree("prototype/character/slabby", d)
    c = json.load(open(d / "character.json"))
    Image.new("RGBA", (40, 60), (0, 0, 0, 0)).save(d / "smug.png")
    c["poses"]["smug"] = {"image": "smug.png"}
    json.dump(c, open(d / "character.json", "w"))
    out = load(str(d))
    assert 'id="slabby-smug" viewBox="0 0 40 60"' in out["svg"] and "data:image/webp;base64," in out["svg"]   # PNG poses are embedded as WebP (page weight)


def test_japanese_titles():
    from slabwise.sources.auction_titles import match_title
    assert match_title("リザードンex SAR 201/165 ポケモンカード151 PSA10")[0] == "ja:sv2a-201"
    assert match_title("2023 Pokemon Japanese 151 Charizard ex SAR #201/165 PSA 10")[0] == "ja:sv2a-201"
    assert match_title("PSA10 ブラッキーVMAX SA 095/069 イーブイヒーローズ")[0] == "ja:s6a-095"
    assert match_title("Pokemon Japanese Charmander AR 168/165 PSA 9")[0] == "ja:sv2a-168"
    assert match_title("Pokemon 151 Charmander IR 168/165 PSA 9")[0] == "sv03.5-168"   # English printing
    assert match_title("PSA10 リザードンex SAR 201/165 まとめ")[0] is None                   # lot


def test_fixed_price_venue_v16b():
    """Protocol section 9b, V1b: a third venue with a known offset is recovered within 0.03."""
    import numpy as np
    from slabwise.identity import identity_layer
    from slabwise.model import LatentValueModel
    from slabwise.sim import SimConfig, simulate
    m = simulate(SimConfig(seed=11, n_cards=60, weeks=104, contamination=0.0, flood=False))
    clean, _ = identity_layer(m.sales, None, verify_certs=False)
    rng = np.random.default_rng(5)
    pick = (clean["venue"] == "ebay").to_numpy() & (rng.random(len(clean)) < 0.30)
    clean.loc[pick, "venue"] = "fixed"
    clean.loc[pick, "price"] = clean.loc[pick, "price"] * np.exp(0.10)
    from slabwise.model import LVMParams
    lvm = LatentValueModel(60, m.era_obs, 5, LVMParams(venue_gaps=True))
    g = dict(tuple(clean.groupby("week")))
    for w in range(104):
        lvm.ingest(w, g.get(w, clean.iloc[:0]))
    print("V1b offsets", np.round(lvm.offs, 3), "spread", np.round(lvm.s_venue, 3))
    assert abs(lvm.offs[2] - 0.10) < 0.03, lvm.offs


def _vintage_run(era_gaps):
    import numpy as np
    from slabwise.identity import identity_layer
    from slabwise.model import LatentValueModel, LVMParams
    from slabwise.sim import SimConfig, simulate
    m = simulate(SimConfig(seed=13, n_cards=120, weeks=104, contamination=0.0, flood=False, vintage_gap=1.5))
    clean, _ = identity_layer(m.sales, None, verify_certs=False)
    lvm = LatentValueModel(120, m.era_obs, 5, LVMParams(era_gaps=era_gaps))
    g = dict(tuple(clean.groupby("week")))
    for w in range(104):
        lvm.ingest(w, g.get(w, clean.iloc[:0]))
    wotc = np.where(m.era == 0)[0]
    true_gap = float(np.mean(m.value[wotc, 1, -1] - m.value[wotc, 0, -1]))
    learnt = float(lvm.gap_prior(0)[0][0])
    low, tot = 0, 0
    for c in wotc:
        f = lvm.fit[c]
        if f is None:
            continue
        for o, pg in zip(lvm.obs[c], f["pgen"]):
            if o["g"] == 0:
                tot += 1
                low += pg < 0.5
    return true_gap, learnt, low / max(tot, 1), tot


import pytest  # noqa: E402


@pytest.mark.xfail(strict=True, reason="v1.7c fails G1 (protocol section 11c, D58): kept as a record, era_gaps stays off")
def test_era_grade_gaps_v17():
    """Protocol section 11, G1-G3: per-era grade-gap prior on a market with a big vintage 10->9 gap."""
    t, l17, share17, n = _vintage_run(True)
    _, l15, share15, _ = _vintage_run(False)
    print(f"G1 true {t:.3f} v1.7 {l17:.3f} | G2 v1.7 {share17:.1%} of {n} | G3 v1.5 {l15:.3f} {share15:.1%}")
    assert abs(l17 - t) <= 0.20, (l17, t)
    assert share17 <= 0.10, share17
