import pytest
from unittest.mock import AsyncMock
import sys
import types


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
