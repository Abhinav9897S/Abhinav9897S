#!/usr/bin/env python3
"""Generate the animated 3D SVG assets used in the profile README.

GitHub strips JavaScript and external CSS from READMEs, but SVGs loaded via
<img> still run their own SMIL/CSS animations. Each 3D shape here is rotated
and projected in Python, and the frames are baked into SMIL keyframes.

Usage: python3 scripts/generate_assets.py
"""
import math
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets"
FONT = "'Segoe UI', 'SF Pro Display', Helvetica, Arial, sans-serif"
MONO = "'JetBrains Mono', 'Fira Code', Consolas, monospace"

NAME = "ABHINAV"
TAGLINE = "Developer  ·  Builder  ·  Lifelong Learner"


def f(x):
    return f"{x:.1f}".rstrip("0").rstrip(".")


def rot(p, ax, ay, az=0.0):
    x, y, z = p
    # X axis
    y, z = y * math.cos(ax) - z * math.sin(ax), y * math.sin(ax) + z * math.cos(ax)
    # Y axis
    x, z = x * math.cos(ay) + z * math.sin(ay), -x * math.sin(ay) + z * math.cos(ay)
    # Z axis
    x, y = x * math.cos(az) - y * math.sin(az), x * math.sin(az) + y * math.cos(az)
    return x, y, z


def project(p, cx, cy, scale, dist=4.0):
    x, y, z = p
    k = dist / (dist - z)
    return cx + x * scale * k, cy + y * scale * k, z


def icosahedron():
    t = (1 + 5 ** 0.5) / 2
    v = [(-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0),
         (0, -1, t), (0, 1, t), (0, -1, -t), (0, 1, -t),
         (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1)]
    n = math.sqrt(1 + t * t)
    v = [(a / n, b / n, c / n) for a, b, c in v]
    edges = [(i, j) for i in range(12) for j in range(i + 1, 12)
             if abs(math.dist(v[i], v[j]) - 2 / n) < 1e-6]
    return v, edges


def cube():
    v = [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
    edges = [(i, j) for i in range(8) for j in range(i + 1, 8)
             if sum(a != b for a, b in zip(v[i], v[j])) == 1]
    return v, edges


def wireframe(verts, edges, cx, cy, scale, frames, dur, spin=(1, 1, 0),
              stroke="url(#wire)", width=1.6, node_r=2.6, node_fill="#e9d5ff",
              tilt=(0.35, 0.0, 0.0)):
    """Rotating wireframe: each edge animates its endpoints and its depth-based opacity."""
    edge_d = [[] for _ in edges]
    edge_o = [[] for _ in edges]
    node_x = [[] for _ in verts]
    node_y = [[] for _ in verts]
    node_o = [[] for _ in verts]
    for fi in range(frames + 1):
        a = 2 * math.pi * fi / frames
        pts = []
        for p in verts:
            q = rot(p, tilt[0] + a * spin[0], tilt[1] + a * spin[1], tilt[2] + a * spin[2])
            pts.append(project(q, cx, cy, scale))
        for ei, (i, j) in enumerate(edges):
            (x1, y1, z1), (x2, y2, z2) = pts[i], pts[j]
            edge_d[ei].append(f"M{f(x1)} {f(y1)}L{f(x2)} {f(y2)}")
            depth = (z1 + z2) / 2  # -1 (back) .. 1 (front)
            edge_o[ei].append(f(0.18 + 0.82 * (depth + 1) / 2))
        for vi, (x, y, z) in enumerate(pts):
            node_x[vi].append(f(x))
            node_y[vi].append(f(y))
            node_o[vi].append(f(0.25 + 0.75 * (z + 1) / 2))
    out = []
    for ei in range(len(edges)):
        out.append(
            f'<path d="{edge_d[ei][0]}" stroke="{stroke}" stroke-width="{width}" '
            f'stroke-linecap="round" fill="none">'
            f'<animate attributeName="d" dur="{dur}s" repeatCount="indefinite" values="{";".join(edge_d[ei])}"/>'
            f'<animate attributeName="opacity" dur="{dur}s" repeatCount="indefinite" values="{";".join(edge_o[ei])}"/>'
            f"</path>")
    for vi in range(len(verts)):
        out.append(
            f'<circle r="{node_r}" fill="{node_fill}" cx="{node_x[vi][0]}" cy="{node_y[vi][0]}">'
            f'<animate attributeName="cx" dur="{dur}s" repeatCount="indefinite" values="{";".join(node_x[vi])}"/>'
            f'<animate attributeName="cy" dur="{dur}s" repeatCount="indefinite" values="{";".join(node_y[vi])}"/>'
            f'<animate attributeName="opacity" dur="{dur}s" repeatCount="indefinite" values="{";".join(node_o[vi])}"/>'
            f"</circle>")
    return "\n".join(out)


def stars(n, w, h, seed=7):
    import random
    rnd = random.Random(seed)
    out = []
    for _ in range(n):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        r = rnd.choice([0.6, 0.8, 1.0, 1.3])
        d = rnd.uniform(2, 6)
        b = rnd.uniform(0, 5)
        out.append(
            f'<circle cx="{f(x)}" cy="{f(y)}" r="{r}" fill="#fff">'
            f'<animate attributeName="opacity" values="0.15;0.9;0.15" dur="{d:.1f}s" '
            f'begin="-{b:.1f}s" repeatCount="indefinite"/></circle>')
    return "\n".join(out)


def perspective_grid(w, horizon, bottom, lines=10, frames=40, dur=3, color="#a855f7"):
    """Synthwave floor: converging rails + horizontal lines that scroll toward the viewer."""
    cx = w / 2
    out = []
    # Converging rails
    for i in range(-16, 17):
        xb = cx + i * (w / 14)
        out.append(f'<line x1="{f(cx + i * 6)}" y1="{horizon}" x2="{f(xb)}" y2="{bottom}"/>')
    # Moving horizontal lines: depth z goes from far to near, y = horizon + k / z
    span = bottom - horizon
    for li in range(lines):
        ys, os = [], []
        for fi in range(frames + 1):
            phase = (li + fi / frames) / lines  # 0..1
            z = 1.0 / (0.04 + phase * 0.96)  # far -> near
            y = horizon + span / z
            ys.append(f(y))
            os.append(f(min(1.0, phase * 1.6)))
        out.append(
            f'<line x1="0" x2="{w}" y1="{ys[0]}" y2="{ys[0]}">'
            f'<animate attributeName="y1" dur="{dur}s" repeatCount="indefinite" values="{";".join(ys)}"/>'
            f'<animate attributeName="y2" dur="{dur}s" repeatCount="indefinite" values="{";".join(ys)}"/>'
            f'<animate attributeName="opacity" dur="{dur}s" repeatCount="indefinite" values="{";".join(os)}"/>'
            f"</line>")
    return (f'<g stroke="{color}" stroke-width="1" stroke-opacity="0.7" mask="url(#floorFade)">'
            + "\n".join(out) + "</g>")


def banner():
    W, H = 1200, 340
    ico_v, ico_e = icosahedron()
    cube_v, cube_e = cube()
    shape = wireframe(ico_v, ico_e, 960, 150, 92, frames=90, dur=18, spin=(1, 1, 0))
    inner = wireframe(cube_v, cube_e, 960, 150, 30, frames=60, dur=9, spin=(-1, 1, 1),
                      stroke="#22d3ee", width=1.2, node_r=1.6, node_fill="#a5f3fc")
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#05010f"/>
    <stop offset="0.55" stop-color="#140a2e"/>
    <stop offset="1" stop-color="#2a0b3d"/>
  </linearGradient>
  <radialGradient id="sun" cx="0.5" cy="0.5" r="0.5">
    <stop offset="0" stop-color="#f472b6" stop-opacity="0.55"/>
    <stop offset="0.6" stop-color="#7c3aed" stop-opacity="0.18"/>
    <stop offset="1" stop-color="#7c3aed" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="wire" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#c084fc"/>
    <stop offset="1" stop-color="#f472b6"/>
  </linearGradient>
  <linearGradient id="title" x1="0" y1="0" x2="0.5" y2="0" spreadMethod="reflect">
    <stop offset="0" stop-color="#67e8f9"/>
    <stop offset="0.5" stop-color="#e9d5ff"/>
    <stop offset="1" stop-color="#f9a8d4"/>
    <animateTransform attributeName="gradientTransform" type="translate" values="0 0;1 0" dur="6s" repeatCount="indefinite"/>
  </linearGradient>
  <linearGradient id="fadeV" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#fff" stop-opacity="0"/>
    <stop offset="1" stop-color="#fff" stop-opacity="1"/>
  </linearGradient>
  <mask id="floorFade"><rect x="0" y="230" width="{W}" height="{H - 230}" fill="url(#fadeV)"/></mask>
  <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
    <feGaussianBlur stdDeviation="3.5" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="softglow" x="-20%" y="-50%" width="140%" height="200%">
    <feGaussianBlur stdDeviation="3" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <clipPath id="card"><rect width="{W}" height="{H}" rx="22"/></clipPath>
</defs>
<g clip-path="url(#card)">
  <rect width="{W}" height="{H}" fill="url(#bg)"/>
  <g>{stars(110, W, 230)}</g>
  <circle cx="960" cy="150" r="190" fill="url(#sun)">
    <animate attributeName="r" values="180;200;180" dur="6s" repeatCount="indefinite"/>
  </circle>
  {perspective_grid(W, 230, H)}
  <g filter="url(#glow)">
    <ellipse cx="960" cy="150" rx="150" ry="34" fill="none" stroke="#22d3ee" stroke-opacity="0.45" stroke-width="1.2" stroke-dasharray="4 7">
      <animateTransform attributeName="transform" type="rotate" values="-14 960 150;346 960 150" dur="30s" repeatCount="indefinite"/>
    </ellipse>
    <circle r="5" fill="#67e8f9">
      <animateMotion dur="7s" repeatCount="indefinite" path="M1110 150a150 34 0 1 1 -300 0a150 34 0 1 1 300 0"/>
    </circle>
    {shape}
    {inner}
  </g>
  <g font-family="{FONT}">
    <text x="80" y="118" fill="#a5b4fc" font-size="20" letter-spacing="6" opacity="0.9">HELLO, WORLD — I'M</text>
    <text x="76" y="200" font-size="92" font-weight="800" letter-spacing="4" fill="url(#title)" filter="url(#softglow)">{NAME}</text>
    <text x="80" y="246" fill="#e2e8f0" font-size="21" opacity="0.85">{TAGLINE}</text>
    <rect x="80" y="266" width="260" height="3" rx="1.5" fill="url(#title)">
      <animate attributeName="width" values="0;260" dur="1.4s" begin="0.4s" fill="freeze" calcMode="spline" keySplines="0.2 0.8 0.2 1"/>
    </rect>
  </g>
</g>
<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="21" fill="none" stroke="#a855f7" stroke-opacity="0.35"/>
</svg>'''
    (OUT / "banner.svg").write_text(svg)


def orb():
    """Rotating sphere of glowing points (Fibonacci lattice) for the About section."""
    W = H = 360
    cx, cy, R = W / 2, H / 2, 128
    n, frames, dur = 140, 60, 14
    golden = math.pi * (3 - 5 ** 0.5)
    pts = []
    for i in range(n):
        y = 1 - 2 * (i + 0.5) / n
        r = math.sqrt(1 - y * y)
        th = golden * i
        pts.append((math.cos(th) * r, y, math.sin(th) * r))
    dots = []
    for i, p in enumerate(pts):
        xs, ys, rs, os = [], [], [], []
        for fi in range(frames + 1):
            a = 2 * math.pi * fi / frames
            q = rot(p, 0.38, a)
            x, y, z = project(q, cx, cy, R, dist=5)
            xs.append(f(x)); ys.append(f(y))
            rs.append(f(1.2 + 1.8 * (z + 1) / 2))
            os.append(f(0.15 + 0.85 * (z + 1) / 2))
        color = ["#22d3ee", "#c084fc", "#f472b6"][i % 3]
        dots.append(
            f'<circle fill="{color}" cx="{xs[0]}" cy="{ys[0]}" r="{rs[0]}">'
            f'<animate attributeName="cx" dur="{dur}s" repeatCount="indefinite" values="{";".join(xs)}"/>'
            f'<animate attributeName="cy" dur="{dur}s" repeatCount="indefinite" values="{";".join(ys)}"/>'
            f'<animate attributeName="r" dur="{dur}s" repeatCount="indefinite" values="{";".join(rs)}"/>'
            f'<animate attributeName="opacity" dur="{dur}s" repeatCount="indefinite" values="{";".join(os)}"/>'
            f"</circle>")
    rings = []
    for i, (rx, ry, d, col) in enumerate([(165, 40, 22, "#c084fc"), (165, 40, 30, "#22d3ee")]):
        start = -20 if i == 0 else 25
        rings.append(
            f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="none" stroke="{col}" '
            f'stroke-opacity="0.5" stroke-width="1.2" stroke-dasharray="2 6">'
            f'<animateTransform attributeName="transform" type="rotate" '
            f'values="{start} {cx} {cy};{start + (360 if i == 0 else -360)} {cx} {cy}" dur="{d}s" repeatCount="indefinite"/>'
            f"</ellipse>")
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
  <radialGradient id="core" cx="0.5" cy="0.5" r="0.5">
    <stop offset="0" stop-color="#a855f7" stop-opacity="0.45"/>
    <stop offset="0.7" stop-color="#6d28d9" stop-opacity="0.08"/>
    <stop offset="1" stop-color="#6d28d9" stop-opacity="0"/>
  </radialGradient>
  <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
    <feGaussianBlur stdDeviation="2.2" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
</defs>
<circle cx="{cx}" cy="{cy}" r="170" fill="url(#core)">
  <animate attributeName="opacity" values="0.6;1;0.6" dur="5s" repeatCount="indefinite"/>
</circle>
<g filter="url(#glow)">
{chr(10).join(rings)}
{chr(10).join(dots)}
</g>
</svg>'''
    (OUT / "orb.svg").write_text(svg)


def divider():
    W, H = 1200, 24
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
  <linearGradient id="g" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#22d3ee" stop-opacity="0"/>
    <stop offset="0.3" stop-color="#22d3ee"/>
    <stop offset="0.5" stop-color="#c084fc"/>
    <stop offset="0.7" stop-color="#f472b6"/>
    <stop offset="1" stop-color="#f472b6" stop-opacity="0"/>
  </linearGradient>
  <linearGradient id="spark" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#fff" stop-opacity="0"/>
    <stop offset="0.5" stop-color="#fff"/>
    <stop offset="1" stop-color="#fff" stop-opacity="0"/>
  </linearGradient>
  <filter id="glow"><feGaussianBlur stdDeviation="2"/></filter>
</defs>
<rect x="0" y="11" width="{W}" height="2" fill="url(#g)"/>
<rect x="0" y="9" width="{W}" height="6" fill="url(#g)" opacity="0.5" filter="url(#glow)"/>
<rect y="10" width="160" height="4" rx="2" fill="url(#spark)">
  <animate attributeName="x" values="-160;{W}" dur="3.5s" repeatCount="indefinite"/>
</rect>
</svg>'''
    (OUT / "divider.svg").write_text(svg)


def footer():
    W, H = 1200, 120
    ico_v, ico_e = icosahedron()
    left = wireframe(ico_v, ico_e, 90, 60, 34, frames=60, dur=12, spin=(1, -1, 0),
                     width=1.2, node_r=1.6)
    right = wireframe(ico_v, ico_e, 1110, 60, 34, frames=60, dur=12, spin=(-1, 1, 0),
                      width=1.2, node_r=1.6)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#140a2e"/>
    <stop offset="0.5" stop-color="#05010f"/>
    <stop offset="1" stop-color="#2a0b3d"/>
  </linearGradient>
  <linearGradient id="wire" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#c084fc"/>
    <stop offset="1" stop-color="#f472b6"/>
  </linearGradient>
  <linearGradient id="t" x1="0" y1="0" x2="0.5" y2="0" spreadMethod="reflect">
    <stop offset="0" stop-color="#22d3ee"/>
    <stop offset="0.5" stop-color="#c084fc"/>
    <stop offset="1" stop-color="#f472b6"/>
    <animateTransform attributeName="gradientTransform" type="translate" values="0 0;1 0" dur="6s" repeatCount="indefinite"/>
  </linearGradient>
  <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
    <feGaussianBlur stdDeviation="2.5" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
</defs>
<rect width="{W}" height="{H}" rx="18" fill="url(#bg)"/>
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="18" fill="none" stroke="#a855f7" stroke-opacity="0.35"/>
<g filter="url(#glow)">{left}{right}</g>
<text x="{W / 2}" y="56" text-anchor="middle" font-family="{FONT}" font-size="26" font-weight="700" letter-spacing="3" fill="url(#t)">THANKS FOR STOPPING BY</text>
<text x="{W / 2}" y="86" text-anchor="middle" font-family="{MONO}" font-size="15" fill="#94a3b8">&lt;/&gt; build things that matter  ·  ship  ·  repeat</text>
</svg>'''
    (OUT / "footer.svg").write_text(svg)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    banner()
    orb()
    divider()
    footer()
    for p in sorted(OUT.glob("*.svg")):
        print(f"{p.name}: {p.stat().st_size / 1024:.0f} KB")
