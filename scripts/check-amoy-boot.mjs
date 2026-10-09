/** GTA_AMOY M1 boot verification: load the city, drive a bit, capture evidence. */
import {chromium} from 'playwright';
import fs from 'node:fs';
fs.mkdirSync('output/amoy',{recursive:true});
const browser=await chromium.launch({channel:'msedge',headless:false});
const page=await browser.newPage({viewport:{width:1600,height:900}});
page.on('console',m=>{const t=m.text();if(!t.includes('BJS')&&!t.includes('ExperimentalWarning'))console.log('[console]',t.slice(0,220));});
page.on('pageerror',e=>console.log('[pageerror]',String(e).slice(0,400)));
await page.goto('http://127.0.0.1:5173/?quality=low',{waitUntil:'domcontentloaded'});
let loaded=false,loadErr=null;
for(let i=0;i<75;i++){
 await page.waitForTimeout(2000);
 const status=await page.evaluate(()=>{
  const overlay=document.getElementById('city-loading');
  const failure=overlay?.querySelector('.city-loader-failure p')?.textContent??'';
  return {gone:!overlay,failure,ready:!!(window.__SHENCHENGJI_CITY__?.ready)};
 });
 if(status.failure){loadErr=status.failure;break;}
 if(status.gone&&status.ready){loaded=true;console.log('city ready after',(i+1)*2,'s');break;}
}
if(!loaded){console.log('LOAD RESULT: '+(loadErr?('FAILED — '+loadErr):'timeout / not ready'));await page.screenshot({path:'output/amoy/boot-failed.png'});}
else{
 await page.waitForTimeout(2500);
 await page.screenshot({path:'output/amoy/boot-spawn.png'});
 await page.keyboard.down('KeyW');
 await page.waitForTimeout(5000);
 await page.keyboard.up('KeyW');
 await page.screenshot({path:'output/amoy/drive-huandao.png'});
 const state=await page.evaluate(()=>window.__SHENCHENGJI_CITY__?.state);
 const perf=await page.evaluate(()=>window.__SHENCHENGJI_CITY__?.performance);
 const diagnostics=await page.evaluate(()=>{const d=window.__SHENCHENGJI_CITY__?.world?.diagnostics?.();return d?{drawCalls:d.drawCalls,shaders:d.shaders.compiles,materials:d.shaders.materials,lights:d.shaders.lights}:null;});
 console.log('state',JSON.stringify(state));
 console.log('performance',JSON.stringify({meanFps:perf?.meanFps?.toFixed?.(1)??perf?.meanFps,p95:perf?.p95?.toFixed?.(1)??perf?.p95,meshes:perf?.meshes,triangles:perf?.triangles,over50ms:perf?.over50ms}));
 console.log('diagnostics',JSON.stringify(diagnostics));
 // night + day modes for the lighting check
 await page.keyboard.press('KeyL');await page.waitForTimeout(1800);await page.screenshot({path:'output/amoy/night.png'});
 await page.keyboard.press('KeyL');await page.waitForTimeout(1800);await page.screenshot({path:'output/amoy/day.png'});
}
await browser.close();
