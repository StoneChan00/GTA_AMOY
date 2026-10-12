/** Post-fix verification: Gulangyu island exists with buildings/green/terrain, no car roads, landmark arrival intact. */
import {chromium} from 'playwright';
import fs from 'node:fs';
fs.mkdirSync('output/amoy/gulangyu-fix',{recursive:true});
const browser=await chromium.launch({channel:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1600,height:900}});
await page.goto('http://127.0.0.1:5173/?quality=low',{waitUntil:'domcontentloaded'});
let booted=false;
for(let i=0;i<150;i++){await page.waitForTimeout(2000);if(await page.evaluate(()=>!!(window.__SHENCHENGJI_CITY__?.ready))){booted=true;console.log('ready after',i*2,'s');break;}}
if(!booted){console.error('BOOT FAILED');await page.screenshot({path:'output/amoy/gulangyu-fix/boot-fail.png'});await browser.close();process.exit(1);}
await page.waitForTimeout(6000); // let optional layers (canopy/planting/facades) settle

const GX=-3143,GZ=-2698,R=750;
const inv=await page.evaluate(([gx,gz,r])=>{
  const w=window.__SHENCHENGJI_CITY__.world,out={hits:[],roads:[],green:0,buildings:0,terrain:[],pedestrian:0,canopy:0};
  for(const m of w.scene.meshes){
    if(!m.getTotalVertices())continue;
    const b=m.getBoundingInfo().boundingBox;
    const near=b.maximumWorld.x>gx-r&&b.minimumWorld.x<gx+r&&b.maximumWorld.z>gz-r&&b.minimumWorld.z<gz+r;
    if(!near)continue;
    const inside=b.minimumWorld.x>gx-r&&b.maximumWorld.x<gx+r&&b.minimumWorld.z>gz-r&&b.maximumWorld.z<gz+r;
    const rec={name:m.name,verts:m.getTotalVertices(),inside};
    out.hits.push(rec);
    if(/road|street/i.test(m.name)&&inside)out.roads.push(rec);
    if(/green|park|forest|grass|tree|canopy|palm|plant/i.test(m.name))out.green+=m.getTotalVertices();
    if(/^block_/.test(m.name))out.buildings+=m.getTotalVertices();
    if(/terrain|land|ground|coast/i.test(m.name))out.terrain.push(rec);
    if(/pedestrian|promenade|path/i.test(m.name))out.pedestrian+=m.getTotalVertices();
  }
  out.hits.sort((a,b)=>b.verts-a.verts);
  return out;
},[GX,GZ,R]);
console.log('== meshes near Gulangyu ==');
for(const h of inv.hits.slice(0,25))console.log(' ',h.name,'verts='+h.verts,h.inside?'[inside]':'');
console.log('car-road meshes fully inside Gulangyu:',inv.roads.length);
console.log('building verts:',inv.buildings,'| green/canopy verts:',inv.green,'| pedestrian verts:',inv.pedestrian);
console.log('terrain-ish meshes:',JSON.stringify(inv.terrain.slice(0,6)));

const lm=await page.evaluate(()=>{
  const w=window.__SHENCHENGJI_CITY__.world;
  const marks=(w.landmarks??[]).filter(l=>/gulangyu|鼓浪/.test(l.id+l.name));
  return {marks,arrival:marks[0]?.arrival,observerPose:w.observer?.pose?.()};
});
console.log('gulangyu landmark:',JSON.stringify(lm.marks));

const shots=[
  // top-down-ish aerial of the island itself
  {name:'gulangyu-aerial',x:GX,z:GZ,targetHeight:80,distance:2400,elevation:.55,angle:-1.2},
  // low oblique from NE across the island toward Haicang strait
  {name:'gulangyu-close',x:GX,z:GZ,targetHeight:40,distance:1100,elevation:.22,angle:.7},
  // same as pre-fix strait shot for before/after comparison
  {name:'gulangyu-strait-after',x:400,z:-1500,targetHeight:80,distance:5600,elevation:.35,angle:-1.20},
];
for(const s of shots){
  await page.evaluate(m=>{
    const w=window.__SHENCHENGJI_CITY__.world;
    w.enterPhoto({id:'probe-'+m.name,name:'probe',x:m.x,z:m.z,height:0,area:'probe',excludeRadius:0,arrival:[m.x,m.z],
     photoDistance:m.distance,photoElevation:m.elevation,photoAngle:m.angle,photoTargetHeight:m.targetHeight});
  },s);
  await page.waitForTimeout(2500);
  await page.screenshot({path:'output/amoy/gulangyu-fix/'+s.name+'.png'});
  console.log('shot:',s.name);
}
await browser.close();
