from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float
from app.models.types import GUID as UUID, JsonEncodedDict
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Dataset(Base):
    __tablename__ = "datasets"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID, ForeignKey("jobs.id"), nullable=False, index=True)
    
    # Metadata
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    schema = Column(JsonEncodedDict, nullable=True)  # Inferred schema
    
    # Statistics
    total_records = Column(Integer, default=0)
    total_sources = Column(Integer, default=0)

    # Retention
    data_retention_days = Column(Integer, default=365)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    job = relationship("Job", back_populates="datasets")
    records = relationship("DataRecord", back_populates="dataset", cascade="all, delete-orphan")
    access_logs = relationship("DataAccessLog", back_populates="dataset", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Dataset(id={self.id}, name='{self.name}', records={self.total_records})>"


class DataRecord(Base):
    __tablename__ = "data_records"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    dataset_id = Column(UUID, ForeignKey("datasets.id"), nullable=False, index=True)
    
    # Source information
    source_url = Column(String, nullable=False)
    source_title = Column(String, nullable=True)
    
    # Extracted data
    data = Column(JsonEncodedDict, nullable=False)
    
    # Vector embedding for similarity search
    embedding_id = Column(String, nullable=True)  # Reference to vector store
    
    # Quality metrics
    confidence_score = Column(Float, nullable=True)
    extraction_method = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Retention
    data_retention_days = Column(Integer, default=365)
    
    # Relationships
    dataset = relationship("Dataset", back_populates="records")
    
    def __repr__(self):
        return f"<DataRecord(id={self.id}, source_url='{self.source_url}')>"