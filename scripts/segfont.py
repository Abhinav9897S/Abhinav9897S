"""Slanted 14-segment display font (DS-Digital style) rendered as SVG paths.

SVGs embedded in a README can't load web fonts, so every glyph is drawn from
segments. Each SVG gets one <path> per used character in <defs>, and text is
laid out with <use>, which keeps files small.
"""
import math

W, H = 10.0, 18.0      # glyph box
T = 1.55               # segment thickness
GAP = 0.42             # gap between segments
SLANT = 0.13           # italic lean
ADV = 14.0             # monospaced advance


def _h(x0, x1, y):
    t = T / 2
    x0, x1 = x0 + GAP, x1 - GAP
    return [(x0, y), (x0 + t, y - t), (x1 - t, y - t), (x1, y), (x1 - t, y + t), (x0 + t, y + t)]


def _v(x, y0, y1):
    t = T / 2
    y0, y1 = y0 + GAP, y1 - GAP
    return [(x, y0), (x + t, y0 + t), (x + t, y1 - t), (x, y1), (x - t, y1 - t), (x - t, y0 + t)]


def _d(x0, y0, x1, y1):
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy)
    nx, ny = -dy / L * T * 0.42, dx / L * T * 0.42
    return [(x0 + nx, y0 + ny), (x1 + nx, y1 + ny), (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)]


def _sq(cx, cy, s=1.7):
    return [(cx - s / 2, cy - s / 2), (cx + s / 2, cy - s / 2), (cx + s / 2, cy + s / 2), (cx - s / 2, cy + s / 2)]


M2, C2 = H / 2, W / 2
I0, IC = T * 0.95, T * 0.6
SEG = {
    "A": _h(0, W, 0), "D": _h(0, W, H),
    "B": _v(W, 0, M2), "C": _v(W, M2, H), "E": _v(0, M2, H), "F": _v(0, 0, M2),
    "G1": _h(0, C2, M2), "G2": _h(C2, W, M2),
    "I": _v(C2, 0, M2), "L": _v(C2, M2, H),
    "H": _d(I0, I0, C2 - IC, M2 - IC * 1.3), "J": _d(W - I0, I0, C2 + IC, M2 - IC * 1.3),
    "K": _d(I0, H - I0, C2 - IC, M2 + IC * 1.3), "M": _d(W - I0, H - I0, C2 + IC, M2 + IC * 1.3),
    "DOT": _sq(C2, H - 0.85), "DOTL": _sq(C2 - 1.5, H - 0.85),
    "COLU": _sq(C2, H * 0.3), "COLD": _sq(C2, H * 0.78),
    "TICK": _d(C2 - 1.4, H + 0.2, C2 - 2.6, H + 2.4),
}

GLYPHS = {
    "0": "A B C D E F", "1": "B C", "2": "A B G1 G2 E D", "3": "A B C D G1 G2",
    "4": "F G1 G2 B C", "5": "A F G1 G2 C D", "6": "A F E D C G1 G2", "7": "A B C",
    "8": "A B C D E F G1 G2", "9": "A B C D F G1 G2",
    "A": "A B C E F G1 G2", "B": "A B C D I L G2", "C": "A D E F", "D": "A B C D I L",
    "E": "A D E F G1 G2", "F": "A E F G1", "G": "A C D E F G2", "H": "B C E F G1 G2",
    "I": "A D I L", "J": "B C D E", "K": "E F G1 J M", "L": "D E F", "M": "B C E F H J",
    "N": "B C E F H M", "O": "A B C D E F", "P": "A B E F G1 G2", "Q": "A B C D E F M",
    "R": "A B E F G1 G2 M", "S": "A F G1 G2 C D", "T": "A I L", "U": "B C D E F",
    "V": "E F K J", "W": "B C E F K M", "X": "H J K M", "Y": "H J L", "Z": "A J K D",
    "-": "G1 G2", "_": "D", "/": "J K", "\\": "H M", "+": "G1 G2 I L", "*": "G1 G2 H I J K L M",
    "=": "G1 G2 D", "<": "J M", ">": "H K", "(": "J M", ")": "H K", "[": "A D E F", "]": "A B C D",
    "'": "I", '"': "F I", "|": "I L", ".": "DOT", ",": "DOT TICK", ":": "COLU COLD",
    ";": "COLU DOT TICK", "!": "I DOT", "?": "A B G2 L", "&": "A H J G1 E D M",
    "@": "A B D E F G2 I", "#": "B C G1 G2 I L D", "%": "F C J K", "$": "A F G1 G2 C D I L",
    "°": "A B F G1 G2", "^": "K M", "~": "G1 G2", "8ALL": "A B C D E F G1 G2 H I J K L M",
}


def _path(names):
    d = []
    for n in names.split():
        pts = [(x + (H - y) * SLANT, y) for x, y in SEG[n]]
        d.append("M" + "L".join(f"{x:.2f} {y:.2f}" for x, y in pts) + "Z")
    return "".join(d)


def clean(s):
    """Uppercase and drop anything the font can't draw."""
    out = []
    for ch in s.upper():
        ch = {"·": "/", "—": "-", "–": "-", "’": "'", "“": '"', "”": '"', "…": "..."}.get(ch, ch)
        if ch == " " or ch in GLYPHS:
            out.append(ch)
    return "".join(out)


def width(s, size):
    n = len(clean(s))
    return 0 if n == 0 else (n * ADV - (ADV - W) + H * SLANT) * size / H


class Seg:
    """Collects used glyphs for one SVG document."""

    def __init__(self):
        self.used = set()

    def text(self, s, x, y, size, fill="#e0f2fe", anchor="start", ghost=None, attrs=""):
        """Draw text with its baseline at y. `ghost` = (color, opacity) shows unlit segments."""
        s = clean(s)
        k = size / H
        w = width(s, size)
        if anchor == "middle":
            x -= w / 2
        elif anchor == "end":
            x -= w
        parts = []
        if ghost:
            self.used.add("8ALL")
            col, op = ghost
            uses = "".join(f'<use xlink:href="#sg8ALL" x="{i * ADV:g}"/>' for i, ch in enumerate(s) if ch != " ")
            parts.append(f'<g fill="{col}" opacity="{op}">{uses}</g>')
        uses = []
        for i, ch in enumerate(s):
            if ch == " ":
                continue
            self.used.add(ch)
            uses.append(f'<use xlink:href="#sg{ord(ch)}" x="{i * ADV:g}"/>')
        parts.append(f'<g fill="{fill}">{"".join(uses)}</g>')
        return f'<g transform="translate({x:.1f} {y - size:.1f}) scale({k:.4f})" {attrs}>{"".join(parts)}</g>'

    def defs(self):
        out = []
        for ch in sorted(self.used):
            gid = "8ALL" if ch == "8ALL" else str(ord(ch))
            out.append(f'<path id="sg{gid}" d="{_path(GLYPHS[ch])}"/>')
        return "".join(out)
