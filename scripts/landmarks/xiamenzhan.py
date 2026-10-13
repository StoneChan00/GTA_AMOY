"""Xiamen Railway Station (厦门站, rebuilt 2012-16); see data/landmarks/xiamenzhan.json.

Two station bars north and south of the tracks with a white arched roof
spanning between them — the reported 31 m crown and 67 m truss span read as
one grand saddle over the platforms. The OSM station node anchors the plan;
the rails run east-west so the long bars sit along local x.
"""
import math

try:
    from ._helpers import arch_ribs
except ImportError:
    from _helpers import arch_ribs


def build(b, spec, cx, cy, scale):
    """(cx, cy) is the projected OSM railway-station node."""
    dims = spec['dims']
    length = dims['widthEastWestMeters']['value']      # 145 m along the rails
    span = dims['lengthNorthSouthMeters']['value'] * .42  # bars + roof throat
    crown = dims['archTopMeters']['value']             # 31 m
    bar_w, bar_h = 34, 18
    # North bar (厦禾路 side) and south bar (站南路 side), both glass-fronted.
    for side in (-1, 1):
        y = side * span / 2
        ring = [(cx - length / 2 * scale, cy + (y - bar_w / 2) * scale),
                (cx + length / 2 * scale, cy + (y - bar_w / 2) * scale),
                (cx + length / 2 * scale, cy + (y + bar_w / 2) * scale),
                (cx - length / 2 * scale, cy + (y + bar_w / 2) * scale),
                (cx - length / 2 * scale, cy + (y - bar_w / 2) * scale)]
        b.footprint('concrete', ring, 0, bar_h * scale, 1)
        b.footprint('darkglass', ring, 1.2 * scale, (bar_h - 1.4) * scale, .994)
        b.box('whiteroof', (cx, cy + y * scale, (bar_h + 1.6) * scale),
              (length * 1.04 * scale, bar_w * 1.08 * scale, 3.2 * scale))
    # The grand roof: arc ribs springing between the bars, crest along the rails.
    ribs = []
    for i in range(20):
        x = (i / 19 - .5) * length * .96
        crest = crown - 4 * (1 - (2 * i / 19 - 1) ** 2)
        rib = [(x, y, 16 + (crest - 16) * (1 - (y / (span / 2)) ** 2))
               for y in [(-.5 + j / 8) * span for j in range(9)]]
        ribs.append([(cx + p[0] * scale, cy + p[1] * scale, p[2] * scale) for p in rib])
    arch_ribs(b, 'whiteroof', ribs, cap_ends=True)
    # V-column hints under the north springing.
    for i in range(7):
        x = (i / 6 - .5) * length * .8
        b.tube('steel', (cx + x * scale, cy - span / 2 * scale, 0),
               (cx + x * scale, cy - span * .18 * scale, 16 * scale), .8 * scale, 6)
    return {'bars': 2, 'crownMeters': crown, 'spanModeledMeters': round(span, 1)}
