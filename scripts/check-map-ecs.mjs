/** Verify the DEPLOYED ECS entry shows Gulangyu on the M-key map. */
import {chromium} from 'playwright';
import fs from 'node:fs';
fs.mkdirSync('output/amoy/map-check',{recursive:true});
const browser=await chromium.launch({channel:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1600,height:900}});
await page.goto('http://39.96.117.179/GTA_AMOY/?quality=low',{waitUntil:'domcontentloaded'});
let booted=false;
for(let i=0;i<180;i++){await page.waitForTimeout(2000);if(await page.evaluate(()=>!!(window.__SHENCHENGJI_CITY__?.ready))){booted=true;console.log('ready after',i*2,'s');break;}}
if(!booted){console.error('BOOT FAILED');await page.screenshot({path:'output/amoy/map-check/ecs-boot-fail.png'});await browser.close();process.exit(1);}
await page.waitForTimeout(5000);
await page.evaluate(()=>{const w=window.__SHENCHENGJI_CITY__.world;
  w.enterPhoto({id:'probe-map',name:'probe',x:-3143,z:-2698,height:0,area:'probe',excludeRadius:0,arrival:[-3143,-2698],
   photoDistance:900,photoElevation:.9,photoAngle:0,photoTargetHeight:60});});
await page.waitForTimeout(2000);
await page.keyboard.press('m');
await page.waitForTimeout(2500);
await page.screenshot({path:'output/amoy/map-check/ecs-map-open.png'});
console.log('ECS map screenshot taken');
await browser.close();
