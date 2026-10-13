"""Yundang Lake musical fountain (筼筜湖音乐喷泉, Bailu Island); see data/landmarks/yundang.json.

Idle-state (no jets) stand-in for the reported 933-nozzle / 1094-LED fountain
inside the OSM-mapped 63 x 38 m pool: a concrete perimeter curb hugging the
water polygon, a central spray platform, three elliptical nozzle ring rails
with representative heads, eight LED bollards on the curb and a small control
kiosk at the east pool edge. The pool water already renders as the city water
layer at z = -0.25 game metres; every z here is anchored to that plane. Real
metres in, scaled once by the caller.
"""
import math

try:
    from ._helpers import centroid, bbox, scaled, closed
except ImportError:
    from _helpers import centroid, bbox, scaled, closed

ZW = -0.25  # game-metre water plane shared with the city water layer


def _curb(b, ring, scale):
    """Low concrete curb following the pool outline, plus a top ledge band."""
    pts = ring[:-1]
    inner = scaled(ring, 0.965)[:-1]  # 0.965: ~0.35 m ledge width on the ~11 m half-span
    top = ZW + 0.5 * scale            # 0.5 m curb above water (satellite-estimated)
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        b.face('concrete', [(pts[i][0], pts[i][1], ZW), (pts[j][0], pts[j][1], ZW),
                            (pts[j][0], pts[j][1], top), (pts[i][0], pts[i][1], top)])
        b.face('concrete', [(pts[i][0], pts[i][1], top), (pts[j][0], pts[j][1], top),
                            (inner[j][0], inner[j][1], top), (inner[i][0], inner[i][1], top)])


def _rails(b, cx, cy, rx_max, ry_max, scale):
    """Three elliptical steel ring rails with representative silver nozzle heads."""
    aspect = min(1.0, ry_max / rx_max)  # rings follow the pool aspect (63 x 38 m)
    rail_z = ZW + 0.15 * scale          # rails skim just above the water
    heads = 0
    for r, cnt, seg in ((8, 12, 24), (13, 14, 28), (17, 16, 32)):
        # Rail radii in real m (photo-estimated layout); outer clamped inside the curb.
        rx = min(r * scale, rx_max)
        ry = min(rx * aspect, ry_max)
        w = 0.12 * scale                # rail strip half-width (~0.24 m pipe walkway)
        for i in range(seg):
            q = []
            for a in (i * math.tau / seg, (i + 1) * math.tau / seg):
                ca, sa = math.cos(a), math.sin(a)
                q.append((cx + (rx - w) * ca, cy + (ry - w) * sa, rail_z))
                q.append((cx + (rx + w) * ca, cy + (ry + w) * sa, rail_z))
            b.face('steel', [q[0], q[1], q[3], q[2]])
        head = 0.35 * scale             # representative head; 933 reported (厦门网 2024)
        for i in range(cnt):
            a = (i + .5) * math.tau / cnt
            b.box('silver', (cx + rx * math.cos(a), cy + ry * math.sin(a),
                             rail_z + head / 2), (head, head, head))
            heads += 1
    return heads


def _bollards(b, ring, scale, count=8):
    """LED bollards evenly spaced on the curb ledge (1094 underwater LEDs reported;
    represented symbolically per the spec limitations)."""
    pts = scaled(ring, 0.98)[:-1]
    step = max(1, len(pts) // count)
    base = ZW + 0.5 * scale             # standing on the curb top
    h, w = 0.5 * scale, 0.3 * scale     # 0.5 m tall x 0.3 m wide bollard
    n = 0
    for i in range(0, len(pts), step):
        if n >= count:
            break
        x, y = pts[i]
        b.box('led', (x, y, base + h / 2), (w, w, h))
        n += 1
    return n


def _kiosk(b, ring, scale):
    """Control kiosk (17 underwater control cabinets per spec) just outside the
    curb at the east end of the pool's long axis; base anchored at water level."""
    x0, y0, x1, y1 = bbox(ring)
    cy = (y0 + y1) / 2
    w, d, h = 3.5 * scale, 2.5 * scale, 2.2 * scale  # reported small equipment room
    x = x1 + d / 2 + 0.4 * scale                     # 0.4 m clear of the curb
    b.box('concrete', (x, cy, ZW + h / 2), (d, w, h))
    b.box('darkglass', (x, cy, ZW + h * .62), (d * 1.05, w * 1.05, h * .28))
    b.box('redled', (x, cy, ZW + h + 0.15 * scale), (0.3 * scale, 0.3 * scale, 0.3 * scale))


def build(b, spec, pool_ring, scale):
    """Emit the idle fountain; pool_ring is the projected OSM pool outline in
    game metres, closed (first point repeated at the end)."""
    ring = closed(pool_ring)
    x0, y0, x1, y1 = bbox(ring)
    cx, cy = centroid(ring[:-1])
    seg = len(ring) - 1
    margin = 0.9 * scale  # keeps rails/platform clear of the curb ledge
    _curb(b, ring, scale)
    pr = 6 * scale        # 6 m central spray stage; 40 m center jet not modeled (idle)
    b.loft('concrete', [(cx, cy, ZW, pr, pr, 1),
                        (cx, cy, ZW + 0.3 * scale, pr, pr, 1)], n=24)
    heads = _rails(b, cx, cy, (x1 - x0) / 2 - margin, (y1 - y0) / 2 - margin, scale)
    lights = _bollards(b, ring, scale)
    _kiosk(b, ring, scale)
    extent = spec.get('pool', {}).get('extentMeters', {}).get('value', [63, 38])
    tris = (seg * 4            # curb walls + ledge quads
            + 92               # platform loft: 24 quads + two 24-gon caps
            + (24 + 28 + 32) * 2 + heads * 12 + lights * 12 + 3 * 12)
    return {'poolExtentMeters': extent, 'nozzleRings': 3, 'bollards': lights,
            'nozzleHeads': heads, 'trianglesApprox': tris}
