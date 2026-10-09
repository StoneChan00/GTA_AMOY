/** Fine-grained NPC yielding test: 200ms sampling of all cars within 45m. */
import {chromium} from 'playwright';
const browser=await chromium.launch({channel:'msedge',headless:false});
const page=await browser.newPage({viewport:{width:1600,height:900}});
await page.goto('http://127.0.0.1:5173/?quality=low',{waitUntil:'domcontentloaded'});
for(let i=0;i<75;i++){await page.waitForTimeout(2000);if(await page.evaluate(()=>!!(window.__SHENCHENGJI_CITY__?.ready))){console.log('ready');break;}}
// Drive forward briefly so the car sits squarely in a live lane, then stop.
await page.keyboard.down('KeyW');await page.waitForTimeout(2500);await page.keyboard.up('KeyW');
await page.keyboard.down('KeyS');await page.waitForTimeout(1500);await page.keyboard.up('KeyS');
const trace=await page.evaluate(async()=>{
 const w=window.__SHENCHENGJI_CITY__.world;const rows=[];
 for(let t=0;t<80;t++){
  await new Promise(r=>setTimeout(r,250));
  const p=w.state;
  const near=(w.traffic?.cars??[]).map(c=>({d:+Math.hypot(c.x-p.x,c.z-p.z).toFixed(1),x:+c.x.toFixed(0),z:+c.z.toFixed(0),yaw:+c.yaw.toFixed(2)}))
   .filter(c=>c.d<45).sort((a,b)=>a.d-b.d).slice(0,3);
  rows.push(near.map(c=>`${c.d}@(${c.x},${c.z})yaw${c.yaw}`).join('  ')||'-');
  // Did any car ever overlap the player (<2.5m)?
  if(near.length&&near[0].d<2.5)rows[rows.length-1]+='  <<OVERLAP';
 }
 return rows;});
console.log(trace.join('\n'));
await browser.close();
