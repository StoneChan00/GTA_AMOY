"""Xiamen University Jiageng-style groups; see data/landmarks/xmu.json.

Three groups from official per-building dimensions: the 1921-22 群贤楼群 row,
the 2001 嘉庚楼群 with the 21-storey 颂恩楼, and 建南大会堂 above 上弦场.
Anchors and row axes are projected by the caller from OSM group ways.
Real metres in, scaled once by the caller; b.frame local axes used per group.
"""
import math

try:
    from ._helpers import gable_roof, hip_roof, swallowtail_hip
except ImportError:
    from _helpers import gable_roof, hip_roof, swallowtail_hip

FLOOR = 3.4  # metres per storey, applied to reported floor counts


def _hall(b, mat, x, y, angle, w, d, floors, roof, scale):
    """One stone-walled hall with a window band and the given roof kind.

    x, y, angle place the hall in the caller's local frame; w, d and floors
    are real metres, scaled here into game metres.
    """
    h = FLOOR * floors * scale
    w, d = w * scale, d * scale
    ca, sa = math.cos(angle), math.sin(angle)

    def p(dx, dy):
        return (x + dx * ca - dy * sa, y + dx * sa + dy * ca)

    ring = [p(-w / 2, -d / 2), p(w / 2, -d / 2), p(w / 2, d / 2), p(-w / 2, d / 2), p(-w / 2, -d / 2)]
    b.footprint(mat, ring, 0, h, 1)
    b.footprint('darkglass', ring, 0.9 * scale, min(h - 0.9 * scale, FLOOR * (floors - 0.35) * scale), .992)
    if roof == 'gable-orange':
        gable_roof(b, 'orangetile', x, y, angle, w, d, h, 3.2 * scale)
    elif roof == 'swallow-green':
        swallowtail_hip(b, 'greentile', x, y, angle, w, d, h, 3.0 * scale)
    elif roof == 'double-eave':
        hip_roof(b, 'greentile', x, y, angle, w, d, h, 2.2 * scale)
        hip_roof(b, 'greentile', x, y, angle, w * .52, d * .52, h + 2.2 * scale, 3.4 * scale)
    return h


def _qunxian(b, spec, anchor, scale):
    """The 1921-22 row: five halls 一字排开 along local +x (the OSM 囊萤→映雪 axis)."""
    row = spec['groups']['qunxian']['buildingsWestToEast']
    gap = spec['groups']['qunxian']['gapMeters'] * scale
    widths = [bd['widthMeters'] * scale for bd in row]
    total_w = sum(widths) + gap * (len(row) - 1)
    x = -total_w / 2
    for bd, w in zip(row, widths):
        cx = x + w / 2
        floors = bd['floors'] if isinstance(bd['floors'], int) else 3
        roof = {'囊萤楼': 'gable-orange', '映雪楼': 'gable-orange',
                '同安楼': 'swallow-green', '集美楼': 'swallow-green',
                '群贤楼': 'double-eave'}[bd['name']]
        _hall(b, 'stone', cx, 0, 0, w, bd['depthMeters'] * scale, floors, roof, scale)
        if bd['name'] == '群贤楼':  # T-plan wings drop to two storeys.
            for side in (-1, 1):
                wx = cx + side * w * .28
                _hall(b, 'stone', wx, 0, 0, w * .18, bd['depthMeters'] * .8 * scale, 2, 'swallow-green', scale)
        x += w + gap
    return {'rowLengthMeters': round(total_w / scale, 1), 'buildings': len(row)}


def _jiageng(b, spec, anchor, scale):
    """The 2001 group: four 6-storey wings and the 21-storey 颂恩楼."""
    row = spec['groups']['jiageng']['buildingsNorthToSouth']
    fw, fd = (v * scale for v in spec['groups']['jiageng']['fromBuildingFootprintMeters']['value'])
    main_w, main_d = 34 * scale, 30 * scale
    gap = 14 * scale
    total_w = fw * 4 + main_w + gap * 4
    x = -total_w / 2
    for bd in row:
        is_main = bd['name'].startswith('颂恩')
        w = main_w if is_main else fw
        cx = x + w / 2
        if is_main:
            h = FLOOR * 21 * scale
            ring = _box(cx, 0, 0, main_w, main_d)
            b.footprint('landmarkglass', ring, 0, h, 1)
            b.footprint('darkglass', ring, 2.5 * scale, h - 3 * scale, .994)
            # Course bands every three storeys keep the curtain wall reading tall.
            for z in range(1, 21, 3):
                b.footprint('stone', _box(cx, 0, 0, main_w * 1.04, main_d * 1.04),
                            z * FLOOR * scale, z * FLOOR * scale + 1.1 * scale, 1)
            # Tiered green crown: three shrinking hipped steps to a spire.
            z = h
            for s, hh in ((.82, 4.2), (.55, 3.6), (.3, 3.0)):
                hip_roof(b, 'greentile', cx, 0, 0, main_w * s, main_d * s, z, hh * scale)
                z += hh * scale
            b.tube('silver', (cx, 0, z), (cx, 0, z + 4.5 * scale), .8 * scale, 6)
            b.box('redled', (cx, 0, z + 5 * scale), (1.4 * scale, 1.4 * scale, 1.4 * scale))
        else:
            _hall(b, 'stone', cx, 0, 0, w, fd, bd['floors'], 'gable-orange', scale)
        x += w + gap
    return {'mainFloors': 21, 'mainHeightMeters': round((FLOOR * 21 + 11), 1)}


def _box(cx, cy, angle, w, d):
    ca, sa = math.cos(angle), math.sin(angle)

    def p(dx, dy):
        return [cx + dx * ca - dy * sa, cy + dx * sa + dy * ca]

    return [p(-w / 2, -d / 2), p(w / 2, -d / 2), p(w / 2, d / 2), p(-w / 2, d / 2), p(-w / 2, -d / 2)]


def _jiannan(b, spec, anchor, scale):
    """建南大会堂: podium, hall under a red gable, green double-eave gate tower.

    Local +x runs along the facade; the gate tower sits at local +y (the front
    facing 上弦场 and the sea), set by the caller's frame rotation.
    """
    j = spec['groups']['jiannan']
    w, d = j['widthMeters'] * scale, j['depthMeters'] * scale
    # Stone podium suggests the real hillside seat.
    b.footprint('stone', _box(0, 0, 0, w * 1.1, d * 1.06), 0, 3.5 * scale, 1)
    # Hall body (single tall storey under a wide red gable), set back.
    b.footprint('stone', _box(0, -d * .12, 0, w, d * .8), 3.5 * scale, 3.5 * scale + 11 * scale, 1)
    b.footprint('darkglass', _box(0, -d * .12, 0, w, d * .8), 5 * scale, 12.5 * scale, .992)
    gable_roof(b, 'orangetile', 0, -d * .12, 0, w, d * .8, 14.5 * scale, 5.2 * scale)
    # Gate tower on the front edge (four storeys, double-eave green crown).
    b.footprint('stone', _box(0, d * .42, 0, w * .34, 14 * scale), 3.5 * scale, 3.5 * scale + FLOOR * 4 * scale, 1)
    b.footprint('darkglass', _box(0, d * .42, 0, w * .34, 14 * scale), 5 * scale, 15 * scale, .994)
    hip_roof(b, 'greentile', 0, d * .42, 0, w * .36, 15.5 * scale, 3.5 * scale + FLOOR * 4 * scale, 2.4 * scale)
    hip_roof(b, 'greentile', 0, d * .42, 0, w * .2, 9 * scale, 3.5 * scale + FLOOR * 4 * scale + 2.4 * scale, 3.2 * scale)
    return {'gateTowerFloors': 4, 'hallDepthMeters': j['depthMeters']}


def build(b, spec, qunxian_anchor, jiageng_anchor, jiannan_anchor, scale):
    """Anchors are (x, y, rotation) in game metres; rotation orients local +x."""
    report = {}
    for name, fn, anchor in (('qunxian', _qunxian, qunxian_anchor),
                             ('jiageng', _jiageng, jiageng_anchor),
                             ('jiannan', _jiannan, jiannan_anchor)):
        ax, ay, rotation = anchor
        b.frame = (ax, ay, rotation)
        report[name] = fn(b, spec, anchor, scale)
        b.frame = (0, 0, 0)
    return report
