/** Reproduce the user's report: open the M-key city map and look at the Gulangyu area. */
import {chromium} from 'playwright';
import fs from 'node:fs';
fs.mkdirSync('output/amoy/map-check',{recursive:true});
const browser=await chromium.launch({channel:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1600,height:900}});
await page.goto('http://127.0.0.1:5173/?quality=low',{waitUntil:'domcontentloaded'});
let booted=false;
for(let i=0;i<150;i++){await page.waitForTimeout(2000);if(await page.evaluate(()=>!!(window.__SHENCHENGJI_CITY__?.ready))){booted=true;console.log('ready after',i*2,'s');break;}}
if(!booted){console.error('BOOT FAILED');await browser.close();process.exit(1);}
await page.waitForTimeout(5000);
// position the camera over the strait between Gulangyu and the main island, looking down
await page.evaluate(()=>{const w=window.__SHENCHENGJI_CITY__.world;
  w.enterPhoto({id:'probe-map',name:'probe',x:-3143,z:-2698,height:0,area:'probe',excludeRadius:0,arrival:[-3143,-2698],
   photoDistance:900,photoElevation:.9,photoAngle:0,photoTargetHeight:60});});
await page.waitForTimeout(2000);
await page.screenshot({path:'output/amoy/map-check/scene-before-map.png'});
// open the city map (M)
await page.keyboard.press('m');
await page.waitForTimeout(2500);
await page.screenshot({path:'output/amoy/map-check/map-open.png'});
console.log('map opened, screenshot taken');
// inspect what the map overlay contains (DOM) for diagnostics
const mapInfo=await page.evaluate(()=>{
  const overlays=[...document.querySelectorAll('canvas,svg,[class*=map],[id*=map]')].map(e=>({tag:e.tagName,cls:e.className?.toString?.().slice(0,60),id:e.id,w:e.clientWidth,h:e.clientHeight}));
  return overlays.filter(o=>o.w>100&&o.h>100);
});
console.log('map-ish elements:',JSON.stringify(mapInfo,null,1));
await browser.close();
