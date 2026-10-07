#!/usr/bin/env python3
"""Render a neon 'Contribution Pulse' SVG from the last 31 days of contributions.

Runs in the profile workflow (needs GITHUB_TOKEN and USERNAME env vars).
`python3 scripts/activity_graph.py --demo` renders random data for previewing.
"""
import json
import os
import random
import sys
import urllib.request
from datetime import date, timedelta
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "dist" / "activity-graph.svg"
DAYS = 31
QUERY = """query($login: String!) { user(login: $login) { contributionsCollection {
  contributionCalendar { weeks { contributionDays { date contributionCount } } } } } }"""


def fetch(login, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        data = json.load(r)
    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    days = [(d["date"], d["contributionCount"]) for w in weeks for d in w["contributionDays"]]
    return days[-DAYS:]


def demo():
    today = date.today()
    return [((today - timedelta(days=DAYS - 1 - i)).isoformat(), random.randint(0, 12)) for i in range(DAYS)]


def smooth_path(pts, floor):
    """Catmull-Rom -> cubic Bezier for a soft neon curve."""
    d = f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"
    for i in range(len(pts) - 1):
        p0 = pts[i - 1] if i else pts[i]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[i + 2] if i + 2 < len(pts) else p2
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        c1 = (c1[0], min(c1[1], floor))
        c2 = (c2[0], min(c2[1], floor))
        d += f"C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}"
    return d


def render(days):
    W, H = 1200, 360
    L, R, T, B = 70, 30, 80, 60
    counts = [c for _, c in days]
    top = max(4, max(counts))
    top = ((top + 3) // 4) * 4  # nice round gridlines
    pw, ph = W - L - R, H - T - B
    xs = [L + pw * i / (len(days) - 1) for i in range(len(days))]
    pts = [(x, T + ph * (1 - c / top)) for x, c in zip(xs, counts)]
    line = smooth_path(pts, T + ph)
    area = f"{line}L{pts[-1][0]:.1f} {T + ph}L{pts[0][0]:.1f} {T + ph}Z"

    grid = []
    for k in range(5):
        y = T + ph * k / 4
        v = round(top * (1 - k / 4))
        grid.append(f'<line x1="{L}" x2="{W - R}" y1="{y:.1f}" y2="{y:.1f}" stroke="#a855f7" stroke-opacity="0.14"/>'
                    f'<text x="{L - 14}" y="{y + 4:.1f}" text-anchor="end">{v}</text>')
    labels = [f'<text x="{xs[i]:.1f}" y="{H - B + 26}" text-anchor="middle">{date.fromisoformat(days[i][0]).strftime("%b %d")}</text>'
              for i in range(0, len(days), 5)]
    dots = []
    for (x, y), c in zip(pts, counts):
        dots.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{4 if c else 2.5}" fill="{"#f472b6" if c else "#7c3aed"}"/>')
    total = sum(counts)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#0d0221"/><stop offset="1" stop-color="#1a0630"/>
  </linearGradient>
  <linearGradient id="area" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#a855f7" stop-opacity="0.55"/>
    <stop offset="1" stop-color="#a855f7" stop-opacity="0"/>
  </linearGradient>
  <linearGradient id="line" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#22d3ee"/><stop offset="0.5" stop-color="#c084fc"/><stop offset="1" stop-color="#f472b6"/>
  </linearGradient>
  <filter id="glow" x="-10%" y="-30%" width="120%" height="160%">
    <feGaussianBlur stdDeviation="4" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
</defs>
<rect width="{W}" height="{H}" rx="18" fill="url(#bg)"/>
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="18" fill="none" stroke="#a855f7" stroke-opacity="0.35"/>
<g font-family="'Segoe UI', Helvetica, Arial, sans-serif">
  <text x="{L}" y="46" font-size="24" font-weight="700" fill="#c084fc">Contribution Pulse</text>
  <text x="{W - R}" y="46" font-size="15" fill="#94a3b8" text-anchor="end">{total} contributions · last {DAYS} days</text>
  <g font-size="12" fill="#94a3b8">{"".join(grid)}{"".join(labels)}</g>
</g>
<path d="{area}" fill="url(#area)">
  <animate attributeName="opacity" from="0" to="1" begin="0.8s" dur="1.2s" fill="freeze"/>
</path>
<path d="{line}" fill="none" stroke="url(#line)" stroke-width="3" stroke-linecap="round" filter="url(#glow)"
      pathLength="1" stroke-dasharray="1" stroke-dashoffset="0">
  <animate attributeName="stroke-dashoffset" from="1" to="0" dur="2s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="0.4 0 0.2 1"/>
</path>
<g filter="url(#glow)">{"".join(dots)}</g>
</svg>'''


if __name__ == "__main__":
    days = demo() if "--demo" in sys.argv else fetch(os.environ["USERNAME"], os.environ["GITHUB_TOKEN"])
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(render(days))
    print(f"wrote {OUT}")
