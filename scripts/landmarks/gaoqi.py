"""Gaoqi Airport T3/T4 terminals; see data/landmarks/gaoqi.json.

T4 (2014): L-shaped hall under a saddle roof — the crest rises toward both
ends of the long axis (闽南起翘), glass front on the city side. T3 (1996):
white Minnan swallowtail imagery with a long concourse. Rings are projected
OSM footprints; heights are reported (T4) and photo-estimated (T3).
"""
import math

try:
    from ._helpers import centroid, bbox, closed, arch_ribs, rib_arc
except ImportError:
    from _helpers import centroid, bbox, closed, arch_ribs, rib_arc


def _oriented_extents(ring):
    """Principal axis (longest bbox side direction) of a footprint ring."""
    x0, y0, x1, y1 = bbox(ring)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    # Sample four candidate headings, keep the one minimising the cross extent.
    best = None
    for k in range(36):
        a = k * math.pi / 18
        ca, sa = math.cos(a), math.sin(a)
        along = cross = 0
        for x, y in ring:
            u, v = (x - cx) * ca + (y - cy) * sa, -(x - cx) * sa + (y - cy) * ca
            along, cross = max(along, abs(u)), max(cross, abs(v))
        if best is None or along > best[0]:
            best = (along, cross, a)
    return cx, cy, best[2], best[0] * 2, best[1] * 2


def _saddle_roof(b, cx, cy, angle, length, span, eave, crown, rise_ends):
    """Saddle roof: arc ribs across the span, crest rising toward both ends.

    length/span are game metres; eave/crown/rise_ends are game metres too
    (the caller scales the reported heights once).
    """
    ca, sa = math.cos(angle), math.sin(angle)
    n_ribs = 22
    ribs = []
    for i in range(n_ribs):
        t = i / (n_ribs - 1) * 2 - 1                # -1 … 1 along the length
        x = t * length / 2
        crest = crown - rise_ends * (1 - abs(t) ** 2.6)
        rib = [(x, y, eave + (crest - eave) * (1 - (y / (span / 2)) ** 2))
               for y in [(-.5 + j / 8) * span for j in range(9)]]
        ribs.append([(cx + p[0] * ca - p[1] * sa, cy + p[0] * sa + p[1] * ca, p[2]) for p in rib])
    arch_ribs(b, 'whiteroof', ribs, cap_ends=True)
    return {'crestMin': round(crown - rise_ends, 1), 'crestMax': round(crown, 1)}


def _t4(b, ring, scale):
    """T4: podium, curtain wall, saddle roof over the main hall extent."""
    cx, cy, angle, length, span = _oriented_extents(ring)
    length, span = length * .78, span * .82          # main hall inside the L (game metres)
    b.footprint('concrete', ring, 0, 4 * scale, 1)
    b.footprint('landmarkglass', ring, 4 * scale, 21 * scale, .985)
    # City-side (south-east) glass band: rotate the local +y normal outward.
    front = angle + math.pi / 2
    fx, fy = cx + math.cos(front) * span * .49, cy + math.sin(front) * span * .49
    for z in (8, 14):
        b.box('darkglass', (fx, fy, z * scale), (length * .8, 2.4 * scale, 3.2 * scale))
    report = _saddle_roof(b, cx, cy, angle, length, span,
                          20 * scale, 39 * scale, 8 * scale)
    # Mullion strips hint the 79 leaning columns on the front edge.
    ca, sa = math.cos(angle), math.sin(angle)
    for i in range(9):
        t = (i / 8 - .5) * length * .86
        px, py = cx + t * ca + math.cos(front) * span * .5, cy + t * sa + math.sin(front) * span * .5
        b.tube('steel', (px, py, 4 * scale), (px, py, 26 * scale), .55 * scale, 6)
    return report


def _t3(b, ring, scale):
    """T3: long hall + concourse under white Minnan swallowtail roofs."""
    cx, cy, angle, length, span = _oriented_extents(ring)
    h = 14 * scale
    b.footprint('silver', ring, 0, h, 1)
    b.footprint('darkglass', ring, 2.4 * scale, (h - 1.2 * scale), .994)
    # Main roof: two long swallowtail bars over the hall, ridge along the axis.
    for oy in (-span * .22, span * .22):
        c2x, c2y = cx - math.sin(angle) * oy, cy + math.cos(angle) * oy
        hip_roof_bar(b, 'whiteroof', c2x, c2y, angle, length * .8, span * .5, h, 6.5 * scale)
    return {'hallHeightMeters': 14}


def hip_roof_bar(b, mat, cx, cy, angle, width, depth, eave, ridge_h):
    """Long four-slope bar used for T3's white roofs (ridge along the axis)."""
    ca, sa = math.cos(angle), math.sin(angle)

    def p(x, y, z):
        return (cx + x * ca - y * sa, cy + x * sa + y * ca, z)

    hw, hd = width / 2, depth / 2
    r = eave + ridge_h
    ridge = [p(-hw + hd, 0, r), p(hw - hd, 0, r)]
    sw, se = p(-hw, -hd, eave), p(hw, -hd, eave)
    nw, ne = p(-hw, hd, eave), p(hw, hd, eave)
    b.face(mat, [sw, se, ridge[1], ridge[0]])
    b.face(mat, [ne, nw, ridge[0], ridge[1]])
    b.face(mat, [nw, sw, ridge[0]])
    b.face(mat, [se, ne, ridge[1]])
    # Swallowtail: ridge bars kick up at both ends.
    for x0 in (-hw + hd, hw - hd):
        b.box(mat, p(x0, 0, r + ridge_h * .25), (depth * .9, 2.2, ridge_h * .55))


def build(b, spec, t3_ring, t4_ring, scale):
    """Emit both terminals from their projected OSM rings."""
    return {'t3': _t3(b, t3_ring, scale), 't4': _t4(b, t4_ring, scale)}
