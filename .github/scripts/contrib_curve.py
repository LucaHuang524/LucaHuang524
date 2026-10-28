"""Weekly contributions as a line that draws itself, on loop.

Run daily by the workflow; writes a dark and a light SVG to dist/.
"""

import json
import os
import random
import sys
import urllib.request
from datetime import date

USER = os.environ.get("GH_USER", "lxkz1")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT_DIR = sys.argv[1] if len(sys.argv) > 1 else "dist"

W, H = 820, 250
PAD_L, PAD_R, PAD_T, PAD_B = 36, 36, 64, 44

CYCLE = 10.0
DRAW_START, DRAW_END = 0.4, 5.4
FADE_START, FADE_END = 9.2, 9.8

THEMES = {
    "dark": {"line": "#FFFFFF", "fill": "#FFFFFF", "grid": "#30363D", "text": "#8B949E", "strong": "#E6E6E6", "bar": "#FFFFFF"},
    "light": {"line": "#111111", "fill": "#000000", "grid": "#D0D7DE", "text": "#57606A", "strong": "#24292F", "bar": "#000000"},
}
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


def fetch():
    query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks { firstDay contributionDays { contributionCount } }
          }
        }
      }
    }"""
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        cal = json.load(resp)["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    weeks = [(w["firstDay"], sum(d["contributionCount"] for d in w["contributionDays"])) for w in cal["weeks"]]
    return weeks, cal["totalContributions"]


def smooth_path(points, lo, hi):
    """Catmull-Rom spline through the points, clamped between hi (top) and lo (baseline)."""
    d = [f"M{points[0][0]:.1f},{points[0][1]:.1f}"]
    for i in range(len(points) - 1):
        p0 = points[i - 1] if i > 0 else points[i]
        p1, p2 = points[i], points[i + 1]
        p3 = points[i + 2] if i + 2 < len(points) else p2
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        c1 = (c1[0], min(lo, max(hi, c1[1])))
        c2 = (c2[0], min(lo, max(hi, c2[1])))
        d.append(f"C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}")
    return " ".join(d)


def kt(*secs):
    return ";".join(f"{s / CYCLE:.4f}" for s in secs)


def render(weeks, total, theme):
    t = THEMES[theme]
    counts = [c for _, c in weeks]
    peak = max(counts) or 1
    cw, ch = W - PAD_L - PAD_R, H - PAD_T - PAD_B
    step = cw / (len(counts) - 1)
    base = PAD_T + ch
    pts = [(PAD_L + i * step, base - ch * c / peak) for i, c in enumerate(counts)]
    line = smooth_path(pts, base, PAD_T)
    area = f"{line} L{pts[-1][0]:.1f},{base:.1f} L{pts[0][0]:.1f},{base:.1f} Z"
    best = max(range(len(counts)), key=lambda i: counts[i])

    loop = f'dur="{CYCLE}s" repeatCount="indefinite"'
    vis = f'<animate attributeName="opacity" {loop} values="1;1;0;0" keyTimes="{kt(0, FADE_START, FADE_END, CYCLE)}"/>'

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        '<style>text{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}</style>',
        f'<defs><linearGradient id="area" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{t["fill"]}" stop-opacity=".22"/>'
        f'<stop offset="1" stop-color="{t["fill"]}" stop-opacity="0"/></linearGradient>'
        "</defs>",
        f'<text x="{PAD_L}" y="22" font-size="13" fill="{t["strong"]}">{USER}</text>',
        f'<text x="{W - PAD_R}" y="22" text-anchor="end" font-size="13" fill="{t["text"]}">'
        f'{total} contributions · last 12 months</text>',
        f'<line x1="{PAD_L}" y1="{base:.1f}" x2="{W - PAD_R}" y2="{base:.1f}" stroke="{t["grid"]}"/>',
    ]

    # faint weekly bars, always visible, so the shape reads even mid-animation
    bw = max(2.0, step * 0.45)
    for (x, y), c in zip(pts, counts):
        if c:
            out.append(f'<rect x="{x - bw / 2:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{base - y:.1f}" '
                       f'rx="1" fill="{t["bar"]}" fill-opacity=".07"/>')

    # month labels at the first week of each month
    seen, last_x = set(), -100
    for i, (first_day, _) in enumerate(weeks):
        m = date.fromisoformat(first_day).month
        if m not in seen and i < len(weeks) - 2 and pts[i][0] - last_x > 34:
            seen.add(m)
            last_x = pts[i][0]
            out.append(f'<text x="{pts[i][0]:.1f}" y="{base + 22:.1f}" font-size="11" fill="{t["text"]}">{MONTHS[m - 1]}</text>')

    # area and line revealed left to right, then faded out before the loop restarts
    out.append(
        f'<path d="{area}" fill="url(#area)" opacity="0">'
        f'<animate attributeName="opacity" {loop} values="0;0;1;1;0;0" '
        f'keyTimes="{kt(0, DRAW_END - .6, DRAW_END + .4, FADE_START, FADE_END, CYCLE)}"/></path>'
        f'<g>{vis}<path d="{line}" pathLength="1000" fill="none" stroke="{t["line"]}" stroke-width="2" '
        f'stroke-linejoin="round" stroke-dasharray="1000 1000" stroke-dashoffset="1000">'
        f'<animate attributeName="stroke-dashoffset" {loop} values="1000;1000;0;0" '
        f'keyTimes="{kt(0, DRAW_START, DRAW_END, CYCLE)}"/></path></g>'
    )

    # dot that leads the line
    out.append(
        f'<circle r="4" fill="{t["line"]}" opacity="0">'
        f'<animateMotion {loop} calcMode="linear" path="{line}" keyPoints="0;0;1;1" keyTimes="{kt(0, DRAW_START, DRAW_END, CYCLE)}"/>'
        f'<animate attributeName="opacity" {loop} values="0;0;1;1;0;0" keyTimes="{kt(0, DRAW_START - .1, DRAW_START, FADE_START, FADE_END, CYCLE)}"/>'
        "</circle>"
    )

    # label the best week once the line reaches it
    bx, by = pts[best]
    seg = [((pts[i + 1][0] - pts[i][0]) ** 2 + (pts[i + 1][1] - pts[i][1]) ** 2) ** .5 for i in range(len(pts) - 1)]
    frac = sum(seg[:best]) / (sum(seg) or 1)
    reach = DRAW_START + (DRAW_END - DRAW_START) * frac
    anchor = "end" if bx > W - 160 else "start"
    lx = bx - 8 if anchor == "end" else bx + 8
    out.append(
        f'<g opacity="0"><animate attributeName="opacity" {loop} values="0;0;1;1;0;0" '
        f'keyTimes="{kt(0, reach, reach + .3, FADE_START, FADE_END, CYCLE)}"/>'
        f'<circle cx="{bx:.1f}" cy="{by:.1f}" r="3" fill="none" stroke="{t["line"]}"/>'
        f'<text x="{lx:.1f}" y="{by - 8:.1f}" text-anchor="{anchor}" font-size="11" fill="{t["strong"]}">'
        f'best week · {counts[best]}</text></g>'
    )

    out.append("</svg>")
    return "".join(out)


def main():
    if os.environ.get("FAKE_DATA"):
        rng = random.Random(3)
        weeks, d = [], date(2025, 10, 26)
        from datetime import timedelta
        for i in range(53):
            c = 0 if i < 30 and rng.random() < .8 else rng.randint(0, 6 + i)
            weeks.append(((d + timedelta(weeks=i)).isoformat(), c))
        total = sum(c for _, c in weeks)
    else:
        weeks, total = fetch()
    os.makedirs(OUT_DIR, exist_ok=True)
    for theme, name in (("dark", "curve-dark.svg"), ("light", "curve.svg")):
        with open(os.path.join(OUT_DIR, name), "w", encoding="utf-8") as fh:
            fh.write(render(weeks, total, theme))


if __name__ == "__main__":
    main()
