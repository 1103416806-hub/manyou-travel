# 后端验证记录

验证日期：2026-09-12。范围：独立 `manyou` 包及本地 FastAPI 接口；未修改上游 `src/agentic_search`。

## 已执行

- FastAPI TestClient：杭州 2、3、4、5 天 × relaxed、balanced、full 共 12 种组合均生成 HTTP 200；通过日期、节奏、活动时长、时间不重叠、引用 ID 与活动 ID 检查。
- 非杭州示例、单日或日期反向请求返回 HTTP 422；请求错误统一为中文 `detail` 字符串，不序列化 Pydantic 异常对象。
- 导入拒绝非 HTTPS、伪装后缀、IP 地址、URL 用户信息、非标准端口、反斜线构造等 6 类输入。允许列表仅限小红书/抖音官方域名。服务不直接请求用户 URL，也不跟随短链跳转。
- 手动导入正文标记为摘要，明确未核对平台全文/未解析视频；引文 URL 去掉 xsec_token 等查询参数。
- 2100 年日期天气返回 `unknown`，温度保持 null，不联网生成伪预报。
- 未配置模型密钥的实时规划返回 HTTP 503，未回退为示例。
- 跨站 Origin 发起 POST 被 HTTP 403 拒绝，防止第三方页面调用本机收费能力。
- Open-Meteo 真实联网查询杭州 2026-09-13 至 2026-09-15 成功：状态 `forecast`，三天温度均非空。

## 尚未进行

- 未配置有效模型密钥，未执行真实付费模型的端到端行程生成。
- 未连接已登录小红书服务，未获得抖音官方搜索权限与令牌，未声称社交检索已端到端验证。
- 地点营业、预约、交通时空可行性、票价未真实核验。live 输出统一为 `limited` 草案，活动 `verified=false`，未经地理核验的坐标为 null。

## 数据隔离与限制

- 不保存隐式导入或检索缓存。前端通过本次 TripRequest 的 `source_materials` 显式传入最多 10 份资料。
- 前端提供的材料重新分配来源 ID，按用户提供的摘要使用；不继承其自称的官方或全文身份；示例材料不进入 live。
- 每个数据源有请求超时；抖音响应结构和天气日期/温度数组缺失会返回明确错误，未知天气不冒充预报。
- 结构校验通过只代表格式和安排约束通过，不等于攻略事实已证实。

## 接口依据

- 小红书只读 HTTP 路由：[主仓库 routes.go](https://github.com/xpzouying/xiaohongshu-mcp/blob/main/routes.go)、[请求类型](https://github.com/xpzouying/xiaohongshu-mcp/blob/main/types.go)。仅使用 search/detail，不调用发布、评论、收藏或点赞。
- 抖音：[官方关键词视频搜索](https://developer.open-douyin.com/docs/resource/zh-CN/dop/develop/openapi/douyin-search-capability/aweme-dy-video-search)。需要获准 `aweme.dy.video_search`，GET 固定官方接口，access-token 与 device_id 从本项目配置读取。
- 天气：[Open-Meteo Forecast](https://open-meteo.com/en/docs)、[Geocoding](https://open-meteo.com/en/docs/geocoding-api)。
