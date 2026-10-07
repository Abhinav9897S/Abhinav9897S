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
from generate_assets import DIM, GLOW, GOLD, LINE, SUB, TEXT, brackets, panel, starfield  # noqa: E402
from segfont import Seg, width  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "dist"
FEATURED = ["DueDiligenceIQ", "forex-trade-optimizer", "AQI-Predictor", "Working-with-IBM-Granite"]
RAMP = ["#161616", "#2c2a27", "#4a463f", "#77705f", "#a99878", "#e8dcc0"]  # low -> high activity
SHADES = ["#e8e6e1", "#c9a45c", "#a19d94", "#7a756d", "#5f5b55", "#46423d", "#34312d", "#26241f"]
CELL = "#0c0d0f"

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


def heading(s, title, right, W):
    return (s.text(title, 50, 58, 13, fill=TEXT) + s.text(right, W - 50, 58, 10, fill=DIM, anchor="end")
            + f'<line x1="50" y1="74" x2="{W - 50}" y2="74" stroke="{LINE}"/>')


# --------------------------------------------------------------------------- telemetry
def telemetry(u, days, langs):
    W, H = 1200, 390
    s = Seg()
    cc = u["contributionsCollection"]
    cur, longest = streaks(days)
    stars = sum(r["stargazerCount"] for r in u["repositories"]["nodes"])
    cells = [("CONTRIBUTIONS / 1Y", cc["contributionCalendar"]["totalContributions"]),
             ("COMMITS / 1Y", cc["totalCommitContributions"] + cc["restrictedContributionsCount"]),
             ("PULL REQUESTS", u["pullRequests"]["totalCount"]), ("REPOSITORIES", u["repositories"]["totalCount"]),
             ("STARS EARNED", stars), ("FOLLOWERS", u["followers"]["totalCount"]),
             ("CURRENT STREAK / DAYS", cur), ("LONGEST STREAK / DAYS", longest)]
    body = [panel(W, H), starfield(random.Random(5), W, H, 90, 8),
            heading(s, "ACTIVITY SUMMARY", f"UPDATED {date.today().isoformat()}", W)]
    cw, ch, x0, y0 = 267, 98, 50, 96
    for i, (label, val) in enumerate(cells):
        x, y = x0 + (i % 4) * (cw + 10), y0 + (i // 4) * (ch + 10)
        body.append(f'<rect x="{x}" y="{y}" width="{cw}" height="{ch}" rx="6" fill="{CELL}" stroke="{LINE}"/>')
        body.append(s.text(label, x + 16, y + 26, 10, fill=DIM))
        body.append(s.text(str(val), x + cw - 18, y + 78, 34, fill=TEXT, anchor="end"))
    # language composition: monochrome bands, legend below
    ys = 336
    body.append(s.text("LANGUAGE COMPOSITION", 50, ys - 14, 10, fill=SUB))
    total = sum(v for _, _, v in langs) or 1
    x, bw = 50, W - 100
    for k, (name, _, v) in enumerate(langs):
        w = bw * v / total
        body.append(f'<rect x="{x:.1f}" y="{ys - 6}" width="{max(w - 1.5, 0.5):.1f}" height="8" fill="{SHADES[k % len(SHADES)]}"/>')
        x += w
    lx = 50
    for k, (name, _, v) in enumerate(langs[:6]):
        label = f"{name} {100 * v / total:.1f}%"
        body.append(f'<rect x="{lx}" y="{ys + 16}" width="8" height="8" fill="{SHADES[k]}"/>')
        body.append(s.text(label, lx + 14, ys + 25, 9, fill=SUB))
        lx += 14 + width(label, 9) + 28
    return svg(W, H, s, "\n".join(body))


# --------------------------------------------------------------------------- 3D skyline
def skyline(weeks_days):
    W, H = 1200, 430
    s = Seg()
    weeks = weeks_days[-53:]
    flat = [c for w in weeks for _, c in w]
    mx = max(flat + [1])
    levels = sorted(set(c for c in flat if c))
    q = [levels[int(len(levels) * k / 5)] for k in range(1, 5)] if levels else [1, 2, 3, 4]

    def level(c):
        return 0 if c == 0 else 1 + sum(c > t for t in q)

    sx, dx, dy, bw = 19.2, 5.6, -5.0, 15
    ox, oy = 64, 380
    bars = []
    for d in range(6, -1, -1):
        for wi, wk in enumerate(weeks):
            if d >= len(wk):
                continue
            c = wk[d][1]
            col = RAMP[min(level(c), 5)]
            h = 3 + 150 * math.sqrt(c / mx)
            x, y = ox + wi * sx + d * dx, oy + d * dy
            front = f"M{x:.1f} {y:.1f}h{bw}v{-h:.1f}h{-bw}Z"
            top = f"M{x:.1f} {y - h:.1f}h{bw}l{dx:.1f} {dy:.1f}h{-bw}Z"
            side = f"M{x + bw:.1f} {y:.1f}l{dx:.1f} {dy:.1f}v{-h:.1f}l{-dx:.1f} {-dy:.1f}Z"
            delay = 0.03 * wi + 0.05 * (6 - d)
            dur = delay + 1.2
            anim = (f'<animateTransform attributeName="transform" type="scale" values="1 0.01;1 0.01;1 1" '
                    f'keyTimes="0;{delay / dur:.3f};1" dur="{dur:.2f}s" fill="freeze" calcMode="spline" '
                    f'keySplines="0 0 1 1;0.2 0.7 0.2 1"/>')
            bars.append(f'<g transform="translate(0 {y:.1f})"><g>{anim}<g transform="translate(0 {-y:.1f})">'
                        f'<path d="{side}" fill="{col}" filter="url(#dark)"/><path d="{front}" fill="{col}"/>'
                        f'<path d="{top}" fill="{col}" filter="url(#lite)"/></g></g></g>')
    gx1 = ox + len(weeks) * sx
    ground = (f'<path d="M{ox - 8} {oy + 6}L{gx1 + 4} {oy + 6}L{gx1 + 4 + 7 * dx} {oy + 6 + 7 * dy}L{ox - 8 + 7 * dx} {oy + 6 + 7 * dy}Z" '
              f'fill="#ffffff" fill-opacity="0.02" stroke="{LINE}"/>')
    months, last = [], None
    for wi, wk in enumerate(weeks):
        m = date.fromisoformat(wk[0][0]).strftime("%b").upper()
        if m != last and wi < len(weeks) - 1:
            months.append(s.text(m, ox + wi * sx, oy + 30, 9, fill=DIM))
            last = m
    total = sum(flat)
    legend = "".join(f'<rect x="{W - 214 + i * 20}" y="98" width="14" height="8" fill="{c}"/>' for i, c in enumerate(RAMP))
    body = [panel(W, H), starfield(random.Random(9), W, H, 120, 10),
            heading(s, "CONTRIBUTION SKYLINE", "LAST 12 MONTHS", W),
            s.text(str(total), 50, 120, 30, fill=TEXT), s.text("CONTRIBUTIONS", 50 + width(str(total), 30) + 14, 120, 10, fill=DIM),
            s.text("LOW", W - 222, 106, 8, fill=DIM, anchor="end"), legend, s.text("HIGH", W - 86, 106, 8, fill=DIM),
            ground, *bars, *months]
    defs = ('<filter id="dark"><feColorMatrix type="matrix" values="0.55 0 0 0 0 0 0.55 0 0 0 0 0 0.55 0 0 0 0 0 1 0"/></filter>'
            '<filter id="lite"><feComponentTransfer><feFuncR type="linear" slope="1.3"/><feFuncG type="linear" slope="1.3"/>'
            '<feFuncB type="linear" slope="1.3"/></feComponentTransfer></filter>')
    return svg(W, H, s, "\n".join(body), defs)


# --------------------------------------------------------------------------- light curve
def light_curve(days):
    W, H = 1200, 340
    s = Seg()
    days = days[-60:]
    counts = [c for _, c in days]
    top = max(4, max(counts))
    top = ((top + 3) // 4) * 4
    L, R, T, B = 90, 50, 96, 60
    pw, ph = W - L - R, H - T - B

    def X(i):
        return L + pw * i / (len(days) - 1)

    def Y(v):
        return T + ph * (1 - v / top)

    body = [panel(W, H), starfield(random.Random(13), W, H, 80, 6),
            heading(s, "LIGHT CURVE / DAILY CONTRIBUTIONS", f"60 DAYS / PEAK {max(counts)}", W)]
    for k in range(5):
        v = top * k / 4
        body.append(f'<line x1="{L}" x2="{W - R}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke="{LINE}" stroke-opacity="0.7"/>')
        body.append(s.text(f"{v:g}", L - 14, Y(v) + 4, 9, fill=DIM, anchor="end"))
    for i in range(0, len(days), 10):
        body.append(s.text(days[i][0][5:], X(i), H - B + 24, 9, fill=DIM, anchor="middle"))
    body.append(f'<g transform="translate(34 {T + ph / 2}) rotate(-90)">{s.text("FLUX", 0, 0, 9, fill=DIM, anchor="middle")}</g>')
    # 7-day moving average as the model fit
    avg = [sum(counts[max(0, i - 3):i + 4]) / len(counts[max(0, i - 3):i + 4]) for i in range(len(counts))]
    fit = "M" + "L".join(f"{X(i):.1f} {Y(v):.1f}" for i, v in enumerate(avg))
    body.append(f'<path d="{fit}" fill="none" stroke="{GOLD}" stroke-width="1.4" stroke-dasharray="5 4"/>')
    pts = []
    for i, c in enumerate(counts):
        err = math.sqrt(c) if c else 0.5
        y0, y1 = Y(max(0, c - err)), Y(min(top, c + err))
        col = TEXT if c else DIM
        pts.append(f'<line x1="{X(i):.1f}" x2="{X(i):.1f}" y1="{y0:.1f}" y2="{y1:.1f}" stroke="{SUB}" stroke-opacity="0.45"/>'
                   f'<circle cx="{X(i):.1f}" cy="{Y(c):.1f}" r="{2.6 if c else 1.8}" fill="{col}"/>')
    body.append("".join(pts))
    body.append(f'<line x1="{W - 190}" x2="{W - 166}" y1="{H - 22}" y2="{H - 22}" stroke="{GOLD}" stroke-width="1.4" stroke-dasharray="5 4"/>')
    body.append(s.text("7-DAY MEAN", W - 50, H - 18, 9, fill=SUB, anchor="end"))
    return svg(W, H, s, "\n".join(body))


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
    lang = (r.get("primaryLanguage") or {"name": "N/A"})["name"]
    desc = wrap(r.get("description") or "NO DESCRIPTION ON FILE", 10, W - 70)
    if len(desc) > 3:
        desc = desc[:3]
        desc[-1] = desc[-1][:max(0, len(desc[-1]) - 3)] + "..."
    body = [panel(W, H, rx=12), starfield(random.Random(20 + i), W, H, 40, 4),
            s.text(f"FILE {i + 1:02d}", 34, 44, 10, fill=GOLD),
            s.text(f"UPDATED {r['pushedAt'][:10]}", W - 34, 44, 9, fill=DIM, anchor="end"),
            s.text(r["name"], 34, 82, 18, fill=TEXT),
            f'<line x1="34" y1="98" x2="{W - 34}" y2="98" stroke="{LINE}"/>']
    for k, line in enumerate(desc):
        body.append(s.text(line, 34, 124 + k * 19, 10, fill=SUB))
    body.append(f'<rect x="34" y="{H - 38}" width="7" height="7" fill="{SUB}"/>')
    body.append(s.text(lang, 48, H - 31, 10, fill=SUB))
    body.append(s.text(f"STARS {r['stargazerCount']}   FORKS {r['forkCount']}", W - 34, H - 31, 10, fill=DIM, anchor="end"))
    return svg(W, H, s, "\n".join(body))


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
            agg[e["node"]["name"]] = agg.get(e["node"]["name"], 0) + e["size"]
    langs = sorted(((n, None, v) for n, v in agg.items()), key=lambda t: -t[2])[:8]

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
