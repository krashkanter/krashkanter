"""Palette variants for the language card.

Each variant owns everything colour: the data ramp, the panel, the Aero gloss
constants and the four dither stops for the portrait. The portrait's darkest
stop must equal the panel's top colour, or the photo reads as a square patch
instead of sitting flush.
"""

PALETTES = {
    # v1 - the avatar's sky rather than its treeline
    "v1": {
        "ramp": ["#14508f", "#1a67ad", "#2380c9", "#3f9bdc", "#6fb8ea", "#a6d5f5"],
        "bg_top": "#0a1626",
        "bg_bottom": "#0f2036",
        "border": "#1d3a5c",
        "text": "#cfdcea",
        "dim": "#5c7a9c",
        "sheen": "#d8e8ff",
        "bevel": "#c6dcf5",
        "bevel_opacity": "0.16",
        "spec": "#ffffff",
        "spec_hi": "0.30",
        "spec_lo": "0.05",
        "gloss": (0.34, 0.08, 0.22, 0.04),
        "portrait": [(10, 22, 38), (29, 58, 96), (63, 112, 168), (150, 190, 232)],
        "portrait_brightness": 0.86,
        "backdrop_darken": 0.40,
        "backdrop_stops": None,
        "light": False,
        "reflect": ("#fff", "0.24"),
        "horizon": None,
    },

    # v2 - tropical sunset, everything warm
    "v2": {
        "ramp": ["#6d3a7a", "#9c3f72", "#c4485c", "#e0662f", "#f08c2a", "#f6b93f"],
        "bg_top": "#1a1024",
        "bg_bottom": "#2a1733",
        "border": "#4a2b50",
        "text": "#f2e0e4",
        "dim": "#a57a8c",
        "sheen": "#ffd9c0",
        "bevel": "#ffc9a6",
        "bevel_opacity": "0.18",
        "spec": "#fff3e6",
        "spec_hi": "0.20",
        "spec_lo": "0.03",
        "gloss": (0.22, 0.04, 0.24, 0.04),
        "portrait": [(26, 16, 36), (78, 38, 74), (158, 68, 68), (232, 150, 78)],
        "portrait_brightness": 0.80,
        "backdrop_darken": 0.58,
        "backdrop_stops": None,
        "light": False,
        "reflect": ("#fff", "0.24"),
        "horizon": None,
    },

    # v3 - near-black ground lit by a low orange/gold horizon, with the photo
    # and the data both held in the cooler alpine accents so they read against
    # the warmth rather than dissolving into it.
    "v3": {
        "ramp": ["#0e6f9c", "#12908f", "#2f9b74", "#58a35f", "#83ac5c", "#a8b46b"],
        "bg_top": "#080a09",
        "bg_bottom": "#140f0a",
        "border": "#3a2a18",
        "text": "#e8e2d6",
        "dim": "#8a7a63",
        "sheen": "#ffc46a",
        "bevel": "#ffb347",
        "bevel_opacity": "0.14",
        "spec": "#ffffff",
        "spec_hi": "0.28",
        "spec_lo": "0.05",
        "gloss": (0.32, 0.07, 0.24, 0.04),
        "portrait": [(8, 10, 9), (29, 74, 68), (63, 138, 99), (159, 184, 122)],
        "portrait_brightness": 0.86,
        "backdrop_darken": 0.66,
        "backdrop_stops": None,
        "light": False,
        "reflect": ("#fff", "0.24"),
        # warm light pooling at the bottom edge, with a black skyline over it
        "horizon": {"glow": "#ff9836", "glow_opacity": "0.30", "band": "#05060a"},
    },

    # light - the same scene printed rather than lit. Every layer inverts: the
    # envelope runs white-at-the-left instead of black, the portrait becomes
    # dark ink on paper, and the ramp deepens so the bars hold against it.
    "light": {
        "ramp": ["#0a3f76", "#0d5493", "#126aae", "#2181c6", "#3d97d6", "#5faae0"],
        "bg_top": "#f1f5fa",
        "bg_bottom": "#e3ebf4",
        "border": "#b4c5d8",
        "text": "#16232f",
        "dim": "#5f7286",
        "sheen": "#ffffff",
        "bevel": "#ffffff",
        "bevel_opacity": "0.55",
        "spec": "#ffffff",
        "spec_hi": "0.34",
        "spec_lo": "0.06",
        "gloss": (0.30, 0.06, 0.24, 0.04),
        # shadows land on ink, highlights on paper
        "portrait": [(38, 56, 78), (92, 122, 156), (160, 188, 214), (236, 242, 248)],
        "portrait_brightness": 0.98,
        "backdrop_darken": 0.0,
        # stated outright rather than derived: on paper the field has to stay
        # inside a narrow, pale band or the legend stops reading
        "backdrop_stops": [(170, 195, 220), (202, 218, 234), (226, 236, 245), (245, 249, 252)],
        "light": True,
        # a white reflection is invisible on paper
        "reflect": ("#16232f", "0.16"),
        "horizon": None,
    },
}


def get(name):
    try:
        return PALETTES[name]
    except KeyError:
        raise SystemExit(f"unknown variant {name!r}; have {sorted(PALETTES)}")
