import uuid
import pytest
import asyncio
from unittest import mock

from app.tenancy import set_current_tenant


@pytest.mark.unit
def test_job_list_scoped_by_tenant(db_session):
    with mock.patch(
        "app.middleware.rate_limiting.user_limiter.limit", lambda *a, **k: (lambda f: f)
    ), mock.patch(
        "app.middleware.rate_limiting.tenant_limiter.limit",
        lambda *a, **k: (lambda f: f),
    ):
        from app.models import User, Job
        from app.auth.jwt_handler import get_password_hash
        from app.api.v1.jobs import list_jobs

        tenant1 = uuid.uuid4()
        tenant2 = uuid.uuid4()
        user1 = User(
            email="u1@example.com",
            hashed_password=get_password_hash("pw"),
            tenant_id=tenant1,
        )
        user2 = User(
            email="u2@example.com",
            hashed_password=get_password_hash("pw"),
            tenant_id=tenant2,
        )
    db_session.add_all([user1, user2])
    db_session.commit()

    job1 = Job(user_id=user1.id, tenant_id=tenant1, prompt="job1")
    job2 = Job(user_id=user2.id, tenant_id=tenant2, prompt="job2")
    db_session.add_all([job1, job2])
    db_session.commit()

    set_current_tenant(user1.tenant_id)
    try:
        result = asyncio.run(list_jobs(current_user=user1, db=db_session))
    finally:
        set_current_tenant(None)

    assert len(result.jobs) == 1
    assert result.jobs[0].id == str(job1.id)
