/** GTA_AMOY fix verification: collision volumes, NPC yielding, rear wheels. */
import {chromium} from 'playwright';
import fs from 'node:fs';
fs.mkdirSync('output/amoy',{recursive:true});
const browser=await chromium.launch({channel:'msedge',headless:false});
const page=await browser.newPage({viewport:{width:1600,height:900}});
page.on('pageerror',e=>console.log('[pageerror]',String(e).slice(0,300)));
await page.goto('http://127.0.0.1:5173/?quality=low',{waitUntil:'domcontentloaded'});
for(let i=0;i<75;i++){await page.waitForTimeout(2000);if(await page.evaluate(()=>!!(window.__SHENCHENGJI_CITY__?.ready))){console.log('ready');break;}}
// --- Collision probe: buildings, twin towers, water, road ---
const collision=await page.evaluate(()=>{
 const w=window.__SHENCHENGJI_CITY__.world;const out={};
 const big=[...w.data.buildings].sort((a,b)=>b.height-a.height).slice(0,5).map(b=>{
  const ring=b.rings[0];const cx=ring.reduce((s,p)=>s+p[0],0)/ring.length,cz=ring.reduce((s,p)=>s+p[1],0)/ring.length;
  return {name:b.name||'(unnamed)',height:Math.round(b.height),blocked:w.collision.blocked(cx,cz)};});
 out.tallBuildings=big;
 const shimao=w.data.landmarks.find(m=>m.id==='shimao');
 out.shimao={x:shimao.x,z:shimao.z,at30m:w.collision.blocked(shimao.x+30,shimao.z),at50m:w.collision.blocked(shimao.x+50,shimao.z)};
 const huizhan=w.data.landmarks.find(m=>m.id==='huizhan');
 const convention=w.data.buildings.filter(b=>Math.hypot(b.rings[0][0][0]-huizhan.x,b.rings[0][0][1]-huizhan.z)<300);
 out.conventionCenterNearby=convention.length;
 out.spawnRoadBlocked=w.collision.blocked(w.state.x,w.state.z);
 return out;});
console.log('COLLISION',JSON.stringify(collision,null,1));
// --- NPC yielding probe: hold the car still on the road for 20s and sample the nearest NPC ---
const npc=await page.evaluate(async()=>{
 const w=window.__SHENCHENGJI_CITY__.world;const samples=[];
 for(let t=0;t<20;t++){
  await new Promise(r=>setTimeout(r,1000));
  const cars=w.traffic?.cars??[];
  let nearest=null;for(const c of cars){const d=Math.hypot(c.x-w.state.x,c.z-w.state.z);if(!nearest||d<nearest.d)nearest={d:Math.round(d),speed:Math.round(c.speed)};}
  samples.push(nearest?`${nearest.d}m@${nearest.speed}`:'none');
 }
 return samples;});
console.log('NPC approach over 20s (distance@nominal speed):',npc.join(' | '));
// --- Wheels visual: chase view screenshot after driving ---
await page.keyboard.down('KeyW');await page.waitForTimeout(4000);await page.keyboard.up('KeyW');
await page.waitForTimeout(800);
await page.screenshot({path:'output/amoy/wheels-fixed.png'});
const carProbe=await page.evaluate(()=>{
 const w=window.__SHENCHENGJI_CITY__.world;
 const wheels=w.carMeshes.filter(m=>m.name.startsWith('wheel_')).map(m=>({name:m.name,pivotX:+m.getPivotPoint().x.toFixed(2),pivotZ:+m.getPivotPoint().z.toFixed(2)}));
 return {wheelCount:wheels.length,sample:wheels.slice(0,4),wheelRadius:w.wheelRadius,trafficCars:w.traffic?.cars.length};});
console.log('WHEELS',JSON.stringify(carProbe,null,1));
await browser.close();
