from fastapi import FastAPI
from app.api.routes import api_router
from app.core.db import init_db
from app.core.utils import logger

app = FastAPI(title="Daemonology RAG API", version="1.0")

app.include_router(api_router, prefix="")

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Daemonology RAG API...")
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

