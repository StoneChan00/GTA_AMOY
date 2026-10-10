/** Autopilot one-way compliance check (M3 bugfix: 自动前往逆行).
 * 1) The shared RoadGraph must carry a real one-way rule (set by CityWorld.startTraffic).
 * 2) Every planned autopilot route must be direction-legal: no segment against a oneway road.
 * 3) A real drive along a oneway-heavy route must never meet oncoming traffic on the same oneway road. */
import {chromium} from 'playwright';
const browser=await chromium.launch({channel:'msedge',headless:false});
const page=await browser.newPage({viewport:{width:1600,height:900}});
await page.goto('http://127.0.0.1:5173/?quality=low',{waitUntil:'domcontentloaded'});
let booted=false;
for(let i=0;i<75;i++){await page.waitForTimeout(2000);if(await page.evaluate(()=>!!(window.__SHENCHENGJI_CITY__?.ready))){booted=true;console.log('ready');break;}}
if(!booted){console.error('BOOT FAILED');await browser.close();process.exit(1);}

const result=await page.evaluate(async()=>{
 const w=window.__SHENCHENGJI_CITY__.world,wrap=a=>Math.atan2(Math.sin(a),Math.cos(a));
 // --- 1) wiring: the graph's one-way rule must reject the reverse sense of at least one real oneway road
 const graph=w.traffic.graph;let onewayWired=false,onewayRoads=0;
 for(const r of w.data.roads){if(!r.oneway||r.points.length<2)continue;onewayRoads++;
  const find=p=>graph.nodes.findIndex(n=>Math.hypot(n[0]-p[0],n[1]-p[1])<.5);
  const a=find(r.points[0]),b=find(r.points.at(-1));
  if(a>=0&&b>=0&&graph.directionAllowed(a,b)&&!graph.directionAllowed(b,a)){onewayWired=true;break;}}
 // --- 2) plan a route to every landmark and audit each polyline against road direction.
 // Skip the first and last segments: they are lateral docking connectors (car→projection,
 // projection→arrival) that are perpendicular to the road by construction, never wrong-way.
 const audit=route=>{let onewaySegs=0,violations=0,detail=[];
  for(let i=1;i+1<route.length-1;i++){const [ax,az]=route[i],[bx,bz]=route[i+1];
   if(Math.hypot(bx-ax,bz-az)<.3)continue;
   const n=w.collision.nearest((ax+bx)/2,(az+bz)/2);
   if(!n||n.d>n.road.width/2+1||!n.road.oneway)continue;
   onewaySegs++;
   if((bx-ax)*Math.sin(n.yaw)+(bz-az)*Math.cos(n.yaw)<=0){violations++;detail.push({x:+ax.toFixed(1),z:+az.toFixed(1),road:n.road.name||n.road.id});}}
  return {onewaySegs,violations,detail};};
 const plans=[];
 for(const lm of w.data.landmarks){if(!lm.arrival||!lm.arrival.every(Number.isFinite))continue;
  w.startAutoDrive(lm);let route=null;
  for(let t=0;t<40;t++){await new Promise(r=>setTimeout(r,250));const st=w.autopilot.status;
   if(st.route.length>1){route=st.route;break;}if(st.phase==='blocked')break;}
  const st=w.autopilot.status;const check=route?audit(route):null;
  plans.push({id:lm.id,name:lm.name,phase:st.phase,points:route?route.length:0,...check});
  w.cancelAutoDrive('verify-next');await new Promise(r=>setTimeout(r,150));}
 // --- 3) real drive: pick a reachable 150-800m destination whose plan uses the most oneway segments
 const s=w.state,candidates=plans.filter(p=>p.points>1&&p.phase!=='blocked')
  .map(p=>{const lm=w.data.landmarks.find(m=>m.id===p.id);const d=Math.hypot(lm.arrival[0]-s.x,lm.arrival[1]-s.z);return {...p,straight:d};})
  .filter(p=>p.straight>150&&p.straight<800).sort((a,b)=>b.onewaySegs-a.onewaySegs);
 const target=candidates[0];
 const drive={found:!!target,onewayOncoming:0,encounters:[],samples:0,phases:[],minRemaining:Infinity};
 if(target){const lm=w.data.landmarks.find(m=>m.id===target.id);
  w.startAutoDrive(lm);
  for(let t=0;t<340;t++){await new Promise(r=>setTimeout(r,300));
   const st=w.autopilot.status,p=w.state;drive.samples++;if(!drive.phases.includes(st.phase))drive.phases.push(st.phase);
   drive.minRemaining=Math.min(drive.minRemaining,st.remainingDistance);
   const pn=w.collision.nearest(p.x,p.z);
   for(const c of (w.traffic?.cars??[])){
    const d=Math.hypot(c.x-p.x,c.z-p.z);if(d>30)continue;
    if(Math.abs(wrap(c.yaw-p.yaw))<2.4)continue;               // not opposing
    if(!pn||!pn.road.oneway)continue;                           // player not on a oneway road
    const cn=w.collision.nearest(c.x,c.z);
    if(!cn||cn.road.id!==pn.road.id)continue;                   // different roadway (dual carriageway)
    drive.onewayOncoming++;
    drive.encounters.push({t:+(t*.3).toFixed(1),x:+p.x.toFixed(1),z:+p.z.toFixed(1),road:pn.road.name||pn.road.id,d:+d.toFixed(1)});
   }
   if(!st.active)break;}
  drive.final=w.autopilot.status.phase;drive.arrived=w.autopilot.status.phase==='arrived';}
 return {onewayWired,onewayRoads,plans,drive};});

const summary={wired:result.onewayWired,onewayRoads:result.onewayRoads,
 planned:result.plans.filter(p=>p.points>0).length,blocked:result.plans.filter(p=>p.phase==='blocked').length,
 violating:result.plans.filter(p=>p.violations>0).map(p=>({id:p.id,name:p.name,violations:p.violations,detail:p.detail.slice(0,3)})),
 onewaySegsTotal:result.plans.reduce((s,p)=>s+(p.onewaySegs||0),0),
 drive:{found:result.drive.found,phases:result.drive.phases,samples:result.drive.samples,
  onewayOncoming:result.drive.onewayOncoming,encounters:result.drive.encounters.slice(0,5),
  minRemaining:+result.drive.minRemaining.toFixed(1),arrived:result.drive.arrived,final:result.drive.final}};
console.log(JSON.stringify(summary,null,1));
let fail=0;
if(!result.onewayWired){console.error('FAIL: graph one-way rule not wired');fail=1;}
if(summary.violating.length){console.error('FAIL: routes with wrong-way segments: '+summary.violating.map(p=>p.id).join(','));fail=1;}
if(result.drive.found&&result.drive.onewayOncoming>0){console.error('FAIL: oncoming traffic met on one-way roads');fail=1;}
if(result.drive.found&&!result.drive.arrived&&result.drive.minRemaining>=Infinity){console.error('FAIL: no progress');fail=1;}
console.log(fail?'RESULT: FAIL':'RESULT: PASS');
await browser.close();process.exit(fail);
