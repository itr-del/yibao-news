"""
AI 处理管线：评分 + 摘要 + 分类 + 标签
批量处理，降低 API 调用成本
"""
import datetime
import json
import logging
import re
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from openai import OpenAI
from config import (
    LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, LLM_TIMEOUT,
    AI_BATCH_SIZE, SELECTED_SCORE_THRESHOLD, CATEGORIES,
)
from models import Item, get_session

logger = logging.getLogger("yibao.ai")

CATEGORY_LIST = "\n".join(f"  - {k}: {v}" for k, v in CATEGORIES.items())

SYSTEM_PROMPT = f"""你是医保政策分析专家。对以下医保相关新闻进行批量处理，返回 JSON 数组。

对每条新闻执行：
1. summaryZh: 生成 100-150 字中文摘要，突出政策要点
2. relevance: 医保相关性评分 (0-100)
   - 90-100: 直接涉及医保政策、支付改革、药品目录
   - 70-89: 间接相关(医改、药价、医保基金监管)
   - 50-69: 泛医疗健康领域
   - 0-49: 弱相关
3. quality: 内容质量评分 (0-100)
   - 90-100: 首发政策文件、官方解读
   - 70-89: 深度分析、行业研判
   - 50-69: 常规报道
   - 0-49: 标题党、软文
4. finalScore: 综合分 = max(relevance, quality)，但要调整：
   - 高相关+低质量 → 降 10 分
   - 低相关+高质量 → 降 10 分
5. category: 最匹配的分类 ({", ".join(CATEGORIES.keys())})
6. tags: 提取 1-5 个关键标签词 (人名、机构名、政策名、药名)
7. selectedReason: 如果 finalScore >= 60，用一句话解释入选理由(<=40字)；否则为 null

返回格式(纯 JSON 数组，不要 markdown 代码块):
[
  {{
    "index": 0,
    "summaryZh": "...",
    "relevance": 85,
    "quality": 78,
    "finalScore": 80,
    "category": "policy",
    "tags": ["国家医保局", "DRG改革"],
    "selectedReason": "首发的DRG支付改革文件，影响深远"
  }},
  ...
]
"""


def build_llm_client() -> OpenAI:
    return OpenAI(
        base_url=LLM_BASE_URL,
        api_key=LLM_API_KEY,
        timeout=LLM_TIMEOUT,
    )


def build_batch_messages(items: list[Item]) -> str:
    """Build a user message describing all items in a batch."""
    lines = []
    for i, item in enumerate(items):
        published = item.published_at.strftime("%Y-%m-%d %H:%M") if item.published_at else "unknown"
        lines.append(
            f"[{i}] 标题: {item.title}\n"
            f"    来源: {item.source_name}\n"
            f"    时间: {published}\n"
            f"    链接: {item.url}"
        )
    return "\n\n".join(lines)


def call_llm_with_retry(client: OpenAI, messages: list, max_retries: int = 2) -> str | None:
    """Call LLM with retry logic."""
    for attempt in range(max_retries + 1):
        try:
            resp = client.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
                temperature=0.2,
                max_tokens=4096,
            )
            content = resp.choices[0].message.content
            return content.strip() if content else None
        except Exception as e:
            logger.warning("LLM call attempt %d failed: %s", attempt + 1, e)
            if attempt < max_retries:
                time.sleep(3)
    return None


def extract_json(text: str) -> list | None:
    """Extract JSON array from LLM response, handling markdown code blocks."""
    # Try direct parse first
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        pass

    # Try to extract from markdown code block
    for pattern in [r'```(?:json)?\s*([\s\S]*?)\s*```', r'\[[\s\S]*\]']:
        match = re.search(pattern, text)
        if match:
            try:
                data = json.loads(match.group(1) if match.lastindex else match.group(0))
                if isinstance(data, list):
                    return data
            except json.JSONDecodeError:
                continue
    return None


def apply_ai_results(items: list[Item], results: list[dict], session) -> int:
    """Apply AI processing results to items. Returns count updated."""
    results_by_index = {r["index"]: r for r in results}
    updated = 0

    for i, item in enumerate(items):
        result = results_by_index.get(i)
        if not result:
            continue

        item.summary_zh = str(result.get("summaryZh", ""))[:500]
        item.ai_relevance = int(result.get("relevance", 0))
        item.quality_score = int(result.get("quality", 0))
        item.final_score = int(result.get("finalScore", 0))
        item.category = result.get("category")
        if item.category not in CATEGORIES:
            item.category = None

        tags = result.get("tags", [])
        item.tags = json.dumps(tags[:5], ensure_ascii=False) if tags else None

        item.ai_selected = item.final_score >= SELECTED_SCORE_THRESHOLD if item.final_score else False
        if item.ai_selected and result.get("selectedReason"):
            item.ai_selected_reason = str(result["selectedReason"])[:200]

        item.ai_processed = True
        item.ai_processed_at = datetime.datetime.utcnow()
        session.add(item)
        updated += 1

    session.commit()
    return updated


def process_unprocessed_items(session=None) -> int:
    """Process all unprocessed items through AI pipeline. Returns count processed."""
    if session is None:
        session = get_session()

    items = (
        session.query(Item)
        .filter(Item.ai_processed == False, Item.duplicate_of_id.is_(None))
        .order_by(Item.published_at.desc())
        .limit(AI_BATCH_SIZE * 3)  # Max 3 batches per run
        .all()
    )

    if not items:
        logger.info("No unprocessed items")
        return 0

    client = build_llm_client()
    total_updated = 0

    for batch_start in range(0, len(items), AI_BATCH_SIZE):
        batch = items[batch_start:batch_start + AI_BATCH_SIZE]
        user_msg = build_batch_messages(batch)

        logger.info("Processing batch of %d items", len(batch))
        result_text = call_llm_with_retry(client, [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ])

        if not result_text:
            logger.error("LLM returned empty response for batch")
            continue

        results = extract_json(result_text)
        if not results:
            logger.error("Failed to parse LLM response: %s", result_text[:300])
            continue

        updated = apply_ai_results(batch, results, session)
        total_updated += updated
        logger.info("Batch: updated %d/%d items", updated, len(batch))

    return total_updated


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
    s = get_session()
    count = process_unprocessed_items(s)
    print(f"AI processing: {count} items updated")
    s.close()
