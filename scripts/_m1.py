"""§67 M1 helpers (dHash of the illustration window, best of small shifts), shared by the twin scripts."""
import numpy as np
from slabwise.print_match import ART_BOX


def _hash(im, box, n=16):
    w, h = im.size
    x0, y0, x1, y1 = box
    a = np.asarray(im.crop((int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h))).resize((n + 1, n)), dtype=float)
    return (a[:, 1:] > a[:, :-1]).flatten()


def _boxes():
    x0, y0, x1, y1 = ART_BOX
    cx, cy, bw, bh = (x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0
    for s in (0.9, 1.0, 1.1):
        for dx in (-0.04, -0.02, 0, 0.02, 0.04):
            for dy in (-0.04, -0.02, 0, 0.02, 0.04):
                w2, h2 = bw * s / 2, bh * s / 2
                b = (cx + dx - w2, cy + dy - h2, cx + dx + w2, cy + dy + h2)
                if b[0] >= 0 and b[1] >= 0 and b[2] <= 1 and b[3] <= 1:
                    yield b


BOXES = list(_boxes())


def m1(en_im, ja_im):
    e = _hash(en_im, ART_BOX)
    return min(int((e != _hash(ja_im, b)).sum()) for b in BOXES)


