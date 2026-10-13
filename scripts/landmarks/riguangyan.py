"""Sunlight Rock (日光岩) granite hill for Gulangyu; see data/landmarks/riguangyan.json.

The game terrain is flat here, so the mass carries its own hill: a broad granite
dome, the summit boulders reported as "two rocks, one upright one leaning",
the temple cluster at the south-east foot and a hint of the Zheng Chenggong
stockade gate. Real metres in, scaled once by the caller.
"""
import math

try:
    from ._helpers import centroid
except ImportError:
    from _helpers import centroid


def _hill(b, cx, cy, scale):
    """Layered superellipse dome; ring radii shrink with height, noise-free.

    The base ellipse (about 160 x 120 m real) follows the mapped 日光岩 green
    area so canopy trees planted there end up inside the mass or at its foot,
    not cutting through mid-slope faces.
    """
    levels = [  # (z_metres, rx, ry, power)
        (0, 80, 60, 1.0), (12, 72, 54, 1.0), (28, 58, 44, 1.05),
        (44, 42, 32, 1.1), (58, 26, 20, 1.2), (70, 12, 10, 1.3),
    ]
    rings = [(cx, cy, z * scale, rx * scale, ry * scale, pw) for z, rx, ry, pw in levels]
    b.loft('granite', rings, n=26)
    # Two darker bosses at the north-west shoulder keep the silhouette from
    # reading as one clean cone.
    for ox, oy, r, h in ((-.5, -.35, 16, 9), (.48, -.52, 12, 7)):
        b.loft('granite', [(cx + ox * 40 * scale, cy + oy * 40 * scale, 34 * scale,
                            r * scale, r * .85 * scale, 1),
                           (cx + ox * 40 * scale, cy + oy * 40 * scale,
                            (34 + h) * scale, r * .4 * scale, r * .35 * scale, 1)], n=12)


def _summit(b, cx, cy, scale):
    """The upright monolith and its leaning capstone to the reported 92.7 m."""
    top = 92.7 * scale
    base = 70 * scale
    # Upright boulder: tapered loft closing to a point at the crest.
    b.loft('granite', [
        (cx - 5 * scale, cy + 3 * scale, base, 16 * scale, 13 * scale, 1.25),
        (cx - 2 * scale, cy + 1 * scale, base + 8 * scale, 13 * scale, 11 * scale, 1.2),
        (cx, cy, top - 4 * scale, 7 * scale, 6 * scale, 1.1),
        (cx, cy, top, 1.5 * scale, 1.2 * scale, 1),
    ], n=16)
    # Leaning capstone straddling the monolith shoulder.
    b.box('granite', (cx + 8 * scale, cy - 4 * scale, top - 7 * scale),
          (20 * scale, 11 * scale, 5 * scale))
    # 百米高台 viewing platform ring on the shoulder.
    b.tube('granite', (cx - 16 * scale, cy + 11 * scale, base + 2 * scale),
           (cx - 11 * scale, cy + 7 * scale, top - 14 * scale), .8 * scale, 6)


def _temple(b, cx, cy, scale):
    """日光岩寺 at the south-east foot: green-tile halls against the rock."""
    ox, oy = cx + 44 * scale, cy - 30 * scale
    for dx, dy, w, d, h in ((0, 0, 22, 12, 6.5), (-14, 10, 12, 9, 5), (13, 9, 10, 8, 4.5)):
        x, y = ox + dx * scale, oy + dy * scale
        b.footprint('concrete', [(x - w / 2 * scale, y - d / 2 * scale),
                                 (x + w / 2 * scale, y - d / 2 * scale),
                                 (x + w / 2 * scale, y + d / 2 * scale),
                                 (x - w / 2 * scale, y + d / 2 * scale),
                                 (x - w / 2 * scale, y - d / 2 * scale)],
                    0, h * scale, 1)
        b.box('greentile', (x, y, (h + .9) * scale), (w * 1.12 * scale, 2 * scale, 1.8 * scale))


def _zheng_gate(b, cx, cy, scale):
    """龙头山寨寨门: a narrow stone passage at the south-west shoulder."""
    x, y = cx - 38 * scale, cy + 20 * scale
    b.box('granite', (x, y - 3.4 * scale, 2.2 * scale), (2.4 * scale, 1.4 * scale, 4.4 * scale))
    b.box('granite', (x, y + 3.4 * scale, 2.2 * scale), (2.4 * scale, 1.4 * scale, 4.4 * scale))
    b.box('granite', (x, y, 4.6 * scale), (2.6 * scale, 8.2 * scale, 1.2 * scale))


def build(b, spec, cx, cy, scale):
    """Emit the rock mass; (cx, cy) is the projected OSM peak anchor."""
    _hill(b, cx, cy, scale)
    _summit(b, cx, cy, scale)
    _temple(b, cx, cy, scale)
    _zheng_gate(b, cx, cy, scale)
    return {'peakMeters': 92.7, 'summitGameZ': round(92.7 * scale, 2),
            'base': 'flat game terrain; hill mass carried by the model'}
