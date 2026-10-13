"""XICEC main exhibition halls; see data/landmarks/huizhan.json.

Phase-1 main building massing from the OSM hall rings: a long glass-fronted
base (the lobby faces the west plaza) under a rising sequence of shell vaults
toward the reported 42.6 m roof crown, with the cantilevered eave reading of
the 双向外挑 35 m steel roof. Real metres in, scaled once by the caller.
"""
import math

try:
    from ._helpers import centroid, bbox
except ImportError:
    from _helpers import centroid, bbox


def _shell_row(b, cx, cy, angle, length, span, eave, crowns, scale):
    """A row of barrel shells along local +x; crowns rise then fall (大鹏)."""
    ca, sa = math.cos(angle), math.sin(angle)
    n = len(crowns)
    ribs = []
    for i in range(n * 2 + 1):
        x = (i / (n * 2) - .5) * length
        bay = min(int(i / 2), n - 1)
        crown = crowns[bay] * scale
        rib = [(x, y, eave * scale + (crown - eave * scale) * (1 - (y / (span / 2)) ** 2))
               for y in [(-.5 + j / 8) * span for j in range(9)]]
        ribs.append([(cx + p[0] * ca - p[1] * sa, cy + p[0] * sa + p[1] * ca, p[2]) for p in rib])
    for a, c in zip(ribs, ribs[1:]):
        for i in range(len(a) - 1):
            b.face('silver', [a[i], a[i + 1], c[i + 1], c[i]])
    return {'shells': n, 'crownMax': max(crowns)}


def build(b, spec, rings, scale):
    """rings: {'big1': ring, 'big2': ring, 'big3': ring} in game metres."""
    # The main complex axis runs north-south (long side); the glass lobby
    # faces west toward the plaza, so the vault rows run along north-south.
    all_pts = [p for ring in rings.values() for p in ring]
    x0, y0 = min(p[0] for p in all_pts), min(p[1] for p in all_pts)
    x1, y1 = max(p[0] for p in all_pts), max(p[1] for p in all_pts)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    length, width = y1 - y0, x1 - x0
    angle = math.pi / 2  # local +x of the shell rows points north
    # Two parallel shell rows (west lobby row + east hall row) over the merged
    # extent; the west row sits over the 18.5 m lobby, the east over the halls.
    hall_eave, hall_crowns = 17, [26, 30, 34, 34, 30, 26]
    lobby_eave, lobby_crowns = 12, [20, 26, 31, 31, 26, 20]
    # One wide hall row plus a lower lobby row: the merged ring bbox is wider
    # than the real complex, so clamp the shell span to the reported ~140 m
    # hall width instead of the bbox width (neighbour blocks stay clear).
    row_offset = 20 * scale
    span = min(width * .34, 150 * scale)
    report = {}
    for name, eave, crowns, ox in (('east', hall_eave, hall_crowns, row_offset),
                                   ('west', lobby_eave, lobby_crowns, -row_offset)):
        rx, ry = cx + math.cos(angle + math.pi / 2) * ox, cy + math.sin(angle + math.pi / 2) * ox
        report[name] = _shell_row(b, rx, ry, angle, length * .94, span, eave, crowns, scale)
    # Base: glass walls around the merged ring set, the west face fully glazed.
    for key, ring in rings.items():
        b.footprint('concrete', ring, 0, 6 * scale, 1)
        b.footprint('landmarkglass', ring, 6 * scale, 14 * scale, .99)
    # Lobby prow: the tallest swoop pushes over the north-west corner.
    px, py = cx - width * .3, cy + length * .36
    b.loft('silver', [(px, py, 14 * scale, 26 * scale, 15 * scale, 1),
                      (px, py, 30 * scale, 15 * scale, 9 * scale, 1),
                      (px, py, 42.6 * scale, 3 * scale, 2 * scale, 1)], n=18)
    report['prowCrownMeters'] = 42.6
    return report
