# 慢游 API 合约

所有接口返回普通 JSON，不使用 SSE。`GET /api/demo` 与 `POST /api/plan` 直接返回 Plan。异常返回 HTTP 422（参数）、503（未配置）、502（上游错误），detail 为中文文本。

`POST /api/plan` 输入：
```json
{"destination":"杭州","origin":"上海","start_date":"2026-09-19","end_date":"2026-09-21","travelers":2,"budget":3000,"pace":"balanced","interests":["自然","美食"],"must_visit":"西湖","notes":"","mode":"demo"}
```

示例仅支持杭州 2–5 天；所有地点资料、预算、天气明确为演示或待核实。live 模式必须配置模型与可用证据，不会在失败时悄悄返回示例。天气中的未知数值为 null，status 为 `sample` / `forecast` / `unknown` / `unavailable`。

TripRequest 另支持可选 `source_materials: Source[]`（默认空，最多 10 项）。前端将本次导入或当前搜索资料显式传入。后端仅按用户提供的摘要处理，重新分配来源 ID，忽略自称的官方/全文身份。服务不缓存或隐式跨目的地复用材料。示例材料不用于实时生成。

`GET /api/status` 返回 `{providers:[{id,name,ready,message}],llm_ready:boolean}`。ready 仅表示配置可用，不表示已核验登录、权限或额度。

`POST /api/search` 输入 `{destination,keyword,platform:'all'|'xiaohongshu'|'douyin'|'web'}`；返回 `{sources,warnings,provider_status}`。

`POST /api/weather` 输入 `{destination,start_date,end_date}`；返回 `{days,status,source_url,warnings}`。

`POST /api/import` 输入 `{url,text?:string}`；返回 `{sources,warnings}`。仅支持小红书/抖音 HTTPS 链接；用户粘贴文本按导入材料标注，不视为平台核验。

Plan 使用父任务指定合约：`id,title,destination,origin,start_date,end_date,travelers,budget,mode,summary,days,sources,tips,warnings,cost_breakdown,trace,provider_status`。所有 source_ids 都来自 sources。活动 lat/lng 在无经核验地点数据时为 null；verified 默认 false。
