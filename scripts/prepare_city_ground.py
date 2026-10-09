"""Disjoint land/park/water meshes: no infinite sea hidden under the whole city."""
import json
from pathlib import Path
import shapely
from shapely.geometry import Polygon,box
P=Path('public/city');c=json.loads((P/'city.json').read_text())
def poly(r):return shapely.make_valid(Polygon(r[0],r[1:]))
land=shapely.union_all([poly(r) for r in c['land']]);water=shapely.union_all([poly(r['rings']) for r in c['water']]);green=shapely.union_all([poly(r['rings']) for r in c['green']]).intersection(land).difference(water)
# Xiamen is an island city: no mainland backdrop — open sea surrounds the
# islands and the horizon is water until the far-shore layer lands (M2).
extent=c['meta']['extent'];sea=box(extent[0]-9000,-16000,extent[2]+9000,extent[3]+16000).difference(land)
layers={'land':land.difference(water).difference(green),'park':green,'water':water.intersection(land),'sea':sea}
out={}
for key,g in layers.items():
 out[key]=[[[round(x,4),round(y,4)] for x,y in list(t.exterior.coords)[:3]] for t in shapely.constrained_delaunay_triangles(g).geoms if t.geom_type=='Polygon'];print(key,len(out[key]))
(P/'ground-surfaces.json').write_text(json.dumps(out,separators=(',',':')))
assert land.intersection(sea).area<.01
