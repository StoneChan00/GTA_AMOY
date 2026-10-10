import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {test} from 'node:test';
import {NullEngine,Scene} from '@babylonjs/core';
import {closest} from '../src/driving.ts';
import {BAMBOO_CORRIDOR,corridorProject,createBambooCorridor,inBambooCorridor,planBambooCorridor} from '../src/city-bamboo-corridor.ts';
import type {CityData,Road,V2} from '../src/city-types.ts';

const rectangle=(x1:number,z1:number,x2:number,z2:number):V2[]=>[[x1,z1],[x2,z1],[x2,z2],[x1,z2],[x1,z1]];
const road=(id:string,points:V2[],width=12,kind='primary'):Road=>({id,name:id,points,width,kind,oneway:false,grade:'0'});
function fixture():CityData{
 return {
  meta:{counts:{},extent:[-3000,-1500,2500,1500],horizontalScale:.6},
  land:[[rectangle(-3000,-1500,2500,1500)]],coast:[],
  roads:[
   road('湖滨东路',[[-819,-536],[-1355,610]],10.5,'primary'),
   road('湖滨南路',[[-1000,-490],[-620,-490]],10,'secondary'),
   road('禾祥东路',[[-1300,120],[-880,120]],10,'tertiary'),
   road('outside',[[1900,0],[2100,0]]),
  ],
  green:[],water:[{name:'lake',rings:[rectangle(-1700,-200,-1500,-80)]}],
  buildings:[
   {rings:[rectangle(-830,-560,-790,-510)],height:28,style:'office'},
   {rings:[rectangle(-1160,-40,-1100,0)],height:22,style:'retail'},
   {rings:[rectangle(1950,10,2050,40)],height:20,style:'office'},
  ],
  landmarks:[
   {id:'xiamenzhan',name:'厦门站',x:-759.83,z:-500.94,height:40,area:'思明',excludeRadius:42,arrival:[-810,-525],yaw:3.14},
   {id:'yundang',name:'筼筜湖',x:-1543.96,z:-120.23,height:4,area:'思明',excludeRadius:0,arrival:[-1350,590],yaw:0},
  ],
  spawn:{x:-810,z:-525,yaw:3.14,road:'湖滨东路'},
 };
}

test('corridor covers 厦门站 and 湖滨东路, not 高崎 or 会展',()=>{
 assert.equal(BAMBOO_CORRIDOR.length,1265);
 assert.ok(inBambooCorridor(-759.83,-500.94),'厦门站在湖滨东路街面上');
 assert.ok(inBambooCorridor(-1087,37),'湖滨东路中段到路点在脊线上');
 assert.ok(inBambooCorridor(-819,-536),'湖滨南路路口在脊线南端');
 assert.equal(inBambooCorridor(303.93,1502.82),false);
 assert.equal(inBambooCorridor(2613.8,-1870.18),false);
});

test('street kit stays off the carriageway and inside budgets',()=>{
 const data=fixture();
 const open=planBambooCorridor(data);
 assert.ok(open.curbs.length>20);
 const hole=open.curbs[12];
 const reserved=(x:number,z:number,r:number)=>Math.hypot(x-hole.x,z-hole.z)<5+r;
 const plan=planBambooCorridor(data,{reserved});
 assert.deepEqual(planBambooCorridor(data,{reserved}),plan);
 assert.ok(plan.curbs.length>20&&plan.walks.length>20&&plan.edges.length>20);
 assert.ok(plan.pits.length>4&&plan.lamps.length>4&&plan.parked.length>2);
 assert.ok(plan.junctions.length>=1&&plan.signals.length>=1);
 assert.ok(plan.plinths.length>=1&&plan.awnings.length===plan.plinths.length&&plan.doors.length===plan.plinths.length);
 assert.ok(plan.curbs.length<=BAMBOO_CORRIDOR.budgets.curb);
 assert.ok(plan.parked.length<=BAMBOO_CORRIDOR.budgets.parked);
 const nearestRoad=(p:{x:number;z:number})=>{
  let best=Infinity,width=12;
  for(const r of data.roads)for(let i=1;i<r.points.length;i++){
   const d=closest(p.x,p.z,r.points[i-1],r.points[i]).d;if(d<best){best=d;width=r.width;}
  }
  return {best,width};
 };
 for(const p of [...plan.curbs,...plan.walks,...plan.pits,...plan.lamps]){
  const {best,width}=nearestRoad(p);assert.ok(best>width/2+.15);
 }
 for(const p of plan.parked){
  let best=Infinity,width=12;
  for(const r of data.roads)for(let i=1;i<r.points.length;i++){
   const d=closest(p.x,p.z,r.points[i-1],r.points[i]).d;if(d<best){best=d;width=r.width;}
  }
  assert.ok(best>width/2-1.7&&best<width/2+.4,'parked cars sit in the curb lane, not the sidewalk or the travel center');
 }
 for(const p of plan.crossings){
  const {best,width}=nearestRoad(p);
  assert.ok(Math.abs(p.sx)*7.2/2<=width/2+.35,'zebra stays on the carriageway, not the shop sidewalk');
  assert.ok(best<width/2+2.4,'zebra sits on a named junction axis');
 }
 assert.equal(plan.curbs.some(p=>Math.hypot(p.x-hole.x,p.z-hole.z)<4),false);
 assert.equal(plan.plinths.some(p=>p.x>0&&p.x<2000),false);
});

test('pause/hide toggle is independent of corridor membership',()=>{
 const data=fixture(),plan=planBambooCorridor(data);
 assert.ok(plan.roadMetres>1100);
 assert.ok(plan.roads>=2);
 const engine=new NullEngine(),scene=new Scene(engine);
 const kit=createBambooCorridor(scene,data,()=>0);
 assert.equal(kit.stats.extraLights,0);
 assert.equal(kit.stats.photoscrape,false);
 assert.ok(kit.stats.curbs>20);
 assert.ok(kit.stats.pits>=4);
 assert.ok(scene.meshes.some(m=>m.name==='corridor-tree'),'tree pits must contain a street tree');
 assert.ok((scene.getMeshByName('corridor-tree')?.getTotalVertices()??0)>80,'street trees are a trunk-plus-canopy mass, not a single lollipop sphere');
 assert.ok(scene.meshes.some(m=>m.name==='corridor-verge-box'),'curb and sidewalk are split by a planting verge');
 assert.ok(scene.meshes.some(m=>m.name==='corridor-lip'),'walk side keeps a stone curb lip at the verge');
 assert.ok((scene.getMeshByName('corridor-walk-box')?.getTotalVertices()??0)>80,'sidewalk is raised pavers, not a flat slab');
 assert.ok(plan.lips.length>8,'stone lip runs along the walk/verge joint');
 assert.ok(scene.meshes.some(m=>m.name==='corridor-pit'),'tree pits are raised planters, not a disk under the sidewalk');
 assert.ok(scene.meshes.some(m=>m.name==='corridor-pit'&&(m.material?.getClassName()==='MultiMaterial'||(m.material?.name??'').includes('pit'))),'tree pits keep a concrete ring and soil well');
 assert.ok(scene.meshes.some(m=>m.name==='corridor-car-0'),'parked cars are one merged sedan, not stacked boxes');
 assert.ok((scene.getMeshByName('corridor-car-0')?.getTotalVertices()??0)>40,'parked sedans keep a hood/cabin split and wheels');
 assert.ok(scene.meshes.some(m=>m.name==='corridor-car-cabin'),'sedan cabins are a separate greenhouse so they still read after merge');
 assert.ok(scene.meshes.some(m=>m.name==='corridor-facade-0'),'shopfronts are one street-wall bay, not stacked door/window/awning boxes');
 assert.ok((scene.getMeshByName('corridor-facade-0')?.getTotalVertices()??0)>120,'shopfronts keep a recessed door, framed window and fascia');
 assert.ok(scene.materials.some(m=>m.name.startsWith('corridor-sign-')),'shop fascia and blades carry fictional lettering, not a blank slab');
 assert.ok(scene.meshes.some(m=>m.name==='corridor-park-bay'),'parked cars sit on a parking bay, not the grass verge');
 assert.ok(plan.decks.length>=8&&plan.dashes.length>=4,'driven 湖滨东路 keeps a day-lit deck and lane dashes');
 assert.ok(Array.isArray(plan.rolling),'in-lane rolling cars are part of the corridor kit');
 assert.ok(scene.meshes.some(m=>m.name==='corridor-deck'),'carriageway uses a corridor deck, not only cinematic charcoal asphalt');
 const zebraA=plan.crossings[0];
 const zebraGap=plan.crossings.filter(p=>p!==zebraA).map(p=>Math.hypot(p.x-zebraA.x,p.z-zebraA.z)).sort((a,b)=>a-b)[0]??0;
 assert.ok(zebraGap>.7,'zebra stripes keep a visible gap, not a solid wash');
 kit.adoptStreetTrees([],[]);
 kit.adoptParkedCars([]);
 assert.ok(scene.getMeshByName('corridor-tree'),'empty adopt keeps the fallback street tree');
 kit.setEnabled(false);assert.equal(kit.root.isEnabled(),false);
 kit.setEnabled(true);kit.update(1,-1087,37,false);assert.equal(kit.root.isEnabled(),true);
 kit.update(1,-1087,37,true);assert.equal(kit.root.isEnabled(),true);
 kit.update(1,0,0,false);assert.equal(kit.root.isEnabled(),false);
 kit.dispose();engine.dispose();
});

test('live city.json still produces a complete 厦门站 street',()=>{
 const data=JSON.parse(readFileSync(new URL('../public/city/city.json',import.meta.url),'utf8')) as CityData;
 const plan=planBambooCorridor(data);
 assert.ok(plan.roadMetres>900,'corridor should collect more than one street block');
 assert.ok(plan.roads>=6);
 assert.ok(plan.curbs.length>=80&&plan.walks.length>=80);
 assert.ok(plan.pits.length>=20&&plan.lamps.length>=16);
 assert.ok(plan.signals.length>=2&&plan.parked.length>=20);
 assert.ok(plan.plinths.length>=8&&plan.awnings.length===plan.plinths.length&&plan.signs.length>=plan.plinths.length);
 assert.ok(plan.junctions.length>=2);
 const xiamenzhan=data.landmarks.find(m=>m.id==='xiamenzhan')!,yundang=data.landmarks.find(m=>m.id==='yundang')!;
 assert.ok(inBambooCorridor(xiamenzhan.x,xiamenzhan.z),'厦门站落在湖滨东路街面套件内');
 // 筼筜湖 is the lake at the corridor's far end; it sits off the carriageway kit
 // (measured 481 m from the spine) but inside the corridor's load/visibility radius.
 assert.ok(corridorProject(yundang.x,yundang.z).d<520,'筼筜湖在街面套件的可见半径内');
 assert.ok(plan.curbs.every(p=>inBambooCorridor(p.x,p.z,4)));
 const proj=(p:{x:number;z:number})=>corridorProject(p.x,p.z);
 const tOf=(p:{x:number;z:number})=>corridorProject(p.x,p.z).t;
 const hubinHit=(x:number,z:number)=>{
  let best=Infinity,width=6;
  for(const r of data.roads){
   if(!/湖滨东路|hubin/i.test(r.name??'')||!r.points||r.points.length<2)continue;
   for(let i=1;i<r.points.length;i++){
    const q=closest(x,z,r.points[i-1],r.points[i]);
    if(q.d<best){best=q.d;width=r.width;}
   }
  }
  return {d:best,width};
 };
 // Along-spine distribution (t 0 = 厦门站 south end, t 1 = 筼筜湖 north end).
 assert.ok(plan.walks.filter(p=>{const t=tOf(p);return t>0.55&&t<0.8;}).length>=8,'筼筜湖端路段要有步道');
 assert.ok(plan.walks.filter(p=>{const t=tOf(p);return t>0.1&&t<0.35;}).length>=8,'厦门站南侧不能出现街道空洞');
 assert.ok(plan.plinths.filter(p=>{const t=tOf(p);return t>0.35&&t<0.5;}).length>=8,'中段不能只剩树和路灯');
 assert.ok(plan.parked.filter(p=>{const t=tOf(p);return t>0.35&&t<0.5;}).length>=4,'中段也要有路边停车');
 assert.ok(plan.walks.filter(p=>{const t=tOf(p);const q=proj(p);return p.x<q.x&&t>0.3&&t<0.5;}).length>=4,'自动驾驶走的湖滨东路中段要有步道');
 assert.ok(plan.plinths.filter(p=>{const t=tOf(p);const q=proj(p);return p.x<q.x&&t>0.3&&t<0.5;}).length>=4,'湖滨东路中段驾驶路径不能只剩院墙');
 const hubinMidCars=plan.parked.filter(p=>{const t=tOf(p);const q=proj(p);return p.x<q.x&&t>0.3&&t<0.5;});
 assert.ok(hubinMidCars.length>=6,'湖滨东路中段驾驶路径要有一串路边停车');
 assert.ok(plan.curbs.filter(p=>{
  const k=hubinHit(p.x,p.z);
  return k.d>k.width/2+.12&&k.d<k.width/2+1.15;
 }).length>=40,'路缘石要贴着当前湖滨东路车行道，不能被双幅路甩到外侧');
 assert.ok(hubinMidCars.filter(p=>{
  const k=hubinHit(p.x,p.z);
  const shop=plan.plinths.slice().sort((a,b)=>Math.hypot(a.x-p.x,a.z-p.z)-Math.hypot(b.x-p.x,b.z-p.z))[0];
  return k.d>k.width/2-1.7&&k.d<k.width/2+.4&&shop&&Math.hypot(shop.x-p.x,shop.z-p.z)>3.6&&Math.hypot(shop.x-p.x,shop.z-p.z)<14&&k.d+1.1<hubinHit(shop.x,shop.z).d;
 }).length>=4,'湖滨东路停车要停在路缘停车带，不能上人行道或店背后');
 const hubinMidPits=plan.pits.filter(p=>{const t=tOf(p);const q=proj(p);return p.x<q.x&&t>0.3&&t<0.5;});
 const hubinMidWalks=plan.walks.filter(p=>{const t=tOf(p);const q=proj(p);return p.x<q.x&&t>0.3&&t<0.5;});
 const mean=(xs:number[])=>xs.reduce((n,v)=>n+v,0)/xs.length;
 assert.ok(plan.decks.filter(p=>hubinHit(p.x,p.z).d<2.4).length>=20,'day-lit deck sits on the driven 湖滨东路, not the geometric spine');
 assert.ok(plan.rolling.length>=4,'chase cone keeps in-lane cars, not only curb parking');
 assert.ok(hubinMidPits.length>=4&&hubinMidWalks.length>=4);
 assert.ok(mean(hubinMidPits.map(p=>hubinHit(p.x,p.z).d))+0.35<mean(hubinMidWalks.map(p=>hubinHit(p.x,p.z).d)),'tree pits sit in the verge, not under the sidewalk');
 assert.ok(plan.walks.filter(p=>{const t=tOf(p);return t>0.1&&t<0.35;}).length>=8,'厦门站到路段要有步道');
 assert.ok(plan.parked.filter(p=>tOf(p)<0.3).length>=2,'厦门站端要有路边停车');
 assert.ok(plan.plinths.length>=16,'长立面应拆成连续首层店面');
 // 厦门站 sits at the street's south edge (t≈0), so the "block ahead" of the
 // origin is expressed as along-spine fractions rather than the Shenzhen N-S
 // driving cone. The shopfront wall runs the driven band (t 0.15..0.65).
 const nearRoad=(p:{x:number;z:number},lo:number,hi:number)=>{const k=hubinHit(p.x,p.z);return k.d>lo&&k.d<hi;};
 assert.ok(plan.plinths.filter(p=>{const t=tOf(p);return t>0.12&&t<0.3&&proj(p).d<30;}).length>=3,'厦门站北第一商业段要有贴路首层店面');
 assert.ok(plan.plinths.filter(p=>{const t=tOf(p);return t>0.3&&t<0.5&&nearRoad(p,5,12);}).length>=4,'湖滨东路中段要有贴路店面，不能只剩路口侧墙');
 assert.ok(plan.signs.filter(p=>{const t=tOf(p);return t>0.12&&t<0.3;}).length>=4,'厦门站北驾驶段要有朝向车道的店招');
 assert.ok(plan.plinths.filter(p=>{const t=tOf(p);return t>0.1&&t<0.35;}).length>=6,'厦门站南侧前两段不能只剩树和路灯');
 const wall=plan.plinths.filter(p=>{const t=tOf(p);const q=proj(p);return t>0.15&&t<0.65&&p.x<q.x;}).sort((a,b)=>tOf(a)-tOf(b));
 assert.ok(wall.length>=28,'湖滨东路西侧要有连续首层街墙');
 let gaps=0;
 for(let i=1;i<wall.length;i++)if(Math.abs(tOf(wall[i])-tOf(wall[i-1]))*plan.corridor.length>16)gaps++;
 assert.ok(gaps<=10,'首层街墙不能只是孤立棚屋');
 assert.ok(plan.walks.filter(p=>{const t=tOf(p);return t>0.55&&t<0.8;}).length>=8,'筼筜湖端到路北侧不能只剩树和路灯');
 assert.ok(plan.pits.filter(p=>{const t=tOf(p);return t>0.55&&t<0.8;}).length>=2,'筼筜湖端路段也要有树池');
 const shop=wall.find(p=>{const t=tOf(p);return t>0.1&&t<0.35;});
 if(shop){
  const q=proj(shop);
  const pit=plan.pits.filter(p=>Math.abs(tOf(p)-q.t)<22/plan.corridor.length&&p.x<q.x)
   .sort((a,b)=>Math.abs(tOf(a)-q.t)-Math.abs(tOf(b)-q.t))[0];
  if(pit){
   const shopD=proj(shop).d,pitD=proj(pit).d;
   assert.ok(pitD<shopD,'行道树要在店面和车道之间的步道上');
  }
  const walk=plan.walks.filter(p=>Math.abs(tOf(p)-q.t)<10/plan.corridor.length&&p.x<q.x)
   .sort((a,b)=>Math.hypot(a.x-shop.x,a.z-shop.z)-Math.hypot(b.x-shop.x,b.z-shop.z))[0];
  if(walk){
   const shopD=proj(shop).d,walkD=proj(walk).d;
   assert.ok(walkD<shopD,'步道要在店面和车道之间，店面不能压在路缘上');
  }
 }
 for(const p of plan.plinths){
  let best=Infinity,width=6;
  for(const r of data.roads){
   if(!r.points||r.points.length<2)continue;
   for(let i=1;i<r.points.length;i++){
    const d=closest(p.x,p.z,r.points[i-1],r.points[i]).d;
    if(d<best){best=d;width=r.width;}
   }
  }
  assert.ok(best>width/2+.85,'店面不能压在支路或主路车行道上');
 }
 for(const p of plan.plinths){
  assert.equal(plan.junctions.some(j=>Math.hypot(p.x-j.x,p.z-j.z)<14),false,'店面不能站在路口车行道上');
 }
 const ribbon=plan.walks.filter(p=>{const t=tOf(p);const q=proj(p);return t>0.1&&t<0.3&&p.x<q.x;});
 assert.ok(ribbon.length>=3,'厦门站南侧步道要连成带，不能只剩店前垫块');
 const doorAprons=plan.plinths.filter(shop=>{
  const flip=shop.sz||1;
  const faceX=-Math.sin(shop.yaw)*flip,faceZ=-Math.cos(shop.yaw)*flip;
  const wallX=Math.cos(shop.yaw),wallZ=-Math.sin(shop.yaw);
  return plan.walks.some(w=>{
   const dx=w.x-shop.x,dz=w.z-shop.z;
   const along=dx*faceX+dz*faceZ,lat=Math.abs(dx*wallX+dz*wallZ);
   return along>0.15&&along<2.3&&lat<3.4;
  });
 });
 assert.ok(doorAprons.length>=12,'店门要落在步道垫面上，不能隔着草坪');
 // 湖滨东路 concentrates curb parking on the shopfront (west, lake-facing) side;
 // the east side is the 厦门站 plaza with no curb lane. Assert the shopfront-side
 // string rather than the Shenzhen two-wall split.
 const westCars=plan.parked.filter(p=>{const q=proj(p);return p.x<q.x&&tOf(p)>0.15&&tOf(p)<0.5;});
 assert.ok(westCars.length>=4,'湖滨东路西墙要排成一串路边停车，驾驶段不能只剩一辆');
 assert.ok(plan.pits.filter(p=>{const t=tOf(p);return t>0.15&&t<0.45;}).length>=2,'驾驶段路缘要有树池，不能只剩树冠');
 assert.ok(plan.signals.filter(p=>{
  const q=proj(p);
  return q.t>0.08&&q.t<0.9;
 }).length>=2,'红绿灯要落在湖滨东路行驶段上，不能只堆在厦门站北端');
 assert.ok(plan.crossings.length>=8&&plan.stops.length>=2,'湖滨东路路口要有斑马线和停止线，不能只剩灯杆');
 assert.ok(plan.crossings.some(p=>{
  const q=proj(p);
  return q.t>0.42&&q.t<0.52&&q.d<12;
 }),'湖滨东路×禾祥东路路口的斑马线要落在驾驶脊上，不能只埋在21米外的湖滨东路单路下');
 assert.ok(plan.crossings.every(p=>{
  let best=Infinity,width=9;
  for(const r of data.roads){
   if(!/湖滨东路|湖滨南路|禾祥东路|厦禾路|hubin/i.test(`${r.name??''} ${r.id}`))continue;
   for(let i=1;i<r.points.length;i++){
    const d=closest(p.x,p.z,r.points[i-1],r.points[i]).d;
    if(d<best){best=d;width=r.width;}
   }
  }
  return Math.abs(p.sx)*7.2/2<=width/2+.35;
 }),'斑马线停在车行道上，不能画到店前步道');
 assert.ok(westCars.every(p=>{
  const shop=plan.plinths.slice().sort((a,b)=>Math.hypot(a.x-p.x,a.z-p.z)-Math.hypot(b.x-p.x,b.z-p.z))[0];
  return shop&&Math.hypot(shop.x-p.x,shop.z-p.z)>3.0;
 }),'路边停车不能贴在店脸上当长凳');
 assert.ok(plan.parked.filter(p=>{const q=proj(p);return p.x<q.x&&tOf(p)>0.3&&tOf(p)<0.5;}).length>=1,'湖滨东路西墙步行带前也要有路边停车');
 assert.ok(plan.signs.some(p=>{
  const shop=plan.plinths.sort((a,b)=>Math.hypot(a.x-p.x,a.z-p.z)-Math.hypot(b.x-p.x,b.z-p.z))[0];
  if(!shop)return false;
  return proj(p).d+1.2<proj(shop).d;
 }),'店招要伸到湖滨东路路缘，不能只贴在17米外的店墙上');
 assert.ok(plan.plinths.some(p=>p.sz<0)&&plan.plinths.some(p=>p.sz>0),'两侧店面都要朝向车道，不能只翻开一边');
});
