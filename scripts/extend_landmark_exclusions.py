"""Extend landmark-detail baseBuildingIds with any city building overlapped by
a detail collision footprint. Runs with the venv Python (needs shapely), after
build_landmark_details.py produced the manifest.

Old generic blocks under a new evidence-based model would otherwise coexist
with (and clip through) the replacement.
"""
import json
from pathlib import Path

import shapely
from shapely.geometry import Polygon

R = Path(__file__).resolve().parents[1]
O = R/'public/city'
manifest = json.loads((O/'landmark-detail.json').read_text(encoding='utf-8'))
city = json.loads((O/'city.json').read_text(encoding='utf-8'))

base = set(manifest['baseBuildingIds'])
city_rings = {b.get('id'): Polygon(b['rings'][0]) for b in city['buildings'] if b.get('id')}
auto = set()
for fp in manifest['collisionFootprints']:
    area = shapely.make_valid(Polygon(fp['rings'][0]))
    for bid, poly in city_rings.items():
        if bid in base or bid in auto:
            continue
        if area.intersects(poly) and area.intersection(poly).area > 24:
            auto.add(bid)

if auto:
    manifest['baseBuildingIds'] = sorted(base | auto)
    (O/'landmark-detail.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'explicit': len(base), 'autoExtended': len(auto),
                  'sample': sorted(auto)[:10]}, ensure_ascii=False))
