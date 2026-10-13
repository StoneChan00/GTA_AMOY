"""Wuyuan Bay yacht harbour (五缘湾游艇港); see data/landmarks/wuyuan.json.

Evidence chain: the 145 OSM man_made=pier ways (wuyuan-piers.json, already
projected and scaled to game metres by the integrator) drive every pontoon
deck position and shape. The reported 351 berths / ~220 moored vessels
(央视网 2026-02-28) motivate the fleet, but its rendered size (spec target
~90 yachts) and each boat's form are artistic, capped by the triangle budget.
Pontoon widths (2.2 / 3.5 real m) and 0.4 real m freeboard are estimates —
the OSM ways carry no width tags. Real metres are multiplied by `scale`
once, at point of use; pier coordinates arrive pre-scaled.
"""
import math
import random

# The bay/lake water plane sits at z = -0.25 game m (coastal infrastructure
# manifest waterHeight); every pontoon/boat z below hangs off that datum.
WATER = -0.25       # game m, bay water plane
Z_TOP = -0.01       # pontoon deck top, game m (0.4 real m freeboard x 0.6)
Z_BOT = -0.19       # pontoon deck soffit, game m (floating-draft edge)
DECK_MAIN = 3.5    # real m, main pier width (>=120 real m piers; estimated)
DECK_FINGER = 2.2  # real m, finger pontoon width (estimated)
MAIN_LEN = 120.0   # real m, main-vs-finger pier length threshold
HULL_BOT = -0.40   # boat keel z, game m (hull partly submerged)
HULL_TOP = 0.25    # boat deck z, game m (~1.2 real m hull height x 0.6 ~ 0.72,
                   # drawn slightly lower so the sheer reads at game scale)
JOINT = 0.05       # game m, per-end segment overlap hiding deck seams
MIN_SEG = 0.5      # game m, segments shorter than this are degenerate: skipped
CLEAR = 0.3        # game m, fender gap between hull and pontoon edge


def _clean(pts):
    """Drop consecutive duplicate/near-duplicate points (degenerate OSM nodes)."""
    out = []
    for p in pts:
        x, y = float(p[0]), float(p[1])
        if not out or math.hypot(x - out[-1][0], y - out[-1][1]) > 1e-3:
            out.append((x, y))
    return out


def _cum(pts):
    """Cumulative arc lengths along a cleaned polyline."""
    c = [0.0]
    for a, b in zip(pts, pts[1:]):
        c.append(c[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    return c


def _at(pts, cum, s):
    """(x, y, heading) at arc length s along the polyline."""
    s = min(max(s, 0.0), cum[-1])
    i = 0
    while i < len(cum) - 2 and cum[i + 1] < s:
        i += 1
    a, b = pts[i], pts[i + 1]
    seg = cum[i + 1] - cum[i]
    t = (s - cum[i]) / seg
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t,
            math.atan2(b[1] - a[1], b[0] - a[0]))


def _deck(b, pts, cum, w, state):
    """Pontoon deck: per segment a top quad + two side quads (rotated, not
    b.box which is axis-aligned). Closed rings arrive pre-closed by build()."""
    hw = w / 2.0
    drawn = False
    for i in range(len(pts) - 1):
        seg = cum[i + 1] - cum[i]
        if seg < MIN_SEG:            # degenerate segment: skip, no crash
            continue
        a, c = pts[i], pts[i + 1]
        ux, uy = (c[0] - a[0]) / seg, (c[1] - a[1]) / seg
        nx, ny = -uy, ux
        x0, y0 = a[0] - ux * JOINT, a[1] - uy * JOINT   # overlap hides joints
        x1, y1 = c[0] + ux * JOINT, c[1] + uy * JOINT
        p = [(x0 + nx * hw, y0 + ny * hw), (x1 + nx * hw, y1 + ny * hw),
             (x1 - nx * hw, y1 - ny * hw), (x0 - nx * hw, y0 - ny * hw)]
        b.face('concrete', [(q[0], q[1], Z_TOP) for q in p])
        b.face('concrete', [(*p[0], Z_TOP), (*p[1], Z_TOP), (*p[1], Z_BOT), (*p[0], Z_BOT)])
        b.face('concrete', [(*p[3], Z_TOP), (*p[2], Z_TOP), (*p[2], Z_BOT), (*p[3], Z_BOT)])
        state['tris'] += 6           # 3 quads per segment
        drawn = True
    return drawn


def _boat_params(rng, spec, scale):
    """Roll one yacht's dimensions/colours; all reals x scale to game metres."""
    lo, hi = spec['boats']['loaRealMeters']              # 8-18 real m LOA
    loa = rng.uniform(lo, hi) * scale
    beam = loa * rng.uniform(0.27, 0.33)                 # beam = LOA x 0.30 +/-10%
    r = rng.random()                                     # fleet mix per spec:
    hull = ('whiteroof' if r < 0.78 else 'carpaint' if r < 0.90 else
            'civicred' if r < 0.95 else 'orangetile')    # 78/12/5/5 percent
    return {'loa': loa, 'beam': beam, 'hull': hull,
            'mast': rng.uniform(11, 19) * scale,         # 11-19 real m rig
            'house': rng.uniform(0.55, 0.70),            # house centre, frac of LOA from bow
            'boom': rng.random() < 0.60}                 # 60% carry a boom


def _plan_fleet(spec, geoms, scale, step_lo, step_hi):
    """Deterministic berth plan: walk each pier 0.25->0.9 of length in
    (step_lo..step_hi) real-metre steps, 70% occupancy, alternating sides;
    main piers may berth on both sides at once."""
    fleet = []
    for idx, g in enumerate(geoms):
        rng = random.Random(idx + 1)                     # per-pier fixed seed
        pts, cum, L, deck_w = g['pts'], g['cum'], g['L'], g['deck_w']
        if L < 5.0 * scale:                              # <5 real m: no berth
            continue
        if L < 7.0 * scale:                              # 5-7 real m stub:
            x, y, a = _at(pts, cum, L * 0.95)            # single bow-end boat
            fleet.append({'x': x, 'y': y, 'ang': a, 'side': 1,
                          'deck_w': deck_w, 'p': _boat_params(rng, spec, scale)})
            continue
        s, end, side = 0.25 * L, 0.9 * L, 1
        while s < end:
            step = rng.uniform(step_lo, step_hi) * scale
            if rng.random() < 0.70:
                x, y, a = _at(pts, cum, s)
                fleet.append({'x': x, 'y': y, 'ang': a, 'side': side,
                              'deck_w': deck_w, 'p': _boat_params(rng, spec, scale)})
                side = -side                             # alternate flanks
                if L >= MAIN_LEN * scale and rng.random() < 0.5:
                    fleet.append({'x': x, 'y': y, 'ang': a, 'side': side,
                                  'deck_w': deck_w, 'p': _boat_params(rng, spec, scale)})
                    side = -side                         # both sides on main piers
            s += step
    return fleet


def _boat(b, pl, scale, state):
    """Sailing yacht along its berth tangent: tapered hull (6 faces),
    deckhouse prism with darkglass bands, raked mast, optional boom."""
    p = pl['p']
    L, W, mh = p['loa'], p['beam'], p['mast']
    ca, sa = math.cos(pl['ang']), math.sin(pl['ang'])
    off = pl['deck_w'] / 2.0 + W / 2.0 + CLEAR           # hull fully off the deck
    cx = pl['x'] - sa * pl['side'] * off
    cy = pl['y'] + ca * pl['side'] * off

    def T(lx, ly, z):                                    # local (bow=+x) -> world
        return (cx + lx * ca - ly * sa, cy + lx * sa + ly * ca, z)

    tw = 0.42 * W                                        # transom half width
    xm = -0.05 * L                                       # max-beam station, slightly aft
    z0, z1 = HULL_BOT, HULL_TOP
    stern, bow = (-L / 2.0, 0.0), (L / 2.0, 0.0)
    for s in (-1, 1):                                  # 4 side faces: transom->beam->bow
        b.face(p['hull'], [T(-L / 2.0, s * tw, z0), T(xm, s * W / 2.0, z0),
                           T(xm, s * W / 2.0, z1), T(-L / 2.0, s * tw, z1)])
        b.face(p['hull'], [T(xm, s * W / 2.0, z0), T(*bow, z0),
                           T(*bow, z1), T(xm, s * W / 2.0, z1)])
    b.face(p['hull'], [T(-L / 2.0, -tw, z1), T(xm, -W / 2.0, z1), T(*bow, z1),
                       T(xm, W / 2.0, z1), T(-L / 2.0, tw, z1)])   # deck (pentagon)
    b.face(p['hull'], [T(-L / 2.0, -tw, z0), T(-L / 2.0, tw, z0),
                       T(-L / 2.0, tw, z1), T(-L / 2.0, -tw, z1)])  # flat transom
    state['tris'] += 13                                  # 4 quads + pent + quad
    # Deckhouse: 0.35 LOA long prism, 0.9 real m high, at p['house'] from bow.
    xh = L / 2.0 - p['house'] * L
    hl, hwd, hh = 0.175 * L, 0.275 * W, 0.9 * scale
    zb, zt = HULL_TOP, HULL_TOP + hh
    for q in ((-hl, -hwd, hl, -hwd), (hl, -hwd, hl, hwd),
              (hl, hwd, -hl, hwd), (-hl, hwd, -hl, -hwd)):
        b.face('whiteroof', [T(q[0], q[1], zb), T(q[2], q[3], zb),
                             T(q[2], q[3], zt), T(q[0], q[1], zt)])
    b.face('whiteroof', [T(-hl, -hwd, zt), T(hl, -hwd, zt), T(hl, hwd, zt), T(-hl, hwd, zt)])
    for s in (-1, 1):                                    # window band each flank
        b.face('darkglass', [T(xh - 0.12 * L, s * (hwd + 0.01), zb + hh * 0.35),
                             T(xh + 0.12 * L, s * (hwd + 0.01), zb + hh * 0.35),
                             T(xh + 0.12 * L, s * (hwd + 0.01), zb + hh * 0.75),
                             T(xh - 0.12 * L, s * (hwd + 0.01), zb + hh * 0.75)])
    state['tris'] += 14                                  # 5 quads + 2 bands
    # Mast at 38% LOA from bow, raked ~8% of height aft; n=6 tube.
    xmast = L / 2.0 - 0.38 * L
    b.tube('steel', T(xmast, 0, HULL_TOP), T(xmast - 0.08 * mh, 0, HULL_TOP + mh),
           0.09 * scale, 6)                              # 0.09 real m spar radius
    state['tris'] += 20                                  # 6 side quads + 2 hex caps
    if p['boom']:                                        # boom 1.2 real m above deck
        h = 1.2 * scale
        dx = -0.08 * h                                   # rake at gooseneck height
        b.tube('steel', T(xmast + dx, 0, HULL_TOP + h),
               T(xmast + dx - 0.55 * L, 0, HULL_TOP + h), 0.06 * scale, 6)
        state['tris'] += 20


def build(b, spec, piers, scale):
    """Emit the marina; `piers` polylines are pre-projected game metres (east,
    north). Returns {'piers', 'boats', 'trianglesApprox'}."""
    state = {'tris': 0}
    geoms = []
    for pr in piers:
        pts = _clean(pr['polyline'])
        if pr.get('closed') and len(pts) > 2 and pts[0] != pts[-1]:
            pts.append(pts[0])                           # close the ring for decks
        if len(pts) < 2:
            continue
        cum = _cum(pts)
        L = cum[-1]
        if L < MIN_SEG:                                  # fully degenerate way
            continue
        deck_w = (DECK_MAIN if L >= MAIN_LEN * scale else DECK_FINGER) * scale
        geoms.append({'pts': pts, 'cum': cum, 'L': L, 'deck_w': deck_w})
    rendered = 0
    for g in geoms:
        if _deck(b, g['pts'], g['cum'], g['deck_w'], state):
            rendered += 1
    # Fleet: plan at the evidence spacing (14-20 real m berths), then thin by
    # raising the step until within the spec target if the budget would burst.
    target = spec['boats']['target']                     # ~90 boats
    lo, hi = 14.0, 20.0
    fleet = _plan_fleet(spec, geoms, scale, lo, hi)
    tries = 0
    while len(fleet) > target and tries < 8:
        f = len(fleet) / (target * 0.92)
        lo, hi = lo * f, hi * f
        fleet = _plan_fleet(spec, geoms, scale, lo, hi)
        tries += 1
    fleet = fleet[:target]                               # hard safety cap
    for pl in fleet:
        _boat(b, pl, scale, state)
    return {'piers': rendered, 'boats': len(fleet), 'trianglesApprox': state['tris']}
