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
- "看下handoff还有没完成的内容，继续完成"

GOAL
----
维护 GTA_AMOY（鹭岛纪，厦门岛浏览器城市，fork 自 GTA_SZ）并推进 M3 后迭代：M3 已收官（山体地形/对岸天际线/地标精修管线+双子塔样板/鼓浪屿入岛/地图可见性），当前主线为地标内容生产与观感调优（见 PENDING TASKS）。

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
- 我完成了步行岛地图目的地修复（2026-10-12）：鼓浪屿 166 个 POI 此前被 600m 道路筛只剩 81 个且 arrival 全吸到海峡对岸（日光岩/菽庄花园等核心景点反被丢弃，酒店幸存）——新增 carFreeLandTest（无路 land 多边形判定，city-map-geometry.ts），岛上 POI 绕过道路过滤、arrival 用自身坐标（快速移动直接上岛，与 collision.nearest 岛上返 null 的语义自洽）、节流 place 类（酒店/商铺 93 个全清，景点 73 个保留）；步行岛 arrival 一律不生成驾驶路线（city-map.ts/main.ts 守卫，避免 26km"跨海路线"把自动驾驶开进海里；鼓浪屿地标的 arrival 在演武大桥上属可驾驶，保留路线）；选中标签与玩家同点时全偏移碰撞 → chosen 标签新增 [0,-46] 第五偏移
- 我恢复了 life-hub.glb（career 生活驿站 3D 模型，全端 404 导致该特性静默降级）：从 GTA_SZ 上游经 media.githubusercontent.com 直拉 1.9MB（sha256 b42f1ffb…，glTF magic 校验），本地验证 stats.lifeHubs=3、0 console 错误
- 我清了 scipy 管线债：.venv 安装 scipy 1.18.1 后 make_facade_relief_atlas.py 端到端跑通，再生成的 facade-relief.png/roof-detail.png 与已提交版本逐字节一致（sha 相同，git status 干净）——立面 relief 管线完全可复现，不再依赖 LFS 预生成
- 我完成了海面观感调参（2026-10-13，HANDOFF 待办销账）：三症状三治——夜间开阔海面黑洞（海面被排除在所有路灯/车灯外+平面镜像只有 2-4% 星空 → setMode 分模式响应：夜 env 0.78→3、mirror.level .92→1.4、roughness .13→.16，shader 用已插桩未用的 cityBayClock.y 夜旗做月光蓝水体 tint（.052,.09,.13），夜雾色 (.055,.05,.095)→(.085,.085,.15)；实测海面带亮度 6.8→20.9（3×，B>G>R 月光蓝调））；暮色闷红平板（雾色主导 → 雾色 (.44,.27,.31)→(.58,.37,.38)+水面 env 1→1.35，29.9→45.4 且暖调保持，海天亮带衔接柔化）；白昼波浪细节衰减（bayResolvedStrength 距离下限 .08→.30、衰减区间 80-1100→120-2600m，风坡四波前振幅 ×1.35，镜像扰动 falloff .30@900→.45@1500m → 白昼太阳 glitter 光路带交叉波纹碎片+全水面涟漪可见，夜间月光光路同步增强）；附带浅滩带 2-62→3-85m/混合 .78→.9、泡沫 .11→.15（受 shore-distance 纹理 ~10m/px 分辨率限制，视觉提升有限，见 PENDING）；修复 setMode 从未在启动时调用（新材质停留在创建值直到首次 L 键）；292/292、tsc 干净、三模式多机位量化 A/B（output/amoy/sea-tuning/，含 pngstat 像素统计法）
- 我完成了地标精修第一轮 7/10 对象交付（2026-10-13）：证据→spec（data/landmarks/{riguangyan,bagua,xmu,gaoqi,xiamenzhan,huizhan}.json，全部证据标注 basis=reported/measured/estimated + 分歧记录）→模块（scripts/landmarks/ 同名 .py + _helpers.py 嘉庚屋顶件）→Blender 集成（build_landmark_details.py 全量重写：project_ring 闭合、point_blocked 完整镜像 CityCollision.blocked 语义——建筑环+1.15m 边距+陆地/水域+道路豁免——arrival 不再落进自己模型；extend_landmark_exclusions.py 足印交叠自动扩排 baseBuildingIds（21 个，Blender 外跑 shapely）；city_mesh 新材质 granite/greentile/orangetile/whiteroof + loft 支持逐环 power）。交付对象：日光岩（92.7m 花岗岩山体+双巨石+寺+寨门，模型自带地形）、八卦楼（25.7m/10m 穹顶、仿岩石圆顶八棱红穹）、厦大三楼群（群贤五楼官方面宽/进深+嘉庚颂恩 21 层+建南门楼）、高崎 T3/T4（T4 39m 马鞍屋盖+起翘、跑道 05/23 实测端点）、厦门站（31m 拱顶/206×145m、OSM 节点实测 vs M1 偏 700m）、会展中心（432m/42.6m 主楼证据升级、双排拱壳+前桅、拱壳跨度按 140m 实测收敛）；M1 错位标记全部迁移（会展偏 2.5km/厦大偏 250m/厦门站偏 700m/高崎→T4）；日光岩/八卦楼为鼓浪屿步行岛新记录（arrival 环外逃逸+walk_only）。全链重建：facades→optimize→split(131 tiles)→colorize→diversity→装回；292/292；网格审计 0 旧楼残留；视觉验收：日光岩（像素级灰花岗岩实证）、颂恩楼（蓝塔+绿阶顶+红旗杆可读）、T4/会展屋面形态可读——八卦楼/厦门站/T3/会展全貌具名验收待 heritage 高度上限（见 PENDING，本轮 GPU 疲劳黑屏多次，截图在 output/amoy/landmarks-v1/ 13 张）
- 我完成了岸距纹理分辨率升级（海面残余销项）：prepare_coastal_infrastructure.py 2048×1536→4096×3072（BFS 腐蚀圈 13.7→6.8m/圈，泡沫带从亚像素升到 1-2 texel），PNG 34KB→112KB，其余产物逐字节不变（crossings/parkLights/far-shore 确定性重建验证）

CURRENT STATE
-------------
- 33 个 commit（6def972 M1 → 本轮地标精修+海面+岸距），工作树干净；origin=StoneChan00/GTA_AMOY（master + gh-pages 分支）
- 2026-10-13 第三批提交：地标精修第一轮 7/10（riguangyan/bagua/xmu/gaoqi/xiamenzhan/huizhan + 集成器全量重写 + 自动排除 + 嘉庚屋顶件）+ 岸距纹理 4096；全链 facades 重建、292/292、0 旧楼残留
- 2026-10-13 早前提交：海面观感三模式调参（a48da65，量化验收夜间 3×/暮色 1.5×/白昼 glitter 可见）
- npm test：292/292 全通过；tsc 干净；vite build 正常
- 浏览器验证：日光岩像素级灰花岗岩实证、颂恩塔楼可读、T4/会展屋面形态可读（output/amoy/landmarks-v1/ 13 张 + sea-tuning/ 量化 A/B）；dev server 重启过多次——**长会话 GPU 会疲劳（WebGL CONTEXT_LOST/黑屏/2fps），视觉验证用 headless Edge 全新进程（scripts/check-landmarks-batch.mjs / check-landmarks-closeups.mjs 是范本），每轮新开进程**
- 2026-10-12 第二批提交（继 1e47291/7b8a1de/4a05097/1f28ed8/2c32315 之后）：步行岛地图目的地修复（POI 节流+arrival 上岛+路线抑制+标签避让，292/292 含 2 个新测试）；life-hub.glb 上游取回（career 生活驿站修复）；scipy 入 venv（relief 管线可复现）
- npm test：292/292 全通过；tsc 干净；vite build 正常（dist 含 life-hub.glb）
- 浏览器验证：日光岩可搜可选、快速移动落岛（实测玩家 -3510,-2696 在岛 bbox 内）、岛上无酒店标签、选中标签在玩家同点仍渲染（output/amoy/island-poi-fix/ 4 张截图证据）；海面三模式多机位 A/B（output/amoy/sea-tuning/，基线 vs final 各模式 + pngstat 海面带像素统计）
- dev server 已重启（PID 会变；**运行中新增 public/ 下的 .glb/.bin/.hdr 必须重启 dev server**——vite 启动时一次性索引 public/，新文件会以 index.html 兜底返回 "Unexpected magic: 1868833084"，vite.config.ts 注释有记录）
- 环境：Windows + Blender 5.2.2（winget，路径 C:\Program Files\Blender Foundation\Blender 5.2\blender.exe）+ .venv（Python 3.12，osmium/shapely/pyproj/rasterio/numpy/PIL/scipy 1.18.1 已装）+ npm ci 完成

RELEASE & DEPLOYMENT
--------------------
- 三入口（均验证可用）：源码 https://github.com/StoneChan00/GTA_AMOY · Pages https://stonechan00.github.io/GTA_AMOY/ · 国内镜像 http://39.96.117.179/GTA_AMOY/（根路径 302 跳转）
- 2026-10-12 双批次均已部署双端并验证：M3 双提交（鼓浪屿+双子塔）与 1f28ed8 地图修复（index.html/JS bundle 哈希与本地 dist 逐字节一致）
- 2026-10-13 a48da65 海面调参已部署双端并验证：JS bundle index-DwwCZWqB.js SHA256 与本地 dist 逐字节一致（Pages 推送后 CDN 传播约 1-2 分钟，404 属正常瞬态，等 75s 后哈希即匹配）
- **部署哈希校验坑（Windows）**：nginx 不回 charset，PowerShell Invoke-WebRequest 会把 HTML 按 Latin-1 解码再转 UTF-8 导致哈希假性不一致——校验一律用 -OutFile 原始字节再 Get-FileHash，或直接比对 JS bundle（二进制不受影响）
- GitHub 推送曾间歇性 TLS 阻断（代理 127.0.0.1:7897 出口不稳）——2026-10-12 窗口期已全部推完（master+gh-pages 同步）；再遇到就等窗口重试，ECS 通道（SSH IP 直连）不受影响
- 一键部署：npm run deploy:pages（推 gh-pages 分支，普通 blob 非 LFS 指针）；npm run deploy:ecs（scp+解压到 /var/www/<repo>/）。两条命令共享 scripts/rewrite-dist-paths.mjs：源码 57+ 处 JS 与 4 处 JSON manifest 的根绝对路径（'/city/...'、'/characters' 等）Vite 不会重写，必须后处理加 /GTA_AMOY/ 前缀，**残留即构建失败**（新增硬编码路径需先加进重写清单）
- ECS：Ubuntu 24.04（2C/1.6G，磁盘 27G 可用），Nginx 多项目根 /var/www（正则 location 适配任意 /<repo>/ 子目录），gzip+缓存+Range 已配；SSH 免密 root@39.96.117.179（ssh config 别名 ali-cloud-ecs 带括号，**scp 用它会传参失败，一律 IP 直连**）；安全组 80 已放行；带宽 3Mbps 固定（完整加载 5-6 分钟，与 MC 服 frp 共享，详见 worklog）
- **M3 编码注意**：ECS 是纯 HTTP（无域名无法签证书），crypto.subtle/clipboard/ServiceWorker 等安全上下文 API 不可用——新代码要么不用，要么按 src/sha256.ts 的模式做回退（city-observer-beacons.ts 的 globalThis.crypto?.randomUUID?.() ?? fallback 是范本）

PENDING TASKS
------------
- **历史街区/校园建筑高度上限（本轮实证的头号 follow-up）**：M1 全市高度估算（中位 23.4m）把鼓浪屿与厦大校园的普通楼撑到 14-30+ 游戏米——八卦楼（15m 实测模型）与群贤/嘉庚低层群被通用高楼埋没、日光岩脚树线穿模，可读性受损。需 prepare_driving_city 对 heritage 区（鼓浪屿全域+厦大校园 bbox）加高度上限（真实 2-4 层 ≈ 6-15m）+ radius-42 回归一起做全量重跑（见管线债）
- 地标精修第二轮（本轮已交付 7/10 对象，见 WORK COMPLETED）：剩 白鹭洲/筼筜湖/五缘湾（园区类，需先拆对象：白鹭女神雕塑/筼筜湖喷泉/五缘湾游艇港）与 沙坡尾渔船道具；八卦楼/厦门站/gaoqi-T3/huizhan 的具名视觉验收待历史高度上限落地后补（本轮 GPU 疲劳+背景楼遮挡，几何/材质/碰撞已审计通过）
- 海面残余（可选）：海峡城市灯光倒影为弥散亮带而非结构化灯柱（512px mirror RTT + roughness 物理上限）；海面波浪四波前在 glitter 内呈规则交叉纹（加更多非公度波前可破，上游设计取舍）——岸距纹理已升 4096×3072（≈6.8m/圈）并销项
- 管线债：M1 错位 radius-42 在厦港老城误除的普通楼 + heritage 高度上限（上条）一起在下一次 prepare_driving_city 全量重跑时回归；shimao 冠部斜撑一塔仍略外张、帆面弧线远距微妙（记录于 validation.json）
- 岛外扩展三档（可选）：远景剪影已完成；半实景天际线 1-2 天；可驾驶大陆 2-4 周

KEY FILES
---------
- src/city-map-geometry.ts - 厦门坐标系 wgs84ToMap、MapRoadIndex、mapPointDestination（步行岛 arrival 不跨海峡吸附）、carFreeLandTest（无路 land 多边形=步行岛判定，POI 节流与路线抑制共用）
- src/city-bay-water.ts - 海面材质与 BaySurface shader 插件：setMode 分模式响应（夜 env3/mirror1.4/roughness .16，暮 env1.35，日基线；启动即应用）、GLSL 波浪四波前+距离衰减（下限 .30@2.6km）+浅滩/泡沫（受岸距纹理 10m/px 限制）+夜间月光蓝水体（cityBayClock.y 夜旗）；测试契约：aerial perspective 仅 day、shader 注入点与顶点不变
- scripts/prepare_driving_city.py - city.json 生成器（岛屿选择含鼓浪屿显式并入+车行道限主岛 main_land；10 地标/spawn 自动定向/主干道最小宽度 10.5m）
- scripts/landmark_tasks.py + data/landmarks/priority-places.json - 地标精修任务包生成器与清单（厦门坐标策略）
- scripts/build_landmark_details.py + scripts/landmarks/shimao.py + data/landmarks/shimao.json - 地标总构建器与双子塔样板（evidence→model→verified 全链路）
- docs/landmarks/agent-workflow.md - 地标精修契约（集成链命令/机位三角学/管道陷阱/交付状态）
- scripts/build_city_facades.py - 基础楼体+立面重建（读 landmark-detail.json 的 baseBuildingIds 排除旧楼；两导出缺一不可）
- scripts/traffic.ts 旁边的 src/traffic.ts - NPC 避让（ahead(px,pz,true) 玩家检查）
- src/landmark-details.ts - landmark manifest schema 与加载契约（运行时合并地标/过滤旧楼/处置旧网格/碰撞足印）
- scripts/build_placeholder_landmark_glbs.py - Blender 占位 GLB 生成器（勿用 gltf-transform 替代）
- output/amoy/ - Playwright 截图证据（gulangyu-fix/、shimao-detail/、sea-check/、sea-tuning/ 海面调参前后 A/B 与量化）
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
- "不能把照片估计或 OSM 标签自动当作实测值"（AGENTS.md；厦门地标坐标中 shimao 已经证据工作流修正——M1 曾偏 2.2km，其余 9 个仍为 estimated）
- "不同 Agent 只能并行改独立对象模块；共享渲染源码、数据和总资产由一个集成人员串行修改"（AGENTS.md）
- "不得只凭构建成功宣称外观或性能通过；具名视觉复核和性能结果须来自当前资产"（AGENTS.md）

CONTEXT FOR CONTINUATION
------------------------
- 所有构建命令样例：$env:PYTHONUTF8='1'; & .venv\Scripts\python.exe scripts\<x>.py；& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background --factory-startup --python scripts\<x>.py；node scripts\optimize_city.mjs <names>
- M2 完整构建顺序（依赖驱动）：prepare_driving_city → node_city_roads → prepare_city_ground → build_driving_assets[Blender] → copy car→traffic-car → prepare_city_streets → build_city_ground[B] → build_city_detail_assets[B] → prepare_coastal_infrastructure → build_coastal_infrastructure[B] → optimize_city buildings roads terrain → copy indigo-gt→car.glb → prepare_city_ambient → (M2) signals/canopy/ebikes --prepare+[B] → rooftops → facades→split→colorize→diversity→atlas→relief
- 失败测试速查：当前无已知失败（292/292）；历史条目已清空——如再出现 mountains/coastal-horizon/autopilot 类失败，先查对应管线段是否重跑完整（链末段缺失是 1e47291 修过的坑：car.glb LFS 恢复/facade diversity 重跑）
- 遇到 "Unexpected magic: 1868833084" = Vite 返回了 index.html——文件不存在，或 **dev server 启动后才新增的 public/ 二进制**（vite 只在启动时索引 public/，见 vite.config.ts 注释）→ 先 curl 确认，新增过文件就重启 dev server
- GTA_SZ（D:\2_Projects\github\GTA_SZ）是参照仓库，其 git 工作树处于异常状态（大量文件标记删除但实际存在，git lfs pull 静默失败），LFS 取物一律走 GitHub media URL
- 今日排障/部署三篇 worklog（~/worklogs，检索关键词：ECS 部署 / 子路径化 / crypto.subtle）：「GTA_AMOY 部署阿里云 ECS 全程」「ECS 部署子路径化 /GTA_AMOY/」「纯 HTTP 部署下 crypto.subtle 缺失」——含 SSH 锁死恢复、PowerShell 传参坑、nginx reload 瞬态 404、安全上下文教训等完整链路
