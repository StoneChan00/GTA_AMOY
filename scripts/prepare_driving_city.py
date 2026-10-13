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
# Gulangyu (1.9 km²) sits far below the 0.004°² filter but belongs with the
# island set per the design comment above: union its cell explicitly when the
# coastline closes around it, so the pedestrian island renders with land,
# buildings and green instead of a lone map marker.
_gy=Point(118.0683,24.4446)
_gy_cell=next((p for p in cells if p.contains(_gy) and not p.intersects(bounds.boundary)),None)
if _gy_cell is not None and not any(p.equals(_gy_cell) for p in islands):islands.append(_gy_cell)
anchor=Point(118.128,24.490)
if not any(p.contains(anchor) for p in islands):
 # Coastline topology connected the island to the mainland (e.g. a mapped
 # causeway); clip that cell back to the island's enclosing box at the strait.
 big=max((p for p in cells if p.contains(anchor)),key=lambda p:p.area,default=None)
 if big is None:raise SystemExit('coastline does not close around Xiamen Island; check source data')
 islands=[big.intersection(box(118.055,24.415,118.195,24.565))]
main=max(islands,key=lambda p:p.area)
main_land=transform(project,main)
# Car roads belong to the main island only: Gulangyu is a pedestrian island in
# reality, and its footpath-derived service lanes would strand the 鼓浪屿
# landmark arrival on a road graph island with no bridge to the mainland.
island_union=unary_union(islands)
# Only island shores get the runtime promenade; mainland coastlines stay bare.
coasts=[l for l in coasts if l.geom_type=='LineString' and island_union.distance(l)<.002]
land=transform(project,island_union).simplify(.5,preserve_topology=True)
landparts=parts(land,'Polygon')
# --------------------------------------------------------------- heritage
# Heritage low-rise height policy (real metres; basis=reported):
# - Gulangyu (UNESCO World Heritage historic town): villa fabric is "普遍为
#   二三层，有的达到四层" (鼓浪屿管委会官网 2009), 2-4 storeys on 300-1200 m²
#   footprints (Buildings 2023, 13, 229), and the tallest old villa is the
#   26.6 m 八卦楼 (厦门日报 2024-09-26); redevelopment "一般不超过相邻历史风貌
#   建筑的平均基本高度" (鼓浪屿历史风貌建筑保护规划). The citywide typology
#   estimate (median 23.4 game m) buries those low-rise streets and the
#   hand-modelled landmarks behind generic towers, so untagged blocks here
#   draw from a 2-4 storey range instead.
# - XMU Siming campus (OSM way/154986493; ring in data/landmarks/heritage-
#   zones.json): Jiageng core is 2-3 storeys with 21-25 m rooflines (群贤 3F
#   通高21m, 建南 5F 通高25m, 厦大新闻网/资产与后勤处), 1950s dorms 3F 局部5F,
#   late-20th-c blocks 5-6F ≈ 15-18 m; the campus sits inside the 鼓浪屿-万石山
#   scenic control zone (厦大基建处 2024). Untagged blocks draw from 3-6 storeys.
# Tagged heights (osm_height / building:levels) clamp to the zone cap — OSM
# tags in these zones are unvetted and the conservation policy wins. Modelled
# landmarks (八卦楼/群贤群/颂恩楼…) keep their own true heights via
# landmark-detail.json and baseBuildingIds.
heritage=[]
if _gy_cell is not None:
 heritage.append((transform(project,_gy_cell).simplify(2,preserve_topology=True),15.0,(7,10,13,15)))
_hz=json.loads((R/'data/landmarks/heritage-zones.json').read_text(encoding='utf-8'))
heritage.append((transform(project,shape({'type':'Polygon','coordinates':[_hz['xmuCampus']['ring']]})).simplify(2,preserve_topology=True),18.0,(10,13,16,18)))
allowed={'trunk','primary','secondary','tertiary','residential','unclassified','service','trunk_link','primary_link','secondary_link','tertiary_link'}
roads=[]
for f in load('roads'):
 t=f['properties']['tags'];k=t.get('highway');g=shape(f['geometry'])
 if k not in allowed or not g.intersects(bounds) or t.get('access') in ['private','no'] or t.get('motor_vehicle')=='no':continue
 # Flatten grade separation consistently, including tunnel centerlines. No
 # claim of surveyed bridge/tunnel reconstruction in this iteration.
 g=transform(project,g.intersection(bounds)).intersection(main_land.buffer(12))
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
# Arrival roads must sit on the largest connected component: marina/quay and
# campus service lanes are drive-isolated and would strand the travel teleport
# (city.test.ts routes every mark continuously from spawn). Union-find over
# road vertices on a 1.5 m grid approximates the navigation graph's main
# component the same way build_landmark_details.arrival does.
_parent=list(range(len(roads)))
def _find(a):
 while _parent[a]!=a:_parent[a]=_parent[_parent[a]];a=_parent[a]
 return a
_node_roads={}
for _i,_r in enumerate(roads):
 for _p in _r['points']:_node_roads.setdefault((round(_p[0]/1.5),round(_p[1]/1.5)),[]).append(_i)
for _rs in _node_roads.values():
 for _a in _rs[1:]:_parent[_find(_rs[0])]=_find(_a)
_comp_size=Counter(_find(_i) for _i in range(len(roads)))
_main_root=max(_comp_size,key=_comp_size.get)
mainlines=[roadlines[_i] for _i in range(len(roads)) if _find(_i)==_main_root]
maintree=STRtree(mainlines)
landmarks=[
 # Evidence-corrected anchors (see data/landmarks/*.json specs and the
 # landmark-detail manifest). M1 estimates drifted up to 2.5 km: shimao sat in
 # the strait off 演武大桥, huizhan 2.5 km SW, xiamenzhan 700 m N, gaoqi
 # mid-field. Every excludeRadius is now 0 — site clearing is owned by the
 # landmark workflow (landmark-detail.json baseBuildingIds via
 # extend_landmark_exclusions.py), so a mislocated radius can never again
 # remove ordinary blocks: M1's shimao radius-70 (= 42 game m) sat harmlessly
 # in the sea, but placed on the corrected 沙坡尾 site it would have eaten
 # 厦港老城 blocks. xiamenzhan/yundang keep their M1 spots: they anchor the
 # locked M3 湖滨东路 street corridor (src/city-bamboo-corridor.ts
 # BAMBOO_CORRIDOR origin/talent are test-locked there); the landmark
 # manifest owns the corrected station position and the round-2 yundang
 # spec owns the lake anchor.
 ('shimao','世茂海峡大厦 · 双子塔',118.08379,24.43827,300,'思明 · 沙坡尾',0),
 ('xmu','厦门大学 · 嘉庚建筑群',118.0907,24.4392,85,'思明 · 厦大',0),
 ('gulangyu','鼓浪屿',118.0683,24.4446,0,'思明 · 鼓浪屿',0),
 ('xiamenzhan','厦门站',118.1075,24.4775,25,'思明 · 厦禾路',0),
 ('yundang','筼筜湖',118.0946,24.4832,0,'思明 · 筼筜湖',0),
 ('bailu','白鹭洲公园 · 白鹭女神',118.087126,24.476662,14,'思明 · 白鹭洲',0),
 ('gaoqi','高崎机场 T4',118.142327,24.547275,39,'湖里 · 高崎机场',0),
 ('wuyuan','五缘湾 · 游艇港',118.175692,24.535432,0,'湖里 · 五缘湾',0),
 ('huizhan','厦门国际会展中心',118.177954,24.468992,42.6,'思明 · 前埔会展',0),
 ('shapowei','沙坡尾 · 避风坞',118.081863,24.441888,0,'思明 · 沙坡尾',0)]
marks=[]
for id,name,lon,lat,h,area,radius in landmarks:
 x,z=project(lon,lat); p=Point(x,z)
 # Arrival point lies on a driveable, connected surface, never at the centre.
 ri=int(maintree.nearest(p));line=mainlines[ri];q=line.interpolate(line.project(p));dd=min(line.length,max(0,line.project(p))+4);p2=line.interpolate(dd)
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
  # Heritage low-rise policy (zone evidence at the heritage block above):
  # untagged estimates redraw from the zone's real storey range; tagged
  # values clamp to the zone cap.
  for hz_poly,hz_cap,hz_storeys in heritage:
   if hz_poly.contains(center):
    if status=='typology_estimate':h=rnd.choice(hz_storeys)*SCALE;status='heritage_estimate'
    else:h=min(h,hz_cap*SCALE)
    break
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
