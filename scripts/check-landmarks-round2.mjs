/** Round-2 visual verification: 4 new landmark objects (wuyuan marina / bailu
 * statue / yundang fountain / shapowei boats), the 4 pending named acceptances
 * (bagua / xiamenzhan / gaoqi-T3 / huizhan) and the heritage height-cap
 * headline check (Gulangyu + XMU low-rise fabric under the landmark models). */
import {chromium} from 'playwright';
import fs from 'node:fs';
fs.mkdirSync('output/amoy/landmarks-v2',{recursive:true});
const browser=await chromium.launch({channel:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1440,height:810}});
await page.goto('http://127.0.0.1:5173/?quality=low',{waitUntil:'domcontentloaded'});
let booted=false;
for(let i=0;i<180;i++){await page.waitForTimeout(2000);if(await page.evaluate(()=>!!(window.__SHENCHENGJI_CITY__?.ready))){booted=true;console.log('ready after',i*2,'s');break;}}
if(!booted){console.error('BOOT FAILED');await page.screenshot({path:'output/amoy/landmarks-v2/boot-fail.png'});await browser.close();process.exit(1);}
await page.waitForTimeout(5000);

const audit=await page.evaluate(()=>{
  const w=window.__SHENCHENGJI_CITY__.world;
  const groups={};
  for(const m of w.scene.meshes){
    if(!m.getTotalVertices()||!m.name.startsWith('detail_'))continue;
    const pfx=m.name.split('_').slice(0,2).join('_');
    const g=groups[pfx]??=({meshes:0,verts:0,min:[1e9,1e9,1e9],max:[-1e9,-1e9,-1e9]});
    g.meshes++;g.verts+=m.getTotalVertices();
    const b=m.getBoundingInfo().boundingBox;
    for(let i=0;i<3;i++){g.min[i]=Math.min(g.min[i],b.minimumWorld.asArray()[i]);g.max[i]=Math.max(g.max[i],b.maximumWorld.asArray()[i]);}
  }
  const excluded=w.detailManifest.baseBuildingIds.filter(id=>w.data.buildings.some(b=>b.id===id)).length;
  return {groups,baseIds:w.detailManifest.baseBuildingIds.length,stillPresent:excluded,
    landmarks:w.detailManifest.landmarks.map(l=>({id:l.id,x:Math.round(l.x),z:Math.round(l.z),h:Math.round(l.height)}))};
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
  // round-2 objects
  ['wuyuan-marina-air',3230,130,3230,3420,6,3390],
  ['wuyuan-marina-close',3300,10,3310,3430,2,3400],
  ['bailu-statue',-1880,18,-570,-1881,5,-620],
  ['bailu-statue-wide',-1780,60,-520,-1900,6,-620],
  ['yundang-fountain',-2100,36,-560,-2101,2,-634],
  ['yundang-lake-air',-1900,250,-500,-2100,0,-640],
  ['shapowei-boats-air',-2400,55,-2790,-2350,2,-2880],
  ['shapowei-boats-close',-2320,12,-2830,-2360,1,-2890],
  // pending named acceptances from round 1 (heritage caps now un-bury them)
  ['bagua',-3446,45,-2250,-3446,10,-2329],
  ['bagua-gulangyu-fabric',-3200,150,-2150,-3450,25,-2500],
  ['xiamenzhan',-648,55,-750,-648,10,-860],
  ['gaoqi-t3',600,90,3350,410,10,3510],
  ['huizhan',3050,130,-1060,3530,14,-1068],
  // heritage height-cap headline checks
  ['gulangyu-heritage-air',-3150,230,-2450,-3500,35,-2700],
  ['gulangyu-heritage-strait',-2400,90,-2700,-3400,30,-2650],
  ['xmu-heritage-air',-1900,150,-3080,-1800,25,-3050],
];
for(const[name,cx,cy,cz,tx,ty,tz]of shots){
  await page.evaluate(([n,a,b,c,d,e,f])=>window.__shot(a,b,c,d,e,f),[name,cx,cy,cz,tx,ty,tz]);
  await page.waitForTimeout(2600);
  await page.screenshot({path:'output/amoy/landmarks-v2/'+name+'.png'});
  console.log('shot:',name);
}
await browser.close();
