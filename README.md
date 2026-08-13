# 🏥 yibao-news

> 医保新闻智能资讯采集系统

## ✨ 功能

- 📰 **多源采集**：国家医保局、地方医保局、权威媒体
- 🤖 **AI 摘要**：自动提炼新闻要点
- 🏷️ **智能分类**：政策法规 / 试点动态 / 数据发布 / 案例
- ⏰ **定时推送**：每日定时汇总推送到飞书
- 🔍 **关键词监控**：自定义关键词触发即时推送

## 🛠️ 技术栈

- Python + httpx
- PostgreSQL 存储
- APScheduler 调度
- 飞书 Webhook 推送

## 🚀 启动

```bash
git clone https://github.com/itr-del/yibao-news.git
cd yibao-news
pip install -r requirements.txt
python3 main.py
```

## 📁 项目结构

```
yibao-news/
├── crawlers/          # 各数据源爬虫
├── analyzer/          # AI 摘要/分类
├── scheduler/         # 定时任务
├── push/              # 飞书推送
└── main.py            # 入口
```

## ⚙️ 配置

环境变量：
- `FEISHU_WEBHOOK_URL` — 飞书群机器人 Webhook
- `DB_URL` — 数据库连接
- `KEYWORDS` — 监控关键词列表

## 📜 License

MIT

## 🙏 数据源

国家医疗保障局、各地医保局公开信息、新华网、人民网等权威媒体。
