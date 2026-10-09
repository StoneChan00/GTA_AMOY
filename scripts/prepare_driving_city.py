"""OSM-derived compressed Xiamen exterior world. WGS84 -> local meters * .60.
Roads are deliberately flattened for the first driving prototype. All output
is a derivative OSM database (ODbL); unknown building heights are estimates.
"""
import json, math, re, random
from pathlib import Path
from collections import Counter
from shapely.geometry import shape, box, Point, Polygon, LineString, mapping
from shapely.ops import unary_union, polygonize, transform
from shapely.strtree import STRtree
R=Path(__file__).resolve().parents[1]; OUT=R/'public/city';OUT.mkdir(exist_ok=True)
BBOX=[118.03,24.40,118.21,24.57]; SCALE=.60; ORIGIN=[118.12,24.485]
bounds=box(*BBOX)
def project(x,y,z=None):return ((x-ORIGIN[0])*101310*SCALE,(y-ORIGIN[1])*111320*SCALE)
def load(layer):return json.load(open(R/f'data/processed/xiamen_study/{layer}.geojson'))['features']
def parts(g,kind):
 if g.is_empty:return []
 if g.geom_type==kind:return [g]
 if hasattr(g,'geoms'):return [p for v in g.geoms for p in parts(v,kind)]
 return []
def coords(ring):return [[round(x,2),round(y,2)] for x,y in ring.coords]
def poly(g):return [coords(g.exterior),*[coords(r) for r in g.interiors]]
coasts=[shape(f['geometry']).intersection(bounds) for f in load('coastline') if shape(f['geometry']).intersects(bounds)]
# Xiamen is an island city: keep landmasses fully enclosed by the study box
# (Xiamen Island + Gulangyu); the mainland (Jimei/Haicang/Xiang'an) touches
# the bbox boundary and stays outside the playable area.
cells=polygonize(unary_union([bounds.boundary,*coasts]))
islands=[p for p in cells if p.area>.004 and not p.intersects(bounds.boundary)]
anchor=Point(118.128,24.490)
if not any(p.contains(anchor) for p in islands):
 # Coastline topology connected the island to the mainland (e.g. a mapped
 # causeway); clip that cell back to the island's enclosing box at the strait.
 big=max((p for p in cells if p.contains(anchor)),key=lambda p:p.area,default=None)
 if big is None:raise SystemExit('coastline does not close around Xiamen Island; check source data')
 islands=[big.intersection(box(118.055,24.415,118.195,24.565))]
island_union=unary_union(islands)
# Only island shores get the runtime promenade; mainland coastlines stay bare.
coasts=[l for l in coasts if l.geom_type=='LineString' and island_union.distance(l)<.002]
land=transform(project,island_union).simplify(.5,preserve_topology=True)
landparts=parts(land,'Polygon')
allowed={'trunk','primary','secondary','tertiary','residential','unclassified','service','trunk_link','primary_link','secondary_link','tertiary_link'}
roads=[]
for f in load('roads'):
 t=f['properties']['tags'];k=t.get('highway');g=shape(f['geometry'])
 if k not in allowed or not g.intersects(bounds) or t.get('access') in ['private','no'] or t.get('motor_vehicle')=='no':continue
 # Flatten grade separation consistently, including tunnel centerlines. No
 # claim of surveyed bridge/tunnel reconstruction in this iteration.
 g=transform(project,g.intersection(bounds)).intersection(land.buffer(12))
 try: lanes=max(1,min(5,int(t.get('lanes','2').split(';')[0])))
 except:lanes=2
 width=max(5.8,min(16,lanes*3.0))
 if k=='service':width=4.5
 # Xiamen OSM often lacks lanes tags on arterials; keep trunk/primary visually
 # wide enough for the coastal boulevard read.
 if k in ('trunk','primary'):width=max(10.5,width)
 for line in parts(g,'LineString'):
  line=line.simplify(.8)
  if line.length<3:continue
  roads.append({'id':f['id'],'name':t.get('name','支路'),'kind':k,'width':width,'oneway':t.get('oneway')=='yes','points':coords(line),'grade':t.get('layer','0')})
roadlines=[LineString(r['points']) for r in roads];tree=STRtree(roadlines)
landmarks=[
 # Coordinates are game-design estimates for M1 map marks (basis: estimated),
 # to be replaced by the landmark-reconstruction evidence workflow.
 ('shimao','世茂海峡大厦 · 双子塔',118.1187,24.4296,300,'思明 · 演武大桥',70),
 ('xmu','厦门大学',118.0897,24.4366,30,'思明 · 厦大',150),
 ('gulangyu','鼓浪屿',118.0683,24.4446,0,'思明 · 鼓浪屿',0),
 ('xiamenzhan','厦门站',118.1075,24.4775,25,'思明 · 厦门站',60),
 ('yundang','筼筜湖',118.0946,24.4832,0,'思明 · 筼筜湖',0),
 ('bailu','白鹭洲公园',118.0930,24.4800,0,'思明 · 白鹭洲',0),
 ('gaoqi','高崎机场 T4',118.1250,24.5075,30,'湖里 · 高崎',120),
 ('wuyuan','五缘湾',118.1530,24.5330,0,'湖里 · 五缘湾',0),
 ('huizhan','厦门国际会展中心',118.1630,24.4570,40,'思明 · 会展',100),
 ('shapowei','沙坡尾',118.0838,24.4340,0,'思明 · 沙坡尾',0)]
marks=[]
for id,name,lon,lat,h,area,radius in landmarks:
 x,z=project(lon,lat); p=Point(x,z)
 # Arrival point lies on a driveable surface, never at tower centre.
 ri=int(tree.nearest(p));line=roadlines[ri];q=line.interpolate(line.project(p));dd=min(line.length,max(0,line.project(p))+4);p2=line.interpolate(dd)
 if q.distance(p2)<1:p2=line.interpolate(max(0,line.project(p)-4))
 marks.append({'id':id,'name':name,'lon':lon,'lat':lat,'x':round(x,2),'z':round(z,2),'height':h*SCALE,'area':area,'excludeRadius':radius*SCALE,'arrival':[round(q.x,2),round(q.y,2)],'yaw':math.atan2(p2.x-q.x,p2.y-q.y)})
buildings=[];seen=set();est=Counter()
for f in load('buildings'):
 g=shape(f['geometry']);t=f['properties']['tags']
 if not g.intersects(bounds):continue
 g=transform(project,g.intersection(bounds)); center=g.centroid
 if not land.contains(center) or any(math.hypot(center.x-m['x'],center.y-m['z'])<m['excludeRadius'] for m in marks):continue
 if t.get('building') in ['roof','garage','garages','shed','construction'] or t.get('building:part'):continue
 for p in parts(g,'Polygon'):
  if p.area<22:continue
  seed=f['properties']['osm_id'];rnd=random.Random(seed)
  key=(round(p.centroid.x),round(p.centroid.y))
  if key in seen:continue
  seen.add(key)
  raw=t.get('height','');lev=t.get('building:levels','')
  try:h=float(re.search(r'[0-9.]+',raw).group())*SCALE;status='osm_height'
  except:
   try:h=float(lev)*3.3*SCALE;status='osm_levels_estimated'
   except:h=rnd.choice([18,24,30,39,54,72,96])*SCALE;status='typology_estimate'
  h=max(5,min(290,h));est[status]+=1
  # Preserve footprint shape, reserve pavement clearance where the compressed
  # real streets require it. Reject clipped slivers instead of blocking roads.
  near=tree.query(p.buffer(12)); buffers=[roadlines[i].buffer(roads[int(i)]['width']/2+2.0) for i in near]
  if buffers:p=p.difference(unary_union(buffers))
  for pp in parts(p,'Polygon'):
   if pp.area<20:continue
   pp=pp.simplify(.4)
   typ='office' if h>48 or t.get('building') in ['commercial','office'] else 'residential'
   buildings.append({'id':f['id'],'name':t.get('name',''),'rings':poly(pp),'height':round(h,1),'heightSource':status,'style':typ,'seed':seed})
green=[];water=[]
for layer,dest in [('green',green),('water',water)]:
 for f in load(layer):
  g=shape(f['geometry']);t=f['properties']['tags']
  if not g.intersects(bounds):continue
  if layer=='water' and t.get('natural')=='wetland':continue
  g=transform(project,g.intersection(bounds)).intersection(land)
  for p in parts(g,'Polygon'):
   if p.area<180:continue
   dest.append({'name':t.get('name',''),'rings':poly(p.simplify(1))})
spawnpoint=Point(*project(118.166,24.459))
# Pick an Island Ring Road (环岛干道/环岛东路) segment beside the convention
# centre so the drive opens with the strait on one side and twin towers in reach.
choices=[i for i,r in enumerate(roads) if '环岛' in r['name'] and '辅' not in r['name'] and r['kind'] in ['trunk','primary']]
si=min(choices,key=lambda i:roadlines[i].distance(spawnpoint));sl=roadlines[si];sp=sl.interpolate(sl.project(spawnpoint))
# Face along the chosen ring-road segment instead of an arbitrary compass
# heading, so the car opens on the boulevard instead of driving off it.
_t=sl.project(spawnpoint);_q2=sl.interpolate(min(sl.length,_t+4));yaw=math.atan2(_q2.x-sp.x,_q2.y-sp.y)
metadata={'version':'0.2','source':'OpenStreetMap contributors / Geofabrik Fujian extract (OSM-FR mirror) 2026-10-08','license':'ODbL-1.0','bboxWGS84':BBOX,'originWGS84':ORIGIN,'horizontalScale':SCALE,'verticalScale':SCALE,'coordinateSystem':'local east/north; equirectangular at Xiamen latitude (111320*cos(24.485°)≈101310), metres scaled 0.60','roadTreatment':'prototype roads flattened; one-way tags kept but arcade driving unrestricted','heightStatus':dict(est),'counts':{'roads':len(roads),'buildings':len(buildings),'green':len(green),'water':len(water),'landmarks':len(marks)},'extent':[round(v,2) for v in land.bounds]}
city={'meta':metadata,'land':[poly(p) for p in landparts],'coast':[coords(transform(project,l).simplify(.6)) for l in coasts if l.geom_type=='LineString'],'roads':roads,'buildings':buildings,'green':green,'water':water,'landmarks':marks,'spawn':{'x':round(sp.x,2),'z':round(sp.y,2),'yaw':yaw,'road':roads[si]['name']}}
(OUT/'city.json').write_text(json.dumps(city,ensure_ascii=False,separators=(',',':')))
(OUT/'metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2))
print(json.dumps(metadata,ensure_ascii=False,indent=2));print('spawn',city['spawn']);print('bytes',(OUT/'city.json').stat().st_size)
