"""Extract full WGS84 rings for chosen way ids + find railway/terminal features."""
import json

import osmium

PBF = 'data/raw/fujian-latest.osm.pbf'

WANTED = {
    'way/156122784': 'xmu-qunxian',
    'way/156122776': 'xmu-jiageng',
    'way/560033573': 'xmu-jiannan',
    'way/156122777': 'xmu-qunxian2',
    'way/164652578': 'gulangyu-bagua',
    'way/286527185': 'huizhan-hall2',
    'way/1490453918': 'huizhan-hallD',
    'way/326732173': 'huizhan-big1',
    'way/326732174': 'huizhan-big2',
    'way/326732172': 'huizhan-big3',
    'way/1130611208': 'huizhan-theatre',
    'way/488160597': 'huizhan-comm',
}
STATION_BOX = (118.098, 24.473, 118.118, 24.488)
GAOQI_BOX = (118.108, 24.500, 118.145, 24.540)


def inside(lon, lat, box):
    return box[0] <= lon <= box[2] and box[1] <= lat <= box[3]


class Handler(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.rings = {}
        self.rail = []
        self.terminal = []

    def way(self, w):
        wid = f'way/{w.id}'
        tags = {t.k: t.v for t in w.tags}
        if wid in WANTED:
            try:
                coords = [[round(n.lon, 7), round(n.lat, 7)] for n in w.nodes]
            except osmium.InvalidLocationError:
                return
            self.rings[WANTED[wid]] = {'osmId': wid, 'name': tags.get('name', ''),
                                       'ring': coords}
        if tags.get('railway') in ('station', 'terminal') or tags.get('building') == 'train_station' or '航站楼' in tags.get('name', '') or '厦门站' in tags.get('name', ''):
            try:
                coords = [(n.lon, n.lat) for n in w.nodes]
            except osmium.InvalidLocationError:
                return
            if coords:
                cx = sum(p[0] for p in coords) / len(coords); cy = sum(p[1] for p in coords) / len(coords)
                if inside(cx, cy, STATION_BOX) or inside(cx, cy, GAOQI_BOX):
                    self.rail.append({'id': wid, 'name': tags.get('name', ''), 'tags': {k: v for k, v in tags.items() if k in ('railway', 'building', 'aeroway', 'name', 'height', 'public_transport')}, 'nodes': len(coords), 'center': [round(cx, 6), round(cy, 6)]})


if __name__ == '__main__':
    h = Handler()
    h.apply_file(PBF, locations=True, idx='flex_mem')
    out = {}
    for key, r in h.rings.items():
        ring = r['ring']
        xs = [p[0] for p in ring]; ys = [p[1] for p in ring]
        out[key] = {'osmId': r['osmId'], 'name': r['name'], 'nodes': len(ring),
                    'bboxMeters': [round((max(xs) - min(xs)) * 101310 * .6), round((max(ys) - min(ys)) * 111320 * .6)],
                    'ring': ring}
    print(json.dumps(out, ensure_ascii=False, indent=1)[:12000])
    print('=== rail/terminal features ===')
    for r in h.rail:
        print(json.dumps(r, ensure_ascii=False))
