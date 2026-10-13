"""One-shot generator: emits data/landmarks specs with OSM rings injected.

Evidence labels follow the agent-workflow contract (reported/measured/estimated).
Run once: PYTHONUTF8=1 .venv/Scripts/python.exe scripts/landmarks/write_specs.py
"""
import json
from pathlib import Path

R = json.loads(Path('artifacts/landmark-rings/rings.json').read_text(encoding='utf-8'))
OUT = Path('data/landmarks')


def ring(key):
    entry = R[key]
    return {'osmId': entry['osmId'], 'name': entry['name'], 'footprintWGS84': entry['ring']}


def write(name, spec):
    path = OUT / f'{name}.json'
    path.write_text(json.dumps(spec, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print('wrote', path, len(json.dumps(spec)))


# ---------------------------------------------------------------- riguangyan
write('riguangyan', {
    'schemaVersion': 1, 'id': 'riguangyan', 'name': '日光岩 · 龙头山',
    'status': 'source-grounded exterior: OSM node peak position; reported elevation; photo-estimated rock form',
    'sources': ['osm-fujian-snapshot', 'wikipedia-gulangyu', 'bendibao-riguangyan', 'chinaholiday-riguangyan'],
    'site': {
        'centerWGS84': [118.062257, 24.444632],
        'basis': 'osm-node/1762860367 (日光岩) co-located with node/8411299103 (龙头山 natural=peak)',
        'note': '鼓浪屿中部偏南；游戏地形为平地，岩体模型自带山体',
    },
    'peak': {'elevationMeters': {'value': 92.7, 'basis': 'reported'},
             'variants': '92.68 (chinaholiday) / 92.6 (bendibao 日光岩寺页) recorded'},
    'form': {
        'kind': '两块巨石一竖一横相倚而立，峰顶巨石直径40余米',
        'basis': 'reported (bendibao/福建省旅游协会)',
        'hillMassMeters': {'value': 120, 'basis': 'estimated', 'method': 'photo/satellite estimate of the granite hill base span; uncertainty ±25m'},
    },
    'temple': {'name': '日光岩寺（莲花庵 · 一片瓦）', 'kind': '天然石洞覆巨石为顶，绿瓦红柱，弥陀殿与大雄殿对合而设',
               'position': '岩体东南麓', 'basis': 'reported (导游词/bendibao)'},
    'zheng': {'kind': '龙头山寨寨门（高1.7m宽0.74m）与水操台遗址（闽海雄风石刻）', 'basis': 'reported'},
    'limitations': [
        '岩体轮廓为照片/卫星估计，非测绘；巨石组合简化为山体+主峰立石+横石三段',
        '日光岩寺简化为绿瓦建筑组，不复原对合殿格局',
        '寨门/水操台以小型石构点缀示意',
    ],
})

# --------------------------------------------------------------------- bagua
b = ring('bagua')
write('bagua', {
    'schemaVersion': 1, 'id': 'bagua', 'name': '八卦楼 · 风琴博物馆',
    'status': 'source-grounded exterior: OSM-mapped footprint; reported heights; wikidata-cross-validated position',
    'sources': ['osm-fujian-snapshot', 'wikipedia-bagua', 'bendibao-bagua', 'people-bagua-2024'],
    'site': {
        'centerWGS84': [118.063306, 24.450129],
        'basis': 'osm-way centroid; zh.wikipedia 24.4501N 118.06327E 互洽',
        'note': '鼓浪屿东北部笔架山东北麓，坐西南朝东北，俯瞰厦门港',
    },
    'footprint': {'osmId': b['osmId'], 'name': b['name'], 'footprintWGS84': b['footprintWGS84']},
    'heights': {
        'totalMeters': {'value': 25.7, 'basis': 'reported (bendibao)'},
        'domeMeters': {'value': 10, 'basis': 'reported (bendibao)'},
        'note': '体量和高度均为鼓浪屿别墅之最 (people.cn 2024)',
    },
    'form': {
        'storeys': '地下隔潮层 + 主体三层；三层为八角形平台，上覆八棱红色穹顶（仿耶路撒冷岩石圆顶）',
        'basis': 'reported (wikipedia/资产描述)',
        'plan': '十字形平面分区，四端耳房',
        'orientation': '坐西南朝东北',
    },
    'built': {'start': 1907, 'completed': {'value': 1920, 'basis': 'wikipedia'},
              'note': 'people.cn 2024 称 1930 穹顶封顶——完工年份分歧已记录'},
    'limitations': [
        '25.7m 是否含穹顶存在表述歧义（按含穹顶处理，墙体段约 15.7m）',
        '十字形平面与耳房按文字描述简化；八角鼓座直径按足印内切估计',
        '建筑面积多源分歧（5786 wiki / 6300 主楼 people / 3710 本地宝）不作几何依据',
    ],
})

# ------------------------------------------------------------------ xiamenzhan
write('xiamenzhan', {
    'schemaVersion': 1, 'id': 'xiamenzhan', 'name': '厦门站',
    'status': 'source-grounded exterior: OSM railway-station node position; official reported dimensions; photo-estimated form',
    'sources': ['osm-fujian-snapshot', 'baidu-baike-xiamenzhan', 'railway-net-2014', 'xmu-news-placeholder'],
    'site': {
        'centerWGS84': [118.109343, 24.472126],
        'basis': 'osm-node/8829523163 railway=station（湖滨东路/梧村街道）',
        'note': 'M1 游戏标记 (118.1075,24.4777) 偏北约 700m，本 spec 移至实测站点；地址 思明区厦禾路900号',
    },
    'dims': {
        'lengthNorthSouthMeters': {'value': 206, 'basis': 'reported (南昌铁路/百科)'},
        'widthEastWestMeters': {'value': 145, 'basis': 'reported (百科)'},
        'archTopMeters': {'value': 31, 'basis': 'reported (铁路网 2014 施工报道)'},
        'roofTrussSpanMeters': {'value': 67, 'basis': 'reported'},
        'floorArea': '2.76万m² (2016 通报/维基) vs 2.16万m² (中国铁路 2024)——分歧记录，不作几何依据',
    },
    'form': {
        'kind': '白鹭展翅：白色钢结构大跨屋盖，拱顶最高31m，V型巨柱，象牙白+海天蓝，玻璃幕墙',
        'basis': 'reported (海峡网/闽南网 2016)',
        'layout': '南北站房夹高铁站台（5台9线），高架候车厅上跨线路；北站房面厦禾路，南站房面站南路',
    },
    'rebuilt': '2012-12 开工，2015-02 南站房投用，2016-01 北站房投用',
    'limitations': [
        'OSM 无站房建筑足印，平面按报道的 206×145m 与站台关系简化为南北两翼+上跨拱顶',
        '屋盖按拱顶 31m 单拱示意，未复原多跨曲线细部',
    ],
})

# ----------------------------------------------------------------------- xmu
X = {r['id']: r for r in json.loads(Path('artifacts/landmark-rings/xmu-buildings.json').read_text(encoding='utf-8'))}
qunxian_row = {
    'axisFrom': '囊萤楼西端 → 映雪楼东端（OSM 中心连线，方位约 116°）',
    'buildingsWestToEast': [
        {'name': '囊萤楼', 'osmId': 'way/156122793', 'widthMeters': 49.83, 'depthMeters': 17.16, 'floors': 3,
         'roof': '西式双坡橙瓦，山墙尖拱窗，三楼前廊8根西式圆柱'},
        {'name': '同安楼', 'osmId': None, 'widthMeters': 50.01, 'depthMeters': 10.2, 'floors': 2,
         'roof': '双翘脊悬山顶燕尾式，绿琉璃瓦（官网校史称中式绿瓦宫殿式屋面）'},
        {'name': '群贤楼', 'osmId': 'way/156122784', 'widthMeters': 73.75, 'depthMeters': 30.17, 'floors': '中部3层两翼2层',
         'roof': 'T形平面；中部双翘脊重檐歇山顶绿琉璃瓦，两翼悬山燕尾'},
        {'name': '集美楼', 'osmId': 'way/156122801', 'widthMeters': 50.84, 'depthMeters': 10.77, 'floors': 2,
         'roof': '双翘脊悬山顶燕尾式，绿琉璃瓦；内设鲁迅纪念馆'},
        {'name': '映雪楼', 'osmId': 'way/156122775', 'widthMeters': 49.83, 'depthMeters': 17.16, 'floors': 3,
         'roof': '西式双坡橙瓦，与囊萤对称'},
    ],
    'gapMeters': 6,
    'dimBasis': 'reported (厦门大学资产与后勤事务管理处：群贤楼群各楼面宽/进深)',
    'positionBasis': 'row anchored on OSM way/156122784 群贤楼群 centroid；行向按囊萤(way/156122793)→映雪(way/156122775)中心连线',
}
jiageng_row = {
    'buildingsNorthToSouth': [
        {'name': '保欣丽英楼（嘉庚1）', 'floors': 6},
        {'name': '成枫楼（嘉庚2）', 'floors': 6},
        {'name': '颂恩楼（嘉庚3 · 主楼）', 'floors': 21, 'floorAreaMeters': 21000, 'note': '1998-06 开工 2001-04 竣工'},
        {'name': '祖营楼（嘉庚4）', 'floors': 6},
        {'name': '钟铭选楼（嘉庚5）', 'osmId': 'way/156122773', 'floors': 6},
    ],
    'fromBuildingFootprintMeters': {'value': [44, 19], 'basis': 'estimated', 'method': 'photo estimate; official gives only group total 49000 m²'},
    'songenRoof': '绿色琉璃攒尖/台阶式塔顶（照片），21层约 69m 檐口+塔顶约 12m（estimated from 21层 reported）',
    'fromRoof': '红瓦硬山双坡（官网：红瓦、坡顶、硬山延续芙蓉/建南从楼意象）',
    'layout': '一字排开，主楼与南北从楼以廊道相连，东侧嘉庚广场+120m 花岗石大台阶',
    'positionBasis': 'row anchored on OSM way/156122776 嘉庚楼群 centroid，行向按钟铭选楼(南端, way/156122773)→群中心连线（约 23° NNE）',
    'dimBasis': 'floors/建筑面积 reported (厦门大学基建处/新闻网)；从楼 footprint 为照片估计',
}
jiannan = {
    'osmId': 'way/560033573',
    'widthMeters': 47.12, 'depthMeters': 69.035, 'floorAreaMeters': 5578,
    'gateTowerFloors': 4, 'gateRoof': '双翘脊重檐歇山顶燕尾式，绿琉璃瓦',
    'hall': '单层西式双坡顶红瓦，前部门楼4层',
    'group': '建南楼群（成义/南安/建南/南光/成智，1951-1954）沿山势半月形围合上弦场，外轮入厦门海域即见',
    'dimBasis': 'reported (厦门大学资产与后勤事务管理处)',
    'orientation': '面南偏东朝上弦场与海（estimated from 上弦场位置）',
}
write('xmu', {
    'schemaVersion': 1, 'id': 'xmu', 'name': '厦门大学 · 嘉庚建筑群',
    'status': 'source-grounded exterior: OSM-mapped group anchors; official per-building dimensions; photo-estimated roofs',
    'sources': ['osm-fujian-snapshot', 'xmu-zichu-2011', 'xmu-jjc-2011', 'xmu-news-2024', 'xmu-arch-2020'],
    'site': {
        'centerWGS84': [118.0907, 24.4392],
        'basis': '群贤-嘉庚楼群带中心（OSM 组环质心平均）',
        'note': 'M1 标记 (118.0897,24.4366) 在校园西南角，本 spec 移至楼群实测锚点',
    },
    'groups': {'qunxian': qunxian_row, 'jiageng': jiageng_row, 'jiannan': jiannan},
    'anchorsWGS84': {
        'nangyingCenter': [118.089011, 24.43988], 'yingxueCenter': [118.091658, 24.438699],
        'qunxianGroupCenter': [118.090445, 24.439328],
        'jiagengGroupCenter': [118.092488, 24.440225], 'zhongmingxuanCenter': [118.091906, 24.438976],
        'jiannanCenter': [118.092867, 24.437076],
        'jiannanFacadeBearingDeg': {'value': 140, 'basis': 'estimated',
                                    'method': '建南面朝上弦场与海（上弦场在其东南），按 140° 示意'},
    },
    'limitations': [
        '群贤/同安/集美屋面瓦色存在 2011 资产处(红机平瓦) 与 2024 校史网(绿琉璃) 记载分歧，模型取绿琉璃（与照片一致）',
        '从楼开间/塔顶细部为照片估计；嘉庚广场台阶与连廊简化',
        '建南大会堂依平地建模，山岗高差以石砌台基示意',
    ],
})

# --------------------------------------------------------------------- gaoqi
t3, t4 = ring('gaoqi_T3'), ring('gaoqi_T4')
write('gaoqi', {
    'schemaVersion': 1, 'id': 'gaoqi', 'name': '高崎机场 · T3/T4 航站楼',
    'status': 'source-grounded exterior: OSM-mapped terminal footprints; reported T4 heights/roof; photo-estimated T3',
    'sources': ['osm-fujian-snapshot', 'wikipedia-gaoqi', 'iaion-t4-2014', 'alwindoor-t4', 'xiamen-daily-t4'],
    'site': {
        'centerWGS84': [118.1344, 24.5424],
        'basis': 'T3/T4 OSM 足印质心均值',
        'note': 'ARP 24.5450N 118.1267E (AIXM)；跑道 05/23 3400×45m，05 端 (24.5347,118.1144) 23 端 (24.5539,118.1413)，真方位约 52°；两航站楼均在跑道东南（城市）侧',
    },
    't4': {
        'footprint': {'osmId': t4['osmId'], 'name': t4['name'], 'footprintWGS84': t4['footprintWGS84']},
        'opened': '2014-12-28',
        'heightMeters': {'value': 39, 'basis': 'reported (维基/iaion 屋盖钢结构高度)',
                         'note': '幕墙网载建筑高度 43.1m——分歧记录'},
        'roofProjectionMeters': {'value': [251.7, 136], 'basis': 'reported (iaion 屋盖水平投影东西向×南北向最大值)'},
        'form': 'L形（主楼+指廊）；马鞍形双曲面屋盖，大鹏展翅，融合闽南起翘屋顶；79根倾斜钢柱（柱顶 20.8-37.25m，倾角 2.5°-27.5°）',
        'serves': '非厦门航/南航国内航班',
    },
    't3': {
        'footprint': {'osmId': t3['osmId'], 'name': t3['name'], 'footprintWGS84': t3['footprintWGS84']},
        'opened': '1996-11-08',
        'heightMeters': {'value': 25, 'basis': 'estimated', 'method': '照片估计主楼檐口；无权威数值'},
        'form': '白色闽南大厝意象/燕尾脊，候机指廊 768m；1996 二期改扩建',
        'serves': '厦门航/南航及国际地区航班',
    },
    'status2026': '运营中；翔安国际机场 2026-12-25 启用后高崎同日关闭（多源），2025 旅客 2919.4 万人次、全国最繁忙单跑道机场',
    'limitations': [
        'T3 高度无权威来源（照片估计）；T4 采用屋盖 39m 而非幕墙口径 43.1m',
        '马鞍形屋盖以双曲抛物面近似；79 根斜柱以立面竖梃示意',
        '跑道/滑行道已有 OSM 道路层，不重复建模',
    ],
})

# -------------------------------------------------------------------- huizhan
h1, h2, h3 = ring('huizhan_big1'), ring('huizhan_big2'), ring('huizhan_big3')
write('huizhan', {
    'schemaVersion': 1, 'id': 'huizhan', 'name': '厦门国际会展中心 · 主展馆',
    'status': 'source-grounded exterior: OSM-mapped hall footprints; reported phase-1 program; photo-estimated shell roofs',
    'sources': ['osm-fujian-snapshot', '91-expo', 'cnenc-xicec', 'sunnews-2026'],
    'site': {
        'centerWGS84': [118.1784, 24.4691],
        'basis': '一/二期主展馆 OSM 足印质心（big1+big2+big3）',
        'note': 'M1 标记 (118.163,24.457) 偏西南约 2.5km，本 spec 移至实测馆区；前埔会展路198号，东南海岸',
    },
    'halls': [
        {'key': 'big1', 'name': '主展馆东段', **{'osmId': h1['osmId'], 'footprintWGS84': h1['footprintWGS84']}},
        {'key': 'big2', 'name': '主展馆西段', **{'osmId': h2['osmId'], 'footprintWGS84': h2['footprintWGS84']}},
        {'key': 'big3', 'name': '辅厅', **{'osmId': h3['osmId'], 'footprintWGS84': h3['footprintWGS84']}},
    ],
    'phase1': {
        'built': '1998-10-01 动工，2000-09 建成投用', 'floorAreaMeters': 165000,
        'halls': '5 个室内展厅（A-E 各 6560 m²），净高中央至两翼 7.6/10/15m；A/E 为 81×81m 无柱展区',
        'lobbyMeters': {'height': 18.5, 'basis': 'reported (中文百科：大堂及功能前区高 18.5m)'},
        'mainBuildingLengthMeters': {'value': 432, 'basis': 'reported (qufair 中文页，低置信转译)'},
        'form': '主体如展翅大鹏/起航巨轮；一至五期沿轴线对称生长（2000/2008/2012/2015/2023，片区总建筑面积 70万 m²）',
    },
    'roof': '展厅大跨金属屋面 + 序厅弧形壳体（照片：连续拱壳天际线）；朝向前广场（西侧会展路）',
    'limitations': [
        '主楼 432m/42.6m 数值来自低置信转译页，仅用于量级校核，几何以 OSM 足印 + 净高/大堂高为基准',
        '拱壳屋面为艺术化连续拱，不复原逐跨桁架',
        '北侧二期馆群（二号馆/D展厅/海峡大剧院）保留通用建筑，不在本轮替换范围',
    ],
})

OUT.mkdir(exist_ok=True)
print('done')
