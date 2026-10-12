/** Verify map fixes: minimap land outline for Gulangyu + M-map pedestrian paths at street zoom. */
import {chromium} from 'playwright';
import fs from 'node:fs';
fs.mkdirSync('output/amoy/map-fix',{recursive:true});
const browser=await chromium.launch({channel:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1600,height:900}});
await page.goto('http://127.0.0.1:5173/?quality=low',{waitUntil:'domcontentloaded'});
let booted=false;
for(let i=0;i<150;i++){await page.waitForTimeout(2000);if(await page.evaluate(()=>!!(window.__SHENCHENGJI_CITY__?.ready))){booted=true;console.log('ready after',i*2,'s');break;}}
if(!booted){console.error('BOOT FAILED');await browser.close();process.exit(1);}
await page.waitForTimeout(6000);
// stand on the main-island waterfront (Lujiang road) facing Gulangyu across the strait
await page.evaluate(()=>{const w=window.__SHENCHENGJI_CITY__.world;
  w.enterPhoto({id:'probe-strait',name:'probe',x:-2700,z:-2600,height:0,area:'probe',excludeRadius:0,arrival:[-2700,-2600],
   photoDistance:500,photoElevation:.35,photoAngle:-2.2,photoTargetHeight:30});});
await page.waitForTimeout(2500);
await page.screenshot({path:'output/amoy/map-fix/minimap-strait.png'});
console.log('shot: minimap-strait (bottom-left minimap should now outline Gulangyu to the west)');
// open the M map — local view centers near the strait at street zoom (ped paths visible)
await page.keyboard.press('m');
await page.waitForTimeout(3000);
await page.screenshot({path:'output/amoy/map-fix/mmap-street-gulangyu.png'});
console.log('shot: mmap-street-gulangyu (pedestrian lanes should render on the island)');
// also capture the full-city view for the caption fix
await page.keyboard.press('0');
await page.waitForTimeout(2000);
await page.screenshot({path:'output/amoy/map-fix/mmap-full.png'});
console.log('shot: mmap-full (caption should read 思明 · 湖里)');
await browser.close();
