"""Build independent source-grounded landmark assets; never overwrite city roads.

Xiamen (GTA_AMOY) edition. Object modules live in scripts/landmarks/<id>.py
with evidence-labelled specs in data/landmarks/<id>.json; this integrator owns
the Blender scene, projection, collision footprints, manifest and export.
Run with Blender --background --factory-startup --python this_file.py.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from city_mesh import *
import hashlib
from collections import defaultdict
from landmarks import shimao

city = json.loads((O/'city.json').read_text())
scale = city['meta']['horizontalScale']
origin = city['meta']['originWGS84']
project = lambda lon, lat: ((lon-origin[0])*101310*scale, (lat-origin[1])*111320*scale)
spec = json.loads((R/'data/landmarks/shimao.json').read_text())
objects, records, collisions, replacements = [], [], [], ['landmark_shimao_']
reports = []


def footprint(identifier, ring):
    ring = [[round(x, 4), round(z, 4)] for x, z in ring]
    if ring[-1] != ring[0]:
        ring.append(ring[0])
    collisions.append({'id': identifier, 'rings': [ring]})


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
    i = min(candidates, key=lambda i: math.dist(nav['nodes'][i], (x, z)))
    a = nav['nodes'][i]
    j = min(adjacency[i], key=lambda j: math.dist(nav['nodes'][j], (x, z)))
    q = nav['nodes'][j]
    return {'arrival': a, 'yaw': math.atan2(q[0]-a[0], q[1]-a[1]), 'arrivalRoad': '周边连通道路'}


def collect(b, name, report=None, smooth=False):
    obs = b.finish(name, smooth)
    objects.extend(obs)
    reports.append({'id': name, 'triangles': sum(sum(len(p.vertices)-2 for p in ob.data.polygons) for ob in obs),
                    'meshes': len(obs), 'report': report})


# Shimao Strait Towers: anchored to the OSM-mapped Shapowei site. The legacy M1
# marker sits 2.2 km east on the wrong block; the manifest record moves the
# map/photo marker onto the mapped site and the old circular exclusion dies
# with detailCollision footprints from the mapped rings.
towers = []
for tower in spec['towers']:
    ring = [project(*p) for p in tower['footprintWGS84']]
    towers.append({**tower, 'ring': ring})
    footprint('detail-shimao-'+tower['id'].lower(), ring)
podium = {**spec['podium'], 'ring': [project(*p) for p in spec['podium']['footprintWGS84']]}
footprint('detail-shimao-podium', podium['ring'])
b = B()
collect(b, 'detail_shimao', shimao.build(b, spec, towers, podium, scale))

site_x = sum(p[0] for t in towers for p in t['ring']) / sum(len(t['ring']) for t in towers)
site_z = sum(p[1] for t in towers for p in t['ring']) / sum(len(t['ring']) for t in towers)
legacy = next(lm for lm in city['landmarks'] if lm['id'] == 'shimao')
crown_top = max(t['crownTopMeters']['value'] if isinstance(t['crownTopMeters'], dict) else t['crownTopMeters'] for t in spec['towers'])
records.append({**legacy, 'x': round(site_x, 2), 'z': round(site_z, 2),
                'lon': spec['site']['centerWGS84'][0], 'lat': spec['site']['centerWGS84'][1],
                'height': crown_top*scale, 'area': '思明 · 沙坡尾',
                'excludeRadius': 0, 'detailCollision': True,
                'photoDistance': 640, 'photoTargetHeight': 118, 'photoElevation': .24, 'photoAngle': -1.42,
                'sourceStatus': spec['status'], **arrival(site_x, site_z)})

asset = export('landmark-detail', objects)
bpy.ops.wm.save_as_mainfile(filepath=str(A/'landmark-details.blend'))
source_paths = ['data/landmarks/shimao.json', 'scripts/landmarks/shimao.py',
                'scripts/build_landmark_details.py', 'scripts/city_mesh.py']
manifest = {'schemaVersion': 1, 'asset': '/city/landmark-detail.glb', 'assetStats': asset,
            'replacedMeshPrefixes': replacements,
            'baseBuildingIds': sorted([t['osmId'] for t in spec['towers']] + [spec['podium']['osmId']]),
            'landmarks': records, 'baseBuildingExclusionsRequired': True,
            'collisionFootprints': collisions, 'terrain': {'url': '/city/terrain-detail.json'},
            'modelReports': reports,
            'sourceSha256': {p: hashlib.sha256((R/p).read_bytes()).hexdigest() for p in source_paths},
            'coordinateSystem': 'Blender east,north,up; GLB y-up; runtime preserves root Z reflection',
            'horizontalScale': scale, 'verticalScale': scale,
            'generator': {'blender': bpy.app.version_string},
            'limitations': spec['limitations']}
(O/'landmark-detail.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
print('LANDMARK_DETAILS', json.dumps({'asset': asset, 'models': reports,
      'baseBuildingIds': manifest['baseBuildingIds']}, ensure_ascii=False), flush=True)
