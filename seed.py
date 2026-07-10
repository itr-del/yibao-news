"""
Seed 脚本 — 预填充真实国家医保局数据到空数据库
用于开发/测试时快速看到效果，无需等待采集管线
"""
import sys
import os
import json
import datetime
import logging
import uuid

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "server"))

from models import Item, Daily, init_db, get_session


def seed_items(session):
    """Fill the database with real NHSA data (same as yibao-hub v2)."""
    existing = session.query(Item).count()
    if existing > 0:
        print(f"DB already has {existing} items — skipping seed")
        return existing

    BASE = "https://www.nhsa.gov.cn"

    NEWS = [
        # y1 — 医保服务
        {"title": "刷脸、扫码，3分钟搞定", "url": f"{BASE}/art/2026/6/4/art_14_20846.html",
         "source_id": "nhsa-gov", "source_name": "国家医保局", "source_kind": "scraper",
         "category": "service", "ai_relevance": 85, "quality_score": 72,
         "final_score": 85, "ai_selected": True,
         "ai_selected_reason": "便捷就医服务直接影响群众体验",
         "ai_processed": True, "published_at": datetime.datetime(2026, 6, 4),
         "summary_zh": "国家医保局推出便捷服务，通过刷脸和扫码实现快速就医结算，大幅简化异地就医流程。"},

        # y2 — 智慧医保
        {"title": "云南医保和您一起比药价", "url": f"{BASE}/art/2026/6/3/art_14_20844.html",
         "source_id": "nhsa-gov", "source_name": "云南医保", "source_kind": "scraper",
         "category": "service", "ai_relevance": 78, "quality_score": 70,
         "final_score": 78, "ai_selected": True,
         "ai_selected_reason": "医保价格透明化改革举措",
         "ai_processed": True, "published_at": datetime.datetime(2026, 6, 3),
         "summary_zh": "云南省医保局推广药店比价小程序，让参保人能够便捷比较药店价格，降低购药成本。"},

        # y3 — DRG/DIP
        {"title": "医保支付方式改革有关情况介绍（第2期）", "url": f"{BASE}/art/2026/6/3/art_14_20842.html",
         "source_id": "nhsa-gov", "source_name": "国家医保局", "source_kind": "scraper",
         "category": "drg-dip", "ai_relevance": 92, "quality_score": 88,
         "final_score": 92, "ai_selected": True,
         "ai_selected_reason": "支付方式改革核心政策解读，影响深远",
         "ai_processed": True, "published_at": datetime.datetime(2026, 6, 3),
         "summary_zh": "国家医保局继续推进DRG/DIP支付方式改革，介绍改革进展和下一步计划。"},

        # y4 — 长期护理/服务
        {"title": '"失能不失爱 保障有温度" 徐州长护经办的承诺', "url": f"{BASE}/art/2026/6/3/art_14_20840.html",
         "source_id": "nhsa-gov", "source_name": "徐州医保", "source_kind": "scraper",
         "category": "service", "ai_relevance": 70, "quality_score": 68,
         "final_score": 70, "ai_selected": True,
         "ai_selected_reason": "长护险便民服务典型经验",
         "ai_processed": True, "published_at": datetime.datetime(2026, 6, 3),
         "summary_zh": "徐州市长期护理保险经办机构介绍长护险服务，为失能人员提供有温度的保障服务。"},

        # y5 — 政策
        {"title": "清算提速见实效：2025年度清算5月底前圆满完成", "url": f"{BASE}/art/2026/6/2/art_14_20838.html",
         "source_id": "nhsa-gov", "source_name": "国家医保局", "source_kind": "scraper",
         "category": "policy", "ai_relevance": 75, "quality_score": 72,
         "final_score": 75, "ai_selected": True,
         "ai_selected_reason": "医保结算效率提升的重要进展",
         "ai_processed": True, "published_at": datetime.datetime(2026, 6, 2),
         "summary_zh": "全国医保结算清算工作提速，154个统筹地区在3天内完成清算，效率显著提升。"},

        # y6 — 基金监管
        {"title": "深入开展医保基金专项整治 严厉打击违法违规使用医保基金行为", "url": f"{BASE}/art/2026/6/2/art_14_20829.html",
         "source_id": "nhsa-gov", "source_name": "国家医保局", "source_kind": "scraper",
         "category": "fund", "ai_relevance": 90, "quality_score": 85,
         "final_score": 90, "ai_selected": True,
         "ai_selected_reason": "基金监管专项整治，关乎基金安全",
         "ai_processed": True, "published_at": datetime.datetime(2026, 6, 2),
         "summary_zh": "国家医保局部署专项整治行动，严厉打击骗保、虚假住院、过度诊疗等违法违规行为。"},

        # y7 — 基金监管
        {"title": "专项行动典型案例第三期：定点零售药店违法违规使用医保基金问题", "url": f"{BASE}/art/2026/5/31/art_14_20818.html",
         "source_id": "nhsa-gov", "source_name": "国家医保局", "source_kind": "scraper",
         "category": "fund", "ai_relevance": 82, "quality_score": 78,
         "final_score": 82, "ai_selected": True,
         "ai_selected_reason": "典型案例通报具有警示作用",
         "ai_processed": True, "published_at": datetime.datetime(2026, 5, 31),
         "summary_zh": "国家医保局公布第三批次典型案例，重点揭示定点零售药店在医保基金使用中的各类违规问题。"},

        # y8 — 药品目录
        {"title": "国家医保局发布《2026年国家基本医疗保险、生育保险药品目录调整公告》", "url": f"{BASE}/art/2026/5/31/art_109_20816.html",
         "source_id": "nhsa-gov", "source_name": "国家医保局", "source_kind": "scraper",
         "category": "drugs", "ai_relevance": 95, "quality_score": 92,
         "final_score": 95, "ai_selected": True,
         "ai_selected_reason": "年度药品目录调整是最核心政策",
         "ai_processed": True, "published_at": datetime.datetime(2026, 5, 31),
         "summary_zh": "国家医保局正式发布2026年版医保药品目录，纳入更多慢性病、罕见病用药。"},

        # y9 — 药品目录
        {"title": "关于2026年第二批参照药预沟通增补药品信息的公示", "url": f"{BASE}/art/2026/5/27/art_109_20821.html",
         "source_id": "nhsa-gov", "source_name": "国家医保局", "source_kind": "scraper",
         "category": "drugs", "ai_relevance": 76, "quality_score": 70,
         "final_score": 76, "ai_selected": True,
         "ai_selected_reason": "药品目录调整重要环节",
         "ai_processed": True, "published_at": datetime.datetime(2026, 5, 27),
         "summary_zh": "国家医保局公示第二批参照药预沟通增补药品信息，涉及多种慢性病用药。"},

        # y10 — 基金监管
        {"title": "关于印发《医疗保障基金监督检查五年行动计划（2026年—2030年）》的通知", "url": f"{BASE}/art/2026/5/13/art_104_20494.html",
         "source_id": "nhsa-gov", "source_name": "国家医保局", "source_kind": "scraper",
         "category": "fund", "ai_relevance": 93, "quality_score": 90,
         "final_score": 93, "ai_selected": True,
         "ai_selected_reason": "五年计划级基金监管顶层设计",
         "ai_processed": True, "published_at": datetime.datetime(2026, 5, 13),
         "summary_zh": "发布基金监管五年行动计划，强化医保基金使用全流程监管，维护基金安全。"},

        # y11 — 基金监管
        {"title": "关于进一步加强定点零售药店职工医保个人账户使用监督管理的通知", "url": f"{BASE}/art/2026/5/19/art_104_20545.html",
         "source_id": "nhsa-gov", "source_name": "国家医保局", "source_kind": "scraper",
         "category": "fund", "ai_relevance": 78, "quality_score": 75,
         "final_score": 78, "ai_selected": True,
         "ai_selected_reason": "两部门联合发文，药店账户监管",
         "ai_processed": True, "published_at": datetime.datetime(2026, 5, 19),
         "summary_zh": "两部门联合发文，规范定点药店职工医保个人账户资金使用，防范医保基金流失。"},

        # y12 — 药品集采
        {"title": "国家药品监督管理局等七部门联合发布《医药代表管理办法》", "url": f"{BASE}/art/2026/5/15/art_104_20513.html",
         "source_id": "nhsa-gov", "source_name": "国家药监局", "source_kind": "scraper",
         "category": "drugs", "ai_relevance": 72, "quality_score": 70,
         "final_score": 72, "ai_selected": True,
         "ai_selected_reason": "七部门联合规范医药代表行为",
         "ai_processed": True, "published_at": datetime.datetime(2026, 5, 15),
         "summary_zh": "七部门联合发布医药代表管理办法，规范医药代表学术推广行为，防范商业贿赂。"},

        # y13 — 智慧医保
        {"title": "国家医保局邀请您参加药店药价大家谈活动", "url": f"{BASE}/art/2026/6/2/art_109_20837.html",
         "source_id": "nhsa-gov", "source_name": "国家医保局", "source_kind": "scraper",
         "category": "service", "ai_relevance": 65, "quality_score": 60,
         "final_score": 65, "ai_selected": True,
         "ai_selected_reason": "推广比价小程序助力价格透明",
         "ai_processed": True, "published_at": datetime.datetime(2026, 6, 2),
         "summary_zh": "国家医保局推出药店比价小程序推广活动，鼓励参保人使用比价工具降低购药支出。"},

        # y14 — 智慧医保
        {"title": "国家医保局关于公开发布第十三批智能监管两库规则", "url": f"{BASE}/art/2026/6/1/art_109_20822.html",
         "source_id": "nhsa-gov", "source_name": "国家医保局", "source_kind": "scraper",
         "category": "industry", "ai_relevance": 74, "quality_score": 70,
         "final_score": 74, "ai_selected": True,
         "ai_selected_reason": "AI智能监管规则持续完善",
         "ai_processed": True, "published_at": datetime.datetime(2026, 6, 1),
         "summary_zh": "发布第十三批智能监管规则库和知识库，利用AI技术提升医保基金使用监管智能化水平。"},

        # y15 — DRG/DIP
        {"title": "医保支付方式改革有关情况介绍（第1期）", "url": f"{BASE}/art/2026/5/30/art_14_20799.html",
         "source_id": "nhsa-gov", "source_name": "国家医保局", "source_kind": "scraper",
         "category": "drg-dip", "ai_relevance": 88, "quality_score": 85,
         "final_score": 88, "ai_selected": True,
         "ai_selected_reason": "支付方式改革系统解读",
         "ai_processed": True, "published_at": datetime.datetime(2026, 5, 30),
         "summary_zh": "国家医保局系统介绍DRG/DIP支付方式改革背景、进展和成效，解读改革方案。"},

        # y16 — 智慧医保
        {"title": "养成新习惯，别花冤枉钱——国家医保局建议用好药店比价小程序", "url": f"{BASE}/art/2026/5/30/art_14_20812.html",
         "source_id": "nhsa-gov", "source_name": "国家医保局", "source_kind": "scraper",
         "category": "service", "ai_relevance": 60, "quality_score": 55,
         "final_score": 60, "ai_selected": True,
         "ai_selected_reason": "消费提示，引导使用比价工具",
         "ai_processed": True, "published_at": datetime.datetime(2026, 5, 30),
         "summary_zh": "国家医保局发布消费提示，建议参保群众使用药店比价小程序，理性选择购药渠道。"},

        # y17 — 政策/统计
        {"title": "2026年1-4月基本医疗保险统筹基金和生育保险主要指标", "url": f"{BASE}/art/2026/5/25/art_7_20702.html",
         "source_id": "nhsa-gov", "source_name": "国家医保局", "source_kind": "scraper",
         "category": "policy", "ai_relevance": 91, "quality_score": 88,
         "final_score": 91, "ai_selected": True,
         "ai_selected_reason": "官方统计数据，基金运行核心指标",
         "ai_processed": True, "published_at": datetime.datetime(2026, 5, 25),
         "summary_zh": "国家医保局发布2026年1-4月全国医保基金运行数据，包括收入、支出、结余等关键指标。"},

        # y18 — 药品目录
        {"title": "关于改革完善儿童用药供应保障机制的实施意见", "url": f"{BASE}/art/2026/5/15/art_104_20517.html",
         "source_id": "nhsa-gov", "source_name": "国家医保局", "source_kind": "scraper",
         "category": "drugs", "ai_relevance": 73, "quality_score": 70,
         "final_score": 73, "ai_selected": True,
         "ai_selected_reason": "儿童用药保障政策",
         "ai_processed": True, "published_at": datetime.datetime(2026, 5, 15),
         "summary_zh": "多部门联合发布儿童用药供应保障机制，确保儿童用药可及性和安全性。"},

        # y19 — 基金监管
        {"title": "针对销售回流药问题 乌鲁木齐取消违规药店医保定点服务资格", "url": f"{BASE}/art/2026/5/29/art_14_20805.html",
         "source_id": "nhsa-gov", "source_name": "乌鲁木齐医保", "source_kind": "scraper",
         "category": "fund", "ai_relevance": 76, "quality_score": 72,
         "final_score": 76, "ai_selected": True,
         "ai_selected_reason": "地方违规查处典型案例",
         "ai_processed": True, "published_at": datetime.datetime(2026, 5, 29),
         "summary_zh": "乌鲁木齐市对违规销售回流药的药店采取取消医保定点资格措施，维护医保基金安全。"},

        # y20 — 智慧医保
        {"title": "四川医保和您一起比药价", "url": f"{BASE}/art/2026/6/1/art_14_20826.html",
         "source_id": "nhsa-gov", "source_name": "四川医保", "source_kind": "scraper",
         "category": "service", "ai_relevance": 68, "quality_score": 65,
         "final_score": 68, "ai_selected": True,
         "ai_selected_reason": "跨省协同推进价格透明",
         "ai_processed": True, "published_at": datetime.datetime(2026, 6, 1),
         "summary_zh": "四川省推广药店比价小程序，与云南等省份协同推进医保价格透明化。"},
    ]

    for i, n in enumerate(NEWS):
        item = Item(
            id=f"yb_{uuid.uuid4().hex[:16]}",
            url=n["url"],
            title=n["title"],
            title_zh=n["title"],
            summary_zh=n["summary_zh"],
            source_id=n["source_id"],
            source_name=n["source_name"],
            source_kind=n["source_kind"],
            published_at=n["published_at"],
            fetched_at=datetime.datetime.utcnow(),
            category=n["category"],
            tags=json.dumps([n["category"], n["source_name"][:4]], ensure_ascii=False),
            ai_relevance=n["ai_relevance"],
            quality_score=n["quality_score"],
            final_score=n["final_score"],
            ai_selected=n["ai_selected"],
            ai_selected_reason=n["ai_selected_reason"],
            ai_processed=True,
            ai_processed_at=datetime.datetime.utcnow(),
        )
        session.add(item)

    session.commit()
    print(f"✅ Seeded {len(NEWS)} items")
    return len(NEWS)


def seed_daily(session):
    """Generate daily reports from seeded items, grouping by UTC date."""
    from models import Daily
    from config import CATEGORIES
    import json
    import datetime

    existing = session.query(Daily).count()

    # Group selected items by date
    items = session.query(Item).filter(
        Item.ai_selected == True,
        Item.duplicate_of_id.is_(None),
    ).order_by(Item.published_at.desc()).all()

    # Group by date (UTC)
    from collections import defaultdict
    by_date = defaultdict(list)
    for item in items:
        day = item.published_at.strftime("%Y-%m-%d")
        by_date[day].append(item)

    created = 0
    for date_str in sorted(by_date.keys(), reverse=True):
        day_items = by_date[date_str]
        if len(day_items) < 3:
            continue

        # Group by category
        sections_map = defaultdict(list)
        for item in day_items:
            cat = item.category or "industry"
            sections_map[cat].append(item)

        sections = []
        for cat_slug in ["policy", "drugs", "drg-dip", "fund", "service", "industry", "opinion"]:
            if cat_slug in sections_map:
                sections.append({
                    "label": CATEGORIES.get(cat_slug, cat_slug),
                    "items": [i.id for i in sections_map[cat_slug]],
                })

        daily = Daily(
            date=date_str,
            generated_at=datetime.datetime.utcnow(),
            lead_title=day_items[0].title,
            lead_summary=day_items[0].summary_zh or "",
            sections_json=json.dumps(sections, ensure_ascii=False),
            flashes_json=json.dumps([i.title[:80] for i in day_items[1:6]], ensure_ascii=False),
        )
        session.add(daily)
        created += 1

    session.commit()
    print(f"✅ Generated {created} dailies")


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
    init_db()
    session = get_session()
    try:
        count = seed_items(session)
        if count > 0:
            seed_daily(session)
    finally:
        session.close()
