"""只读资料适配。每个外部调用均有超时，失败保留缺失状态。"""
import asyncio
import hashlib
import json
import os
import re
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import httpx

from .models import ImportRequest, SearchRequest, Source, Weather, WeatherRequest

ROOT = Path(__file__).resolve().parents[1]


def load_local_env():
    # 仅读取本独立项目，环境变量优先；不寻找或暴露其他项目的密钥。
    path = ROOT / ".env.travel"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip().strip("\"'")
        if re.fullmatch(r"[A-Z][A-Z0-9_]*", key) and value:
            os.environ.setdefault(key, value)


load_local_env()


class ProviderError(Exception):
    def __init__(self, message: str, status: int = 502):
        self.message, self.status = message, status
        super().__init__(message)


def llm_config():
    key = os.getenv("TRAVEL_LLM_API_KEY") or os.getenv("ARK_API_KEY") or os.getenv("OPENAI_API_KEY", "")
    base = os.getenv("TRAVEL_LLM_BASE_URL") or os.getenv("ARK_BASE_URL") or (
        "https://ark.cn-beijing.volces.com/api/v3" if os.getenv("ARK_API_KEY") else "https://api.openai.com/v1")
    model = os.getenv("TRAVEL_LLM_MODEL") or os.getenv("DOUBAO_PRO_MODEL") or os.getenv("OPENAI_MODEL", "")
    return key, base.rstrip("/"), model


def provider_status():
    key, _, model = llm_config()
    return {"providers": [
        {"id":"xiaohongshu", "name":"小红书", "ready":bool(os.getenv("XHS_MCP_URL")), "message":"已配置本地服务；登录状态需搜索时核验" if os.getenv("XHS_MCP_URL") else "待连接本地小红书服务并登录，可先粘贴笔记正文"},
        {"id":"douyin", "name":"抖音", "ready":bool(os.getenv("DOUYIN_SEARCH_TOKEN") and os.getenv("DOUYIN_DEVICE_ID")), "message":"已配置；搜索权限与令牌有效性尚待实际调用核验" if os.getenv("DOUYIN_SEARCH_TOKEN") else "需要官方关键词搜索权限及令牌，可先粘贴攻略文字"},
        {"id":"web", "name":"网页搜索", "ready":bool(os.getenv("BOCHA_API_KEY") or os.getenv("TAVILY_API_KEY")), "message":"已配置网页搜索" if os.getenv("BOCHA_API_KEY") or os.getenv("TAVILY_API_KEY") else "待配置博查或 Tavily"},
        {"id":"weather", "name":"Open-Meteo 天气", "ready":True, "message":"无需密钥，需联网；仅在预报时间范围内提供天气"},
        {"id":"llm", "name":"行程模型", "ready":bool(key and model), "message":"已配置；有效性在生成时核验" if key and model else "待配置模型密钥和模型名称"},
    ], "llm_ready":bool(key and model)}


def source_id(url: str, prefix: str = "src") -> str:
    return prefix + "-" + hashlib.sha256(url.encode()).hexdigest()[:12]


def safe_public_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        return parsed.scheme == "https" and bool(host) and not parsed.username and not parsed.password and host not in {"localhost", "127.0.0.1", "::1"} and not re.fullmatch(r"[\d.]+", host)
    except ValueError:
        return False


async def request_json(method, url, *, timeout=20, **kwargs):
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
            response = await client.request(method, url, **kwargs)
            if response.status_code in {401, 403}:
                raise ProviderError("数据源拒绝访问，请检查登录、权限或密钥。", 503)
            if response.status_code == 429:
                raise ProviderError("数据源达到调用额度，请稍后重试。", 503)
            response.raise_for_status()
            data = response.json()
            if not isinstance(data,dict):
                raise ProviderError("数据源返回了不支持的响应格式。")
            return data
    except ProviderError:
        raise
    except httpx.TimeoutException:
        raise ProviderError("数据源请求超时，未返回可用结果。") from None
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        raise ProviderError("数据源连接失败或响应格式异常。") from None


def xhs_base():
    value = os.getenv("XHS_MCP_URL", "").rstrip("/")
    if not value:
        raise ProviderError("小红书尚未连接本地服务；请先配置 XHS_MCP_URL 并登录。", 503)
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or parsed.hostname not in {"localhost", "127.0.0.1", "::1"} or parsed.username or parsed.password:
        raise ProviderError("XHS_MCP_URL 仅接受本机 localhost、127.0.0.1 或 ::1 服务。", 503)
    return value


async def xhs_call(path: str, payload: dict):
    token = os.getenv("XHS_MCP_TOKEN", "")
    headers = {"Authorization":f"Bearer {token}"} if token else {}
    data = await request_json("POST", xhs_base()+path, json=payload, headers=headers, timeout=25)
    if data.get("success") is False:
        raise ProviderError("小红书未返回内容，请确认服务已登录并且笔记仍可访问。", 503)
    return data.get("data", data)


def find_note(data):
    if isinstance(data, dict):
        for key in ("note", "noteCard", "note_card"):
            if isinstance(data.get(key), dict):
                return data[key]
        if "desc" in data or "displayTitle" in data:
            return data
        for child in data.values():
            result = find_note(child)
            if result:
                return result
    elif isinstance(data, list):
        for child in data[:5]:
            result = find_note(child)
            if result:
                return result
    return {}


async def xhs_detail(feed_id: str, token: str):
    return await xhs_call("/api/v1/feeds/detail", {"feed_id":feed_id,"xsec_token":token,"load_all_comments":False})


async def search_xhs(keyword: str):
    data = await xhs_call("/api/v1/feeds/search", {"keyword":keyword,"filters":{"sort_by":"综合","note_type":"不限"}})
    feeds = data.get("feeds", []) if isinstance(data, dict) else []
    sources, warnings = [], []
    for feed in feeds[:5]:
        fid = str(feed.get("id", ""))
        if not re.fullmatch(r"[A-Za-z0-9_-]{8,80}", fid):
            continue
        note = find_note(feed)
        title = str(note.get("displayTitle") or note.get("title") or "小红书笔记")
        excerpt, status = str(note.get("desc") or title), "snippet"
        token = feed.get("xsecToken") or feed.get("xsec_token")
        # 浏览器服务串行读取，避免多个标签同时操控一个登录会话。
        if token and len(sources) < 2:
            try:
                full = find_note(await xhs_detail(fid, str(token)))
                if full.get("desc"):
                    excerpt, status = str(full["desc"]), "full"
                    title = str(full.get("title") or title)
            except ProviderError:
                warnings.append("部分小红书笔记只获得搜索摘要，未读到完整正文。")
        url = f"https://www.xiaohongshu.com/explore/{fid}"
        sources.append(Source(id=source_id(url,"xhs"),platform="xiaohongshu",title=title[:200],url=url,
                              excerpt=excerpt[:5000],content_status=status))
    return sources, list(dict.fromkeys(warnings))


async def search_douyin(keyword: str):
    token, device = os.getenv("DOUYIN_SEARCH_TOKEN", ""), os.getenv("DOUYIN_DEVICE_ID", "")
    if not token or not device:
        raise ProviderError("抖音关键词检索需要已获准的官方权限、令牌和 device_id；当前不可用。",503)
    data = await request_json("GET", "https://open.douyin.com/dy_open_api/v1/search/video/",
        headers={"access-token":token}, params={"keyword":keyword,"count":5,"device_id":device})
    body = data.get("data", {})
    if not isinstance(body,dict):
        raise ProviderError("抖音搜索响应格式异常，未提取任何视频资料。")
    error = body.get("error_code", data.get("error_code", 0))
    if error not in (None,0,"0"):
        raise ProviderError("抖音官方搜索未获授权或令牌失效，未返回攻略。",503)
    items = body.get("list") or body.get("videos") or body.get("aweme_list") or []
    if not isinstance(items,list):
        raise ProviderError("抖音视频列表格式异常，请检查当前接口权限与版本。")
    sources = []
    for item in items[:5]:
        if not isinstance(item,dict):
            continue
        share_info = item.get("share_info") or {}
        url = item.get("share_url") or (share_info.get("share_url", "") if isinstance(share_info,dict) else "")
        vid = str(item.get("aweme_id") or item.get("item_id") or "")
        if not url and re.fullmatch(r"\d{10,30}",vid):
            url = "https://www.douyin.com/video/"+vid
        if not safe_public_url(url):
            continue
        description = str(item.get("title") or item.get("desc") or "抖音视频信息")
        sources.append(Source(id=source_id(url,"dy"),platform="douyin",title=description[:150],url=url,
            excerpt=description[:5000],content_status="snippet"))
    return sources, ["抖音检索只使用接口返回的标题/描述；尚未转写视频音频或解析画面。"]


async def search_web(keyword: str):
    bocha, tavily = os.getenv("BOCHA_API_KEY", ""), os.getenv("TAVILY_API_KEY", "")
    if bocha:
        data = await request_json("POST", "https://api.bochaai.com/v1/web-search",
            headers={"Authorization":f"Bearer {bocha}"},json={"query":keyword,"count":8,"freshness":"noLimit","summary":True})
        if data.get("code") not in (None,200,"200",0):
            raise ProviderError("博查搜索请求失败，请检查密钥与额度。",503)
        rows = data.get("data",{}).get("webPages",{}).get("value",[])
        items = [(r.get("name","网页结果"),r.get("url",""),r.get("summary") or r.get("snippet", "")) for r in rows]
    elif tavily:
        data = await request_json("POST", "https://api.tavily.com/search",json={"api_key":tavily,"query":keyword,
            "max_results":8,"include_answer":False,"include_raw_content":False})
        items = [(r.get("title","网页结果"),r.get("url",""),r.get("content", "")) for r in data.get("results",[])]
    else:
        raise ProviderError("尚未配置博查或 Tavily 网页搜索。",503)
    sources = []
    for title,url,excerpt in items:
        if not safe_public_url(url):
            continue
        host = urlparse(url).hostname or ""
        platform = "xiaohongshu" if host.endswith("xiaohongshu.com") else "douyin" if host.endswith("douyin.com") else "official" if host.endswith(".gov.cn") else "web"
        sources.append(Source(id=source_id(url),platform=platform,title=str(title)[:200],url=url,excerpt=str(excerpt)[:5000],content_status="snippet"))
    return sources, ["网页搜索结果仅为摘要；即使链接来自社交平台，也不等于已读取完整攻略。"]


async def search_sources(request: SearchRequest):
    query = f"{request.destination} {request.keyword}".strip()
    functions = {"xiaohongshu":search_xhs,"douyin":search_douyin,"web":search_web}
    selected = list(functions) if request.platform == "all" else [request.platform]
    results = await asyncio.gather(*(functions[name](query) for name in selected),return_exceptions=True)
    sources, warnings, statuses = [], [], {}
    for name,result in zip(selected,results):
        if isinstance(result,Exception):
            statuses[name] = "unavailable"
            warnings.append(result.message if isinstance(result,ProviderError) else f"{name} 数据读取失败，未使用该来源。")
        else:
            rows, notes = result
            statuses[name] = "ready" if rows else "empty"
            sources.extend(rows)
            warnings.extend(notes)
            if not rows:
                warnings.append(f"{name} 未返回可用攻略。")
    unique = {s.id:s for s in sources}
    return {"sources":list(unique.values()),"warnings":list(dict.fromkeys(warnings)),"provider_status":statuses}


ALLOWED_IMPORT_HOSTS = ("xiaohongshu.com","xhslink.com","douyin.com","iesdouyin.com")


def validate_import_url(url: str):
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower().rstrip(".")
        if parsed.scheme != "https" or parsed.username or parsed.password or parsed.port not in {None,443}:
            raise ValueError()
        if not any(host == domain or host.endswith("."+domain) for domain in ALLOWED_IMPORT_HOSTS):
            raise ValueError()
        if "\\" in url or any(ord(c)<32 for c in url):
            raise ValueError()
    except ValueError:
        raise ProviderError("仅支持小红书或抖音官方域名的 HTTPS 分享链接。",422) from None
    return parsed


async def import_source(request: ImportRequest):
    parsed = validate_import_url(request.url)
    platform = "xiaohongshu" if any(x in (parsed.hostname or "") for x in ["xiaohongshu.com","xhslink.com"]) else "douyin"
    # 从不直接请求用户 URL，不跟随短链跳转；避免把链接导入变成任意网络访问。
    if request.text.strip():
        citation_url = parsed._replace(query="",fragment="").geturl()
        src = Source(id=source_id(citation_url+request.text,"import"),platform=platform,title="手动导入的攻略文字",
            url=citation_url,excerpt=request.text.strip()[:15000],content_status="snippet")
        return {"sources":[src],"warnings":["正文由你手动提供，未与平台原文核对；没有解析视频、图片或评论。"]}
    if platform == "xiaohongshu" and (parsed.hostname or "").endswith("xiaohongshu.com"):
        match = re.search(r"/(?:explore|discovery/item)/([a-fA-F0-9]{24})(?:/|$)",parsed.path)
        token = parse_qs(parsed.query).get("xsec_token",[""])[0]
        if match and token:
            note = find_note(await xhs_detail(match.group(1),token))
            if note.get("desc"):
                url = "https://www.xiaohongshu.com/explore/"+match.group(1)
                return {"sources":[Source(id=source_id(url,"xhs"),platform=platform,title=str(note.get("title") or "小红书笔记"),
                        url=url,excerpt=str(note["desc"])[:15000],content_status="full")],"warnings":[]}
    return {"sources":[],"warnings":["当前链接未读取到正文。请粘贴攻略文字；短链与抖音视频内容暂不自动解析。"]}


def sanitize_materials(materials: list[Source]) -> list[Source]:
    """浏览器送来的材料只能标作用户提供的摘要，不继承自称的官方或全文身份。"""
    result = []
    for item in materials[:10]:
        if item.content_status in {"sample","unavailable"} or not item.excerpt.strip():
            continue
        if not safe_public_url(item.url):
            raise ProviderError("提供的材料必须包含有效的 HTTPS 来源链接。",422)
        parsed = urlparse(item.url)
        url = parsed._replace(query="",fragment="").geturl()
        result.append(Source(id=source_id(url+item.excerpt,"provided"),platform="web",
            title="用户提供 · "+item.title[:180],url=url,excerpt=item.excerpt[:6000],content_status="snippet"))
    return result


WEATHER_URL = "https://open-meteo.com/en/docs"
CITY_ALIASES = {"杭州":"Hangzhou","杭州市":"Hangzhou","上海":"Shanghai","北京":"Beijing","成都":"Chengdu","苏州":"Suzhou","南京":"Nanjing","广州":"Guangzhou","深圳":"Shenzhen","重庆":"Chongqing","西安":"Xi'an"}


def unknown_weather(day: date, message: str, status="unknown"):
    return Weather(date=day.isoformat(),description=message,source_url=WEATHER_URL,status=status)


def weather_description(code):
    if code == 0: return "晴"
    if code in (1,2,3): return "多云" if code != 3 else "阴"
    if code in (45,48): return "雾"
    if code in (51,53,55,56,57): return "毛毛雨"
    if code in (61,63,65,66,67,80,81,82): return "降雨"
    if code in (71,73,75,77,85,86): return "降雪"
    if code in (95,96,99): return "雷暴"
    return "天气现象待确认"


async def fetch_weather(request: WeatherRequest):
    dates = [request.start_date+timedelta(days=i) for i in range((request.end_date-request.start_date).days+1)]
    today = date.today()
    horizon = today+timedelta(days=15)
    in_range = [d for d in dates if today <= d <= horizon]
    if not in_range:
        return {"days":[unknown_weather(d,"不在可查询预报范围内") for d in dates],"status":"unknown",
                "source_url":WEATHER_URL,"warnings":["仅提供未来约 16 天的预报；过去日期或更远日期保持未知，不用气候均值代替天气。"]}
    geo = await request_json("GET","https://geocoding-api.open-meteo.com/v1/search",params={
        "name":CITY_ALIASES.get(request.destination,request.destination),"count":5,"language":"zh","format":"json"})
    locations = geo.get("results",[])
    if not isinstance(locations,list):
        raise ProviderError("天气地点查询返回格式异常，请稍后重试。")
    if not locations:
        raise ProviderError("天气服务未找到目的地，请填写城市名，必要时附上国家或省份。",422)
    city = locations[0]
    if not isinstance(city,dict) or not all(isinstance(city.get(k),(int,float)) for k in ("latitude","longitude")):
        raise ProviderError("天气服务未返回有效的城市坐标。")
    params = {"latitude":city["latitude"],"longitude":city["longitude"],"daily":"temperature_2m_min,temperature_2m_max,weather_code,precipitation_probability_max",
        "timezone":city.get("timezone","auto"),"forecast_days":16}
    response = await request_json("GET","https://api.open-meteo.com/v1/forecast",params=params)
    daily = response.get("daily",{})
    if not isinstance(daily,dict) or not isinstance(daily.get("time"),list):
        raise ProviderError("天气服务未返回按日预报，未生成天气信息。")
    weather_fields = ("temperature_2m_min","temperature_2m_max","weather_code","precipitation_probability_max")
    if any(not isinstance(daily.get(k),list) for k in weather_fields):
        raise ProviderError("天气预报缺少温度或降水字段，请稍后重试。")
    found = {}
    for i,ds in enumerate(daily.get("time",[])):
        if not isinstance(ds,str):
            raise ProviderError("天气预报日期格式异常。")
        def value(key):
            rows = daily.get(key,[])
            return rows[i] if i < len(rows) else None
        if value("temperature_2m_min") is None or value("temperature_2m_max") is None:
            continue
        try:
            found[ds] = Weather(date=ds,temp_min=value("temperature_2m_min"),temp_max=value("temperature_2m_max"),
                description=weather_description(value("weather_code")),precipitation_probability=value("precipitation_probability_max"),
                source_url=WEATHER_URL,status="forecast")
        except ValueError:
            raise ProviderError("天气预报包含无效数值，未展示该结果。") from None
    days = [found.get(d.isoformat()) or unknown_weather(d,"暂未获得该日期的预报") for d in dates]
    warnings = [f"天气地点匹配：{city.get('name',request.destination)}，{city.get('admin1','')} {city.get('country','')}；如同名城市匹配错误，请细化目的地。"]
    if any(d.status != "forecast" for d in days):
        warnings.append("部分日期超出预报范围，保持未知，请临近出行时更新。")
    return {"days":days,"status":"forecast" if all(d.status=="forecast" for d in days) else "partial","source_url":WEATHER_URL,"warnings":warnings}
