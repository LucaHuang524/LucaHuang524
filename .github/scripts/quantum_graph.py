"""Render the contribution calendar as qubits that get "measured".

Every day starts in superposition (a flickering violet cell). A measurement
beam sweeps left to right and collapses each column to its real contribution
level, then the cycle restarts. Writes a dark and a light SVG to dist/.
"""

import json
import os
import random
import sys
import urllib.request

USER = os.environ.get("GH_USER", "lxkz1")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT_DIR = sys.argv[1] if len(sys.argv) > 1 else "dist"

CELL, GAP = 11, 3
PAD_X, PAD_TOP, PAD_BOTTOM = 24, 34, 40

CYCLE = 14.0        # seconds for one full loop
SWEEP_START = 1.6   # beam starts moving
SWEEP_END = 9.6     # beam reaches the right edge
RESET_AT = 12.8     # cells fall back into superposition

THEMES = {
    "dark": {
        "bg": "#0D1117",
        "levels": ["#161B22", "#2B3A67", "#4C5FD5", "#7B5CFF", "#C3B1FF"],
        "qubit": "#7B5CFF",
        "beam": "#C3B1FF",
        "text": "#8B949E",
        "accent": "#C3B1FF",
    },
    "light": {
        "bg": "#FFFFFF",
        "levels": ["#EBEDF0", "#D8D1FF", "#A897FF", "#7B5CFF", "#4B2FD6"],
        "qubit": "#7B5CFF",
        "beam": "#7B5CFF",
        "text": "#57606A",
        "accent": "#4B2FD6",
    },
}

LEVEL_INDEX = {
    "NONE": 0,
    "FIRST_QUARTILE": 1,
    "SECOND_QUARTILE": 2,
    "THIRD_QUARTILE": 3,
    "FOURTH_QUARTILE": 4,
}


def fetch_weeks():
    query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks { contributionDays { contributionCount contributionLevel weekday } }
          }
        }
      }
    }"""
    body = json.dumps({"query": query, "variables": {"login": USER}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    weeks = [
        [(d["weekday"], LEVEL_INDEX.get(d["contributionLevel"], 0)) for d in w["contributionDays"]]
        for w in cal["weeks"]
    ]
    return weeks, cal["totalContributions"]


def pct(seconds):
    return f"{seconds / CYCLE * 100:.2f}%"


def render(weeks, total, theme):
    t = THEMES[theme]
    cols = len(weeks)
    grid_w = cols * (CELL + GAP) - GAP
    grid_h = 7 * (CELL + GAP) - GAP
    width = grid_w + 2 * PAD_X
    height = PAD_TOP + grid_h + PAD_BOTTOM
    rng = random.Random(42)

    css = [
        "text{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}",
        "@keyframes flicker{0%,100%{opacity:.18}50%{opacity:.85}}",
        ".q{animation:flicker 1.1s ease-in-out infinite}",
        # beam sweeps across, then fades out before the reset
        "@keyframes sweep{"
        f"0%,{pct(SWEEP_START)}{{transform:translateX(0);opacity:0}}"
        f"{pct(SWEEP_START + 0.2)}{{opacity:1}}"
        f"{pct(SWEEP_END)}{{transform:translateX({grid_w}px);opacity:1}}"
        f"{pct(SWEEP_END + 0.4)},100%{{transform:translateX({grid_w}px);opacity:0}}}}",
        f".beam{{animation:sweep {CYCLE}s linear infinite}}",
        # caption swaps from 'superposition' to 'measured'
        "@keyframes capA{"
        f"0%,{pct(SWEEP_END)}{{opacity:1}}{pct(SWEEP_END + 0.3)},{pct(RESET_AT)}{{opacity:0}}"
        f"{pct(RESET_AT + 0.4)},100%{{opacity:1}}}}",
        "@keyframes capB{"
        f"0%,{pct(SWEEP_END)}{{opacity:0}}{pct(SWEEP_END + 0.4)},{pct(RESET_AT)}{{opacity:1}}"
        f"{pct(RESET_AT + 0.3)},100%{{opacity:0}}}}",
        f".capA{{animation:capA {CYCLE}s linear infinite}}",
        f".capB{{animation:capB {CYCLE}s linear infinite}}",
    ]

    body = []
    for c, week in enumerate(weeks):
        hit = SWEEP_START + (SWEEP_END - SWEEP_START) * (c + 0.5) / cols
        a, b = pct(hit), pct(hit + 0.15)
        r0, r1 = pct(RESET_AT), pct(RESET_AT + 0.5)
        css.append(f"@keyframes q{c}{{0%,{a}{{opacity:1}}{b},{r0}{{opacity:0}}{r1},100%{{opacity:1}}}}")
        css.append(f"@keyframes m{c}{{0%,{a}{{opacity:0}}{b},{r0}{{opacity:1}}{r1},100%{{opacity:0}}}}")
        css.append(
            f"@keyframes f{c}{{0%,{a}{{opacity:0}}{pct(hit + 0.08)}{{opacity:.9}}"
            f"{pct(hit + 0.9)},100%{{opacity:0}}}}"
        )
        css.append(f".q{c}{{animation:q{c} {CYCLE}s linear infinite}}")
        css.append(f".m{c}{{animation:m{c} {CYCLE}s linear infinite}}")
        css.append(f".f{c}{{animation:f{c} {CYCLE}s linear infinite}}")

        x = PAD_X + c * (CELL + GAP)
        qubits, measured, flashes = [], [], []
        for weekday, level in week:
            y = PAD_TOP + weekday * (CELL + GAP)
            delay = rng.uniform(0, 1.1)
            qubits.append(
                f'<rect class="q" style="animation-delay:-{delay:.2f}s" x="{x}" y="{y}" '
                f'width="{CELL}" height="{CELL}" rx="2.5" fill="{t["qubit"]}"/>'
            )
            measured.append(
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" fill="{t["levels"][level]}"/>'
            )
            if level > 0:
                flashes.append(
                    f'<rect x="{x - 2}" y="{y - 2}" width="{CELL + 4}" height="{CELL + 4}" rx="4" '
                    f'fill="none" stroke="{t["accent"]}" stroke-width="1.2"/>'
                )
        body.append(f'<g class="q{c}">{"".join(qubits)}</g>')
        body.append(f'<g class="m{c}">{"".join(measured)}</g>')
        if flashes:
            body.append(f'<g class="f{c}">{"".join(flashes)}</g>')

    beam = (
        f'<g class="beam"><rect x="{PAD_X - 6}" y="{PAD_TOP - 8}" width="3" height="{grid_h + 16}" '
        f'rx="1.5" fill="{t["beam"]}"/>'
        f'<rect x="{PAD_X - 16}" y="{PAD_TOP - 8}" width="22" height="{grid_h + 16}" '
        f'fill="url(#glow)"/></g>'
    )
    defs = (
        '<defs><linearGradient id="glow" x1="0" x2="1">'
        f'<stop offset="0" stop-color="{t["beam"]}" stop-opacity="0"/>'
        f'<stop offset="1" stop-color="{t["beam"]}" stop-opacity=".35"/>'
        "</linearGradient></defs>"
    )
    cap_y = PAD_TOP + grid_h + 26
    captions = (
        f'<text class="capA" x="{PAD_X}" y="{cap_y}" font-size="12" fill="{t["text"]}">'
        f'<tspan fill="{t["accent"]}">|ψ⟩</tspan> = every day in superposition… measuring</text>'
        f'<text class="capB" x="{PAD_X}" y="{cap_y}" font-size="12" fill="{t["text"]}">'
        f'<tspan fill="{t["accent"]}">measured:</tspan> {total} contributions in the last year</text>'
        f'<text x="{PAD_X}" y="20" font-size="12" fill="{t["text"]}">'
        f'<tspan fill="{t["accent"]}">⟨contributions|</tspan> {USER}</text>'
    )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">'
        f"{defs}<style>{''.join(css)}</style>"
        f'<rect width="{width}" height="{height}" rx="10" fill="{t["bg"]}"/>'
        f'{"".join(body)}{beam}{captions}</svg>'
    )


def main():
    if os.environ.get("FAKE_DATA"):
        rng = random.Random(7)
        weeks = [[(d, rng.choice([0, 0, 0, 1, 1, 2, 3, 4])) for d in range(7)] for _ in range(53)]
        total = 656
    else:
        weeks, total = fetch_weeks()
    os.makedirs(OUT_DIR, exist_ok=True)
    for theme, name in (("dark", "quantum-graph-dark.svg"), ("light", "quantum-graph.svg")):
        with open(os.path.join(OUT_DIR, name), "w", encoding="utf-8") as fh:
            fh.write(render(weeks, total, theme))


if __name__ == "__main__":
    main()
