from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
from src.infrastructure.database.models import (
    ScrapeJob, ScrapeResult, MetaTag, ImageUrl, JsonLdBlock, ArticleLink
)
from src.dto.scraper_dto import ScrapeResult as ScrapeResultDTO
from datetime import datetime

logger = logging.getLogger(__name__)


class RepositoryService:
    """Repository service for database operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_scrape_job(self, url: str) -> int:
        """Create scrape job and return ID"""
        job = ScrapeJob(
            url=url,
            status="pending",
            created_at=datetime.utcnow()
        )
        self.session.add(job)
        await self.session.flush()
        await self.session.refresh(job)
        return job.id
    
    async def update_job_status(
        self,
        job_id: int,
        status: str,
        error_message: Optional[str] = None
    ):
        """Update job status"""
        try:
            job = await self.session.get(ScrapeJob, job_id)
            if job:
                job.status = status
                if status == "started":
                    job.started_at = datetime.utcnow()
                elif status in ["completed", "failed"]:
                    job.completed_at = datetime.utcnow()
                if error_message:
                    job.error_message = error_message[:1000]
                await self.session.flush()
        except Exception as e:
            logger.error(f"[REPO] Error updating job status: {e}")
            await self.session.rollback()
            raise
    
    async def save_scrape_result(
        self,
        job_id: Optional[int],
        result: ScrapeResultDTO
    ) -> int:
        """Save scrape result and return ID"""
        db_result = ScrapeResult(
            job_id=job_id,
            url=result.url,
            html=result.html,
            cleaned_html=result.cleaned_html,
            debug_ref=result.debug_ref,
            debug_html_path=result.debug_html_path,
            debug_json_path=result.debug_json_path,
            created_at=datetime.utcnow()
        )
        self.session.add(db_result)
        await self.session.flush()
        await self.session.refresh(db_result)
        result_id = db_result.id
        
        for key, value in result.meta_tags.items():
            meta = MetaTag(
                result_id=result_id,
                key=key,
                value=value,
                created_at=datetime.utcnow()
            )
            self.session.add(meta)
        
        for image_url in result.images:
            if len(image_url) > 2048:
                logger.warning(f"[REPO] Image URL too long ({len(image_url)} chars), truncating: {image_url[:100]}...")
                image_url = image_url[:2048]
            image = ImageUrl(
                result_id=result_id,
                url=image_url,
                created_at=datetime.utcnow()
            )
            self.session.add(image)
        
        for jsonld in result.json_ld_blocks:
            jsonld_block = JsonLdBlock(
                result_id=result_id,
                content=jsonld,
                created_at=datetime.utcnow()
            )
            self.session.add(jsonld_block)
        
        for article_link in result.article_links:
            link = ArticleLink(
                result_id=result_id,
                url=article_link,
                created_at=datetime.utcnow()
            )
            self.session.add(link)
        
        await self.session.flush()
        return result_id
    
    async def get_scrape_job(self, job_id: int) -> Optional[ScrapeJob]:
        """Get scrape job by ID"""
        return await self.session.get(ScrapeJob, job_id)
    
    async def get_scrape_result(self, result_id: int) -> Optional[ScrapeResult]:
        """Get scrape result by ID"""
        return await self.session.get(ScrapeResult, result_id)
    
    async def commit(self):
        """Commit transaction"""
        await self.session.commit()
    
    async def rollback(self):
        """Rollback transaction"""
        await self.session.rollback()
