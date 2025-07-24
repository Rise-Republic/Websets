import pytest
import uuid
from datetime import datetime


@pytest.mark.unit
class TestUserModel:
    @pytest.fixture(autouse=True)
    def model_imports(self):
        from app.models.user import User
        from app.auth.jwt_handler import get_password_hash

        self.User = User
        self.get_password_hash = get_password_hash

    def test_user_creation(self, db_session):
        """Test creating a user."""
        user = self.User(
            email="test@example.com",
            hashed_password=self.get_password_hash("password"),
            full_name="Test User",
            tenant_id=uuid.uuid4(),
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
        user = self.User(
            email="test@example.com",
            hashed_password=self.get_password_hash("password"),
            tenant_id=uuid.uuid4(),
        )

        db_session.add(user)
        db_session.commit()

        repr_str = repr(user)
        assert "User(id=" in repr_str
        assert "email='test@example.com'" in repr_str

    def test_user_unique_email_constraint(self, db_session):
        """Test that email must be unique."""
        user1 = self.User(
            email="test@example.com",
            hashed_password=self.get_password_hash("password1"),
            tenant_id=uuid.uuid4(),
        )
        user2 = self.User(
            email="test@example.com",
            hashed_password=self.get_password_hash("password2"),
            tenant_id=uuid.uuid4(),
        )

        db_session.add(user1)
        db_session.commit()

        db_session.add(user2)
        with pytest.raises(Exception):  # Should raise IntegrityError
            db_session.commit()


class TestDataRetention:
    @pytest.fixture(autouse=True)
    def model_imports(self):
        from app.models.dataset import Dataset
        from app.models.job import Job
        from app.models.user import User
        from app.auth.jwt_handler import get_password_hash

        self.Dataset = Dataset
        self.Job = Job
        self.User = User
        self.get_password_hash = get_password_hash

    def test_dataset_retention_default(self, db_session):
        user = self.User(
            email="retention@example.com",
            hashed_password=self.get_password_hash("password"),
            tenant_id=uuid.uuid4(),
        )
        db_session.add(user)
        db_session.commit()

        job = self.Job(user_id=user.id, tenant_id=user.tenant_id, prompt="test")
        db_session.add(job)
        db_session.commit()

        dataset = self.Dataset(job_id=job.id, tenant_id=user.tenant_id, name="ds")
        db_session.add(dataset)
        db_session.commit()

        assert dataset.data_retention_days == 365
