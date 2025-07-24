from sqlalchemy import Column, String, DateTime, Text, Boolean, Integer, ForeignKey
from app.models.types import GUID as UUID, JsonEncodedDict
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class DiscoveredURL(Base):
    __tablename__ = "discovered_urls"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID, ForeignKey("jobs.id"), nullable=False, index=True)
    
    # URL information
    url = Column(String, nullable=False, index=True)
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    
    # Discovery metadata
    discovery_method = Column(String, nullable=True)  # e.g., "llm_search", "sitemap", "links"
    priority = Column(Integer, default=1)  # 1=high, 5=low
    
    # Crawling status
    is_crawled = Column(Boolean, default=False)
    crawl_attempts = Column(Integer, default=0)
    last_crawl_attempt = Column(DateTime, nullable=True)

    # Retention
    data_retention_days = Column(Integer, default=365)
    
    # Timestamps
    discovered_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    job = relationship("Job", back_populates="discovered_urls")
    crawl_results = relationship("CrawlResult", back_populates="discovered_url", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<DiscoveredURL(id={self.id}, url='{self.url}', crawled={self.is_crawled})>"


class CrawlResult(Base):
    __tablename__ = "crawl_results"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    discovered_url_id = Column(UUID, ForeignKey("discovered_urls.id"), nullable=False, index=True)
    
    # Crawl metadata
    status_code = Column(Integer, nullable=True)
    success = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)
    
    # Content
    raw_html = Column(Text, nullable=True)
    page_title = Column(String, nullable=True)
    meta_description = Column(Text, nullable=True)
    
    # Processing results
    extracted_data = Column(JsonEncodedDict, nullable=True)
    schema_inference = Column(JsonEncodedDict, nullable=True)
    
    # Storage paths
    html_file_path = Column(String, nullable=True)
    screenshot_path = Column(String, nullable=True)
    
    # Timestamps
    crawled_at = Column(DateTime, default=datetime.utcnow)

    # Retention
    data_retention_days = Column(Integer, default=365)
    
    # Relationships
    discovered_url = relationship("DiscoveredURL", back_populates="crawl_results")
    
    def __repr__(self):
        return f"<CrawlResult(id={self.id}, success={self.success}, status={self.status_code})>"
