from sqlalchemy import Column, Integer, String, Text, DateTime, Index, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class ScrapeJob(Base):
    """Scrape job table - no cascading, loose coupling"""
    __tablename__ = "scrape_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(2048), nullable=False, index=True)
    status = Column(String(50), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    
    __table_args__ = (
        Index('idx_url_status', 'url', 'status'),
    )


class ScrapeResult(Base):
    """Scrape result table"""
    __tablename__ = "scrape_results"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, nullable=True)
    url = Column(String(2048), nullable=False, index=True)
    html = Column(Text, nullable=True)
    cleaned_html = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        Index('idx_job_id', 'job_id'),
        Index('idx_url_created', 'url', 'created_at'),
    )


class MetaTag(Base):
    """Meta tags table - normalized"""
    __tablename__ = "meta_tags"
    
    id = Column(Integer, primary_key=True, index=True)
    result_id = Column(Integer, nullable=True)
    key = Column(String(255), nullable=False, index=True)
    value = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        Index('idx_result_key', 'result_id', 'key'),
    )


class ImageUrl(Base):
    """Image URLs table - normalized"""
    __tablename__ = "image_urls"
    
    id = Column(Integer, primary_key=True, index=True)
    result_id = Column(Integer, nullable=True)
    url = Column(String(2048), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        Index('idx_result_url', 'result_id', 'url'),
        Index('idx_url_unique', 'url'),
    )


class JsonLdBlock(Base):
    """JSON-LD blocks table"""
    __tablename__ = "json_ld_blocks"
    
    id = Column(Integer, primary_key=True, index=True)
    result_id = Column(Integer, nullable=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        Index('idx_result_id', 'result_id'),
    )


class ArticleLink(Base):
    """Article links table - normalized"""
    __tablename__ = "article_links"
    
    id = Column(Integer, primary_key=True, index=True)
    result_id = Column(Integer, nullable=True)
    url = Column(String(2048), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        Index('idx_result_url', 'result_id', 'url'),
        Index('idx_url_unique', 'url'),
    )
