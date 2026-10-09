/** Clean visual check: rear wheels at spawn + driving, no UI interference. */
import {chromium} from 'playwright';
import fs from 'node:fs';
fs.mkdirSync('output/amoy',{recursive:true});
const browser=await chromium.launch({channel:'msedge',headless:false});
const page=await browser.newPage({viewport:{width:1600,height:900}});
page.on('pageerror',e=>console.log('[pageerror]',String(e).slice(0,300)));
await page.goto('http://127.0.0.1:5173/?quality=low',{waitUntil:'domcontentloaded'});
for(let i=0;i<75;i++){await page.waitForTimeout(2000);if(await page.evaluate(()=>!!(window.__SHENCHENGJI_CITY__?.ready))){console.log('ready');break;}}
await page.waitForTimeout(2500);
await page.screenshot({path:'output/amoy/wheels-rear-spawn.png'});
await page.keyboard.down('KeyW');await page.waitForTimeout(3500);await page.keyboard.up('KeyW');
await page.waitForTimeout(600);
await page.screenshot({path:'output/amoy/wheels-rear-drive.png'});
const check=await page.evaluate(()=>{
 const w=window.__SHENCHENGJI_CITY__.world;
 const wheels=w.carMeshes.filter(m=>m.name.startsWith('wheel_'));
 const rr=wheels.find(m=>m.name.startsWith('wheel_rr'));
 return {wheelMeshes:wheels.length,rrPivot:rr?[+rr.getPivotPoint().x.toFixed(3),+rr.getPivotPoint().z.toFixed(3)]:null,spin:+rr?.rotation.x.toFixed(2),wheelRadius:+w.wheelRadius.toFixed(3),road:w.roadName};});
console.log('WHEEL CHECK',JSON.stringify(check));
await browser.close();
