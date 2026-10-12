import {filmProgress,orbit,type FilmPose,type FilmShot,type Point3} from './trailer-shots.ts';

/** Short caption-free loops for the README (`trailer.html?reel=readme`). Every shot is a real
 * camera orbit or a staged drive on the current assets; 6 s each so the GIFs stay small. */
const mix=(a:number,b:number,u:number)=>a+(b-a)*u;
function sweep(target:Point3,yaw:[number,number],pitch:[number,number],distance:[number,number],seconds:number,fov=.85){
 return (t:number):FilmPose=>{const u=filmProgress(t,seconds);return orbit(target,mix(yaw[0],yaw[1],u),mix(pitch[0],pitch[1],u),mix(distance[0],distance[1],u),fov);};
}
export const README_SHOTS:FilmShot[]=[
 {id:'r1',title:'双子塔 · 黄昏',location:'思明 · 世茂海峡大厦',mode:'sunset',seconds:6,pose:sweep([-2200,105,-3118],[-.62,-.34],[.07,.11],[600,540],6)},
 {id:'r2',title:'筼筜湖 · 白天',location:'思明 · 白鹭洲与筼筜湖',mode:'day',seconds:6,pose:sweep([-1544,140,-120],[.62,.36],[.19,.17],[1350,1250],6,.82)},
 {id:'r3',title:'会展 · 夜',location:'思明 · 厦门国际会展中心',mode:'night',seconds:6,pose:sweep([2614,125,-1870],[.34,-.02],[.15,.13],[640,600],6,.88)},
 {id:'r4',title:'鼓浪屿 · 绿荫',location:'思明 · 鼓浪屿',mode:'day',seconds:6,pose:sweep([-3143,78,-2698],[-2.55,-2.12],[.21,.19],[540,500],6,.86)},
 {id:'r5',title:'环岛干道 · 夜间驾驭',location:'环岛干道 · 自由驾驶',mode:'night',seconds:6,drive:{start:1720,speed:16.5,acceleration:.12},pose:()=>orbit([0,0,0],0,0,1)},
 {id:'r6',title:'仙岳山 · 山与城',location:'湖里 · 仙岳山公园',mode:'sunset',seconds:6,pose:sweep([-1216,30,1270],[Math.PI-.16,Math.PI+.10],[.24,.22],[880,820],6)}
];
