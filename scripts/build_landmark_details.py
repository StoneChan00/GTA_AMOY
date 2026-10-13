"""Build independent source-grounded landmark assets; never overwrite city roads.

Xiamen (GTA_AMOY) edition. Object modules live in scripts/landmarks/<id>.py
with evidence-labelled specs in data/landmarks/<id>.json; this integrator owns
the Blender scene, projection, collision footprints, manifest and export.
Run with Blender --background --factory-startup --python this_file.py.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / 'landmarks'))
from city_mesh import *
import hashlib
import math
from collections import defaultdict
from landmarks import shimao, riguangyan, bagua, xmu, gaoqi, xiamenzhan, huizhan

city = json.loads((O/'city.json').read_text())
scale = city['meta']['horizontalScale']
origin = city['meta']['originWGS84']
project = lambda lon, lat: ((lon-origin[0])*101310*scale, (lat-origin[1])*111320*scale)
bearing = lambda a, b: math.atan2((b[0]-a[0])*101310, (b[1]-a[1])*111320)
objects, records, collisions, replacements = [], [], [], ['landmark_shimao_']
base_ids = set()
reports = []
specs = {sid: json.loads((R/f'data/landmarks/{sid}.json').read_text(encoding='utf-8'))
         for sid in ('shimao', 'riguangyan', 'bagua', 'xmu', 'gaoqi', 'xiamenzhan', 'huizhan')}


def project_ring(points):
    """Project a WGS84 ring and close it (OSM ways are implicitly closed)."""
    ring = [project(lon, lat) for lon, lat in points]
    if ring[0] != ring[-1]:
        ring.append(ring[0])
    return ring


def footprint(identifier, ring):
    ring = [[round(x, 4), round(z, 4)] for x, z in ring]
    if ring[-1] != ring[0]:
        ring.append(ring[0])
    collisions.append({'id': identifier, 'rings': [ring]})


def _in_ring(x, z, ring):
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, zi = ring[i]
        xj, zj = ring[j]
        if (zi > z) != (zj > z) and x < (xj - xi) * (z - zi) / (zj - zi) + xi:
            inside = not inside
        j = i
    return inside


# Kept city buildings as (bbox, ring) for arrival-blocked checks; excluded ids
# are skipped live so late additions to base_ids still free their ground.
_city_blocks = [(bd.get('id'),
                 (min(p[0] for p in bd['rings'][0]), min(p[1] for p in bd['rings'][0]),
                  max(p[0] for p in bd['rings'][0]), max(p[1] for p in bd['rings'][0])),
                 bd['rings'][0]) for bd in city['buildings']]


def _seg_dist2(x, z, a, b):
    dx, dz = b[0]-a[0], b[1]-a[1]
    t = max(0, min(1, ((x-a[0])*dx + (z-a[1])*dz) / (dx*dx + dz*dz or 1)))
    return (x-a[0]-dx*t)**2 + (z-a[1]-dz*t)**2


_road_segments = []
for _road in city['roads']:
    _w = _road['width']/2 - .65
    if _w <= 0 or len(_road['points']) < 2:
        continue
    for _i in range(1, len(_road['points'])):
        _a, _b = _road['points'][_i-1], _road['points'][_i]
        _road_segments.append((_w, _a, _b,
                               min(_a[0], _b[0])-_w, min(_a[1], _b[1])-_w,
                               max(_a[0], _b[0])+_w, max(_a[1], _b[1])+_w))


def _on_road(x, z):
    """Road carve-out mirrors CityCollision: within width/2-.65 of a segment."""
    for w, a, b, x0, z0, x1, z1 in _road_segments:
        if x < x0 or x > x1 or z < z0 or z > z1:
            continue
        if _seg_dist2(x, z, a, b) < w*w:
            return True
    return False


def point_blocked(x, z):
    """Mirror CityCollision.blocked: buildings (+1.15 m edge margin), land and
    water polygons; roads carve out. Detail footprints count as buildings."""
    if _on_road(x, z):
        return False
    rings = [fp['rings'][0] for fp in collisions]
    rings += [ring for bid, bb, ring in _city_blocks if bid not in base_ids]
    for ring in rings:
        if _in_ring(x, z, ring):
            return True
        for i in range(1, len(ring)):
            if _seg_dist2(x, z, ring[i-1], ring[i]) < 1.15**2:
                return True
    on_land = any(_in_ring(x, z, p[0]) and not any(_in_ring(x, z, h) for h in p[1:])
                  for p in city['land'])
    if not on_land:
        return True
    if any(_in_ring(x, z, p['rings'][0]) and not any(_in_ring(x, z, h) for h in p['rings'][1:])
           for p in city['water']):
        return True
    return False


def arrival(x, z):
    # Reuse the connected navigation graph for a genuinely reachable destination.
    nav = json.loads((O/'navigation.json').read_text())
    parent = list(range(len(nav['nodes'])))
    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    adjacency = defaultdict(list)
    for a, b in nav['edges']:
        parent[find(a)] = find(b)
        adjacency[a].append(b)
        adjacency[b].append(a)
    counts = defaultdict(int)
    for i in range(len(parent)):
        counts[find(i)] += 1
    main = max(counts, key=counts.get)
    candidates = [i for i in range(len(parent)) if find(i) == main and adjacency[i]]
    # Nearest road nodes first, but skip nodes that sit inside a detail
    # footprint: the arrival must stay drivable, not clipped by our own model.
    candidates.sort(key=lambda i: math.dist(nav['nodes'][i], (x, z)))
    i = next((c for c in candidates[:12] if not point_blocked(*nav['nodes'][c])), candidates[0])
    a = nav['nodes'][i]
    j = min(adjacency[i], key=lambda j: math.dist(nav['nodes'][j], (x, z)))
    q = nav['nodes'][j]
    return {'arrival': a, 'yaw': math.atan2(q[0]-a[0], q[1]-a[1]), 'arrivalRoad': '周边连通道路'}


def walk_only(x, z):
    # Gulangyu carries no road graph: the arrival stays near the object, but it
    # must escape the model's own collision ring so it stays walkable.
    for step in range(0, 14):
        for angle in (0, .8, -.8, 1.6, -1.6, 2.4, -2.4, math.pi):
            px, pz = x + math.cos(angle) * 4 * step, z + math.sin(angle) * 4 * step
            if not point_blocked(px, pz):
                return {'arrival': [round(px, 2), round(pz, 2)], 'yaw': 0, 'arrivalRoad': '鼓浪屿 · 步行岛'}
    return {'arrival': [round(x, 2), round(z, 2)], 'yaw': 0, 'arrivalRoad': '鼓浪屿 · 步行岛'}


def collect(b, name, report=None, smooth=False):
    obs = b.finish(name, smooth)
    objects.extend(obs)
    reports.append({'id': name, 'triangles': sum(sum(len(p.vertices)-2 for p in ob.data.polygons) for ob in obs),
                    'meshes': len(obs), 'report': report})


def rect(cx, cy, angle, w, d):
    ca, sa = math.cos(angle), math.sin(angle)
    pts = [(-w/2, -d/2), (w/2, -d/2), (w/2, d/2), (-w/2, d/2), (-w/2, -d/2)]
    return [[cx + x*ca - y*sa, cy + x*sa + y*ca] for x, y in pts]


# ------------------------------------------------------------------ Shimao
towers = []
for tower in specs['shimao']['towers']:
    ring = project_ring(tower['footprintWGS84'])
    towers.append({**tower, 'ring': ring})
    footprint('detail-shimao-'+tower['id'].lower(), ring)
podium = {**specs['shimao']['podium'], 'ring': project_ring(specs['shimao']['podium']['footprintWGS84'])}
footprint('detail-shimao-podium', podium['ring'])
b = B()
collect(b, 'detail_shimao', shimao.build(b, specs['shimao'], towers, podium, scale))
site_x = sum(p[0] for t in towers for p in t['ring']) / sum(len(t['ring']) for t in towers)
site_z = sum(p[1] for t in towers for p in t['ring']) / sum(len(t['ring']) for t in towers)
legacy = next(lm for lm in city['landmarks'] if lm['id'] == 'shimao')
crown_top = max(t['crownTopMeters']['value'] if isinstance(t['crownTopMeters'], dict) else t['crownTopMeters'] for t in specs['shimao']['towers'])
records.append({**legacy, 'x': round(site_x, 2), 'z': round(site_z, 2),
                'lon': specs['shimao']['site']['centerWGS84'][0], 'lat': specs['shimao']['site']['centerWGS84'][1],
                'height': crown_top*scale, 'area': '思明 · 沙坡尾',
                'excludeRadius': 0, 'detailCollision': True,
                'photoDistance': 640, 'photoTargetHeight': 118, 'photoElevation': .24, 'photoAngle': -1.42,
                'sourceStatus': specs['shimao']['status'], **arrival(site_x, site_z)})
base_ids |= set(t['osmId'] for t in specs['shimao']['towers']) | {specs['shimao']['podium']['osmId']}

# ------------------------------------------------------------- 日光岩 (new)
cx, cz = project(*specs['riguangyan']['site']['centerWGS84'])
b = B()
collect(b, 'detail_riguangyan', riguangyan.build(b, specs['riguangyan'], cx, cz, scale))
rock = [[cx + 82 * scale * math.cos(i * math.tau / 24), cz + 62 * scale * math.sin(i * math.tau / 24)] for i in range(24)]
footprint('detail-riguangyan-rock', rock)
records.append({'id': 'riguangyan', 'name': '日光岩 · 龙头山', 'x': round(cx, 2), 'z': round(cz, 2),
                'lon': specs['riguangyan']['site']['centerWGS84'][0], 'lat': specs['riguangyan']['site']['centerWGS84'][1],
                'height': round(92.7*scale, 1), 'area': '鼓浪屿 · 中部偏南',
                'excludeRadius': 0, 'detailCollision': True,
                'photoDistance': 420, 'photoTargetHeight': 46, 'photoElevation': .18, 'photoAngle': 2.4,
                'sourceStatus': specs['riguangyan']['status'], **walk_only(cx, cz)})

# ------------------------------------------------------------ 八卦楼 (new)
ring = project_ring(specs['bagua']['footprint']['footprintWGS84'])
bx, bz = sum(p[0] for p in ring)/len(ring), sum(p[1] for p in ring)/len(ring)
footprint('detail-bagua', ring)
b = B()
collect(b, 'detail_bagua', bagua.build(b, specs['bagua'], ring, scale))
records.append({'id': 'bagua', 'name': '八卦楼 · 风琴博物馆', 'x': round(bx, 2), 'z': round(bz, 2),
                'lon': specs['bagua']['site']['centerWGS84'][0], 'lat': specs['bagua']['site']['centerWGS84'][1],
                'height': round(25.7*scale, 1), 'area': '鼓浪屿 · 笔架山',
                'excludeRadius': 0, 'detailCollision': True,
                'photoDistance': 300, 'photoTargetHeight': 14, 'photoElevation': .22, 'photoAngle': -.9,
                'sourceStatus': specs['bagua']['status'], **walk_only(bx, bz)})

# ------------------------------------------------------------------ 厦门大学
XANCH = specs['xmu']['anchorsWGS84']
q_c = project(*(sum(p)/2 for p in zip(XANCH['nangyingCenter'], XANCH['yingxueCenter'])))
q_rot = bearing(XANCH['nangyingCenter'], XANCH['yingxueCenter'])
j_c = project(*XANCH['jiagengGroupCenter'])
j_rot = bearing(XANCH['zhongmingxuanCenter'], XANCH['jiagengGroupCenter'])
n_c = project(*XANCH['jiannanCenter'])
n_rot = math.radians(XANCH['jiannanFacadeBearingDeg']['value'] - 90)
row = specs['xmu']['groups']['qunxian']
row_w = sum(bd['widthMeters'] for bd in row['buildingsWestToEast']) + row['gapMeters']*4
footprint('detail-xmu-qunxian', rect(q_c[0], q_c[1], q_rot, row_w*scale, 36*scale))
footprint('detail-xmu-jiageng', rect(j_c[0], j_c[1], j_rot, 320*scale, 42*scale))
footprint('detail-xmu-jiannan', rect(n_c[0], n_c[1], n_rot, 55*scale, 78*scale))
b = B()
collect(b, 'detail_xmu', xmu.build(b, specs['xmu'],
                                   (q_c[0], q_c[1], q_rot), (j_c[0], j_c[1], j_rot),
                                   (n_c[0], n_c[1], n_rot), scale))
legacy = next(lm for lm in city['landmarks'] if lm['id'] == 'xmu')
records.append({**legacy, 'x': round(q_c[0], 2), 'z': round(q_c[1], 2),
                'lon': specs['xmu']['site']['centerWGS84'][0], 'lat': specs['xmu']['site']['centerWGS84'][1],
                'height': round(85*scale, 1), 'area': '思明 · 厦门大学',
                'excludeRadius': 0, 'detailCollision': True,
                'photoDistance': 520, 'photoTargetHeight': 30, 'photoElevation': .16, 'photoAngle': -.7,
                'sourceStatus': specs['xmu']['status'], **arrival(q_c[0], q_c[1])})
base_ids |= {'way/156122784', 'way/156122776', 'way/560033573', 'way/156122777',
             'way/156122793', 'way/156122775', 'way/156122801', 'way/156122773'}

# -------------------------------------------------------------------- 高崎
t3_ring = project_ring(specs['gaoqi']['t3']['footprint']['footprintWGS84'])
t4_ring = project_ring(specs['gaoqi']['t4']['footprint']['footprintWGS84'])
footprint('detail-gaoqi-t3', t3_ring)
footprint('detail-gaoqi-t4', t4_ring)
b = B()
collect(b, 'detail_gaoqi', gaoqi.build(b, specs['gaoqi'], t3_ring, t4_ring, scale))
g4x = sum(p[0] for p in t4_ring)/len(t4_ring)
g4z = sum(p[1] for p in t4_ring)/len(t4_ring)
g4lon = sum(p[0] for p in specs['gaoqi']['t4']['footprint']['footprintWGS84'])/len(specs['gaoqi']['t4']['footprint']['footprintWGS84'])
g4lat = sum(p[1] for p in specs['gaoqi']['t4']['footprint']['footprintWGS84'])/len(specs['gaoqi']['t4']['footprint']['footprintWGS84'])
legacy = next(lm for lm in city['landmarks'] if lm['id'] == 'gaoqi')
records.append({**legacy, 'x': round(g4x, 2), 'z': round(g4z, 2),
                'lon': round(g4lon, 6), 'lat': round(g4lat, 6),
                'height': round(39*scale, 1), 'area': '湖里 · 高崎机场',
                'excludeRadius': 0, 'detailCollision': True,
                'photoDistance': 560, 'photoTargetHeight': 16, 'photoElevation': .2, 'photoAngle': 2.9,
                'sourceStatus': specs['gaoqi']['status'], **arrival(g4x, g4z)})
base_ids |= {specs['gaoqi']['t3']['footprint']['osmId'], specs['gaoqi']['t4']['footprint']['osmId']}

# ------------------------------------------------------------------ 厦门站
sx, sz = project(*specs['xiamenzhan']['site']['centerWGS84'])
dims = specs['xiamenzhan']['dims']
station_rect = rect(sx, sz, 0, dims['widthEastWestMeters']['value']*scale,
                    (dims['lengthNorthSouthMeters']['value']*.42 + 34)*scale)
footprint('detail-xiamenzhan', station_rect)
b = B()
collect(b, 'detail_xiamenzhan', xiamenzhan.build(b, specs['xiamenzhan'], sx, sz, scale))
legacy = next(lm for lm in city['landmarks'] if lm['id'] == 'xiamenzhan')
records.append({**legacy, 'x': round(sx, 2), 'z': round(sz, 2),
                'lon': specs['xiamenzhan']['site']['centerWGS84'][0], 'lat': specs['xiamenzhan']['site']['centerWGS84'][1],
                'height': round(31*scale, 1), 'area': '思明 · 厦禾路',
                'excludeRadius': 0, 'detailCollision': True,
                'photoDistance': 480, 'photoTargetHeight': 14, 'photoElevation': .2, 'photoAngle': math.pi,
                'sourceStatus': specs['xiamenzhan']['status'], **arrival(sx, sz)})

# ------------------------------------------------------------------ 会展中心
hall_rings = {}
for hall in specs['huizhan']['halls']:
    hall_rings[hall['key']] = project_ring(hall['footprintWGS84'])
    footprint(f"detail-huizhan-{hall['key']}", hall_rings[hall['key']])
    base_ids.add(hall['osmId'])
b = B()
collect(b, 'detail_huizhan', huizhan.build(b, specs['huizhan'], hall_rings, scale))
hx = sum(p[0] for r in hall_rings.values() for p in r) / sum(len(r) for r in hall_rings.values())
hz = sum(p[1] for r in hall_rings.values() for p in r) / sum(len(r) for r in hall_rings.values())
legacy = next(lm for lm in city['landmarks'] if lm['id'] == 'huizhan')
records.append({**legacy, 'x': round(hx, 2), 'z': round(hz, 2),
                'lon': specs['huizhan']['site']['centerWGS84'][0], 'lat': specs['huizhan']['site']['centerWGS84'][1],
                'height': round(42.6*scale, 1), 'area': '思明 · 前埔会展',
                'excludeRadius': 0, 'detailCollision': True,
                'photoDistance': 620, 'photoTargetHeight': 18, 'photoElevation': .18, 'photoAngle': -2.2,
                'sourceStatus': specs['huizhan']['status'], **arrival(hx, hz)})

# Final pass: later footprints may cover an earlier arrival; re-snap any that
# ended up inside a model's own collision ring.
for r in records:
    if point_blocked(*r['arrival']):
        fixed = walk_only(r['x'], r['z']) if r['id'] in ('riguangyan', 'bagua') else arrival(*r['arrival'])
        r['arrival'], r['yaw'] = fixed['arrival'], fixed['yaw']

# Auto-extension of baseBuildingIds by footprint overlap runs outside Blender
# (scripts/extend_landmark_exclusions.py with the venv shapely).

asset = export('landmark-detail', objects)
bpy.ops.wm.save_as_mainfile(filepath=str(A/'landmark-details.blend'))
source_paths = ['data/landmarks/shimao.json', 'data/landmarks/riguangyan.json', 'data/landmarks/bagua.json',
                'data/landmarks/xmu.json', 'data/landmarks/gaoqi.json', 'data/landmarks/xiamenzhan.json',
                'data/landmarks/huizhan.json',
                'scripts/landmarks/shimao.py', 'scripts/landmarks/riguangyan.py', 'scripts/landmarks/bagua.py',
                'scripts/landmarks/xmu.py', 'scripts/landmarks/gaoqi.py', 'scripts/landmarks/xiamenzhan.py',
                'scripts/landmarks/huizhan.py', 'scripts/landmarks/_helpers.py',
                'scripts/build_landmark_details.py', 'scripts/city_mesh.py']
manifest = {'schemaVersion': 1, 'asset': '/city/landmark-detail.glb', 'assetStats': asset,
            'replacedMeshPrefixes': replacements,
            'baseBuildingIds': sorted(base_ids),
            'landmarks': records, 'baseBuildingExclusionsRequired': True,
            'collisionFootprints': collisions, 'terrain': {'url': '/city/terrain-detail.json'},
            'modelReports': reports,
            'sourceSha256': {p: hashlib.sha256((R/p).read_bytes()).hexdigest() for p in source_paths},
            'coordinateSystem': 'Blender east,north,up; GLB y-up; runtime preserves root Z reflection',
            'horizontalScale': scale, 'verticalScale': scale,
            'generator': {'blender': bpy.app.version_string},
            'limitations': [l for sid in specs for l in specs[sid].get('limitations', [])]}
(O/'landmark-detail.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
print('LANDMARK_DETAILS', json.dumps({'asset': asset, 'models': [{r['id']: r['triangles']} for r in reports],
      'landmarks': [r['id'] for r in records], 'baseBuildings': len(base_ids)}, ensure_ascii=False), flush=True)
