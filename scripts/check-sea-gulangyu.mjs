/** Visual check: aerial screenshots for (1) Gulangyu emptiness, (2) sea around the island, (3) mainland far-shore. */
import {chromium} from 'playwright';
import fs from 'node:fs';
fs.mkdirSync('output/amoy/sea-check',{recursive:true});
const browser=await chromium.launch({channel:'msedge',headless:false});
const page=await browser.newPage({viewport:{width:1600,height:900}});
await page.goto('http://127.0.0.1:5173/?quality=low',{waitUntil:'domcontentloaded'});
let booted=false;
for(let i=0;i<150;i++){await page.waitForTimeout(2000);if(await page.evaluate(()=>!!(window.__SHENCHENGJI_CITY__?.ready))){booted=true;console.log('ready after',i*2,'s');break;}}
if(!booted){console.error('BOOT FAILED');await page.screenshot({path:'output/amoy/sea-check/boot-fail.png'});await browser.close();process.exit(1);}
await page.waitForTimeout(5000); // let layers settle

// Gulangyu mesh inventory: any scene mesh with vertices within 600 of (-3143,-2698)?
const gulangyu=await page.evaluate(()=>{
 const w=window.__SHENCHENGJI_CITY__.world,gx=-3143,gz=-2698;
 const hits=[];
 for(const m of w.scene.meshes){
  if(!m.getTotalVertices())continue;
  const b=m.getBoundingInfo().boundingBox;
  if(b.maximumWorld.x>gx-700&&b.minimumWorld.x<gx+700&&b.maximumWorld.z>gz-700&&b.minimumWorld.z<gz+700){
   hits.push({name:m.name,verts:m.getTotalVertices(),min:[+b.minimumWorld.x.toFixed(0),+b.minimumWorld.z.toFixed(0)],max:[+b.maximumWorld.x.toFixed(0),+b.maximumWorld.z.toFixed(0)]});
  }
 }
 return hits;
});
console.log('meshes overlapping Gulangyu area:',gulangyu.length);
for(const h of gulangyu)console.log(' ',h.name,'verts='+h.verts,'bbox',JSON.stringify(h.min),JSON.stringify(h.max));

// Bay water stats
const waterStats=await page.evaluate(()=>{
 const w=window.__SHENCHENGJI_CITY__.world;
 const ext=w.scene.getMeshByName('bay-horizon-water');
 const b=w.bayWater?.stats();
 return {extensionExists:!!ext,extensionVerts:ext?ext.getTotalVertices():0,horizonCoverage:b?.horizonCoverageBounds,waterLevel:b?.waterLevel};
});
console.log('bay-horizon-water:',JSON.stringify(waterStats));

// Camera shots via the game's own observer rig (enterPhoto): camera = focus-(sin(yaw),cos(yaw))*cos(pitch)*d, y=focus.y+sin(pitch)*d, yaw=-photoAngle
const shots=[
 // SW of the strait looking NE across Gulangyu+island
 {name:'gulangyu-strait',x:400,z:-1500,targetHeight:80,distance:5600,elevation:.35,angle:-1.20},
 // far south looking north: island in the sea + north mainland
 {name:'south-sea-north',x:0,z:-1000,targetHeight:80,distance:6470,elevation:.382,angle:0},
 // far west looking east: strait, Gulangyu, island
 {name:'west-look-east',x:0,z:-1400,targetHeight:80,distance:7678,elevation:.146,angle:-1.41},
];
for(const s of shots){
 await page.evaluate(m=>{
  const w=window.__SHENCHENGJI_CITY__.world;
  w.enterPhoto({id:'probe-'+m.name,name:'probe',x:m.x,z:m.z,height:0,area:'probe',excludeRadius:0,arrival:[m.x,m.z],
   photoDistance:m.distance,photoElevation:m.elevation,photoAngle:m.angle,photoTargetHeight:m.targetHeight});
 },s);
 await page.waitForTimeout(2000);
 await page.screenshot({path:'output/amoy/sea-check/'+s.name+'.png'});
 console.log('shot:',s.name,'pose:',JSON.stringify(await page.evaluate(()=>window.__SHENCHENGJI_CITY__.world.observer.pose())));
}
await browser.close();
