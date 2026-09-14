"""Palette variants for the language card.

Each variant owns everything colour: the data ramp, the panel, the Aero gloss
constants and the four dither stops for the portrait. The portrait's darkest
stop must equal the panel's top colour, or the photo reads as a square patch
instead of sitting flush.
"""

PALETTES = {
    # v1 - alpine, sampled from the old avatar
    "v1": {
        "ramp": ["#0b6e8c", "#0f8fa4", "#17b0a8", "#3fc9a0", "#79dba6", "#b6e9bd"],
        "bg_top": "#0a201b",
        "bg_bottom": "#0f2d25",
        "border": "#1d4536",
        "text": "#cfe0d6",
        "dim": "#5c8279",
        "sheen": "#d8f2e2",
        "bevel": "#c6ecd6",
        "bevel_opacity": "0.16",
        "spec": "#ffffff",
        "spec_hi": "0.30",
        "spec_lo": "0.05",
        "gloss": (0.34, 0.08, 0.22, 0.04),
        "portrait": [(10, 32, 27), (29, 74, 68), (63, 138, 99), (159, 184, 122)],
        "portrait_brightness": 0.86,
        "backdrop_darken": 0.40,
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
        # warm light pooling at the bottom edge, with a black skyline over it
        "horizon": {"glow": "#ff9836", "glow_opacity": "0.30", "band": "#05060a"},
    },
}


def get(name):
    try:
        return PALETTES[name]
    except KeyError:
        raise SystemExit(f"unknown variant {name!r}; have {sorted(PALETTES)}")
