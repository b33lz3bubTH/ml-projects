from pathlib import Path
from llama_index.core import VectorStoreIndex, Settings, StorageContext
from llama_index.core.readers import SimpleDirectoryReader
from llama_index.vector_stores.postgres import PGVectorStore
from sqlalchemy import make_url
from app.core.config import settings
from app.core.embeddings import get_embedding_model
from app.core.llm import get_llm
from app.core.utils import logger


def create_index_from_directory(data_dir: str = None):
    """Create vector index from PDFs in data directory."""
    if data_dir is None:
        data_dir = settings.DATA_DIR
    
    data_path = Path(data_dir)
    if not data_path.exists():
        data_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created data directory: {data_path}")
    
    logger.info(f"Loading documents from {data_path}")
    reader = SimpleDirectoryReader(str(data_path))
    documents = reader.load_data()
    
    if not documents:
        logger.warning(f"No documents found in {data_path}")
        return None
    
    logger.info(f"Loaded {len(documents)} documents")
    
    try:
        embedding_model = get_embedding_model()
        Settings.embed_model = embedding_model
        llm = get_llm()
        Settings.llm = llm
    except Exception as e:
        logger.error(f"Error setting up models: {e}")
        raise
    
    db_url = make_url(settings.DATABASE_URL)
    
    vector_store = PGVectorStore.from_params(
        database=db_url.database,
        host=db_url.host or "localhost",
        password=db_url.password,
        port=db_url.port or 5432,
        user=db_url.username,
        table_name="documents",
        embed_dim=1536,
    )
    
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    
    logger.info("Creating vector index...")
    index = VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        show_progress=True
    )
    
    logger.info("Index created successfully")
    return index


def load_index(require_llm: bool = True):
    """Load existing index from PostgreSQL."""
    try:
        embedding_model = get_embedding_model()
        Settings.embed_model = embedding_model
        if require_llm:
            try:
                llm = get_llm()
                Settings.llm = llm
            except Exception as e:
                logger.warning(f"LLM setup failed (may be OK for vector-only operations): {e}")
                if require_llm:
                    raise
    except Exception as e:
        logger.error(f"Error setting up models: {e}")
        raise
    
    db_url = make_url(settings.DATABASE_URL)
    
    vector_store = PGVectorStore.from_params(
        database=db_url.database,
        host=db_url.host or "localhost",
        password=db_url.password,
        port=db_url.port or 5432,
        user=db_url.username,
        table_name="documents",
        embed_dim=1536,
    )
    
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store,
        storage_context=storage_context
    )
    
    return index

