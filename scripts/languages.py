"""Render a language-mix card from the GitHub API.

The surface treatment is Aero glass, kept quiet - a gloss step across each
bar, one sheen over the panel, specular dots. Colour lives entirely in
palettes.py; this file only knows how to light whatever it is handed.

    python scripts/languages.py           # just the primary variant
    python scripts/languages.py --all     # every variant, for comparing
"""

import base64
import datetime
import json
import os
import shutil
import sys
import urllib.request

from palettes import PALETTES, get

# The variant the profile shows by default; CI copies it to languages.svg and
# it is the fallback for anyone whose theme cannot be resolved.
PRIMARY = "v1"

# Everything the README references, so a bare run refreshes all of it. The
# light card would otherwise freeze while the dark one kept updating.
PUBLISHED = ["v1", "light"]

# --- tuning -----------------------------------------------------------------

HALF_LIFE_DAYS = 240  # a repo untouched this long counts half as much
TOP_N = 6

# Sanity floor: a token that cannot see the account returns almost nothing.
MIN_REPOS = 10

# Markup and config noise: real, but not what "what does he write" means.
SKIP = {
    "HTML", "CSS", "SCSS", "Dockerfile", "Makefile", "CMake",
    "Batchfile", "Roff", "Shell", "PLpgSQL",
}

# .ipynb byte counts are dominated by base64-encoded cell outputs, which
# inflates notebooks by more than an order of magnitude against real source.
DAMP = {"Jupyter Notebook": 0.04}

# Notebooks are Python wearing a different extension; counting them apart
# splits one skill across two rows and understates both.
MERGE = {"Jupyter Notebook": "Python"}

# Each language in its own colour rather than a position on a ramp. Values are
# the official brand colour where one exists, otherwise the Linguist colour -
# the one GitHub itself paints that language with, which is what people
# actually recognise.
LANGUAGE_COLORS = {
    "TypeScript": "#3178C6",
    "JavaScript": "#F7DF1E",
    "Python": "#3776AB",
    "Dart": "#0553B1",
    "C++": "#F34B7D",
    "C": "#A8B9CC",
    "C#": "#68217A",
    "Kotlin": "#7F52FF",
    "Java": "#EA2D2E",
    "Go": "#00ADD8",
    "Rust": "#CE422B",
    "Swift": "#F05138",
    "Ruby": "#CC342D",
    "PHP": "#777BB4",
    "Lua": "#2C2D72",
    "R": "#276DC3",
    "Julia": "#9558B2",
    "Haskell": "#5E5086",
    "Scala": "#DC322F",
    "Elixir": "#4B275F",
    "Erlang": "#A90533",
    "Zig": "#F7A41D",
    "Cuda": "#76B900",
    "Svelte": "#FF3E00",
    "Vue": "#41B883",
    "Objective-C": "#438EFF",
    "Assembly": "#6E4C13",
    "Solidity": "#363636",
    "GDScript": "#478CBF",
    "HLSL": "#AACE60",
    "ShaderLab": "#222C37",
}


def language_color(name, index, palette):
    """Brand colour when the language has one, else fall back to the ramp."""
    ramp = palette["ramp"]
    return LANGUAGE_COLORS.get(name, ramp[index % len(ramp)])

OWNER = "krashkanter"

# Deliberately not `viewer`: GITHUB_TOKEN authenticates as the Actions bot, so
# `viewer` silently resolves to the bot's own repositories - this one, and
# nothing else. Naming the account means a weak token yields the public subset
# rather than a fiction.
QUERY = """
query($login: String!, $cursor: String) {
  user(login: $login) {
    repositories(first: 100, after: $cursor, ownerAffiliations: OWNER,
                 isFork: false, orderBy: {field: PUSHED_AT, direction: DESC}) {
      pageInfo { hasNextPage endCursor }
      nodes {
        pushedAt
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name } }
        }
      }
    }
  }
}
"""


# --- colour -----------------------------------------------------------------

def _mix(hex_color, target, amount):
    rgb = tuple(int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    out = tuple(round(c + (t - c) * amount) for c, t in zip(rgb, target))
    return "#%02x%02x%02x" % out


def lighten(hex_color, amount):
    return _mix(hex_color, (255, 255, 255), amount)


def darken(hex_color, amount):
    return _mix(hex_color, (0, 0, 0), amount)


# --- data -------------------------------------------------------------------

def fetch(token):
    repos, cursor = [], None
    while True:
        body = json.dumps({
            "query": QUERY,
            "variables": {"login": OWNER, "cursor": cursor},
        })
        req = urllib.request.Request(
            "https://api.github.com/graphql",
            data=body.encode(),
            headers={
                "Authorization": f"bearer {token}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req) as resp:
            payload = json.load(resp)
        if "errors" in payload:
            raise SystemExit(payload["errors"])
        page = payload["data"]["user"]["repositories"]
        repos += page["nodes"]
        if not page["pageInfo"]["hasNextPage"]:
            return repos
        cursor = page["pageInfo"]["endCursor"]


def shares(repos):
    now = datetime.datetime.now(datetime.timezone.utc)
    totals = {}
    for repo in repos:
        pushed = datetime.datetime.fromisoformat(
            repo["pushedAt"].replace("Z", "+00:00")
        )
        weight = 0.5 ** ((now - pushed).days / HALF_LIFE_DAYS)
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            if name in SKIP:
                continue
            value = edge["size"] * weight * DAMP.get(name, 1.0)
            name = MERGE.get(name, name)
            totals[name] = totals.get(name, 0) + value

    ranked = sorted(totals.items(), key=lambda kv: -kv[1])[:TOP_N]
    total = sum(value for _, value in ranked)
    return [(name, value / total * 100) for name, value in ranked]


# --- drawing ----------------------------------------------------------------

W, H = 840, 240
PORTRAIT = 240
PAD_L = PORTRAIT + 36            # content starts clear of the photo
BAR_X = PAD_L
BAR_W = W - PAD_L - 30
BAR_Y, BAR_H = 64, 18            # no heading, so the block is centred instead
BAR_RADIUS = 2                   # Aero troughs are barely rounded at all
CARD_RADIUS = 4                  # same as the link buttons, so they read as a set
LEGEND_TOP = 122
LEGEND_STEP = 32

# Named, never embedded - the viewer's own copy resolves it, so there is no
# font licence in play. Segoe UI only exists on Windows; Noto Sans catches
# everyone else.
SANS = "'Segoe UI','Noto Sans',ui-sans-serif,system-ui,sans-serif"

# a low, uneven skyline for variants that light the bottom edge
SKYLINE = (
    f"M0 {H} L0 218 L64 212 L118 220 L176 209 L242 219 L318 207 L402 218 "
    f"L486 210 L566 220 L648 211 L724 221 L792 213 L{W} 219 L{W} {H} Z"
)


def _defs(palette, rows):
    """Gradients and masks. One gloss gradient per bar segment."""
    sheen = palette["sheen"]
    spec = palette["spec"]

    out = [
        '<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{palette["bg_top"]}"/>'
        f'<stop offset="1" stop-color="{palette["bg_bottom"]}"/></linearGradient>',

        # panel sheen: light pools at the top and dies out by the midline
        '<linearGradient id="sheen" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{sheen}" stop-opacity="0.075"/>'
        f'<stop offset="0.55" stop-color="{sheen}" stop-opacity="0.012"/>'
        f'<stop offset="1" stop-color="{sheen}" stop-opacity="0"/></linearGradient>',

        # specular cap sitting on the top half of every glossy element
        '<linearGradient id="spec" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{spec}" stop-opacity="{palette["spec_hi"]}"/>'
        f'<stop offset="1" stop-color="{spec}" stop-opacity="{palette["spec_lo"]}"/>'
        "</linearGradient>",

        # the photo dissolves into the card gradient instead of ending on an edge
        '<linearGradient id="fade" x1="0" y1="0" x2="1" y2="0">'
        '<stop offset="0" stop-color="#fff" stop-opacity="0"/>'
        '<stop offset="1" stop-color="#fff" stop-opacity="1"/></linearGradient>',
        f'<mask id="fademask"><rect x="{PORTRAIT - 72}" y="0" width="72" '
        f'height="{H}" fill="url(#fade)"/></mask>',

        # reflection below the bar, gone within a few pixels. White on a dark
        # panel, ink on a pale one - a white reflection on paper is nothing.
        '<linearGradient id="reflect" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{palette["reflect"][0]}" '
        f'stop-opacity="{palette["reflect"][1]}"/>'
        f'<stop offset="1" stop-color="{palette["reflect"][0]}" '
        'stop-opacity="0"/></linearGradient>',
        f'<mask id="reflectmask"><rect x="{BAR_X}" y="{BAR_Y + BAR_H}" '
        f'width="{BAR_W}" height="9" fill="url(#reflect)"/></mask>',

        f'<clipPath id="card"><rect x="0" y="0" width="{W}" height="{H}" rx="{CARD_RADIUS}"/></clipPath>',
        # top-edge bevel as a stroke that follows the corners. Drawn as a
        # straight line it stops dead where the curve begins, leaving a stub.
        '<linearGradient id="bevelfade" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{palette["bevel"]}" '
        f'stop-opacity="{palette["bevel_opacity"]}"/>'
        f'<stop offset="0.14" stop-color="{palette["bevel"]}" '
        'stop-opacity="0"/></linearGradient>',
        f'<clipPath id="barclip"><rect x="{BAR_X}" y="{BAR_Y}" width="{BAR_W}" '
        f'height="{BAR_H}" rx="{BAR_RADIUS}"/></clipPath>',

        # shading held tight against each section's vertical edges
        '<linearGradient id="edge" x1="0" y1="0" x2="1" y2="0">'
        '<stop offset="0" stop-color="#000" stop-opacity="0.30"/>'
        '<stop offset="0.09" stop-color="#000" stop-opacity="0"/>'
        '<stop offset="0.91" stop-color="#000" stop-opacity="0"/>'
        '<stop offset="1" stop-color="#000" stop-opacity="0.30"/></linearGradient>',
    ]

    horizon = palette["horizon"]
    if horizon:
        out.append(
            '<radialGradient id="glow" cx="0.62" cy="1" r="0.85">'
            f'<stop offset="0" stop-color="{horizon["glow"]}" '
            f'stop-opacity="{horizon["glow_opacity"]}"/>'
            f'<stop offset="0.45" stop-color="{horizon["glow"]}" stop-opacity="0.09"/>'
            f'<stop offset="1" stop-color="{horizon["glow"]}" stop-opacity="0"/>'
            "</radialGradient>"
        )

    light_top, light_mid, dark_mid, dark_bot = palette["gloss"]
    for i, (name, _) in enumerate(rows):
        base = language_color(name, i, palette)
        out.append(
            f'<linearGradient id="g{i}" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{lighten(base, light_top)}"/>'
            f'<stop offset="0.45" stop-color="{lighten(base, light_mid)}"/>'
            f'<stop offset="0.45" stop-color="{darken(base, dark_mid)}"/>'
            f'<stop offset="1" stop-color="{darken(base, dark_bot)}"/>'
            "</linearGradient>"
        )
    return out


def render(rows, variant):
    palette = get(variant)
    ramp = palette["ramp"]
    text, dim = palette["text"], palette["dim"]
    horizon = palette["horizon"]

    with open(f"assets/portrait-{variant}.png", "rb") as fh:
        portrait_b64 = base64.b64encode(fh.read()).decode()
    with open(f"assets/backdrop-{variant}.png", "rb") as fh:
        backdrop_b64 = base64.b64encode(fh.read()).decode()

    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        'role="img" aria-label="Language mix">',
        "<defs>",
        *_defs(palette, rows),
        # defined once, drawn twice - the second pass is what feathers the
        # portrait's right edge back into the field
        f'<image id="bd" x="0" y="0" width="{W}" height="{H}" '
        f'xlink:href="data:image/png;base64,{backdrop_b64}"/>',
        "</defs>",

        f'<rect width="{W}" height="{H}" rx="{CARD_RADIUS}" fill="url(#bg)"/>',
        '<g clip-path="url(#card)">',
        '<use xlink:href="#bd"/>',
    ]

    if horizon:
        out.append(f'<rect width="{W}" height="{H}" fill="url(#glow)"/>')

    out += [
        f'<image x="0" y="0" width="{PORTRAIT}" height="{PORTRAIT}" '
        f'xlink:href="data:image/png;base64,{portrait_b64}"/>',
        '<use xlink:href="#bd" mask="url(#fademask)"/>',
    ]

    if horizon:
        out.append(f'<path d="{SKYLINE}" fill="{horizon["band"]}" fill-opacity="0.92"/>')

    out += [
        # glass over the whole panel, photo included
        f'<rect width="{W}" height="{H}" fill="url(#sheen)"/>',
        "</g>",

        # bevel: bright hairline on top, plain border around
        # a 1px stroke at 0.5 inset needs radius R - 0.5 to sit flush inside a
        # clip of radius R; at R itself the fill pokes past it at each corner
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" '
        f'rx="{CARD_RADIUS - 0.5}" fill="none" stroke="{palette["border"]}"/>',
        f'<rect x="1.25" y="1.25" width="{W - 2.5}" height="{H - 2.5}" '
        f'rx="{CARD_RADIUS - 1.25}" fill="none" stroke="url(#bevelfade)" '
        'stroke-width="1.5"/>',

        f'<g clip-path="url(#barclip)">',
    ]

    # Boundaries are accumulated rather than summed per-segment, so the widths
    # are exact and the last one lands flush on the right edge. The shares
    # always total 100%, so the trough is never visible - it is a frame, not a
    # track, which is why it carries no inset and almost no radius.
    segments = []
    edge = BAR_X
    total = 0.0
    for i, (_, pct) in enumerate(rows):
        total += pct
        end = BAR_X + BAR_W * total / 100
        width = end - edge
        segments.append((edge, width))
        out += [
            f'<rect x="{edge:.2f}" y="{BAR_Y}" width="{width:.2f}" '
            f'height="{BAR_H}" fill="url(#g{i})"/>',
            # each section darkens into its own left and right edges; with no
            # gap between them this is what keeps the divisions legible
            f'<rect x="{edge:.2f}" y="{BAR_Y}" width="{width:.2f}" '
            f'height="{BAR_H}" fill="url(#edge)"/>',
        ]
        edge = end

    out += [
        "</g>",
        # the frame, drawn over the fill so the corners stay clean
        f'<rect x="{BAR_X + 0.5}" y="{BAR_Y + 0.5}" width="{BAR_W - 1}" '
        f'height="{BAR_H - 1}" rx="{BAR_RADIUS - 0.5}" fill="none" '
        f'stroke="{darken(palette["border"], 0.30)}"/>',
    ]

    # mirrored strip under the bar, masked to nothing within 9px
    out.append(
        f'<g mask="url(#reflectmask)" '
        f'transform="translate(0,{2 * (BAR_Y + BAR_H)}) scale(1,-1)">'
    )
    for i, (start, w) in enumerate(segments):
        out.append(
            f'<rect x="{start:.2f}" y="{BAR_Y}" width="{w:.2f}" height="{BAR_H}" '
            f'fill="{language_color(rows[i][0], i, palette)}"/>'
        )
    out.append("</g>")

    col_w = BAR_W // 2
    for i, (name, pct) in enumerate(rows):
        base = language_color(name, i, palette)
        cx = PAD_L + 4 + (i % 2) * col_w
        cy = LEGEND_TOP + (i // 2) * LEGEND_STEP
        out += [
            f'<circle cx="{cx}" cy="{cy - 4}" r="4.5" fill="{darken(base, 0.25)}"/>',
            f'<circle cx="{cx}" cy="{cy - 4}" r="4.5" fill="url(#g{i})"/>',
            # highlight bead, upper-left like a lit sphere
            f'<ellipse cx="{cx - 0.6}" cy="{cy - 6}" rx="2.4" ry="1.5" '
            'fill="#fff" fill-opacity="0.45"/>',
            f'<text x="{cx + 15}" y="{cy}" fill="{text}" font-size="13" '
            f'font-family="{SANS}">{name}</text>',
            f'<text x="{cx + col_w - 26}" y="{cy}" fill="{dim}" font-size="12" '
            f'text-anchor="end" font-family="{SANS}">{pct:.0f}%</text>',
        ]

    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["--all"]:
        variants = sorted(PALETTES)
    else:
        # bare invocation renders only what the README references, so CI does
        # not leave the comparison variants dirty in the working tree
        variants = args or PUBLISHED
    repos = fetch(os.environ["GH_TOKEN"])
    # A token that cannot see the account returns a near-empty set rather than
    # an error. Refuse to render that instead of committing a fiction.
    if len(repos) < MIN_REPOS:
        raise SystemExit(
            f"only {len(repos)} repos visible to this token; expected at least "
            f"{MIN_REPOS}. Refusing to render. Is STATS_TOKEN set?"
        )
    rows = shares(repos)

    for variant in variants:
        path = f"assets/languages-{variant}.svg"
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(render(rows, variant) + "\n")
        print(f"wrote {path}")

    if PRIMARY in variants:
        shutil.copyfile(f"assets/languages-{PRIMARY}.svg", "assets/languages.svg")
        print(f"wrote assets/languages.svg (from {PRIMARY})")
