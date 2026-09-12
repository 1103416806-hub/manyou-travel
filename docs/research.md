# 旅行规划助手：GitHub 竞品调研与第一版复用方案

调研日期：2026-09-12。目标：基于 1103416806-hub/Agentic_search 新建独立项目，面向 AI 策略产品经理作品集。用户确认的流程是：检索小红书、抖音攻略，查询天气及相关信息，制定完整出行计划。

本轮核验范围为仓库文档、许可证信息及关键源码；没有安装运行候选项目，没有验证平台登录、接口权限、实时数据质量或端到端成功率。

## 推荐组合

沿用原项目的搜索编排、重排与补搜机制；参考 AiClient 的旅游信息收集流程；以 xiaohongshu-mcp 接小红书搜索；抖音关键词搜索与链接解析分开接入；参考 ai-trip 的结构化时间轴与冲突检查；天气和地图结果进入行程检查过程。

复用以独立模块或服务为单位。保留源项目版权、许可及必要的修改说明，在新项目中记录采用的版本和文件。当前尚未复制第三方代码。

## 核验结果

| 项目 | 已核验的内容 | 最值得采用的部分 | 复用边界 |
|---|---|---|---|
| [Cooosin/AiClient](https://github.com/Cooosin/AiClient) | README 描述小红书、高德、天气组合；实际服务先调用工具助手生成攻略，再让模型生成 HTML 写入文件，二次检查代码被注释 | 旅行需求清单、信息收集顺序、完整交付内容 | MIT；Java 技术栈，宜迁移流程而非更换现有 Python 后端；提示词要求准确不等于程序已经验证准确 |
| [xpzouying/xiaohongshu-mcp](https://github.com/xpzouying/xiaohongshu-mcp) | 关键词搜索、排序与筛选、笔记详情和评论读取均有代码 | 作为独立 MCP 服务接搜索、读取能力 | Apache-2.0；首次登录由用户完成；搜索过滤刷新失败时可能回退至未过滤结果，需要检查返回时间与异常 |
| [yzfly/douyin-mcp-server](https://github.com/yzfly/douyin-mcp-server) | 分享链接解析，视频音频提取及语音识别 | 抖音攻略链接导入与口播文本提取 | Apache-2.0；2026-07-02 已归档；没有关键词搜索工具；语音转录不等于识别视频画面和所有字幕 |
| [Ripwords/ai-trip](https://github.com/Ripwords/ai-trip) | 每日时间轴、拖拽排序、失败恢复、交通间隔、冲突审查、Google Places 地点补全 | 时间轴＋地图联动；按天检查；问题分级与修复入口 | MIT；Nuxt/Vue，与原 Python 后端需要适配。地点补全失败可返回空信息，不能将所有候选都显示为已核验 |
| [entbappy/TripMate-AI-Using-MCP](https://github.com/entbappy/TripMate-AI-Using-MCP) | OpenWeather 真实请求、Tavily 酒店搜索、LangGraph 汇总流程 | 天气工具封装和搜索结果汇总方式 | MIT；天气只取预报前五条，未按出行日期过滤；航班节点使用机场/航空公司列表后让模型估价，不能当作实时报价 |
| [OSU-NLP-Group/TravelPlanner](https://github.com/OSU-NLP-Group/TravelPlanner) | 独立的规划基准，含常识和硬约束评估代码 | 将预算、餐饮、住宿、交通条件转成可检查规则的思路 | MIT 代码；是评测项目，不是可直接部署的旅游产品。数据使用另按其来源许可核对，自建测试不冒充官方榜单结果 |

## 关键源码入口

- AiClient：[旅行流程](https://github.com/Cooosin/AiClient/blob/master/src/main/java/com/coosin/aiclient/service/TravelService.java)、[需求与攻略提示模板](https://github.com/Cooosin/AiClient/blob/master/src/main/resources/TravelGuidePrompt.txt)。
- 小红书：[搜索](https://github.com/xpzouying/xiaohongshu-mcp/blob/main/xiaohongshu/search.go)、[详情读取](https://github.com/xpzouying/xiaohongshu-mcp/blob/main/xiaohongshu/feed_detail.go)。优先调用其服务，避免把浏览器代码搬进现有检索模块。
- 抖音：[分享链接处理与文本提取](https://github.com/yzfly/douyin-mcp-server/blob/main/douyin_mcp_server/server.py)。
- ai-trip：[每日时间轴](https://github.com/Ripwords/ai-trip/blob/master/app/components/DaySection.vue)、[地图](https://github.com/Ripwords/ai-trip/blob/master/app/components/TripMap.vue)、[行程审查](https://github.com/Ripwords/ai-trip/blob/master/app/components/ItineraryReviewPanel.vue)、[地点补全](https://github.com/Ripwords/ai-trip/blob/master/server/lib/enrich.ts)。
- TripMate：[天气工具](https://github.com/entbappy/TripMate-AI-Using-MCP/blob/main/custom_weather_mcp_server.py)、[后端流程](https://github.com/entbappy/TripMate-AI-Using-MCP/blob/main/backend.py)。
- TravelPlanner：[硬约束评估](https://github.com/OSU-NLP-Group/TravelPlanner/blob/main/evaluation/hard_constraint.py)、[常识约束评估](https://github.com/OSU-NLP-Group/TravelPlanner/blob/main/evaluation/commonsense_constraint.py)。

## 第一版完整使用流程

1. **了解出行要求**：出发地、目的地、日期、人数、预算、住宿位置或偏好、必去地点、出行节奏和交通方式。将不可违反的条件与可权衡的偏好分开。
2. **检索攻略**：围绕城市、季节和人群生成检索词；收集小红书与可访问的抖音内容。保留平台、作者、链接、发布时间及实际取得的内容类型，不把搜索摘要标成全文。
3. **整理候选**：抽取地点、玩法、停留建议、费用线索和注意事项；同名地点消歧、重复攻略去重。多篇转载不能当作多个独立证据。
4. **补充事实**：通过地图核实地点与交通；通过天气服务查询行程日期内的预报；通过官方资料核查营业和预约信息。超出天气预报范围时标记未知，季节经验单独展示。
5. **制定行程**：按天编排早中晚活动、交通间隔、用餐与休息、住宿区域、预算区间及雨天备选；附预约待办和行前准备。缺少实时报价时明确使用估计区间，不编造可订房间或车次余票。
6. **审阅与调整**：以时间轴、地图、来源卡片展示；用户可移除、替换或移动活动。修改后重新检查受影响的日期、交通、预算及必去条件，并允许撤销。

完整计划指覆盖用户出行所需的主要安排和待办，不把尚未确认的营业、价格、交通数据包装成确定事实。

## 小红书与抖音接入判断

小红书已经找到具备关键词搜索源码的独立模块，但仍需在本机验证登录态和搜索效果。

抖音官方有视频搜索接口，产品页同时明确需要申请内测并获批。因此“存在接口文档”不代表当前账户已经有权限。优先验证官方接入资格，获得权限后接自动关键词搜索；未获权限时，可提供公开网页检索到的抖音链接及用户导入链接作为降级路径，界面显示检索范围。链接导入不能标为已完成全站搜索。[官方产品页](https://developer.open-douyin.com/product/search)、[搜索接口说明](https://developer.open-douyin.com/docs/resource/zh-CN/dop/develop/openapi/douyin-search-capability/aweme-dy-video-search)

## 值得参考但不作为首选代码底座

- [Prot10/MyTripPlanner](https://github.com/Prot10/MyTripPlanner)：AGPL-3.0-or-later。地图联动、跨天拖动、AI 修改逐项撤销值得参考；公开 Demo 的 AI 为脚本演示，真实接入另有代码。优先借鉴交互，代码复用需要处理相应许可义务。
- [sarakshnbzg/tripbreeze-ai](https://github.com/sarakshnbzg/tripbreeze-ai)：已核验结构化行程、预算和审阅分支；许可证未确认。作为流程参考。尚未核验天气会驱动重新规划。
- [NanmiCoder/MediaCrawler](https://github.com/NanmiCoder/MediaCrawler)：具备小红书、抖音关键词采集；当前是非商业学习使用许可证，且接入维护更重，不作为第一版默认依赖。
- JourneyPilot：搜索索引能返回项目介绍，但直接访问仓库为 404；本轮排除，不据缓存介绍推荐复用。

## 作品集中的独立贡献与验证

新增贡献应集中在攻略可信度与去重、地点消歧、硬约束检查、天气触发的局部调整、补搜与停止条件、完整且可编辑的行程交付。

在修改提示词与规划策略前，固定原项目版本建立基线。先整理一组规格驱动的测试需求，并明确它们是合成案例而非真实用户样本；以后补充真实失败。评估出行条件满足率、来源支持率、时间冲突、未知信息处理、天气日期匹配、耗时与调用成本。保留独立测试集；有随机性的生成需重复运行。

目前没有评测分数，没有已验证的效果提升比例。

## 实施顺序

1. 新建独立项目并记录原 Agentic_search 版本；保留旧检索流程用于基线。
2. 做小红书搜索、抖音搜索权限/链接解析、天气和地图的最小连通性验证，记录成功、空结果、未登录及失败状态。
3. 定义攻略来源、地点事实、行程活动和约束检查的统一结构，再接入规划流程。
4. 实现时间轴、地图、来源查看和局部调整，展示完整行程。
5. 跑基线与新策略对照，输出演示案例、失败分析和作品集说明。
