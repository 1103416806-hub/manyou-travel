import asyncio
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .demo import build_demo, default_request
from .models import ImportRequest, Plan, SearchRequest, TripRequest, WeatherRequest, validate_plan
from .planner import generate_live
from .providers import ProviderError, fetch_weather, import_source, provider_status, search_sources

ROOT = Path(__file__).resolve().parents[1]
app = FastAPI(title="慢游 · 旅行规划助手",version="0.1.0")


@app.middleware("http")
async def local_mutation_guard(request: Request, call_next):
    # 本地演示服务无账户体系；阻止外站在用户浏览器中发起耗费密钥的跨站请求。
    if request.method == "POST" and request.url.path.startswith("/api/"):
        origin = request.headers.get("origin")
        if origin:
            from urllib.parse import urlparse
            if urlparse(origin).netloc != request.headers.get("host"):
                return JSONResponse(status_code=403,content={"detail":"请从本应用页面发起请求。"})
    return await call_next(request)


@app.exception_handler(ProviderError)
async def provider_error_handler(request, exc: ProviderError):
    return JSONResponse(status_code=exc.status,content={"detail":exc.message})


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request, exc: RequestValidationError):
    labels = {"destination":"目的地","origin":"出发地","start_date":"开始日期","end_date":"结束日期",
              "travelers":"出行人数","budget":"预算","pace":"出行节奏","mode":"规划模式",
              "source_materials":"攻略材料","url":"链接","text":"正文","interests":"兴趣","notes":"补充要求"}
    messages = []
    for error in exc.errors()[:3]:
        loc = error.get("loc",())
        name = next((labels[str(x)] for x in loc if str(x) in labels),"请求内容")
        kind = error.get("type","")
        message = str(error.get("msg","参数不符合要求。"))
        if kind=="value_error":
            message = message.removeprefix("Value error, ")
        elif kind=="missing":
            message = f"请填写{name}。"
        elif kind=="literal_error":
            message = f"{name}不是支持的选项。"
        elif "date" in kind:
            message = f"{name}请使用有效日期（YYYY-MM-DD）。"
        elif kind in {"greater_than_equal","less_than_equal","too_long","string_too_long","string_too_short"}:
            message = f"{name}超出支持范围或长度。"
        else:
            message = f"{name}格式不正确，请检查后重试。"
        messages.append(message)
    return JSONResponse(status_code=422,content={"detail":"；".join(dict.fromkeys(messages))})


@app.get("/api/status")
async def status():
    return provider_status()


@app.get("/api/demo",response_model=Plan)
async def demo():
    return build_demo(default_request())


@app.post("/api/plan",response_model=Plan)
async def plan(request: TripRequest):
    if request.mode == "demo":
        result = build_demo(request)
        problems = validate_plan(result,request)
        if problems:
            raise HTTPException(500,"示例行程未通过结构检查。")
        return result
    try:
        return await asyncio.wait_for(generate_live(request),timeout=170)
    except asyncio.TimeoutError:
        raise ProviderError("此次规划超过等待时间，未生成行程。请稍后重试或减少资料。") from None


@app.post("/api/weather")
async def weather(request: WeatherRequest):
    return await fetch_weather(request)


@app.post("/api/search")
async def search(request: SearchRequest):
    result = await search_sources(request)
    if not result["sources"] and result["provider_status"] and all(x=="unavailable" for x in result["provider_status"].values()):
        raise ProviderError("；".join(result["warnings"]),503)
    return result


@app.post("/api/import")
async def import_text(request: ImportRequest):
    return await import_source(request)


DIST = ROOT / "web" / "dist"
if (DIST/"assets").is_dir():
    app.mount("/assets",StaticFiles(directory=DIST/"assets"),name="assets")


@app.get("/{path:path}")
async def frontend(path: str):
    if path.startswith("api/"):
        raise HTTPException(404,"接口不存在。")
    candidate = (DIST/path).resolve()
    if DIST.resolve() in candidate.parents and candidate.is_file():
        return FileResponse(candidate)
    if (DIST/"index.html").is_file():
        return FileResponse(DIST/"index.html")
    return JSONResponse(status_code=503,content={"detail":"前端尚未构建。API 已就绪，可访问 /api/demo 或 /docs。"})
