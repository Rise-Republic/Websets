"""
Unit Tests for Authentication Service
Testing JWT handling, user authentication, and authorization
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import jwt
from fastapi import HTTPException, status

from app.auth.jwt_handler import JWTHandler
from app.auth.service import AuthService
from app.auth.models import User, UserRole
from app.auth.dependencies import get_current_user, require_permission


class TestJWTHandler:
    """Test JWT token creation and validation"""

    def setup_method(self):
        self.jwt_handler = JWTHandler()
        self.test_user_data = {
            "user_id": "test-user-123",
            "email": "test@example.com",
            "role": "user",
            "tenant_id": "tenant-456"
        }

    def test_create_access_token(self):
        """Test access token creation"""
        token = self.jwt_handler.create_access_token(self.test_user_data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Decode and verify payload
        decoded = jwt.decode(
            token, 
            self.jwt_handler.secret_key, 
            algorithms=[self.jwt_handler.algorithm]
        )
        
        assert decoded["user_id"] == "test-user-123"
        assert decoded["email"] == "test@example.com"
        assert decoded["role"] == "user"
        assert decoded["tenant_id"] == "tenant-456"
        assert "exp" in decoded
        assert "iat" in decoded

    def test_create_refresh_token(self):
        """Test refresh token creation"""
        token = self.jwt_handler.create_refresh_token(self.test_user_data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        decoded = jwt.decode(
            token, 
            self.jwt_handler.secret_key, 
            algorithms=[self.jwt_handler.algorithm]
        )
        
        assert decoded["user_id"] == "test-user-123"
        assert decoded["type"] == "refresh"

    def test_verify_token_valid(self):
        """Test valid token verification"""
        token = self.jwt_handler.create_access_token(self.test_user_data)
        payload = self.jwt_handler.verify_token(token)
        
        assert payload["user_id"] == "test-user-123"
        assert payload["email"] == "test@example.com"

    def test_verify_token_expired(self):
        """Test expired token verification"""
        # Create token with past expiry
        expired_data = {
            **self.test_user_data,
            "exp": datetime.utcnow() - timedelta(hours=1)
        }
        
        token = jwt.encode(
            expired_data,
            self.jwt_handler.secret_key,
            algorithm=self.jwt_handler.algorithm
        )
        
        with pytest.raises(HTTPException) as exc_info:
            self.jwt_handler.verify_token(token)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Token has expired" in str(exc_info.value.detail)

    def test_verify_token_invalid_signature(self):
        """Test token with invalid signature"""
        # Create token with wrong secret
        token = jwt.encode(
            self.test_user_data,
            "wrong-secret",
            algorithm=self.jwt_handler.algorithm
        )
        
        with pytest.raises(HTTPException) as exc_info:
            self.jwt_handler.verify_token(token)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_verify_token_malformed(self):
        """Test malformed token verification"""
        with pytest.raises(HTTPException) as exc_info:
            self.jwt_handler.verify_token("invalid.token.format")
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_access_token(self):
        """Test access token refresh"""
        refresh_token = self.jwt_handler.create_refresh_token(self.test_user_data)
        new_access_token = self.jwt_handler.refresh_access_token(refresh_token)
        
        assert isinstance(new_access_token, str)
        
        # Verify new token contains user data
        payload = self.jwt_handler.verify_token(new_access_token)
        assert payload["user_id"] == "test-user-123"

    def test_refresh_with_access_token_fails(self):
        """Test refresh fails with access token"""
        access_token = self.jwt_handler.create_access_token(self.test_user_data)
        
        with pytest.raises(HTTPException) as exc_info:
            self.jwt_handler.refresh_access_token(access_token)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


class TestAuthService:
    """Test authentication service operations"""

    def setup_method(self):
        self.auth_service = AuthService()
        self.mock_workos_client = Mock()
        self.auth_service.workos_client = self.mock_workos_client

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self):
        """Test successful user authentication"""
        # Mock WorkOS response
        mock_user = {
            "id": "user-123",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User"
        }
        
        self.mock_workos_client.user_management.get_user.return_value = mock_user
        
        user = await self.auth_service.authenticate_user("valid-token")
        
        assert user.id == "user-123"
        assert user.email == "test@example.com"
        assert user.name == "Test User"

    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_token(self):
        """Test authentication with invalid token"""
        self.mock_workos_client.user_management.get_user.side_effect = Exception("Invalid token")
        
        with pytest.raises(HTTPException) as exc_info:
            await self.auth_service.authenticate_user("invalid-token")
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_get_user_permissions(self):
        """Test user permission retrieval"""
        mock_user = User(
            id="user-123",
            email="admin@example.com",
            name="Admin User",
            role=UserRole.ADMIN
        )
        
        permissions = await self.auth_service.get_user_permissions(mock_user)
        
        assert "read:datasets" in permissions
        assert "write:datasets" in permissions
        assert "admin:users" in permissions

    @pytest.mark.asyncio
    async def test_validate_tenant_access(self):
        """Test tenant access validation"""
        mock_user = User(
            id="user-123",
            email="test@example.com",
            name="Test User",
            tenant_id="tenant-456"
        )
        
        # Valid tenant access
        is_valid = await self.auth_service.validate_tenant_access(mock_user, "tenant-456")
        assert is_valid is True
        
        # Invalid tenant access
        is_valid = await self.auth_service.validate_tenant_access(mock_user, "other-tenant")
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_create_user_session(self):
        """Test user session creation"""
        mock_user = User(
            id="user-123",
            email="test@example.com",
            name="Test User"
        )
        
        with patch.object(self.auth_service, 'jwt_handler') as mock_jwt:
            mock_jwt.create_access_token.return_value = "access-token"
            mock_jwt.create_refresh_token.return_value = "refresh-token"
            
            session = await self.auth_service.create_user_session(mock_user)
            
            assert session["access_token"] == "access-token"
            assert session["refresh_token"] == "refresh-token"
            assert session["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_revoke_user_session(self):
        """Test user session revocation"""
        with patch.object(self.auth_service, 'token_blacklist') as mock_blacklist:
            mock_blacklist.add_token = AsyncMock()
            
            await self.auth_service.revoke_user_session("access-token")
            
            mock_blacklist.add_token.assert_called_once_with("access-token")


class TestAuthDependencies:
    """Test FastAPI authentication dependencies"""

    def setup_method(self):
        self.mock_jwt_handler = Mock()
        self.mock_auth_service = Mock()

    @pytest.mark.asyncio
    async def test_get_current_user_success(self):
        """Test successful current user retrieval"""
        mock_request = Mock()
        mock_request.headers = {"Authorization": "Bearer valid-token"}
        
        mock_user = User(
            id="user-123",
            email="test@example.com",
            name="Test User"
        )
        
        with patch('app.auth.dependencies.jwt_handler') as mock_jwt:
            with patch('app.auth.dependencies.auth_service') as mock_auth:
                mock_jwt.verify_token.return_value = {"user_id": "user-123"}
                mock_auth.get_user_by_id.return_value = mock_user
                
                user = await get_current_user(mock_request)
                
                assert user.id == "user-123"
                assert user.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_current_user_no_token(self):
        """Test current user retrieval without token"""
        mock_request = Mock()
        mock_request.headers = {}
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_format(self):
        """Test current user retrieval with invalid token format"""
        mock_request = Mock()
        mock_request.headers = {"Authorization": "InvalidFormat token"}
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_require_permission_success(self):
        """Test successful permission requirement"""
        mock_user = User(
            id="user-123",
            email="admin@example.com",
            name="Admin User",
            role=UserRole.ADMIN
        )
        
        # Should not raise exception for admin user
        await require_permission("admin:users")(mock_user)

    @pytest.mark.asyncio
    async def test_require_permission_insufficient(self):
        """Test insufficient permission requirement"""
        mock_user = User(
            id="user-123",
            email="user@example.com",
            name="Regular User",
            role=UserRole.USER
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await require_permission("admin:users")(mock_user)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_tenant_isolation(self):
        """Test tenant isolation in multi-tenant environment"""
        user_tenant_a = User(
            id="user-123",
            email="user@example.com",
            name="User A",
            tenant_id="tenant-a"
        )
        
        user_tenant_b = User(
            id="user-456",
            email="user2@example.com",
            name="User B",
            tenant_id="tenant-b"
        )
        
        # Mock dataset belonging to tenant A
        mock_dataset = Mock()
        mock_dataset.tenant_id = "tenant-a"
        
        with patch('app.auth.dependencies.validate_resource_access') as mock_validate:
            mock_validate.return_value = True
            
            # User A should have access
            result = await mock_validate(user_tenant_a, mock_dataset)
            assert result is True
            
            mock_validate.return_value = False
            
            # User B should not have access
            result = await mock_validate(user_tenant_b, mock_dataset)
            assert result is False


class TestUserModel:
    """Test User model and role-based permissions"""

    def test_user_creation(self):
        """Test user model creation"""
        user = User(
            id="user-123",
            email="test@example.com",
            name="Test User",
            role=UserRole.USER
        )
        
        assert user.id == "user-123"
        assert user.email == "test@example.com"
        assert user.role == UserRole.USER

    def test_user_permissions_by_role(self):
        """Test user permissions based on role"""
        admin_user = User(
            id="admin-123",
            email="admin@example.com",
            name="Admin User",
            role=UserRole.ADMIN
        )
        
        regular_user = User(
            id="user-123",
            email="user@example.com",
            name="Regular User",
            role=UserRole.USER
        )
        
        # Admin should have all permissions
        assert admin_user.has_permission("admin:users")
        assert admin_user.has_permission("write:datasets")
        assert admin_user.has_permission("read:datasets")
        
        # Regular user should have limited permissions
        assert not regular_user.has_permission("admin:users")
        assert regular_user.has_permission("read:datasets")

    def test_user_serialization(self):
        """Test user model serialization"""
        user = User(
            id="user-123",
            email="test@example.com",
            name="Test User",
            role=UserRole.USER
        )
        
        user_dict = user.dict()
        
        assert user_dict["id"] == "user-123"
        assert user_dict["email"] == "test@example.com"
        assert user_dict["role"] == "user"

    def test_user_equality(self):
        """Test user model equality"""
        user1 = User(
            id="user-123",
            email="test@example.com",
            name="Test User"
        )
        
        user2 = User(
            id="user-123",
            email="test@example.com",
            name="Test User"
        )
        
        user3 = User(
            id="user-456",
            email="other@example.com",
            name="Other User"
        )
        
        assert user1 == user2
        assert user1 != user3


@pytest.fixture
def mock_auth_service():
    """Fixture for mocked authentication service"""
    with patch('app.auth.service.AuthService') as mock:
        yield mock.return_value


@pytest.fixture
def mock_jwt_handler():
    """Fixture for mocked JWT handler"""
    with patch('app.auth.jwt_handler.JWTHandler') as mock:
        yield mock.return_value


@pytest.fixture
def sample_user():
    """Fixture for sample user"""
    return User(
        id="user-123",
        email="test@example.com",
        name="Test User",
        role=UserRole.USER,
        tenant_id="tenant-456"
    )
