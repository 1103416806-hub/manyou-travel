# 上游与参考记录

2026-09-12 从 [1103416806-hub/Agentic_search](https://github.com/1103416806-hub/Agentic_search) 固定提交 `e41c1d7b667f29082f69a55e44c25c809ce25c0d` 创建独立副本。原 MIT 许可证保留在 LICENSE。上游源码、测试与示例保留；旅行应用是独立模块，不回写原仓库。

本轮没有声称七个上游 Agent 全部在旅行流程中运行。第一版采用需求结构化、证据收集、受约束生成和确定性校验的较短流程，便于独立测试和评审。

| 参考 | 采用的思路 | 代码处理 |
| --- | --- | --- |
| [Cooosin/AiClient](https://github.com/Cooosin/AiClient) · MIT | 小红书、地图、天气到旅行计划的资料收集顺序 | 参考流程；新写 Python 和结构化界面，没有复制 Java 或 HTML 生成代码 |
| [xpzouying/xiaohongshu-mcp](https://github.com/xpzouying/xiaohongshu-mcp) · Apache-2.0 | 登录后的搜索和详情接口 | 可选外部服务，不分发其实现 |
| [Ripwords/ai-trip](https://github.com/Ripwords/ai-trip) · MIT | 每日调整、撤销、地图与列表对应 | 交互参考，重新实现 |
| [entbappy/TripMate-AI-Using-MCP](https://github.com/entbappy/TripMate-AI-Using-MCP) · MIT | 天气和检索编排 | 按旅行日期查询，明确未知值 |
| [OSU-NLP-Group/TravelPlanner](https://github.com/OSU-NLP-Group/TravelPlanner) · MIT | 时间、预算和约束独立评估 | 新写合成案例，不是官方基准成绩 |

抖音参考[官方搜索说明](https://developer.open-douyin.com/product/search)和[视频搜索接口](https://developer.open-douyin.com/docs/resource/zh-CN/dop/develop/openapi/douyin-search-capability/aweme-dy-video-search)，权限需要单独申请。

没有复制许可证不明、AGPL 或限制非商业用途项目的代码。横幅为本次生成的意境配图，记录在 `docs/image-notes.md`。

交互地图使用 [Leaflet 1.9.4](https://leafletjs.com/reference.html)，许可证随网页保留在 `web/public/leaflet-license.txt`。底图与点位数据来自 [OpenStreetMap contributors](https://www.openstreetmap.org/copyright)，遵循[瓦片使用政策](https://operations.osmfoundation.org/policies/tiles/)；页面保留署名，只加载当前视口，无离线预取。杭州点位的查询记录与来源见 `docs/map-coordinates.json`，归一后的展示数据见 `manyou/demo_locations.json`。这些位置不代表入口、可达性或营业事实已核验。

## 杭州示例的建议用餐区域 · 2026-09-13

以下位置来自实际查询的 OpenStreetMap 对象，坐标为 WGS84（EPSG:4326），数据署名为 © OpenStreetMap contributors，许可为 [ODbL 1.0](https://www.openstreetmap.org/copyright)。查询为一次性的人工指定地点核对，遵守 [Nominatim 使用政策](https://operations.osmfoundation.org/policies/nominatim/)，串行请求并间隔至少 2 秒；应用不接入公共 Nominatim 作为运行时搜索服务。

| 示例午餐 | 手动选择的区域 | 纬度，经度 | 位置出处 | 选区依据与限制 |
| --- | --- | --- | --- | --- |
| 第 1 天 | 北山街东段 | 30.2627230, 120.1509942 | [北山街道路代表点](https://www.openstreetmap.org/way/29021290) | 结合断桥与下午白堤、孤山的安排，建议在北岸道路周边找餐；未核验具体商家。 |
| 第 2 天 | 之江文化中心周边 | 30.1621809, 120.0964232 | [之江文化中心商业区域代表点](https://www.openstreetmap.org/relation/19222157) | 上午看展后在附近用餐，再转往下午馆区；区域代表点不是公共服务中心入口或餐厅坐标。 |
| 第 3 天 | 龙井路沿线 | 30.2272857, 120.1087497 | [龙井路道路代表点](https://www.openstreetmap.org/way/583614082) | 结合龙井村前往双峰馆区的方向提出找餐建议；道路数据本身不证明附近有营业餐馆。 |
| 第 4 天 | 桥弄街东段 | 30.3207155, 120.1331645 | [桥弄街步行段代表点](https://www.openstreetmap.org/way/345074150) | 位于拱宸桥西侧，衔接上午游桥与下午桥西街区；未核验具体商家。 |
| 第 5 天 | 深潭口—河渚街周边 | 30.2741947, 120.0665378 | [深潭口村落代表点](https://www.openstreetmap.org/node/7309303306) | 在湿地游览与河渚街安排之间寻找午餐；村落代表点不是餐馆或步行入口。 |

第二天的餐饮背景参考[之江文化中心公共服务中心报道](https://tidenews.com.cn/news.html?id=2565525)，第五天参考[河渚街美食报道](https://hznews.hangzhou.com.cn/chengshi/content/2026-02/03/content_9172650.htm)。历史报道仅支持区域背景，不证明出行当天营业、价格或可预订。第一、三、四天的用餐选区属于结合行程的人工推断，不作为商家事实或社交平台检索结果。

界面通过金色编号、虚线圈及顺序箭头展示这些建议。虚线圈半径为人工设定的展示范围，不是 OSM 提供的餐饮边界。第二天因地点靠近，只偏移屏幕标签并用细线连回真实区域中心，参考坐标不变。上述处理仅适用于预设的杭州示例午餐，其余未知位置仍显示“待定位”。展示配置位于 `web/src/dining-areas.ts`。
