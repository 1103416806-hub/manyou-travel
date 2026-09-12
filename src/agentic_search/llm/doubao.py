from langchain_openai import ChatOpenAI

from agentic_search.config import settings


def get_llm_pro() -> ChatOpenAI:
    return ChatOpenAI(
        base_url=settings.ARK_BASE_URL,
        api_key=settings.ARK_API_KEY,
        model=settings.DOUBAO_PRO_MODEL,
        temperature=0.1,
        max_tokens=4096,
    )


def get_llm_lite() -> ChatOpenAI:
    return ChatOpenAI(
        base_url=settings.ARK_BASE_URL,
        api_key=settings.ARK_API_KEY,
        model=settings.DOUBAO_LITE_MODEL,
        temperature=0.3,
        max_tokens=2048,
    )
