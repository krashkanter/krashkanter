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

# The variant the profile actually shows; CI copies it to languages.svg.
PRIMARY = "v1"

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
            totals[name] = totals.get(name, 0) + edge["size"] * weight * DAMP.get(name, 1.0)

    ranked = sorted(totals.items(), key=lambda kv: -kv[1])[:TOP_N]
    total = sum(value for _, value in ranked)
    return [(name, value / total * 100) for name, value in ranked]


# --- drawing ----------------------------------------------------------------

W, H = 840, 240
PORTRAIT = 240
PAD_L = PORTRAIT + 36            # content starts clear of the photo
BAR_X = PAD_L
BAR_W = W - PAD_L - 30
TAGLINE_Y = 52
BAR_Y, BAR_H, GAP = 78, 18, 3
LEGEND_TOP = 136
LEGEND_STEP = 30

# Said plainly, and split so the paid work reads first and the hobby sits
# back in the dim colour rather than competing with it.
TAGLINE = ("Web / app developer", "hobby game dev")

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

        # reflection below the bar, gone within a few pixels
        '<linearGradient id="reflect" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#fff" stop-opacity="0.24"/>'
        '<stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>',
        f'<mask id="reflectmask"><rect x="{BAR_X}" y="{BAR_Y + BAR_H}" '
        f'width="{BAR_W}" height="9" fill="url(#reflect)"/></mask>',

        f'<clipPath id="card"><rect x="0" y="0" width="{W}" height="{H}" rx="14"/></clipPath>',
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
    for i, _ in enumerate(rows):
        base = palette["ramp"][i % len(palette["ramp"])]
        out.append(
            f'<linearGradient id="g{i}" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{lighten(base, light_top)}"/>'
            f'<stop offset="0.49" stop-color="{lighten(base, light_mid)}"/>'
            f'<stop offset="0.51" stop-color="{darken(base, dark_mid)}"/>'
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

        f'<rect width="{W}" height="{H}" rx="14" fill="url(#bg)"/>',
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
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="14" '
        f'fill="none" stroke="{palette["border"]}"/>',
        f'<path d="M14 0.75 H{W - 14}" stroke="{palette["bevel"]}" '
        f'stroke-opacity="{palette["bevel_opacity"]}" stroke-width="1.5" fill="none"/>',

        f'<text x="{PAD_L}" y="{TAGLINE_Y}" font-family="{SANS}" font-size="15" '
        f'letter-spacing="0.2" fill="{text}">{TAGLINE[0]}'
        f'<tspan dx="9" fill="{dim}">&#183;</tspan>'
        f'<tspan dx="9" fill="{dim}">{TAGLINE[1]}</tspan></text>',

        # trough the bar sits in
        f'<rect x="{BAR_X - 1}" y="{BAR_Y - 1}" width="{BAR_W + 2}" '
        f'height="{BAR_H + 2}" rx="4" fill="#000" fill-opacity="0.28"/>',
    ]

    segments = []
    x = float(BAR_X)
    for i, (_, pct) in enumerate(rows):
        w = max(BAR_W * pct / 100 - GAP, 2)
        segments.append((x, w))
        out += [
            f'<rect x="{x:.1f}" y="{BAR_Y}" width="{w:.1f}" height="{BAR_H}" '
            f'rx="3" fill="url(#g{i})"/>',
            # specular cap, inset so it reads as gloss rather than a second bar
            f'<rect x="{x + 1:.1f}" y="{BAR_Y + 1}" width="{max(w - 2, 1):.1f}" '
            f'height="{BAR_H / 2 - 1:.1f}" rx="2" fill="url(#spec)"/>',
        ]
        x += w + GAP

    # mirrored strip under the bar, masked to nothing within 9px
    out.append(
        f'<g mask="url(#reflectmask)" '
        f'transform="translate(0,{2 * (BAR_Y + BAR_H)}) scale(1,-1)">'
    )
    for i, (start, w) in enumerate(segments):
        out.append(
            f'<rect x="{start:.1f}" y="{BAR_Y}" width="{w:.1f}" height="{BAR_H}" '
            f'rx="3" fill="{ramp[i % len(ramp)]}"/>'
        )
    out.append("</g>")

    col_w = (BAR_W + GAP) // 2
    for i, (name, pct) in enumerate(rows):
        base = ramp[i % len(ramp)]
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
        # bare invocation renders only what the profile shows, so CI does not
        # leave the comparison variants dirty in the working tree
        variants = args or [PRIMARY]
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
