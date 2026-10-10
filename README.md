# GTA_AMOY · 鹭岛纪

在浏览器中驾驶、行走、飞行，探索一座可玩的厦门岛。基于 OpenStreetMap 地理数据、Blender 资产管线与 Babylon.js 实时渲染。

本项目衍生自 **[GTA_SZ · 深城纪](https://github.com/linranff/GTA_SZ)**（原作者 [linranff](https://github.com/linranff)），感谢原项目提供的完整城市生成管线、渲染架构与工程实践。在本仓库中，城市数据与内容已替换为厦门岛（会展中心、厦门大学、白鹭洲、环岛路、五缘湾等），并完成信号灯、林冠、电动车、立面与屋顶等城市生活层的厦门化。

**在线体验**（桌面浏览器 + WebGL2）：<https://stonechan00.github.io/GTA_AMOY/>

## 快速开始

需要 Node.js（建议 24）、npm、Git LFS 与支持 WebGL2 的桌面浏览器。

```sh
git lfs install
git clone https://github.com/StoneChan00/GTA_AMOY.git
cd GTA_AMOY
git lfs pull
npm ci
npm run dev
```

打开 Vite 输出的地址（通常 `http://127.0.0.1:5173/`）。

```sh
npm test          # 运行测试
npm run build     # 生产构建
npm run preview   # 本地预览构建产物
```

### 更新在线版

```sh
npm run deploy:pages
```

一键构建并发布 GitHub Pages：自动从 `origin` 推导子路径并传入 `--base`、重写产物内的根绝对资源路径（有遗漏会直接构建失败而非上线 404）、以普通文件（非 LFS 指针）推送到 `gh-pages` 分支。非默认子路径（自定义域名等）可用 `DEPLOY_PAGES_BASE=/` 覆盖。

## 操作一览

| 模式 / 按键 | 动作 |
| --- | --- |
| 车辆：WASD / 方向键，Space | 驾驶、手刹 |
| F / T | 上下车；驾驶中切换车辆 / 坦克 |
| 步行：WASD，Shift，C | 行走、奔跑、第一 / 第三人称 |
| G / B | 无人机观察；切换无人机 / 飞机 |
| M / L / J | 地图、光照预设、城市日志 |
| P | 帧率信息 |

## 城市数据

- 道路与建筑轮廓来自 OpenStreetMap（© OpenStreetMap contributors，ODbL）
- 地形高程来自 Copernicus DEM
- 城市为艺术化的压缩演绎（建筑高度、立面与地形有美术加工），并非测绘级数字孪生
- 详细数据来源与署名见 [data/ATTRIBUTION.md](data/ATTRIBUTION.md)

## 许可

代码以 MIT 许可发布，见 [LICENSE](LICENSE)（含原项目版权声明）。

**许可仅覆盖代码。** `public/` 下的模型、贴图与 HDR 环境，以及 `data/` 下的地理数据保留各自的原始许可与署名要求，详见 [public/licenses/](public/licenses/) 与 [data/ATTRIBUTION.md](data/ATTRIBUTION.md)。角色模型由米哈游提供、观海（Guanhai）MMD 改编，原始条款禁止商用与二次分发。本项目为非商业原型，与米哈游 / HoYoverse 无关联，未获其授权或背书。
