# GTA_AMOY · LuDaoJi (鹭岛纪)

**English** · [简体中文](README.zh-CN.md)

Drive, walk, and fly through a playable island of Xiamen, China — built in the browser from OpenStreetMap data, a Blender asset pipeline, and Babylon.js real-time rendering.

This project is derived from **[GTA_SZ · ShenChengJi](https://github.com/linranff/GTA_SZ)** (deep thanks to [linranff](https://github.com/linranff) for the complete city-generation pipeline, rendering architecture, and engineering practice). In this repository the city data and content have been replaced with Xiamen Island (Convention & Exhibition Center, Xiamen University, Bailu Zhou, Island Ring Road, Wuyuan Bay, …), and the city-life layers — signal lights, tree canopy, e-bikes, facades, rooftops — have been localized for the Xiamen setting.

**Play** (desktop browser with WebGL2):

- <https://stonechan00.github.io/GTA_AMOY/> — primary entry
- <http://39.96.117.179/GTA_AMOY/> — China-friendly mirror (self-hosted, limited bandwidth; a full load takes a few minutes)

## Quick start

Requires Node.js (24 recommended), npm, Git LFS, and a WebGL2 desktop browser.

```sh
git lfs install
git clone https://github.com/StoneChan00/GTA_AMOY.git
cd GTA_AMOY
git lfs pull
npm ci
npm run dev
```

Open the URL Vite prints (usually `http://127.0.0.1:5173/`).

```sh
npm test          # run tests
npm run build     # production build
npm run preview   # preview the build locally
```

### Updating the online versions

```sh
npm run deploy:ecs     # Alibaba Cloud ECS mirror
npm run deploy:pages   # GitHub Pages
```

Both commands build with the sub-path derived from the `origin` remote and rewrite root-absolute asset paths inside the bundle (failing loudly on any leftover instead of shipping 404s). The ECS serves multiple projects from one Nginx root (`/var/www/<repo>/`), mirroring the GitHub Pages project-site convention; the Pages release pushes the `gh-pages` branch as plain files (never Git LFS pointers). Override the sub-path via `DEPLOY_PAGES_BASE=/` for a custom domain.

## Controls at a glance

| Mode / input | Action |
| --- | --- |
| Car: WASD / arrows, Space | Drive, handbrake |
| F / T | Enter/exit a vehicle; switch car / tank while driving |
| Walking: WASD, Shift, C | Walk, run, first/third person |
| G / B | Drone observation; switch drone / aircraft |
| M / L / J | Map, lighting preset, city journal |
| P | Frame-rate info |

## City data

- Roads and building footprints from OpenStreetMap (© OpenStreetMap contributors, ODbL)
- Terrain elevation from Copernicus DEM
- The city is an artistic, compressed interpretation (building heights, facades, and terrain are stylized) — not a survey-grade digital twin
- Full data provenance and attribution: [data/ATTRIBUTION.md](data/ATTRIBUTION.md)

## License

Code is released under the MIT license, see [LICENSE](LICENSE) (it preserves the upstream copyright notice).

**The license covers code only.** Models, textures, and HDR environments under `public/`, and geographic data under `data/`, keep their own original licenses and attribution requirements — see [public/licenses/](public/licenses/) and [data/ATTRIBUTION.md](data/ATTRIBUTION.md). Character models are provided by miHoYo with MMD adaptation by Guanhai (观海); the original terms prohibit commercial use and redistribution. This is a non-commercial prototype, not affiliated with or endorsed by miHoYo / HoYoverse.
