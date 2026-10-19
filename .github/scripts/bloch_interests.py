"""Draw an animated Bloch sphere with interests around it.

Static artwork (no data needed): run once and commit the SVGs in assets/.
    python3 .github/scripts/bloch_interests.py assets
"""

import math
import os
import sys

OUT = sys.argv[1] if len(sys.argv) > 1 else "assets"

W, H = 760, 290
CX, CY, R = 380, 145, 96
RY = R * 0.32          # how flat the equator looks (fake perspective)
STEPS = 96
DUR = 7                # seconds per precession loop

LEFT = ["machine learning", "language models"]
RIGHT = ["quantum computing", "digital inclusion"]

THEMES = {
    "dark": {"line": "#D0D0D0", "vec": "#FFFFFF", "tip": "#FFFFFF",
             "text": "#C9D1D9", "accent": "#FFFFFF", "faint": "#FFFFFF"},
    "light": {"line": "#555555", "vec": "#111111", "tip": "#111111",
              "text": "#24292F", "accent": "#111111", "faint": "#000000"},
}


def state(i):
    """Point on the sphere for animation step i (precessing + nodding)."""
    phi = 2 * math.pi * i / STEPS
    theta = math.radians(52 + 18 * math.sin(2 * phi))
    x = CX + R * math.sin(theta) * math.cos(phi)
    y = CY - R * math.cos(theta) + RY * math.sin(theta) * math.sin(phi)
    px = x
    py = CY + RY * math.sin(theta) * math.sin(phi)     # shadow on the equator plane
    return x, y, px, py


def values(fn):
    pts = [state(i) for i in range(STEPS + 1)]
    return ";".join(f"{fn(p):.1f}" for p in pts)


def anim(attr, fn):
    return (f'<animate attributeName="{attr}" dur="{DUR}s" repeatCount="indefinite" '
            f'calcMode="linear" values="{values(fn)}"/>')


def render(theme):
    t = THEMES[theme]
    trail = " ".join(f"{state(i)[0]:.1f},{state(i)[1]:.1f}" for i in range(STEPS + 1))
    eq_back = f"M {CX - R} {CY} A {R} {RY:.1f} 0 0 1 {CX + R} {CY}"
    eq_front = f"M {CX - R} {CY} A {R} {RY:.1f} 0 0 0 {CX + R} {CY}"

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        "<defs>",
        f'<radialGradient id="glow"><stop offset="0" stop-color="{t["tip"]}" stop-opacity=".9"/>'
        f'<stop offset="1" stop-color="{t["tip"]}" stop-opacity="0"/></radialGradient>',
        f'<radialGradient id="body" cx=".38" cy=".32"><stop offset="0" stop-color="{t["faint"]}" stop-opacity=".16"/>'
        f'<stop offset="1" stop-color="{t["faint"]}" stop-opacity="0"/></radialGradient>',
        f'<linearGradient id="fadeL" x1="0" x2="1"><stop offset="0" stop-color="{t["line"]}" stop-opacity=".7"/>'
        f'<stop offset="1" stop-color="{t["line"]}" stop-opacity="0"/></linearGradient>',
        f'<linearGradient id="fadeR" x1="1" x2="0"><stop offset="0" stop-color="{t["line"]}" stop-opacity=".7"/>'
        f'<stop offset="1" stop-color="{t["line"]}" stop-opacity="0"/></linearGradient>',
        "</defs>",
        '<style>text{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}</style>',
        # sphere
        f'<circle cx="{CX}" cy="{CY}" r="{R}" fill="url(#body)" stroke="{t["line"]}" stroke-opacity=".55" stroke-width="1.4"/>',
        f'<ellipse cx="{CX}" cy="{CY}" rx="{RY:.1f}" ry="{R}" fill="none" stroke="{t["line"]}" stroke-opacity=".18"/>',
        f'<path d="{eq_back}" fill="none" stroke="{t["line"]}" stroke-opacity=".3" stroke-dasharray="3 4"/>',
        f'<path d="{eq_front}" fill="none" stroke="{t["line"]}" stroke-opacity=".55"/>',
        f'<line x1="{CX}" y1="{CY - R - 6}" x2="{CX}" y2="{CY + R + 6}" stroke="{t["line"]}" stroke-opacity=".3" stroke-dasharray="2 4"/>',
        f'<text x="{CX}" y="{CY - R - 14}" text-anchor="middle" font-size="14" fill="{t["accent"]}">|0⟩</text>',
        f'<text x="{CX}" y="{CY + R + 26}" text-anchor="middle" font-size="14" fill="{t["accent"]}">|1⟩</text>',
        # particles orbiting the equator
        f'<circle r="2.6" fill="{t["tip"]}" opacity=".8"><animateMotion dur="5s" repeatCount="indefinite" path="{eq_front} A {R} {RY:.1f} 0 0 0 {CX - R} {CY}"/></circle>',
        f'<circle r="1.8" fill="{t["tip"]}" opacity=".55"><animateMotion dur="8s" begin="-3s" repeatCount="indefinite" path="{eq_front} A {R} {RY:.1f} 0 0 0 {CX - R} {CY}"/></circle>',
        # precession trail
        f'<polyline points="{trail}" fill="none" stroke="{t["vec"]}" stroke-opacity=".22" stroke-dasharray="2 3"/>',
        # shadow of the state on the equator plane
        f'<line x1="{CX}" y1="{CY}" stroke="{t["line"]}" stroke-opacity=".35" stroke-dasharray="2 3">'
        f'{anim("x2", lambda p: p[2])}{anim("y2", lambda p: p[3])}</line>',
        f'<line stroke="{t["line"]}" stroke-opacity=".35" stroke-dasharray="2 3">'
        f'{anim("x1", lambda p: p[0])}{anim("y1", lambda p: p[1])}{anim("x2", lambda p: p[2])}{anim("y2", lambda p: p[3])}</line>',
        # state vector, glowing tip and |psi> label riding along
        f'<line x1="{CX}" y1="{CY}" stroke="{t["vec"]}" stroke-width="2.6" stroke-linecap="round">'
        f'{anim("x2", lambda p: p[0])}{anim("y2", lambda p: p[1])}</line>',
        f'<circle r="14" fill="url(#glow)">{anim("cx", lambda p: p[0])}{anim("cy", lambda p: p[1])}</circle>',
        f'<circle r="4.2" fill="{t["tip"]}">{anim("cx", lambda p: p[0])}{anim("cy", lambda p: p[1])}</circle>',
        f'<text font-size="14" fill="{t["text"]}">|ψ⟩{anim("x", lambda p: p[0] + 10)}{anim("y", lambda p: p[1] - 10)}</text>',
        f'<circle cx="{CX}" cy="{CY}" r="2.4" fill="{t["vec"]}"/>',
    ]

    # interests: two on each side, pulsing one after another
    rows = [CY - 42, CY + 52]
    for k, (label, y) in enumerate(zip(LEFT + RIGHT, rows + rows)):
        left = k < 2
        begin = f"{k * 1.75:.2f}s"
        pulse = (f'<animate attributeName="opacity" values=".45;1;1;.45;.45" keyTimes="0;.08;.22;.32;1" '
                 f'dur="7s" begin="{begin}" repeatCount="indefinite"/>')
        grow = (f'<animate attributeName="r" values="3;6;6;3;3" keyTimes="0;.08;.22;.32;1" '
                f'dur="7s" begin="{begin}" repeatCount="indefinite"/>')
        if left:
            tx, anchor, dot, l1, l2, grad = 232, "end", 246, 254, CX - R - 10, "fadeL"
        else:
            tx, anchor, dot, l1, l2, grad = W - 232, "start", W - 246, CX + R + 10, W - 254, "fadeR"
        parts.append(
            f'<g opacity=".45">{pulse}'
            f'<text x="{tx}" y="{y + 5}" text-anchor="{anchor}" font-size="16" fill="{t["text"]}">{label}</text>'
            f'<circle cx="{dot}" cy="{y}" r="3" fill="{t["accent"]}">{grow}</circle>'
            f'<line x1="{min(l1, l2)}" y1="{y}" x2="{max(l1, l2)}" y2="{y}" stroke="url(#{grad})" stroke-width="1.2"/>'
            "</g>"
        )

    parts.append("</svg>")
    return "".join(parts)


def main():
    os.makedirs(OUT, exist_ok=True)
    for theme, name in (("dark", "bloch-dark.svg"), ("light", "bloch.svg")):
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
            fh.write(render(theme))


if __name__ == "__main__":
    main()
