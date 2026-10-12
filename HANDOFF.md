HANDOFF CONTEXT
===============

USER REQUESTS (AS-IS)
---------------------
- "帮我分析下当前项目的依赖以及是如何实现的以及资源的来源是什么；然后分析下如果想复刻一下厦门的容易实现吗"
- "帮我新起一个GTA_AMOY来实现厦门的复刻：先总结方案后直接开始实施"
- "先做首次commit后验证一下，现在好像后轮有点问题，并且车没有碰撞体积，其他车遇到了后也不会避让会穿过去"
- "继续M2"
- "记录handooff交接，并且记录worklog，然后我现在进入网页后title还是深城纪"
- "帮我推到 GitHub（StoneChan00/GTA_AMOY），加上 MIT LICENSE 和 GTA_SZ 原始链接"
- "部署到阿里云 ECS，路径统一成 /GTA_AMOY/ 子路径（多项目规范）"
- "看下 issue：用户通过 GitHub Pages 访问遇到问题，是否已修复"

GOAL
----
继续 GTA_AMOY（鹭岛纪，厦门岛浏览器城市，fork 自 GTA_SZ）的 M3 阶段：山体地形接入、对岸天际线、地标精修内容生产。

WORK COMPLETED
--------------
- 我完成了完整的项目分析（GTA_SZ 依赖/架构/数据来源/厦门复刻可行性）
- 我创建了 D:\2_Projects\github\GTA_AMOY 并完成 M1：福建 PBF（经 OSM-FR 镜像下载，Geofabrik 被墙）→ xiamen_study 提取 → 岛屿自动选择算法 → city.json（5,023 道路/4,069 建筑/10 厦门地标）→ 13 个 GLB（meshopt 压缩）→ 浏览器可玩
- 我修复了三个 M1 bug：car.glb 被 build_city_detail_assets 覆盖导致车轮枢轴错误（链条末尾重新部署 indigo-gt.glb）；会展中心/厦大/高崎等 M1 无模型地标的 excludeRadius 把真实建筑整栋排除导致无碰撞（归零，仅 shimao 保留 70）；NPC 不避让玩家（traffic.ts 增加玩家 actor 前向避让，11m+弯道后向容差-3m）
- 我完成了 M2：信号灯（213 路口）、林冠（45,088 树/6 树种/3 街道档）、电动车（2,584 辆，修了 102850→101310 系数与 shenzhen_study→xiamen_study 路径）、立面链（build_city_facades→optimize→split 126 瓦片→colorize→diversity 8 家族 UV2→atlas）、屋顶（14 原型/23,961 布点）、剧情文案厦门化（会展/五缘湾/白鹭洲/环岛路）、车牌与座舱"鹭岛纪"
- 我完成了 M2 收尾：landmark-detail/terrain-detail/landmark-candidates 最小有效 manifest + Blender 占位 GLB（scripts/build_placeholder_landmark_glbs.py，注意 gltf-transform 单行写法会产出坏 GLB，必须用 Blender）；屋顶测试阈值厦门化（路口≥150、车辆≥1500、屋顶总数 15000-60000、helipads≥1、lookup>1500×1500）
- 我修复了页面标题：index.html/trailer.html/combat-lab.html 的 title/description/wordmark/aria-label 全部"深城纪"→"鹭岛纪"，Playwright 验证 TITLE: 鹭岛纪 · 一路向海
- 我完成了公开发布（2026-10-10）：GitHub 仓库 StoneChan00/GTA_AMOY（MIT LICENSE 双版权行 linranff+StoneChan00；README 英文主版 + README.zh-CN.md）+ GitHub Pages + 阿里云 ECS 镜像，三入口均验证可用
- 我修复了 issue #1（外部用户反馈）：加载屏粘土动画 bamboo-clay-loop.mp4 在 M1 迁移时损坏为 0 字节（poster.jpg 静态图兜底所以一直没被发现）导致 416 Range 错误，从 GTA_SZ 源仓库取回 6.77MB 真视频并重部署（62c90ed），已在 issue 用英文回复闭环
- 我修复了 ECS（纯 HTTP）启动崩溃：crypto.subtle 在非安全上下文为 undefined，landscape 资格门禁的 SHA-256 调用炸掉 boot 链；新增 src/sha256.ts 纯 JS 回退（优先 crypto.subtle，HTTP 下回退同步实现，校验语义一致）（ea9cd1b，含 4 个 FIPS 标准向量测试）

CURRENT STATE
-------------
- 14 个 commit（6def972 M1 → 7b8a1de 地标精修管线+双子塔样板），工作树干净；origin=StoneChan00/GTA_AMOY（master + gh-pages 分支）
- 2026-10-12 双提交：1e47291 鼓浪屿入岛（面积阈值误滤修复+全管线重跑+链末段补齐：car.glb LFS 恢复/facade diversity 重跑/coastal-horizon 重编号 54582/3426/6852）；7b8a1de M3 地标精修管线+世茂双子塔样板 verified（详见 docs/landmarks/agent-workflow.md）
- npm test：290/290 全通过（M3 主体完成后无已知失败）
- 浏览器验证：12-14s 启动；鼓浪屿独立岛屿（红屋顶建筑群+绿地+0 车行道）；世茂双塔新模型（收分比实测 0.67-0.75）
- dev server 已重启（PID 会变，遇到 "Unexpected magic: 1868833084" 先重启）
- 环境：Windows + Blender 5.2.2（winget，路径 C:\Program Files\Blender Foundation\Blender 5.2\blender.exe）+ .venv（Python 3.12，osmium(shapely/pyproj/rasterio/numpy/PIL 已装，scipy 未装）+ npm ci 完成

RELEASE & DEPLOYMENT
--------------------
- 三入口（均验证可用）：源码 https://github.com/StoneChan00/GTA_AMOY · Pages https://stonechan00.github.io/GTA_AMOY/ · 国内镜像 http://39.96.117.179/GTA_AMOY/（根路径 302 跳转）
- 一键部署：npm run deploy:pages（推 gh-pages 分支，普通 blob 非 LFS 指针）；npm run deploy:ecs（scp+解压到 /var/www/<repo>/）。两条命令共享 scripts/rewrite-dist-paths.mjs：源码 57+ 处 JS 与 4 处 JSON manifest 的根绝对路径（'/city/...'、'/characters' 等）Vite 不会重写，必须后处理加 /GTA_AMOY/ 前缀，**残留即构建失败**（新增硬编码路径需先加进重写清单）
- ECS：Ubuntu 24.04（2C/1.6G，磁盘 27G 可用），Nginx 多项目根 /var/www（正则 location 适配任意 /<repo>/ 子目录），gzip+缓存+Range 已配；SSH 免密 root@39.96.117.179（ssh config 别名 ali-cloud-ecs 带括号，**scp 用它会传参失败，一律 IP 直连**）；安全组 80 已放行；带宽 3Mbps 固定（完整加载 5-6 分钟，与 MC 服 frp 共享，详见 worklog）
- **M3 编码注意**：ECS 是纯 HTTP（无域名无法签证书），crypto.subtle/clipboard/ServiceWorker 等安全上下文 API 不可用——新代码要么不用，要么按 src/sha256.ts 的模式做回退（city-observer-beacons.ts 的 globalThis.crypto?.randomUUID?.() ?? fallback 是范本）

PENDING TASKS
------------
- 地标精修内容生产（M3 主线，管线+样板已就绪）：9/10 地标 planned 待证据整理（priority-places.json 已建）；契约入口 docs/landmarks/agent-workflow.md + skills/landmark-reconstruction/SKILL.md（厦门化）；样板 scripts/landmarks/shimao.py；鼓浪屿建筑高度 heritage 上限（全市估算中位 23.4m vs 真实 2-4 层）
- 管线债：M1 错位 radius-42 在厦港老城误除的普通楼，下次 prepare_driving_city 全量重跑时回归；shimao 冠部斜撑一塔仍略外张、帆面弧线远距微妙（记录于 validation.json）
- 双端部署：1e47291+7b8a1de 未推送（npm run deploy:pages / deploy:ecs）
- 海面观感调参（1-2 天）：暮色/夜间黑色空洞、白昼波浪细节衰减（机制已在，纯调参）
- 岛外扩展三档（可选）：远景剪影已完成；半实景天际线 1-2 天；可驾驶大陆 2-4 周
- make_facade_relief_atlas.py 需 scipy（当前用 LFS 预生成 PNG，管线不完全可复现）
- EXPLICIT CONSTRAINTS 引用的 AGENTS.md 属上游 GTA_SZ（本仓库无）

KEY FILES
---------
- src/city-map-geometry.ts - 厦门坐标系唯一权威（origin [118.12,24.485]，经度系数 101310，纬度 111320，缩放 0.60）
- scripts/prepare_driving_city.py - city.json 生成器（岛屿选择含鼓浪屿显式并入+车行道限主岛 main_land；10 地标/spawn 自动定向/主干道最小宽度 10.5m）
- scripts/landmark_tasks.py + data/landmarks/priority-places.json - 地标精修任务包生成器与清单（厦门坐标策略）
- scripts/build_landmark_details.py + scripts/landmarks/shimao.py + data/landmarks/shimao.json - 地标总构建器与双子塔样板（evidence→model→verified 全链路）
- docs/landmarks/agent-workflow.md - 地标精修契约（集成链命令/机位三角学/管道陷阱/交付状态）
- scripts/build_city_facades.py - 基础楼体+立面重建（读 landmark-detail.json 的 baseBuildingIds 排除旧楼；两导出缺一不可）
- scripts/traffic.ts 旁边的 src/traffic.ts - NPC 避让（ahead(px,pz,true) 玩家检查）
- src/landmark-details.ts - landmark manifest schema 与加载契约（运行时合并地标/过滤旧楼/处置旧网格/碰撞足印）
- scripts/build_placeholder_landmark_glbs.py - Blender 占位 GLB 生成器（勿用 gltf-transform 替代）
- output/amoy/ - Playwright 截图证据（gulangyu-fix/、shimao-detail/、sea-check/）
- config/regions.json - xiamen_study [117.95,24.35,118.30,24.65] / xiamen_island bbox
- scripts/deploy-pages.mjs + scripts/deploy-ecs.mjs + scripts/rewrite-dist-paths.mjs - 双入口一键部署与子路径重写（见 RELEASE & DEPLOYMENT）
- src/sha256.ts - SHA-256 纯 JS 回退（安全上下文优先 crypto.subtle，HTTP 部署依赖它）

IMPORTANT DECISIONS
-------------------
- 最小改动面策略：内部标识符保留（localStorage 'shenchengji-*'、glTF 扩展名 SHENCHENGJI_preserve_scene_lights、window.__SHENCHENGJI_CITY__），只改用户可见文案与数据，保持与上游 GTA_SZ 的 diff 最小
- 岛屿选择算法：polygonize(bbox 边界+海岸线) 后保留不与 bbox 相交的多边形（厦门岛+鼓浪屿），锚点 [118.128,24.490] 兜底（若海岸线拓扑把岛连上大陆则裁剪回 box(118.055,24.415,118.195,24.565)）
- 数据源镜像：Geofabrik 被 TLS 重置阻断，改用 download.openstreetmap.fr/extracts/asia/china/fujian-latest.osm.pbf；LFS 二进制经 media.githubusercontent.com/media/linranff/GTA_SZ/main/<path> 直拉（本 checkout 的 git 索引状态异常，git lfs pull 无效）
- Python 脚本全部用 PYTHONUTF8=1 运行（Windows GBK 会炸中文 JSON）；blender 调用 --background --factory-startup --python
- 测试阈值厦门化而非跳过：深圳规模断言（路口 300/车辆 15000/屋顶 50000）按厦门实际值（213/2584/23961）保守下调，保持测试语义
- traffic-car.glb 保持上游 stage-5 约定（简单车），car.glb 链条末尾必须是 indigo-gt.glb（CarConcept GT）

EXPLICIT CONSTRAINTS
--------------------
- "不能把照片估计或 OSM 标签自动当作实测值"（AGENTS.md，厦门地标坐标当前全部标注 estimated，待 landmark-reconstruction 证据工作流修正）
- "不同 Agent 只能并行改独立对象模块；共享渲染源码、数据和总资产由一个集成人员串行修改"（AGENTS.md）
- "不得只凭构建成功宣称外观或性能通过；具名视觉复核和性能结果须来自当前资产"（AGENTS.md）

CONTEXT FOR CONTINUATION
------------------------
- 所有构建命令样例：$env:PYTHONUTF8='1'; & .venv\Scripts\python.exe scripts\<x>.py；& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background --factory-startup --python scripts\<x>.py；node scripts\optimize_city.mjs <names>
- M2 完整构建顺序（依赖驱动）：prepare_driving_city → node_city_roads → prepare_city_ground → build_driving_assets[Blender] → copy car→traffic-car → prepare_city_streets → build_city_ground[B] → build_city_detail_assets[B] → prepare_coastal_infrastructure → build_coastal_infrastructure[B] → optimize_city buildings roads terrain → copy indigo-gt→car.glb → prepare_city_ambient → (M2) signals/canopy/ebikes --prepare+[B] → rooftops → facades→split→colorize→diversity→atlas→relief
- 失败测试速查：mountains×2=需地形；coastal-horizon=需 far-shore；autopilot×3=深圳现场断言；cafe×3+corridor+baypark+character-gaits=深圳内容；roadside-planting=banyan-lod 包络
- 遇到 "Unexpected magic: 1868833084" = Vite 返回了 index.html（文件不存在或 dev server 太老）→ 先 curl 确认、必要时重启 dev server
- GTA_SZ（D:\2_Projects\github\GTA_SZ）是参照仓库，其 git 工作树处于异常状态（大量文件标记删除但实际存在，git lfs pull 静默失败），LFS 取物一律走 GitHub media URL
- 今日排障/部署三篇 worklog（~/worklogs，检索关键词：ECS 部署 / 子路径化 / crypto.subtle）：「GTA_AMOY 部署阿里云 ECS 全程」「ECS 部署子路径化 /GTA_AMOY/」「纯 HTTP 部署下 crypto.subtle 缺失」——含 SSH 锁死恢复、PowerShell 传参坑、nginx reload 瞬态 404、安全上下文教训等完整链路
