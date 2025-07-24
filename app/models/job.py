from sqlalchemy import Column, Integer, DateTime, Text, Enum, ForeignKey
from app.models.types import GUID as UUID, JsonEncodedDict
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

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False, index=True)
    tenant_id = Column(UUID, nullable=True, index=True)

    # Job configuration
    prompt = Column(Text, nullable=False)
    status = Column(
        Enum(JobStatus), default=JobStatus.PENDING, nullable=False, index=True
    )

    # Planning phase
    plan = Column(JsonEncodedDict, nullable=True)

    # Progress tracking
    total_urls = Column(Integer, default=0)
    crawled_urls = Column(Integer, default=0)
    extracted_records = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Retention
    data_retention_days = Column(Integer, default=365)

    # Error handling
    error_message = Column(Text, nullable=True)
    logs = Column(Text, nullable=True)

    # Relationships
    user = relationship("User", back_populates="jobs")
    discovered_urls = relationship(
        "DiscoveredURL", back_populates="job", cascade="all, delete-orphan"
    )
    datasets = relationship(
        "Dataset", back_populates="job", cascade="all, delete-orphan"
    )
    data_access_logs = relationship(
        "DataAccessLog", back_populates="job", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Job(id={self.id}, status={self.status.value}, prompt='{self.prompt[:50]}...')>"
