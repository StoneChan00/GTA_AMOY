/** Batch visual verification for the M3 landmark wave: every detail object
 * in, its OSM base blocks out, records moved, and one named screenshot each. */
import {chromium} from 'playwright';
import fs from 'node:fs';
fs.mkdirSync('output/amoy/landmarks-v1',{recursive:true});
const browser=await chromium.launch({channel:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1440,height:810}});
await page.goto('http://127.0.0.1:5173/?quality=low',{waitUntil:'domcontentloaded'});
let booted=false;
for(let i=0;i<180;i++){await page.waitForTimeout(2000);if(await page.evaluate(()=>!!(window.__SHENCHENGJI_CITY__?.ready))){booted=true;console.log('ready after',i*2,'s');break;}}
if(!booted){console.error('BOOT FAILED');await page.screenshot({path:'output/amoy/landmarks-v1/boot-fail.png'});await browser.close();process.exit(1);}
await page.waitForTimeout(5000);

const audit=await page.evaluate(()=>{
  const w=window.__SHENCHENGJI_CITY__.world;
  const groups={};
  for(const m of w.scene.meshes){
    if(!m.getTotalVertices())continue;
    const pfx=m.name.split('_').slice(0,2).join('_');
    if(!m.name.startsWith('detail_'))continue;
    const g=groups[pfx]??=({meshes:0,verts:0,min:[1e9,1e9,1e9],max:[-1e9,-1e9,-1e9]});
    g.meshes++;g.verts+=m.getTotalVertices();
    const b=m.getBoundingInfo().boundingBox;
    for(let i=0;i<3;i++){g.min[i]=Math.min(g.min[i],b.minimumWorld.asArray()[i]);g.max[i]=Math.max(g.max[i],b.maximumWorld.asArray()[i]);}
  }
  const excluded=w.detailManifest.baseBuildingIds.filter(id=>w.data.buildings.some(b=>b.id===id)).length;
  return {groups,baseIds:w.detailManifest.baseBuildingIds.length,stillPresent:excluded,
    landmarks:w.detailManifest.landmarks.map(l=>({id:l.id,x:Math.round(l.x),z:Math.round(l.z),h:Math.round(l.height),area:l.area}))};
});
console.log('== detail groups ==');
for(const[k,g]of Object.entries(audit.groups))console.log(' ',k,'meshes='+g.meshes,'verts='+g.verts,'bbox='+JSON.stringify(g.min.map(Math.round))+'..'+JSON.stringify(g.max.map(Math.round)));
console.log('baseBuildingIds kept-but-present (should be 0):',audit.stillPresent,'/',audit.baseIds);
console.log('records:',JSON.stringify(audit.landmarks));

await page.evaluate(()=>{const w=window.__SHENCHENGJI_CITY__.world;w.toggleAerial();w.setLightMode('day');
  window.__shot=(cx,cy,cz,tx,ty,tz)=>{const ob=w.observer;ob.focus={x:tx,y:ty,z:tz};
    ob.yaw=Math.atan2(tx-cx,tz-cz);ob.pitch=Math.asin(Math.max(-1,Math.min(1,(cy-ty)/Math.hypot(tx-cx,ty-cy,tz-cz))));
    ob.distance=Math.hypot(tx-cx,ty-cy,tz-cz);};
  for(const rtt of [w.mirror,w.waterMirror]){rtt.refreshRate=1;rtt.resetRefreshCounter();}});

const shots=[
  ['riguangyan',-3509,70,-2600,-3510,35,-2696],
  ['riguangyan-wide',-3300,150,-2350,-3510,30,-2696],
  ['bagua',-3446,45,-2250,-3446,10,-2329],
  ['xmu-rows',-1770,110,-3380,-1800,20,-3030],
  ['xmu-jiannan',-1560,70,-3320,-1665,14,-3205],
  ['gaoqi-t4',1310,80,3900,1310,12,4171],
  ['gaoqi-t3',600,90,3350,410,10,3510],
  ['xiamenzhan',-648,55,-750,-648,10,-860],
  ['huizhan',3050,130,-1060,3530,14,-1068],
];
for(const[name,cx,cy,cz,tx,ty,tz]of shots){
  await page.evaluate(([n,a,b,c,d,e,f])=>window.__shot(a,b,c,d,e,f),[name,cx,cy,cz,tx,ty,tz]);
  await page.waitForTimeout(2600);
  await page.screenshot({path:'output/amoy/landmarks-v1/'+name+'.png'});
  console.log('shot:',name);
}
await browser.close();
