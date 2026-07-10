# 医保新闻智能资讯服务（医保 HOT）规格说明书

## 1. 项目概述

### 1.1 定位
面向中文用户的医保政策/行业新闻 AI 资讯服务。自动采集、AI 精编、提供 REST API 供 LLM Agent 查询。

### 1.2 对标
参考 [AI HOT](https://aihot.virxact.com) 的架构，将 AI 行业新闻替换为医保领域。

### 1.3 核心价值
- 医保新闻来源分散（国家局、各省局、行业媒体），一站式聚合
- AI 自动摘要、评分、分类，降低信息过载
- REST API + SKILL.md，LLM Agent（Hermes/Claude Code 等）可直接接入

---

## 2. 数据源

### 2.1 RSS 源（第一优先级）
| 来源 | URL | 说明 |
|---|---|---|
| 国家医保局 | 待确认 RSS 地址 | 政策法规、通知公告 |
| 新华网健康频道 | 待确认 | 医保政策解读 |
| 中国医疗保险研究会 | 待确认 | 行业研究 |
| 健康界 | 待确认 | 医疗/医保行业媒体 |
| 医药魔方 | 待确认 | 药品政策、集采信息 |
| 丁香园 | 待确认 | 医药行业动态 |
| 人民日报健康客户端 | 待确认 | 官方口径 |

### 2.2 网页抓取（RSS 不可用时）
- 国家医保局官网 `http://www.nhsa.gov.cn` 通知公告
- 各省医保局官网（首批覆盖 5-10 个重点省份）
- 微信公众号（通过 WeRSS 等第三方工具转 RSS）

### 2.3 来源优先级
1. RSS → 2. 网页结构化抓取 → 3. 手动录入（重要政策）

---

## 3. 数据模型

### 3.1 核心条目（items）

```yaml
id: string              # 唯一ID (cuid/nanoid)
url: string             # 原始链接
title: string           # 原始标题
title_zh: string|null   # 中文标题（AI 翻译，源为中文则留空）
summary_zh: string      # AI 生成中文摘要（~150 字）
source:
  id: string            # 来源ID
  name: string          # 来源显示名
  kind: "rss" | "scraper" | "manual"
published_at: datetime  # 原始发布时间
fetched_at: datetime    # 采集时间
category: enum          # 见 3.2
tags: array<string>     # AI 打的标签

# AI 评分（0-100）
ai_relevance: int       # 医保相关性
quality_score: int      # 内容质量
final_score: int        # 综合分（加权或取高）

# 精选
ai_selected: bool       # 是否入选精选
ai_selected_reason: string|null  # 入选理由（AI 生成，<=60 字）

# 去重
duplicate_of_id: string|null  # 指向主条目
```

### 3.2 医保专属分类

| slug | 中文名 | 说明 |
|---|---|---|
| `policy` | 政策法规 | 国家/地方医保新政策、法规发布 |
| `drugs` | 药品集采 | 国采/省采/联盟采、药品目录调整 |
| `drg-dip` | DRG/DIP | 支付方式改革 |
| `fund` | 医保基金 | 基金监管、飞行检查、骗保案例 |
| `service` | 医保服务 | 异地就医、门诊共济、电子凭证 |
| `industry` | 行业动态 | 商业医保、数字医疗、大健康 |
| `opinion` | 专家观点 | 解读、评论、研究 |

### 3.3 日报（daily）

```yaml
date: date              # 日期
generated_at: datetime  # 生成时间
lead:                   # 头条
  title: string
  summary: string
sections:               # 按分类分组
  - label: string       # 分类中文名
    items: array<item>
flashes: array          # 快讯（一句话标题列表）
```

---

## 4. API 设计

### 4.1 端点

```
Base URL: https://<domain>

GET /api/public/items        条目列表
GET /api/public/daily        最新日报
GET /api/public/daily/{date} 历史日报
GET /api/public/dailies      日报归档列表
GET /api/public/sources      数据源列表
GET /openapi.yaml            OpenAPI 规范
```

### 4.2 接口详情

**GET /api/public/items**

| 参数 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `mode` | `selected`\|`all` | `selected` | 精选 / 全部 |
| `category` | slug | 全部 | 分类筛选 |
| `q` | string | - | 关键词搜索（标题+摘要） |
| `since` | ISO datetime | now-7d | 起始时间（上限 30 天） |
| `take` | 1-100 | 50 | 条数 |
| `cursor` | string | - | 翻页 token |

**GET /api/public/daily**
最新日报（北京时间每天 08:00 生成）

**GET /api/public/daily/{YYYY-MM-DD}**
指定日期日报

**GET /api/public/dailies**
| 参数 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `take` | 1-180 | 30 | 返回最近 N 天的日报列表 |

### 4.3 响应规范
- 匿名只读，无需鉴权
- Nginx `proxy_cache` 5 分钟
- 限流 300 req/min/IP
- CORS: `*`

---

## 5. AI 处理 Pipeline

### 5.1 处理流程
```
采集 → 去重 → AI评分 → AI摘要 → AI分类+打标签 → 精选 → 日报生成
```

### 5.2 各环节说明

| 环节 | 说明 | 频率 |
|---|---|---|
| **采集** | 定时拉取 RSS/抓取网页，新条目入库 | 每 30 分钟 |
| **去重** | URL 精确去重 + 标题相似度去重 | 入库时 |
| **AI 评分** | LLM 对 `relevance` 和 `quality` 打分 | 入库后批量 |
| **AI 摘要** | 用原始内容生成 150 字中文摘要 | 入库后批量 |
| **AI 分类** | 分到 7 个医保分类 + 打标签 | 入库后批量 |
| **精选** | `final_score >= 60` 默认精选 | 评分后 |
| **日报** | 将过去 24h 精选条目按分类组装 | 每天 08:00 |

### 5.3 AI 评分 Prompt 模板

```
你是医保政策分析专家。对以下医保新闻打分（0-100）：

相关性：这篇内容与医保政策的直接关联度
  - 90-100：直接涉及医保政策、支付、药品目录等
  - 70-89：间接相关（医疗改革、药品定价等）
  - 50-69：泛医疗健康领域
  - 0-49：弱相关

质量：内容的实质性
  - 90-100：首发政策文件、官方解读
  - 70-89：深度分析、行业研判
  - 50-69：常规报道
  - 0-49：标题党、软文

返回：{"relevance": N, "quality": N, "reason": "一句话理由"}
```

### 5.4 LLM 调用策略
- 批量处理（每次 10-20 条），降低 API 调用次数
- 使用 DeepSeek API（已有 key），单条成本约 0.001 元
- 重试：失败重试 2 次，间隔 5 秒
- 幂等：同一 url 只处理一次（`ai_processed = true` 标记）

---

## 6. 技术栈

| 层 | 选型 | 理由 |
|---|---|---|
| 后端框架 | Python FastAPI | 轻量、async、自动生成 OpenAPI |
| ORM | SQLAlchemy + SQLite | 初期数据量小，零运维；后期可迁 PG |
| 任务调度 | APScheduler / cron | 定时采集 + 日报生成 |
| RSS 解析 | feedparser | Python 标准 RSS 库 |
| HTTP 客户端 | httpx / aiohttp | 异步抓取 |
| LLM | DeepSeek API（已有 key） | 低成本、中文好 |
| Web 服务器 | Nginx + proxy_cache | 缓存加速 |
| Agent 集成 | SKILL.md | LLM Agent 说明书 |

---

## 7. 目录结构

```
yibao-news/
├── server/
│   ├── main.py              # FastAPI 入口
│   ├── models.py            # SQLAlchemy 模型
│   ├── api/
│   │   ├── items.py         # /api/public/items
│   │   ├── daily.py         # /api/public/daily
│   │   └── sources.py       # /api/public/sources
│   ├── pipeline/
│   │   ├── fetch.py         # RSS/网页采集
│   │   ├── dedup.py         # 去重
│   │   ├── score.py         # AI 评分
│   │   ├── summarize.py     # AI 摘要
│   │   ├── classify.py      # AI 分类+标签
│   │   └── daily_gen.py     # 日报生成
│   └── config.py            # 配置
├── cron/
│   ├── fetch.sh             # 采集定时任务
│   ├── process.sh           # AI 处理定时任务
│   └── daily.sh             # 日报生成定时任务
├── skills/
│   └── SKILL.md             # Agent Skill 说明书
├── requirements.txt
├── openapi.yaml             # OpenAPI 3.1 规范
└── SPEC.md                  # 本文件
```

---

## 8. 实施阶段

### Phase 1：MVP（第 1 周）
- [ ] 搭建 FastAPI + SQLite 骨架
- [ ] 接入 3-5 个 RSS 源
- [ ] 实现 `/api/public/items` 基础查询
- [ ] 写 AI 评分 Prompt，验证效果

### Phase 2：AI 管线（第 2 周）
- [ ] AI 摘要 + 分类 + 标签
- [ ] 精选筛选逻辑
- [ ] 日报自动生成
- [ ] 完善 API（daily/dailies 端点）

### Phase 3：上线（第 3 周）
- [ ] Nginx 配置 + proxy_cache
- [ ] 部署到 VPS
- [ ] 编写 SKILL.md Agent 集成
- [ ] 接入 Hermes/Claude Code 测试

### Phase 4：迭代
- [ ] 增加更多数据源
- [ ] 网页抓取（无 RSS 的源）
- [ ] 数据看板（可选）
- [ ] 用户反馈机制

---

## 9. 与 AI HOT 的关键差异

| | AI HOT | 医保 HOT |
|---|---|---|
| 领域 | AI/大模型 | 医保政策 |
| 分类 | 模型/产品/行业/论文/技巧 | 政策/集采/DRG/基金/服务/行业/观点 |
| 精选标准 | 技术重要性、行业影响 | 政策影响力、民生相关性 |
| 用户 | AI 从业者/投资人 | 医保从业者、医疗机构、公众 |
| 日报格式 | 5 版块 | 7 版块 |
| 信源 | 科技媒体、arXiv | 政府网站、行业媒体 |
