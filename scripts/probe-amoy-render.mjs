/** GTA_AMOY render probe: inspect runtime materials on terrain/roads/water meshes. */
import {chromium} from 'playwright';
const browser=await chromium.launch({channel:'msedge',headless:false});
const page=await browser.newPage({viewport:{width:1600,height:900}});
page.on('pageerror',e=>console.log('[pageerror]',String(e).slice(0,300)));
await page.goto('http://127.0.0.1:5173/?quality=low',{waitUntil:'domcontentloaded'});
for(let i=0;i<75;i++){await page.waitForTimeout(2000);if(await page.evaluate(()=>!!(window.__SHENCHENGJI_CITY__?.ready))){console.log('ready after',(i+1)*2,'s');break;}}
const probe=await page.evaluate(()=>{
 const w=window.__SHENCHENGJI_CITY__.world,out={};
 const pick=(re)=>{const meshes=w.scene.meshes.filter(m=>re.test(m.name)&&m.getTotalVertices()>0).slice(0,3);
  return meshes.map(m=>{const mat=m.material;return {mesh:m.name,material:mat?.name??"null",albedoTexture:mat?.albedoTexture?mat.albedoTexture.name??"(no-name)":"none",texSize:mat?.albedoTexture?.getSize?.()?.join?.('x')??null};});};
 out.terrain=pick(/^terrain_/);out.roads=pick(/^roads_/);out.buildings=pick(/^block_/);
 out.water=w.scene.meshes.filter(m=>m.name.includes('water')).slice(0,3).map(m=>({mesh:m.name,material:m.material?.name,albedo:m.material?.albedoTexture?.name??'none'}));
 out.skyMat=w.scene.getMeshByName('atmosphere')?.material?.name;
 out.envTexture=w.scene.environmentTexture?.name??String(w.scene.environmentTexture?.constructor?.name)+'(procedural)';
 out.envIntensity=w.scene.environmentIntensity;
 out.screenshots=w.scene.textures.filter(t=>t.name.includes('mirror')||t.name.includes('reflection')).map(t=>t.name);
 out.materialCount=w.scene.materials.length;
 out.textureErrors=w.scene.textures.filter(t=>t.isReady&&!t.isReady()).map(t=>t.name);
 const d=w.diagnostics();
 out.shaderCompiles=d.shaders.compiles;out.drawCalls=d.drawCalls;
 return out;});
console.log(JSON.stringify(probe,null,1));
await browser.close();
