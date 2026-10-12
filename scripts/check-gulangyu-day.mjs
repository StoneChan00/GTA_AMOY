/** Daylight verification: Gulangyu red roofs in day mode + strict road-tile audit against the Gulangyu land bbox. */
import {chromium} from 'playwright';
import fs from 'node:fs';
fs.mkdirSync('output/amoy/gulangyu-fix',{recursive:true});
const browser=await chromium.launch({channel:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1600,height:900}});
await page.goto('http://127.0.0.1:5173/?quality=low',{waitUntil:'domcontentloaded'});
let booted=false;
for(let i=0;i<150;i++){await page.waitForTimeout(2000);if(await page.evaluate(()=>!!(window.__SHENCHENGJI_CITY__?.ready))){booted=true;console.log('ready after',i*2,'s');break;}}
if(!booted){console.error('BOOT FAILED');await browser.close();process.exit(1);}
await page.waitForTimeout(6000);
await page.evaluate(()=>{window.__SHENCHENGJI_CITY__.world.setLightMode('day');});
await page.waitForTimeout(2500);

// Gulangyu land bbox (from city.json land[0]): x[-4076,-2916] z[-3113,-1931]
const audit=await page.evaluate(()=>{
  const w=window.__SHENCHENGJI_CITY__.world;
  const G={x0:-4076,x1:-2916,z0:-3113,z1:-1931};
  const roads=[],hits=[];
  for(const m of w.scene.meshes){
    if(!m.getTotalVertices())continue;
    const b=m.getBoundingInfo().boundingBox;
    const bx={x0:b.minimumWorld.x,x1:b.maximumWorld.x,z0:b.minimumWorld.z,z1:b.maximumWorld.z};
    const overlapsG=bx.x1>G.x0&&bx.x0<G.x1&&bx.z1>G.z0&&bx.z0<G.z1;
    if(!overlapsG)continue;
    const fullyInside=bx.x0>=G.x0&&bx.x1<=G.x1&&bx.z0>=G.z0&&bx.z1<=G.z1;
    if(/^roads?[-_]/i.test(m.name)||/road|street/i.test(m.name)){
      roads.push({name:m.name,verts:m.getTotalVertices(),bbox:bx,fullyInside});
    }
    hits.push({name:m.name,verts:m.getTotalVertices(),fullyInside});
  }
  const roadsOnGulangyu=roads.filter(r=>r.fullyInside);
  const roadTilesNear=roads.map(r=>r.name+'['+(r.fullyInside?'INSIDE':'near')+']');
  const buildings=hits.filter(h=>/^block_/.test(h.name)&&h.fullyInside);
  return {roadsOnGulangyu,roadTilesNear,buildingMeshes:buildings.length,buildingVerts:buildings.reduce((s,b)=>s+b.verts,0),totalNear:hits.length};
});
console.log('== road meshes overlapping Gulangyu land bbox ==');
for(const n of audit.roadTilesNear)console.log(' ',n);
console.log('road meshes FULLY INSIDE Gulangyu:',audit.roadsOnGulangyu.length,JSON.stringify(audit.roadsOnGulangyu.map(r=>r.name)));
console.log('building meshes fully inside Gulangyu:',audit.buildingMeshes,'verts:',audit.buildingVerts);

const GX=-3143,GZ=-2698;
const shots=[
  {name:'day-gulangyu-aerial',x:GX,z:GZ,targetHeight:80,distance:2400,elevation:.55,angle:-1.2},
  {name:'day-gulangyu-close',x:GX,z:GZ,targetHeight:40,distance:1100,elevation:.22,angle:.7},
  {name:'day-west-gulangyu-after',x:400,z:-1500,targetHeight:80,distance:5600,elevation:.35,angle:-1.20},
];
for(const s of shots){
  await page.evaluate(m=>{
    const w=window.__SHENCHENGJI_CITY__.world;
    w.enterPhoto({id:'probe-'+m.name,name:'probe',x:m.x,z:m.z,height:0,area:'probe',excludeRadius:0,arrival:[m.x,m.z],
     photoDistance:m.distance,photoElevation:m.elevation,photoAngle:m.angle,photoTargetHeight:m.targetHeight});
  },s);
  await page.waitForTimeout(2500);
  await page.screenshot({path:'output/amoy/gulangyu-fix/'+s.name+'.png'});
  console.log('shot:',s.name);
}
await browser.close();
