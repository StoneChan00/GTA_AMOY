/** Probe the white anomalies: which meshes render white, their materials and heights. */
import {chromium} from 'playwright';
const browser=await chromium.launch({channel:'msedge',headless:false});
const page=await browser.newPage({viewport:{width:1600,height:900}});
const errors=[];
page.on('console',m=>{if(m.type()==='error'||m.text().includes('404')||m.text().includes('Failed'))errors.push(m.text().slice(0,160));});
page.on('requestfailed',r=>errors.push('REQ FAIL: '+r.url().slice(-90)));
await page.goto('http://127.0.0.1:5173/?quality=low',{waitUntil:'domcontentloaded'});
let booted=false;
for(let i=0;i<150;i++){await page.waitForTimeout(2000);if(await page.evaluate(()=>!!(window.__SHENCHENGJI_CITY__?.ready))){booted=true;break;}}
if(!booted){console.error('BOOT FAILED');console.log(errors.slice(0,10).join('\n'));await browser.close();process.exit(1);}
await page.waitForTimeout(3000);
const out=await page.evaluate(()=>{
 const w=window.__SHENCHENGJI_CITY__.world,scene=w.scene;
 const wanted=/mountain|relief|far|shore|horizon|terrain_water|bay|opposite|vegetation|island-tree|palm/i;
 const rows=[];
 for(const m of scene.meshes){
  if(!m.getTotalVertices()||!wanted.test(m.name))continue;
  const b=m.getBoundingInfo().boundingBox;
  const mat=m.material;
  let matInfo='none';
  try{matInfo=mat?(mat.name+(mat.albedoColor?` albedo=${mat.albedoColor.r.toFixed(2)},${mat.albedoColor.g.toFixed(2)},${mat.albedoColor.b.toFixed(2)}`:'')+(mat.diffuseTexture?` tex=${mat.diffuseTexture.name}`:'')+(mat.getClassName?` (${mat.getClassName()})`:'')):'none';}catch(e){matInfo='err';}
  rows.push({name:m.name,verts:m.getTotalVertices(),
   x:[+b.minimumWorld.x.toFixed(0),+b.maximumWorld.x.toFixed(0)],
   y:[+b.minimumWorld.y.toFixed(1),+b.maximumWorld.y.toFixed(1)],
   z:[+b.minimumWorld.z.toFixed(0),+b.maximumWorld.z.toFixed(0)],
   mat:matInfo.slice(0,110),enabled:m.isEnabled()});
 }
 return {rows,mountains:w.mountains?Object.keys(w.mountains):null,groundRelief:!!w.groundRelief};
});
console.log('=== candidate meshes ===');
for(const r of out.rows)console.log(JSON.stringify(r));
console.log('=== console errors (first 12) ===');
for(const e of errors.slice(0,12))console.log(e);
await browser.close();
