// Definitive probe: for each candidate street, find the best straight window
// (>=0.7 km) and report geometry + building frontage + landmark proximity so a
// spine + anchor pair can be chosen from real data.
import {readFileSync} from 'node:fs';
type V2=[number,number];
type Road={id:string;name:string;kind:string;width:number;oneway:boolean;points:V2[]};
type Landmark={id:string;name:string;x:number;z:number;arrival:V2};
const d=JSON.parse(readFileSync(new URL('../public/city/city.json',import.meta.url),'utf8')) as {
  roads:Road[];buildings:{rings:V2[][];height:number}[];landmarks:Landmark[];
};
const segDistPts=(x:number,z:number,p:V2[])=>{let b=Infinity;for(let i=1;i<p.length;i++){const dx=p[i][0]-p[i-1][0],dz=p[i][1]-p[i-1][1],l2=dx*dx+dz*dz;let t=l2?((x-p[i-1][0])*dx+(z-p[i-1][1])*dz)/l2:0;t=Math.max(0,Math.min(1,t));b=Math.min(b,Math.hypot(x-(p[i-1][0]+dx*t),z-(p[i-1][1]+dz*t)));}return b;};
const segDist=(x:number,z:number,a:V2,b:V2)=>{const dx=b[0]-a[0],dz=b[1]-a[1],l2=dx*dx+dz*dz;let t=l2?((x-a[0])*dx+(z-a[1])*dz)/l2:0;t=Math.max(0,Math.min(1,t));return Math.hypot(x-(a[0]+dx*t),z-(a[1]+dz*t));};

const NAMES=['嘉禾路','吕岭路','湖滨东路','厦禾路','莲前东路'];

for(const name of NAMES){
  const roads=d.roads.filter(r=>r.name===name&&r.points.length>=2);
  const segs:{a:V2;b:V2;len:number}[]=[];
  for(const r of roads)for(let i=1;i<r.points.length;i++){const a=r.points[i-1],b=r.points[i];const len=Math.hypot(b[0]-a[0],b[1]-a[1]);if(len>=2)segs.push({a,b,len});}
  const pts:V2[]=[];
  for(const s of segs){for(let t=0;t<=1;t+=.25)pts.push([s.a[0]+(s.b[0]-s.a[0])*t,s.a[1]+(s.b[1]-s.a[1])*t]);}
  console.log(`\n######## ${name}  (${roads.length} roads, ${segs.length} segs, ${segs.reduce((s,e)=>s+e.len,0).toFixed(0)}m total)`);

  interface Win{ax:number;az:number;bx:number;bz:number;len:number;dev:number;n:number;yaw:number}
  const wins:Win[]=[];
  for(const s of segs){
    if(s.len<60)continue;
    const ax=s.a[0],az=s.a[1],dx=s.b[0]-s.a[0],dz=s.b[1]-s.a[1],ylen=Math.hypot(dx,dz),yaw=Math.atan2(dx,dz);
    let dev=0,n=0;
    for(const p of pts){
      const along=(p[0]-ax)*dx/ylen+(p[1]-az)*dz/ylen;
      if(along>=-40&&along<=ylen+40){
        const perp=Math.abs((p[0]-ax)*(-dz/ylen)+(p[1]-az)*(dx/ylen));
        if(perp<=60){dev=Math.max(dev,perp);n++;}
      }
    }
    if(n<8)continue;
    wins.push({ax,az,bx:s.b[0],bz:s.b[1],len:ylen,dev,n,yaw});
  }
  wins.sort((a,b)=>b.len-a.len);
  const seen=new Set<string>();let shown=0;
  for(const w of wins){
    const key=`${Math.round(w.ax)},${Math.round(w.az)}->${Math.round(w.bx)},${Math.round(w.bz)}`;
    if(seen.has(key))continue;seen.add(key);
    if(w.len<700)continue;
    console.log(`  WINDOW len=${w.len.toFixed(0)}m maxPerpDev=${w.dev.toFixed(0)}m  from(${w.ax.toFixed(0)},${w.az.toFixed(0)}) to(${w.bx.toFixed(0)},${w.bz.toFixed(0)})`);
    let b20=0,b40=0;
    for(const b of d.buildings){const ring=b.rings[0];if(!ring||ring.length<3)continue;let best=Infinity;for(const p of ring){best=Math.min(best,segDist(p[0],p[1],[w.ax,w.az],[w.bx,w.bz]));}if(best<20)b20++;else if(best<40)b40++;}
    console.log(`     buildings(vtx)<20m=${b20} <40m=${b40}`);
    if(++shown>=3)break;
  }
  const lm=d.landmarks.map(m=>{let b=Infinity;for(const r of roads)b=Math.min(b,segDistPts(m.x,m.z,r.points));return{...m,d:b};}).sort((a,b)=>a.d-b.d);
  console.log(`  landmarks near street: `+lm.slice(0,4).map(m=>`${m.id} d=${m.d.toFixed(0)}m`).join(' | '));
}
