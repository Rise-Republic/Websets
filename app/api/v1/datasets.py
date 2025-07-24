from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models import Dataset, DataRecord, Job, User
from loguru import logger
from app.auth.dependencies import get_current_active_user
from app.storage import VectorStore, EmbeddingGenerator
from app.middleware import rbac_required, user_limiter, tenant_limiter, RateLimits
from app.middleware.audit_middleware import DataAccessAudit
from app.utils import (
    get_cached_dataset_records,
    set_cached_dataset_records,
    invalidate_dataset_records,
    sanitize_prompt,
)

router = APIRouter(prefix="/datasets", tags=["v1-datasets"])


class DatasetResponse(BaseModel):
    id: str
    job_id: str
    name: str
    description: str = None
    schema: dict = None
    total_records: int
    total_sources: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class DataRecordResponse(BaseModel):
    id: str
    source_url: str
    source_title: Optional[str] = None
    data: dict
    confidence_score: Optional[float] = None
    extraction_method: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


class DatasetListResponse(BaseModel):
    datasets: List[DatasetResponse]
    total: int
    page: int
    size: int


class SearchRequest(BaseModel):
    query: str
    limit: int = 10
    threshold: float = 0.5


class SearchResult(BaseModel):
    record: DataRecordResponse
    similarity_score: float


class SearchResponse(BaseModel):
    results: List[SearchResult]
    query: str
    total_found: int


@router.get("/", response_model=DatasetListResponse)
@rbac_required(permissions=["datasets:read"])
@user_limiter.limit(RateLimits.USER_DATASETS)
@tenant_limiter.limit(RateLimits.TENANT_DATASETS)
async def list_datasets(
    page: int = 1,
    size: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List user's datasets with pagination."""

    # Build query to get datasets for user's jobs
    query = db.query(Dataset).join(Job).filter(Job.tenant_id == current_user.tenant_id)

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * size
    datasets = (
        query.order_by(Dataset.created_at.desc()).offset(offset).limit(size).all()
    )

    # Convert to response format
    dataset_responses = []
    for dataset in datasets:
        dataset_responses.append(
            DatasetResponse(
                id=str(dataset.id),
                job_id=str(dataset.job_id),
                name=dataset.name,
                description=dataset.description,
                schema=dataset.schema,
                total_records=dataset.total_records,
                total_sources=dataset.total_sources,
                created_at=dataset.created_at.isoformat(),
                updated_at=dataset.updated_at.isoformat(),
            )
        )

    return DatasetListResponse(
        datasets=dataset_responses, total=total, page=page, size=size
    )


@router.get("/{dataset_id}", response_model=DatasetResponse)
@rbac_required(permissions=["datasets:read"])
@user_limiter.limit(RateLimits.USER_DATASETS)
@tenant_limiter.limit(RateLimits.TENANT_DATASETS)
async def get_dataset(
    dataset_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get dataset details."""

    dataset = (
        db.query(Dataset)
        .join(Job)
        .filter(Dataset.id == dataset_id, Job.tenant_id == current_user.tenant_id)
        .first()
    )

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found"
        )

    return DatasetResponse(
        id=str(dataset.id),
        job_id=str(dataset.job_id),
        name=dataset.name,
        description=dataset.description,
        schema=dataset.schema,
        total_records=dataset.total_records,
        total_sources=dataset.total_sources,
        created_at=dataset.created_at.isoformat(),
        updated_at=dataset.updated_at.isoformat(),
    )


@router.get("/{dataset_id}/records")
@rbac_required(permissions=["datasets:read"])
@user_limiter.limit(RateLimits.USER_DATASETS)
@tenant_limiter.limit(RateLimits.TENANT_DATASETS)
async def get_dataset_records(
    dataset_id: str,
    page: int = 1,
    size: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get records from a dataset with pagination."""

    # Check cache first
    cached = await get_cached_dataset_records(
        dataset_id, page, size, current_user.tenant_id
    )
    if cached:
        return cached

    # Verify dataset access
    dataset = (
        db.query(Dataset)
        .join(Job)
        .filter(Dataset.id == dataset_id, Job.tenant_id == current_user.tenant_id)
        .first()
    )

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found"
        )

    # Get records with pagination
    query = db.query(DataRecord).filter(DataRecord.dataset_id == dataset_id)
    total = query.count()

    offset = (page - 1) * size
    records = (
        query.order_by(DataRecord.created_at.desc()).offset(offset).limit(size).all()
    )

    DataAccessAudit.log_data_access(
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        dataset_id=dataset.id,
        access_type="read",
        records_accessed=len(records),
    )

    # Convert to response format
    record_responses = []
    for record in records:
        record_responses.append(
            DataRecordResponse(
                id=str(record.id),
                source_url=record.source_url,
                source_title=record.source_title,
                data=record.data,
                confidence_score=record.confidence_score,
                extraction_method=record.extraction_method,
                created_at=record.created_at.isoformat(),
            )
        )

    response = {
        "records": record_responses,
        "total": total,
        "page": page,
        "size": size,
        "dataset_id": dataset_id,
    }

    await set_cached_dataset_records(
        dataset_id, page, size, current_user.tenant_id, response
    )
    return response


@router.post("/{dataset_id}/search", response_model=SearchResponse)
@rbac_required(permissions=["datasets:read"])
@user_limiter.limit(RateLimits.USER_DATASETS)
@tenant_limiter.limit(RateLimits.TENANT_DATASETS)
async def search_dataset(
    dataset_id: str,
    search_request: SearchRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Perform semantic search on dataset records."""

    # Verify dataset access
    dataset = (
        db.query(Dataset)
        .join(Job)
        .filter(Dataset.id == dataset_id, Job.tenant_id == current_user.tenant_id)
        .first()
    )

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found"
        )

    try:
        sanitized_query = sanitize_prompt(search_request.query)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    try:
        # Initialize components
        embedding_gen = EmbeddingGenerator()
        vector_store = VectorStore()

        # Load vector store
        if not vector_store.load():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Vector search not available",
            )

        # Generate query embedding
        query_embedding = embedding_gen.generate_embedding(sanitized_query)

        # Search for similar vectors
        search_results = vector_store.search(
            query_embedding, k=search_request.limit, threshold=search_request.threshold
        )

        # Filter results for this dataset and get record details
        record_ids = [
            uuid.UUID(res["record_id"])
            for res in search_results
            if res.get("dataset_id") == dataset_id
        ]
        records = (
            db.query(DataRecord).filter(DataRecord.id.in_(record_ids)).all()
            if record_ids
            else []
        )
        record_map = {str(r.id): r for r in records}

        filtered_results = []
        for result in search_results:
            if result.get("dataset_id") == dataset_id:
                record = record_map.get(result.get("record_id"))
                if record:
                    filtered_results.append(
                        SearchResult(
                            record=DataRecordResponse(
                                id=str(record.id),
                                source_url=record.source_url,
                                source_title=record.source_title,
                                data=record.data,
                                confidence_score=record.confidence_score,
                                extraction_method=record.extraction_method,
                                created_at=record.created_at.isoformat(),
                            ),
                            similarity_score=result["similarity_score"],
                        )
                    )

        return SearchResponse(
            results=filtered_results,
            query=search_request.query,
            total_found=len(filtered_results),
        )

    except Exception as e:
        logger.opt(exception=e).error("Dataset search failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed",
        )


@router.get("/{dataset_id}/export")
@rbac_required(permissions=["datasets:export"])
@user_limiter.limit(RateLimits.USER_DATASETS)
@tenant_limiter.limit(RateLimits.TENANT_DATASETS)
async def export_dataset(
    dataset_id: str,
    format: str = Query("json", regex="^(json|csv)$"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Export dataset in JSON or CSV format."""

    # Verify dataset access
    dataset = (
        db.query(Dataset)
        .join(Job)
        .filter(Dataset.id == dataset_id, Job.tenant_id == current_user.tenant_id)
        .first()
    )

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found"
        )

    # Get all records
    records = db.query(DataRecord).filter(DataRecord.dataset_id == dataset_id).all()

    DataAccessAudit.log_data_access(
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        dataset_id=dataset.id,
        access_type="export",
        records_accessed=len(records),
    )

    if format == "json":
        from fastapi.responses import JSONResponse

        export_data = {
            "dataset": {
                "id": str(dataset.id),
                "name": dataset.name,
                "description": dataset.description,
                "schema": dataset.schema,
                "total_records": len(records),
                "exported_at": datetime.utcnow().isoformat(),
            },
            "records": [
                {
                    "id": str(record.id),
                    "source_url": record.source_url,
                    "source_title": record.source_title,
                    "data": record.data,
                    "confidence_score": record.confidence_score,
                    "created_at": record.created_at.isoformat(),
                }
                for record in records
            ],
        }

        return JSONResponse(content=export_data)

    elif format == "csv":
        import csv
        import io
        from fastapi.responses import StreamingResponse

        # Create CSV content
        output = io.StringIO()

        if records:
            # Get all possible field names from the data
            all_fields = set()
            for record in records:
                all_fields.update(record.data.keys())

            # Create header
            fieldnames = [
                "id",
                "source_url",
                "source_title",
                "confidence_score",
                "created_at",
            ] + sorted(all_fields)
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()

            # Write records
            for record in records:
                row = {
                    "id": str(record.id),
                    "source_url": record.source_url,
                    "source_title": record.source_title or "",
                    "confidence_score": record.confidence_score or 0.0,
                    "created_at": record.created_at.isoformat(),
                }
                # Add data fields
                for field in all_fields:
                    value = record.data.get(field, "")
                    # Convert complex types to strings
                    if isinstance(value, (dict, list)):
                        value = str(value)
                    row[field] = value

                writer.writerow(row)

        output.seek(0)

        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=dataset_{dataset_id}.csv"
            },
        )


@router.delete("/{dataset_id}")
@rbac_required(permissions=["datasets:delete"])
@user_limiter.limit(RateLimits.USER_DATASETS)
@tenant_limiter.limit(RateLimits.TENANT_DATASETS)
async def delete_dataset(
    dataset_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete a dataset and all its records."""

    dataset = (
        db.query(Dataset)
        .join(Job)
        .filter(Dataset.id == dataset_id, Job.tenant_id == current_user.tenant_id)
        .first()
    )

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found"
        )

    # Delete dataset (cascade will handle records)
    db.delete(dataset)
    db.commit()

    await invalidate_dataset_records(dataset_id)

    return {"message": "Dataset deleted successfully"}
