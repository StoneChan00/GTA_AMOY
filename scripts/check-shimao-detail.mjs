/** Shimao twin-sails visual verification: detail meshes in, M1 model out, OSM towers replaced, sails readable. */
import {chromium} from 'playwright';
import fs from 'node:fs';
fs.mkdirSync('output/amoy/shimao-detail',{recursive:true});
const browser=await chromium.launch({channel:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1600,height:900}});
await page.goto('http://127.0.0.1:5173/?quality=low',{waitUntil:'domcontentloaded'});
let booted=false;
for(let i=0;i<150;i++){await page.waitForTimeout(2000);if(await page.evaluate(()=>!!(window.__SHENCHENGJI_CITY__?.ready))){booted=true;console.log('ready after',i*2,'s');break;}}
if(!booted){console.error('BOOT FAILED');await page.screenshot({path:'output/amoy/shimao-detail/boot-fail.png'});await browser.close();process.exit(1);}
await page.waitForTimeout(6000);
await page.evaluate(()=>{window.__SHENCHENGJI_CITY__.world.setLightMode('day');});
await page.waitForTimeout(2500);

const audit=await page.evaluate(()=>{
  const w=window.__SHENCHENGJI_CITY__.world;
  const detail=[],legacy=[];
  for(const m of w.scene.meshes){
    if(!m.getTotalVertices())continue;
    if(m.name.startsWith('detail_shimao_'))detail.push({name:m.name,verts:m.getTotalVertices(),yMax:+m.getBoundingInfo().boundingBox.maximumWorld.y.toFixed(1)});
    if(m.name.startsWith('landmark_shimao_'))legacy.push(m.name);
  }
  const lm=w.data.landmarks.find(l=>l.id==='shimao');
  return {detail,legacyCount:legacy.length,legacyNames:legacy.slice(0,4),
    landmark:{x:+lm.x.toFixed(0),z:+lm.z.toFixed(0),height:+lm.height.toFixed(0),arrival:lm.arrival,detailCollision:lm.detailCollision,area:lm.area},
    blockedAtTowers:null};
});
console.log('== detail_shimao meshes ==');for(const d of audit.detail)console.log(' ',d.name,'verts='+d.verts,'yMax='+d.yMax);
console.log('legacy landmark_shimao_* remaining:',audit.legacyCount,audit.legacyNames);
console.log('shimao landmark record:',JSON.stringify(audit.landmark));

const shots=[
  // SW over the strait looking NE at both sails (the Gulangyu postcard view)
  {name:'day-sails-from-strait',x:-2200,z:-3118,targetHeight:100,distance:1350,elevation:.22,angle:-2.05},
  // closer from the south (baypark side), towers fill the frame
  {name:'day-sails-close',x:-2200,z:-3118,targetHeight:95,distance:560,elevation:.16,angle:-1.25},
  // crown-focused: from the SSW, camera above the strait looking up the masts
  {name:'day-crown-focus',x:-2200,z:-3118,targetHeight:135,distance:520,elevation:.10,angle:-1.9},
  // street-ish from 大学路 NE side looking SW over the podium
  {name:'day-podium-street',x:-2196,z:-3110,targetHeight:20,distance:420,elevation:.05,angle:.55},
];
for(const s of shots){
  await page.evaluate(m=>{
    const w=window.__SHENCHENGJI_CITY__.world;
    w.enterPhoto({id:'probe-'+m.name,name:'probe',x:m.x,z:m.z,height:0,area:'probe',excludeRadius:0,arrival:[m.x,m.z],
     photoDistance:m.distance,photoElevation:m.elevation,photoAngle:m.angle,photoTargetHeight:m.targetHeight});
  },s);
  await page.waitForTimeout(2500);
  await page.screenshot({path:'output/amoy/shimao-detail/'+s.name+'.png'});
  console.log('shot:',s.name);
}
await browser.close();
