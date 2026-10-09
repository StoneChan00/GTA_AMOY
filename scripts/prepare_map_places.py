"""GTA_AMOY M1 map-places catalog: OSM-derived POI/park/district entries with
the same schema as the upstream data/map-places.json. Every entry keeps its
OSM source URL and the game x/z uses the exact wgs84ToMap arithmetic so the
catalog test stays a coordinate-conversion contract.
"""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
ORIGIN=[118.12,24.485]; SCALE=.60
def to_map(lon,lat):return ((lon-ORIGIN[0])*101310*SCALE,(lat-ORIGIN[1])*111320*SCALE)
places=[]
def add(pid,name,category,kind,lon,lat,provider='OpenStreetMap',osm_type='node',osm_id=0,method='OSM node coordinates, WGS84'):
 x,z=to_map(lon,lat)
 places.append({'id':pid,'name':name,'category':category,'kind':kind,'x':x,'z':z,'lon':lon,'lat':lat,
  'source':{'provider':provider,'id':f'osm:{osm_type}/{osm_id}','url':f'https://www.openstreetmap.org/{osm_type}/{osm_id}','file':'data/processed/xiamen_study/pois.geojson','coordinateMethod':method}})
# Districts covering the playable island (relation ids from OSM).
for pid,name,lon,lat,rid in [('district-siming','思明区',118.082,24.449,3892702),('district-huli','湖里区',118.146,24.516,3892704)]:
 x,z=to_map(lon,lat)
 places.append({'id':pid,'name':name,'category':'district','kind':'city','x':x,'z':z,'lon':lon,'lat':lat,
  'source':{'provider':'OpenStreetMap','id':f'osm:relation/{rid}','url':f'https://www.openstreetmap.org/relation/{rid}','file':'data/processed/xiamen_study/pois.geojson','coordinateMethod':'OSM administrative centroid, WGS84'}})
pois=json.loads((R/'data/processed/xiamen_study/pois.geojson').read_text(encoding='utf-8'))['features']
count=0
for f in pois:
 t=f['properties']['tags'];name=f['properties'].get('name') or ''
 if not name:continue
 g=f['geometry'];lon,lat=g['coordinates'][0],g['coordinates'][1]
 typ,oid=f['properties']['osm_type'],f['properties']['osm_id']
 if t.get('railway')=='subway_entrance':
  add(f'subway-{typ}-{oid}',name,'transport','subway_entrance',lon,lat,osm_type=typ,osm_id=oid)
 elif t.get('tourism') in ('attraction','viewpoint','artwork'):
  add(f'see-{typ}-{oid}',name,'landmark',t['tourism'],lon,lat,osm_type=typ,osm_id=oid)
 elif t.get('amenity') in ('bench','drinking_water','toilets','bicycle_rental','shelter'):
  continue
 else:
  add(f'poi-{typ}-{oid}',name,'place','named_poi',lon,lat,osm_type=typ,osm_id=oid)
 count+=1
green=json.loads((R/'data/processed/xiamen_study/green.geojson').read_text(encoding='utf-8'))['features']
for f in green:
 name=f['properties'].get('name') or ''
 if not name:continue
 g=f['geometry']
 if g['type']!='Polygon':continue
 ring=g['coordinates'][0]
 lon=sum(p[0] for p in ring[:-1])/len(ring[:-1]);lat=sum(p[1] for p in ring[:-1])/len(ring[:-1])
 typ,oid=f['properties']['osm_type'],f['properties']['osm_id']
 add(f'park-{typ}-{oid}',name,'park','park',lon,lat,osm_type=typ,osm_id=oid,method='OSM polygon centroid, WGS84')
catalog={'schemaVersion':1,'originWGS84':ORIGIN,'source':'OpenStreetMap contributors (ODbL), xiamen_study extract 2026-10-07','places':places}
(R/'data/map-places.json').write_text(json.dumps(catalog,ensure_ascii=False),encoding='utf-8')
print('places',len(places),'(pois',count,')')
