"""Ordered-dither the source photo twice per palette.

Two tiles come out of one image:

  portrait-<v>.png   the sharp head-and-shoulders crop, 232px square
  backdrop-<v>.png   the same photo blown up, blurred past recognition and
                     dithered into a darkened copy of the same four stops,
                     so the whole panel is pattern instead of a flat ramp

Both go through the same Bayer 8x8 pass, so the dot grids line up and the
portrait dissolves into the backdrop rather than sitting on top of it.

Run this locally, not in CI: the source photo is gitignored on purpose, so
only the dithered tiles are ever published.

    python scripts/portrait.py            # every variant
    python scripts/portrait.py v1         # just one
"""

import sys

from PIL import Image, ImageChops, ImageEnhance, ImageFilter, ImageOps

from palettes import PALETTES, get

SRC = "assets/source-portrait.jpg"

CROP = (150, 20, 1015, 885)  # head and shoulders out of the 1080 square
SIZE = 232

CARD_W, CARD_H = 840, 240
BLUR = 34  # enough that no feature survives, only tone

# The backdrop is driven left-to-right: pitch black behind the photo, climbing
# to the palette's lightest stop at the right edge. Above 1.0 the black holds
# longer before the ramp starts to lift.
LIGHT_GAMMA = 1.15

# How much the blurred photo is allowed to swing the ramp. The ramp sets the
# envelope; this only mottles it. Letting the photo drive luminance outright
# just reproduces its own dark right-hand side, which pulls the light back
# into the middle of the card.
PHOTO_FLOOR = 168  # of 255

# The photo sits on the left, so it has to fall into the black as well or the
# card still reads bright-left. Floor is how much survives at the very edge;
# the exponent below 1 makes the recovery fast, so only the outer strip goes.
PORTRAIT_FLOOR = 0.28
PORTRAIT_GAMMA = 0.5

BAYER8 = [
    [0, 32, 8, 40, 2, 34, 10, 42],
    [48, 16, 56, 24, 50, 18, 58, 26],
    [12, 44, 4, 36, 14, 46, 6, 38],
    [60, 28, 52, 20, 62, 30, 54, 22],
    [3, 35, 11, 43, 1, 33, 9, 41],
    [51, 19, 59, 27, 49, 17, 57, 25],
    [15, 47, 7, 39, 13, 45, 5, 37],
    [63, 31, 55, 23, 61, 29, 53, 21],
]


def bayer(gray, stops):
    """Ordered-dither a greyscale image into an ordered list of RGB stops."""
    w, h = gray.size
    src = gray.load()
    out = Image.new("RGB", (w, h))
    dst = out.load()
    levels = len(stops) - 1

    for y in range(h):
        row = BAYER8[y % 8]
        for x in range(w):
            value = src[x, y] / 255 * levels
            base = int(value)
            threshold = (row[x % 8] + 0.5) / 64
            level = base + (1 if (value - base) > threshold else 0)
            dst[x, y] = stops[min(level, levels)]
    return out


def save(img, path, colors=4):
    img.convert("P", palette=Image.ADAPTIVE, colors=colors).save(path, optimize=True)
    print(f"wrote {path}")


def resample(stops, count):
    """Walk the stop sequence and pick `count` evenly spaced colours along it."""
    last = len(stops) - 1
    out = []
    for i in range(count):
        t = i / (count - 1) * last
        lo = int(t)
        hi = min(lo + 1, last)
        f = t - lo
        out.append(tuple(
            round(stops[lo][c] + (stops[hi][c] - stops[lo][c]) * f)
            for c in range(3)
        ))
    return out


def portrait(variant, palette):
    img = Image.open(SRC).convert("L").crop(CROP).resize((SIZE, SIZE), Image.LANCZOS)
    img = ImageOps.autocontrast(img, cutoff=2)
    img = ImageEnhance.Contrast(img).enhance(1.18)
    img = ImageEnhance.Brightness(img).enhance(palette["portrait_brightness"])
    img = envelope(img, portrait_ramp(), palette["light"])
    save(bayer(img, palette["portrait"]), f"assets/portrait-{variant}.png")


def envelope(img, ramp, light):
    """Apply a horizontal falloff, toward black on dark and white on light.

    Multiplying is what drives a value to black; on a pale panel that is the
    wrong direction entirely, so the light variants screen against the
    inverted ramp and run to paper instead.
    """
    if light:
        return ImageChops.screen(img, ImageOps.invert(ramp))
    return ImageChops.multiply(img, ramp)


def portrait_ramp():
    """Left-to-right ramp across the portrait, never reaching full black."""
    row = Image.new("L", (SIZE, 1))
    row.putdata([
        round(255 * (PORTRAIT_FLOOR + (1 - PORTRAIT_FLOOR)
                     * (x / (SIZE - 1)) ** PORTRAIT_GAMMA))
        for x in range(SIZE)
    ])
    return row.resize((SIZE, SIZE))


def light_ramp():
    """Left-to-right luminance ramp, black at x=0, full at the right edge."""
    row = Image.new("L", (CARD_W, 1))
    row.putdata([
        round(255 * (x / (CARD_W - 1)) ** LIGHT_GAMMA) for x in range(CARD_W)
    ])
    return row.resize((CARD_W, CARD_H))


def falling_ramp(floor):
    """Paper at the left, easing down to `floor` at the right.

    On a light panel the falloff is carried by ink density rather than by
    colour, so the envelope descends instead of climbing.
    """
    span = 255 - floor
    row = Image.new("L", (CARD_W, 1))
    row.putdata([
        round(255 - span * (x / (CARD_W - 1)) ** LIGHT_GAMMA)
        for x in range(CARD_W)
    ])
    return row.resize((CARD_W, CARD_H))


def backdrop(variant, palette):
    # Same four hues, pulled down far enough that legend text still reads
    # against them. Keeping every stop is what makes the field shimmer - but
    # the darkest one goes to true black so the left edge bottoms out.
    if palette["backdrop_stops"]:
        stops = list(palette["backdrop_stops"])
    else:
        factor = 1 - palette["backdrop_darken"]
        stops = [tuple(round(channel * factor) for channel in stop)
                 for stop in palette["portrait"]]
        stops[0] = (0, 0, 0)
    stops = resample(stops, palette["backdrop_levels"])

    img = Image.open(SRC).convert("L")
    img = ImageOps.fit(img, (CARD_W, CARD_H), Image.LANCZOS, centering=(0.5, 0.42))
    img = img.filter(ImageFilter.GaussianBlur(BLUR))
    # the blur flattens contrast; stretch it back so all four stops get used
    img = ImageOps.autocontrast(img, cutoff=1)
    # squash the photo into [PHOTO_FLOOR, 255] so it can only mottle the ramp
    span = 255 - PHOTO_FLOOR
    img = img.point(lambda v: PHOTO_FLOOR + round(span * v / 255))
    if palette["light"]:
        img = ImageChops.multiply(falling_ramp(palette["backdrop_floor"]), img)
    else:
        img = ImageChops.multiply(light_ramp(), img)
    save(bayer(img, stops), f"assets/backdrop-{variant}.png", colors=8)


def build(variant):
    palette = get(variant)
    portrait(variant, palette)
    backdrop(variant, palette)


if __name__ == "__main__":
    for name in sys.argv[1:] or sorted(PALETTES):
        build(name)
