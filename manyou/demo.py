"""固定、明确标注的杭州演示材料；不调用任何网络服务。"""
from datetime import date, timedelta
from uuid import uuid4
import json
from pathlib import Path

from .models import Activity, Cost, Day, Plan, Source, Trace, TripRequest, Weather


# 路线费用为示例；真正使用的坐标来自可追溯 WGS84 目录。
DEMO_LOCATIONS = json.loads(Path(__file__).with_name('demo_locations.json').read_text(encoding='utf-8'))['locations']
ROUTES = [
    ("湖边，把脚步放慢", "沿西湖北线散步，给第一天留一点空白。", [
        ("断桥残雪", 30.2596, 120.1495, False, "从北山街走到湖边，停下来看看水面。"),
        ("孤山与白堤", 30.2508, 120.1404, False, "沿湖步行，拍照和休息时间都留在里面。"),
        ("西泠印社外街", 30.2512, 120.1329, False, "小路与湖景，适合没有目的地地走一会儿。"),
        ("北山街", 30.2566, 120.1397, False, "结束前再看一眼湖岸。"),
    ]),
    ("雨天也有好去处", "演示下雨后的室内替代安排；实际天气请单独查询。", [
        ("浙江省博物馆之江馆区", 30.1503, 120.0901, True, "以室内展览替代长时间户外游览，开放与预约需出发前确认。"),
        ("中国丝绸博物馆", 30.2268, 120.1478, True, "从面料与工艺看看杭州，馆区间交通请核查。"),
        ("南宋御街", 30.2385, 120.1713, False, "若雨势减弱，可选短距离散步；否则跳过。"),
        ("河坊街", 30.2370, 120.1731, False, "按体力选择，不必把一天排满。"),
    ]),
    ("走进茶山的绿色", "龙井附近慢行，户外安排需要结合当天雨量。", [
        ("龙井村", 30.2175, 120.1016, False, "茶山周边散步，不进入限制通行区域。"),
        ("中国茶叶博物馆双峰馆区", 30.2289, 120.1179, True, "把茶的知识和茶山风景放在同一天。"),
        ("茅家埠", 30.2419, 120.1175, False, "水边栈道散步，雨天留意路面。"),
        ("浴鹄湾", 30.2307, 120.1259, False, "作为可选的湖边收尾。"),
    ]),
    ("运河边的旧时光", "把运河沿线安排在一起，减少跨城区折返。", [
        ("拱宸桥", 30.3184, 120.1382, False, "沿运河看桥与老街。"),
        ("桥西历史街区", 30.3183, 120.1351, False, "小街与沿河空间，慢慢逛。"),
        ("中国刀剪剑博物馆", 30.3160, 120.1360, True, "作为室内文化活动，开放情况待确认。"),
        ("小河直街", 30.3084, 120.1369, False, "有余力再加这一段。"),
    ]),
    ("城市里留一片湿地", "以西溪为中心，预留返程整理与交通余量。", [
        ("西溪国家湿地公园", 30.2672, 120.0613, False, "湿地漫步；门票、船票和开放范围另行核验。"),
        ("西溪河渚街", 30.2712, 120.0626, False, "安排短距离收尾，不追求走遍全部区域。"),
        ("西溪中国湿地博物馆", 30.2515, 120.0724, True, "雨天可考虑的室内方向，预约信息待确认。"),
        ("西溪东门周边", 30.2632, 120.0791, False, "保留弹性时间，按返程需要结束。"),
    ]),
]


def default_request() -> TripRequest:
    start = date.today() + timedelta(days=7)
    return TripRequest(destination="杭州", origin="上海", start_date=start,
                       end_date=start + timedelta(days=2), travelers=2, budget=3000,
                       interests=["自然风景", "人文", "美食"], must_visit="西湖")


def build_demo(request: TripRequest) -> Plan:
    sources = [Source(id="sample-hangzhou", platform="sample", title="慢游 · 杭州路线演示材料",
        url="https://wgly.hangzhou.gov.cn/", excerpt="人工编排的杭州演示路线。地点、坐标、费用和安排均为展示产品交互，不代表当天开放、报价或真实平台检索结果。", content_status="sample")]
    warnings = ["当前是离线示例：未检索小红书或抖音，未查询真实天气。", "坐标、交通和预算仅供演示，营业时间、预约和票价均待核实。", "住宿为示例预算；往返大交通尚未计入，请按实际订单补充。"]
    if request.must_visit and not any(part in request.must_visit for part in ["西湖", "断桥", "白堤"]):
        warnings.append(f"示例尚未核验必去要求「{request.must_visit}」，请在实时模式补充检索。")
    if request.notes:
        warnings.append("额外要求已记录，但示例不会自动理解并满足所有自然语言要求。")
    count = {"relaxed": 2, "balanced": 3, "full": 4}[request.pace]
    days = []
    for index, day_date in enumerate(request.dates):
        title, description, candidates = ROUTES[index]
        activities = []
        for i, item in enumerate(candidates[:count]):
            name, lat, lng, indoor, detail = item
            location = DEMO_LOCATIONS.get(name, {})
            lat, lng = location.get('lat'), location.get('lng')
            starts = ["09:30", "13:30", "16:00", "18:00"]
            ends = ["11:30", "15:00", "17:00", "19:00"]
            durations = [120, 90, 60, 60]
            activities.append(Activity(id=f"d{index+1}-a{i+1}", time=starts[i], end_time=ends[i],
                title=name, category="attraction", description=detail, duration_minutes=durations[i],
                cost=0, lat=lat, lng=lng, source_ids=["sample-hangzhou"], verified=False,
                indoor=indoor, transport_note="示例预留换乘余量；距离与交通耗时需地图核验。"))
        activities.append(Activity(id=f"d{index+1}-meal", time="11:45", end_time="12:45",
            title="附近午餐 · 留一点当地味道", category="food", description="选择当前区域内的餐馆；尚未检索具体商家，费用为每人示例预算。",
            duration_minutes=60, cost=65 * request.travelers, source_ids=["sample-hangzhou"], indoor=True,
            transport_note="优先选附近餐馆，具体店铺和营业情况待确认。"))
        activities.sort(key=lambda a: a.time)
        weather = Weather(date=day_date.isoformat(), temp_min=21 if index==1 else 23,
            temp_max=26 if index==1 else 29, description="示例 · 小雨" if index==1 else "示例 · 多云",
            precipitation_probability=75 if index==1 else 20, source_url="https://open-meteo.com/", status="sample")
        days.append(Day(date=day_date.isoformat(), title=title, description=description, weather=weather, activities=activities))
    n = len(days)
    costs = [Cost(label="餐饮 · 示例预算", amount=n*150*request.travelers),
             Cost(label="住宿 · 示例预算", amount=(n-1)*350*((request.travelers+1)//2)),
             Cost(label="市内交通 · 示例预算", amount=n*40*request.travelers),
             Cost(label="门票与体验 · 预留", amount=200*request.travelers)]
    if sum(c.amount for c in costs) > request.budget:
        warnings.append("当前示例预算超过你的总预算，且尚未计入往返大交通；需要调整住宿或活动。")
    return Plan(id="demo-"+uuid4().hex[:12], title=f"杭州 {n} 日，慢慢走", destination="杭州", origin=request.origin,
        start_date=request.start_date.isoformat(), end_date=request.end_date.isoformat(), travelers=request.travelers,
        budget=request.budget, mode="demo", summary=f"给 {request.travelers} 位旅行者的杭州 {n} 日示例。沿湖、看展、走入茶山，按你的节奏每天安排 {count} 个地点。所有信息均为演示。",
        days=days, sources=sources, tips=["出发前确认场馆预约、闭馆日和票务。", "按真正天气调整户外安排；示例第二天演示室内替代。", "预算不含往返大交通，也不是实时报价。", "返程当日请根据车次或航班预留交通余量。"],
        warnings=warnings, cost_breakdown=costs,
        trace=[Trace(step="读取需求",status="done",detail=f"杭州 · {n} 天 · {request.travelers} 人"),
               Trace(step="攻略资料",status="sample",detail="使用人工编排的示例，未连接社交平台"),
               Trace(step="天气安排",status="sample",detail="第二天使用雨天演示数据"),
               Trace(step="行程校验",status="done",detail="校验日期、时间冲突、引用；交通与事实仍待核验")],
        provider_status={"xiaohongshu":"demo","douyin":"demo","weather":"sample","llm":"not_used"})
