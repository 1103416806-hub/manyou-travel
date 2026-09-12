from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ARK_API_KEY: str = ""
    ARK_BASE_URL: str = "https://ark.cn-beijing.volces.com/api/v3"
    DOUBAO_PRO_MODEL: str = "doubao-pro-32k"
    DOUBAO_LITE_MODEL: str = "doubao-lite-32k"

    TAVILY_API_KEY: str = ""
    BOCHA_API_KEY: str = ""

    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION: str = "agentic_search"
    QDRANT_API_KEY: str = ""

    RERANKER_API_URL: str = ""
    RERANKER_API_KEY: str = ""

    POSTGRES_DSN: str = "postgresql://postgres:postgres@localhost:5432/agentic_search"

    GITHUB_TOKEN: str = ""
    REDDIT_CLIENT_ID: str = ""
    REDDIT_CLIENT_SECRET: str = ""
    SEMANTIC_SCHOLAR_API_KEY: str = ""

    FEISHU_APP_ID: str = ""
    FEISHU_APP_SECRET: str = ""

    MAX_ITERATIONS: int = 5
    MAX_RETRIES: int = 2
    CONFIDENCE_THRESHOLD: float = 0.85
    REFLECTION_STOP_THRESHOLD: float = 0.7
    RERANK_TOP_K: int = 8
    RERANK_RRF_K: int = 60
    RERANK_CROSS_ENCODER_TOP_N: int = 30
    CANDIDATE_POOL_MAX: int = 300

    model_config = {"env_file": str(Path(__file__).parent.parent.parent.parent / ".env"), "extra": "ignore"}


settings = Settings()
