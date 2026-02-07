from fastapi import FastAPI
from src.api.routes import router
from src.api.dependencies import get_config, get_db_manager, get_queue_service
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    config = get_config()
    db_manager = get_db_manager()
    
    from src.infrastructure.database.models import Base
    async with db_manager.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    queue_service = get_queue_service()
    await queue_service.start()
    
    yield
    
    await queue_service.stop()
    await db_manager.close()

app = FastAPI(title="Quant Data System", lifespan=lifespan)
app.include_router(router, prefix="/api/v1", tags=["scraper"])
