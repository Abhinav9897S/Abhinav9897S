#!/usr/bin/env python3
"""Generate the static animated SVGs for the profile README.

Visual direction: restrained, Interstellar-style. Black, off-white and warm
greys with a single muted gold accent; thin hairlines, no neon, no glow.

GitHub strips JavaScript and external CSS/fonts from READMEs, but SVGs loaded
via <img> still run their own SMIL animations. All text uses the segment font
in segfont.py. 3D effects come from rotating flat groups inside a squashed
(inclined) parent group, or from projecting 3D geometry in Python and baking
the frames into SMIL keyframes.

Usage: python3 scripts/generate_assets.py
"""
import math
import random
import xml.dom.minidom
from pathlib import Path

from segfont import Seg, width

OUT = Path(__file__).resolve().parent.parent / "assets"

NAME = "ABHINAV SINGH"
TAGLINE = "MATHEMATICS & COMPUTING / JIIT 2029"
FIELDS = "AI  /  MACHINE LEARNING  /  DATA SCIENCE  /  ASTROPHYSICS"

# Palette
BG, PANEL, LINE = "#000000", "#07080a", "#26272a"
TEXT, SUB, DIM, GOLD = "#e8e6e1", "#a19d94", "#5f5b55", "#c9a45c"
STARS = ["#ffffff", "#f4f1ea", "#dedad2", "#c9c4ba"]

GLOW = '''
<filter id="soft" x="-50%" y="-50%" width="200%" height="200%">
  <feGaussianBlur stdDeviation="4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
</filter>'''


def svg(w, h, seg, body, extra_defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{w}" height="{h}" viewBox="0 0 {w} {h}">\n<defs>{seg.defs()}{GLOW}{extra_defs}</defs>\n{body}\n</svg>')


def panel(w, h, rx=14):
    return (f'<rect width="{w}" height="{h}" rx="{rx}" fill="{PANEL}"/>'
            f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="{rx}" fill="none" stroke="{LINE}"/>')


def starfield(rnd, w, h, n_static, n_twinkle, band=None):
    out = []
    for _ in range(n_static):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        if band and rnd.random() < 0.55:  # Milky Way band: y = a*x + b with scatter
            a, b, spread = band
            y = a * x + b + rnd.gauss(0, spread)
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rnd.choice([0.35, 0.45, 0.6])}" '
                   f'fill="{rnd.choice(STARS)}" opacity="{rnd.uniform(0.25, 0.7):.2f}"/>')
    for _ in range(n_twinkle):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rnd.choice([0.8, 1.0])}" fill="{rnd.choice(STARS)}">'
                   f'<animate attributeName="opacity" values="0.35;0.9;0.35" dur="{rnd.uniform(5, 10):.1f}s" '
                   f'begin="-{rnd.uniform(0, 8):.1f}s" repeatCount="indefinite"/></circle>')
    return "\n".join(out)


def brackets(x0, y0, x1, y1, L=14, col=SUB, op=0.45):
    p = (f"M{x0} {y0 + L}V{y0}H{x0 + L}M{x1 - L} {y0}H{x1}V{y0 + L}"
         f"M{x1} {y1 - L}V{y1}H{x1 - L}M{x0 + L} {y1}H{x0}V{y1 - L}")
    return f'<path d="{p}" fill="none" stroke="{col}" stroke-opacity="{op}" stroke-width="1"/>'


# --------------------------------------------------------------------------- banner
def black_hole(rnd, cx, cy, incl=0.2):
    """Gargantua-style black hole: thin rotating disk, lensed halo, photon ring."""
    bands = [(56, 78, 7, "#fffaf0"), (78, 108, 11, "#f3e3c3"), (108, 148, 17, "#dcc08e"), (148, 215, 28, "#a98552")]
    disk = []
    for bi, (r0, r1, period, col) in enumerate(bands):
        parts = []
        for r in range(r0, r1, 5):
            dash = rnd.choice(["30 6", "50 10", "18 5", "70 14"])
            op = 0.9 - 0.65 * (r - 56) / 160
            parts.append(f'<circle r="{r}" fill="none" stroke="{col}" stroke-width="{3.6 - bi * 0.5:.1f}" '
                         f'stroke-dasharray="{dash}" stroke-opacity="{op:.2f}"/>')
        disk.append(f'<g><animateTransform attributeName="transform" type="rotate" from="0" to="-360" '
                    f'dur="{period}s" repeatCount="indefinite"/>{"".join(parts)}</g>')
    disk_g = (f'<g mask="url(#beam)"><g transform="translate({cx} {cy}) scale(1 {incl})">'
              f'<circle r="215" fill="url(#diskglow)"/>{"".join(disk)}</g></g>')
    defs = f'''
<radialGradient id="diskglow"><stop offset="0.25" stop-color="#f3e3c3" stop-opacity="0.35"/>
  <stop offset="0.7" stop-color="#a98552" stop-opacity="0.12"/><stop offset="1" stop-color="#a98552" stop-opacity="0"/></radialGradient>
<radialGradient id="halo"><stop offset="0.3" stop-color="#e9d3a8" stop-opacity="0.16"/><stop offset="1" stop-color="#e9d3a8" stop-opacity="0"/></radialGradient>
<linearGradient id="beamg" x1="0" x2="1"><stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0.55"/></linearGradient>
<mask id="beam" maskUnits="userSpaceOnUse" x="{cx - 240}" y="{cy - 240}" width="480" height="480">
  <rect x="{cx - 240}" y="{cy - 240}" width="480" height="480" fill="url(#beamg)"/></mask>
<clipPath id="back"><rect x="{cx - 260}" y="{cy - 260}" width="520" height="260"/></clipPath>
<clipPath id="front"><rect x="{cx - 260}" y="{cy}" width="520" height="260"/></clipPath>
<linearGradient id="arc" x1="0" x2="1"><stop offset="0" stop-color="#fffaf0"/><stop offset="0.5" stop-color="#e9d3a8"/>
  <stop offset="1" stop-color="#fffaf0" stop-opacity="0.7"/></linearGradient>'''
    body = f'''
<circle cx="{cx}" cy="{cy}" r="170" fill="url(#halo)"/>
<g clip-path="url(#back)">{disk_g}</g>
<path d="M{cx - 64} {cy + 2}A64 62 0 0 1 {cx + 64} {cy + 2}" fill="none" stroke="url(#arc)" stroke-width="5" opacity="0.85" filter="url(#soft)"/>
<path d="M{cx - 54} {cy + 3}A54 46 0 0 0 {cx + 54} {cy + 3}" fill="none" stroke="#e9d3a8" stroke-width="1.4" opacity="0.55"/>
<circle cx="{cx}" cy="{cy}" r="46.5" fill="none" stroke="#fffaf0" stroke-width="1.6" opacity="0.9"/>
<circle cx="{cx}" cy="{cy}" r="45" fill="#000"/>
<g clip-path="url(#front)">{disk_g}</g>'''
    return defs, body


def banner():
    W, H = 1200, 380
    rnd = random.Random(42)
    s = Seg()
    bx, by = 925, 192
    bdefs, bh = black_hole(rnd, bx, by)
    hud = "\n".join([
        brackets(690, 30, 1160, 350, L=16),
        s.text("OBJECT  SGR A*", 708, 56, 10, fill=SUB),
        s.text("4.3E6 SOLAR MASSES", 1142, 56, 10, fill=DIM, anchor="end"),
        s.text("RA 17H 45M 40S", 708, 334, 10, fill=DIM),
        s.text("DEC -29° 00' 28\"", 1142, 334, 10, fill=DIM, anchor="end"),
    ])
    text = "\n".join([
        s.text("OBSERVATION LOG  /  2026", 72, 74, 12, fill=DIM),
        s.text(NAME, 70, 170, 46, fill=TEXT),
        s.text(TAGLINE, 72, 216, 17, fill=SUB),
        f'<rect x="72" y="240" width="56" height="1.5" fill="{GOLD}"/>',
        s.text(FIELDS, 72, 276, 12, fill=SUB),
        s.text("28.62 N  77.37 E  /  NOIDA, INDIA", 72, 334, 10, fill=DIM),
    ])
    defs = bdefs + f'''
<radialGradient id="space" cx="0.77" cy="0.5" r="0.75"><stop offset="0" stop-color="#0e0d0c"/><stop offset="1" stop-color="{BG}"/></radialGradient>
<clipPath id="card"><rect width="{W}" height="{H}" rx="14"/></clipPath>'''
    body = f'''<g clip-path="url(#card)">
<rect width="{W}" height="{H}" fill="url(#space)"/>
{starfield(rnd, W, H, 300, 40, band=(-0.2, 320, 38))}
{bh}
{hud}
{text}
</g>
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="14" fill="none" stroke="{LINE}"/>'''
    (OUT / "banner.svg").write_text(svg(W, H, s, body, defs))


# --------------------------------------------------------------------------- typing line
def typing():
    W, H = 1200, 56
    s = Seg()
    phrases = ["OBSERVING THE UNIVERSE THROUGH DATA", "MATHEMATICS IS THE LANGUAGE OF THE COSMOS",
               "FROM RAW SIGNAL TO MEASURED STRUCTURE", "DO NOT GO GENTLE INTO THAT GOOD NIGHT"]
    size, per = 16, 5.0
    total = per * len(phrases)
    body, defs = [], []
    for i, p in enumerate(phrases):
        w = width(p, size) + 4
        x0 = W / 2 - w / 2
        t0, t1, t2, t3 = [round(v / total, 4) for v in (i * per, i * per + 1.8, i * per + 4.2, i * per + 4.7)]
        keys = sorted({0.0, t0, t1, t2, t3, 1.0})

        def vals(a, b):
            m = {t1: b, t2: b}
            return ";".join(str(m.get(k, a)) for k in keys)
        kt = ";".join(f"{k:.4f}" for k in keys)
        on = ";".join("1" if t0 <= k < t3 else "0" for k in keys)
        defs.append(f'<clipPath id="tc{i}"><rect x="{x0:.1f}" y="0" width="{w:.1f}" height="{H}">'
                    f'<animate attributeName="width" values="{vals(0, round(w, 1))}" keyTimes="{kt}" dur="{total}s" repeatCount="indefinite"/>'
                    f'</rect></clipPath>')
        body.append(f'''<g opacity="{1 if i == 0 else 0}"><animate attributeName="opacity" values="{on}" keyTimes="{kt}" dur="{total}s" calcMode="discrete" repeatCount="indefinite"/>
  <g clip-path="url(#tc{i})">{s.text(p, x0, 36, size, fill=SUB)}</g>
  <rect y="19" width="2" height="18" fill="{GOLD}" x="{x0 + w + 4:.1f}">
    <animate attributeName="x" values="{vals(round(x0 + 4, 1), round(x0 + w + 4, 1))}" keyTimes="{kt}" dur="{total}s" repeatCount="indefinite"/>
    <animate attributeName="fill-opacity" values="1;0;1" dur="1.2s" calcMode="discrete" repeatCount="indefinite"/></rect>
</g>''')
    (OUT / "typing.svg").write_text(svg(W, H, s, "\n".join(body), "".join(defs)))


# --------------------------------------------------------------------------- about + galaxy
def galaxy(rnd, cx, cy, R=175):
    pts = []
    for i in range(1000):
        if i < 200:  # bulge stars
            r = abs(rnd.gauss(0, R * 0.13))
            a = rnd.uniform(0, 2 * math.pi)
            col = rnd.choice(["#f4ead8", "#e9d3a8", "#fffaf0"])
        else:
            arm = i % 2
            r = R * (0.12 + 0.88 * rnd.random() ** 0.8)
            a = arm * math.pi + 2.6 * math.log(r / (R * 0.12) + 1) + rnd.gauss(0, 0.2)
            col = rnd.choice(["#ffffff", "#dedad2", "#c9c4ba", "#b9c2cc"])
        pts.append(f'<circle cx="{r * math.cos(a):.1f}" cy="{r * math.sin(a):.1f}" r="{rnd.uniform(0.5, 1.5):.1f}" '
                   f'fill="{col}" opacity="{rnd.uniform(0.3, 0.9):.2f}"/>')
    defs = '''<radialGradient id="core"><stop offset="0" stop-color="#fffaf0" stop-opacity="0.95"/><stop offset="0.3" stop-color="#e9d3a8" stop-opacity="0.45"/>
  <stop offset="1" stop-color="#e9d3a8" stop-opacity="0"/></radialGradient>
<radialGradient id="diskhaze"><stop offset="0" stop-color="#dedad2" stop-opacity="0.08"/><stop offset="1" stop-color="#dedad2" stop-opacity="0"/></radialGradient>'''
    body = f'''<g transform="translate({cx} {cy}) rotate(-24) scale(1 0.5)">
  <circle r="{R + 20}" fill="url(#diskhaze)"/>
  <g><animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="90s" repeatCount="indefinite"/>{"".join(pts)}</g>
</g>
<ellipse cx="{cx}" cy="{cy}" rx="44" ry="30" fill="url(#core)" transform="rotate(-24 {cx} {cy})"/>'''
    return defs, body


def about():
    W, H = 1200, 440
    rnd = random.Random(7)
    s = Seg()
    gdefs, gal = galaxy(rnd, 940, 215)
    rows = [("SUBJECT", "ABHINAV SINGH"), ("PROGRAMME", "MATHEMATICS & COMPUTING"), ("INSTITUTE", "JIIT NOIDA / CLASS OF 2029"),
            ("POSITION", "28.62 N / 77.37 E"), ("RESEARCH", "AI / MACHINE LEARNING"), ("", "DATA SCIENCE"),
            ("", "INFORMATION RETRIEVAL"), ("OBSERVING", "ASTROPHYSICS / COSMOLOGY"), ("MISSION", "SUDARSHANA VYUHA"),
            ("CONTRIBUTES", "OPEN SOURCE"), ("STATUS", "OPEN TO INTERNSHIPS & COLLABORATION")]
    lines, clips = [], []
    y0, step, size = 112, 26, 12
    for i, (k, v) in enumerate(rows):
        y = y0 + i * step
        key = (k + " " + "." * (12 - len(k))) if k else ""
        delay, dur = 0.3 + i * 0.25, 0.5
        clips.append(f'<clipPath id="ln{i}"><rect x="56" y="{y - size - 4}" width="640" height="{size + 10}">'
                     f'<animate attributeName="width" values="0;0;640" keyTimes="0;{delay / (delay + dur):.3f};1" '
                     f'dur="{delay + dur:.2f}s" fill="freeze"/></rect></clipPath>')
        lines.append(f'<g clip-path="url(#ln{i})">'
                     + (s.text(key, 62, y, size, fill=DIM) if key else "")
                     + s.text(v, 62 + 14 * 14 * size / 18, y, size, fill=GOLD if k == "MISSION" else TEXT) + "</g>")
    body = f'''{panel(W, H)}
{starfield(rnd, W, H, 160, 15)}
{gal}
{s.text("SUBJECT PROFILE", 62, 66, 13, fill=TEXT)}
{s.text("FILE 01", 680, 66, 10, fill=DIM, anchor="end")}
<line x1="62" y1="82" x2="680" y2="82" stroke="{LINE}"/>
{"".join(lines)}
<line x1="62" y1="{y0 + len(rows) * step - 6}" x2="680" y2="{y0 + len(rows) * step - 6}" stroke="{LINE}"/>
{s.text("SPIRAL GALAXY / INCLINATION 60°", 940, 410, 10, fill=DIM, anchor="middle")}'''
    defs = gdefs + "".join(clips)
    (OUT / "about.svg").write_text(svg(W, H, s, body, defs))


# --------------------------------------------------------------------------- current mission
def rot_yx(p, ay, ax):
    x, y, z = p
    x, z = x * math.cos(ay) + z * math.sin(ay), -x * math.sin(ay) + z * math.cos(ay)
    y, z = y * math.cos(ax) - z * math.sin(ax), y * math.sin(ax) + z * math.cos(ax)
    return x, y, z


def mission():
    """Primary mission card: Sudarshana Vyuha, with a rotating 3D reconstruction of a building."""
    W, H = 1200, 380
    rnd = random.Random(21)
    s = Seg()
    # --- 3D model: 8 x 5 m room, 3 m walls, gable roof, 2 m doorway kept open in the floor plan
    V = {"f0": (-4, 0, -2.5), "f1": (4, 0, -2.5), "f2": (4, 0, 2.5), "f3": (-4, 0, 2.5),
         "t0": (-4, 3, -2.5), "t1": (4, 3, -2.5), "t2": (4, 3, 2.5), "t3": (-4, 3, 2.5),
         "r0": (-4, 4.4, 0), "r1": (4, 4.4, 0), "d0": (-1, 0, 2.5), "d1": (1, 0, 2.5),
         "d2": (-1, 2.1, 2.5), "d3": (1, 2.1, 2.5)}
    plan = [("f0", "f1"), ("f1", "f2"), ("f2", "d1"), ("d0", "f3"), ("f3", "f0")]
    frame_e = [("f0", "t0"), ("f1", "t1"), ("f2", "t2"), ("f3", "t3"), ("t0", "t1"), ("t1", "t2"), ("t2", "t3"),
               ("t3", "t0"), ("r0", "r1"), ("t0", "r0"), ("t3", "r0"), ("t1", "r1"), ("t2", "r1"),
               ("d0", "d2"), ("d1", "d3"), ("d2", "d3")]
    cloud = []
    for _ in range(110):  # sparse reconstruction points on walls and roof
        face = rnd.random()
        if face < 0.25:
            p = (rnd.uniform(-4, 4), rnd.uniform(0, 3), rnd.choice([-2.5, 2.5]))
        elif face < 0.45:
            p = (rnd.choice([-4, 4]), rnd.uniform(0, 3), rnd.uniform(-2.5, 2.5))
        elif face < 0.6:
            x, z = rnd.choice([-4, 4]), rnd.uniform(-2.5, 2.5)
            p = (x, rnd.uniform(3, 3 + 1.4 * (1 - abs(z) / 2.5)), z)
        else:
            z = rnd.uniform(-2.5, 2.5)
            p = (rnd.uniform(-4, 4), 3 + 1.4 * (1 - abs(z) / 2.5), z)
        if abs(p[0]) < 1 and p[2] == 2.5 and p[1] < 2.1:
            continue  # doorway stays empty
        cloud.append(p)
    cx, cy, sc, frames, dur, tilt = 940, 165, 28, 90, 36, 0.38

    def proj(p, fi):
        x, y, z = rot_yx((p[0], p[1] - 2.2, p[2]), 2 * math.pi * fi / frames, tilt)
        k = 14 / (14 - z)
        return cx + x * sc * k, cy - y * sc * k, z

    def edge_svg(edges, col, wdt):
        out = []
        for a, b in edges:
            ds, ops = [], []
            for fi in range(frames + 1):
                (x1, y1, z1), (x2, y2, z2) = proj(V[a], fi), proj(V[b], fi)
                ds.append(f"M{x1:.1f} {y1:.1f}L{x2:.1f} {y2:.1f}")
                ops.append(f"{0.35 + 0.65 * ((z1 + z2) / 2 + 5) / 10:.2f}")
            out.append(f'<path d="{ds[0]}" stroke="{col}" stroke-width="{wdt}" fill="none" stroke-linecap="round">'
                       f'<animate attributeName="d" dur="{dur}s" repeatCount="indefinite" values="{";".join(ds)}"/>'
                       f'<animate attributeName="opacity" dur="{dur}s" repeatCount="indefinite" values="{";".join(ops)}"/></path>')
        return "".join(out)

    pts = []
    for p in cloud:
        xs, ys = [], []
        for fi in range(0, frames + 1, 2):
            x, y, _ = proj(p, fi)
            xs.append(f"{x:.0f}")
            ys.append(f"{y:.0f}")
        pts.append(f'<circle r="1.1" fill="{SUB}" cx="{xs[0]}" cy="{ys[0]}">'
                   f'<animate attributeName="cx" dur="{dur}s" repeatCount="indefinite" values="{";".join(xs)}"/>'
                   f'<animate attributeName="cy" dur="{dur}s" repeatCount="indefinite" values="{";".join(ys)}"/></circle>')
    model = edge_svg(frame_e, TEXT, 1) + edge_svg(plan, GOLD, 1.6) + f'<g opacity="0.7">{"".join(pts)}</g>'

    # --- left column
    stages = ["FOOTAGE", "FRAMES", "POSES", "SURFACE", "PLAN"]
    px0, px1, py = 92, 590, 240
    step = (px1 - px0) / (len(stages) - 1)
    pipe = [f'<line x1="{px0}" y1="{py}" x2="{px1}" y2="{py}" stroke="{LINE}" stroke-width="1"/>']
    for i, st in enumerate(stages):
        x = px0 + i * step
        pipe.append(f'<rect x="{x - 4:.1f}" y="{py - 4}" width="8" height="8" fill="{PANEL}" stroke="{SUB}"/>')
        pipe.append(s.text(f"0{i + 1}", x, py - 14, 9, fill=DIM, anchor="middle"))
        pipe.append(s.text(st, x, py + 26, 10, fill=SUB, anchor="middle"))
    pipe.append(f'<rect y="{py - 1}" width="40" height="2" fill="{GOLD}">'
                f'<animate attributeName="x" values="{px0};{px1 - 40}" dur="9s" repeatCount="indefinite"/>'
                f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.1;0.9;1" dur="9s" repeatCount="indefinite"/></rect>')
    metrics = [("674,094", "DENSE POINTS"), ("4.7M", "TRIANGLES"), ("79/80", "FRAMES REGISTERED"), ("8.06 X 5.00 M", "FROM 8.00 X 5.00 M")]
    met = []
    mx = [62, 200, 318, 470]
    for (v, l), x in zip(metrics, mx):
        met.append(s.text(v, x, 318, 18, fill=TEXT))
        met.append(s.text(l, x, 340, 9, fill=DIM))
    body = f'''{panel(W, H)}
{starfield(rnd, W, H, 120, 10)}
{brackets(720, 30, 1160, 350, L=14)}
{s.text("RECONSTRUCTION / LIVE MODEL", 738, 54, 10, fill=SUB)}
{s.text("OFFLINE", 1142, 54, 10, fill=DIM, anchor="end")}
{model}
{s.text("8.00 X 5.00 M ROOM / 2.0 M DOORWAY KEPT OPEN", 738, 336, 9, fill=DIM)}
{s.text("PRIMARY MISSION", 62, 58, 11, fill=DIM)}
<rect x="{620 - width("IN PROGRESS", 11) - 16:.1f}" y="48" width="7" height="7" fill="{GOLD}"><animate attributeName="opacity" values="1;0.35;1" dur="3s" repeatCount="indefinite"/></rect>
{s.text("IN PROGRESS", 620, 58, 11, fill=GOLD, anchor="end")}
{s.text("SUDARSHANA VYUHA", 62, 106, 34, fill=TEXT)}
{s.text("TEAM ODAX  /  DRONE VIDEO TO 3D MODEL AND FLOOR PLAN", 62, 134, 11, fill=SUB)}
{s.text("RAW DRONE AND BODY-CAM FOOTAGE IN. A MEASURED 3D MODEL AND A", 62, 172, 10, fill=SUB)}
{s.text("DIMENSIONED FLOOR PLAN OUT. ON ONE LAPTOP, FULLY OFFLINE.", 62, 190, 10, fill=SUB)}
{"".join(pipe)}
<line x1="62" y1="286" x2="620" y2="286" stroke="{LINE}"/>
{"".join(met)}'''
    (OUT / "mission.svg").write_text(svg(W, H, s, body))


# --------------------------------------------------------------------------- section headers
SECTIONS = [("about", "01", "ABOUT"), ("mission", "02", "CURRENT MISSION"), ("projects", "03", "MISSION ARCHIVE"),
            ("stack", "04", "INSTRUMENTATION"), ("telemetry", "05", "TELEMETRY"), ("comet", "06", "TRAJECTORY")]


def headers():
    W, H = 1200, 60
    for key, num, title in SECTIONS:
        s = Seg()
        tw = width(title, 18)
        body = f'''{s.text(num, 10, 40, 12, fill=GOLD)}
{s.text(title, 50, 42, 18, fill=TEXT)}
<line x1="{50 + tw + 24:.0f}" y1="34" x2="{W - 90}" y2="34" stroke="{LINE}"/>
{s.text(f"{num} / {len(SECTIONS):02d}", W - 10, 40, 10, fill=DIM, anchor="end")}'''
        (OUT / f"h-{key}.svg").write_text(svg(W, H, s, body))


# --------------------------------------------------------------------------- divider
def divider():
    W, H = 1200, 24
    s = Seg()
    body = (f'<line x1="0" y1="12" x2="{W / 2 - 14}" y2="12" stroke="{LINE}"/>'
            f'<line x1="{W / 2 + 14}" y1="12" x2="{W}" y2="12" stroke="{LINE}"/>'
            f'<rect x="{W / 2 - 3}" y="9" width="6" height="6" fill="none" stroke="{GOLD}" transform="rotate(45 {W / 2} 12)"/>')
    (OUT / "divider.svg").write_text(svg(W, H, s, body))


# --------------------------------------------------------------------------- footer
def footer():
    W, H = 1200, 200
    rnd = random.Random(11)
    s = Seg()
    cx, cy, incl = 880, 100, 0.18
    planets = [(46, 6, 1.8, "#9e9a94"), (68, 10, 2.8, "#d8cfbd"), (92, 16, 3, "#a9b4bf"),
               (118, 24, 2.4, "#b59a87"), (170, 40, 6.5, "#cdb79a"), (236, 60, 5.5, "#d8cfbd")]
    orbits, movers = [], []
    for i, (r, per, pr, col) in enumerate(planets):
        ry = r * incl
        orbits.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{r}" ry="{ry:.1f}" fill="none" stroke="{LINE}"/>')
        path = f"M{cx + r} {cy}A{r} {ry:.1f} 0 1 1 {cx - r} {cy}A{r} {ry:.1f} 0 1 1 {cx + r} {cy}"
        ring = (f'<ellipse rx="{pr * 2}" ry="{pr * 0.5:.1f}" fill="none" stroke="#e8e6e1" stroke-width="1" opacity="0.7"/>'
                if i == 5 else "")
        movers.append(f'<g><animateMotion dur="{per}s" begin="-{rnd.uniform(0, per):.1f}s" repeatCount="indefinite" path="{path}"/>'
                      f'<circle r="{pr}" fill="{col}"/>{ring}</g>')
    m = "".join(movers)
    body = f'''{panel(W, H)}
{starfield(rnd, W, H, 180, 15)}
{"".join(orbits)}
<g clip-path="url(#fback)">{m}</g>
<circle cx="{cx}" cy="{cy}" r="34" fill="url(#sunglow)"/>
<circle cx="{cx}" cy="{cy}" r="11" fill="#fffaf0"/>
<g clip-path="url(#ffront)">{m}</g>
{s.text("END OF TRANSMISSION", 62, 88, 24, fill=TEXT)}
<rect x="62" y="106" width="40" height="1.5" fill="{GOLD}"/>
{s.text("CLEAR SKIES. THANK YOU FOR VISITING.", 62, 136, 11, fill=SUB)}
{s.text("GITHUB.COM/ABHINAV9897S", 62, 160, 10, fill=DIM)}'''
    defs = f'''<radialGradient id="sunglow"><stop offset="0" stop-color="#fffaf0" stop-opacity="0.45"/><stop offset="1" stop-color="#e9d3a8" stop-opacity="0"/></radialGradient>
<clipPath id="fback"><rect x="0" y="0" width="{W}" height="{cy}"/></clipPath>
<clipPath id="ffront"><rect x="0" y="{cy}" width="{W}" height="{H - cy}"/></clipPath>'''
    (OUT / "footer.svg").write_text(svg(W, H, s, body, defs))


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for old in ("orb.svg",):
        (OUT / old).unlink(missing_ok=True)
    banner()
    typing()
    about()
    mission()
    headers()
    divider()
    footer()
    for p in sorted(OUT.glob("*.svg")):
        xml.dom.minidom.parse(str(p))  # fail loudly on malformed SVG
        print(f"{p.name}: {p.stat().st_size / 1024:.0f} KB")
