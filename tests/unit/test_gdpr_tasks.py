import uuid
from datetime import datetime, timedelta

import pytest

from app.tasks import gdpr_tasks
from app.auth.jwt_handler import get_password_hash


@pytest.mark.unit
def test_export_user_data_task(db_session, mocker):
    from app.models import User, Job, Dataset
    user = User(
        email="u@example.com",
        hashed_password=get_password_hash("pw"),
        tenant_id=uuid.uuid4(),
        consent_given=True,
        consent_given_at=datetime.utcnow(),
    )
    db_session.add(user)
    db_session.commit()

    job = Job(user_id=user.id, tenant_id=user.tenant_id, prompt="test")
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    dataset = Dataset(job_id=job.id, tenant_id=user.tenant_id, name="ds")
    db_session.add(dataset)
    db_session.commit()

    mock_log = mocker.patch("app.tasks.gdpr_tasks.DataAccessAudit.log_data_access")
    result = gdpr_tasks.export_user_data_task(str(user.id))

    assert result["user"]["email"] == user.email
    mock_log.assert_called_once()


@pytest.mark.unit
def test_delete_user_data_task(db_session, mocker):
    from app.models import User
    user = User(
        email="delete@example.com",
        hashed_password=get_password_hash("pw"),
        tenant_id=uuid.uuid4(),
    )
    db_session.add(user)
    db_session.commit()

    mock_log = mocker.patch("app.tasks.gdpr_tasks.DataAccessAudit.log_data_access")
    result = gdpr_tasks.delete_user_data_task(str(user.id))

    assert result is True
    assert db_session.query(User).count() == 0
    mock_log.assert_called_once()


@pytest.mark.unit
def test_purge_expired_data(db_session):
    from app.models import User
    old_user = User(
        email="old@example.com",
        hashed_password=get_password_hash("pw"),
        tenant_id=uuid.uuid4(),
        created_at=datetime.utcnow() - timedelta(days=400),
        data_retention_days=365,
    )
    db_session.add(old_user)
    db_session.commit()

    deleted = gdpr_tasks.purge_expired_data()
    assert deleted >= 1
    assert db_session.query(User).count() == 0
