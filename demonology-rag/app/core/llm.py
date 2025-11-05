from llama_index.llms.openai import OpenAI
from app.core.config import settings
from app.core.utils import logger


def get_llm():
    """Get LLM model based on configuration."""
    if settings.OPENROUTER_API_KEY:
        logger.info(f"Using OpenRouter with model: {settings.LLM_MODEL}")
        # Use OpenAI class with OpenRouter endpoint - bypass model validation
        llm = OpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            api_base="https://openrouter.ai/api/v1",
            temperature=0.1,
            additional_headers={
                "HTTP-Referer": "https://github.com/demonology-rag",
                "X-Title": "Daemonology RAG API"
            }
        )
        # Set model directly to bypass validation
        llm.model = settings.LLM_MODEL
        return llm
    elif settings.OPENAI_API_KEY:
        logger.info("Using OpenAI with model: gpt-3.5-turbo")
        return OpenAI(
            api_key=settings.OPENAI_API_KEY,
            model="gpt-3.5-turbo",
            temperature=0.1
        )
    else:
        raise ValueError("Either OPENROUTER_API_KEY or OPENAI_API_KEY must be set in environment")

