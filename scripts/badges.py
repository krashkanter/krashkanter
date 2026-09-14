"""Render the contact links as Aero buttons.

A link has to be clickable, and an SVG rendered as <img> cannot carry one -
so each badge is its own file, wrapped in an anchor in the README.

The chassis is plain chrome, no photograph: a solid base under a specular
that stops dead at the midline, a darker lower half that lifts again at the
bottom edge, and a dark outer border with a lighter one inset a pixel inside
it. Only the icon carries the palette, filled with the same blues the bars
use.

    python scripts/badges.py              # everything the README references
    python scripts/badges.py --all
"""

import sys

from languages import PUBLISHED, SANS, darken, lighten
from palettes import PALETTES, get

H = 34          # Aero buttons were short; 40 reads as a modern pill
RADIUS = 4      # tight, not rounded - and the same as the card
PAD_X = 12
ICON = 15
GAP = 8

# simple-icons paths, 24x24 viewBox
ICONS = {
    "linkedin": (
        "M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0"
        "-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637"
        "-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c"
        "-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 "
        "2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3."
        "555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23."
        "227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 "
        "23.2 0 22.222 0h.003z"
    ),
    "email": (
        "M24 5.457v13.909c0 .904-.732 1.636-1.636 1.636h-3.819V11.73L12 16.64l"
        "-6.545-4.91v9.273H1.636A1.636 1.636 0 0 1 0 19.366V5.457c0-2.023 2.309"
        "-3.178 3.927-1.964L5.455 4.64 12 9.548l6.545-4.91 1.528-1.145C21.69 2."
        "28 24 3.434 24 5.457z"
    ),
}

BADGES = [
    ("linkedin", "LinkedIn", 104),
    ("email", "Email", 86),
]


def chassis(palette):
    """The button's own colour: lifted off a dark panel, sunk into a pale one."""
    if palette["light"]:
        return darken(palette["bg_top"], 0.06)
    return lighten(palette["bg_bottom"], 0.16)


def render(variant, key, label, width):
    palette = get(variant)
    ramp = palette["ramp"]
    base = chassis(palette)

    # the icon runs the ramp's own span, so the buttons and the bars are
    # visibly the same palette rather than merely similar
    lo, hi = ramp[1], ramp[4]

    scale = ICON / 24
    icon_x, icon_y = PAD_X, (H - ICON) / 2

    return "\n".join([
        '<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{H}" viewBox="0 0 {width} {H}" '
        f'role="img" aria-label="{label}">',
        "<defs>",
        f'<clipPath id="r"><rect width="{width}" height="{H}" rx="{RADIUS}"/></clipPath>',
        f'<linearGradient id="ic" x1="0" y1="0" x2="0.6" y2="1">'
        f'<stop offset="0" stop-color="{lighten(hi, 0.12)}"/>'
        f'<stop offset="1" stop-color="{darken(lo, 0.08)}"/></linearGradient>',
        # the Aero step: specular on the top half, cut dead at the midline
        f'<linearGradient id="gloss" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{palette["spec"]}" stop-opacity="0.26"/>'
        f'<stop offset="1" stop-color="{palette["spec"]}" stop-opacity="0.05"/>'
        "</linearGradient>",
        # below the step it darkens, then lifts again at the bottom edge so the
        # button reads as a lit solid rather than fading into a hole
        '<linearGradient id="under" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#000" stop-opacity="0.20"/>'
        '<stop offset="0.75" stop-color="#000" stop-opacity="0.10"/>'
        f'<stop offset="1" stop-color="{palette["sheen"]}" stop-opacity="0.05"/>'
        "</linearGradient>",
        "</defs>",
        '<g clip-path="url(#r)">',
        f'<rect width="{width}" height="{H}" fill="{base}"/>',
        f'<rect y="{H / 2}" width="{width}" height="{H / 2}" fill="url(#under)"/>',
        f'<rect width="{width}" height="{H / 2}" fill="url(#gloss)"/>',
        "</g>",
        # double border: dark outer, light inner, one pixel apart. Each radius
        # is reduced by its own inset so the curves stay concentric with the
        # clip - otherwise the corners show a sliver of fill.
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{H - 1}" '
        f'rx="{RADIUS - 0.5}" fill="none" stroke="{darken(palette["border"], 0.35)}"/>',
        f'<rect x="1.5" y="1.5" width="{width - 3}" height="{H - 3}" '
        f'rx="{RADIUS - 1.5}" fill="none" stroke="{palette["bevel"]}" '
        'stroke-opacity="0.13"/>',
        f'<g transform="translate({icon_x},{icon_y}) scale({scale:.4f})">'
        f'<path d="{ICONS[key]}" fill="url(#ic)"/></g>',
        f'<text x="{PAD_X + ICON + GAP}" y="{H / 2 + 4.5:.0f}" '
        f'font-family="{SANS}" font-size="13" letter-spacing="0.2" '
        f'fill="{palette["text"]}">{label}</text>',
        "</svg>",
    ])


def build(variant):
    for key, label, width in BADGES:
        svg = render(variant, key, label, width) + "\n"
        path = f"assets/{key}-{variant}.svg"
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(svg)
        print(f"wrote {path}")

        # the README links to the unsuffixed name, so switching the default
        # variant does not mean editing markdown
        if variant == PUBLISHED[0]:
            with open(f"assets/{key}.svg", "w", encoding="utf-8") as fh:
                fh.write(svg)
            print(f"wrote assets/{key}.svg (from {variant})")


if __name__ == "__main__":
    args = sys.argv[1:]
    for name in (sorted(PALETTES) if args == ["--all"] else args or PUBLISHED):
        build(name)
