import pytest
from datetime import datetime
from app.models.user import User
from app.auth.jwt_handler import get_password_hash


@pytest.mark.unit
class TestUserModel:
    def test_user_creation(self, db_session):
        """Test creating a user."""
        user = User(
            email="test@example.com",
            hashed_password=get_password_hash("password"),
            full_name="Test User"
        )
        
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.is_active is True
        assert user.is_admin is False
        assert isinstance(user.created_at, datetime)

    def test_user_repr(self, db_session):
        """Test user string representation."""
        user = User(
            email="test@example.com",
            hashed_password=get_password_hash("password")
        )
        
        db_session.add(user)
        db_session.commit()
        
        repr_str = repr(user)
        assert "User(id=" in repr_str
        assert "email='test@example.com'" in repr_str

    def test_user_unique_email_constraint(self, db_session):
        """Test that email must be unique."""
        user1 = User(
            email="test@example.com",
            hashed_password=get_password_hash("password1")
        )
        user2 = User(
            email="test@example.com",
            hashed_password=get_password_hash("password2")
        )
        
        db_session.add(user1)
        db_session.commit()
        
        db_session.add(user2)
        with pytest.raises(Exception):  # Should raise IntegrityError
            db_session.commit()