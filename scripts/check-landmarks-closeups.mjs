/** Close-up verification for XMU groups and other objects that need reading. */
import {chromium} from 'playwright';
import fs from 'node:fs';
fs.mkdirSync('output/amoy/landmarks-v1',{recursive:true});
const browser=await chromium.launch({channel:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1440,height:810}});
await page.goto('http://127.0.0.1:5173/?quality=medium',{waitUntil:'domcontentloaded'});
let booted=false;
for(let i=0;i<180;i++){await page.waitForTimeout(2000);if(await page.evaluate(()=>!!(window.__SHENCHENGJI_CITY__?.ready))){booted=true;console.log('ready after',i*2,'s');break;}}
if(!booted){console.error('BOOT FAILED');await browser.close();process.exit(1);}
await page.waitForTimeout(5000);
await page.evaluate(()=>{const w=window.__SHENCHENGJI_CITY__.world;w.toggleAerial();w.setLightMode('day');
  window.__shot=(cx,cy,cz,tx,ty,tz)=>{const ob=w.observer;ob.focus={x:tx,y:ty,z:tz};
    ob.yaw=Math.atan2(tx-cx,tz-cz);ob.pitch=Math.asin(Math.max(-1,Math.min(1,(cy-ty)/Math.hypot(tx-cx,ty-cy,tz-cz))));
    ob.distance=Math.hypot(tx-cx,ty-cy,tz-cz);};
  for(const rtt of [w.mirror,w.waterMirror]){rtt.refreshRate=1;rtt.resetRefreshCounter();}});
const shots=[
  ['xmu-songen-close',-1598,60,-2960,-1598,26,-2799],
  ['xmu-qunxian-row',-1800,38,-3120,-1803,7,-3053],
  ['xmu-jiannan-close',-1620,42,-3290,-1665,10,-3205],
  ['gaoqi-t4-close',1310,46,4020,1310,12,4171],
  ['huizhan-close',3300,52,-1068,3540,13,-1068],
];
for(const[name,cx,cy,cz,tx,ty,tz]of shots){
  await page.evaluate(([n,a,b,c,d,e,f])=>window.__shot(a,b,c,d,e,f),[name,cx,cy,cz,tx,ty,tz]);
  await page.waitForTimeout(2600);
  await page.screenshot({path:'output/amoy/landmarks-v1/'+name+'.png'});
  console.log('shot:',name);
}
await browser.close();
