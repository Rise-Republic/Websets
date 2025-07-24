import asyncio
import pytest

from app.websockets import events

class DummyManager:
    def __init__(self):
        self.broadcasts = []
        self.sent = []
    async def broadcast_to_topic(self, topic, data, msg_type):
        self.broadcasts.append((topic, data, msg_type))
    async def send_to_user(self, user_id, data, msg_type):
        self.sent.append((user_id, data, msg_type))

def setup_tracker(monkeypatch):
    manager = DummyManager()
    monkeypatch.setattr(events, "get_websocket_manager", lambda: manager)
    tracker = events.JobProgressTracker()
    return tracker, manager

@pytest.mark.asyncio
async def test_emit_event_to_job_and_user(monkeypatch):
    tracker, manager = setup_tracker(monkeypatch)
    evt = events.ProgressEvent(
        event_type=events.ProgressEventType.JOB_STARTED,
        job_id="j",
        user_id="u",
        progress_percentage=0.0,
        message="start",
    )
    await tracker.emit_event(evt)
    assert manager.broadcasts[0][0] == tracker.get_topic_for_job("j")
    assert manager.broadcasts[1][0] == tracker.get_topic_for_user("u")
    assert manager.sent[0][0] == "u"

@pytest.mark.asyncio
async def test_cleanup_job_state(monkeypatch):
    tracker, _ = setup_tracker(monkeypatch)
    tracker.job_states["x"] = {"event_type": "dummy"}
    tracker.cleanup_job_state("x")
    assert tracker.get_job_state("x") is None
