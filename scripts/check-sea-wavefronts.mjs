/** Sea wavefront A/B: sun-glitter crosshatch check (day mode).
 * Shots look WNW into the day sun (azimuth -71°) across the west strait. */
import {chromium} from 'playwright';
import fs from 'node:fs';

const tag = process.argv[2] ?? 'after';
const outDir = 'output/amoy/sea-wavefronts';
fs.mkdirSync(outDir, {recursive: true});
const browser = await chromium.launch({channel: 'msedge', headless: true});
const page = await browser.newPage({viewport: {width: 1440, height: 810}});
await page.goto('http://127.0.0.1:5173/?quality=low', {waitUntil: 'domcontentloaded'});
let booted = false;
for (let i = 0; i < 180; i++) {
  await page.waitForTimeout(2000);
  if (await page.evaluate(() => !!(window.__SHENCHENGJI_CITY__?.ready))) { booted = true; break; }
}
if (!booted) { console.error('BOOT FAILED'); await browser.close(); process.exit(1); }
await page.waitForTimeout(4000);
await page.evaluate(() => {
  const w = window.__SHENCHENGJI_CITY__.world;
  w.toggleAerial(); w.setLightMode('day');
  window.__shot = (cx, cy, cz, tx, ty, tz) => {
    const ob = w.observer;
    ob.focus = {x: tx, y: ty, z: tz};
    ob.yaw = Math.atan2(tx - cx, tz - cz);
    ob.pitch = Math.asin(Math.max(-1, Math.min(1, (cy - ty) / Math.hypot(tx - cx, ty - cy, tz - cz))));
    ob.distance = Math.hypot(tx - cx, ty - cy, tz - cz);
  };
  for (const rtt of [w.mirror, w.waterMirror]) { rtt.refreshRate = 1; rtt.resetRefreshCounter(); }
});
await page.waitForTimeout(1500);
// sun azimuth -71deg: (east,north) direction (-0.945, +0.326)
const shots = [
  ['glitter-high', -2800, 40, -3200, -2800 - 2079, 6, -3200 + 717],   // south strait, into sun
  ['glitter-graze', -3000, 14, -3600, -3000 - 1796, 1, -3600 + 619],  // SW strait, low, into sun
  ['away-control', -2800, 40, -3200, -2800 + 2079, 6, -3200 - 717],   // away from sun (island side)
];
for (const [name, cx, cy, cz, tx, ty, tz] of shots) {
  await page.evaluate(([n, a, b, c, d, e, f]) => window.__shot(a, b, c, d, e, f), [name, cx, cy, cz, tx, ty, tz]);
  await page.waitForTimeout(2600);
  await page.screenshot({path: `${outDir}/${tag}-${name}.png`});
  console.log('shot:', tag + '-' + name);
}
await browser.close();
