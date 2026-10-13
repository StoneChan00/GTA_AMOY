"""Focused follow-up probe: all big buildings per site + named POIs + natural peaks.

Read-only evidence helper for landmark specs; run:
PYTHONUTF8=1 .venv/Scripts/python.exe scripts/query_osm_sites.py
"""
import json

import osmium

PBF = 'data/raw/fujian-latest.osm.pbf'

SITES = {
    'huizhan': (118.175, 24.450, 118.210, 24.475),
    'gaoqi': (118.100, 24.493, 118.145, 24.535),
    'xiamenzhan': (118.098, 24.473, 118.116, 24.488),
}
GULANGYU = (118.062, 24.440, 118.076, 24.454)
NAME_KEYS = ['日光岩', '八卦', '风琴', '英雄山', '钢琴', '皓月', '淑庄', '菽庄', '鼓浪']


def inside(lon, lat, box):
    return box[0] <= lon <= box[2] and box[1] <= lat <= box[3]


class Handler(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.buildings = {k: [] for k in SITES}
        self.gulangyu_named = []
        self.peaks = []

    def way(self, w):
        tags = {t.k: t.v for t in w.tags}
        if 'building' in tags or 'aeroway' in tags:
            try:
                coords = [(n.lon, n.lat) for n in w.nodes]
            except osmium.InvalidLocationError:
                return
            if not coords:
                return
            xs = [p[0] for p in coords]; ys = [p[1] for p in coords]
            cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
            span = ((max(xs) - min(xs)) * 101310 * .6, (max(ys) - min(ys)) * 111320 * .6)
            for site, box in SITES.items():
                if inside(cx, cy, box) and (span[0] * span[1] > 1500 or tags.get('name')):
                    self.buildings[site].append({
                        'id': f'way/{w.id}', 'name': tags.get('name', ''),
                        'b': tags.get('building') or tags.get('aeroway'),
                        'height': tags.get('height'), 'levels': tags.get('building:levels'),
                        'nodes': len(coords), 'bboxMeters': [round(v) for v in span],
                        'center': [round(cx, 6), round(cy, 6)],
                    })
            if inside(cx, cy, GULANGYU) and tags.get('name') and any(k in tags['name'] for k in NAME_KEYS):
                self.gulangyu_named.append({'id': f'way/{w.id}', 'name': tags['name'],
                                            'b': tags.get('building'), 'nodes': len(coords),
                                            'center': [round(cx, 6), round(cy, 6)]})

    def node(self, n):
        tags = {t.k: t.v for t in n.tags}
        name = tags.get('name', '')
        if tags.get('natural') in ('peak', 'volcano', 'crag', 'rock') or (name and any(k in name for k in NAME_KEYS)):
            if inside(n.location.lon, n.location.lat, GULANGYU):
                self.peaks.append({'id': f'node/{n.id}', 'name': name,
                                   'natural': tags.get('natural'), 'ele': tags.get('ele'),
                                   'center': [round(n.location.lon, 6), round(n.location.lat, 6)]})


if __name__ == '__main__':
    h = Handler()
    h.apply_file(PBF, locations=True, idx='flex_mem')
    for site, rows in h.buildings.items():
        print(f'=== {site} buildings ({len(rows)}) ===')
        for r in sorted(rows, key=lambda r: -(r['bboxMeters'][0] * r['bboxMeters'][1]))[:25]:
            print(json.dumps(r, ensure_ascii=False))
    print(f'=== gulangyu named ({len(h.gulangyu_named)}) ===')
    for r in h.gulangyu_named:
        print(json.dumps(r, ensure_ascii=False))
    print(f'=== gulangyu peaks/nodes ({len(h.peaks)}) ===')
    for r in h.peaks:
        print(json.dumps(r, ensure_ascii=False))
