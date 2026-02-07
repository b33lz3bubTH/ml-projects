from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.dto.scraper_dto import ScrapeRequest, ScrapeResult
from src.api.dependencies import (
    get_db_session,
    get_scraper_service,
    get_spider_service
)
from src.core.relevance.news_sources import get_default_news_sources
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
        repo = RepositoryService(session)
        job_id = await repo.create_scrape_job(request.url)
        await repo.update_job_status(job_id, "started")
        try:
            result = await scraper_service.scrape(request)
            await repo.save_scrape_result(job_id, result)
            await repo.update_job_status(job_id, "completed")
            job = await repo.get_scrape_job(job_id)
            await repo.commit()
            if job:
                result.job_created_at = job.created_at
                result.job_processed_at = job.completed_at
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


@router.post("/spider/seed-sources", response_model=dict)
async def seed_best_sources():
    """Seed spider with best news sources and official press release feeds."""
    try:
        spider_service = get_spider_service()
        await spider_service.start()

        sources = get_default_news_sources()
        results = []
        enqueued = 0
        skipped = 0

        for source in sources:
            success = await spider_service.enqueue_url(source.seed_url, priority=source.priority)
            results.append(
                {
                    "source": source.name,
                    "url": source.seed_url,
                    "priority": source.priority,
                    "status": "enqueued" if success else "skipped"
                }
            )
            if success:
                enqueued += 1
            else:
                skipped += 1

        return {
            "status": "completed",
            "enqueued": enqueued,
            "skipped": skipped,
            "sources": results
        }
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
