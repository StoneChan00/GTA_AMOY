/** Gaoqi T4 proper acceptance: camera onto the T4 centroid (1310,4171). */
import {chromium} from 'playwright';
import fs from 'node:fs';
fs.mkdirSync('output/amoy/landmarks-v2',{recursive:true});
const browser=await chromium.launch({channel:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1440,height:810}});
await page.goto('http://127.0.0.1:5173/?quality=low',{waitUntil:'domcontentloaded'});
let booted=false;
for(let i=0;i<180;i++){await page.waitForTimeout(2000);if(await page.evaluate(()=>!!(window.__SHENCHENGJI_CITY__?.ready))){booted=true;break;}}
if(!booted){console.error('BOOT FAILED');await browser.close();process.exit(1);}
await page.waitForTimeout(4000);
await page.evaluate(()=>{const w=window.__SHENCHENGJI_CITY__.world;w.toggleAerial();w.setLightMode('day');
  window.__shot=(cx,cy,cz,tx,ty,tz)=>{const ob=w.observer;ob.focus={x:tx,y:ty,z:tz};
    ob.yaw=Math.atan2(tx-cx,tz-cz);ob.pitch=Math.asin(Math.max(-1,Math.min(1,(cy-ty)/Math.hypot(tx-cx,ty-cy,tz-cz))));
    ob.distance=Math.hypot(tx-cx,ty-cy,tz-cz);};
  for(const rtt of [w.mirror,w.waterMirror]){rtt.refreshRate=1;rtt.resetRefreshCounter();}});
const shots=[
  ['gaoqi-t4-front',1090,60,4020,1310,10,4171],   // T4 centroid, from SW
  ['gaoqi-t4-runway',1310,150,3900,1310,5,4200],  // higher, incl runway side
];
for(const[name,cx,cy,cz,tx,ty,tz]of shots){
  await page.evaluate(([n,a,b,c,d,e,f])=>window.__shot(a,b,c,d,e,f),[name,cx,cy,cz,tx,ty,tz]);
  await page.waitForTimeout(2600);
  await page.screenshot({path:'output/amoy/landmarks-v2/'+name+'.png'});
  console.log('shot:',name);
}
await browser.close();
