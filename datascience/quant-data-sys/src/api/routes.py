from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from src.dto.scraper_dto import ScrapeRequest, ScrapeResult
from src.api.dependencies import (
    get_db_session,
    get_scraper_service,
    get_spider_service
)
from src.services.scraper_service import ScraperService
from src.services.spider_service import SpiderService
from src.services.repository_service import RepositoryService

router = APIRouter()


@router.post("/scrape", response_model=ScrapeResult)
async def scrape_url(
    request: ScrapeRequest,
    scraper_service: ScraperService = Depends(get_scraper_service),
    session: AsyncSession = Depends(get_db_session)
):
    """Scrape URL synchronously"""
    try:
        result = await scraper_service.scrape(request)
        
        repo = RepositoryService(session)
        job_id = await repo.create_scrape_job(request.url)
        await repo.update_job_status(job_id, "started")
        try:
            await repo.save_scrape_result(job_id, result)
            await repo.update_job_status(job_id, "completed")
            await repo.commit()
        except Exception as e:
            await repo.update_job_status(job_id, "failed", str(e))
            await repo.rollback()
            raise
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/spider/enqueue", response_model=dict)
async def enqueue_url(
    request: ScrapeRequest
):
    """Enqueue URL for spider processing"""
    try:
        spider_service = get_spider_service()
        await spider_service.start()
        success = await spider_service.enqueue_url(request.url)
        
        if success:
            return {"status": "enqueued", "url": request.url}
        else:
            return {"status": "skipped", "url": request.url, "reason": "already processed or invalid"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/spider/stats", response_model=dict)
async def get_spider_stats():
    """Get spider queue statistics"""
    try:
        spider_service = get_spider_service()
        stats = await spider_service.get_queue_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
