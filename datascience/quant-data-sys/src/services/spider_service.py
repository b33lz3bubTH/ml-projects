from typing import Optional, List, Iterable, Tuple, Dict
import logging
import asyncio
from urllib.parse import urlparse
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy import select, update, and_
from sqlalchemy.exc import IntegrityError
from src.dto.scraper_dto import ScrapeRequest, ScrapeResult
from src.services.scraper_service import ScraperService
from src.services.repository_service import RepositoryService
from src.infrastructure.database.models import UrlQueue
from src.infrastructure.database.session import DatabaseManager
from src.core.queue.async_queue import AsyncQueue
from src.core.filters.filter_service import LinkFilterService
from src.core.relevance.article_priority import ArticlePriorityPolicy
from datetime import datetime

logger = logging.getLogger(__name__)


class SpiderService:
    """Spider service for crawling URLs with queue management"""
    
    def __init__(
        self,
        scraper_service: ScraperService,
        session_factory: async_sessionmaker,
        filter_service: Optional[LinkFilterService] = None,
        priority_policy: Optional[ArticlePriorityPolicy] = None,
        max_workers: int = 3,
        max_queue_size: int = 876,
        cooldown_seconds: float = 1.0
    ):
        self.scraper_service = scraper_service
        self.session_factory = session_factory
        self.filter_service = filter_service
        self.priority_policy = priority_policy
        self.max_workers = max_workers
        self.max_queue_size = max_queue_size
        self.cooldown_seconds = cooldown_seconds
        self.queue: Optional[AsyncQueue] = None
        self.running = False
        self._lock = asyncio.Lock()
    
    async def start(self):
        """Start spider workers"""
        async with self._lock:
            if self.running:
                logger.warning("[SPIDER] Already running")
                return
            
            self.running = True
            self.queue = AsyncQueue(
                worker_func=self._process_url,
                max_workers=self.max_workers,
                max_queue_size=self.max_queue_size
            )
            await self.queue.start()
            logger.info(f"[SPIDER] Started with {self.max_workers} workers, max queue: {self.max_queue_size}")
    
    async def stop(self):
        """Stop spider workers"""
        async with self._lock:
            if not self.running:
                return
            
            self.running = False
            if self.queue:
                await self.queue.stop()
            logger.info("[SPIDER] Stopped")
    
    async def _process_url(self, url: str) -> Optional[ScrapeResult]:
        """Process a single URL - uses its own session"""
        logger.info(f"[SPIDER] Processing URL: {url}")
        
        try:
            async with self.session_factory() as session:
                stmt = select(UrlQueue).where(UrlQueue.url == url)
                result = await session.execute(stmt)
                url_record = result.scalar_one_or_none()
                
                if not url_record:
                    logger.warning(f"[SPIDER] URL not found in queue: {url}")
                    return None
                
                if url_record.status == "done":
                    logger.info(f"[SPIDER] URL already done, skipping: {url}")
                    return None
                
                if url_record.processing_count <= -5:
                    logger.warning(f"[SPIDER] URL processing_count too low ({url_record.processing_count}), skipping: {url}")
                    return None
                
                logger.info(f"[SPIDER] URL status: {url_record.status}, processing_count: {url_record.processing_count}")
                
                url_record.status = "processing"
                url_record.last_processed_at = datetime.utcnow()
                await session.commit()
            
            await self._apply_cooldown()
            
            async with self.session_factory() as repo_session:
                repo = RepositoryService(repo_session)
                job_id = await repo.create_scrape_job(url)
                await repo.update_job_status(job_id, "started")
                
                try:
                    request = ScrapeRequest(url=url)
                    scrape_result = await self.scraper_service.scrape(request)

                    # Second layer: Check content filter
                    if self.filter_service and self.filter_service.should_exclude_content(url, scrape_result.html or ""):
                        logger.info(f"[SPIDER] Content excluded by filter, skipping: {url}")
                        await repo.update_job_status(job_id, "failed", "Excluded by content filter")
                        await repo_session.commit()
                        async with self.session_factory() as update_session:
                            stmt = update(UrlQueue).where(UrlQueue.url == url).values(
                                status="done",
                                processing_count=1,
                                error_message="Excluded by content filter",
                                last_processed_at=datetime.utcnow()
                            )
                            await update_session.execute(stmt)
                            await update_session.commit()
                        return None

                    result_id = await repo.save_scrape_result(job_id, scrape_result)
                    await repo.update_job_status(job_id, "completed")
                    await repo_session.commit()
                    
                    logger.info(f"[SPIDER] Successfully scraped URL: {url}, found {len(scrape_result.article_links)} article links")
                    
                    await self._enqueue_article_links(scrape_result.article_links, url)
                    
                    async with self.session_factory() as update_session:
                        stmt = update(UrlQueue).where(UrlQueue.url == url).values(
                            status="done",
                            processing_count=1,
                            error_message=None,
                            last_processed_at=datetime.utcnow()
                        )
                        await update_session.execute(stmt)
                        await update_session.commit()
                    
                    return scrape_result
                    
                except Exception as e:
                    try:
                        await repo_session.rollback()
                        await repo.update_job_status(job_id, "failed", str(e)[:500])
                        await repo_session.commit()
                    except Exception as rollback_error:
                        logger.error(f"[SPIDER] Failed to update job status: {rollback_error}")
                    logger.error(f"[SPIDER] Failed to save result for {url}: {e}")
                    raise
                
        except Exception as e:
            logger.error(f"[SPIDER] Error processing URL {url}: {e}", exc_info=True)
            
            try:
                async with self.session_factory() as error_session:
                    stmt = update(UrlQueue).where(UrlQueue.url == url).values(
                        processing_count=UrlQueue.processing_count - 1,
                        status="failed",
                        error_message=str(e)[:500],
                        last_processed_at=datetime.utcnow()
                    )
                    await error_session.execute(stmt)
                    await error_session.commit()
            except Exception as commit_error:
                logger.error(f"[SPIDER] Failed to update URL status: {commit_error}")
            
            return None
    
    async def _enqueue_article_links(self, article_links: set[str], source_url: str):
        """Enqueue article links with priority ordering"""
        if not article_links:
            logger.debug(f"[SPIDER] No article links to enqueue from {source_url}")
            return

        sorted_links = sorted(article_links)
        logger.info(f"[SPIDER] Enqueueing {len(sorted_links)} article links from {source_url}")
        links_with_priority = self._assign_priorities(sorted_links)
        ordered_links = self._interleave_links_by_domain(links_with_priority)
        
        enqueued_count = 0
        skipped_count = 0
        
        for link, priority in ordered_links:
            if not self.running:
                break
            
            try:
                queue_size = self.queue.queue.qsize() if self.queue else 0
            except Exception:
                queue_size = 0
            
            if queue_size >= self.max_queue_size:
                logger.warning(f"[SPIDER] Queue full ({self.max_queue_size}), stopping enqueue")
                break
            
            # First layer: Check URL filter
            if self.filter_service and self.filter_service.should_exclude_url(link):
                skipped_count += 1
                logger.debug(f"[SPIDER] URL excluded by filter: {link}")
                continue

            if self.priority_policy and self.priority_policy.should_exclude_url(link):
                skipped_count += 1
                logger.debug(f"[SPIDER] URL excluded by priority policy: {link}")
                continue
            
            try:
                async with self.session_factory() as session:
                    stmt = select(UrlQueue).where(UrlQueue.url == link)
                    result = await session.execute(stmt)
                    existing = result.scalar_one_or_none()
                    
                    if existing:
                        if existing.status == "done":
                            skipped_count += 1
                            continue
                        if existing.processing_count <= -5:
                            skipped_count += 1
                            continue
                        existing.status = "pending"
                        existing.priority = priority
                        await session.commit()
                    else:
                        try:
                            url_record = UrlQueue(
                                url=link,
                                processing_count=0,
                                status="pending",
                                priority=priority,
                                created_at=datetime.utcnow()
                            )
                            session.add(url_record)
                            await session.commit()
                        except IntegrityError:
                            await session.rollback()
                            skipped_count += 1
                            continue
                    
                    if self.queue:
                        await self.queue.enqueue(link, priority=priority)
                        enqueued_count += 1
                        logger.debug(f"[SPIDER] Enqueued: {link}")
                
            except IntegrityError:
                skipped_count += 1
                continue
            except Exception as e:
                logger.error(f"[SPIDER] Error enqueueing link {link}: {e}")
                continue
        
        logger.info(f"[SPIDER] Enqueued {enqueued_count} links, skipped {skipped_count} links")

    def _assign_priorities(self, links: Iterable[str]) -> List[Tuple[str, int]]:
        """Assign priorities to links using the policy when available."""
        links_with_priority: List[Tuple[str, int]] = []
        for link in links:
            priority = 0
            if self.priority_policy:
                priority = self.priority_policy.get_priority(link)
            links_with_priority.append((link, priority))
        return links_with_priority

    def _interleave_links_by_domain(
        self,
        links_with_priority: Iterable[Tuple[str, int]]
    ) -> List[Tuple[str, int]]:
        """Interleave links by domain within priority groups to avoid source starvation."""
        priority_groups: Dict[int, Dict[str, List[str]]] = {}

        for link, priority in links_with_priority:
            domain = urlparse(link).netloc or "unknown"
            priority_groups.setdefault(priority, {}).setdefault(domain, []).append(link)

        ordered: List[Tuple[str, int]] = []
        for priority in sorted(priority_groups.keys()):
            domain_map = priority_groups[priority]
            domains = sorted(domain_map.keys())
            domain_queues = {domain: list(urls) for domain, urls in domain_map.items()}

            while any(domain_queues.values()):
                for domain in domains:
                    if domain_queues[domain]:
                        ordered.append((domain_queues[domain].pop(0), priority))

        return ordered
    
    async def _apply_cooldown(self):
        """Apply cooldown between requests"""
        if self.cooldown_seconds > 0:
            await asyncio.sleep(self.cooldown_seconds)
    
    async def enqueue_url(self, url: str, priority: int = 0) -> bool:
        """Enqueue a URL for processing"""
        if not self.running:
            logger.warning("[SPIDER] Not running, cannot enqueue")
            return False
        
        # First layer: Check URL filter
        if self.filter_service and self.filter_service.should_exclude_url(url):
            logger.debug(f"[SPIDER] URL excluded by filter: {url}")
            return False

        if self.priority_policy and self.priority_policy.should_exclude_url(url):
            logger.debug(f"[SPIDER] URL excluded by priority policy: {url}")
            return False

        if priority == 0 and self.priority_policy:
            priority = self.priority_policy.get_priority(url)
        
        try:
            async with self.session_factory() as session:
                stmt = select(UrlQueue).where(UrlQueue.url == url)
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()
                
                if existing:
                    if existing.status == "done":
                        logger.info(f"[SPIDER] URL already done: {url}")
                        return False
                    if existing.processing_count <= -5:
                        logger.warning(f"[SPIDER] URL processing_count too low: {url}")
                        return False
                    existing.status = "pending"
                    existing.priority = priority
                    await session.commit()
                else:
                    try:
                        url_record = UrlQueue(
                            url=url,
                            processing_count=0,
                            status="pending",
                            priority=priority,
                            created_at=datetime.utcnow()
                        )
                        session.add(url_record)
                        await session.commit()
                    except IntegrityError:
                        await session.rollback()
                        logger.debug(f"[SPIDER] URL already exists (duplicate): {url}")
                        return False
                
                if self.queue:
                    await self.queue.enqueue(url, priority=priority)
                    logger.info(f"[SPIDER] Enqueued URL: {url} with priority {priority}")
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"[SPIDER] Error enqueueing URL {url}: {e}")
            return False
    
    async def get_queue_stats(self) -> dict:
        """Get queue statistics"""
        try:
            pending_stmt = select(UrlQueue).where(UrlQueue.status == "pending")
            processing_stmt = select(UrlQueue).where(UrlQueue.status == "processing")
            done_stmt = select(UrlQueue).where(UrlQueue.status == "done")
            failed_stmt = select(UrlQueue).where(UrlQueue.status == "failed")
            
            async with self.session_factory() as session:
                pending_result = await session.execute(pending_stmt)
                processing_result = await session.execute(processing_stmt)
                done_result = await session.execute(done_stmt)
                failed_result = await session.execute(failed_stmt)
                
                try:
                    queue_size = self.queue.queue.qsize() if self.queue else 0
                except Exception:
                    queue_size = 0
                
                return {
                    "pending": len(pending_result.all()),
                    "processing": len(processing_result.all()),
                    "done": len(done_result.all()),
                    "failed": len(failed_result.all()),
                    "queue_size": queue_size,
                    "max_queue_size": self.max_queue_size,
                    "workers": self.max_workers,
                    "running": self.running
                }
        except Exception as e:
            logger.error(f"[SPIDER] Error getting stats: {e}")
            return {}
