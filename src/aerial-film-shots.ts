import {filmProgress,orbit,type FilmPose,type FilmShot,type Point3} from './trailer-shots.ts';

// Scaled city coordinates (Xiamen island). All shots are real camera
// translations or orbits over mapped landmarks: the Shimao sails, Gulangyu,
// Xianyue hill, Wuyuan bay and the conference-centre coast.
const mix=(a:number,b:number,u:number)=>a+(b-a)*u;
const point=(a:Point3,b:Point3,u:number):Point3=>a.map((v,i)=>mix(v,b[i],u)) as Point3;
function fly(a:FilmPose,b:FilmPose,duration:number,bend:Point3=[0,0,0]){
 return (seconds:number):FilmPose=>{
  const u=filmProgress(seconds,duration),arc=4*u*(1-u),eye=point(a.eye,b.eye,u);
  return {eye:eye.map((v,i)=>v+bend[i]*arc) as Point3,target:point(a.target,b.target,u),fov:mix(a.fov,b.fov,u)};
 };
}
const cbd:Point3=[300,-150,600];
const lastOrbit=orbit(cbd,1.65,.74,1900,.80);
export const AERIAL_SHOTS:FilmShot[]=[
 {id:'01',title:'城市初现 · 全域推进',location:'厦门 · 城市全景',mode:'day',seconds:16,
  pose:fly({eye:[-2600,1500,-4300],target:[-600,-100,200],fov:.75},
           {eye:[-1200,950,-2400],target:[600,-100,400],fov:.76},16,[90,60,0])},
 {id:'02',title:'俯冲天际线 · 沙坡尾',location:'思明 · 双子塔天际线',mode:'day',seconds:16,
  pose:fly({eye:[-1200,950,-2400],target:[600,-100,400],fov:.76},
           {eye:[-1560,430,-2760],target:[-2200,95,-3118],fov:.88},16,[-150,80,-70])},
 {id:'03',title:'越过楼群 · 山城展开',location:'湖里 · 仙岳山与城',mode:'day',seconds:14,
  pose:t=>{const u=filmProgress(t,14);return orbit([-900,-40,800],mix(-1,-.60,u),mix(.80,.86,u),mix(1350,2100,u),.86);}},
 {id:'04',title:'城市长轴 · 纵贯鹭岛',location:'嘉禾路 · 城市纵轴',mode:'sunset',seconds:14,
  pose:fly({eye:[400,1150,3600],target:[200,-500,1800],fov:.94},
           {eye:[150,1250,500],target:[-100,-700,-1700],fov:.94},14,[0,100,0])},
 {id:'05',title:'从海峡到双子塔',location:'思明 · 鹭江海峡与世茂双塔',mode:'sunset',seconds:16,
  pose:fly({eye:[-4400,1250,-2600],target:[-3143,40,-2698],fov:.92},
           {eye:[-2900,500,-3700],target:[-2200,100,-3118],fov:.89},16,[130,150,0])},
 {id:'06',title:'飞越万家灯火 · 厦港',location:'思明 · 厦港与老城',mode:'night',seconds:16,
  pose:fly({eye:[-700,1150,-3800],target:[-1600,-150,-2700],fov:.95},
           {eye:[1500,1000,-3500],target:[-900,-200,-2800],fov:.95},16,[0,100,-160])},
 {id:'07',title:'城市巨环 · 五缘湾',location:'湖里 · 五缘湾夜航',mode:'night',seconds:14,
  pose:t=>{const u=filmProgress(t,14);return orbit([2006,10,3206],mix(1.0,1.65,u),mix(.80,.74,u),mix(2200,1700,u),.80);}},
 {id:'08',title:'万城归于一幅天际线',location:'厦门 · 天际之上',mode:'night',seconds:14,
  pose:fly(lastOrbit,{eye:[-2500,1650,-1400],target:[600,-200,300],fov:.70},14,[-160,80,0])}
];
