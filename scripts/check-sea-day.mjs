/** Day-mode comparison shots: does the sea read as sea in daylight? */
import {chromium} from 'playwright';
const browser=await chromium.launch({channel:'msedge',headless:false});
const page=await browser.newPage({viewport:{width:1600,height:900}});
await page.goto('http://127.0.0.1:5173/?quality=low',{waitUntil:'domcontentloaded'});
let booted=false;
for(let i=0;i<150;i++){await page.waitForTimeout(2000);if(await page.evaluate(()=>!!(window.__SHENCHENGJI_CITY__?.ready))){booted=true;break;}}
if(!booted){console.error('BOOT FAILED');await browser.close();process.exit(1);}
await page.waitForTimeout(3000);
await page.evaluate(()=>{window.__SHENCHENGJI_CITY__.world.setLightMode('day');});
await page.waitForTimeout(2500);
const shots=[
 {name:'day-south-north',x:0,z:-1000,targetHeight:80,distance:6470,elevation:.382,angle:0},
 {name:'day-west-gulangyu',x:400,z:-1500,targetHeight:80,distance:5600,elevation:.35,angle:-1.20},
];
for(const s of shots){
 await page.evaluate(m=>{
  const w=window.__SHENCHENGJI_CITY__.world;
  w.enterPhoto({id:'probe-'+m.name,name:'probe',x:m.x,z:m.z,height:0,area:'probe',excludeRadius:0,arrival:[m.x,m.z],
   photoDistance:m.distance,photoElevation:m.elevation,photoAngle:m.angle,photoTargetHeight:m.targetHeight});
 },s);
 await page.waitForTimeout(2000);
 await page.screenshot({path:'output/amoy/sea-check/'+s.name+'.png'});
 console.log('shot:',s.name);
}
await browser.close();
