import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {CityAutopilot,type AutopilotTraffic} from '../src/city-autopilot.ts';
import {CityCollision,closest,stepCar,type CarState} from '../src/driving.ts';
import {RoadGraph} from '../src/navigation.ts';
import type {CityData,V2} from '../src/city-types.ts';

const DT=1/30;
function fixture(points:V2[],width=10) {
 const data:CityData={meta:{counts:{},extent:[-500,-500,500,500],horizontalScale:.6},
  land:[[[[-500,-500],[500,-500],[500,500],[-500,500],[-500,-500]]]],coast:[],
  roads:[{id:'road',name:'Test road',kind:'residential',width,oneway:false,points,grade:'0'}],
  buildings:[],green:[],water:[],landmarks:[],spawn:{x:points[0][0],z:points[0][1],yaw:0,road:'Test road'}};
 return {data,collision:new CityCollision(data),graph:new RoadGraph(data.roads)};
}
function car(x=0,z=0,yaw=0):CarState{return {x,z,yaw,speed:0,steer:0,distance:0};}
function tick(controller:CityAutopilot,state:CarState,collision:CityCollision,traffic:readonly AutopilotTraffic[]=[]) {
 const before={...state},start=performance.now(),result=controller.update(state,traffic,DT),updateMs=performance.now()-start;
 assert.deepEqual(state,before,'controller must not move the car itself');
 assert(Number.isFinite(result.input.throttle)&&Math.abs(result.input.throttle)<=1);
 assert(Number.isFinite(result.input.steer)&&Math.abs(result.input.steer)<=1);
 stepCar(state,result.input,DT);
 const nose=Math.sign(state.speed)*1.45;
 const collisionHit=collision.blocked(state.x+Math.sin(state.yaw)*nose,state.z+Math.cos(state.yaw)*nose)
  ||traffic.some(t=>Math.hypot(t.x-state.x,t.z-state.z)<2.7);
 if(collisionHit){state.x=before.x;state.z=before.z;state.distance=before.distance;state.speed=-before.speed*.15;}
 assert(Math.hypot(state.x-before.x,state.z-before.z)<=Math.abs(state.speed)*DT+.05,'no reset or teleport');
 return {result,collisionHit,updateMs};
}
function drive(controller:CityAutopilot,state:CarState,collision:CityCollision,seconds:number,traffic=(t:number):readonly AutopilotTraffic[]=>[]) {
 let hits=0,reverseFrames=0,waitingFrames=0,elapsed=seconds;const updates:number[]=[],slowUpdates:{ms:number;phase:string;reason:string|null;seconds:number}[]=[];
 for(let frame=0;frame<seconds/DT;frame++) {
  const sample=tick(controller,state,collision,traffic(frame*DT));
  hits+=Number(sample.collisionHit);reverseFrames+=Number(state.speed<-.2);
  updates.push(sample.updateMs);
  if(sample.updateMs>8)slowUpdates.push({ms:sample.updateMs,phase:sample.result.status.phase,reason:sample.result.status.reason,seconds:frame*DT});
  waitingFrames+=Number(sample.result.status.phase==='yielding');
  if(!sample.result.status.active){elapsed=frame*DT;break;}
 }
 updates.sort((a,b)=>a-b);
 const updateMs={mean:updates.reduce((a,b)=>a+b,0)/updates.length,p95:updates[Math.floor(updates.length*.95)],p99:updates[Math.floor(updates.length*.99)],max:updates.at(-1),over8:updates.filter(v=>v>8).length,over16:updates.filter(v=>v>16).length};
 return {seconds:elapsed,hits,reverseFrames,waitingFrames,updateMs,slowUpdates:slowUpdates.sort((a,b)=>b.ms-a.ms).slice(0,5)};
}
function assertArrived(controller:CityAutopilot,state:CarState,target:V2) {
 assert.equal(controller.status.phase,'arrived',JSON.stringify({phase:controller.status.phase,reason:controller.status.reason,remaining:controller.status.remainingDistance,state}));
 assert(Math.hypot(state.x-target[0],state.z-target[1])<=2.6,'park at the actual destination');
 assert(Math.abs(state.speed)<.2,'arrival means stopped');
 assert.equal(controller.status.remainingDistance,0);
 assert.equal(controller.status.etaSeconds,0);
}

test('real steering and wheelbase negotiate two turns and park without circling',()=>{
 const {collision,graph}=fixture([[0,0],[0,70],[65,70],[65,145]],12),controller=new CityAutopilot(graph,collision),state=car(),arrival:V2=[65,140];
 controller.start({id:'turns',name:'Two turns',arrival});
 const run=drive(controller,state,collision,100);assertArrived(controller,state,arrival);assert.equal(run.hits,0);
 const parked={...state};for(let i=0;i<300;i++)tick(controller,state,collision);
 assert(Math.hypot(state.x-parked.x,state.z-parked.z)<.03,'arrival remains parked');
});

test('opposite initial heading uses bounded real forward/reverse steering and then reaches the destination',()=>{
 const {collision,graph}=fixture([[0,-40],[0,160]],18),controller=new CityAutopilot(graph,collision),state=car(0,0,Math.PI),arrival:V2=[0,145];
 controller.start({id:'reverse-start',name:'Behind the car',arrival});
 const run=drive(controller,state,collision,120);assertArrived(controller,state,arrival);assert.equal(run.hits,0);assert(run.reverseFrames>0);
 assert(controller.status.maneuvers>0&&controller.status.maneuvers<=3);
});

test('a destination just behind the parking tolerance triggers a maneuver instead of driving away',()=>{
 for(const distance of [2.6,3.5,4.1])for(const width of [6,12]) {
  const {collision,graph}=fixture([[0,-40],[0,160]],width),controller=new CityAutopilot(graph,collision),state=car(0,0,Math.PI),arrival:V2=[0,distance];
  controller.start({id:'close-behind',name:'Close behind',arrival});
  const run=drive(controller,state,collision,90);assertArrived(controller,state,arrival);assert.equal(run.hits,0);
  assert(controller.status.maneuvers>0,'pure pursuit has no steering authority directly behind the car');
  assert(state.distance<40,'a nearby destination must not drive to the remote road end');
 }
});

test('narrow-road turns recover from offset angled starts at a dead end through the real steering rack',()=>{
 for(const z of [-38,0])for(const yaw of [Math.PI*.75,Math.PI*1.25]) {
  const {collision,graph}=fixture([[0,-40],[0,160]],4),controller=new CityAutopilot(graph,collision),state=car(.8,z,yaw),arrival:V2=[0,145];
  controller.start({id:'narrow-turn',name:'Narrow turn',arrival});let hits=0,reverseFrames=0,maxRoadDistance=0;
  for(let frame=0;frame<120/DT&&controller.status.active;frame++) {
   const sample=tick(controller,state,collision);hits+=Number(sample.collisionHit);reverseFrames+=Number(state.speed<-.2);
   maxRoadDistance=Math.max(maxRoadDistance,collision.nearest(state.x,state.z)!.d);
  }
  assertArrived(controller,state,arrival);assert.equal(hits,0);assert(reverseFrames>0);
  assert(maxRoadDistance<2.15,'recovery must not cut across the surrounding ground');
 }
});

test('arrival at a walled dead end can reverse the graph edges and drive back out',()=>{
 const {data}=fixture([[0,-40],[0,110]],6);
 data.buildings=[
  {id:'right-wall',height:8,style:'wall',rings:[[[4.2,-45],[20,-45],[20,115],[4.2,115],[4.2,-45]]]},
  {id:'left-wall',height:8,style:'wall',rings:[[[-4.2,-45],[-20,-45],[-20,115],[-4.2,115],[-4.2,-45]]]},
 ];
 const collision=new CityCollision(data),controller=new CityAutopilot(new RoadGraph(data.roads),collision),state=car(),end:V2=[0,108],returnTo:V2=[0,-30];
 controller.start({id:'dead-end',name:'Dead end',arrival:end});
 const outward=drive(controller,state,collision,60);assertArrived(controller,state,end);assert.equal(outward.hits,0);
 controller.start({id:'return',name:'Return along the same road',arrival:returnTo});
 const back=drive(controller,state,collision,120);assertArrived(controller,state,returnTo);assert.equal(back.hits,0);assert(back.reverseFrames>0);
 assert(controller.status.maneuvers>0);
 assert(controller.status.route.at(-1)![1]<controller.status.route[0][1],'the return route follows graph edges in the opposite direction');
});

test('manual takeover during a reversing maneuver immediately releases all automatic controls',()=>{
 const {collision,graph}=fixture([[0,-40],[0,160]],6),controller=new CityAutopilot(graph,collision),state=car(0,0,Math.PI);
 controller.start({id:'turn',name:'Turn',arrival:[0,145]});
 for(let frame=0;frame<30/DT&&state.speed>-.2;frame++)tick(controller,state,collision);
 assert(state.speed<-.2);assert.equal(controller.status.phase,'maneuvering');controller.cancel('manual-takeover');
 for(let i=0;i<30;i++)assert.deepEqual(controller.update(state,[],DT).input,{throttle:0,steer:0,handbrake:false});
 assert.equal(controller.status.phase,'cancelled');
});

test('moving traffic is followed and temporary full-width blockage resumes after the vehicle leaves',()=>{
 const {collision,graph}=fixture([[0,-20],[0,230]],6),arrival:V2=[0,160];
 const following=new CityAutopilot(graph,collision),s=car();following.start({id:'follow',name:'Follow',arrival});
 const run=drive(following,s,collision,90,t=>[{x:1.15,z:18+t*4,speed:15,yaw:0}]);
 assertArrived(following,s,arrival);assert.equal(run.hits,0);assert(run.seconds>30,'must account for slower leading traffic');
 const waiting=new CityAutopilot(graph,collision),w=car();waiting.start({id:'wait',name:'Wait',arrival});
 const waited=drive(waiting,w,collision,90,t=>t<12?[{x:0,z:24,speed:15,yaw:0}]:[]);
 assertArrived(waiting,w,arrival);assert.equal(waited.hits,0);assert(waited.waitingFrames>10,'stationary traffic is detected from actual positions, not its nominal speed');
});

test('persistent obstruction stops safely, and manual takeover immediately cancels future commands',()=>{
 const {collision,graph}=fixture([[0,-20],[0,150]],6),controller=new CityAutopilot(graph,collision,{maxWaitSeconds:4}),state=car();
 controller.start({id:'blocked',name:'Blocked',arrival:[0,130]});
 const blocker=[{x:0,z:24,speed:12,yaw:0}],run=drive(controller,state,collision,30,()=>blocker);
 assert.equal(controller.status.phase,'blocked');assert.equal(run.hits,0);assert(Math.abs(state.speed)<.2);assert(state.z<21);
 assert.equal(controller.status.reroutes,0,'a single blocked road has no invented detour');
 controller.start({id:'manual',name:'Manual',arrival:[0,130]});
 for(let i=0;i<30;i++)tick(controller,state,collision);
 controller.cancel('manual-takeover');
 for(let i=0;i<60;i++) {
  const result=controller.update(state,[],DT);assert.equal(result.status.phase,'cancelled');
  assert.deepEqual(result.input,{throttle:0,steer:0,handbrake:false});
 }
 assert.equal(controller.status.reason,'manual-takeover');
});

test('wide-road passing stays on the road and avoids the stopped traffic car',()=>{
 const {collision,graph}=fixture([[0,-20],[0,170]],18),controller=new CityAutopilot(graph,collision),state=car(),arrival:V2=[0,150];
 controller.start({id:'pass',name:'Pass stopped car',arrival});
 const run=drive(controller,state,collision,90,()=>[{x:1.15,z:35,speed:12,yaw:0}]);
 assertArrived(controller,state,arrival);assert.equal(run.hits,0);
});

test('selecting the current stopped destination immediately arrives without starting a loop',()=>{
 const {collision,graph}=fixture([[0,0],[0,100]],8),controller=new CityAutopilot(graph,collision),state=car(0,70);
 controller.start({id:'here',name:'Already here',arrival:[0,70]});
 tick(controller,state,collision);assertArrived(controller,state,[0,70]);assert.equal(state.distance,0);
});

test('disconnected road graph stops without moving; invalid destinations are rejected',()=>{
 const {collision,data}=fixture([[0,0],[0,20]],6);
 const graph=new RoadGraph(data.roads,{nodes:[[0,0],[0,20],[100,0],[100,20]],edges:[[0,1],[2,3]]});
 const controller=new CityAutopilot(graph,collision),state=car();
 assert.throws(()=>controller.start({id:'bad',name:'Bad',arrival:[NaN,0]}));
 controller.start({id:'unreachable',name:'Unreachable',arrival:[100,20]});
 const {result}=tick(controller,state,collision);assert.equal(result.status.phase,'blocked');assert.equal(result.status.reason,'no-road-route');assert.equal(state.distance,0);
});

test('one-way roads: the planner and map preview loop around instead of reversing into traffic',()=>{
 // A clockwise loop whose two long sides are one-way; the connectors are two-way.
 // The destination sits 40 units "behind" the car on the same one-way road, so
 // the only legal route drives the whole loop forward (~200 units). Reversing
 // along the one-way edge — what an undirected search returns — is a regression.
 const loop:CityData={meta:{counts:{},extent:[-40,-20,40,120],horizontalScale:.6},
  land:[[[[-40,-20],[40,-20],[40,120],[-40,120],[-40,-20]]]],coast:[],
  roads:[
   {id:'north-flow',name:'North flow',kind:'residential',width:10,oneway:true,points:[[0,0],[0,100]]},
   {id:'south-flow',name:'South flow',kind:'residential',width:10,oneway:true,points:[[20,100],[20,0]]},
   {id:'top-link',name:'Top link',kind:'residential',width:10,oneway:false,points:[[0,100],[20,100]]},
   {id:'bottom-link',name:'Bottom link',kind:'residential',width:10,oneway:false,points:[[0,0],[20,0]]},
  ],
  buildings:[],green:[],water:[],landmarks:[],spawn:{x:0,z:0,yaw:0,road:'North flow'}};
 const collision=new CityCollision(loop),graph=new RoadGraph(loop.roads);
 // Same rule the world publishes for NPC traffic: one-way roads allow travel only along their polyline.
 graph.directionAllowed=(from,to)=>{const p=graph.nodes[from],q=graph.nodes[to],n=collision.nearest((p[0]+q[0])/2,(p[1]+q[1])/2);return !n?.road.oneway||(q[0]-p[0])*Math.sin(n.yaw)+(q[1]-p[1])*Math.cos(n.yaw)>0;};
 const pathLength=(points:V2[])=>points.reduce((s,p,i)=>i?s+Math.hypot(p[0]-points[i-1][0],p[1]-points[i-1][1]):s,0);
 const preview=graph.route([0,50],[0,10]);
 assert(pathLength(preview)>150,`map preview must loop around one-way roads, got ${pathLength(preview).toFixed(1)}`);
 const controller=new CityAutopilot(graph,collision),state=car(0,50);
 controller.start({id:'oneway-behind',name:'Behind on a one-way road',arrival:[0,10]});
 const run=drive(controller,state,collision,180);
 assertArrived(controller,state,[0,10]);assert.equal(run.hits,0);
 assert(state.distance>150,`the car must detour around the loop (odometer ${state.distance.toFixed(1)}), not reverse against one-way traffic`);
});

const actual=JSON.parse(fs.readFileSync('public/city/city.json','utf8'));
const detail=JSON.parse(fs.readFileSync('public/city/landmark-detail.json','utf8'));
actual.buildings=actual.buildings.filter((b:{id:string})=>!detail.baseBuildingIds.includes(b.id));
for(const b of detail.collisionFootprints)actual.buildings.push({...b,height:1,style:'detail'});
for(const m of detail.landmarks) {const index=actual.landmarks.findIndex((p:{id:string})=>p.id===m.id);if(index<0)actual.landmarks.push(m);else actual.landmarks[index]={...actual.landmarks[index],...m};}
const city=actual as CityData,cityCollision=new CityCollision(city),cityGraph=new RoadGraph(city.roads,JSON.parse(fs.readFileSync('public/city/navigation.json','utf8')));
// Same one-way rule the world publishes in CityWorld.startTraffic: these
// integration tests must route like production traffic, never reversing
// along a directed road (53.5% of this city's road length is one-way).
cityGraph.directionAllowed=(from,to)=>{const p=cityGraph.nodes[from],q=cityGraph.nodes[to],n=cityCollision.nearest((p[0]+q[0])/2,(p[1]+q[1])/2);return !n?.road.oneway||(q[0]-p[0])*Math.sin(n.yaw)+(q[1]-p[1])*Math.cos(n.yaw)>0;};
test('actual two-way Zongsilu turns toward destinations 3.5 and 40 units behind the car',t=>{
 const road=city.roads.find(r=>r.id==='way/128826870')!;assert(road&&!road.oneway);assert.equal(road.width,12);
 const [a,b]=road.points,roadYaw=Math.atan2(b[0]-a[0],b[1]-a[1]),x=(a[0]+b[0])/2,z=(a[1]+b[1])/2;
 for(const distance of [3.5,40]) {
  const state=car(x,z,roadYaw+Math.PI),initial={...state},arrival:V2=[x+Math.sin(roadYaw)*distance,z+Math.cos(roadYaw)*distance];
  assert(!cityCollision.blocked(x,z)&&!cityCollision.blocked(...arrival));
  const controller=new CityAutopilot(cityGraph,cityCollision);controller.start({id:'real-road-turn',name:road.name,arrival});
  const run=drive(controller,state,cityCollision,120);assertArrived(controller,state,arrival);assert.equal(run.hits,0);
  assert(controller.status.maneuvers>0);assert(run.reverseFrames>0);
  t.diagnostic(JSON.stringify({road:road.name,initial,arrival,maneuvers:controller.status.maneuvers,...run}));
 }
});
for(const [name,start] of [
 ['actual spawn pose',[city.spawn.x,city.spawn.z,city.spawn.yaw]],
 ['trunk approach pose',[2849,-1843,-2.393]],
] as const)test(`stationary traffic on Huandao Avenue: ${name} safely detours to the convention centre`,t=>{
 const destination=city.landmarks.find(m=>m.id==='huizhan')!,controller=new CityAutopilot(cityGraph,cityCollision),state=car(...start);
 // A stopped car in the Huandao Avenue lane recreates a blocked one-way trunk;
 // the parallel service street is the legal detour around it. The 1.15-unit lane
 // offset leaves less than the 3.05 passing bubble to the wide offset line, so
 // the controller must wait and reroute instead of squeezing past.
 const stoppedTraffic=[{x:2827.9,z:-1864.5,speed:12,yaw:-2.393}];
 controller.start(destination);const run=drive(controller,state,cityCollision,600,()=>stoppedTraffic);
 assertArrived(controller,state,destination.arrival);assert.equal(run.hits,0);
 assert.equal(controller.status.reroutes,1);assert(run.waitingFrames>60,'wait for observed stationary traffic before rerouting');
 const planned=controller.status.route,obstacle=stoppedTraffic[0];
 assert(planned.slice(1).every((p,i)=>closest(obstacle.x,obstacle.z,planned[i],p).d>3.05),'the detour must not seed the far side of an obstructed start edge');
 t.diagnostic(JSON.stringify({name,state,reroutes:controller.status.reroutes,...run}));
});
const destinations=process.env.AUTOPILOT_ALL_DESTINATIONS==='1'?city.landmarks.map(m=>m.id):['huizhan','xiamenzhan','gaoqi','shimao'];
for(const id of destinations)test(`actual merged city: opening → ${id} completes entirely through stepCar`,t=>{
 const destination=city.landmarks.find(m=>m.id===id)!,controller=new CityAutopilot(cityGraph,cityCollision),state:CarState={...city.spawn,speed:0,steer:0,distance:0};
 controller.start(destination);const run=drive(controller,state,cityCollision,id==='huizhan'?400:1200);
 assertArrived(controller,state,destination.arrival);assert.equal(run.hits,0);assert(state.distance>(id==='huizhan'?500:2500));
 t.diagnostic(JSON.stringify({id,distance:state.distance,maneuvers:controller.status.maneuvers,...run}));
});

test('faster main-road cruise remains road-aware and brakes before the destination',t=>{
 const runFor=(kind:string,cruiseSpeed?:number)=>{const {collision,graph,data}=fixture([[0,0],[0,450]],12);data.roads[0].kind=kind;const controller=new CityAutopilot(graph,collision,{cruiseSpeed}),state=car(),arrival:V2=[0,430];controller.start({id:kind,name:kind,arrival});let peak=0,hits=0,seconds=0;for(let i=0;i<3000&&controller.status.active;i++){const sample=tick(controller,state,collision);peak=Math.max(peak,state.speed);hits+=Number(sample.collisionHit);seconds=i*DT;}assertArrived(controller,state,arrival);assert.equal(hits,0);return{peak,seconds};};
 const main=runFor('primary'),local=runFor('residential'),service=runFor('service'),previousCeiling=runFor('primary',13);t.diagnostic(JSON.stringify({main,local,service,previousCeiling}));
 assert(main.peak>22&&main.peak<24.5,JSON.stringify(main));assert(local.peak<=15.1);assert(service.peak<=10.1);assert(main.seconds<local.seconds*.8,'main-road cruise should produce a materially faster journey');assert(main.seconds<previousCeiling.seconds*.75,'straight-route journey should be at least 25% shorter than the previous 13-unit ceiling');
});

test('higher main-road cruise anticipates a right angle and stopped traffic without collisions',()=>{
 const {collision,graph,data}=fixture([[0,0],[0,260],[150,260]],12);data.roads[0].kind='primary';const controller=new CityAutopilot(graph,collision),state=car(),arrival:V2=[145,260];controller.start({id:'fast-turn',name:'Fast turn',arrival});let peak=0,nearTurnPeak=0,hits=0;
 for(let i=0;i<6000&&controller.status.active;i++){const sample=tick(controller,state,collision);peak=Math.max(peak,state.speed);if(Math.hypot(state.x,state.z-260)<8)nearTurnPeak=Math.max(nearTurnPeak,state.speed);hits+=Number(sample.collisionHit);}
 assertArrived(controller,state,arrival);assert.equal(hits,0);assert(peak>22);assert(nearTurnPeak<8,'braking must occur before a high-speed right angle');
 const straight=fixture([[0,-20],[0,450]],6);straight.data.roads[0].kind='primary';const waiting=new CityAutopilot(straight.graph,straight.collision,{maxWaitSeconds:4}),w=car();waiting.start({id:'fast-blocked',name:'Fast blocked',arrival:[0,430]});const run=drive(waiting,w,straight.collision,60,()=>[{x:0,z:180,speed:0,yaw:0}]);assert.equal(run.hits,0);assert.equal(waiting.status.phase,'blocked');assert(w.z<177.4);assert(Math.abs(w.speed)<.2);
});
