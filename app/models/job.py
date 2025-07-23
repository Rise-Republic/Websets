from sqlalchemy import Column, Integer, String, DateTime, Text, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class JobStatus(enum.Enum):
    PENDING = "pending"
    PLANNING = "planning"
    DISCOVERING = "discovering"
    CRAWLING = "crawling"
    EXTRACTING = "extracting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Job configuration
    prompt = Column(Text, nullable=False)
    status = Column(Enum(JobStatus), default=JobStatus.PENDING, nullable=False)
    
    # Planning phase
    plan = Column(JSONB, nullable=True)
    
    # Progress tracking
    total_urls = Column(Integer, default=0)
    crawled_urls = Column(Integer, default=0)
    extracted_records = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    logs = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="jobs")
    discovered_urls = relationship("DiscoveredURL", back_populates="job", cascade="all, delete-orphan")
    datasets = relationship("Dataset", back_populates="job", cascade="all, delete-orphan")
    data_access_logs = relationship("DataAccessLog", back_populates="job", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Job(id={self.id}, status={self.status.value}, prompt='{self.prompt[:50]}...')>"