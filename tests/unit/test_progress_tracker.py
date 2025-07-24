import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, ANY

from app.tasks.progress_tracker import JobProgressTracker, ProgressContext
from app.models.job import JobStatus


@pytest.fixture
def tracker_setup(mocker):
    job = SimpleNamespace(
        id="job1",
        user_id="user1",
        status=JobStatus.PENDING,
        logs="",
        crawled_urls=0,
        total_urls=0,
        extracted_records=0,
        completed_at=None,
    )

    db = mocker.MagicMock()
    q = mocker.MagicMock()
    f = mocker.MagicMock()
    f.first.return_value = job
    q.filter.return_value = f
    db.query.return_value = q
    db.commit = mocker.MagicMock()
    db.rollback = mocker.MagicMock()
    db.close = mocker.MagicMock()
    mocker.patch("app.tasks.progress_tracker.SessionLocal", return_value=db)

    ws = mocker.MagicMock()
    ws.broadcast_to_channel = AsyncMock()
    mocker.patch("app.tasks.progress_tracker.WebSocketManager", return_value=ws)

    tracker = JobProgressTracker(job.id)
    return tracker, job, db, ws


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_status_updates_job_and_broadcasts(tracker_setup):
    tracker, job, db, ws = tracker_setup
    await tracker.update_status(JobStatus.CRAWLING, "start")

    assert job.status == JobStatus.CRAWLING
    assert "start" in job.logs
    db.commit.assert_called_once()
    db.rollback.assert_not_called()
    assert ws.broadcast_to_channel.call_count == 2
    call = ws.broadcast_to_channel.call_args_list[0]
    assert call.args[0] == f"job_{job.id}"
    msg = call.args[1]
    assert msg.data["type"] == "status_change"
    assert msg.data["new_status"] == JobStatus.CRAWLING.value
    assert msg.data["message"] == "start"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_status_rolls_back_on_error(tracker_setup):
    tracker, _, db, _ = tracker_setup
    db.commit.side_effect = Exception("db fail")
    await tracker.update_status(JobStatus.CRAWLING)

    db.rollback.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_progress_commits_and_broadcasts(tracker_setup):
    tracker, job, db, ws = tracker_setup
    await tracker.update_progress("crawling", 50, {"completed": 5, "total": 10})

    assert job.crawled_urls == 5
    assert job.total_urls == 10
    db.commit.assert_called_once()
    message = ws.broadcast_to_channel.call_args_list[0].args[1]
    assert message.data["type"] == "progress_update"
    assert message.data["progress"] == 50
    assert message.data["phase"] == "crawling"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_add_log_commits_and_broadcasts(tracker_setup):
    tracker, job, db, ws = tracker_setup
    await tracker.add_log("info", "hello", {"x": 1})

    assert "hello" in job.logs
    db.commit.assert_called_once()
    message = ws.broadcast_to_channel.call_args_list[0].args[1]
    assert message.data["type"] == "log"
    assert message.data["level"] == "info"
    assert message.data["message"] == "hello"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_complete_job_updates_status_and_broadcasts(tracker_setup):
    tracker, job, db, ws = tracker_setup
    await tracker.complete_job({"done": True})

    assert job.status == JobStatus.COMPLETED
    assert job.completed_at is not None
    db.commit.assert_called_once()
    message = ws.broadcast_to_channel.call_args_list[0].args[1]
    assert message.data["type"] == "job_completed"
    assert message.data["summary"] == {"done": True}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_report_error_calls_dependencies(tracker_setup, mocker):
    tracker, _, _, _ = tracker_setup
    mock_up = mocker.patch.object(tracker, "update_status", new=AsyncMock())
    mock_log = mocker.patch.object(tracker, "add_log", new=AsyncMock())
    await tracker.report_error("boom", {"a": 1})
    mock_up.assert_awaited_once_with(JobStatus.FAILED, "Error: boom")
    mock_log.assert_awaited_once_with("error", "boom", {"a": 1})


@pytest.fixture
def context_tracker(mocker):
    tracker = mocker.MagicMock()
    tracker.update_status = AsyncMock()
    tracker.update_progress = AsyncMock()
    tracker.add_log = AsyncMock()
    tracker.report_error = AsyncMock()
    mocker.patch("app.tasks.progress_tracker.JobProgressTracker", return_value=tracker)
    return tracker


@pytest.mark.unit
@pytest.mark.asyncio
async def test_progress_context_success(context_tracker):
    tracker = context_tracker
    async with ProgressContext("job2", "crawling", 10) as ctx:
        await ctx.increment()
        await ctx.log("step")
    tracker.update_status.assert_awaited_once_with(JobStatus.CRAWLING, "Starting crawling phase")
    tracker.update_progress.assert_awaited_with("crawling", 10, ANY)
    tracker.add_log.assert_awaited_with("info", "step", None)
    tracker.report_error.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_progress_context_error(context_tracker):
    tracker = context_tracker
    with pytest.raises(RuntimeError):
        async with ProgressContext("job2", "planning", 5):
            raise RuntimeError("fail")
    tracker.report_error.assert_awaited_once()
    args = tracker.report_error.call_args.args
    assert args[0] == "fail"
    assert args[1]["phase"] == "planning"
    assert args[1]["step"] == 0
