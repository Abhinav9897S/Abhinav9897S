#!/usr/bin/env python3
"""Build the data-driven SVGs (telemetry, 3D skyline, light curve, project cards).

Runs in the profile workflow with GITHUB_TOKEN and USERNAME set.
`python3 scripts/build_dynamic.py --demo [OUT_DIR]` renders fake data for previewing.
"""
import json
import math
import os
import random
import sys
import urllib.request
import xml.dom.minidom
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_assets import AMBER, CYAN, DIM, GLOW, ICE, MAGENTA, brackets, starfield  # noqa: E402
from segfont import Seg, width  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "dist"
FEATURED = ["DueDiligenceIQ", "forex-trade-optimizer", "AQI-Predictor", "Working-with-IBM-Granite"]
RAMP = ["#111633", "#3b2a8c", "#7c3aed", "#c026d3", "#38bdf8", "#e0f2fe"]  # nebula: cold -> hot

QUERY = """query($login: String!) { user(login: $login) {
  followers { totalCount }
  pullRequests { totalCount }
  repositories(ownerAffiliations: OWNER, isFork: false, first: 100) { totalCount nodes {
    name description stargazerCount forkCount pushedAt
    primaryLanguage { name color }
    languages(first: 10, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name color } } } } }
  contributionsCollection {
    totalCommitContributions totalPullRequestContributions totalIssueContributions restrictedContributionsCount
    contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } } } } }"""


def fetch(login, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        data = json.load(r)
    if "errors" in data:
        raise SystemExit(data["errors"])
    return data["data"]["user"]


def demo_data():
    rnd = random.Random(1)
    start = date.today() - timedelta(days=370)
    while start.weekday() != 6:
        start += timedelta(days=1)
    weeks, d = [], start
    while d <= date.today():
        days = []
        for _ in range(7):
            if d > date.today():
                break
            days.append({"date": d.isoformat(), "contributionCount": rnd.choice([0, 0, 0, 1, 2, 3, 5, 8, 12])})
            d += timedelta(days=1)
        weeks.append({"contributionDays": days})
    langs = [("Python", "#3572A5", 60000), ("Jupyter Notebook", "#DA5B0B", 30000), ("JavaScript", "#f1e05a", 15000),
             ("HTML", "#e34c26", 8000), ("CSS", "#563d7c", 4000), ("C++", "#f34b7d", 2000)]
    repos = [{"name": n, "description": "Demo description for this repository that is moderately long to test wrapping",
              "stargazerCount": rnd.randint(0, 9), "forkCount": rnd.randint(0, 3), "pushedAt": "2026-09-01T00:00:00Z",
              "primaryLanguage": {"name": "Python", "color": "#3572A5"},
              "languages": {"edges": [{"size": s, "node": {"name": l, "color": c}} for l, c, s in langs]}} for n in FEATURED]
    return {"followers": {"totalCount": 6}, "pullRequests": {"totalCount": 14},
            "repositories": {"totalCount": 7, "nodes": repos},
            "contributionsCollection": {"totalCommitContributions": 210, "totalPullRequestContributions": 12,
                                        "totalIssueContributions": 4, "restrictedContributionsCount": 30,
                                        "contributionCalendar": {"totalContributions": 280, "weeks": weeks}}}


def svg(w, h, s, body, defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}">\n<defs>{s.defs()}{GLOW}{defs}</defs>\n{body}\n</svg>')


def frame(w, h):
    return (f'<rect width="{w}" height="{h}" rx="18" fill="url(#bg)"/>'
            f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="18" fill="none" stroke="{CYAN}" stroke-opacity="0.22"/>')


BG = ('<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#050816"/>'
      '<stop offset="1" stop-color="#0b0f2a"/></linearGradient>')


def streaks(days):
    counts = [c for _, c in days]
    longest = cur = 0
    for c in counts:
        cur = cur + 1 if c else 0
        longest = max(longest, cur)
    current = 0
    i = len(counts) - 1
    if counts and counts[i] == 0:  # today not counted yet
        i -= 1
    while i >= 0 and counts[i]:
        current += 1
        i -= 1
    return current, longest


# --------------------------------------------------------------------------- telemetry
def telemetry(u, days, langs):
    W, H = 1200, 400
    s = Seg()
    cc = u["contributionsCollection"]
    cur, longest = streaks(days)
    stars = sum(r["stargazerCount"] for r in u["repositories"]["nodes"])
    cells = [("CONTRIBUTIONS 1Y", cc["contributionCalendar"]["totalContributions"]),
             ("COMMITS 1Y", cc["totalCommitContributions"] + cc["restrictedContributionsCount"]),
             ("PULL REQUESTS", u["pullRequests"]["totalCount"]), ("REPOSITORIES", u["repositories"]["totalCount"]),
             ("STARS EARNED", stars), ("FOLLOWERS", u["followers"]["totalCount"]),
             ("CURRENT STREAK", cur), ("LONGEST STREAK", longest)]
    body = [frame(W, H), starfield(random.Random(5), W, H, 120, 20), brackets(24, 22, W - 24, H - 22, L=16, op=0.4),
            s.text("TELEMETRY // LIVE FROM GITHUB", 50, 62, 15, fill=CYAN, attrs='filter="url(#glow)"'),
            s.text(f"UPDATED {date.today().isoformat()}", W - 50, 62, 11, fill=DIM, anchor="end")]
    cw, ch, x0, y0 = 270, 104, 50, 84
    for i, (label, val) in enumerate(cells):
        x, y = x0 + (i % 4) * (cw + 10), y0 + (i // 4) * (ch + 10)
        v = str(val)
        body.append(f'<rect x="{x}" y="{y}" width="{cw}" height="{ch}" rx="8" fill="#0a1030" stroke="{CYAN}" stroke-opacity="0.15"/>')
        body.append(s.text(label, x + 16, y + 26, 11, fill=DIM))
        digits = max(5, len(v))
        body.append(s.text(v.rjust(digits), x + cw - 18, y + 82, 40, fill=AMBER, anchor="end",
                           ghost=None, attrs='filter="url(#glow)"'))
        body.append(s.text("8" * digits, x + cw - 18, y + 82, 40, fill=AMBER, anchor="end", attrs='opacity="0.06"'))
    # language spectrum
    ys = 332
    body.append(s.text("LANGUAGE SPECTRUM", 50, ys - 14, 11, fill=CYAN))
    total = sum(v for _, _, v in langs) or 1
    x, bw = 50, W - 100
    for name, col, v in langs:
        w = bw * v / total
        body.append(f'<rect x="{x:.1f}" y="{ys - 6}" width="{w:.1f}" height="14" fill="{col}" opacity="0.9"/>')
        x += w
    body.append(f'<rect x="50" y="{ys - 6}" width="{bw}" height="14" fill="url(#lines)"/>')
    lx = 50
    for name, col, v in langs[:6]:
        label = f"{name} {100 * v / total:.1f}%"
        body.append(f'<rect x="{lx}" y="{ys + 22}" width="9" height="9" fill="{col}"/>')
        body.append(s.text(label, lx + 15, ys + 32, 10, fill=ICE))
        lx += 15 + width(label, 10) + 26
    defs = BG + ('<pattern id="lines" width="37" height="14" patternUnits="userSpaceOnUse">'
                 '<rect x="11" width="1.5" height="14" fill="#000" opacity="0.45"/><rect x="29" width="1" height="14" fill="#000" opacity="0.3"/></pattern>')
    return svg(W, H, s, "\n".join(body), defs)


# --------------------------------------------------------------------------- 3D skyline
def skyline(weeks_days):
    W, H = 1200, 440
    s = Seg()
    weeks = weeks_days[-53:]
    flat = [c for w in weeks for _, c in w]
    mx = max(flat + [1])
    levels = sorted(set(c for c in flat if c))
    q = [levels[int(len(levels) * k / 5)] for k in range(1, 5)] if levels else [1, 2, 3, 4]

    def level(c):
        return 0 if c == 0 else 1 + sum(c > t for t in q)

    sx, dx, dy, bw = 19.2, 5.6, -5.0, 15
    ox, oy = 64, 384
    bars = []
    for d in range(6, -1, -1):
        for wi, wk in enumerate(weeks):
            if d >= len(wk):
                continue
            c = wk[d][1]
            lv = min(level(c), 5)
            h = 3 + 150 * math.sqrt(c / mx)
            x, y = ox + wi * sx + d * dx, oy + d * dy
            col = RAMP[lv]
            front = f"M{x:.1f} {y:.1f}h{bw}v{-h:.1f}h{-bw}Z"
            top = f"M{x:.1f} {y - h:.1f}h{bw}l{dx:.1f} {dy:.1f}h{-bw}Z"
            side = f"M{x + bw:.1f} {y:.1f}l{dx:.1f} {dy:.1f}v{-h:.1f}l{-dx:.1f} {-dy:.1f}Z"
            delay = 0.03 * wi + 0.05 * (6 - d)
            dur = delay + 0.9
            anim = (f'<animateTransform attributeName="transform" type="scale" values="1 0.01;1 0.01;1 1" '
                    f'keyTimes="0;{delay / dur:.3f};1" dur="{dur:.2f}s" fill="freeze"/>')
            bars.append(f'<g transform="translate(0 {y:.1f})"><g>{anim}<g transform="translate(0 {-y:.1f})">'
                        f'<path d="{side}" fill="{col}" filter="url(#dark)"/><path d="{front}" fill="{col}"/>'
                        f'<path d="{top}" fill="{col}" filter="url(#lite)"/></g></g></g>')
    # ground plane
    gx1 = ox + len(weeks) * sx
    ground = (f'<path d="M{ox - 8} {oy + 6}L{gx1 + 4} {oy + 6}L{gx1 + 4 + 7 * dx} {oy + 6 + 7 * dy}L{ox - 8 + 7 * dx} {oy + 6 + 7 * dy}Z" '
              f'fill="#7c3aed" opacity="0.12" stroke="{CYAN}" stroke-opacity="0.3"/>')
    months, last = [], None
    for wi, wk in enumerate(weeks):
        m = date.fromisoformat(wk[0][0]).strftime("%b").upper()
        if m != last and wi < len(weeks) - 1:
            months.append(s.text(m, ox + wi * sx, oy + 30, 10, fill=DIM))
            last = m
    total = sum(flat)
    legend = "".join(f'<rect x="{W - 230 + i * 22}" y="70" width="16" height="10" fill="{c}"/>' for i, c in enumerate(RAMP))
    body = [frame(W, H), starfield(random.Random(9), W, H, 160, 30),
            s.text("CONTRIBUTION SKYLINE // LAST 12 MONTHS", 50, 52, 15, fill=CYAN, attrs='filter="url(#glow)"'),
            s.text(f"{total} CONTRIBUTIONS", 50, 84, 22, fill=AMBER, attrs='filter="url(#glow)"'),
            s.text("COLD", W - 238, 66, 9, fill=DIM, anchor="end"), legend, s.text("HOT", W - 92, 66, 9, fill=DIM),
            ground, *bars, *months]
    defs = BG + ('<filter id="dark"><feColorMatrix type="matrix" values="0.55 0 0 0 0 0 0.55 0 0 0 0 0 0.55 0 0 0 0 0 1 0"/></filter>'
                 '<filter id="lite"><feComponentTransfer><feFuncR type="linear" slope="1.35"/><feFuncG type="linear" slope="1.35"/>'
                 '<feFuncB type="linear" slope="1.35"/></feComponentTransfer></filter>')
    return svg(W, H, s, "\n".join(body), defs)


# --------------------------------------------------------------------------- light curve
def light_curve(days):
    W, H = 1200, 340
    s = Seg()
    days = days[-60:]
    counts = [c for _, c in days]
    top = max(4, max(counts))
    top = ((top + 3) // 4) * 4
    L, R, T, B = 90, 40, 80, 64
    pw, ph = W - L - R, H - T - B

    def X(i):
        return L + pw * i / (len(days) - 1)

    def Y(v):
        return T + ph * (1 - v / top)

    body = [frame(W, H), starfield(random.Random(13), W, H, 100, 15),
            s.text("LIGHT CURVE // DAILY CONTRIBUTIONS // 60 DAYS", 50, 50, 15, fill=CYAN, attrs='filter="url(#glow)"'),
            s.text(f"PEAK FLUX {max(counts)}", W - 50, 50, 11, fill=AMBER, anchor="end")]
    for k in range(5):
        v = top * k / 4
        body.append(f'<line x1="{L}" x2="{W - R}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke="{CYAN}" stroke-opacity="0.1"/>')
        body.append(s.text(f"{v:g}", L - 14, Y(v) + 5, 10, fill=DIM, anchor="end"))
    for i in range(0, len(days), 10):
        body.append(s.text(days[i][0][5:], X(i), H - B + 26, 10, fill=DIM, anchor="middle"))
    body.append(f'<g transform="translate(30 {T + ph / 2}) rotate(-90)">{s.text("FLUX", 0, 0, 10, fill=DIM, anchor="middle")}</g>')
    # 7-day moving average as the model fit
    avg = [sum(counts[max(0, i - 3):i + 4]) / len(counts[max(0, i - 3):i + 4]) for i in range(len(counts))]
    fit = "M" + "L".join(f"{X(i):.1f} {Y(v):.1f}" for i, v in enumerate(avg))
    body.append(f'<path d="{fit}" fill="none" stroke="{MAGENTA}" stroke-width="2" stroke-dasharray="6 5" opacity="0.8" filter="url(#glow)"/>')
    pts = []
    for i, c in enumerate(counts):
        err = math.sqrt(c) if c else 0.5
        y0, y1 = Y(max(0, c - err)), Y(min(top, c + err))
        col = AMBER if c else "#475569"
        pts.append(f'<line x1="{X(i):.1f}" x2="{X(i):.1f}" y1="{y0:.1f}" y2="{y1:.1f}" stroke="{col}" stroke-opacity="0.5"/>'
                   f'<circle cx="{X(i):.1f}" cy="{Y(c):.1f}" r="{3.2 if c else 2.2}" fill="{col}"/>')
    body.append(f'<g filter="url(#glow)">{"".join(pts)}</g>')
    body.append(f'<rect x="{L}" y="{T}" width="2" height="{ph}" fill="{CYAN}" opacity="0.5">'
                f'<animate attributeName="x" values="{L};{W - R}" dur="6s" repeatCount="indefinite"/></rect>')
    body.append(s.text("--- 7 DAY FIT", W - 50, H - 22, 10, fill=MAGENTA, anchor="end"))
    return svg(W, H, s, "\n".join(body), BG)


# --------------------------------------------------------------------------- project cards
def wrap(text, size, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        nxt = (cur + " " + w).strip()
        if width(nxt, size) > maxw and cur:
            lines.append(cur)
            cur = w
        else:
            cur = nxt
    if cur:
        lines.append(cur)
    return lines


def project_card(i, r):
    W, H = 590, 210
    s = Seg()
    lang = r.get("primaryLanguage") or {"name": "N/A", "color": DIM}
    desc = wrap(r.get("description") or "NO DESCRIPTION ON FILE", 11, W - 70)
    if len(desc) > 3:
        desc = desc[:3]
        desc[-1] = desc[-1][:max(0, len(desc[-1]) - 3)] + "..."
    body = [frame(W, H), starfield(random.Random(20 + i), W, H, 50, 10), brackets(14, 14, W - 14, H - 14, L=12, op=0.4),
            s.text(f"OBJ-{i + 1:02d}", 34, 46, 11, fill=AMBER),
            s.text(f"UPDATED {r['pushedAt'][:10]}", W - 34, 46, 9, fill=DIM, anchor="end"),
            s.text(r["name"], 34, 84, 19, fill=ICE, attrs='filter="url(#glow)"')]
    for k, line in enumerate(desc):
        body.append(s.text(line, 34, 116 + k * 20, 11, fill="#94a3b8"))
    body.append(f'<circle cx="40" cy="{H - 34}" r="5" fill="{lang["color"] or DIM}" filter="url(#glow)"/>')
    body.append(s.text(lang["name"], 54, H - 28, 11, fill=CYAN))
    body.append(s.text(f"STARS {r['stargazerCount']}  FORKS {r['forkCount']}", W - 34, H - 28, 11, fill=AMBER, anchor="end"))
    return svg(W, H, s, "\n".join(body), BG)


def main():
    demo = "--demo" in sys.argv
    out = Path(next((a for a in sys.argv[1:] if not a.startswith("--")), OUT))
    u = demo_data() if demo else fetch(os.environ["USERNAME"], os.environ["GITHUB_TOKEN"])
    cal = u["contributionsCollection"]["contributionCalendar"]["weeks"]
    weeks = [[(d["date"], d["contributionCount"]) for d in w["contributionDays"]] for w in cal]
    days = [d for w in weeks for d in w]
    agg = {}
    for r in u["repositories"]["nodes"]:
        for e in r["languages"]["edges"]:
            n = e["node"]
            name, col, size = n["name"], n["color"] or "#64748b", e["size"]
            agg[name] = (col, agg.get(name, (col, 0))[1] + size)
    langs = sorted(((n, c, v) for n, (c, v) in agg.items()), key=lambda t: -t[2])[:8]

    out.mkdir(parents=True, exist_ok=True)
    files = {"telemetry.svg": telemetry(u, days, langs), "skyline.svg": skyline(weeks), "lightcurve.svg": light_curve(days)}
    by_name = {r["name"]: r for r in u["repositories"]["nodes"]}
    for i, name in enumerate(FEATURED):
        if name in by_name:
            files[f"project-{name}.svg"] = project_card(i, by_name[name])
    for fn, content in files.items():
        xml.dom.minidom.parseString(content)  # fail loudly on malformed SVG
        (out / fn).write_text(content)
        print(f"{fn}: {len(content) / 1024:.0f} KB")


if __name__ == "__main__":
    main()
