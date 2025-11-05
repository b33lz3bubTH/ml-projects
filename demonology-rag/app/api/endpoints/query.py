from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.index import load_index
from app.core.config import settings
from app.core.utils import logger

router = APIRouter()


class QueryRequest(BaseModel):
    query: str


@router.post("/query")
async def query_documents(request: QueryRequest):
    """Query indexed documents using LLM."""
    try:
        logger.info(f"Loading index for query: {request.query}")
        index = load_index()
        
        query_engine = index.as_query_engine()
        response = query_engine.query(request.query)
        
        sources = []
        if hasattr(response, 'source_nodes') and response.source_nodes:
            for node in response.source_nodes:
                if hasattr(node, 'node') and hasattr(node.node, 'metadata'):
                    metadata = node.node.metadata
                    source = metadata.get('file_name', 'Unknown')
                    page = metadata.get('page_label', '')
                    if page:
                        source += f" - page {page}"
                    sources.append(source)
        
        return {
            "answer": str(response),
            "sources": list(set(sources)) if sources else []
        }
    except Exception as e:
        logger.error(f"Error during query: {e}")
        raise HTTPException(status_code=500, detail=f"Error during query: {str(e)}")

