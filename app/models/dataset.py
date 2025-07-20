from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Dataset(Base):
    __tablename__ = "datasets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    
    # Metadata
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    schema = Column(JSONB, nullable=True)  # Inferred schema
    
    # Statistics
    total_records = Column(Integer, default=0)
    total_sources = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    job = relationship("Job", back_populates="datasets")
    records = relationship("DataRecord", back_populates="dataset", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Dataset(id={self.id}, name='{self.name}', records={self.total_records})>"


class DataRecord(Base):
    __tablename__ = "data_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=False)
    
    # Source information
    source_url = Column(String, nullable=False)
    source_title = Column(String, nullable=True)
    
    # Extracted data
    data = Column(JSONB, nullable=False)
    
    # Vector embedding for similarity search
    embedding_id = Column(String, nullable=True)  # Reference to vector store
    
    # Quality metrics
    confidence_score = Column(Float, nullable=True)
    extraction_method = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    dataset = relationship("Dataset", back_populates="records")
    
    def __repr__(self):
        return f"<DataRecord(id={self.id}, source_url='{self.source_url}')>"