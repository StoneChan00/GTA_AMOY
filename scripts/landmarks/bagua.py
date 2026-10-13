"""Gulangyu Bagua Building (八卦楼, organ museum); see data/landmarks/bagua.json.

Cross-shaped three-storey body on a granite damp-course, octagonal drum and the
red dome after the Dome of the Rock. The OSM ring anchors plan and orientation;
heights are the reported 25.7 m total with a 10 m dome. Real metres in, scaled
once by the caller.
"""
import math

try:
    from ._helpers import centroid, bbox, scaled, closed
except ImportError:
    from _helpers import centroid, bbox, scaled, closed


def _cross_arms(b, ring, scale):
    """Four corner pavilions (耳房) on the cross arms' ends."""
    x0, y0, x1, y1 = bbox(ring)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    span_x, span_y = (x1 - x0) * .30, (y1 - y0) * .30
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        px, py = cx + dx * span_x * 2, cy + dy * span_y * 2
        w, d = (span_x * .55, span_y * .42) if dx else (span_x * .42, span_y * .55)
        b.footprint('stone', closed([(px - w, py - d), (px + w, py - d), (px + w, py + d), (px - w, py + d), (px - w, py - d)]),
                    2.4 * scale, 11.5 * scale, 1)
        b.box('orangetile', (px, py, 13.2 * scale), (w * 2 * 1.1, d * 2 * 1.1, 2.4 * scale))


def build(b, spec, ring, scale):
    """Emit the building; ring is the projected OSM footprint (game metres)."""
    total, dome = 25.7, 10
    body_top = total - dome          # 15.7 m body including the drum base
    x0, y0, x1, y1 = bbox(ring)
    cx, cy = centroid(ring)
    span = min(x1 - x0, y1 - y0) / 2
    # Granite damp-course plinth, slightly proud of the main ring.
    b.footprint('stone', ring, 0, 2.4 * scale, 1.045)
    # Three-storey main body with a band of glazing per floor.
    b.footprint('stone', ring, 2.4 * scale, body_top * .82, .985)
    for z in (5.6, 10.2, 14.0):
        b.footprint('darkglass', ring, z * scale, (z + 1.4) * scale, .995)
    b.footprint('stone', ring, body_top * .82, body_top * scale, .968)
    _cross_arms(b, ring, scale)
    # Octagonal platform + drum, then the eight-ribbed red dome.
    drum_r = span * .52
    b.loft('stone', [(cx, cy, body_top * scale, drum_r * 1.16, drum_r * 1.16, 1),
                     (cx, cy, (body_top + 1.6) * scale, drum_r, drum_r, 1)], n=8)
    dome_r = drum_r * .96
    b.loft('civicred', [
        (cx, cy, (body_top + 1.4) * scale, dome_r, dome_r, 1),
        (cx, cy, (body_top + 3.4) * scale, dome_r * .93, dome_r * .93, 1),
        (cx, cy, (body_top + 6.2) * scale, dome_r * .72, dome_r * .72, 1),
        (cx, cy, (body_top + 8.2) * scale, dome_r * .42, dome_r * .42, 1),
        (cx, cy, total * scale, dome_r * .06, dome_r * .06, 1),
    ], n=8)
    b.tube('silver', (cx, cy, total * scale), (cx, cy, (total + 3.2) * scale), .55 * scale, 6)
    b.box('redled', (cx, cy, (total + 3.6) * scale), (1.2 * scale, 1.2 * scale, 1.2 * scale))
    return {'totalMeters': total, 'domeMeters': dome,
            'ringPoints': len(ring), 'drumRadiusMeters': round(drum_r / scale, 1)}
