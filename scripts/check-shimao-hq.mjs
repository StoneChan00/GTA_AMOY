/** Shimao v2 decisive verification: high quality, orthogonal side profile + top-down footprint. */
import {chromium} from 'playwright';
import fs from 'node:fs';
fs.mkdirSync('output/amoy/shimao-detail',{recursive:true});
const browser=await chromium.launch({channel:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1600,height:900}});
await page.goto('http://127.0.0.1:5173/?quality=high',{waitUntil:'domcontentloaded'});
let booted=false;
for(let i=0;i<150;i++){await page.waitForTimeout(2000);if(await page.evaluate(()=>!!(window.__SHENCHENGJI_CITY__?.ready))){booted=true;console.log('ready after',i*2,'s');break;}}
if(!booted){console.error('BOOT FAILED');await page.screenshot({path:'output/amoy/shimao-detail/hq-boot-fail.png'});await browser.close();process.exit(1);}
await page.waitForTimeout(8000);
await page.evaluate(()=>{window.__SHENCHENGJI_CITY__.world.setLightMode('day');});
await page.waitForTimeout(2500);
const shots=[
  // side profile from the south-east, perpendicular to the splay axis
  {name:'hq-side-profile',x:-2200,z:-3118,targetHeight:85,distance:460,elevation:.26,angle:-2.39},
  // end-on from the water SW, the Gulangyu postcard direction
  {name:'hq-end-on',x:-2200,z:-3118,targetHeight:95,distance:520,elevation:.13,angle:-.98},
  // top-down footprint read
  {name:'hq-topdown',x:-2200,z:-3118,targetHeight:40,distance:1000,elevation:.78,angle:-2.0},
];
for(const s of shots){
  await page.evaluate(m=>{
    const w=window.__SHENCHENGJI_CITY__.world;
    w.enterPhoto({id:'probe-'+m.name,name:'probe',x:m.x,z:m.z,height:0,area:'probe',excludeRadius:0,arrival:[m.x,m.z],
     photoDistance:m.distance,photoElevation:m.elevation,photoAngle:m.angle,photoTargetHeight:m.targetHeight});
  },s);
  await page.waitForTimeout(3000);
  await page.screenshot({path:'output/amoy/shimao-detail/'+s.name+'.png'});
  console.log('shot:',s.name);
}
await browser.close();
