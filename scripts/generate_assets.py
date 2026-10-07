#!/usr/bin/env python3
"""Generate the static animated SVGs for the profile README (astrophysics theme).

GitHub strips JavaScript and external CSS/fonts from READMEs, but SVGs loaded
via <img> still run their own SMIL animations. All text uses the segment font
in segfont.py. 3D effects come from rotating flat groups inside a squashed
(inclined) parent group, plus front/back clipping so bodies pass behind and in
front of the central object.

Usage: python3 scripts/generate_assets.py
"""
import math
import random
import xml.dom.minidom
from pathlib import Path

from segfont import Seg, width

OUT = Path(__file__).resolve().parent.parent / "assets"

NAME = "ABHINAV SINGH"
TAGLINE = "MATHEMATICS & COMPUTING // JIIT '29"
FIELDS = "AI / ML / DATA SCIENCE / ASTROPHYSICS"

CYAN, ICE, AMBER, MAGENTA, DIM = "#7dd3fc", "#e0f2fe", "#fbbf24", "#d946ef", "#64748b"
SPECTRAL = ["#9bb0ff", "#aabfff", "#cad7ff", "#f8f7ff", "#fff4ea", "#ffd2a1", "#ffb56c"]

GLOW = '''
<filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
  <feGaussianBlur stdDeviation="2.2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
</filter>
<filter id="bigglow" x="-50%" y="-50%" width="200%" height="200%">
  <feGaussianBlur stdDeviation="5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
</filter>'''


def svg(w, h, seg, body, extra_defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{w}" height="{h}" viewBox="0 0 {w} {h}">\n<defs>{seg.defs()}{GLOW}{extra_defs}</defs>\n{body}\n</svg>')


def starfield(rnd, w, h, n_static, n_twinkle, band=None):
    out = []
    for _ in range(n_static):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        if band and rnd.random() < 0.6:  # Milky Way band: y = a*x + b with scatter
            a, b, spread = band
            y = a * x + b + rnd.gauss(0, spread)
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rnd.choice([0.4, 0.5, 0.7])}" '
                   f'fill="{rnd.choice(SPECTRAL)}" opacity="{rnd.uniform(0.3, 0.8):.2f}"/>')
    for _ in range(n_twinkle):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rnd.choice([0.9, 1.1, 1.4])}" fill="{rnd.choice(SPECTRAL)}">'
                   f'<animate attributeName="opacity" values="0.2;1;0.2" dur="{rnd.uniform(2, 6):.1f}s" '
                   f'begin="-{rnd.uniform(0, 5):.1f}s" repeatCount="indefinite"/></circle>')
    return "\n".join(out)


def nebula(blobs):
    """Soft nebula clouds from radial gradients (cheap: no blur filters)."""
    defs, body = [], []
    for i, (cx, cy, rx, ry, col, op) in enumerate(blobs):
        defs.append(f'<radialGradient id="neb{i}"><stop offset="0" stop-color="{col}" stop-opacity="{op}"/>'
                    f'<stop offset="1" stop-color="{col}" stop-opacity="0"/></radialGradient>')
        body.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="url(#neb{i})"/>')
    return "".join(defs), "\n".join(body)


def brackets(x0, y0, x1, y1, L=18, col=CYAN, op=0.6):
    p = (f"M{x0} {y0 + L}V{y0}H{x0 + L}M{x1 - L} {y0}H{x1}V{y0 + L}"
         f"M{x1} {y1 - L}V{y1}H{x1 - L}M{x0 + L} {y1}H{x0}V{y1 - L}")
    return f'<path d="{p}" fill="none" stroke="{col}" stroke-opacity="{op}" stroke-width="1.5"/>'


# --------------------------------------------------------------------------- banner
def black_hole(rnd, cx, cy, incl=0.23):
    """Black hole with a rotating, inclined accretion disk, photon ring and lensed arc."""
    bands = [(58, 80, 5, "#fff7e0"), (80, 112, 8, "#ffd08a"), (112, 150, 13, "#ffa94d"), (150, 205, 21, "#f97316")]
    disk = []
    for bi, (r0, r1, period, col) in enumerate(bands):
        parts = []
        for r in range(r0, r1, 6):
            dash = rnd.choice(["14 9", "26 12", "8 6", "40 18"])
            op = 0.85 - 0.5 * (r - 58) / 150
            parts.append(f'<circle r="{r}" fill="none" stroke="{col}" stroke-width="{4.5 - bi * 0.6:.1f}" '
                         f'stroke-dasharray="{dash}" stroke-opacity="{op:.2f}"/>')
        for _ in range(int((r1 - r0) * 0.9)):
            a = rnd.uniform(0, 2 * math.pi)
            r = rnd.uniform(r0, r1)
            parts.append(f'<circle cx="{r * math.cos(a):.1f}" cy="{r * math.sin(a):.1f}" r="{rnd.uniform(1, 2.4):.1f}" '
                         f'fill="{rnd.choice(["#fff", "#ffe8c2", col])}" opacity="{rnd.uniform(0.5, 1):.2f}"/>')
        disk.append(f'<g><animateTransform attributeName="transform" type="rotate" from="0" to="-360" '
                    f'dur="{period}s" repeatCount="indefinite"/>{"".join(parts)}</g>')
    disk_g = (f'<g mask="url(#beam)"><g transform="translate({cx} {cy}) scale(1 {incl})">'
              f'<circle r="205" fill="url(#diskglow)"/>{"".join(disk)}</g></g>')
    defs = f'''
<radialGradient id="diskglow"><stop offset="0.25" stop-color="#ffb347" stop-opacity="0.55"/>
  <stop offset="0.6" stop-color="#c2410c" stop-opacity="0.25"/><stop offset="1" stop-color="#7c2d12" stop-opacity="0"/></radialGradient>
<radialGradient id="halo"><stop offset="0.3" stop-color="#ffb347" stop-opacity="0.35"/>
  <stop offset="1" stop-color="#ffb347" stop-opacity="0"/></radialGradient>
<linearGradient id="beamg" x1="0" x2="1"><stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0.45"/></linearGradient>
<mask id="beam" maskUnits="userSpaceOnUse" x="{cx - 230}" y="{cy - 230}" width="460" height="460"><rect x="{cx - 230}" y="{cy - 230}" width="460" height="460" fill="url(#beamg)"/></mask>
<clipPath id="back"><rect x="{cx - 260}" y="{cy - 260}" width="520" height="260"/></clipPath>
<clipPath id="front"><rect x="{cx - 260}" y="{cy}" width="520" height="260"/></clipPath>
<linearGradient id="jet" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{CYAN}" stop-opacity="0"/>
  <stop offset="1" stop-color="{CYAN}" stop-opacity="0.55"/></linearGradient>
<linearGradient id="arc" x1="0" x2="1"><stop offset="0" stop-color="#fff1d6"/><stop offset="0.5" stop-color="#ffb347"/>
  <stop offset="1" stop-color="#fff1d6" stop-opacity="0.6"/></linearGradient>'''
    jets = (f'<g opacity="0.7"><animate attributeName="opacity" values="0.35;0.8;0.35" dur="4s" repeatCount="indefinite"/>'
            f'<path d="M{cx - 2} {cy - 40}L{cx - 9} {cy - 175}H{cx + 9}L{cx + 2} {cy - 40}Z" fill="url(#jet)"/>'
            f'<path d="M{cx - 2} {cy - 40}L{cx - 9} {cy - 175}H{cx + 9}L{cx + 2} {cy - 40}Z" fill="url(#jet)" transform="rotate(180 {cx} {cy})"/></g>')
    body = f'''
<circle cx="{cx}" cy="{cy}" r="150" fill="url(#halo)"/>
{jets}
<g clip-path="url(#back)">{disk_g}</g>
<path d="M{cx - 66} {cy}A66 60 0 0 1 {cx + 66} {cy}" fill="none" stroke="url(#arc)" stroke-width="7" opacity="0.8" filter="url(#bigglow)"/>
<path d="M{cx - 56} {cy + 4}A56 44 0 0 0 {cx + 56} {cy + 4}" fill="none" stroke="#ffd08a" stroke-width="1.6" opacity="0.6"/>
<circle cx="{cx}" cy="{cy}" r="47" fill="none" stroke="#fff1d6" stroke-width="2.4" filter="url(#glow)">
  <animate attributeName="stroke-opacity" values="0.7;1;0.7" dur="3s" repeatCount="indefinite"/></circle>
<circle cx="{cx}" cy="{cy}" r="45" fill="#000"/>
<g clip-path="url(#front)">{disk_g}</g>'''
    return defs, body


def banner():
    W, H = 1200, 380
    rnd = random.Random(42)
    s = Seg()
    ndefs, neb = nebula([(300, 70, 420, 150, "#a21caf", 0.22), (640, 330, 380, 120, "#1d4ed8", 0.2),
                         (1050, 60, 260, 110, "#0e7490", 0.18), (120, 300, 260, 120, "#4c1d95", 0.25)])
    bx, by = 925, 192
    bdefs, bh = black_hole(rnd, bx, by)
    hud = "\n".join([
        brackets(690, 28, 1160, 352, L=22),
        f'<g stroke="{CYAN}" stroke-opacity="0.35">'
        + "".join(f'<line x1="{690 + i * 23.5:.0f}" y1="352" x2="{690 + i * 23.5:.0f}" y2="{346 if i % 5 else 340}"/>' for i in range(21))
        + "</g>",
        s.text("TARGET: SGR A*", 704, 54, 11, fill=CYAN),
        '<g><animate attributeName="opacity" values="1;0.2;1" dur="1.6s" repeatCount="indefinite"/>'
        + s.text("LOCKED", 1146, 54, 11, fill=AMBER, anchor="end") + "</g>",
        s.text("RA 17H45M40S", 704, 334, 10, fill=DIM),
        s.text("DEC -29°00'28\"", 1146, 334, 10, fill=DIM, anchor="end"),
    ])
    text = "\n".join([
        '<circle cx="77" cy="66" r="5" fill="#ef4444"><animate attributeName="opacity" values="1;0.15;1" dur="1.4s" repeatCount="indefinite"/></circle>',
        s.text("OBSERVATORY LOG // LIVE FEED", 92, 72, 13, fill=CYAN, attrs='opacity="0.85"'),
        s.text(NAME, 70, 172, 46, fill=ICE, ghost=(CYAN, 0.07), attrs='filter="url(#glow)"'),
        s.text(TAGLINE, 72, 222, 19, fill=CYAN),
        s.text(FIELDS, 72, 256, 15, fill=AMBER),
        '<rect x="72" y="280" width="300" height="2" fill="url(#rule)"/>',
        s.text("LAT 28.62 N  LON 77.37 E  // NOIDA", 72, 312, 11, fill=DIM),
    ])
    defs = ndefs + bdefs + f'''
<radialGradient id="space" cx="0.75" cy="0.5" r="0.9"><stop offset="0" stop-color="#0b1233"/><stop offset="1" stop-color="#02030a"/></radialGradient>
<linearGradient id="rule" x1="0" x2="1"><stop offset="0" stop-color="{CYAN}"/><stop offset="0.6" stop-color="{MAGENTA}"/>
  <stop offset="1" stop-color="{MAGENTA}" stop-opacity="0"/></linearGradient>
<clipPath id="card"><rect width="{W}" height="{H}" rx="22"/></clipPath>
<linearGradient id="scan" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{CYAN}" stop-opacity="0"/>
  <stop offset="1" stop-color="{CYAN}" stop-opacity="0.07"/></linearGradient>'''
    body = f'''<g clip-path="url(#card)">
<rect width="{W}" height="{H}" fill="url(#space)"/>
{neb}
{starfield(rnd, W, H, 320, 90, band=(-0.22, 330, 40))}
{bh}
{hud}
{text}
<rect x="0" y="-60" width="{W}" height="60" fill="url(#scan)"><animate attributeName="y" values="-60;{H}" dur="7s" repeatCount="indefinite"/></rect>
</g>
<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="21" fill="none" stroke="{CYAN}" stroke-opacity="0.25"/>'''
    (OUT / "banner.svg").write_text(svg(W, H, s, body, defs))


# --------------------------------------------------------------------------- typing line
def typing():
    W, H = 1200, 56
    s = Seg()
    phrases = ["OBSERVING THE UNIVERSE THROUGH DATA", "TRAINING MODELS / CHASING STARS",
               "MATHEMATICS IS THE LANGUAGE OF THE COSMOS", "FINDING SIGNAL IN THE NOISE"]
    size, per = 20, 4.0
    total = per * len(phrases)
    body, defs = [], []
    for i, p in enumerate(phrases):
        w = width(p, size) + 4
        x0 = W / 2 - w / 2
        # keyframes: hidden -> type in -> hold -> erase -> hidden (within this phrase's window)
        keys = [0.0, i * per / total, (i * per + 1.6) / total, (i * per + 3.2) / total, (i * per + 3.7) / total, 1.0]
        keys = sorted(set(round(k, 4) for k in keys))
        t0, t1, t2, t3 = [round(v, 4) for v in (i * per / total, (i * per + 1.6) / total, (i * per + 3.2) / total, (i * per + 3.7) / total)]

        def vals(a, b):
            m = {t1: b, t2: b}
            return ";".join(str(m.get(k, a)) for k in keys)
        kt = ";".join(f"{k:.4f}" for k in keys)
        on = ";".join("1" if t0 <= k < t3 else "0" for k in keys)
        defs.append(f'<clipPath id="tc{i}"><rect x="{x0:.1f}" y="0" width="{w:.1f}" height="{H}">'
                    f'<animate attributeName="width" values="{vals(0, round(w, 1))}" keyTimes="{kt}" dur="{total}s" repeatCount="indefinite"/>'
                    f'</rect></clipPath>')
        body.append(f'''<g opacity="{1 if i == 0 else 0}"><animate attributeName="opacity" values="{on}" keyTimes="{kt}" dur="{total}s" calcMode="discrete" repeatCount="indefinite"/>
  <g clip-path="url(#tc{i})">{s.text(p, x0, 38, size, fill=CYAN, attrs='filter="url(#glow)"')}</g>
  <rect y="18" width="10" height="21" fill="{AMBER}" x="{x0 + w + 2:.1f}">
    <animate attributeName="x" values="{vals(round(x0 + 2, 1), round(x0 + w + 2, 1))}" keyTimes="{kt}" dur="{total}s" repeatCount="indefinite"/>
    <animate attributeName="fill-opacity" values="1;0;1" dur="0.9s" repeatCount="indefinite"/></rect>
</g>''')
    (OUT / "typing.svg").write_text(svg(W, H, s, "\n".join(body), "".join(defs)))


# --------------------------------------------------------------------------- about + galaxy
def galaxy(rnd, cx, cy, R=175):
    pts = []
    for i in range(950):
        if i < 180:  # bulge stars
            r = abs(rnd.gauss(0, R * 0.14))
            a = rnd.uniform(0, 2 * math.pi)
            col = rnd.choice(["#fff4ea", "#ffd2a1", "#ffe8c2"])
        else:
            arm = i % 2
            r = R * (0.12 + 0.88 * rnd.random() ** 0.8)
            a = arm * math.pi + 2.6 * math.log(r / (R * 0.12) + 1) + rnd.gauss(0, 0.28)
            col = (rnd.choice(["#9bb0ff", "#cad7ff", "#e0f2fe", "#aabfff"]) if rnd.random() < 0.8
                   else rnd.choice(["#f472b6", "#e879f9"]))
        pts.append(f'<circle cx="{r * math.cos(a):.1f}" cy="{r * math.sin(a):.1f}" r="{rnd.uniform(0.6, 1.9):.1f}" '
                   f'fill="{col}" opacity="{rnd.uniform(0.35, 1):.2f}"/>')
    defs = '''<radialGradient id="core"><stop offset="0" stop-color="#fff7e0"/><stop offset="0.25" stop-color="#ffd2a1" stop-opacity="0.8"/>
  <stop offset="1" stop-color="#ffb56c" stop-opacity="0"/></radialGradient>
<radialGradient id="armglow"><stop offset="0" stop-color="#6366f1" stop-opacity="0.35"/><stop offset="0.7" stop-color="#7c3aed" stop-opacity="0.12"/>
  <stop offset="1" stop-color="#7c3aed" stop-opacity="0"/></radialGradient>'''
    body = f'''<g transform="translate({cx} {cy}) rotate(-24) scale(1 0.5)">
  <circle r="{R + 20}" fill="url(#armglow)"/>
  <g><animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="60s" repeatCount="indefinite"/>{"".join(pts)}</g>
</g>
<ellipse cx="{cx}" cy="{cy}" rx="46" ry="34" fill="url(#core)" transform="rotate(-24 {cx} {cy})">
  <animate attributeName="opacity" values="0.85;1;0.85" dur="5s" repeatCount="indefinite"/></ellipse>'''
    return defs, body


def about():
    W, H = 1200, 440
    rnd = random.Random(7)
    s = Seg()
    gdefs, gal = galaxy(rnd, 940, 215)
    rows = [("SUBJECT", "ABHINAV SINGH"), ("CLASS", "MATHEMATICS & COMPUTING"), ("STATION", "JIIT NOIDA // CLASS OF 2029"),
            ("COORDINATES", "28.62 N / 77.37 E"), ("RESEARCH", "AI / MACHINE LEARNING"), ("", "DATA SCIENCE"),
            ("", "INFORMATION RETRIEVAL"), ("OBSERVING", "ASTROPHYSICS / COSMOLOGY"), ("TRANSMITS", "OPEN SOURCE"),
            ("STATUS", "OPEN TO INTERNSHIPS & COLLABS")]
    lines, clips = [], []
    y0, step, size = 116, 28, 13
    for i, (k, v) in enumerate(rows):
        y = y0 + i * step
        key = (k + " " + "." * (12 - len(k))) if k else ""
        delay, dur = 0.4 + i * 0.32, 0.55
        clips.append(f'<clipPath id="ln{i}"><rect x="56" y="{y - size - 4}" width="640" height="{size + 10}">'
                     f'<animate attributeName="width" values="0;0;640" keyTimes="0;{delay / (delay + dur):.3f};1" '
                     f'dur="{delay + dur:.2f}s" fill="freeze"/></rect></clipPath>')
        lines.append(f'<g clip-path="url(#ln{i})">' + s.text(">", 60, y, size, fill=MAGENTA)
                     + (s.text(key, 82, y, size, fill=DIM) if key else "")
                     + s.text(v, 82 + 14 * 14 * size / 18, y, size, fill=AMBER if k == "STATUS" else ICE) + "</g>")
    cursor_y = y0 + len(rows) * step
    body = f'''<rect width="{W}" height="{H}" rx="20" fill="url(#aboutbg)"/>
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="20" fill="none" stroke="{CYAN}" stroke-opacity="0.22"/>
{starfield(rnd, W, H, 160, 30)}
{gal}
{brackets(40, 34, 700, 410, L=16, op=0.45)}
{s.text("MISSION LOG // SUBJECT PROFILE", 60, 72, 15, fill=CYAN, attrs='filter="url(#glow)"')}
<line x1="60" y1="86" x2="680" y2="86" stroke="{CYAN}" stroke-opacity="0.25"/>
{"".join(lines)}
<rect x="60" y="{cursor_y - 15}" width="9" height="15" fill="{AMBER}"><animate attributeName="opacity" values="1;0;1" dur="1s" repeatCount="indefinite"/></rect>
{s.text("OBJ: SPIRAL GALAXY // INCL 62°", 940, 410, 11, fill=DIM, anchor="middle")}'''
    defs = gdefs + "".join(clips) + '''<linearGradient id="aboutbg" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="#050816"/><stop offset="1" stop-color="#0b0f2a"/></linearGradient>'''
    (OUT / "about.svg").write_text(svg(W, H, s, body, defs))


# --------------------------------------------------------------------------- section headers
SECTIONS = [("about", "01", "ABOUT ME"), ("projects", "02", "MISSION FILES"), ("stack", "03", "INSTRUMENTATION"),
            ("telemetry", "04", "TELEMETRY"), ("comet", "05", "COMET TRAIL")]


def headers():
    W, H = 1200, 64
    for key, num, title in SECTIONS:
        s = Seg()
        tx = 70
        tw = width(f"{num} // {title}", 22)
        ticks = "".join(f'<line x1="{x}" y1="28" x2="{x}" y2="36"/>' for x in range(int(tx + tw + 60), W - 20, 40))
        body = f'''<circle cx="30" cy="32" r="14" fill="none" stroke="{CYAN}" stroke-opacity="0.4" stroke-dasharray="2 3"/>
<circle cx="30" cy="32" r="4" fill="{AMBER}" filter="url(#glow)"/>
<circle r="2.6" fill="{ICE}"><animateMotion dur="3s" repeatCount="indefinite" path="M44 32a14 14 0 1 1 -28 0a14 14 0 1 1 28 0"/></circle>
{s.text(num, tx, 43, 22, fill=AMBER, attrs='filter="url(#glow)"')}
{s.text("// " + title, tx + width(num + "  ", 22), 43, 22, fill=ICE, attrs='filter="url(#glow)"')}
<line x1="{tx + tw + 36:.0f}" y1="32" x2="{W - 10}" y2="32" stroke="url(#hl)" stroke-width="1.5"/>
<g stroke="{CYAN}" stroke-opacity="0.35">{ticks}</g>
{s.text(f"SEC {num}/05", W - 10, 56, 9, fill=DIM, anchor="end")}'''
        defs = (f'<linearGradient id="hl" x1="0" x2="1"><stop offset="0" stop-color="{CYAN}" stop-opacity="0.7"/>'
                f'<stop offset="1" stop-color="{MAGENTA}" stop-opacity="0.05"/></linearGradient>')
        (OUT / f"h-{key}.svg").write_text(svg(W, H, s, body, defs))


# --------------------------------------------------------------------------- divider
def divider():
    W, H = 1200, 30
    rnd = random.Random(3)
    s = Seg()
    stars = "".join(f'<circle cx="{rnd.uniform(0, W):.0f}" cy="{rnd.uniform(4, H - 4):.0f}" r="{rnd.choice([0.5, 0.8, 1.1])}" '
                    f'fill="{rnd.choice(SPECTRAL)}" opacity="{rnd.uniform(0.3, 0.9):.2f}"/>' for _ in range(70))
    body = f'''{stars}
<rect x="0" y="14.5" width="{W}" height="1" fill="url(#dl)"/>
<g><animateTransform attributeName="transform" type="translate" values="-140 0;{W + 40} 0" dur="5s" repeatCount="indefinite"/>
  <rect x="0" y="13.5" width="120" height="3" rx="1.5" fill="url(#tail)"/>
  <circle cx="121" cy="15" r="3.2" fill="#fff" filter="url(#glow)"/></g>'''
    defs = f'''<linearGradient id="dl" x1="0" x2="1"><stop offset="0" stop-color="{CYAN}" stop-opacity="0"/>
  <stop offset="0.3" stop-color="{CYAN}" stop-opacity="0.6"/><stop offset="0.7" stop-color="{MAGENTA}" stop-opacity="0.6"/>
  <stop offset="1" stop-color="{MAGENTA}" stop-opacity="0"/></linearGradient>
<linearGradient id="tail" x1="0" x2="1"><stop offset="0" stop-color="{CYAN}" stop-opacity="0"/><stop offset="1" stop-color="#e0f2fe"/></linearGradient>'''
    (OUT / "divider.svg").write_text(svg(W, H, s, body, defs))


# --------------------------------------------------------------------------- footer
def footer():
    W, H = 1200, 220
    rnd = random.Random(11)
    s = Seg()
    cx, cy, incl = 870, 112, 0.2
    planets = [(48, 3, 2.4, "#a8a29e", None), (72, 5, 3.6, "#fde68a", None), (98, 8, 4, "#60a5fa", None),
               (124, 12, 3.2, "#f87171", None), (178, 20, 8.5, "#fdba74", "jup"), (244, 30, 7, "#fde68a", "sat")]
    orbits, movers = [], []
    for r, per, pr, col, kind in planets:
        ry = r * incl
        orbits.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{r}" ry="{ry:.1f}" fill="none" stroke="{CYAN}" stroke-opacity="0.18"/>')
        path = f"M{cx + r} {cy}A{r} {ry:.1f} 0 1 1 {cx - r} {cy}A{r} {ry:.1f} 0 1 1 {cx + r} {cy}"
        extra = ""
        if kind == "jup":
            extra = f'<rect x="{-pr}" y="-1.5" width="{2 * pr}" height="2" fill="#b45309" opacity="0.6"/>'
        if kind == "sat":
            extra = f'<ellipse rx="{pr * 2}" ry="{pr * 0.55:.1f}" fill="none" stroke="#fef3c7" stroke-width="1.6" opacity="0.8"/>'
        movers.append(f'<g><animateMotion dur="{per}s" begin="-{rnd.uniform(0, per):.1f}s" repeatCount="indefinite" path="{path}"/>'
                      f'<circle r="{pr}" fill="{col}"/>{extra}</g>')
    m = "".join(movers)
    body = f'''<rect width="{W}" height="{H}" rx="20" fill="url(#fbg)"/>
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="20" fill="none" stroke="{CYAN}" stroke-opacity="0.22"/>
{starfield(rnd, W, H, 200, 40)}
{"".join(orbits)}
<g clip-path="url(#fback)">{m}</g>
<circle cx="{cx}" cy="{cy}" r="40" fill="url(#sunglow)"><animate attributeName="r" values="36;44;36" dur="4s" repeatCount="indefinite"/></circle>
<circle cx="{cx}" cy="{cy}" r="15" fill="#fff4c2" filter="url(#bigglow)"/>
<g clip-path="url(#ffront)">{m}</g>
{s.text("END OF TRANSMISSION", 60, 92, 28, fill=ICE, ghost=(CYAN, 0.07), attrs='filter="url(#glow)"')}
{s.text("CLEAR SKIES // THANKS FOR STOPPING BY", 62, 128, 14, fill=CYAN)}
<g><animate attributeName="opacity" values="1;0.2;1" dur="1.6s" repeatCount="indefinite"/>{s.text("SIGNAL ACTIVE", 62, 166, 11, fill=AMBER)}</g>
{s.text("// ABHINAV9897S", 200, 166, 11, fill=DIM)}'''
    defs = f'''<linearGradient id="fbg" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#050816"/><stop offset="1" stop-color="#0b1233"/></linearGradient>
<radialGradient id="sunglow"><stop offset="0" stop-color="#ffd27d" stop-opacity="0.7"/><stop offset="1" stop-color="#ff8c42" stop-opacity="0"/></radialGradient>
<clipPath id="fback"><rect x="0" y="0" width="{W}" height="{cy}"/></clipPath>
<clipPath id="ffront"><rect x="0" y="{cy}" width="{W}" height="{H - cy}"/></clipPath>'''
    (OUT / "footer.svg").write_text(svg(W, H, s, body, defs))


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    (OUT / "orb.svg").unlink(missing_ok=True)
    banner()
    typing()
    about()
    headers()
    divider()
    footer()
    for p in sorted(OUT.glob("*.svg")):
        xml.dom.minidom.parse(str(p))  # fail loudly on malformed SVG
        print(f"{p.name}: {p.stat().st_size / 1024:.0f} KB")
