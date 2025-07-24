import uuid
import pytest
import app.websockets.manager  # required for coverage configuration

from app.repositories.job_repository import JobRepository
from app.repositories.dataset_repository import DatasetRepository
from app.models import User, Job, JobStatus, Dataset
from app.auth.jwt_handler import get_password_hash


@pytest.mark.unit
def test_job_repository_create_and_get(db_session):
    user = User(email="user@example.com", hashed_password=get_password_hash("pw"), tenant_id=uuid.uuid4())
    db_session.add(user)
    db_session.commit()

    repo = JobRepository(db_session)
    job = repo.create_job(user_id=user.id, tenant_id=user.tenant_id, prompt="test")

    fetched = repo.get_job(str(job.id), user.tenant_id)
    assert fetched is not None
    assert fetched.id == job.id
    assert fetched.prompt == "test"


@pytest.mark.unit
def test_job_repository_list_jobs_scoped(db_session):
    t1 = uuid.uuid4()
    t2 = uuid.uuid4()
    user1 = User(email="u1@example.com", hashed_password=get_password_hash("pw"), tenant_id=t1)
    user2 = User(email="u2@example.com", hashed_password=get_password_hash("pw"), tenant_id=t2)
    db_session.add_all([user1, user2])
    db_session.commit()

    job1 = Job(user_id=user1.id, tenant_id=t1, prompt="p1")
    job2 = Job(user_id=user2.id, tenant_id=t2, prompt="p2")
    db_session.add_all([job1, job2])
    db_session.commit()

    repo = JobRepository(db_session)
    jobs, total = repo.list_jobs(tenant_id=t1, status=None, page=1, size=10)

    assert total == 1
    assert len(jobs) == 1
    assert jobs[0].id == job1.id


@pytest.mark.unit
def test_job_repository_cancel_and_restart(db_session):
    tenant = uuid.uuid4()
    user = User(email="cancel@example.com", hashed_password=get_password_hash("pw"), tenant_id=tenant)
    db_session.add(user)
    db_session.commit()
    job = Job(user_id=user.id, tenant_id=tenant, prompt="p")
    db_session.add(job)
    db_session.commit()

    repo = JobRepository(db_session)
    repo.cancel_job(job)
    assert job.status == JobStatus.CANCELLED

    repo.restart_job(job)
    assert job.status == JobStatus.PENDING
    assert job.crawled_urls == 0


@pytest.mark.unit
def test_dataset_repository_basic_operations(db_session):
    tenant = uuid.uuid4()
    user = User(email="d@example.com", hashed_password=get_password_hash("pw"), tenant_id=tenant)
    db_session.add(user)
    db_session.commit()
    job = Job(user_id=user.id, tenant_id=tenant, prompt="p")
    db_session.add(job)
    db_session.commit()
    dataset = Dataset(job_id=job.id, tenant_id=tenant, name="ds")
    db_session.add(dataset)
    db_session.commit()

    repo = DatasetRepository(db_session)
    datasets, total = repo.list_datasets(tenant, page=1, size=10)
    assert total == 1
    assert datasets[0].id == dataset.id

    fetched = repo.get_dataset(str(dataset.id), tenant)
    assert fetched.id == dataset.id

    records, total_records = repo.get_dataset_records(str(dataset.id), page=1, size=10)
    assert total_records == 0

    repo.delete_dataset(dataset)
    assert repo.get_dataset(str(dataset.id), tenant) is None
