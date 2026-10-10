/**
 * Re-siting evidence for the bamboo-cafe (月白 · 女仆咖啡馆) Xiamen plot.
 *
 * Mirrors the checks in tests/city-cafe.test.ts:
 *  - the rotated footprint envelope (local x ∈ [-10,10], z ∈ [-12,8]) must be
 *    free of city collision (no building / water / landmark) AND must not cover
 *    road surface (distance to nearest road > road.width/2 at every sample);
 *  - the 14 m door approach (walk from local (0,-21) forward along heading) must
 *    reach the interior via CityWalk, using city collision OR cafe layout block.
 *
 * Also verifies the cafe frontage faces the road in front of it (the door's
 * outward direction reaches a road whose tangent ≈ roadYaw within 12°).
 *
 * Run: node --experimental-transform-types scripts/check-cafe-site.mts
 */
import {readFileSync} from 'node:fs';
import {CityCollision,type V2} from '../src/driving.ts';
import {CityWalk} from '../src/city-walk.ts';
import {cafeLayout,type CafeSpec} from '../src/city-cafe-layout.ts';

const city = JSON.parse(readFileSync(new URL('../public/city/city.json', import.meta.url), 'utf8'));
const dataSpec = JSON.parse(readFileSync(new URL('../data/locations/bamboo-cafe.json', import.meta.url), 'utf8')) as CafeSpec;
const manifest = JSON.parse(readFileSync(new URL('../public/city/bamboo-cafe/manifest.json', import.meta.url), 'utf8'));
const collision = new CityCollision(city);

type Result = {
  x: number; z: number; heading: number; roadYaw: number;
  blockedSamples: number; roadOverlaps: number; entered: boolean;
  arrivalOnRoad: boolean; frontRoadYaw: number | null; frontRoadDist: number | null;
  frontRoadName: string | null; aligned: boolean;
};

function checkSite(x: number, z: number, heading: number, roadYaw: number): Result {
  const spec: CafeSpec = {...dataSpec, site: {x, z, heading, arrival: [x, z], roadYaw}};
  const layout = cafeLayout(spec, manifest.colliders, 0);

  let blockedSamples = 0, roadOverlaps = 0;
  for (let lx = -10; lx <= 10; lx++) for (let lz = -12; lz <= 8; lz++) {
    const p = layout.world(lx, lz);
    if (collision.blocked(p.x, p.z)) blockedSamples++;
    const road = collision.nearest(p.x, p.z);
    if (road && road.d <= road.road.width / 2) roadOverlaps++;
  }

  const walk = new CityWalk(
    (x, z) => collision.blocked(x, z) || layout.blocked(x, z),
    (x, z) => layout.floorAt(x, z, 0),
  );
  const start = layout.world(0, -21);
  Object.assign(walk, {active: true, x: start.x, z: start.z, yaw: heading});
  const forward = new Set(['KeyW']);
  const steps = Math.ceil(14.5 / (1.6 * .05));
  let entered = false;
  for (let i = 0; i < steps; i++) { walk.step(forward, .05); if (layout.inside(walk.x, walk.z)) { entered = true; break; } }

  const c = Math.cos(heading), s = Math.sin(heading);
  const door = layout.world(0, -7.8);
  let frontRoadYaw: number | null = null, frontRoadDist: number | null = null, frontRoadName: string | null = null;
  for (let d = 0.5; d <= 40; d += 0.25) {
    const px = door.x - s * d, pz = door.z - c * d;
    const n = collision.nearest(px, pz);
    if (n && n.d <= n.road.width / 2) { frontRoadYaw = n.yaw; frontRoadDist = d; frontRoadName = n.road.name ?? n.road.id; break; }
  }
  const aligned = frontRoadYaw !== null && Math.abs(Math.atan2(Math.sin(frontRoadYaw - roadYaw), Math.cos(frontRoadYaw - roadYaw))) < 0.22;

  const rc = Math.cos(roadYaw), rs = Math.sin(roadYaw);
  const arrival: V2 = [x - 17 * rc, z + 17 * rs];
  const aRoad = collision.nearest(arrival[0], arrival[1]);

  return {
    x, z, heading, roadYaw, blockedSamples, roadOverlaps, entered,
    arrivalOnRoad: !!aRoad && aRoad.d <= aRoad.road.width / 2 - .65,
    frontRoadYaw, frontRoadDist, frontRoadName, aligned,
  };
}

function searchNear(name: string, arrival: V2, radius = 160): Result[] {
  const found: Result[] = [];
  const seen = new Set<string>();
  const cell = (v: number) => Math.floor(v / collision.size);
  for (let cx = cell(arrival[0] - radius) - 1; cx <= cell(arrival[0] + radius) + 1; cx++)
  for (let cz = cell(arrival[1] - radius) - 1; cz <= cell(arrival[1] + radius) + 1; cz++) {
    for (const seg of collision.cells.get(cx + ',' + cz) ?? []) {
      const [a, b] = [seg.a, seg.b];
      const len = Math.hypot(b[0] - a[0], b[1] - a[1]);
      const n = Math.max(1, Math.floor(len / 4));
      for (let i = 0; i <= n; i++) {
        const t = i / n;
        const px = a[0] + (b[0] - a[0]) * t;
        const pz = a[1] + (b[1] - a[1]) * t;
        if (Math.hypot(px - arrival[0], pz - arrival[1]) > radius) continue;
        const yaw = Math.atan2(b[0] - a[0], b[1] - a[1]);
        const pc = Math.cos(yaw), ps = Math.sin(yaw);
        for (const [dh, perp] of [[yaw + Math.PI / 2, [pc, -ps]], [yaw - Math.PI / 2, [-pc, ps]]] as [number, V2][]) {
          for (const D of [15, 17, 19, 21, 23]) {
            const sx = px + D * perp[0];
            const sz = pz + D * perp[1];
            const key = `${Math.round(sx)},${Math.round(sz)},${dh.toFixed(3)}`;
            if (seen.has(key)) continue;
            seen.add(key);
            const r = checkSite(sx, sz, dh, yaw);
            if (r.blockedSamples === 0 && r.roadOverlaps === 0 && r.entered && r.arrivalOnRoad) found.push(r);
          }
        }
      }
    }
  }
  return found;
}

const targets: [string, V2][] = [
  ['shapowei', [-2098.93, -3297.79]],
  ['xmu', [-1838.57, -3227.68]],
  ['huizhan', [2647.71, -1888.94]],
  ['wuyuan', [2003.84, 3205.28]],
];

for (const [name, arrival] of targets) {
  const results = searchNear(name, arrival);
  const aligned = results.filter(r => r.aligned);
  console.log(`\n=== ${name} -> ${results.length} clear, ${aligned.length} door-aligned ===`);
  aligned.sort((p, q) => Math.hypot(p.x - arrival[0], p.z - arrival[1]) - Math.hypot(q.x - arrival[0], q.z - arrival[1]));
  for (const r of aligned.slice(0, 10)) {
    console.log(`  site=(${r.x.toFixed(1)}, ${r.z.toFixed(1)}) heading=${r.heading.toFixed(4)} roadYaw=${r.roadYaw.toFixed(4)} dist=${Math.hypot(r.x - arrival[0], r.z - arrival[1]).toFixed(0)}m front=${r.frontRoadName} frontD=${r.frontRoadDist?.toFixed(1)} frontYaw=${r.frontRoadYaw?.toFixed(3)}`);
  }
  if (!aligned.length && results.length) {
    results.sort((p, q) => Math.hypot(p.x - arrival[0], p.z - arrival[1]) - Math.hypot(q.x - arrival[0], q.z - arrival[1]));
    console.log('  (no door-aligned; nearest clear:)');
    for (const r of results.slice(0, 5)) console.log(`  site=(${r.x.toFixed(1)}, ${r.z.toFixed(1)}) heading=${r.heading.toFixed(4)} roadYaw=${r.roadYaw.toFixed(4)} front=${r.frontRoadName} frontYaw=${r.frontRoadYaw?.toFixed(3)}`);
  }
}

// ----- Chosen site (沙坡尾 shapowei, art district beside the fishing harbour) -----
// Written to data/locations/bamboo-cafe.json and public/city/bamboo-cafe/manifest.json.
const CHOSEN = {x: -2051, z: -3282.3, heading: 1.1095, roadYaw: -0.4613};
const verdict = checkSite(CHOSEN.x, CHOSEN.z, CHOSEN.heading, CHOSEN.roadYaw);
const pass = verdict.blockedSamples === 0 && verdict.roadOverlaps === 0 && verdict.entered && verdict.arrivalOnRoad && verdict.aligned;
console.log(`\n=== CHOSEN SITE ${pass ? 'PASS' : 'FAIL'} ===`);
console.log(`  site=(${CHOSEN.x}, ${CHOSEN.z}) heading=${CHOSEN.heading} roadYaw=${CHOSEN.roadYaw}`);
console.log(`  blockedSamples=${verdict.blockedSamples} roadOverlaps=${verdict.roadOverlaps} entered=${verdict.entered}`);
console.log(`  arrivalOnRoad=${verdict.arrivalOnRoad} frontRoad=${verdict.frontRoadName} frontDist=${verdict.frontRoadDist?.toFixed(1)}m doorAligned=${verdict.aligned}`);
if (!pass) process.exitCode = 1;