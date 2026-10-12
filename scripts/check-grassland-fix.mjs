/** Verify the mountain layers now render with grass coloring (not white) after restoring grassland-v2. */
import {chromium} from 'playwright';
const browser=await chromium.launch({channel:'msedge',headless:false});
const page=await browser.newPage({viewport:{width:1600,height:900}});
const errors=[];
page.on('requestfailed',r=>{if(r.url().includes('grassland'))errors.push('REQ FAIL: '+r.url().slice(-70));});
await page.goto('http://127.0.0.1:5173/?quality=low',{waitUntil:'domcontentloaded'});
let booted=false;
for(let i=0;i<150;i++){await page.waitForTimeout(2000);if(await page.evaluate(()=>!!(window.__SHENCHENGJI_CITY__?.ready))){booted=true;break;}}
if(!booted){console.error('BOOT FAILED');console.log(errors.slice(0,5).join('\n'));await browser.close();process.exit(1);}
await page.waitForTimeout(4000);
// day mode + a shot from the south (mountains north backdrop + near relief both in view)
await page.evaluate(()=>{window.__SHENCHENGJI_CITY__.world.setLightMode('day');});
await page.waitForTimeout(2500);
await page.evaluate(()=>{
 const w=window.__SHENCHENGJI_CITY__.world;
 w.enterPhoto({id:'probe-fix',name:'probe',x:0,z:-1000,height:0,area:'probe',excludeRadius:0,arrival:[0,-1000],
  photoDistance:6470,photoElevation:.382,photoAngle:0,photoTargetHeight:80});
});
await page.waitForTimeout(2500);
await page.screenshot({path:'output/amoy/sea-check/day-south-after-grassland.png'});
console.log('shot taken; grassland request failures:',errors.length);
await browser.close();
