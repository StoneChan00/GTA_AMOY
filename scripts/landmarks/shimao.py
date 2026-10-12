"""Source-grounded Xiamen Shimao Strait Tower twin sails; see data/landmarks/shimao.json.

No bpy import and no export side effects. Tower and podium rings arrive as
absolute game-metre (east, north) polygons already projected by the caller;
vertical dimensions stay real metres scaled once by the caller. Reported,
OSM-mapped and photo-estimated parameters remain separately labelled in the
specification; nothing here upgrades an estimate to a measurement.
"""
import math


def _v(obj, key):
    value = obj[key]
    return value['value'] if isinstance(value, dict) else value


def _taper(spec, z):
    levels = spec['taper']['levelsMetersScale']
    for (z0, s0), (z1, s1) in zip(levels, levels[1:]):
        if z0 <= z <= z1:
            return s0 if z1 == z0 else s0 + (s1 - s0) * (z - z0) / (z1 - z0)
    return levels[-1][1]


def _scaled(ring, s):
    cx = sum(p[0] for p in ring) / len(ring)
    cy = sum(p[1] for p in ring) / len(ring)
    return [(cx + (x - cx) * s, cy + (y - cy) * s) for x, y in ring]


def _centroid(ring):
    return (sum(p[0] for p in ring) / len(ring), sum(p[1] for p in ring) / len(ring))


def _sail_crown(b, ring, roof_scale, roof, top, direction):
    """Open steel framework from the roof ring up to a slanted ridge line.

    The ridge runs along the twin-splay axis with the high end at the reported
    300 m crown top and the low end around the photo-estimated 256 m; the sail
    membrane drags from the ridge down to the south-east roof arc, and both
    ridge ends carry aviation beacons.
    """
    cx, cy = _centroid(ring)
    ux, uy = direction
    projections = [(p[0] - cx) * ux + (p[1] - cy) * uy for p in ring]
    extent = max(abs(v) for v in projections) or 1.0
    # The framework keeps narrowing above the roof (never wider than the top
    # body segment), so the crown reinforces the taper instead of flaring out.
    length = extent * 0.55
    low = (cx - ux * length, cy - uy * length, roof + 6 * (top - roof) / 50.1)
    high = (cx + ux * length, cy + uy * length, top)
    b.tube('steel', low, high, .9, 6)
    # Ring beams hold the frame apart at two levels, both inside the roof ring.
    for z, s in ((roof + (top - roof) * .32, .52), (roof + (top - roof) * .68, .42)):
        b.footprint('steel', _scaled(ring, s), z, z + 1.4, 1.02)
    # Slanted struts from the tapered roof ring up to the ridge.
    roof_ring = _scaled(ring, roof_scale)
    for i, (p, t) in enumerate(zip(roof_ring, projections)):
        frac = t / extent
        zr = low[2] + (high[2] - low[2]) * (frac + 1) / 2
        b.tube('steel', (p[0], p[1], roof), (cx + ux * length * frac, cy + uy * length * frac, zr), .42, 5)
    # Sail membrane: a slanted sheet from the ridge line down to the roof arc
    # on the high (south-east) side, tall enough to read at skyline distance.
    membrane = [(high[0], high[1], high[2])]
    for i, t in enumerate(projections):
        if t < extent * .25:
            continue
        p = roof_ring[i]
        membrane.append((p[0], p[1], roof))
    if len(membrane) >= 3:
        for a, c in zip(membrane, membrane[1:]):
            b.face('landmarkglass', [a, c, (c[0], c[1], roof), (a[0], a[1], roof)],
                   [(0, 0), (1, 0), (1, (max(a[2], c[2]) - roof) / 24), (0, (max(a[2], c[2]) - roof) / 24)])
    for point in (low, high):
        b.box('redled', (point[0], point[1], point[2] + 1.1), (2.6, 2.6, 2.6))
    return high


def _tower(b, tower, spec, scale, direction):
    ring = tower['ring']
    roof_real = _v(tower, 'roofMeters')
    top_real = _v(tower, 'crownTopMeters')
    roof, top = roof_real * scale, top_real * scale
    quads = 0
    # Body: continuously tapered stack of extrusions; footprint() caps each top
    # with the roof material so the final cap reads as the roof deck.
    levels = [z for z, _ in spec['taper']['levelsMetersScale']]
    for z0, z1 in zip(levels, levels[1:]):
        b.footprint('landmarkglass', ring, z0 * scale, z1 * scale, _taper(spec, z1))
        quads += len(ring)
    # Horizontal course bands follow the taper and sit 1.2% proud of the wall.
    for z in range(60, int(roof_real), 30):
        b.footprint('steel', ring, z * scale, (z + 1.6) * scale, _taper(spec, z) * 1.012)
        quads += len(ring)
    # Vertical mullion strips per taper segment give the curtain-wall read
    # without one box per panel; strips re-anchor at each taper break so they
    # never float away from the narrowing wall.
    edges = list(zip(ring, ring[1:] + ring[:1]))
    for (z0, z1) in zip(levels, levels[1:]):
        if z1 <= levels[1]:  # podium sleeve stays uncluttered
            continue
        s0, s1 = _taper(spec, z0), _taper(spec, z1)
        seg0, seg1 = _scaled(ring, s0 * 1.015), _scaled(ring, s1 * 1.015)
        for (a, c), p0, p1 in zip(edges, seg0, seg1):
            if math.dist(a, c) < 6:
                continue
            e0 = (c[0] - a[0], c[1] - a[1])
            b.face('steel', [(p0[0], p0[1], z0 * scale), (p0[0] + e0[0], p0[1] + e0[1], z0 * scale),
                             (p1[0] + e0[0], p1[1] + e0[1], z1 * scale), (p1[0], p1[1], z1 * scale)],
                   [(0, z0 / 24), (.3, z0 / 24), (.3, z1 / 24), (0, z1 / 24)])
            quads += 1
    peak = _sail_crown(b, ring, _taper(spec, roof_real), roof, top, direction)
    return {'id': tower['id'], 'quads': quads, 'peak': [round(v, 2) for v in peak]}


def build(b, spec, towers, podium, scale):
    """Emit the twin sails, shared podium and roof plant into builder b."""
    # Splay axis: the OSM-mapped line between the two tower centroids, with
    # the crown high ends toward the south-east per the photo estimate.
    (ax, ay), (bx, by) = (_centroid(towers[0]['ring']), _centroid(towers[1]['ring']))
    dx, dy = bx - ax, by - ay
    length = math.hypot(dx, dy) or 1.0
    direction = (dx / length, dy / length)
    report = {'towers': []}
    for tower in towers:
        report['towers'].append(_tower(b, tower, spec, scale, direction))
    ring = podium['ring']
    roof = _v(spec['podium'], 'roofMeters') * scale
    b.footprint('stone', ring, 0, roof, 1.0)
    b.footprint('darkglass', ring, 0, 2.8 * scale, .992)
    # Roof plant blocks keep the deck from reading as an empty slab.
    cx, cy = _centroid(ring)
    for i, (ox, oy, s) in enumerate(((-.22, .18, (26, 14, 4.2)), (.16, -.2, (18, 12, 3.4)), (.05, .3, (12, 9, 2.8)))):
        span_x = max(p[0] for p in ring) - min(p[0] for p in ring)
        span_y = max(p[1] for p in ring) - min(p[1] for p in ring)
        b.box('concrete', (cx + ox * span_x, cy + oy * span_y, roof + s[2] * scale * .5), tuple(v * scale for v in s))
    report['podium'] = {'ringPoints': len(ring), 'roofMeters': _v(spec['podium'], 'roofMeters')}
    return report
