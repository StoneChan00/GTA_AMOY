"""Bailu Goddess (白鹭女神) on lake rocks off Bailu Island; see data/landmarks/bailu.json.

13.6 m white-granite statue (王则坚; 1997 enlargement of the 1977 original): a
kneeling goddess combing her long hair, one egret perched on her shoulder, on a
2-3 boulder granite plinth standing in 筼筜湖. Low-poly artistic silhouette
(kneel + raised arm + bird), not a sculptural replica. Real metres in, scaled
once by the caller.
"""
import math


def build(b, spec, cx, cz, scale):
    """Emit statue + plinth; (cx, cz) is the projected OSM artwork anchor.

    cz is the map-plane name for the north (Blender y) coordinate; z is up and
    the lake sea-plane sits at z = -0.25 game metres (build_city_ground).
    """
    x0, y0 = cx, cz
    s = scale
    wat = -0.25
    zb = wat - 1.0 * s          # rock base 1.0 real m under the waterline
    zt = wat + 1.5 * s          # rock crown: 2.5 m plinth, ~1.5 m proud (photo est.)
    fz = lambda h: zt + h * s   # figure z at real height h above the rock crown

    # Rock plinth: three overlapping granite mounds, low and broad per photos.
    b.loft('granite', [(x0 - .6 * s, y0 + .5 * s, zb, 4.9 * s, 4.1 * s, .8),
                       (x0 - .3 * s, y0 + .2 * s, wat + .5 * s, 4.3 * s, 3.6 * s, .8),
                       (x0, y0, zt, 3.3 * s, 2.7 * s, .8)], n=7)   # main, ~9 m across
    b.loft('granite', [(x0 + 3.4 * s, y0 - 1.6 * s, zb, 2.7 * s, 2.3 * s, .8),
                       (x0 + 3.0 * s, y0 - 1.4 * s, zt - .3 * s, 1.6 * s, 1.3 * s, .8)],
           n=6)                                                    # SE rock, ~5 m
    b.loft('granite', [(x0 - 3.1 * s, y0 - 2.0 * s, zb, 2.1 * s, 1.8 * s, .8),
                       (x0 - 2.8 * s, y0 - 1.7 * s, zt - .45 * s, 1.1 * s, .9 * s, .8)],
           n=6)                                                    # low SW rock

    # Kneeling figure facing south (-y) toward open water: the site note puts
    # her on the south water edge; exact bearing is not in the evidence.
    # Lower body: kneeling mass 4.5 m tall, skirt 4.5 m wide, 2.2 m waist.
    b.loft('whiteroof', [(x0, y0 - .25 * s, fz(0), 2.25 * s, 2.0 * s, .9),
                         (x0, y0 - .10 * s, fz(2.2), 1.9 * s, 1.6 * s, .9),
                         (x0, y0 + .15 * s, fz(3.6), 1.45 * s, 1.2 * s, .9),
                         (x0, y0 + .30 * s, fz(4.5), 1.1 * s, .95 * s, .9)], n=12)
    # Torso ~4 m: waist 2.2 -> shoulders 3.2 m, gentle S-lean via ring offsets.
    b.loft('whiteroof', [(x0, y0 + .30 * s, fz(4.5), 1.1 * s, .95 * s, .9),
                         (x0 - .05 * s, y0 + .10 * s, fz(6.0), 1.25 * s, 1.0 * s, .9),
                         (x0 - .10 * s, y0 - .05 * s, fz(7.4), 1.5 * s, .95 * s, .9),
                         (x0, y0 - .10 * s, fz(8.6), 1.6 * s, .75 * s, .9)], n=12)
    # Subtle darkglass sash band over the waist seam (0.55 m tall).
    b.loft('darkglass', [(x0, y0 + .22 * s, fz(4.30), 1.32 * s, 1.15 * s, .9),
                         (x0, y0 + .27 * s, fz(4.85), 1.28 * s, 1.10 * s, .9)], n=12)

    # Neck and ~1.1 m head; hair knot brings the figure to its ~11 m nominal.
    hx, hy = x0 - .05 * s, y0 + .15 * s        # head centre back over the spine
    b.tube('whiteroof', (hx, hy, fz(8.55)), (hx, hy, fz(9.20)), .28 * s, 6)
    b.loft('whiteroof', [(hx, hy, fz(9.10), .34 * s, .38 * s, .9),
                         (hx, hy - .05 * s, fz(9.70), .55 * s, .60 * s, .9),
                         (hx, hy, fz(10.30), .30 * s, .34 * s, .9)], n=8)
    b.loft('whiteroof', [(hx, hy + .10 * s, fz(10.25), .34 * s, .34 * s, .9),
                         (hx, hy + .12 * s, fz(10.90), .08 * s, .08 * s, .9)], n=8)
    # Long hair drape down the back; emitted with both windings so it never
    # back-face-culls from any camera side.
    drape = [(hx - .50 * s, hy + .50 * s, fz(10.10)), (hx + .50 * s, hy + .50 * s, fz(10.10)),
             (hx + .70 * s, hy + 1.15 * s, fz(5.40)), (hx - .70 * s, hy + 1.15 * s, fz(5.40))]
    b.face('whiteroof', drape)
    b.face('whiteroof', list(reversed(drape)))

    # Raised right arm (hair-combing pose): upper arm ~50 deg off vertical,
    # forearm bends in to the hand beside the knot.
    dx = math.tan(math.radians(50)) * .85
    sh = (x0 + 1.45 * s, y0 - .10 * s, fz(8.30))          # shoulder
    el = (sh[0] + dx * s, y0 - .35 * s, fz(9.15))         # elbow out and up
    hd = (x0 + 1.15 * s, y0 - .60 * s, fz(10.35))         # hand at the hair
    b.tube('whiteroof', sh, el, .45 * s, 6, r2=.36 * s)
    b.tube('whiteroof', el, hd, .36 * s, 6, r2=.24 * s)

    # Egret on the far (left) shoulder, ~1.8 m over the feet: placed opposite
    # the raised arm so bird and arm both read against the sky at ~150 m.
    ex, ey = x0 - 1.35 * s, y0 + .05 * s
    for lx in (-.12, .12):                                # silver legs
        b.tube('silver', (ex + lx * s, ey, fz(8.20)), (ex + lx * s, ey, fz(8.62)), .05 * s, 3)
    b.loft('whiteroof', [(ex, ey + .10 * s, fz(8.55), .30 * s, .45 * s, .9),
                         (ex, ey, fz(8.95), .36 * s, .60 * s, .9),      # ~1.2 m body
                         (ex, ey - .05 * s, fz(9.25), .20 * s, .32 * s, .9)], n=6)
    b.tube('whiteroof', (ex, ey - .25 * s, fz(9.10)), (ex - .10 * s, ey - .50 * s, fz(9.50)),
           .13 * s, 5, r2=.10 * s)                        # S-neck, lower curve
    b.tube('whiteroof', (ex - .10 * s, ey - .50 * s, fz(9.50)), (ex, ey - .40 * s, fz(9.95)),
           .10 * s, 5, r2=.08 * s)                        # S-neck, up to the head
    b.tube('silver', (ex, ey - .42 * s, fz(9.92)), (ex, ey - 1.00 * s, fz(9.82)),
           .045 * s, 4)                                   # long egret beak

    return {'statueMeters': 13.6, 'figureMeters': 11, 'rockMeters': 2.5,
            'trianglesApprox': 534}
