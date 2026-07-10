---
name: yibao
description: 医保 HOT (yibao-news) 中文医保新闻资讯查询 Skill。当用户想知道"最近医保有什么新政策"、"医保日报"、"集采最新消息"、"DRG改革动态"、"医保基金监管"、"异地就医政策"、"药品目录调整"、"医保热点"、"医保新闻"、"今天医保圈有什么"等任何医保政策/行业资讯查询时使用。即使用户只说"医保圈"、"医保有啥新闻"，或者只是问"最近有什么政策"且上下文是医疗/医保/卫生领域，也应该触发本 Skill。Skill 会直接 curl 公开 REST API 拉数据并整理成中文 markdown 简报，不需要用户配置任何 API Key 或 MCP server。
---

# 医保 HOT Skill

让 Agent 用最自然的中文查询拿到医保领域最新动态。跨 Claude Code / Codex CLI / Cursor / Gemini CLI / OpenCode / Hermes 兼容。

线上 API：部署后提供

## 什么时候用

| 用户说 | 接口 |
|---|---|
| **默认（宽问题）**："最近医保有什么新政策"、"医保圈有什么" | `GET /api/public/items?mode=selected&since=<语义>` |
| **明确说"日报"**："医保日报"、"今天的日报" | `GET /api/public/daily` |
| **明确说"全部/完整"**："看下全部医保动态" | `GET /api/public/items?mode=all` |
| "昨天的医保日报"、"看下 5 月 6 号的日报" | `GET /api/public/daily/{YYYY-MM-DD}` |
| "最近几天日报" | `GET /api/public/dailies?take=N` |
| "集采最新消息"、"药品目录调整" | `GET /api/public/items?mode=selected&category=drugs` |
| "DRG 改革动态" | `GET /api/public/items?mode=selected&category=drg-dip` |
| "医保基金监管新闻" | `GET /api/public/items?mode=selected&category=fund` |
| "异地就医有什么新政策" | `GET /api/public/items?mode=selected&category=service&q=异地就医` |
| "国家医保局最近发布了什么" | `GET /api/public/items?q=国家医保局` |

## 分类

| slug | 中文名 | 说明 |
|---|---|---|
| `policy` | 政策法规 | 国家/地方医保新政策 |
| `drugs` | 药品集采 | 国采/省采、药品目录 |
| `drg-dip` | DRG/DIP | 支付方式改革 |
| `fund` | 医保基金 | 基金监管、骗保案例 |
| `service` | 医保服务 | 异地就医、门诊共济 |
| `industry` | 行业动态 | 商业医保、数字医疗 |
| `opinion` | 专家观点 | 解读、评论、研究 |

## 端点

| 端点 | 用途 | 参数 |
|---|---|---|
| `/api/public/items` | 条目列表 | `mode`, `category`, `q`, `since`, `take`, `cursor` |
| `/api/public/daily` | 最新日报 | 无 |
| `/api/public/daily/{YYYY-MM-DD}` | 指定日期日报 | path: `date` |
| `/api/public/dailies` | 日报归档 | `take` (1-180) |
| `/api/public/sources` | 数据源列表 | 无 |

约定：
- Base URL: `http://localhost:8700`（生产环境替换为实际域名）
- 鉴权：无（匿名）
- items 端点 `since` 默认 now-7d
- `take` 上限 100，翻页用 `cursor`

## 工作流

### 默认路径：拉精选（宽问题首选）

```bash
BASE="http://localhost:8700"

# 最近 7 天精选（默认）
curl -s "$BASE/api/public/items?mode=selected&take=50" | python3 -m json.tool

# 按分类筛选
curl -s "$BASE/api/public/items?mode=selected&category=drugs&take=30"

# 关键词搜索
curl -s "$BASE/api/public/items?q=国家医保局&take=20"
```

### 拉日报（用户明确说"日报"时）

```bash
curl -s "$BASE/api/public/daily"
```

### 回答用户的格式

把 API 返回的 items 整理成中文简报：

```markdown
**医保 HOT 精选（最近 7 天）**

**1. [标题]**
[AI 摘要] | 来源：[来源名] | [时间]
🔗 [链接]

**2. [标题]**
...
```
