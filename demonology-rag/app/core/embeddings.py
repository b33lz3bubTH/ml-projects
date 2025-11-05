from llama_index.embeddings.openai import OpenAIEmbedding
from app.core.config import settings
from app.core.utils import logger


def get_embedding_model():
    """Get embedding model based on configuration."""
    if settings.OPENROUTER_API_KEY:
        logger.info(f"Using OpenRouter for embeddings with model: {settings.EMBEDDING_MODEL}")
        return OpenAIEmbedding(
            api_key=settings.OPENROUTER_API_KEY,
            model=settings.EMBEDDING_MODEL,
            api_base="https://openrouter.ai/api/v1",
            additional_headers={
                "HTTP-Referer": "https://github.com/demonology-rag",
                "X-Title": "Daemonology RAG API"
            }
        )
    elif settings.OPENAI_API_KEY:
        logger.info(f"Using OpenAI for embeddings with model: {settings.EMBEDDING_MODEL}")
        return OpenAIEmbedding(
            api_key=settings.OPENAI_API_KEY,
            model=settings.EMBEDDING_MODEL
        )
    else:
        raise ValueError("Either OPENROUTER_API_KEY or OPENAI_API_KEY must be set in environment")

