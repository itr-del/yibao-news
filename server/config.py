import os

# Server
HOST = os.getenv("YIBAO_HOST", "0.0.0.0")
PORT = int(os.getenv("YIBAO_PORT", "8700"))
DB_PATH = os.getenv("YIBAO_DB_PATH", "data/yibao.db")

# LLM (DeepSeek via OpenAI-compatible API)
LLM_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
LLM_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
LLM_MODEL = os.getenv("YIBAO_LLM_MODEL", "deepseek-chat")
LLM_TIMEOUT = int(os.getenv("YIBAO_LLM_TIMEOUT", "60"))

# Pipeline
FETCH_INTERVAL_MINUTES = int(os.getenv("YIBAO_FETCH_INTERVAL", "30"))
AI_BATCH_SIZE = int(os.getenv("YIBAO_AI_BATCH_SIZE", "10"))
SELECTED_SCORE_THRESHOLD = int(os.getenv("YIBAO_SELECTED_THRESHOLD", "60"))

# RSS Sources (configured with real NHSA URLs)
RSS_SOURCES: list[dict] = [
    {
        "id": "nhsa-gov",
        "name": "国家医保局",
        "kind": "scraper",
        "url": "http://www.nhsa.gov.cn/col/col14/index.html",
        "rss_url": None,
        "enabled": True,
    },
    {
        "id": "nhsa-policy",
        "name": "国家医保局-政策法规",
        "kind": "scraper",
        "url": "http://www.nhsa.gov.cn/col/col104/index.html",
        "rss_url": None,
        "enabled": True,
    },
    {
        "id": "nhsa-data",
        "name": "国家医保局-统计数据",
        "kind": "scraper",
        "url": "http://www.nhsa.gov.cn/col/col7/index.html",
        "rss_url": None,
        "enabled": True,
    },
    {
        "id": "xinhua-health",
        "name": "新华网健康",
        "kind": "scraper",
        "url": "http://www.news.cn/health",
        "rss_url": None,
        "enabled": True,
    },
    {
        "id": "health-insight",
        "name": "健康界",
        "kind": "scraper",
        "url": "https://www.cn-healthcare.com",
        "rss_url": None,
        "enabled": False,
    },
    {
        "id": "pharma-mofang",
        "name": "医药魔方",
        "kind": "scraper",
        "url": "https://www.pharmcube.com",
        "rss_url": None,
        "enabled": False,
    },
    {
        "id": "dingxiangyuan",
        "name": "丁香园",
        "kind": "scraper",
        "url": "https://www.dxy.cn",
        "rss_url": None,
        "enabled": False,
    },
]

CATEGORIES = {
    "policy": "政策法规",
    "drugs": "药品集采",
    "drg-dip": "DRG/DIP",
    "fund": "医保基金",
    "service": "医保服务",
    "industry": "行业动态",
    "opinion": "专家观点",
}

# Frontend category mapping (maps backend slug to frontend label)
CATEGORY_LABEL_MAP = {
    "policy": "医保政策",
    "drugs": "药品集采",
    "drg-dip": "DRG/DIP",
    "fund": "基金监管",
    "service": "医保服务",
    "industry": "行业动态",
    "opinion": "专家观点",
}
