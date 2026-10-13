"""Shared geometry helpers for landmark modules (no bpy; pure math on B API)."""
import math


def centroid(ring):
    return (sum(p[0] for p in ring) / len(ring), sum(p[1] for p in ring) / len(ring))


def bbox(ring):
    xs = [p[0] for p in ring]
    ys = [p[1] for p in ring]
    return min(xs), min(ys), max(xs), max(ys)


def scaled(ring, s):
    cx, cy = centroid(ring)
    return [(cx + (x - cx) * s, cy + (y - cy) * s) for x, y in ring]


def closed(ring):
    return ring if ring[0] == ring[-1] else ring + [ring[0]]


def gable_roof(b, mat, cx, cy, angle, width, depth, eave, ridge_h, overhang=1.06):
    """Double-slope roof ridge along local x. Local frame: x=ridge axis, y=depth.

    width: ridge-axis length; depth: slope span (eave-to-eave); eave: base z;
    ridge_h: ridge height above eave. Two quads + two gable triangles.
    """
    hw, hd = width / 2 * overhang, depth / 2 * overhang
    ca, sa = math.cos(angle), math.sin(angle)

    def p(x, y, z):
        return (cx + x * ca - y * sa, cy + x * sa + y * ca, z)

    e, r = eave, eave + ridge_h
    b.face(mat, [p(-hw, -hd, e), p(hw, -hd, e), p(hw, 0, r), p(-hw, 0, r)],
           [(0, 0), (width / 8, 0), (width / 8, ridge_h / 6), (0, ridge_h / 6)])
    b.face(mat, [p(hw, hd, e), p(-hw, hd, e), p(-hw, 0, r), p(hw, 0, r)],
           [(0, 0), (width / 8, 0), (width / 8, ridge_h / 6), (0, ridge_h / 6)])
    # Gable end triangles at the ridge-axis ends.
    for x0 in (-hw, hw):
        b.face(mat, [p(x0, -hd, e), p(x0, hd, e), p(x0, 0, r)])


def hip_roof(b, mat, cx, cy, angle, width, depth, eave, ridge_h, overhang=1.06):
    """Four-slope hip roof; ridge along local x, shortened by depth/2 each end."""
    hw, hd = width / 2 * overhang, depth / 2 * overhang
    ca, sa = math.cos(angle), math.sin(angle)

    def p(x, y, z):
        return (cx + x * ca - y * sa, cy + x * sa + y * ca, z)

    e, r = eave, eave + ridge_h
    hr = max(hw - hd, hw * .18)  # ridge half-length
    ridge = [p(-hr, 0, r), p(hr, 0, r)]
    sw, se, nw, ne = p(-hw, -hd, e), p(hw, -hd, e), p(-hw, hd, e), p(hw, hd, e)
    b.face(mat, [sw, se, ridge[1], ridge[0]])
    b.face(mat, [ne, nw, ridge[0], ridge[1]])
    b.face(mat, [nw, sw, ridge[0]])
    b.face(mat, [se, ne, ridge[1]])


def swallowtail_hip(b, mat, cx, cy, angle, width, depth, eave, ridge_h):
    """Minnan hip with upturned ridge ends: hip roof plus raised ridge bars."""
    hip_roof(b, mat, cx, cy, angle, width, depth, eave, ridge_h)
    hw, hd = width / 2 * 1.04, depth / 2 * 1.04
    ca, sa = math.cos(angle), math.sin(angle)

    def p(x, y, z):
        return (cx + x * ca - y * sa, cy + x * sa + y * ca, z)

    r = eave + ridge_h
    for x0 in (-hw, hw):
        # Ridge bar rising toward each end (燕尾起翘).
        b.box(mat, p(x0 * .92, 0, r + ridge_h * .18), (abs(x0) * .18, 1.6, ridge_h * .5))


def arch_ribs(b, mat, ribs, cap_ends=False):
    """Connect consecutive polyline ribs (each a list of (x,y,z)) with quads."""
    for a, c in zip(ribs, ribs[1:]):
        for i in range(len(a) - 1):
            b.face(mat, [a[i], a[i + 1], c[i + 1], c[i]])
    if cap_ends:
        b.face(mat, list(reversed(ribs[0])))
        b.face(mat, ribs[-1])


def rib_arc(cx, cy, cz, half_span, crown, n=9, rise=None):
    """Parabolic arch rib across y in [-half_span, half_span] at fixed x=cx."""
    rise = crown if rise is None else rise
    return [(cx, cy - half_span + 2 * half_span * i / (n - 1),
             cz + rise * (1 - (2 * i / (n - 1) - 1) ** 2)) for i in range(n)]
