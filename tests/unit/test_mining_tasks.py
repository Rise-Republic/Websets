import pytest
from unittest.mock import AsyncMock
import sys
import types
import asyncio


@pytest.fixture(autouse=True, scope="session")
def mock_external_deps():
    """Provide dummy modules for optional dependencies."""
    celery_mod = types.SimpleNamespace(
        CeleryInstrumentor=lambda: types.SimpleNamespace(
            instrument=lambda self=None: None
        )
    )
    crawler_mod = types.SimpleNamespace(
        BrowserCrawler=type(
            "BrowserCrawler",
            (),
            {
                "__aenter__": lambda self: self,
                "__aexit__": lambda self, exc_type, exc, tb: None,
                "crawl_multiple_urls": AsyncMock(return_value=[]),
            },
        )
    )
    sys.modules.setdefault("opentelemetry.instrumentation.celery", celery_mod)
    sys.modules.setdefault("app.crawler", crawler_mod)
    yield
    sys.modules.pop("opentelemetry.instrumentation.celery", None)
    sys.modules.pop("app.crawler", None)


@pytest.fixture
def sample_job(db_session):
    from app.models import Job, JobStatus, User
    from app.auth.jwt_handler import get_password_hash

    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("password"),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    job = Job(user_id=user.id, prompt="collect data", status=JobStatus.PENDING)
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    return job


@pytest.mark.unit
def test_execute_planning_phase(db_session, sample_job, mocker):
    from app.tasks.mining_tasks import execute_planning_phase
    from app.models import Job

    mock_plan = {"summary": "test"}
    mocker.patch(
        "app.tasks.mining_tasks.PlannerAgent.execute",
        new=AsyncMock(return_value=mock_plan),
    )

    result = execute_planning_phase(sample_job, db_session)

    assert result == mock_plan
    refreshed = db_session.get(Job, sample_job.id)
    assert refreshed.plan == mock_plan


@pytest.mark.unit
def test_execute_discovery_phase(db_session, sample_job, mocker):
    from app.tasks.mining_tasks import execute_discovery_phase
    from app.models import DiscoveredURL

    plan = {"search_strategies": [], "estimated_urls": 1}
    mock_urls = ["https://example.com"]
    mocker.patch(
        "app.tasks.mining_tasks.DiscoveryAgent.execute",
        new=AsyncMock(return_value=mock_urls),
    )

    result = execute_discovery_phase(sample_job, plan, db_session)

    assert result == mock_urls
    db_urls = (
        db_session.query(DiscoveredURL)
        .filter(DiscoveredURL.job_id == sample_job.id)
        .all()
    )
    assert len(db_urls) == len(mock_urls)

@pytest.mark.unit
@pytest.mark.asyncio
async def test_execute_crawling_phase(db_session, sample_job, mocker):
    from app.tasks.mining_tasks import execute_crawling_phase
    from app.models import CrawlResult
    
    class DummyCrawler:
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            pass
        async def crawl_multiple_urls(self, urls, job_id):
            return [{"url": u, "html_content": "<html>", "title": "t"} for u in urls]

    class DummyProgress:
        def __init__(self):
            self.logs = []
            self.increments = []
        async def log(self, message, level="info", details=None):
            self.logs.append(message)
        async def increment(self, details=None):
            self.increments.append(details)

    mocker.patch("app.tasks.mining_tasks.BrowserCrawler", DummyCrawler)
    class DummyCR:
        def __init__(self, **kwargs):
            self.id = kwargs.get("id")

    mocker.patch("app.tasks.mining_tasks.CrawlResult", DummyCR)
    mocker.patch.object(db_session, "bulk_save_objects", lambda objs: None)
    mocker.patch.object(db_session, "commit", lambda: None)

    progress = DummyProgress()
    urls = ["https://example.com"]

    results = await asyncio.to_thread(
        execute_crawling_phase, sample_job, urls, db_session, progress
    )

    assert len(results) == 1
    assert results[0]["url"] == urls[0]
    assert progress.logs[0] == "Starting crawling phase"
    assert len(progress.increments) == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_execute_extraction_phase(db_session, sample_job, mocker):
    from app.tasks.mining_tasks import execute_extraction_phase
    import uuid

    class DummyURL:
        def __init__(self):
            self.id = uuid.uuid4()
            self.url = "https://example.com"
            self.html_content = "<html></html>"

    crawl = DummyURL()
    crawl_results = [{"url": crawl.url, "crawl_result_id": str(crawl.id)}]
    mocker.patch("app.tasks.mining_tasks.CrawlResult", DummyURL)
    class DummyDataset:
        def __init__(self, **kwargs):
            self.id = uuid.uuid4()
    class DummyRecord:
        def __init__(self, **kwargs):
            pass
    mocker.patch("app.tasks.mining_tasks.Dataset", DummyDataset)
    mocker.patch("app.tasks.mining_tasks.DataRecord", DummyRecord)

    def fake_query(model):
        class Q:
            def filter(self, *a, **k):
                class F:
                    def first(self_inner):
                        return crawl
                return F()
        return Q()

    mocker.patch.object(db_session, "query", side_effect=fake_query)
    mocker.patch.object(db_session, "bulk_save_objects", lambda objs: None)
    mocker.patch.object(db_session, "add", lambda obj, _warn=True: None)
    mocker.patch.object(db_session, "commit", lambda: None)

    mocker.patch(
        "app.tasks.mining_tasks.SchemaInferenceAgent.execute",
        new=AsyncMock(return_value={"data": [{"field": "value"}]}),
    )

    class DummyProgress:
        def __init__(self):
            self.increments = []
        async def log(self, *a, **k):
            pass
        async def increment(self, details=None):
            self.increments.append(details)

    progress = DummyProgress()
    sample_job.plan = {}
    db_session.commit()

    extracted = await asyncio.to_thread(
        execute_extraction_phase, sample_job, crawl_results, db_session, progress
    )

    assert isinstance(extracted, list)
    assert len(progress.increments) == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_start_and_cleanup_tasks(db_session, sample_job, mocker):
    from datetime import datetime, timedelta
    from app.tasks.mining_tasks import (
        start_mining_job,
        cleanup_old_jobs,
    )
    from app.models import Job, JobStatus

    metrics = mocker.MagicMock()
    mocker.patch("app.tasks.mining_tasks.get_metrics_collector", return_value=metrics)
    mocker.patch("app.tasks.mining_tasks.execute_planning_phase", return_value={})
    mocker.patch("app.tasks.mining_tasks.execute_discovery_phase", return_value=[])
    mocker.patch("app.tasks.mining_tasks.execute_crawling_phase", return_value=[])
    mocker.patch("app.tasks.mining_tasks.execute_extraction_phase", return_value=[])
    from tests.conftest import TestingSessionLocal
    mocker.patch("app.tasks.mining_tasks.SessionLocal", TestingSessionLocal)

    class DummyTracker:
        def __init__(self, job_id):
            self.job_id = job_id
        async def update_status(self, *a, **k):
            sess = TestingSessionLocal()
            job = sess.query(Job).filter(Job.id == self.job_id).first()
            job.started_at = datetime.utcnow()
            sess.commit()
            sess.close()
        async def complete_job(self, *a, **k):
            pass
        async def report_error(self, *a, **k):
            pass
    mocker.patch("app.tasks.mining_tasks.JobProgressTracker", DummyTracker)

    class DummyContext:
        def __init__(self, *a, **k):
            pass
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            return False
        async def update_step(self, *a, **k):
            pass
        async def increment(self, *a, **k):
            pass
        async def log(self, *a, **k):
            pass
    mocker.patch("app.tasks.mining_tasks.ProgressContext", DummyContext)

    sample_job.started_at = datetime.utcnow()
    db_session.commit()
    result = await asyncio.to_thread(start_mining_job.run, str(sample_job.id))

    assert result["status"] == "completed"
    metrics.record_job_started.assert_called_once()
    metrics.record_job_completed.assert_called_once()

    # create old completed job
    old_job = Job(
        user_id=sample_job.user_id,
        prompt="old",
        status=JobStatus.COMPLETED,
        completed_at=datetime.utcnow() - timedelta(days=31),
    )
    recent_job = Job(
        user_id=sample_job.user_id,
        prompt="recent",
        status=JobStatus.COMPLETED,
        completed_at=datetime.utcnow() - timedelta(days=1),
    )
    db_session.add_all([old_job, recent_job])
    db_session.commit()
    mocker.patch("app.tasks.mining_tasks.SessionLocal", return_value=db_session)

    cleanup_old_jobs.run()

    assert db_session.get(Job, old_job.id) is None
    assert db_session.get(Job, recent_job.id) is not None

