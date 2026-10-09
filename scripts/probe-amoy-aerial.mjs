/** GTA_AMOY aerial probe: drone up, look down at the road network. */
import {chromium} from 'playwright';
import fs from 'node:fs';
fs.mkdirSync('output/amoy',{recursive:true});
const browser=await chromium.launch({channel:'msedge',headless:false});
const page=await browser.newPage({viewport:{width:1600,height:900}});
page.on('pageerror',e=>console.log('[pageerror]',String(e).slice(0,300)));
await page.goto('http://127.0.0.1:5173/?quality=low',{waitUntil:'domcontentloaded'});
for(let i=0;i<75;i++){await page.waitForTimeout(2000);if(await page.evaluate(()=>!!(window.__SHENCHENGJI_CITY__?.ready))){console.log('ready');break;}}
// Enter drone (G) and climb with E for a top-down vantage over the spawn road.
await page.keyboard.press('KeyG');await page.waitForTimeout(1200);
for(let i=0;i<14;i++){await page.keyboard.down('KeyE');await page.waitForTimeout(300);await page.keyboard.up('KeyE');}
await page.waitForTimeout(1500);
await page.screenshot({path:'output/amoy/aerial-roads.png'});
// Pitch the camera down: drag downward on the canvas.
await page.mouse.move(800,450);await page.mouse.down();await page.mouse.move(800,760,{steps:8});await page.mouse.up();
await page.waitForTimeout(1200);
await page.screenshot({path:'output/amoy/aerial-roads-down.png'});
const probe=await page.evaluate(()=>{
 const w=window.__SHENCHENGJI_CITY__.world;const s=w.state;
 const near=w.blocks.filter(b=>b.road&&Math.hypot(b.x-s.x,b.z-s.z)<1600).slice(0,6).map(b=>({chunk:b.mesh.name.split('_').slice(0,3).join('_'),enabled:b.mesh.isEnabled(),dist:Math.round(Math.hypot(b.x-s.x,b.z-s.z))}));
 const asphalt=w.scene.materials.find(m=>m.name==='asphalt');
 const n=w.collision.nearest(s.x,s.z);
 return {car:{x:Math.round(s.x),z:Math.round(s.z)},nearestRoad:n?{name:n.road.name,d:Math.round(n.d),width:n.road.width}:null,
  asphaltMaterial:{name:asphalt?.name,albedo:asphalt?.albedoTexture?.name??'none',metallic:asphalt?.metallic,rough:asphalt?.roughness},
  enabledRoadBlocks:near,offroad:w.offroad};});
console.log(JSON.stringify(probe,null,1));
await browser.close();
