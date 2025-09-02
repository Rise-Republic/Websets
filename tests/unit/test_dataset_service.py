"""
Unit Tests for Dataset Service
Testing dataset CRUD operations, validation, and business logic
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from app.services.dataset_service import DatasetService
from app.models.dataset import Dataset, DatasetStatus
from app.schemas.dataset import DatasetCreate, DatasetUpdate
from app.core.exceptions import ValidationError, NotFoundError


class TestDatasetService:
    """Test dataset service operations"""

    def setup_method(self):
        self.mock_db = Mock()
        self.mock_session = Mock()
        self.mock_db.return_value.__enter__.return_value = self.mock_session
        self.dataset_service = DatasetService(self.mock_db)

    @pytest.mark.asyncio
    async def test_create_dataset_success(self):
        """Test successful dataset creation"""
        dataset_data = DatasetCreate(
            name="Test Dataset",
            description="A test dataset",
            source_urls=["https://example.com"],
            tags=["test", "example"]
        )
        
        mock_dataset = Dataset(
            id=1,
            name="Test Dataset",
            description="A test dataset",
            status=DatasetStatus.PENDING,
            created_at=datetime.utcnow(),
            tenant_id="tenant-123"
        )
        
        self.mock_session.add = Mock()
        self.mock_session.commit = AsyncMock()
        self.mock_session.refresh = AsyncMock()
        
        with patch.object(Dataset, '__init__', return_value=None):
            with patch.object(self.dataset_service, '_validate_source_urls', return_value=True):
                result = await self.dataset_service.create_dataset(
                    dataset_data, 
                    user_id="user-123", 
                    tenant_id="tenant-123"
                )
        
        self.mock_session.add.assert_called_once()
        self.mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_dataset_duplicate_name(self):
        """Test dataset creation with duplicate name"""
        dataset_data = DatasetCreate(
            name="Existing Dataset",
            description="A test dataset",
            source_urls=["https://example.com"]
        )
        
        self.mock_session.commit.side_effect = IntegrityError("", "", "")
        
        with pytest.raises(HTTPException) as exc_info:
            await self.dataset_service.create_dataset(
                dataset_data,
                user_id="user-123",
                tenant_id="tenant-123"
            )
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "already exists" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_create_dataset_invalid_urls(self):
        """Test dataset creation with invalid URLs"""
        dataset_data = DatasetCreate(
            name="Test Dataset",
            description="A test dataset",
            source_urls=["invalid-url", "not-a-url"]
        )
        
        with patch.object(self.dataset_service, '_validate_source_urls', side_effect=ValidationError("Invalid URLs")):
            with pytest.raises(ValidationError):
                await self.dataset_service.create_dataset(
                    dataset_data,
                    user_id="user-123",
                    tenant_id="tenant-123"
                )

    @pytest.mark.asyncio
    async def test_get_dataset_success(self):
        """Test successful dataset retrieval"""
        mock_dataset = Dataset(
            id=1,
            name="Test Dataset",
            status=DatasetStatus.ACTIVE,
            tenant_id="tenant-123"
        )
        
        self.mock_session.query.return_value.filter.return_value.first.return_value = mock_dataset
        
        result = await self.dataset_service.get_dataset(1, tenant_id="tenant-123")
        
        assert result.id == 1
        assert result.name == "Test Dataset"

    @pytest.mark.asyncio
    async def test_get_dataset_not_found(self):
        """Test dataset retrieval when not found"""
        self.mock_session.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(NotFoundError):
            await self.dataset_service.get_dataset(999, tenant_id="tenant-123")

    @pytest.mark.asyncio
    async def test_get_dataset_wrong_tenant(self):
        """Test dataset retrieval with wrong tenant"""
        mock_dataset = Dataset(
            id=1,
            name="Test Dataset",
            tenant_id="other-tenant"
        )
        
        self.mock_session.query.return_value.filter.return_value.first.return_value = mock_dataset
        
        with pytest.raises(NotFoundError):
            await self.dataset_service.get_dataset(1, tenant_id="tenant-123")

    @pytest.mark.asyncio
    async def test_list_datasets_with_filters(self):
        """Test dataset listing with filters"""
        mock_datasets = [
            Dataset(id=1, name="Dataset 1", status=DatasetStatus.ACTIVE),
            Dataset(id=2, name="Dataset 2", status=DatasetStatus.ACTIVE)
        ]
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_datasets
        mock_query.count.return_value = 2
        
        self.mock_session.query.return_value = mock_query
        
        result = await self.dataset_service.list_datasets(
            tenant_id="tenant-123",
            status=DatasetStatus.ACTIVE,
            page=1,
            limit=10
        )
        
        assert len(result["datasets"]) == 2
        assert result["total"] == 2
        assert result["page"] == 1

    @pytest.mark.asyncio
    async def test_update_dataset_success(self):
        """Test successful dataset update"""
        mock_dataset = Dataset(
            id=1,
            name="Old Name",
            description="Old description",
            tenant_id="tenant-123"
        )
        
        update_data = DatasetUpdate(
            name="New Name",
            description="New description"
        )
        
        self.mock_session.query.return_value.filter.return_value.first.return_value = mock_dataset
        self.mock_session.commit = AsyncMock()
        
        result = await self.dataset_service.update_dataset(
            1, 
            update_data, 
            tenant_id="tenant-123"
        )
        
        assert mock_dataset.name == "New Name"
        assert mock_dataset.description == "New description"
        self.mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_dataset_success(self):
        """Test successful dataset deletion"""
        mock_dataset = Dataset(
            id=1,
            name="Test Dataset",
            tenant_id="tenant-123"
        )
        
        self.mock_session.query.return_value.filter.return_value.first.return_value = mock_dataset
        self.mock_session.delete = Mock()
        self.mock_session.commit = AsyncMock()
        
        await self.dataset_service.delete_dataset(1, tenant_id="tenant-123")
        
        self.mock_session.delete.assert_called_once_with(mock_dataset)
        self.mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_dataset_with_records(self):
        """Test dataset deletion with existing records"""
        mock_dataset = Dataset(
            id=1,
            name="Test Dataset",
            record_count=1000,
            tenant_id="tenant-123"
        )
        
        self.mock_session.query.return_value.filter.return_value.first.return_value = mock_dataset
        
        with pytest.raises(HTTPException) as exc_info:
            await self.dataset_service.delete_dataset(1, tenant_id="tenant-123")
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "contains records" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_start_processing_dataset(self):
        """Test starting dataset processing"""
        mock_dataset = Dataset(
            id=1,
            name="Test Dataset",
            status=DatasetStatus.PENDING,
            tenant_id="tenant-123"
        )
        
        self.mock_session.query.return_value.filter.return_value.first.return_value = mock_dataset
        self.mock_session.commit = AsyncMock()
        
        with patch.object(self.dataset_service, '_trigger_crawl_job') as mock_trigger:
            mock_trigger.return_value = AsyncMock()
            
            await self.dataset_service.start_processing(1, tenant_id="tenant-123")
            
            assert mock_dataset.status == DatasetStatus.PROCESSING
            mock_trigger.assert_called_once()
            self.mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_processing_invalid_status(self):
        """Test starting processing with invalid status"""
        mock_dataset = Dataset(
            id=1,
            name="Test Dataset",
            status=DatasetStatus.ACTIVE,
            tenant_id="tenant-123"
        )
        
        self.mock_session.query.return_value.filter.return_value.first.return_value = mock_dataset
        
        with pytest.raises(HTTPException) as exc_info:
            await self.dataset_service.start_processing(1, tenant_id="tenant-123")
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "cannot be processed" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_dataset_statistics(self):
        """Test dataset statistics retrieval"""
        mock_stats = {
            "total_records": 10000,
            "successful_crawls": 9500,
            "failed_crawls": 500,
            "avg_processing_time": 15.5,
            "last_updated": datetime.utcnow()
        }
        
        with patch.object(self.dataset_service, '_calculate_statistics', return_value=mock_stats):
            stats = await self.dataset_service.get_dataset_statistics(1, tenant_id="tenant-123")
            
            assert stats["total_records"] == 10000
            assert stats["successful_crawls"] == 9500
            assert "success_rate" in stats

    def test_validate_source_urls_valid(self):
        """Test URL validation with valid URLs"""
        valid_urls = [
            "https://example.com",
            "http://test-site.org/page",
            "https://subdomain.example.com/path?param=value"
        ]
        
        result = self.dataset_service._validate_source_urls(valid_urls)
        assert result is True

    def test_validate_source_urls_invalid(self):
        """Test URL validation with invalid URLs"""
        invalid_urls = [
            "not-a-url",
            "ftp://example.com",  # Unsupported protocol
            "javascript:alert('xss')",  # Security risk
            ""  # Empty URL
        ]
        
        with pytest.raises(ValidationError):
            self.dataset_service._validate_source_urls(invalid_urls)

    def test_validate_source_urls_mixed(self):
        """Test URL validation with mixed valid/invalid URLs"""
        mixed_urls = [
            "https://example.com",
            "invalid-url",
            "http://test-site.org"
        ]
        
        with pytest.raises(ValidationError) as exc_info:
            self.dataset_service._validate_source_urls(mixed_urls)
        
        assert "invalid-url" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_search_datasets(self):
        """Test dataset search functionality"""
        mock_datasets = [
            Dataset(id=1, name="E-commerce Data", description="Product information"),
            Dataset(id=2, name="News Articles", description="Latest news content")
        ]
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_datasets
        
        self.mock_session.query.return_value = mock_query
        
        results = await self.dataset_service.search_datasets(
            query="e-commerce",
            tenant_id="tenant-123"
        )
        
        assert len(results) == 1
        assert results[0].name == "E-commerce Data"

    @pytest.mark.asyncio
    async def test_get_dataset_tags(self):
        """Test dataset tags retrieval"""
        mock_tags = ["e-commerce", "products", "retail", "news", "articles"]
        
        with patch.object(self.dataset_service, '_get_all_tags', return_value=mock_tags):
            tags = await self.dataset_service.get_available_tags(tenant_id="tenant-123")
            
            assert "e-commerce" in tags
            assert "products" in tags
            assert len(tags) == 5

    @pytest.mark.asyncio
    async def test_bulk_update_datasets(self):
        """Test bulk dataset updates"""
        dataset_ids = [1, 2, 3]
        update_data = {"status": DatasetStatus.INACTIVE}
        
        mock_datasets = [
            Dataset(id=1, tenant_id="tenant-123"),
            Dataset(id=2, tenant_id="tenant-123"),
            Dataset(id=3, tenant_id="tenant-123")
        ]
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_datasets
        
        self.mock_session.query.return_value = mock_query
        self.mock_session.commit = AsyncMock()
        
        result = await self.dataset_service.bulk_update_datasets(
            dataset_ids,
            update_data,
            tenant_id="tenant-123"
        )
        
        assert result["updated_count"] == 3
        for dataset in mock_datasets:
            assert dataset.status == DatasetStatus.INACTIVE

    @pytest.mark.asyncio
    async def test_export_dataset_metadata(self):
        """Test dataset metadata export"""
        mock_dataset = Dataset(
            id=1,
            name="Test Dataset",
            description="Test description",
            status=DatasetStatus.ACTIVE,
            record_count=1000,
            tenant_id="tenant-123"
        )
        
        self.mock_session.query.return_value.filter.return_value.first.return_value = mock_dataset
        
        metadata = await self.dataset_service.export_dataset_metadata(
            1,
            tenant_id="tenant-123"
        )
        
        assert metadata["name"] == "Test Dataset"
        assert metadata["record_count"] == 1000
        assert "export_timestamp" in metadata


@pytest.fixture
def mock_dataset_service():
    """Fixture for mocked dataset service"""
    with patch('app.services.dataset_service.DatasetService') as mock:
        yield mock.return_value


@pytest.fixture
def sample_dataset():
    """Fixture for sample dataset"""
    return Dataset(
        id=1,
        name="Sample Dataset",
        description="A sample dataset for testing",
        status=DatasetStatus.ACTIVE,
        record_count=5000,
        tenant_id="tenant-123",
        created_at=datetime.utcnow()
    )


@pytest.fixture
def sample_dataset_create():
    """Fixture for dataset creation data"""
    return DatasetCreate(
        name="New Dataset",
        description="A new dataset for testing",
        source_urls=["https://example.com", "https://test-site.org"],
        tags=["test", "sample"]
    )
