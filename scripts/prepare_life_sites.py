"""GTA_AMOY M1 life-sites staging: three fictional community service spots
snapped to real road geometry (same schema as the upstream life-sites.json).
The site buildings themselves are runtime hubs; coordinates are game staging,
not claimed surveyed POIs.
"""
import json, math
from pathlib import Path
from shapely.geometry import LineString, Point
R=Path(__file__).resolve().parents[1]; P=R/'public/city'
c=json.loads((P/'city.json').read_text())
ORIGIN=[118.12,24.485]; SCALE=.60
def project(lon,lat):return ((lon-ORIGIN[0])*101310*SCALE,(lat-ORIGIN[1])*111320*SCALE)
specs=[
 ('hub','会展生活驿站',118.163,24.460),
 ('office','五缘湾商务驿站',118.150,24.533),
 ('workshop','白鹭洲养护站',118.093,24.481)]
roads=[(LineString(r['points']),r) for r in c['roads'] if len(r['points'])>1]
sites=[]
for id,name,lon,lat in specs:
 p=Point(*project(lon,lat))
 line,r=min(roads,key=lambda lr:lr[0].distance(p))
 t=line.project(p);q=line.interpolate(t);q2=line.interpolate(min(line.length,t+4))
 yaw=math.atan2(q2.x-q.x,q2.y-q.y)
 nx,ny=-math.cos(yaw),math.sin(yaw)
 side=1
 cx,cy=q.x+nx*(r['width']/2+4.5)*side,q.y+ny*(r['width']/2+4.5)*side
 foot=[[cx-5,cy-5],[cx+5,cy-5],[cx+5,cy+5],[cx-5,cy+5]]
 sites.append({'id':id,'name':name,'x':round(cx,4),'z':round(cy,4),'heading':round(yaw,6),
  'arrival':[round(q.x,2),round(q.y,2)],'yaw':round(yaw,6),'road':r['name'],'roadWidth':r['width'],
  'footprint':[[round(v,4) for v in pt] for pt in foot]})
(P/'life-sites.json').write_text(json.dumps({'version':1,'source':'Original fictional community services on mapped vacant roadside plots','sites':sites},ensure_ascii=False,indent=2))
print(json.dumps(sites,ensure_ascii=False,indent=1))
