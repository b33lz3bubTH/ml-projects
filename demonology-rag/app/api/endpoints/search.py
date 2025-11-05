from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.core.index import load_index
from app.core.utils import logger

router = APIRouter()


class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5


@router.post("/search")
async def search_vector_db(request: SearchRequest):
    """Search vector database and return raw results without LLM processing."""
    try:
        logger.info(f"Vector search for query: {request.query}")
        index = load_index(require_llm=False)
        
        # Use retriever instead of query engine to get raw results
        retriever = index.as_retriever(similarity_top_k=request.top_k)
        nodes = retriever.retrieve(request.query)
        
        results = []
        for i, node in enumerate(nodes):
            node_data: Dict[str, Any] = {
                "rank": i + 1,
                "score": getattr(node, 'score', None),
                "text": node.text if hasattr(node, 'text') else str(node),
            }
            
            # Extract metadata
            if hasattr(node, 'node') and hasattr(node.node, 'metadata'):
                metadata = node.node.metadata
                node_data["metadata"] = {
                    "file_name": metadata.get('file_name', 'Unknown'),
                    "page_label": metadata.get('page_label', ''),
                    "file_path": metadata.get('file_path', ''),
                    "file_type": metadata.get('file_type', ''),
                    **{k: v for k, v in metadata.items() if k not in ['file_name', 'page_label', 'file_path', 'file_type']}
                }
            elif hasattr(node, 'metadata'):
                node_data["metadata"] = node.metadata
            else:
                node_data["metadata"] = {}
            
            results.append(node_data)
        
        return {
            "query": request.query,
            "top_k": request.top_k,
            "results_count": len(results),
            "results": results
        }
    except Exception as e:
        logger.error(f"Error during vector search: {e}")
        raise HTTPException(status_code=500, detail=f"Error during vector search: {str(e)}")

