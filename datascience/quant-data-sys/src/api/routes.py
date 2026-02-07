from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from src.dto.scraper_dto import ScrapeRequest, ScrapeResult
from src.api.dependencies import (
    get_db_session,
    get_scraper_service,
    get_queue_service
)
from src.services.scraper_service import ScraperService
from src.services.queue_service import ScraperQueueService
from src.services.repository_service import RepositoryService
from src.dto.queue_dto import QueueTaskDTO

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


@router.post("/scrape/async", response_model=dict)
async def scrape_url_async(
    request: ScrapeRequest,
    queue_service: ScraperQueueService = Depends(get_queue_service),
    session: AsyncSession = Depends(get_db_session)
):
    """Enqueue scrape task"""
    try:
        await queue_service.start()
        task_id = await queue_service.enqueue_scrape(request.url)
        
        repo = RepositoryService(session)
        job_id = await repo.create_scrape_job(request.url)
        await repo.commit()
        
        return {"task_id": task_id, "job_id": job_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/task/{task_id}", response_model=QueueTaskDTO)
async def get_task_status(
    task_id: str,
    queue_service: ScraperQueueService = Depends(get_queue_service)
):
    """Get task status"""
    task = queue_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
