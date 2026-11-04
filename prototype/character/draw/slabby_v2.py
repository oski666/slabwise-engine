"""Slabby v2, an original character: a living graded slab (clear lilac case, black card inside,
orange grade label on top). Writes one SVG per pose; render_png.js turns them into the PNG files
the site uses. Palette: black #111014, orange #FF6A2B, lilac #D9D2E9, grey #C7C0D3, white.

Usage: python prototype/character/draw/slabby_v2.py  (then: node prototype/character/draw/render_png.js)
"""
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "svg")
INK, ORANGE, LILAC, GREY, WHITE = "#111014", "#FF6A2B", "#D9D2E9", "#C7C0D3", "#FFFFFF"
OUTLINE = f'stroke="{INK}" stroke-width="7" stroke-linejoin="round" stroke-linecap="round"'


def arms(kind):
    if kind == "up":
        return (f'<path d="M86 250 Q40 220 34 160" fill="none" {OUTLINE} stroke-width="12"/><circle cx="34" cy="152" r="14" fill="{INK}"/>'
                f'<path d="M314 250 Q360 220 366 160" fill="none" {OUTLINE} stroke-width="12"/><circle cx="366" cy="152" r="14" fill="{INK}"/>')
    if kind == "hips":
        return (f'<path d="M86 260 Q44 270 60 320 Q74 330 88 318" fill="none" {OUTLINE} stroke-width="12"/>'
                f'<path d="M314 260 Q356 270 340 320 Q326 330 312 318" fill="none" {OUTLINE} stroke-width="12"/>')
    if kind == "wave":
        return (f'<path d="M86 270 Q50 300 56 344" fill="none" {OUTLINE} stroke-width="12"/><circle cx="56" cy="350" r="14" fill="{INK}"/>'
                f'<path d="M314 250 Q362 214 356 150" fill="none" {OUTLINE} stroke-width="12"/><circle cx="356" cy="142" r="14" fill="{INK}"/>')
    # down
    return (f'<path d="M86 270 Q50 300 56 344" fill="none" {OUTLINE} stroke-width="12"/><circle cx="56" cy="350" r="14" fill="{INK}"/>'
            f'<path d="M314 270 Q350 300 344 344" fill="none" {OUTLINE} stroke-width="12"/><circle cx="344" cy="350" r="14" fill="{INK}"/>')


def legs():
    return (f'<path d="M150 470 L146 520" {OUTLINE} stroke-width="14"/><ellipse cx="136" cy="526" rx="30" ry="14" fill="{INK}"/>'
            f'<path d="M250 470 L254 520" {OUTLINE} stroke-width="14"/><ellipse cx="264" cy="526" rx="30" ry="14" fill="{INK}"/>')


def eyes(kind):
    L, R, Y = 158, 242, 262
    if kind == "happy":      # closed, curved up
        return "".join(f'<path d="M{x-26} {Y+6} Q{x} {Y-24} {x+26} {Y+6}" fill="none" stroke="{ORANGE}" stroke-width="10" stroke-linecap="round"/>' for x in (L, R))
    if kind == "sleep":
        return "".join(f'<path d="M{x-24} {Y} Q{x} {Y+16} {x+24} {Y}" fill="none" stroke="{GREY}" stroke-width="9" stroke-linecap="round"/>' for x in (L, R))
    if kind == "stars":      # dazzled by a deal
        star = lambda x: (f'<path d="M{x} {Y-30} L{x+9} {Y-9} L{x+31} {Y-8} L{x+14} {Y+6} L{x+20} {Y+28} L{x} {Y+15} '
                          f'L{x-20} {Y+28} L{x-14} {Y+6} L{x-31} {Y-8} L{x-9} {Y-9} Z" fill="{ORANGE}" stroke="{WHITE}" stroke-width="4" stroke-linejoin="round"/>')
        return star(L) + star(R)
    r, pr = (34, 9) if kind == "shock" else (28, 13)
    out = ""
    for x in (L, R):
        out += f'<circle cx="{x}" cy="{Y}" r="{r}" fill="{WHITE}"/><circle cx="{x + (0 if kind == "shock" else 4)}" cy="{Y + 2}" r="{pr + 7}" fill="{ORANGE}"/>'
        out += f'<circle cx="{x + (0 if kind == "shock" else 4)}" cy="{Y + 2}" r="{pr}" fill="{INK}"/><circle cx="{x + 10}" cy="{Y - 8}" r="6" fill="{WHITE}"/>'
    if kind == "smug":       # half-lidded: a lilac lid over the top of each eye
        out += "".join(f'<path d="M{x-36} {Y-6} Q{x} {Y-22} {x+36} {Y-6} L{x+36} {Y-40} L{x-36} {Y-40} Z" fill="{INK}"/>' for x in (L, R))
    return out


def mouth(kind):
    if kind == "smile":
        return f'<path d="M168 330 Q200 356 232 330" fill="none" stroke="{WHITE}" stroke-width="9" stroke-linecap="round"/>'
    if kind == "smirk":
        return f'<path d="M172 336 Q206 352 236 324" fill="none" stroke="{WHITE}" stroke-width="9" stroke-linecap="round"/>'
    if kind == "laugh":
        return (f'<path d="M156 320 Q200 330 244 320 Q236 392 200 394 Q164 392 156 320 Z" fill="{WHITE}"/>'
                f'<path d="M176 372 Q200 360 224 372 Q214 390 200 390 Q186 390 176 372 Z" fill="{ORANGE}"/>')
    if kind == "drool":
        return (f'<path d="M166 326 Q200 362 234 326 Q226 350 200 352 Q174 350 166 326 Z" fill="{WHITE}"/>'
                f'<path d="M226 340 Q234 370 226 386 Q216 370 222 344 Z" fill="#8FD3FF"/>')
    if kind == "shock":
        return f'<ellipse cx="200" cy="350" rx="22" ry="28" fill="{WHITE}"/><ellipse cx="200" cy="358" rx="12" ry="14" fill="{ORANGE}"/>'
    if kind == "sleep":
        return f'<ellipse cx="200" cy="344" rx="12" ry="9" fill="{GREY}"/>'
    return ""


def slab_body(tilt=0, extra=""):
    # clear case (lilac) with the grade label on top, black card window below
    return (f'<g transform="rotate({tilt} 200 300)">'
            f'<rect x="80" y="70" width="240" height="410" rx="40" fill="{LILAC}" {OUTLINE}/>'
            f'<rect x="100" y="90" width="200" height="74" rx="14" fill="{ORANGE}" {OUTLINE} stroke-width="5"/>'
            f'<rect x="118" y="108" width="96" height="12" rx="6" fill="{WHITE}" opacity=".9"/>'
            f'<rect x="118" y="130" width="70" height="10" rx="5" fill="{WHITE}" opacity=".6"/>'
            f'<text x="262" y="146" text-anchor="middle" font-family="Arial Black, Arial, sans-serif" font-weight="900" font-size="46" fill="{INK}">10</text>'
            f'<rect x="104" y="182" width="192" height="276" rx="22" fill="{INK}"/>'
            f'<path d="M116 196 L148 196 L116 236 Z" fill="{WHITE}" opacity=".18"/>'
            f'{extra}</g>')


def pose(arm, eye, mouth_kind, tilt=0, deco=""):
    face = eyes(eye) + mouth(mouth_kind)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 560">{legs()}{arms(arm)}'
            f'{slab_body(tilt, face)}{deco}</svg>')


ZZZ = (f'<text x="318" y="96" font-family="Arial Black, Arial, sans-serif" font-size="40" fill="{GREY}" transform="rotate(-12 318 96)">z</text>'
       f'<text x="350" y="54" font-family="Arial Black, Arial, sans-serif" font-size="30" fill="{GREY}" transform="rotate(-12 350 54)">z</text>')
SHOCK_LINES = "".join(f'<path d="M{x1} {y1} L{x2} {y2}" stroke="{ORANGE}" stroke-width="8" stroke-linecap="round"/>'
                      for x1, y1, x2, y2 in [(40, 70, 64, 100), (360, 70, 336, 100), (20, 150, 50, 160), (380, 150, 350, 160)])
SPARK = (f'<path d="M352 210 l8 18 l18 8 l-18 8 l-8 18 l-8 -18 l-18 -8 l18 -8 z" fill="{ORANGE}"/>'
         f'<path d="M48 120 l6 13 l13 6 l-13 6 l-6 13 l-6 -13 l-13 -6 l13 -6 z" fill="{ORANGE}"/>')

POSES = {
    "smug": pose("hips", "smug", "smirk"),
    "bliss": pose("down", "happy", "smile", deco=SPARK),
    "laugh": pose("up", "happy", "laugh", tilt=-4),
    "drool": pose("down", "stars", "drool"),
    "shock": pose("up", "shock", "shock", deco=SHOCK_LINES),
    "sleep": pose("down", "sleep", "sleep", tilt=4, deco=ZZZ),
}
# peek: only the top of the slab and the eyes, wider than tall
POSES["peek"] = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="60 50 280 250">'
                 + slab_body(0, eyes("open")) + f'<rect x="60" y="292" width="280" height="10" fill="none"/></svg>')

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for k, v in POSES.items():
        open(os.path.join(OUT, f"{k}.svg"), "w").write(v)
    print("scritte", len(POSES), "pose in", OUT)
