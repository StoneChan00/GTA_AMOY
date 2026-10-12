# 地标精修工作契约（厦门 · GTA_AMOY）

本流程把可重复的资料整理和建模拆成逐对象任务。当前工具是 `scripts/landmark_tasks.py`；它输出 JSON 任务包、提示词与状态检查，不自动控制任何外部 Agent。

上游原型：GTA_SZ `docs/landmarks/agent-workflow.md`（深城纪），本文为厦门版契约，状态机与证据纪律不变。

## 可执行入口

```powershell
$env:PYTHONUTF8='1'; & .venv\Scripts\python.exe scripts\landmark_tasks.py generate
$env:PYTHONUTF8='1'; & .venv\Scripts\python.exe scripts\landmark_tasks.py generate --place shimao
$env:PYTHONUTF8='1'; & .venv\Scripts\python.exe scripts\landmark_tasks.py status --job artifacts/landmark-jobs/shimao/job.json
$env:PYTHONUTF8='1'; & .venv\Scripts\python.exe scripts\landmark_tasks.py check --job artifacts/landmark-jobs/shimao/job.json --stage evidence-ready --record
```

清单：`data/landmarks/priority-places.json`（sources + places）。任务包固定五件套：`job.json`（源记录快照+派工+坐标策略+预算+文件所有权）、`prompt.md`（可复制给执行者的中文任务）、`evidence.json`（证据整理者填写）、`model.json`（实存 GLB/源码 SHA256+实际构建命令）、`validation.json`（八项具名验收）。二次生成保留已有任务；新一轮用 `--output artifacts/landmark-jobs-round2`。

## 状态定义（只读检查，重新计算 currentStage）

| 状态 | 实际检查 | 不能据此声称 |
| --- | --- | --- |
| `planned` | 已有独立任务 | 已获取完整资料或已有真实模型 |
| `evidence-ready` | 身份与 WGS84 中心确认；必需形体观察有来源与不确定度；blocker 清空 | 所有尺寸实测、图片已授权作贴图 |
| `modelled` | 前序通过；GLB 有效；模型与源码 SHA256 匹配；构建命令填写 | 视觉符合现实或实机性能达标 |
| `verified` | 前序通过；八项具名验收有本地证据并绑定当前哈希；预算通过 | 测绘级、所有视角与细节完全复原 |

必需观察类别：建筑/紧凑楼群 `footprint/height/orientation/silhouette`；山体 `extent/elevation_profile/silhouette`；片区 `extent/layout/silhouette`。`basis` 只接受 `reported/measured/estimated`；照片推算须记录视角与误差。证据源优先级：本地 OSM PBF（`data/raw/fujian-latest.osm.pbf`，pyosmium 带 `locations=True` 查询）→ 公开权威页（官网/设计院/百科交叉）→ Wikidata/CTBUH 结构化坐标 → Commons 照片（仅参考）→ 卫星影像（Esri World Imagery，时相未标定时不作尺寸依据）。GCJ-02/BD-09（高德/百度）只能作核对，转换后方可参考。

## 坐标与尺度（厦门）

```text
east  = (lon - 118.12) * 101310 * 0.60
north = (lat - 24.485) * 111320 * 0.60
up    = real_height_metres * 0.60
```

原点 `[118.12, 24.485]`（见 `src/city-map-geometry.ts`，唯一权威）。Blender east/north/up；glTF 导出 Y-up；运行时保留根 Z 反射。真实米制参数进证据，游戏内只缩放一次。

## 建模边界

- 对象模块 `scripts/landmarks/<id>.py`：无 bpy 依赖、无导出副作用，`build(b, spec, ...)` 按调用者传入的投影环与 scale 工作（样板：`scripts/landmarks/shimao.py`）。
- 总构建器 `scripts/build_landmark_details.py`（主集成独占）：初始化 Blender 场景、读 `data/landmarks/<id>.json`、投影、碰撞足印、manifest 与导出。
- `city_mesh.py` 的 B API：`face/box/tube/loft/footprint(scale)`；材质表 `M`（landmarkglass/darkglass/steel/silver/stone/concrete/roof/redled…），`footprint()` 会自动 tessellate 顶面为 roof 材质，且要求环首点重复（闭环）。
- 预算：单栋/紧凑建筑组 25k 三角/12 材质/8MiB；山体/片区首轮 60k/12MiB。同屏新增 ≤150k 三角、≤60 draw call。

## 集成链（主集成串行；样板已走通，2026-10-12）

```powershell
# 1) 构建对象 GLB + manifest（baseBuildingIds 写入后，facades 重建才会排除旧楼）
$env:PYTHONUTF8='1'; & 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' --background --factory-startup --python scripts\build_landmark_details.py
node scripts\optimize_landmark_details.mjs
# 2) 基础楼体/立面排除重建（读 landmark-detail.json 的 baseBuildingIds）
$env:PYTHONUTF8='1'; & 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' --background --factory-startup --python scripts\build_city_facades.py
node scripts\optimize_city.mjs buildings facades
node scripts\split_city_facades.mjs
# 3) 立面后处理链（colorize→diversity→装回）
node scripts\colorize_architecture.mjs --input public/city/buildings.glb --output artifacts/materials/buildings-tinted.glb --overwrite
node scripts\prepare_facade_diversity.mjs
Copy-Item artifacts\materials\facade-diversity\buildings-varied.glb public\city\buildings.glb
# 4) 验收
npm test
node scripts\check-<id>-detail.mjs   # Playwright 实拍（样板：check-shimao-detail.mjs / check-shimao-hq.mjs）
```

注意：运行时 `loadLandmarkDetails`（`src/landmark-details.ts`）会按 `baseBuildingIds` 过滤 `data.buildings`（碰撞层）、合并 manifest 地标记录（地图/照片标记迁移）、按 `replacedMeshPrefixes` 处置旧 `landmark_*` 网格、推送 `collisionFootprints` 为碰撞多边形。manifest 必须保留 `terrain.url → /city/terrain-detail.json`（仙岳山网格，运行时 heightAt 依赖）。

## 实拍验证要点（经验教训）

- 机位三角学：`enterPhoto` 相机 = focus − (sin(−photoAngle), cos(−photoAngle))·cos(elev)·d；photoAngle 符号决定相机方位，先算清再拍（样板曾把侧视拍成端视）。
- 帆形斜切冠只在沿脊线方向（端视）可读，侧视必然 edge-on；收分验证用正交侧视+网格裁剪放大（±0.2 格精度），必要时以 GLB 顶点跨度数值复核（量化 GLB 需乘节点矩阵）。
- `?quality=high` 与 day 模式（`setLightMode('day')`）下复核细节；headless Edge 可用（`chromium.launch({channel:'msedge',headless:true})`）。
- PowerShell 管道 `Select-Object -First N` 会提前终止原生命令——长构建一律 `Out-File` 落盘再查尾。

## 当前交付状态

- **shimao（世茂海峡大厦·双子塔）：verified（2026-10-12）**。OSM 测绘足印（A/B塔+裙房）+ reported 高度（300m 冠顶/249.9 屋面/裙房 32.5）+ 照片估计收分与冠顶；3,176 三角；M1 错位标记（2.2km）已迁移到沙坡尾实测场地；旧 202k 三角无出处模型已被替换。
- 其余 9 地标：`planned`（清单已建，证据待整理）。
- 管线债：M1 错位 radius-42 在厦港老城误除的普通楼，需下次 `prepare_driving_city` 全量重跑时回归。
