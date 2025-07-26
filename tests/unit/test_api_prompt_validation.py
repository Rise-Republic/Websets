import pytest
from starlette.background import BackgroundTasks
from fastapi import HTTPException

import importlib
import uuid

from app.auth.jwt_handler import get_password_hash
from app.models import User, Job, Dataset


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_job_invalid_prompt(db_session, monkeypatch):
    jobs_mod = importlib.import_module("app.api.v1.jobs")
    monkeypatch.setattr(jobs_mod.user_limiter, "limit", lambda *a, **k: (lambda f: f))
    monkeypatch.setattr(jobs_mod.tenant_limiter, "limit", lambda *a, **k: (lambda f: f))

    user = User(email="u@example.com", hashed_password=get_password_hash("pw"))
    user.tenant_id = uuid.uuid4()
    db_session.add(user)
    db_session.commit()

    job_data = jobs_mod.JobCreate(prompt="bad\x01prompt")

    with pytest.raises(HTTPException) as exc:
        await jobs_mod.create_job(
            job_data, BackgroundTasks(), current_user=user, db=db_session
        )
    assert exc.value.status_code == 400


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_job_sanitizes_prompt(db_session, monkeypatch):
    jobs_mod = importlib.import_module("app.api.v1.jobs")
    monkeypatch.setattr(jobs_mod.user_limiter, "limit", lambda *a, **k: (lambda f: f))
    monkeypatch.setattr(jobs_mod.tenant_limiter, "limit", lambda *a, **k: (lambda f: f))

    user = User(email="s@example.com", hashed_password=get_password_hash("pw"))
    user.tenant_id = uuid.uuid4()
    db_session.add(user)
    db_session.commit()

    job_data = jobs_mod.JobCreate(prompt="Hello {world}`")
    response = await jobs_mod.create_job(
        job_data, BackgroundTasks(), current_user=user, db=db_session
    )

    job = db_session.query(Job).filter(Job.id == response.id).first()
    assert job.prompt == "Hello \\{world\\}\\`"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_dataset_invalid_query(db_session, monkeypatch):
    datasets_mod = importlib.import_module("app.api.v1.datasets")
    monkeypatch.setattr(
        datasets_mod.user_limiter, "limit", lambda *a, **k: (lambda f: f)
    )
    monkeypatch.setattr(
        datasets_mod.tenant_limiter, "limit", lambda *a, **k: (lambda f: f)
    )

    class DummyVS:
        def load(self):
            return True

        def search(self, *a, **k):
            return []

    monkeypatch.setattr(datasets_mod, "VectorStore", lambda *a, **k: DummyVS())
    monkeypatch.setattr(
        datasets_mod.EmbeddingGenerator, "generate_embedding", lambda *a, **k: []
    )

    user = User(email="u2@example.com", hashed_password=get_password_hash("pw"))
    user.tenant_id = uuid.uuid4()
    db_session.add(user)
    db_session.commit()

    job = Job(user_id=user.id, tenant_id=user.tenant_id, prompt="ok")
    db_session.add(job)
    db_session.commit()

    dataset = Dataset(job_id=job.id, tenant_id=user.tenant_id, name="ds")
    db_session.add(dataset)
    db_session.commit()

    request = datasets_mod.SearchRequest(query="bad\x01query")

    with pytest.raises(HTTPException) as exc:
        await datasets_mod.search_dataset(
            str(dataset.id), request, current_user=user, db=db_session
        )
    assert exc.value.status_code == 400


@pytest.mark.unit
def test_export_dataset_params():
    import pathlib
    import warnings
    from fastapi import Query

    source = pathlib.Path("app/api/v1/datasets.py").read_text()
    assert 'pattern="^(json|csv)$"' in source

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always", DeprecationWarning)
        Query("json", pattern="^(json|csv)$")

    assert not any(issubclass(item.category, DeprecationWarning) for item in w)
