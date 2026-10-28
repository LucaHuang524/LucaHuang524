"""Animated neural network: a forward pass, then a backward pass, on loop.

Static artwork, run once and commit the SVGs:
    python3 .github/scripts/network.py assets
"""

import os
import sys

OUT = sys.argv[1] if len(sys.argv) > 1 else "assets"

LAYERS = [4, 6, 6, 3]
W, H = 760, 270
X0, X1 = 170, 590
TOP, BOTTOM = 40, 220
NODE_R = 7

CYCLE = 8.0
HOP = 0.9             # seconds per layer
FWD_START = 0.4
BWD_START = FWD_START + HOP * (len(LAYERS) - 1) + 0.7

THEMES = {
    "dark": {"edge": "#FFFFFF", "node": "#0D1117", "ring": "#8B949E", "lit": "#FFFFFF",
             "pulse": "#FFFFFF", "grad": "#8B949E", "text": "#8B949E", "strong": "#E6E6E6"},
    "light": {"edge": "#000000", "node": "#FFFFFF", "ring": "#6E7781", "lit": "#111111",
              "pulse": "#111111", "grad": "#8C959F", "text": "#57606A", "strong": "#24292F"},
}


def positions():
    pts = []
    for li, n in enumerate(LAYERS):
        x = X0 + (X1 - X0) * li / (len(LAYERS) - 1)
        gap = (BOTTOM - TOP) / (max(LAYERS) - 1)
        y0 = (TOP + BOTTOM) / 2 - gap * (n - 1) / 2
        pts.append([(x, y0 + gap * i) for i in range(n)])
    return pts


def kt(*secs):
    return ";".join(f"{max(0.0, min(1.0, s / CYCLE)):.4f}" for s in secs)


def render(theme):
    t = THEMES[theme]
    pts = positions()
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        '<style>text{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}</style>',
    ]

    # edges
    for li in range(len(LAYERS) - 1):
        for (xa, ya) in pts[li]:
            for (xb, yb) in pts[li + 1]:
                out.append(f'<line x1="{xa:.1f}" y1="{ya:.1f}" x2="{xb:.1f}" y2="{yb:.1f}" '
                           f'stroke="{t["edge"]}" stroke-opacity=".09"/>')

    # pulses: forward (bright, left to right) and backward (grey, right to left)
    for li in range(len(LAYERS) - 1):
        f0, f1 = FWD_START + HOP * li, FWD_START + HOP * (li + 1)
        b_li = len(LAYERS) - 2 - li          # backward runs the layers in reverse
        b0, b1 = BWD_START + HOP * b_li, BWD_START + HOP * (b_li + 1)
        for (xa, ya) in pts[li]:
            for (xb, yb) in pts[li + 1]:
                out.append(
                    f'<circle r="2.2" fill="{t["pulse"]}" opacity="0">'
                    f'<animateMotion dur="{CYCLE}s" repeatCount="indefinite" calcMode="linear" '
                    f'path="M{xa:.1f},{ya:.1f} L{xb:.1f},{yb:.1f}" keyPoints="0;0;1;1" keyTimes="{kt(0, f0, f1, CYCLE)}"/>'
                    f'<animate attributeName="opacity" dur="{CYCLE}s" repeatCount="indefinite" '
                    f'values="0;0;.9;.9;0;0" keyTimes="{kt(0, f0, f0 + .05, f1 - .05, f1, CYCLE)}"/></circle>'
                )
                out.append(
                    f'<circle r="1.8" fill="{t["grad"]}" opacity="0">'
                    f'<animateMotion dur="{CYCLE}s" repeatCount="indefinite" calcMode="linear" '
                    f'path="M{xb:.1f},{yb:.1f} L{xa:.1f},{ya:.1f}" keyPoints="0;0;1;1" keyTimes="{kt(0, b0, b1, CYCLE)}"/>'
                    f'<animate attributeName="opacity" dur="{CYCLE}s" repeatCount="indefinite" '
                    f'values="0;0;.8;.8;0;0" keyTimes="{kt(0, b0, b0 + .05, b1 - .05, b1, CYCLE)}"/></circle>'
                )

    # nodes light up when a pulse reaches them
    n_layers = len(LAYERS)
    for li, layer in enumerate(pts):
        fwd_hit = FWD_START + HOP * li
        bwd_hit = BWD_START + HOP * (n_layers - 1 - li)
        for (x, y) in layer:
            out.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{NODE_R}" fill="{t["node"]}" stroke="{t["ring"]}" stroke-width="1.3"/>'
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{NODE_R - 2.5}" fill="{t["lit"]}" opacity="0">'
                f'<animate attributeName="opacity" dur="{CYCLE}s" repeatCount="indefinite" '
                f'values="0;0;1;.15;.15;.7;0;0" '
                f'keyTimes="{kt(0, fwd_hit, fwd_hit + .12, fwd_hit + .8, bwd_hit, bwd_hit + .12, bwd_hit + .8, CYCLE)}"/>'
                "</circle>"
            )

    # layer labels and a caption that follows the pass
    names = ["input", "hidden", "hidden", "output"]
    for li, name in enumerate(names):
        x = X0 + (X1 - X0) * li / (n_layers - 1)
        out.append(f'<text x="{x:.1f}" y="{BOTTOM + 34}" text-anchor="middle" font-size="12" fill="{t["text"]}">{name}</text>')
    fwd_end = FWD_START + HOP * (n_layers - 1)
    bwd_end = BWD_START + HOP * (n_layers - 1)
    out.append(
        f'<text x="{W / 2}" y="22" text-anchor="middle" font-size="13" fill="{t["strong"]}" opacity="0">forward pass'
        f'<animate attributeName="opacity" dur="{CYCLE}s" repeatCount="indefinite" values="0;0;1;1;0;0" '
        f'keyTimes="{kt(0, FWD_START - .2, FWD_START, fwd_end + .2, fwd_end + .5, CYCLE)}"/></text>'
        f'<text x="{W / 2}" y="22" text-anchor="middle" font-size="13" fill="{t["strong"]}" opacity="0">backward pass'
        f'<animate attributeName="opacity" dur="{CYCLE}s" repeatCount="indefinite" values="0;0;1;1;0;0" '
        f'keyTimes="{kt(0, BWD_START - .2, BWD_START, bwd_end + .2, bwd_end + .5, CYCLE)}"/></text>'
    )

    out.append("</svg>")
    return "".join(out)


def main():
    os.makedirs(OUT, exist_ok=True)
    for theme, name in (("dark", "network-dark.svg"), ("light", "network.svg")):
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
            fh.write(render(theme))


if __name__ == "__main__":
    main()
