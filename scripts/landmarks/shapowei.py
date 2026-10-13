"""Shapowei typhoon-shelter fleet (沙坡尾避风坞); see data/landmarks/shapowei.json.

The projected OSM basin ring (way/785097854) drives every mooring through an
in-water sampler. Fleet = reported 2017+ landscape-boat era: wooden boats,
黄蓝相间 hulls + colourful flags (人民日报 2019), anchored by one 钓艚-style junk
(澎湃 2015: 船舯浑圆饱满; spec takes the 15 m lower bound). Boats are moored idle —
no gear, no 王船 (spec limitations); forms artistic. Real metres x `scale`.
"""
import math
import random

Z_WATER = -0.25        # game m, harbour water plane (contract)
DRAFT, FREEBOARD = 0.3, 0.8    # real m, keel below / deck above the waterline
CLEAR, GAP = 4.0, 8.0          # real m, edge clearance / hull-to-hull spacing
JUNK_LOA = 15.0                # real m, fleet anchor (spec junkLoaMeters)
SAM_LOA = (6.0, 12.0)          # real m, small-boat LOA range (typicalLoaMeters)
TRIES = 40                     # placement attempts before a boat is skipped


def _in_ring(x, y, ring):
    """Even-odd ray cast (pattern: build_landmark_details._in_ring)."""
    inside = False; j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi, xj, yj = *ring[i], *ring[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def _seg_dist2(x, y, a, c):
    """Squared point-segment distance (pattern: build_landmark_details)."""
    dx, dy = c[0] - a[0], c[1] - a[1]
    t = max(0.0, min(1.0, ((x - a[0]) * dx + (y - a[1]) * dy) / (dx * dx + dy * dy or 1.0)))
    return (x - a[0] - dx * t) ** 2 + (y - a[1] - dy * t) ** 2


def _edge_dist2(x, y, ring):
    """Squared distance to the nearest basin-edge segment (closed ring)."""
    return min(_seg_dist2(x, y, ring[i - 1], ring[i]) for i in range(len(ring)))


def _walk(x, y, dx, dy, ring, clear):
    """Walkable water distance along unit (dx,dy), 2 game m steps."""
    for k in range(1, 151):
        px, py = x + dx * 2.0 * k, y + dy * 2.0 * k
        if not _in_ring(px, py, ring) or _edge_dist2(px, py, ring) < clear * clear:
            return 2.0 * (k - 1)
    return 300.0


def _quayline(ring, clear, n=30):
    """Samples inset from the basin PERIMETER (a straight long-axis chord is
    defeated by the crescent shape: the chord cuts across the mouth). Typhoon-
    shelter boats moor along the quay walls, so walk the ring itself: each
    sample sits `clear` inside the edge, faces the boundary tangent and carries
    the further-inward walkable width."""
    if len(ring) < 4: return []
    pts = ring[:-1] if ring[0] == ring[-1] else ring
    cum = [0.0]
    for a, c in zip(pts, pts[1:] + pts[:1]):
        cum.append(cum[-1] + math.hypot(c[0] - a[0], c[1] - a[1]))
    L = cum[-1]
    if L < 1e-6: return []
    out = []
    for i in range(1, n):
        t = i / float(n); s = t * L; j = 1
        while j < len(cum) - 1 and cum[j] < s: j += 1
        a, c = pts[j - 1], pts[j % len(pts)]
        seg = cum[j] - cum[j - 1] or 1.0
        f = (s - cum[j - 1]) / seg
        x, y = a[0] + (c[0] - a[0]) * f, a[1] + (c[1] - a[1]) * f
        ux, uy = (c[0] - a[0]) / seg, (c[1] - a[1]) / seg
        nx, ny = -uy, ux
        # inward = the side that stays in the water at the inset depth
        if not _in_ring(x + nx * (clear + .5), y + ny * (clear + .5), ring):
            nx, ny = -nx, -ny
        sx, sy = x + nx * (clear + .5), y + ny * (clear + .5)
        if not _in_ring(sx, sy, ring) or _edge_dist2(sx, sy, ring) < clear * clear:
            continue
        w = _walk(sx, sy, nx, ny, ring, clear)
        if w < 1.0: continue                              # narrow tip / mouth chord
        out.append({'t': t, 'x': sx, 'y': sy, 'ux': ux, 'uy': uy,
                    'nx': nx, 'ny': ny, 'wp': w})
    return out


def _frame(p):
    """(cos, sin, local->world); local +x = bow along p['yaw']."""
    ca, sa = math.cos(p['yaw']), math.sin(p['yaw'])
    return ca, sa, lambda lx, ly, z: (p['x'] + lx * ca - ly * sa, p['y'] + lx * sa + ly * ca, z)


def _flag(b, f, scale, mat, state):
    """Double-sided masthead pennant, 0.8 x 0.5 real m (彩旗, reported 2017)."""
    x, y, z, ca, sa = f; w, h = 0.8 * scale, 0.5 * scale
    q = [(x, y, z), (x - ca * w, y - sa * w, z - h * 0.2),
         (x - ca * w, y - sa * w, z - h), (x, y, z - h * 0.8)]
    for qq in (q, list(reversed(q))): b.face(mat, qq)
    state['tris'] += 4


def _cabin(b, T, xh, hl, hw2, hh, z1, state):
    """Rotated wheelhouse prism (b.box is axis-aligned only): walls + roof + glass."""
    zb, zt = z1, z1 + hh
    for q in ((-hl, -hw2, hl, -hw2), (hl, -hw2, hl, hw2),
              (hl, hw2, -hl, hw2), (-hl, hw2, -hl, -hw2)):
        b.face('whiteroof', [T(xh + q[0], q[1], zb), T(xh + q[2], q[3], zb),
                             T(xh + q[2], q[3], zt), T(xh + q[0], q[1], zt)])
    b.face('whiteroof', [T(xh - hl, -hw2, zt), T(xh + hl, -hw2, zt),
                         T(xh + hl, hw2, zt), T(xh - hl, hw2, zt)])
    for s in (-1, 1):                            # window band each flank
        yb = s * (hw2 + .01)
        b.face('darkglass', [T(xh + dx, yb, zb + hh * fr) for dx, fr in
                             ((-hl * .6, .35), (hl * .6, .35), (hl * .6, .78), (-hl * .6, .78))])
    state['tris'] += 14


def _small_params(rng, scale, z0, z1, loa_range):
    """Roll one small boat: LOA 6-12 real m, beam = LOA x 0.32 +/-10%."""
    loa = rng.uniform(*loa_range) * scale; r = rng.random()   # mix per spec boats.mix:
    hull = ('orangetile' if r < 0.60 else        # 60% wooden fishing boats
            'carpaint' if r < 0.85 else 'concrete')   # 25% teal / 15% grey
    return {'loa': loa, 'beam': loa * 0.32 * rng.uniform(0.9, 1.1), 'hull': hull,
            'rail': hull == 'orangetile',        # grey rub-rail stripe on wood
            'house': rng.random() < 0.60,        # wheelhouse on ~60%
            'mast': rng.uniform(3, 5) * scale if rng.random() < 0.50 else 0.0,
            'z0': z0, 'z1': z1}


def _draw_small(b, p, scale, state):
    """Fishing sampan along its mooring yaw: tapered hull (transom quad, wedge
    bow, 4 side faces), low deck, optional wheelhouse + short mast."""
    L, W, z0, z1 = p['loa'], p['beam'], p['z0'], p['z1']
    ca, sa, T = _frame(p)
    tw, xm = 0.42 * W, -0.05 * L                 # transom half beam; beam station
    zb, zt = z0 + (z1 - z0) * 0.55, z1 + 0.25 * scale   # bow bottom; stem sheer
    for s in (-1, 1):
        b.face(p['hull'], [T(-L / 2, s * tw, z0), T(xm, s * W / 2, z0),
                           T(xm, s * W / 2, z1), T(-L / 2, s * tw, z1)])
        b.face(p['hull'], [T(xm, s * W / 2, z0), T(L / 2, 0, zb),
                           T(L / 2, 0, zt), T(xm, s * W / 2, z1)])
    b.face(p['hull'], [T(-L / 2, -tw, z0), T(-L / 2, tw, z0), T(-L / 2, tw, z1), T(-L / 2, -tw, z1)])
    b.face('whiteroof', [T(-L / 2, -tw, z1), T(xm, -W / 2, z1), T(L / 2, 0, zt),
                         T(xm, W / 2, z1), T(-L / 2, tw, z1)])
    state['tris'] += 13                          # 4 sides + transom + pentagon deck
    if p['rail']:                                # rub-rail stripe, proud of the hull
        hz, k = z1 - 0.3 * scale, 1.015
        for s in (-1, 1):
            prof = [(-L / 2, s * tw * k, hz, z1), (xm, s * W / 2 * k, hz, z1),
                    (L / 2, 0, (hz + zt) / 2, zt)]
            for u, v in zip(prof, prof[1:]):
                b.face('concrete', [T(u[0], u[1], u[2]), T(v[0], v[1], v[2]),
                                    T(v[0], v[1], v[3]), T(u[0], u[1], u[3])])
        state['tris'] += 8
    if p['house']:
        _cabin(b, T, -0.20 * L, 0.14 * L, 0.30 * W, 1.1 * scale, z1, state)
    if p['mast']:                                # short working mast, slight rake
        h = p['mast']; top = T(0.20 * L - 0.06 * h, 0, z1 + h)
        b.tube('bark', T(0.20 * L, 0, z1), top, 0.12 * scale, 6)
        state['tris'] += 20
        p['flagpt'] = (top[0], top[1], top[2], ca, sa)


def _draw_junk(b, p, scale, state):
    """钓艚-style fleet anchor: station-rib hull full amidships, bow cabin, two
    raked masts (8/6 real m) with furled sail spars — no canvas."""
    L, W, z0, z1 = p['loa'], p['beam'], p['z0'], p['z1']
    ca, sa, T = _frame(p)
    st = [(-0.50, 0.38), (-0.18, 0.50), (0.14, 0.48), (0.36, 0.30), (0.50, 0.02)]
    for s in (-1, 1):                            # 船舯浑圆饱满: full midship stations
        for (xa, wa), (xc, wc) in zip(st, st[1:]):
            b.face(p['hull'], [T(xa * L, s * wa * W, z0), T(xc * L, s * wc * W, z0),
                               T(xc * L, s * wc * W, z1), T(xa * L, s * wa * W, z1)])
    b.face(p['hull'], [T(-L / 2, -0.38 * W, z0), T(-L / 2, 0.38 * W, z0),
                       T(-L / 2, 0.38 * W, z1), T(-L / 2, -0.38 * W, z1)])
    deck = [T(xf * L, wf * W, z1 + 0.01) for xf, wf in st]
    deck += [T(xf * L, -wf * W, z1 + 0.01) for xf, wf in reversed(st[:-1])]
    b.face('whiteroof', deck)
    state['tris'] += 18 + len(deck) - 2          # 8 side + transom quads + deck
    _cabin(b, T, 0.32 * L, 0.09 * L, 0.30 * W, 1.2 * scale, z1, state)  # bow cabin
    for xm, h in ((-0.20 * L, 8.0 * scale), (0.10 * L, 6.0 * scale)):  # main + fore
        top = T(xm - 0.07 * h, 0, z1 + h)        # slight rake aft
        b.tube('bark', T(xm, 0, z1), top, 0.25 * scale, 6)   # 0.25 real m radius
        state['tris'] += 20
        b.tube('bark', T(xm - 0.02 * h, 0, z1 + h * 0.55),   # furled sail spar
               T(xm - 0.02 * h - 0.28 * L, 0, z1 + h * 0.52), 0.09 * scale, 5)
        state['tris'] += 16
        if h > 7.0 * scale:                      # main masthead carries the flag
            p['flagpt'] = (top[0], top[1], top[2], ca, sa)


def build(b, spec, basin_ring, scale):
    """Emit the moored fleet; basin_ring is the projected closed game-m outline.
    Returns {'boats', 'junkLoaMeters', 'trianglesApprox'}."""
    rng = random.Random(42)                      # deterministic fleet
    bs = spec.get('boats', {}) if isinstance(spec, dict) else {}
    target = int(bs.get('target', 10))           # 10 (spec boats.target)
    junk_loa = bs.get('junkLoaMeters', {}).get('value', JUNK_LOA)
    loa_range = bs.get('typicalLoaMeters', {}).get('value', SAM_LOA)
    ring = list(basin_ring)
    if len(ring) >= 2 and ring[0] != ring[-1]: ring.append(ring[0])
    state = {'tris': 0}; taken = []              # taken: (x, y, circumscribed radius)
    report = {'boats': 0, 'junkLoaMeters': int(junk_loa), 'trianglesApprox': 0}
    if len(ring) < 4: return report              # degenerate basin: no boats
    clear = CLEAR * scale
    z0, z1 = Z_WATER - DRAFT * scale, Z_WATER + FREEBOARD * scale   # keel / deck
    line = _quayline(ring, clear)
    if len(line) < 3: return report              # no walkable quay: no boats

    def seat(t_want, r_circ):
        """TRIES attempts; rejects land/edge/spacing so bad basins skip, not crash."""
        for _ in range(TRIES):
            t = min(max(t_want + rng.uniform(-0.07, 0.07), 0.0), 1.0)
            s = min(line, key=lambda q: abs(q['t'] - t))
            room = s['wp'] - r_circ              # further-inward walkable width
            if room < 0.5: continue
            o, j = room * rng.uniform(0.15, 0.9), rng.uniform(-4.0, 4.0)
            x, y = s['x'] + s['nx'] * o + s['ux'] * j, s['y'] + s['ny'] * o + s['uy'] * j
            if not _in_ring(x, y, ring) or _edge_dist2(x, y, ring) < (clear + r_circ) ** 2:
                continue
            need = r_circ + GAP * scale          # hull gap >= 8 real m between boats
            if any((x - q[0]) ** 2 + (y - q[1]) ** 2 < (need + q[2]) ** 2 for q in taken):
                continue
            yaw = math.atan2(s['uy'], s['ux']) + math.radians(rng.uniform(-15, 15))
            taken.append((x, y, r_circ))
            return {'x': x, 'y': y, 'yaw': yaw, 'z0': z0, 'z1': z1}
        return None

    boats = []; jl = float(junk_loa) * scale     # 15 # 钓艚 lower bound (spec)
    jw = jl * 0.36                               # full midship (澎湃 2015)
    # Stratified fleet mix (spec boats.mix): wooden majority + 2 teal sampans
    # + 1 grey — a raw 25% roll came up empty on the fixed seed, so pin the
    # quotas and let the seeded shuffle spread them around the loop.
    small_n = max(0, target - 1)
    hulls = (['orangetile'] * max(0, small_n - 3) + ['carpaint'] * min(2, small_n) +
             ['concrete'] * (1 if small_n >= 3 else 0) + ['orangetile'] * small_n)[:small_n]
    rng.shuffle(hulls)
    best = max(line, key=lambda q: q['wp'])      # junk at the widest water
    pl = seat(best['t'], math.hypot(jl / 2, jw / 2))
    if pl:
        pl.update({'loa': jl, 'beam': jw, 'hull': 'orangetile'})
        _draw_junk(b, pl, scale, state); boats.append(pl)
    for i in range(max(0, target - 1)):          # 9 smaller boats, spread round the loop
        p = _small_params(rng, scale, z0, z1, loa_range)
        p['hull'] = hulls[i]                     # stratified mix (below), not a raw roll
        t_i = 0.10 + 0.80 * (i + 0.5) / max(1, target - 1)
        pl = seat(t_i, math.hypot(p['loa'] / 2, p['beam'] / 2))
        if pl is None: continue                  # unplaceable after TRIES: skipped
        pl.update(p); _draw_small(b, pl, scale, state); boats.append(pl)
    flagged = [q for q in boats if q.get('flagpt')]
    for k, q in enumerate(rng.sample(flagged, min(4, len(flagged)))):  # 彩旗 on 4
        _flag(b, q['flagpt'], scale, 'redled' if k % 2 == 0 else 'led', state)
    report.update({'boats': len(boats), 'trianglesApprox': state['tris']})
    return report
