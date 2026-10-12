---
name: landmark-reconstruction
description: 用公开地图、地形、建筑资料和参考照片，逐个重建鹭岛纪（厦门）的重点山体、建筑和街区；导出可交给不同 Agent 的独立任务包，验证证据、坐标、轮廓、模型和实机结果。
---

# 重点对象实景建模（厦门）

适用于《鹭岛纪》当前浏览器城市。用户指定重点对象时使用；不把整个厦门扩展为精细建模范围。首次应用本 Skill 时告知用户正在使用它。完整任务契约、证据格式与状态检查见 [agent-workflow.md](../docs/landmarks/agent-workflow.md)。

## 先辨认对象，再决定建模范围

读取 `data/landmarks/priority-places.json`、目标 `data/landmarks/<id>.json`（若有）、现有 `scripts/landmarks/<id>.py` 和当前 `public/city/city.json` 的 `meta`。保留清单中的地点歧义与 blocker。M1 时期的地标坐标全部是游戏设计估算（标记为 estimated），**不得当作实测值**——2026-10-12 的 shimao 样板证明 M1 估算坐标可能偏离 2.2km。

建筑先确认地块、楼栋数、足印、塔楼高度与高低关系、朝向、退台和连桥。山体先确认山脚覆盖、山脊走向、地形剖面和相对高差。街区先拆分可辨识的楼群、广场、道路和开放空间。鼓浪屿为步行岛（车行道限主岛，见 prepare_driving_city.py），历史街区高度不得用全市估算冒充。

## 获取证据（厦门本地通道）

1. 优先查本地 OSM PBF：`data/raw/fujian-latest.osm.pbf`（OSM-FR 镜像 2026-10-08，ODbL）。用 pyosmium `apply_file(..., locations=True)` 按 way/名字/bbox 查询；注意 M1 坐标若错则查询框会被带偏——先交叉核对 Wikidata/维基坐标。保留 way id 与标签差异（如 shimao B塔 OSM 标 261 vs 报告 300，记录不消解）。
2. 地形调用 `scripts/prepare_landmark_terrain.py`（仙岳山样板已适配）；Copernicus DSM 30m 不用于单体建筑尺寸主张。
3. 公开权威页交叉：官网/设计院（ceedi 等）/百科结构化数值；Wikidata/CTBUH 坐标（WGS84）互洽性检查。
4. Wikimedia Commons 照片（CC BY-SA）仅作形态参考，不打包为贴图；Esri World Imagery 瓦片可用于方位/间距交叉（时相未标定，不作尺寸依据）。
5. 每条判断写入任务包 `evidence.json`，区分 `reported/measured/estimated`；高德/百度为 GCJ-02，只作核对不直接混入 WGS84。

## 导出并分派任务

```powershell
$env:PYTHONUTF8='1'; & .venv\Scripts\python.exe scripts\landmark_tasks.py generate
$env:PYTHONUTF8='1'; & .venv\Scripts\python.exe scripts\landmark_tasks.py status --job artifacts/landmark-jobs/<id>/job.json
```

生成 `artifacts/landmark-jobs/<id>/`（job/prompt/evidence/model/validation 五件套）。一次只给一个对象的文件所有权；同一对象的证据整理与建模按顺序执行，不同对象可并行。主集成人员拥有 `src/city-world.ts`、`scripts/build_landmark_details.py`、总 GLB 与公共资产；执行者只提交 `scripts/landmarks/<id>.py`、`data/landmarks/<id>.json` 与任务目录。

## 保持坐标和尺度一致

原点 `[118.12, 24.485]`（`src/city-map-geometry.ts` 唯一权威）：

```text
east  = (lon - 118.12) * 101310 * 0.60
north = (lat - 24.485) * 111320 * 0.60
up    = relative_height_metres * 0.60
```

Blender east/north/up；glTF 导出器负责 Y-up；网页加载器已有方向处理。高度区分海拔/建筑相对高度/游戏高度；不得在 0.60 倍地面上放未缩放塔高。

## 构建与验收

先过证据门槛，再用 `scripts/city_mesh.py` 的 B API（`face/box/tube/loft/footprint(scale)`）制作有来源的主体结构。样板模块：`scripts/landmarks/shimao.py`（帆形双塔：锥形堆叠收分+楼层箍带+竖梃+冠顶钢构+航标+裙房）。集成链（构建→排除重建→验收）的完整命令见 [agent-workflow.md](../docs/landmarks/agent-workflow.md)——含"manifest 先写 baseBuildingIds、facades 后重建"的顺序约束与 PowerShell 管道陷阱。

验收顺序：尺度和轮廓（正交侧视网格测量）→ 近景结构 → 周边衔接 → 碰撞（`tests/landmark-detail.test.ts` live-merge）→ 实机加载（Playwright 截图：俯视/天际线/街面至少各一张）→ 性能（预算与启动/帧率回归）。帆形/斜切冠只在沿脊线方向可读；收分用 GLB 顶点跨度数值复核。自动检查不替代图片形体判断。

交付时说明完成对象、可核对产物、已核实部分、仍属估计的尺寸与未通过项。只有实际测试结果支持时才报告性能达标。

## 材质与预算

材质复用 `city_mesh.py` 的 `M` 表（landmarkglass/darkglass/steel/silver/stone/concrete/roof/redled…），新增走 `material()`。预算：单栋/紧凑建筑组 25k 三角/12 材质/8MiB GLB/2048 贴图边长；山体/片区首轮 60k/12MiB。同屏新增 ≤150k 三角、≤60 draw call。shimao 样板实际用量 3,176 三角（预算 12.7%）。照片与品牌素材不能未授权打包；文字招牌走 SVG/小 PNG 手工重现，遵循上游 signage 经验（exactText 核对、illuminationVerified 默认 false）。
